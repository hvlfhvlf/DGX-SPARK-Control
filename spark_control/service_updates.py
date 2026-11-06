"""Opt-in official app maintenance. Private bindings, stopped units, reversible snapshots.

The HTTP process only checks metadata and launches a bounded transient user unit.
No command, path, URL or package name is accepted from the browser.
"""
import argparse
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

from .services import Registry, ServiceError, atomic, identifier, system_states

ROOT = Path(__file__).resolve().parent.parent
REPOS = {'hermes': 'NousResearch/hermes-agent', 'comfyui': 'Comfy-Org/ComfyUI'}
BUSY = ('queued', 'backup', 'install', 'validate', 'restoring')
VERSION = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?\Z')


def run(args, cwd=None, timeout=30, env=None):
    # Never include stdout/stderr/command in an API error or the journal.
    result = subprocess.run([str(x) for x in args], cwd=cwd, timeout=timeout,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    if result.returncode:
        raise ServiceError('update_command_failed')
    return result.stdout.decode(errors='replace').strip()


def remote_json(url):
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'DGX-SPARK-Control'})
    with urlopen(request, timeout=12) as response:
        if response.geturl().split('/')[2] != url.split('/')[2]:
            raise ServiceError('update_source_changed')
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ServiceError('update_response_limit')
    return json.loads(data)


def current(binding):
    root = Path(binding['root'])
    if binding['kind'] == 'harness':
        version = (root / 'active-version.txt').read_text().strip()
        if not VERSION.fullmatch(version):
            raise ServiceError('update_install_unrecognized')
        package = json.loads((root / 'releases' / version / 'node_modules/@deepseek-ai/dsh/package.json').read_text())
        if package.get('name') != '@deepseek-ai/dsh' or package.get('version') != version:
            raise ServiceError('update_install_unrecognized')
        return version, version
    commit = run(['git', '-C', root, 'rev-parse', 'HEAD'])
    version = run(['git', '-C', root, 'describe', '--tags', '--always'])
    # A local tag name is display data, never a command/target.
    return version[:100], commit


def source_check(binding):
    if binding['kind'] == 'harness':
        return
    root = Path(binding['root'])
    origin = run(['git', '-C', root, 'remote', 'get-url', 'origin'])
    if origin not in ('https://github.com/' + REPOS[binding['kind']],
                      'https://github.com/' + REPOS[binding['kind']] + '.git'):
        raise ServiceError('update_source_changed')
    if run(['git', '-C', root, 'status', '--porcelain', '--untracked-files=no']):
        raise ServiceError('update_local_changes')


def stopped(binding):
    states = system_states(binding['units'])
    for unit in binding['units']:
        s = states.get(unit, {})
        if s.get('LoadState') != 'loaded' or s.get('ActiveState') not in ('inactive', 'failed') or s.get('MainPID') != '0':
            raise ServiceError('update_stop_required')
    # Includes manual launches and other profiles using this installation.
    root = Path(binding['root']).resolve()
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            if (proc / 'cwd').resolve().is_relative_to(root) or (proc / 'exe').resolve().is_relative_to(root):
                raise ServiceError('update_install_in_use')
            argv = (proc / 'cmdline').read_bytes().split(b'\0')
            if any(a.startswith(str(root).encode() + b'/') for a in argv):
                raise ServiceError('update_install_in_use')
        except (OSError, RuntimeError):
            continue


class Snapshot:
    """Copy, never hardlink, mutable environments. Restore quarantines the failed tree."""
    def __init__(self, directory):
        self.directory = Path(directory)

    def create(self, targets):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        records = []
        for index, (source, exclude) in enumerate(targets):
            source = Path(source)
            if source.is_symlink() or not source.exists():
                raise ServiceError('update_snapshot_path')
            dest = self.directory / str(index)
            if source.is_dir():
                shutil.copytree(source, dest, symlinks=True,
                    ignore=lambda path, names: set(names) & set(exclude) if Path(path) == source else set())
            else:
                shutil.copy2(source, dest)
            records.append({'source': str(source), 'copy': str(dest), 'exclude': exclude})
        atomic(self.directory / 'manifest.json', records)
        # The ready manifest is written only after every copy succeeds.

    def restore(self):
        records = json.loads((self.directory / 'manifest.json').read_text())
        for item in records:
            source, saved = Path(item['source']), Path(item['copy'])
            restored = saved.with_name(saved.name + '-restore')
            # Build the complete replacement BEFORE moving the current tree.
            if restored.exists():
                raise ServiceError('update_recovery_needs_local_review')
            if saved.is_dir():
                shutil.copytree(saved, restored, symlinks=True)
            else:
                shutil.copy2(saved, restored)
            failed = source.with_name(source.name + '.update-failed-' + uuid.uuid4().hex[:10])
            os.rename(source, failed)
            try:
                for name in item['exclude']:
                    if (failed / name).exists() or (failed / name).is_symlink():
                        os.rename(failed / name, restored / name)
                os.rename(restored, source)
            except Exception:
                # Keep all paths and snapshot for explicit local recovery.
                raise ServiceError('update_recovery_needs_local_review') from None


