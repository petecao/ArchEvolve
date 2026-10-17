"""2026-10-16 ET. Pure outer guard controls; no actual observation root or tools."""
import copy
import json
from pathlib import Path
import runpy
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
API = runpy.run_path(str(HERE / 'outer.py'))


class Controls(unittest.TestCase):
    def test_exact_child_helpers_and_console_headroom_are_bound_without_running_child(self):
        helpers = API['load_helpers']()
        self.assertEqual(helpers['OutputWatch'].loop.__globals__['BUDGET'], API['AGGREGATE'] - API['CONSOLE'])
        self.assertEqual(helpers['OutputWatch'].loop.__globals__['FINAL_HEADROOM'], API['HEADROOM'])
        self.assertIs(helpers['OutputWatch'].loop.__globals__['extent'], API['extent'])
        self.assertFalse(API['ROOT'].exists())
        with patch.dict(API['load_helpers'].__globals__, {'ENTRY_SHA256': '0' * 64}):
            with self.assertRaises(ValueError):
                API['load_helpers']()

    def test_aggregate_scan_and_guard_include_temporary_profile_logs_and_metadata(self):
        helpers = API['load_helpers']()
        with tempfile.TemporaryDirectory(prefix='probata-move-outer-budget-', dir='/private/tmp') as raw:
            root = Path(raw)
            for name, size in [('tmp/compiler/active', 30), ('profile/native', 30),
                               ('worker.log', 10), ('outer-command.json', 10)]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'x' * size)
            self.assertEqual(API['extent'](root), 80)
            killed = []
            watch = helpers['OutputWatch'](root, lambda: (killed.append(True), watch.stop.set()))
            with patch.dict(helpers['OutputWatch'].loop.__globals__, {'BUDGET': 100, 'FINAL_HEADROOM': 25}):
                watch.loop()
            self.assertEqual(killed, [True])
            self.assertIn('aggregate', watch.error)
            gate = API['make_gate'](helpers, watch, 720, clock=lambda: 1)
            with self.assertRaises(ValueError):
                gate.call(lambda: self.fail('latched outer must never invoke a child'))

    def test_final_metadata_and_console_reserve_cannot_exceed_entire_root_cap(self):
        helpers = API['load_helpers']()
        with tempfile.TemporaryDirectory(prefix='probata-move-outer-final-', dir='/private/tmp') as raw:
            root = Path(raw)
            (root / 'tmp').mkdir()
            (root / 'tmp/compiler').write_bytes(b'x' * 90)
            gate = API['make_gate'](helpers, None, 720, clock=lambda: 1)
            with patch.dict(helpers['finalize'].__globals__, {'BUDGET': 100}):
                with self.assertRaises(ValueError):
                    helpers['finalize'](root, {'producer_complete': True}, gate, 0)
            self.assertFalse((root / 'result.json').exists())
            self.assertFalse((root / 'artifact-manifest.json').exists())
            (root / 'tmp/compiler').write_bytes(b'raw')
            final = helpers['finalize'](root, {'producer_complete': True}, gate, 0)
            self.assertEqual(final['aggregate_bytes'], API['extent'](root))
            self.assertLessEqual(final['aggregate_bytes'] + API['CONSOLE'], API['AGGREGATE'])

    def test_only_both_exact_private_scratch_paths_have_active_socket_and_race_exceptions(self):
        root = Path('/exact/outer')
        for path in (root / 'tmp/compiler/socket', root / 'profile/wp/tmp/socket',
                     root / 'profile/reader/socket', root / 'foreign/socket'):
            for mode in (stat.S_IFSOCK, 'disappearing'):
                def observe(*, follow_symlinks):
                    self.assertFalse(follow_symlinks)
                    if mode == 'disappearing':
                        raise FileNotFoundError(path)
                    return SimpleNamespace(st_mode=mode, st_size=0)
                entry = SimpleNamespace(path=str(path), stat=observe)
                with patch.object(API['os'], 'scandir', return_value=[entry]):
                    for active in (False, True):
                        allowed = active and any(path.is_relative_to(parent)
                            for parent in (root / 'tmp', root / 'profile/wp/tmp'))
                        if allowed:
                            self.assertEqual(API['extent'](root, active=True), 0)
                        else:
                            with self.assertRaises((ValueError, FileNotFoundError)):
                                API['extent'](root, active=active)

    def test_unknown_links_and_oversize_worker_console_refuse_even_during_active_poll(self):
        with tempfile.TemporaryDirectory(prefix='probata-move-outer-path-', dir='/private/tmp') as raw:
            root = Path(raw)
            (root / 'tmp').mkdir()
            (root / 'worker.log').write_bytes(b'x' * (API['CONSOLE'] + 1))
            for active in (False, True):
                with self.assertRaises(ValueError):
                    API['extent'](root, active=active)
            (root / 'worker.log').write_bytes(b'')
            (root / 'tmp/link').symlink_to(root / 'worker.log')
            for active in (False, True):
                with self.assertRaises(ValueError):
                    API['extent'](root, active=active)

    def test_inherited_temporary_environment_is_exact_and_ambient_tool_overrides_refuse(self):
        environment = API['child_environment']({'PATH': '/unchanged', 'TMPDIR': '/old'})
        for name in ('TMPDIR', 'TMP', 'TEMP'):
            self.assertEqual(environment[name], str(API['TEMPORARY']))
        self.assertEqual(environment['PATH'], '/unchanged')
        self.assertEqual(environment['PYTHONDONTWRITEBYTECODE'], '1')
        for name in ('WP_IMPORT', 'FRAMAC_WP_CACHE', 'SWDB_FRAMA_C', 'SWDB_VERIFIER_LOCK'):
            with self.assertRaises(ValueError):
                API['child_environment']({name: 'override'})

    def test_outer_rss_latch_and_deadline_fence_cover_imported_process_launches(self):
        helpers = API['load_helpers']()
        gate = API['make_gate'](helpers, None, 720, clock=lambda: 1)
        for memory in (SimpleNamespace(tripped=True, error=None),
                       SimpleNamespace(tripped=False, error='RSS inspection failed')):
            gate.memory = memory
            with self.assertRaises(ValueError):
                gate.call(lambda: self.fail('RSS-failed outer cannot launch a child'))
            with self.assertRaises(ValueError):
                gate.audit('subprocess.Popen', ('compiler', ['compiler'], None, None))
        gate.memory = None
        gate.clock = lambda: 721
        with self.assertRaises(ValueError):
            gate.remaining(30)

    def test_absolute_deadline_interrupts_blocking_work_and_retains_cleanup_failure(self):
        helpers = API['load_helpers']()
        watch = SimpleNamespace(error=None, cleanup_error=None)
        gate = API['make_gate'](helpers, watch, 720, clock=lambda: 12)
        events, handlers = [], []
        fake_signal = SimpleNamespace(ITIMER_REAL=1, SIGALRM=2,
            getitimer=lambda timer: (0.0, 0.0),
            signal=lambda number, handler: (handlers.append(handler) or 'prior-handler'),
            setitimer=lambda timer, duration: events.append(('timer', duration)))
        def cleanup():
            events.append(('cleanup',))
            raise RuntimeError('retained cleanup error')
        with patch.dict(API['deadline_alarm'].__wrapped__.__globals__, {'signal': fake_signal}):
            with self.assertRaises(SystemExit) as stopped:
                with API['deadline_alarm'](gate, cleanup):
                    handlers[0](2, None)
        self.assertEqual(stopped.exception.code, 124)
        self.assertIn(('timer', 708), events)
        self.assertEqual(events[-1], ('timer', 0))
        self.assertEqual(handlers[-1], 'prior-handler')
        self.assertIn('deadline', watch.error)
        self.assertIn('retained cleanup error', watch.cleanup_error)

    def test_complete_child_artifacts_and_false_scientific_boundary_are_required(self):
        with tempfile.TemporaryDirectory(prefix='probata-move-outer-child-', dir='/private/tmp') as raw:
            root = Path(raw)
            profile = root / 'profile'
            profile.mkdir()
            saved = {'source_commit': API['COMMIT'], 'producer_complete': True, 'diagnostic_only': True,
                'public_proof_record_created': False,
                'source_Heap_Typed_lifetime_body_caller_or_default_admission': False,
                'ordinary': 5, 'smokes': 1, 'normal_outcome': {'verdict': 'not_proven'}}
            publication = {'output': str(profile), 'producer_complete': True,
                'source_or_caller_admission': False, 'requires_zero_exit_and_settled_publication': True}
            result = SimpleNamespace(exit_code=0, timed_out=False, out_of_memory=False)
            def install(value):
                (profile / 'result.json').write_text(json.dumps(value))
                data = (profile / 'result.json').read_bytes()
                (profile / 'artifact-manifest.json').write_text(json.dumps([{
                    'relative': 'result.json', 'path': str(profile / 'result.json'),
                    'bytes': len(data), 'sha256': API['sha'](data)}]))
                (root / 'worker.log').write_text(json.dumps(publication))
            install(saved)
            with patch.dict(API['check_child'].__globals__, {'PROFILE': profile}):
                observed = API['check_child'](result, root)
                self.assertEqual(observed['normal_outcome']['verdict'], 'not_proven')
                self.assertFalse(observed['source_or_caller_admission'])
                for key in ('producer_complete', 'public_proof_record_created',
                            'source_Heap_Typed_lifetime_body_caller_or_default_admission'):
                    changed = copy.deepcopy(saved)
                    changed[key] = not changed[key]
                    install(changed)
                    with self.assertRaises(ValueError):
                        API['check_child'](result, root)
                install(saved)
                (profile / 'unlisted').write_bytes(b'extra')
                with self.assertRaises(ValueError):
                    API['check_child'](result, root)

    def test_current_source_packet_and_head_are_checked_before_any_worker(self):
        helpers = API['load_helpers']()
        gate = API['make_gate'](helpers, None, 7200)
        commands = []
        def metadata(unused, *parts):
            commands.append(parts)
            if parts == ('rev-parse', 'HEAD'):
                return (API['COMMIT'] + '\n').encode()
            if parts[0] == 'merge-base':
                return (API['ANCESTOR'] + '\n').encode()
            if parts[0] == 'show':
                relative = parts[1].split(':swdb-project/', 1)[1]
                return (API['PROJECT'] / relative).read_bytes()
            self.fail('unexpected metadata request')
        with patch.dict(API['source_check'].__globals__, {'git': metadata}):
            packet = API['source_check'](gate)
        self.assertEqual(len(packet['source_pins']), 475)
        self.assertEqual(len(commands), 477)
        with patch.dict(API['source_check'].__globals__, {'git': lambda *args: b'stale'}):
            with self.assertRaises(ValueError):
                API['source_check'](gate)


if __name__ == '__main__':
    unittest.main()
