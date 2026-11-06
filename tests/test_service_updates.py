import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from spark_control.services import Registry, ServiceError, atomic
from spark_control.service_updates import Updates, Snapshot, stopped


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.registry = Registry(self.base / 'config')
        self.updates = Updates(self.registry)
        self.app = self.base / 'app'
        self.data = self.base / 'data'
        self.app.mkdir(); self.data.mkdir()
        self.binding = dict(kind='harness', root=str(self.app), data=str(self.data),
                            units=['fixture.service'], profile_id='fixture')
        (self.app / 'active-version.txt').write_text('1.0.0\n')
        for version in ['1.0.0', '1.1.0']:
            p = self.app / 'releases' / version / 'node_modules/@deepseek-ai/dsh'
            p.mkdir(parents=True)
            (p / 'package.json').write_text(json.dumps(dict(name='@deepseek-ai/dsh', version=version)))
        (self.data / 'history.db').write_bytes(b'original conversations')
        atomic(self.registry.path, dict(registry_schema=1, revision=0, services=[dict(id='fixture', name='Fixture', adapter='process', default_profile_id='fixture')],
            profiles=[dict(id='fixture', service_id='fixture', name='Fixture', allow_control=True, manager=dict(type='systemd-user',unit='fixture.service'))], assets=[]))
        atomic(self.updates.bindings, {'fixture': self.binding})

    def tearDown(self):
        self.tmp.cleanup()

    def job(self):
        job = dict(id='fixture-test',service_id='fixture', binding=self.binding,
            check=dict(fingerprint='1.0.0',target='1.1.0'),status='queued',started_at=time.time())
        atomic(self.updates.active,job)
        (self.registry.directory / 'service-update.lock').touch()
        return job

    def test_active_service_and_unknown_state_rejected(self):
        for fields in [{}, dict(LoadState='loaded',ActiveState='active',MainPID='12'),
                       dict(LoadState='loaded',ActiveState='inactive',MainPID='12'),
                       dict(LoadState='loaded',ActiveState='activating',MainPID='0')]:
            with self.subTest(fields=fields), patch('spark_control.service_updates.system_states', return_value={'fixture.service': fields}):
                with self.assertRaisesRegex(ServiceError,'update_stop_required'):
                    stopped(self.binding)

    def test_readonly_status_does_not_check_network(self):
        with patch('spark_control.service_updates.remote_json') as network:
            self.assertEqual(self.updates.status('fixture')['current'],'1.0.0')
            self.assertFalse(self.updates.status('fixture')['available'])
            network.assert_not_called()

    def test_ticket_expires_and_settings_change_invalidates(self):
        check=dict(ticket='ticket',checked_at=time.time(),binding=self.binding,revision=0,
                   fingerprint='1.0.0',target='1.1.0',version='1.1.0')
        p=self.registry.directory/'update-check-fixture.json'
        atomic(p,check)
        self.assertTrue(self.updates.status('fixture')['available'])
        check['checked_at']-=1801;atomic(p,check)
        self.assertFalse(self.updates.status('fixture')['available'])
        with self.assertRaisesRegex(ServiceError,'update_review_expired'):
            self.updates.apply('fixture','ticket')

    def test_failed_network_invalidates_previous_ticket(self):
        p=self.registry.directory/'update-check-fixture.json'
        atomic(p,{'checked_at':time.time()-40})
        import os
        os.utime(p,(time.time()-40,time.time()-40))
        with patch('spark_control.service_updates.remote_json',side_effect=OSError):
            with self.assertRaises(OSError):self.updates.check('fixture')
        self.assertFalse(p.exists())

    def test_registry_mutations_blocked_during_update(self):
        self.job()
        with self.assertRaisesRegex(ServiceError,'update_in_progress'):
            with self.registry.exclusive():pass
        with self.registry.exclusive(check_update=False):pass

    def test_uncertain_worker_launch_retains_guard(self):
        check=dict(ticket='ticket',checked_at=time.time(),binding=self.binding,revision=0,
                   fingerprint='1.0.0',target='1.1.0',version='1.1.0')
        atomic(self.registry.directory/'update-check-fixture.json',check)
        drop=self.base/'.config/systemd/user/fixture.service.d/90-spark-update-guard.conf'
        drop.parent.mkdir(parents=True)
        guard=self.registry.directory/'service-update.lock'
        drop.write_text('[Unit]\nConditionPathExists=!'+str(guard)+'\n')
        with patch('spark_control.service_updates.Path.home',return_value=self.base), patch('spark_control.service_updates.stopped'), patch('spark_control.service_updates.run',side_effect=TimeoutError):
            with self.assertRaisesRegex(ServiceError,'update_worker_not_started'):
                self.updates.apply('fixture','ticket')
        self.assertTrue(guard.exists())
        self.assertEqual(json.loads(self.updates.active.read_text())['status'],'recovery_required')

    def test_success_keeps_one_managed_backup_and_unmanaged_data(self):
        job=self.job()
        parent=self.registry.directory/'service-update-backups'
        old=parent/'old';old.mkdir(parents=True)
        atomic(old/'retention.json',dict(owner='spark-control',service_id='fixture',binding=self.binding,status='verified_backup',review_required=False))
        unknown=parent/'user-copy';unknown.mkdir();(unknown/'keep').write_text('keep')
        new=parent/job['id'];new.mkdir();(new/'saved').write_text('rollback point')
        job.update(status='completed',code='update_complete_stopped',mutated=True)
        self.updates.finish_backup(job,new)
        self.assertFalse(old.exists());self.assertTrue((new/'saved').exists());self.assertTrue((unknown/'keep').exists())

    def test_failed_update_blocks_repeat_backup_accumulation(self):
        job=self.job();backup=self.registry.directory/'service-update-backups'/job['id'];backup.mkdir(parents=True)
        job.update(status='rolled_back',mutated=True)
        self.updates.finish_backup(job,backup)
        with self.assertRaisesRegex(ServiceError,'update_backup_review_required'):
            self.updates.check_retention('fixture',self.binding)
        self.assertTrue(backup.exists())

    def test_harness_prunes_only_owned_releases_outside_current_and_previous(self):
        releases=self.app/'releases';stale=releases/'0.9.0';stale.mkdir()
        atomic(stale/'.spark-control-release.json',dict(owner='spark-control',version='0.9.0'))
        foreign=releases/'0.8.0';foreign.mkdir();(foreign/'keep').write_text('manual install')
        job=self.job();backup=self.registry.directory/'service-update-backups'/job['id'];backup.mkdir(parents=True)
        job.update(status='completed',mutated=True,code='update_complete_stopped')
        self.updates.finish_backup(job,backup)
        self.assertFalse(stale.exists());self.assertTrue(foreign.exists())
        self.assertTrue((releases/'1.0.0').exists());self.assertTrue((releases/'1.1.0').exists())

    def test_failed_install_restores_real_version_and_history(self):
        self.job()
        def fail(*args):
            (self.app/'active-version.txt').write_text('1.1.0\n')
            (self.data/'history.db').write_bytes(b'new schema')
            (self.data/'new-secret').write_text('private fixture')
            raise RuntimeError('sensitive command output must not escape')
        with patch('spark_control.service_updates.stopped'),patch.object(Updates,'install',side_effect=fail):
            self.updates.worker()
        self.assertEqual((self.app/'active-version.txt').read_text(),'1.0.0\n')
        self.assertEqual((self.data/'history.db').read_bytes(),b'original conversations')
        self.assertFalse((self.data/'new-secret').exists())
        record=json.loads(self.updates.active.read_text())
        self.assertEqual(record['status'],'rolled_back')
        self.assertNotIn('sensitive',json.dumps(record))
        self.assertFalse((self.registry.directory/'service-update.lock').exists())

    def test_validation_failure_rolls_back_environment_and_excludes_weights(self):
        root=self.base/'comfy';root.mkdir()
        for directory in ['.venv','models','custom_nodes']:(root/directory).mkdir()
        (root/'.venv/package').write_text('old dependency')
        (root/'models/weights').write_bytes(b'preserve weights')
        snapshot=Snapshot(self.base/'backup');snapshot.create([(root,['models','custom_nodes'])])
        (root/'.venv/package').write_text('incompatible dependency')
        (root/'new-code.py').write_text('bad')
        snapshot.restore()
        self.assertEqual((root/'.venv/package').read_text(),'old dependency')
        self.assertEqual((root/'models/weights').read_bytes(),b'preserve weights')
        self.assertFalse((root/'new-code.py').exists())
        self.assertTrue((root/'custom_nodes').is_dir())

    def test_snapshot_failure_never_calls_installer(self):
        self.job()
        with patch('spark_control.service_updates.stopped'),patch.object(Snapshot,'create',side_effect=OSError),patch.object(Updates,'install') as install:
            self.updates.worker()
            install.assert_not_called()
        self.assertEqual(json.loads(self.updates.active.read_text())['status'],'failed')
        self.assertEqual((self.data/'history.db').read_bytes(),b'original conversations')

    def test_hermes_nested_environment_and_state_restored_together(self):
        home=self.base/'hermes-home';root=home/'hermes-agent';venv=root/'.hermes'
        venv.mkdir(parents=True)
        (venv/'dependency').write_text('old')
        (root/'code.py').write_text('old code')
        (home/'state.db').write_bytes(b'old schema')
        b=dict(kind='hermes',root=str(root),data=str(home))
        self.assertEqual(len(Updates.targets(b)),1)
        snapshot=Snapshot(self.base/'hermes-backup');snapshot.create(Updates.targets(b))
        (venv/'dependency').write_text('new');(home/'state.db').write_bytes(b'migrated')
        snapshot.restore()
        self.assertEqual((venv/'dependency').read_text(),'old')
        self.assertEqual((home/'state.db').read_bytes(),b'old schema')

    def test_recovery_failure_retains_guard(self):
        self.job()
        with patch('spark_control.service_updates.stopped'),patch.object(Updates,'install',side_effect=RuntimeError),patch.object(Snapshot,'restore',side_effect=OSError):
            self.updates.worker()
        self.assertEqual(json.loads(self.updates.active.read_text())['status'],'recovery_required')
        self.assertTrue((self.registry.directory/'service-update.lock').exists())

    def test_crash_recovery_uses_persisted_backup(self):
        job=self.job()
        Snapshot(self.registry.directory/'service-update-backups'/job['id']).create(Updates.targets(self.binding))
        (self.app/'active-version.txt').write_text('1.1.0\n')
        job.update(status='install',mutated=True);atomic(self.updates.active,job)
        with patch('spark_control.service_updates.stopped'):
            self.updates.worker(recovery=True)
        self.assertEqual((self.app/'active-version.txt').read_text(),'1.0.0\n')
        # ExecStopPost after success/rollback is idempotent and never replays a backup.
        with patch.object(Snapshot,'restore') as restore:
            self.updates.worker(recovery=True);restore.assert_not_called()

    def test_success_keeps_service_stopped_and_no_shell(self):
        self.job()
        def install(*args):(self.app/'active-version.txt').write_text('1.1.0\n')
        with patch('spark_control.service_updates.stopped') as guard,patch.object(Updates,'install',side_effect=install),patch.object(Updates,'validate_install'):
            self.updates.worker()
            self.assertGreaterEqual(guard.call_count,2)
        self.assertEqual(json.loads(self.updates.active.read_text())['status'],'completed')

    def test_hermes_uses_managed_launcher_and_distinguishes_new_doctor_failure(self):
        b=dict(kind='hermes',root=str(self.app),data=str(self.data))
        with patch('spark_control.service_updates.current',return_value=('new','new')),patch('spark_control.service_updates.run') as command,patch('spark_control.service_updates.stopped'),patch.object(Updates,'hermes_doctor',return_value=1):
            with self.assertRaisesRegex(ServiceError,'update_validation_failed'):
                Updates.validate_install(b,dict(target='new',doctor_baseline=0))
            self.assertTrue(Updates.validate_install(b,dict(target='new',doctor_baseline=1)))
            self.assertEqual(str(command.call_args.args[0][0]),str(self.app/'.hermes/bin/hermes'))


if __name__=='__main__':unittest.main()