class Updates:
    def __init__(self, registry):
        self.registry = registry
        self.directory = registry.directory
        self.active = self.directory / 'service-update-active.json'
        self.bindings = self.directory / 'service-updates.json'

    def binding(self, sid):
        identifier(sid)
        if not self.bindings.exists():
            return None
        data = json.loads(self.bindings.read_text())
        b = data.get(sid)
        if b is None:
            return None
        if b.get('kind') not in ('harness', 'hermes', 'comfyui'):
            raise ServiceError('update_install_unrecognized')
        registry = self.registry.read()
        service = next((s for s in registry['services'] if s['id'] == sid), None)
        profiles = [p for p in registry['profiles'] if p['service_id'] == sid]
        if not service or service['default_profile_id'] != b.get('profile_id'):
            raise ServiceError('update_binding_changed')
        if not profiles or any(not p['allow_control'] for p in profiles):
            raise ServiceError('control_not_allowed')
        units = sorted({p['manager']['unit'] for p in profiles})
        if units != sorted(b.get('units', [])):
            raise ServiceError('update_binding_changed')
        for key in ('root', 'data') if b['kind'] != 'comfyui' else ('root',):
            p = Path(b[key])
            if not p.is_absolute() or p.is_symlink() or not p.is_dir() or p == Path.home():
                raise ServiceError('update_install_unrecognized')
        return b

    def status(self, sid):
        b = self.binding(sid)
        if not b:
            return {'supported': False, 'current': None}
        version, fingerprint = current(b)
        check_path = self.directory / ('update-check-' + sid + '.json')
        check = json.loads(check_path.read_text()) if check_path.exists() else {}
        valid = (check.get('fingerprint') == fingerprint and check.get('binding') == b
                 and check.get('revision') == self.registry.read()['revision'] and time.time() - check.get('checked_at', 0) < 1800)
        job = json.loads(self.active.read_text()) if self.active.exists() else {}
        job = job if job.get('service_id') == sid else {}
        return dict(supported=True, current=version, channel=b.get('channel', 'latest'),
                    available=bool(valid and check.get('target') != fingerprint),
                    checked_at=check.get('checked_at') if valid else None,
                    candidate=check.get('version') if valid else None,
                    ticket=check.get('ticket') if valid else None,
                    job={k: job[k] for k in ('id', 'status', 'code', 'started_at', 'finished_at') if k in job})

    def check(self, sid):
        with self.registry.exclusive():
            b = self.binding(sid)
            if not b:
                raise ServiceError('update_not_supported')
            path = self.directory / ('update-check-' + sid + '.json')
            if path.exists() and time.time() - path.stat().st_mtime < 10:
                raise ServiceError('update_check_cooldown')
            # Remove a previous ticket before network access: failure never looks up-to-date.
            path.unlink(missing_ok=True)
            version, fingerprint = current(b)
            source_check(b)
            if b['kind'] == 'harness':
                metadata = remote_json('https://registry.npmjs.org/@deepseek-ai%2Fdsh/latest')
                target = metadata['version']
                if not VERSION.fullmatch(target):
                    raise ServiceError('update_source_changed')
                integrity = metadata['dist']['integrity']
                release = target
            else:
                repo = REPOS[b['kind']]
                channel = b.get('channel', 'stable')
                if channel in ('main', 'master'):
                    branch = 'master' if b['kind'] == 'comfyui' else 'main'
                    metadata = remote_json('https://api.github.com/repos/' + repo + '/git/ref/heads/' + branch)
                    target = metadata['object']['sha']
                    release = target[:12]
                elif channel == 'stable':
                    release = remote_json('https://api.github.com/repos/' + repo + '/releases/latest')['tag_name']
                    from urllib.parse import quote
                    ref = remote_json('https://api.github.com/repos/' + repo + '/git/ref/tags/' + quote(release, safe=''))['object']
                    if ref['type'] == 'tag':
                        ref = remote_json('https://api.github.com/repos/' + repo + '/git/tags/' + ref['sha'])['object']
                    if ref['type'] != 'commit':
                        raise ServiceError('update_source_changed')
                    target = ref['sha']
                else:
                    raise ServiceError('update_channel_unsupported')
                if not re.fullmatch('[0-9a-f]{40}', target):
                    raise ServiceError('update_source_changed')
                # Refuse downgrades/divergent branches, including canary -> older stable.
                if target != fingerprint:
                    compare = remote_json('https://api.github.com/repos/' + repo + '/compare/' + fingerprint + '...' + target + '?per_page=1')
                    if compare.get('status') != 'ahead':
                        raise ServiceError('update_channel_review_required')
                integrity = None
            atomic(path, dict(ticket=uuid.uuid4().hex, checked_at=time.time(), binding=b,
                revision=self.registry.read()['revision'], fingerprint=fingerprint,
                target=target, version=release, integrity=integrity))
            return self.status(sid)

    def apply(self, sid, ticket):
        with self.registry.exclusive():
            status = self.status(sid)
            if not status.get('available') or not ticket or ticket != status.get('ticket'):
                raise ServiceError('update_review_expired')
            b = self.binding(sid)
            self.check_retention(sid, b)
            stopped(b)
            source_check(b)
            # Permanent, private unit drop-ins reject accidental/manual starts while locked.
            guard = self.directory / 'service-update.lock'
            for unit in b['units']:
                drop = Path.home() / '.config/systemd/user' / (unit + '.d') / '90-spark-update-guard.conf'
                expected = '[Unit]\nConditionPathExists=!' + str(guard) + '\n'
                if not drop.exists() or drop.read_text() != expected:
                    raise ServiceError('update_guard_missing')
            check = json.loads((self.directory / ('update-check-' + sid + '.json')).read_text())
            job = dict(id=uuid.uuid4().hex, service_id=sid, binding=b, check=check,
                       status='queued', code='accepted', started_at=time.time())
            atomic(self.active, job)
            guard.touch(mode=0o600, exist_ok=True)
            command = [sys.executable, '-m', 'spark_control.service_updates', 'worker', '--directory', str(self.directory)]
            recovery = shlex.join([sys.executable, '-m', 'spark_control.service_updates', 'recover', '--directory', str(self.directory)])
            try:
                # No output is sent to journal; private state contains sanitized stage/error only.
                run(['systemd-run', '--user', '--quiet', '--collect', '--unit=spark-app-update-' + job['id'],
                     '--property=Type=exec', '--property=MemoryMax=2G', '--property=MemorySwapMax=0',
                     '--property=CPUQuota=150%', '--property=TasksMax=128', '--property=Nice=10',
                     '--property=RuntimeMaxSec=3600', '--property=TimeoutStopSec=180',
                     '--property=ExecStopPost=' + recovery,
                     '--property=StandardOutput=null', '--property=StandardError=null',
                     '--working-directory=' + str(ROOT), *command])
            except Exception:
                # A timeout can occur after systemd accepted the worker. Keep the
                # guard until that worker or explicit recovery resolves the job.
                job.update(status='recovery_required', code='update_worker_not_started')
                atomic(self.active, job)
                raise ServiceError('update_worker_not_started') from None
            return self.status(sid)

    def backups(self, sid, b):
        parent = self.directory / 'service-update-backups'
        if not parent.exists():
            return []
        found = []
        for path in parent.iterdir():
            if path.is_symlink() or not path.is_dir():
                continue
            meta = path / 'retention.json'
            if not meta.is_file() or meta.is_symlink():
                continue
            data = json.loads(meta.read_text())
            if data.get('owner') == 'spark-control' and data.get('service_id') == sid and data.get('binding') == b:
                found.append((path, data))
        return found

    def check_retention(self, sid, b):
        if any(data.get('review_required') for _, data in self.backups(sid, b)):
            raise ServiceError('update_backup_review_required')

    def finish_backup(self, job, backup):
        if not backup.exists():
            return
        state = job['status']
        review = bool(job.get('mutated')) and (state != 'completed' or job.get('code') == 'update_complete_review')
        atomic(backup / 'retention.json', dict(owner='spark-control', service_id=job['service_id'],
            binding=job['binding'], status=state, review_required=review))
        if state == 'completed' and not review:
            # Keep the newest rollback point; only our explicitly managed copies
            # from earlier successful/verified runs are eligible for removal.
            for older, data in self.backups(job['service_id'], job['binding']):
                if older != backup and not data.get('review_required') and data.get('status') in ('completed', 'verified_backup'):
                    shutil.rmtree(older)
            if job['binding']['kind'] == 'harness':
                releases = Path(job['binding']['root']) / 'releases'
                keep = {job['check']['target'], job['check']['fingerprint']}
                for release in releases.iterdir():
                    marker = release / '.spark-control-release.json'
                    if release.name in keep or not VERSION.fullmatch(release.name) or release.is_symlink() or not release.is_dir():
                        continue
                    if marker.is_file() and not marker.is_symlink() and json.loads(marker.read_text()) == {'owner': 'spark-control', 'version': release.name}:
                        shutil.rmtree(release)
        elif not job.get('mutated'):
            # A failed copy/preflight never changed the app; no partial backup is useful.
            shutil.rmtree(backup)

    def worker(self, recovery=False):
        with self.registry.exclusive(check_update=False):
            job = json.loads(self.active.read_text())
            if job['status'] not in BUSY and job['status'] != 'recovery_required':
                return
            b, check = job['binding'], job['check']
            backup = self.directory / 'service-update-backups' / job['id']
            snapshot = Snapshot(backup)
            def stage(status, code=None):
                job.update(status=status, code=code or status)
                atomic(self.active, job)
            mutated = job.get('mutated', False)
            try:
                if self.binding(job['service_id']) != b:
                    raise ServiceError('update_binding_changed')
                stopped(b)
                if recovery:
                    raise ServiceError('update_interrupted')
                if current(b)[1] != check['fingerprint']:
                    raise ServiceError('update_review_expired')
                source_check(b)
                self.check_retention(job['service_id'], b)
                targets = self.targets(b)
                if any(Path(p).parent.stat().st_dev != self.directory.stat().st_dev for p, _ in targets):
                    raise ServiceError('update_snapshot_filesystem')
                size = sum(tree_size(Path(p), excludes) for p, excludes in targets)
                if shutil.disk_usage(self.directory).free < size * 3 + 2 * 1024**3:
                    raise ServiceError('update_disk_space')
                stage('backup')
                snapshot.create(targets)
                stopped(b)
                stage('install')
                job['mutated'] = mutated = True
                atomic(self.active, job)  # Crash recovery must know before first write.
                if b['kind'] == 'hermes':
                    # The official launcher may repair/migrate runtime state, so even
                    # baseline diagnostics run only after a completed snapshot.
                    check['doctor_baseline'] = self.hermes_doctor(b)
                    atomic(self.active, job)
                self.install(b, check)
                stage('validate')
                advisory = self.validate_install(b, check)
                stage('completed', 'update_complete_review' if advisory else 'update_complete_stopped')
            except Exception as error:
                code = str(error) if isinstance(error, ServiceError) else 'update_failed'
                if mutated:
                    stage('restoring')
                    try:
                        stopped(b)
                        snapshot.restore()
                        if current(b)[1] != check['fingerprint']:
                            raise ServiceError('update_restore_version_mismatch')
                        stage('rolled_back', 'update_failed_restored')
                    except Exception:
                        stage('recovery_required', 'update_recovery_needs_local_review')
                else:
                    stage('failed', code)
            finally:
                try:
                    self.finish_backup(job, backup)
                except Exception:
                    # Cleanup must never turn a healthy install into a rollback.
                    job['code'] = 'update_backup_cleanup_required'
                    if backup.exists():
                        atomic(backup / 'retention.json', dict(owner='spark-control', service_id=job['service_id'],
                            binding=b, status=job['status'], review_required=True))
                job['finished_at'] = time.time()
                atomic(self.active, job)
                if job['status'] != 'recovery_required':
                    (self.directory / 'service-update.lock').unlink(missing_ok=True)

    @staticmethod
    def targets(b):
        root = Path(b['root'])
        if b['kind'] == 'harness':
            return [(root / 'active-version.txt', []), (Path(b['data']), [])]
        if b['kind'] == 'hermes':
            # The code + virtualenv may live inside HERMES_HOME; copy only once.
            data = Path(b['data'])
            return [(data, [])] if root.is_relative_to(data) else [(root, []), (data, [])]
        return [(root, ['models', 'input', 'output', 'temp', 'custom_nodes'])]

    @staticmethod
    def install(b, check):
        root, kind = Path(b['root']), b['kind']
        target = check['target']
        if kind == 'harness':
            node = Path(b['node'])
            destination = root / 'releases' / target
            if destination.exists():
                raise ServiceError('update_candidate_exists_review_locally')
            # npm verifies registry integrity; also compare the exact reviewed top-level digest.
            npm = node.parent.parent / 'lib/node_modules/npm/bin/npm-cli.js'
            run([node, npm, 'install', '--prefix', destination, '--save-exact',
                 '@deepseek-ai/dsh@' + target, '--registry=https://registry.npmjs.org',
                 '--no-audit', '--no-fund'], timeout=1800,
                env={**os.environ, 'PATH': str(node.parent) + os.pathsep + os.environ.get('PATH', '')})
            lock = json.loads((destination / 'package-lock.json').read_text())
            if lock['packages']['node_modules/@deepseek-ai/dsh']['integrity'] != check['integrity']:
                raise ServiceError('update_integrity_changed')
            run([node, destination / 'node_modules/@deepseek-ai/dsh/lib/bin.js', '--version'])
            atomic(destination / '.spark-control-release.json', {'owner': 'spark-control', 'version': target})
            temp = root / 'active-version.update-tmp'
            temp.write_text(target + '\n')
            os.replace(temp, root / 'active-version.txt')
        elif kind == 'hermes':
            # Official updater owns migrations/dependency sync. Never restart its fleet.
            run([root / '.hermes/bin/hermes', 'update', '--yes', '--no-gateway-restart',
                 '--channel', b.get('channel', 'stable')], cwd=root, timeout=2400,
                env={**os.environ, 'HERMES_HOME': b['data']})
            if current(b)[1] != target:
                raise ServiceError('update_target_changed')
        else:
            run(['git', '-C', root, 'fetch', '--no-tags', 'origin', target], timeout=300)
            run(['git', '-C', root, 'checkout', '--detach', target])
            python = root / '.venv/bin/python'
            # Preserve the existing DGX CUDA/Torch stack. Conflicting releases fail instead.
            constraints = root / '.spark-update-constraints.txt'
            constraints.write_text(run([python, '-c', "import importlib.metadata as m; print('\\n'.join(n+'=='+m.version(n) for n in ('torch','torchvision','torchaudio') if m.packages_distributions().get(n)))"]) + '\n')
            try:
                run([python, '-m', 'pip', 'install', '-r', 'requirements.txt', '-c', constraints], cwd=root, timeout=1800)
            finally:
                constraints.unlink(missing_ok=True)

    @staticmethod
    def hermes_doctor(b):
        result = subprocess.run([str(Path(b['root']) / '.hermes/bin/hermes'), 'doctor'],
            cwd=b['root'], timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={**os.environ, 'HERMES_HOME': b['data']})
        return result.returncode

    @staticmethod
    def validate_install(b, check):
        root = Path(b['root'])
        advisory = False
        if current(b)[1] != check['target']:
            raise ServiceError('update_target_changed')
        if b['kind'] == 'harness':
            run([b['node'], root / 'releases' / check['target'] / 'node_modules/@deepseek-ai/dsh/lib/bin.js', '--version'])
        elif b['kind'] == 'hermes':
            # Current Hermes can use its managed hermetic runtime, not a pip venv.
            env = {**os.environ, 'HERMES_HOME': b['data']}
            run([root / '.hermes/bin/hermes', '--version'], cwd=root, timeout=90, env=env)
            result = Updates.hermes_doctor(b)
            if result and not check.get('doctor_baseline'):
                raise ServiceError('update_validation_failed')
            advisory = bool(result)
        else:
            python = root / '.venv/bin/python'
            run([python, '-m', 'pip', 'check'], timeout=90)
            run([python, '-c', 'import torch, comfy.cli_args, server'], cwd=root, timeout=90)
        stopped(b)
        return advisory


def tree_size(root, excludes):
    if root.is_file():
        return root.stat().st_size
    total = 0
    for path, directories, files in os.walk(root, followlinks=False):
        if Path(path) == root:
            directories[:] = [d for d in directories if d not in excludes]
        for name in files:
            p = Path(path) / name
            if not p.is_symlink():
                total += p.stat().st_size
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['worker', 'recover', 'guards'])
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    updates = Updates(Registry(args.directory))
    if args.action == 'guards':
        for sid in json.loads(updates.bindings.read_text()):
            b = updates.binding(sid)
            for unit in b['units']:
                path = Path.home() / '.config/systemd/user' / (unit + '.d') / '90-spark-update-guard.conf'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('[Unit]\nConditionPathExists=!' + str(updates.directory / 'service-update.lock') + '\n')
        run(['systemctl', '--user', 'daemon-reload'])
    else:
        updates.worker(args.action == 'recover')


if __name__ == '__main__':
    main()
