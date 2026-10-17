"""2026-10-16 ET. One original-C move observation's complete outer resource guard.

Source only until independent review, fresh Mac preflight and root once-admission.
The immutable child retains its own normal shared verifier lock and every source,
tool, normal reader and scientific refusal. No proof record is created here.
"""
import dataclasses
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import runpy
import signal
import stat
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
COMMIT = '001df353dc4aa46ab43c395997b760fb2b203ab2'
ANCESTOR = 'b86ea2b931c45e126c61c83f6fe1949aac44e96d'
ENTRY = HERE.parent / 'standalone-v3/entry-001df353.py'
ENTRY_SHA256 = 'f04a21e80b596b1dbfbde05ce2fd1a6e58d52be4d7ab881679218016bf70274b'
PACKET = HERE.parent / 'standalone-v3/source-packet-001df353.json'
PACKET_SHA256 = '03260ea03b19845f88bd5d082871a6b3d1640d352e456717700dfd855a1bbe01'
ROOT = Path('/private/tmp/probata-closed-move-original-b86-v3')
PROFILE = ROOT / 'profile'
TEMPORARY = ROOT / 'tmp'
CAP = 8 * 1024**3
SECONDS = 720
CHILD_SECONDS = 690
AGGREGATE = 128 * 1024**2
CONSOLE = 8192
HEADROOM = 1024**2


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def extent(root, *, active=False):
    """Count all outer files without following links; only private scratch races.

    Why3 sockets and disappearing paths are temporary exceptions only below the
    inherited compiler/parser TMPDIR or the child's exact native TMPDIR. Every
    final scan is strict, including empty directories and worker/outer metadata.
    """
    root = Path(root)
    scratch = (root / 'tmp', root / 'profile/wp/tmp')
    total, pending = 0, [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except FileNotFoundError:
            if active and any(directory.is_relative_to(path) for path in scratch):
                continue
            raise
        for entry in entries:
            path = Path(entry.path)
            private = any(path.is_relative_to(parent) for parent in scratch)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                if active and private:
                    continue
                raise
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                total += metadata.st_size
                if path == root / 'worker.log':
                    need(metadata.st_size <= CONSOLE, 'child console exceeds its 8 KiB bound')
            elif not (active and private and stat.S_ISSOCK(metadata.st_mode)):
                raise ValueError('unknown linked/special outer artifact: ' + str(path))
    return total


def load_helpers():
    need(sha(ENTRY.read_bytes()) == ENTRY_SHA256, 'immutable diagnostic entry changed')
    api = runpy.run_path(str(ENTRY))
    # Only the parent's helper globals change. The child runs the unchanged
    # separately hashed entry in its own process with its original 128 MiB cap.
    values = api['OutputWatch'].loop.__globals__
    values.update(extent=extent, BUDGET=AGGREGATE-CONSOLE, FINAL_HEADROOM=HEADROOM)
    return api


def make_gate(api, watch, deadline, *, clock=time.monotonic):
    class OuterGate(api['ProducerGate']):
        memory = None
        cleanup_thread = None
        owner_thread = threading.get_ident()

        def check(self):
            super().check()
            need(self.memory is None or (not self.memory.tripped and not self.memory.error),
                 'whole outer process-tree RSS guard refused')

        @contextmanager
        def cleanup_snapshot(self):
            need(self.cleanup_thread is None and threading.get_ident() == self.owner_thread,
                 'only the outer main-thread deadline cleanup may inspect RSS after a latch')
            self.cleanup_thread = threading.get_ident()
            try:
                yield
            finally:
                self.cleanup_thread = None

        def audit(self, event, args):
            cleanup_ps = (event == 'subprocess.Popen' and len(args) == 4
                and args[0] == 'ps' and args[1] == ['ps', '-A', '-o', 'pid=,ppid=,rss=']
                and args[2] is None and args[3] is None
                and self.cleanup_thread == threading.get_ident() == self.owner_thread)
            if not cleanup_ps:
                super().audit(event, args)

    return OuterGate(watch, deadline, clock=clock)


@contextmanager
def deadline_alarm(gate, kill_children):
    """Interrupt blocking publication/metadata too, retaining the first failure."""
    duration = gate.remaining(SECONDS)
    need(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0), 'fresh outer interval timer required')

    def expired(number, frame):
        if gate.watch.error is None:
            gate.watch.error = 'whole outer 720-second deadline expired'
        try:
            with gate.cleanup_snapshot():
                kill_children()
        except Exception as error:
            gate.watch.cleanup_error = type(error).__name__ + ': ' + str(error)
        raise SystemExit(124)

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, duration)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def git(gate, *parts):
    return gate.call(subprocess.check_output,
        ['git', '--no-optional-locks', '--no-replace-objects', '-c', 'core.fsmonitor=false',
         '-c', 'core.preloadIndex=false', '-c', 'index.threads=1', '-C', str(PROJECT), *parts],
        timeout=gate.remaining(30))


