"""On-demand boot settings for registered user services; never starts a process."""
import os
import subprocess
from .services import ServiceError


def command(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=6)
    except (OSError, subprocess.SubprocessError):
        raise ServiceError('autostart_unavailable') from None


def unit_states(units):
    call = command(['systemctl', '--user', 'show', '--property=Id,LoadState,UnitFileState', '--', *sorted(set(units))])
    rows = {}
    for block in call.stdout.strip().split('\n\n'):
        fields = dict(line.split('=', 1) for line in block.splitlines() if '=' in line)
        if fields.get('Id'):
            rows[fields['Id']] = fields
    return rows


def simple_boot_unit(unit):
    """Reject indirect installs and side effects on other units."""
    call = command(['systemctl', '--user', 'cat', '--', unit])
    section, settings = '', {}
    for line in call.stdout.splitlines():
        line = line.strip()
        if line.startswith('['):
            section = line
        elif section == '[Install]' and '=' in line and not line.startswith(('#', ';')):
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            settings[key] = (settings.get(key, '') + ' ' + value).strip() if value else ''
    return call.returncode == 0 and settings.get('WantedBy', '').split() == ['default.target'] and not any(settings.get(k) for k in ('Also', 'Alias', 'RequiredBy', 'UpheldBy'))


class Autostart:
    def __init__(self, registry):
        self.registry = registry

    def resolve(self, value, sid):
        service = next((s for s in value['services'] if s['id'] == sid), None)
        if not service:
            raise ServiceError('unknown_service')
        return next(p for p in value['profiles'] if p['id'] == service['default_profile_id'])

    def snapshot(self, value, profile, states=None):
        unit = profile['manager']['unit']
        fields = (states if states is not None else unit_states([unit])).get(unit, {})
        state = fields.get('UnitFileState', 'unknown')
        linger = command(['loginctl', 'show-user', str(os.getuid()), '-p', 'Linger', '--value'])
        boot = linger.returncode == 0 and linger.stdout.strip() == 'yes'
        supported = fields.get('LoadState') == 'loaded' and state in ('enabled', 'disabled')
        return dict(profile_id=profile['id'], revision=value['revision'], enabled=state == 'enabled' if supported else None,
                    editable=supported and profile['allow_control'] and simple_boot_unit(unit), boot_ready=boot,
                    maintenance=(self.registry.directory / 'service-update.lock').exists())

    def status(self, sid):
        value = self.registry.read()
        return self.snapshot(value, self.resolve(value, sid))

    def set(self, data):
        if type(data.get('enabled')) is not bool:
            raise ServiceError('invalid_autostart')
        with self.registry.exclusive():
            value = self.registry.read()
            profile = self.resolve(value, data.get('id'))
            if type(data.get('revision')) is not int or data['revision'] != value['revision'] or data.get('profile_id') != profile['id']:
                raise ServiceError('revision_conflict')
            states = unit_states([p['manager']['unit'] for p in value['profiles']])
            current = self.snapshot(value, profile, states)
            if not current['editable']:
                raise ServiceError('autostart_unsupported')
            enabled = data['enabled']
            if enabled and not current['boot_ready']:
                raise ServiceError('autostart_linger_required')
            if enabled:
                for other in value['profiles']:
                    if other['manager']['unit'] == profile['manager']['unit']:
                        continue
                    if other['service_id'] == profile['service_id'] or set(other['exclusive_groups']) & set(profile['exclusive_groups']):
                        other_state = states.get(other['manager']['unit'], {}).get('UnitFileState')
                        if other_state not in ('disabled', 'static', 'masked'):
                            raise ServiceError('autostart_conflict')
            if current['enabled'] != enabled:
                # No --now: change future startup only. Do not expose command output.
                result = command(['systemctl', '--user', 'enable' if enabled else 'disable', '--', profile['manager']['unit']])
                if result.returncode:
                    raise ServiceError('autostart_change_failed')
            result = self.snapshot(value, profile)
            if result['enabled'] is not enabled:
                raise ServiceError('autostart_change_failed')
            return result
