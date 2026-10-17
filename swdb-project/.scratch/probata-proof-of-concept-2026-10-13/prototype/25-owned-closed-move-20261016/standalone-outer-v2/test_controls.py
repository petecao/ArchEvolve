"""2026-10-16 ET. Pure outer guard controls; no actual observation root or tools."""
import copy
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import stat
import sys
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

    def test_post_rss_context_close_delay_and_error_cannot_return_zero(self):
        from swdb import rss_watchdog

        for fault in ('none', 'delay', 'RSS_error'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory(
                    prefix='probata-move-outer-settlement-', dir='/private/tmp') as raw:
                root = Path(raw)
                root.rmdir()  # main itself must exercise exclusive control-root creation.
                clock, timer, closing = [0.0], [False], []
                class Memory:
                    tripped, error, peak = False, None, 1
                    def __enter__(self): return self
                    def __exit__(self, *args):
                        closing.append(timer[0])
                        if fault == 'delay': clock[0] = 721
                        if fault == 'RSS_error': self.error = 'late RSS collector failure'
                @contextmanager
                def alarm(gate, cleanup):
                    timer[0] = True
                    try: yield
                    finally: timer[0] = False
                def worker(*args, **kwargs):
                    kwargs['log'].write_bytes(b'{}')
                    return SimpleNamespace(exit_code=0)
                create_gate = API['make_gate']
                scope = {'ROOT': root, 'PROFILE': root / 'profile', 'TEMPORARY': root / 'tmp',
                    'source_check': lambda gate: None, 'deadline_alarm': alarm,
                    'make_gate': lambda api, watch, deadline: create_gate(
                        api, watch, deadline, clock=lambda: clock[0]),
                    'check_child': lambda *args: {'ordinary': 1, 'smokes': 0}}
                with patch.dict(API['main'].__globals__, scope), \
                        patch.object(API['time'], 'monotonic', return_value=0) as clock_method, \
                        patch.object(API['os'], 'statvfs', return_value=SimpleNamespace(
                            f_bavail=30 * 1024**3, f_frsize=1)), \
                        patch.object(rss_watchdog, 'TreeWatch', return_value=Memory()), \
                        patch.object(rss_watchdog, 'run', side_effect=worker), \
                        patch.object(API['dataclasses'], 'asdict', side_effect=lambda value: {'exit_code': 0}), \
                        redirect_stdout(io.StringIO()):
                    clock_method.side_effect = lambda: clock[0]
                    status = API['main']()
                self.assertEqual(closing, [True], 'absolute timer must remain active through RSS join')
                self.assertEqual(status, int(fault != 'none'))

    def test_deadline_cleanup_uses_real_rss_fallback_shape_through_the_latched_audit(self):
        from swdb import rss_watchdog

        helpers = API['load_helpers']()
        watch = SimpleNamespace(error=None, cleanup_error=None)
        gate = API['make_gate'](helpers, watch, 720, clock=lambda: 1)
        killed, handlers = [], []
        fake_signal = SimpleNamespace(ITIMER_REAL=1, SIGALRM=2,
            getitimer=lambda timer: (0.0, 0.0),
            signal=lambda number, handler: (handlers.append(handler) or 'prior'),
            setitimer=lambda *args: None)
        def fallback(argv, **kwargs):
            # Actual _processes() supplies this argv/cwd/env to subprocess.Popen.
            gate.audit('subprocess.Popen', (argv[0], argv, None, None))
            return SimpleNamespace(stdout='100 1 10\n101 100 20\n')
        def cleanup():
            killed.extend(pid for pid in rss_watchdog.tree(100) if pid != 100)
        with patch.dict(API['deadline_alarm'].__wrapped__.__globals__, {'signal': fake_signal}), \
                patch.dict(sys.modules, {'psutil': None}), \
                patch.object(rss_watchdog.subprocess, 'run', side_effect=fallback):
            with self.assertRaises(SystemExit) as stopped:
                with API['deadline_alarm'](gate, cleanup):
                    handlers[0](2, None)
        self.assertEqual(stopped.exception.code, 124)
        self.assertEqual(killed, [101])
        self.assertIsNone(watch.cleanup_error)
        ps = ('ps', ['ps', '-A', '-o', 'pid=,ppid=,rss='], None, None)
        with self.assertRaises(ValueError): gate.audit('subprocess.Popen', ps)

    def test_main_cleanup_exception_cannot_enable_other_commands_threads_or_later_launches(self):
        helpers = API['load_helpers']()
        gate = API['make_gate'](helpers, SimpleNamespace(error='latched'), 720, clock=lambda: 1)
        exact = ('ps', ['ps', '-A', '-o', 'pid=,ppid=,rss='], None, None)
        with gate.cleanup_snapshot():
            gate.audit('subprocess.Popen', exact)
            for args in (('compiler', ['compiler'], None, None),
                         ('/tmp/ps', exact[1], None, None),
                         ('ps', [*exact[1], 'extra'], None, None),
                         ('ps', exact[1], '/other', None), ('ps', exact[1], None, {})):
                with self.subTest(args=args), self.assertRaises(ValueError):
                    gate.audit('subprocess.Popen', args)
            with self.assertRaises(ValueError):
                gate.audit('os.posix_spawn', exact)
            with patch.object(API['threading'], 'get_ident', return_value=gate.owner_thread + 1):
                with self.assertRaises(ValueError): gate.audit('subprocess.Popen', exact)
        with self.assertRaises(ValueError): gate.audit('subprocess.Popen', exact)
        with patch.object(API['threading'], 'get_ident', return_value=gate.owner_thread + 1):
            with self.assertRaises(ValueError):
                with gate.cleanup_snapshot(): self.fail('foreign cleanup thread entered')


if __name__ == '__main__':
    unittest.main()