def source_check(gate):
    need(sha(ENTRY.read_bytes()) == ENTRY_SHA256 and sha(PACKET.read_bytes()) == PACKET_SHA256,
         'immutable diagnostic entry or packet changed')
    packet = json.loads(PACKET.read_bytes())
    need(packet['source_commit'] == COMMIT and packet['entry']['sha256'] == ENTRY_SHA256
         and packet['output'] == str(PROFILE) and len(packet['source_pins']) == 475,
         'exact concrete diagnostic source/entry/output census required')
    need(git(gate, 'rev-parse', 'HEAD').decode().strip() == COMMIT, 'published source HEAD changed')
    need(git(gate, 'merge-base', ANCESTOR, COMMIT).decode().strip() == ANCESTOR,
         'published source no longer retains the accepted source ancestor')
    for row in packet['source_pins']:
        path = PROJECT / row['relative']
        need(not path.is_symlink() and path.is_file(), 'physical source consumer required')
        raw = path.read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256']
             and raw == git(gate, 'show', COMMIT + ':swdb-project/' + row['relative']),
             'selected physical source consumer differs: ' + row['relative'])
    return packet


def child_environment(environment):
    need(not any(name.startswith(('FRAMAC_WP', 'WP_')) or name in
        {'SWDB_FRAMA_C', 'SWDB_OCAMLFIND', 'SWDB_VERIFIER_LOCK', 'SWDB_PROOF_REPORT_OUT'}
        for name in environment), 'ambient verifier/lock selector refused')
    return {**environment, 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(TEMPORARY),
            'TMP': str(TEMPORARY), 'TEMP': str(TEMPORARY),
            'SWDB_VERIFIER_RSS_CAP_BYTES': str(CAP)}


def check_child(result, root):
    """Require the completed diagnostic; never adopt its mathematical verdict."""
    need(result.exit_code == 0 and not result.timed_out and not result.out_of_memory,
         'original-C observation did not complete within its outer guards')
    console = (root / 'worker.log').read_bytes()
    need(len(console) <= CONSOLE, 'bounded child console required')
    publication = json.loads(console)
    need(publication.get('output') == str(PROFILE) and publication.get('producer_complete') is True
         and publication.get('source_or_caller_admission') is False
         and publication.get('requires_zero_exit_and_settled_publication') is True,
         'child settled publication is incomplete')
    saved = json.loads((PROFILE / 'result.json').read_bytes())
    need(saved.get('source_commit') == COMMIT and saved.get('producer_complete') is True
         and saved.get('diagnostic_only') is True and saved.get('public_proof_record_created') is False
         and saved.get('source_Heap_Typed_lifetime_body_caller_or_default_admission') is False,
         'child result changed its diagnostic-only boundary')
    manifest = json.loads((PROFILE / 'artifact-manifest.json').read_bytes())
    need(isinstance(manifest, list), 'complete physical child manifest required')
    by_name = {row['relative']: row for row in manifest}
    names = {str(path.relative_to(PROFILE)) for path in PROFILE.rglob('*') if path.is_file()}
    need(len(by_name) == len(manifest) and names == set(by_name) | {'artifact-manifest.json'},
         'complete settled child artifact membership differs')
    for name, row in by_name.items():
        path = PROFILE / name
        need(row['path'] == str(path) and path.is_relative_to(PROFILE)
             and not path.is_symlink(), 'child artifact path escaped its exact profile')
        raw = path.read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'settled child artifact changed')
    return {'ordinary': saved['ordinary'], 'smokes': saved['smokes'],
            'normal_outcome': saved.get('normal_outcome'),
            'normal_reader_refusal': saved.get('normal_reader_refusal'),
            'child_artifacts': len(manifest) + 1,
            'source_or_caller_admission': False}


def main():
    started = time.monotonic()
    sys.dont_write_bytecode = True
    api = load_helpers()
    gate = make_gate(api, None, started + SECONDS)
    sys.addaudithook(gate.audit)
    need(ROOT.parent == Path('/private/tmp') and ROOT.parent.resolve() == ROOT.parent
         and not os.path.lexists(ROOT), 'fresh canonical outer root required')
    need(os.statvfs(ROOT.parent).f_bavail * os.statvfs(ROOT.parent).f_frsize >= 20 * 1024**3,
         'complete outer root requires 20 GiB free disk')
    source_check(gate)
    environment = child_environment(dict(os.environ))
    sys.path.insert(0, str(PROJECT))
    from swdb import rss_watchdog
    ROOT.mkdir(mode=0o700)
    TEMPORARY.mkdir(mode=0o700)

    def kill_children():
        for pid in rss_watchdog.tree(os.getpid()):
            if pid != os.getpid():
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    watcher = api['OutputWatch'](ROOT, kill_children)
    gate.watch = watcher
    result = {'created': '2026-10-16 ET', 'source_commit': COMMIT, 'producer_complete': False,
        'diagnostic_only': True, 'public_proof_record_created': False,
        'source_Heap_Typed_lifetime_body_caller_or_default_admission': False,
        'whole_aggregate_limit_bytes': AGGREGATE, 'console_limit_bytes': CONSOLE,
        'RSS_cap_bytes': CAP, 'whole_seconds': SECONDS,
        'temporary_roots': [str(TEMPORARY), str(PROFILE / 'wp/tmp')],
        'resource_boundary': 'sampled aggregate output and RSS; explicit OS/loader/interposition TCB; no kernel hard-quota or continuous source/runtime guarantee'}
    memory = rss_watchdog.TreeWatch(os.getpid(), CAP, spare_root=True)
    gate.memory = memory
    with deadline_alarm(gate, kill_children):
        with memory:
            try:
                with watcher:
                    gate.check()
                    command = [sys.executable, '-B', str(ENTRY)]
                    api['write'](ROOT, ROOT / 'outer-command.json', api['encoded']({
                        'argv': command, 'cwd': str(PROJECT), 'entry_sha256': ENTRY_SHA256,
                        'packet_sha256': PACKET_SHA256, 'inherited_TMPDIR': str(TEMPORARY),
                        'outer_seconds': SECONDS, 'child_seconds': CHILD_SECONDS,
                        'RSS_cap_bytes': CAP, 'aggregate_bytes': AGGREGATE, 'workers': 1}))
                    observed = gate.call(rss_watchdog.run, command, log=ROOT / 'worker.log',
                        cwd=PROJECT, env=environment, cap_bytes=CAP, timeout=gate.remaining(CHILD_SECONDS))
                    result['child_resources'] = dataclasses.asdict(observed)
                    gate.check()
                    extent(ROOT)
                    result.update(check_child(observed, ROOT))
                    source_check(gate)
                    gate.check()
                    result['producer_complete'] = True
            except Exception as error:
                result.update(error_type=type(error).__name__, error=str(error))
            finally:
                result.update(output_guard_error=watcher.error, output_cleanup_error=watcher.cleanup_error,
                              whole_peak_rss_bytes=memory.peak, whole_RSS_tripped=memory.tripped,
                              whole_RSS_error=memory.error)
                try:
                    result['finalized'] = api['finalize'](ROOT, result, gate, started)
                except Exception as error:
                    result.update(producer_complete=False,
                                  finalization_error=type(error).__name__ + ': ' + str(error))
        # The interval timer remains active during the RSS collector's join.
        # A complete-looking result/publication is insufficient without this
        # final clock, strict aggregate and late RSS-error gate after close.
        try:
            gate.check()
            need(extent(ROOT) <= AGGREGATE-CONSOLE, 'settled outer aggregate exceeded after RSS close')
            gate.check()
        except Exception as error:
            result.update(producer_complete=False,
                finalization_error=type(error).__name__ + ': ' + str(error))
            if memory.error and not result.get('error'):
                result['error'] = memory.error
        result.update(whole_peak_rss_bytes=memory.peak, whole_RSS_tripped=memory.tripped,
                      whole_RSS_error=memory.error)
        return api['publish'](ROOT, result, gate)



if __name__ == '__main__':
    raise SystemExit(main())
