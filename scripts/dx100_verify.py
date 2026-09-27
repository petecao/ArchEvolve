"""gem5 entry wrapper: seal the BFS ROI, then resume its verifier.

Updated: 2026-09-27. Executed by the pinned gem5 embedded Python interpreter.
2026-09-27 (R12): an opt-in post-ROI CPU treatment switches the same machine's
O3 CPUs to its restore AtomicSimpleCPUs after the ROI statistics are sealed, so
only the verifier continuation runs in atomic mode. Without the variable the
behavior is unchanged.
"""

import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys

import m5


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def save(path, data):
    # Load the same standalone serializer used by downstream seal consumers.
    serializer = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'swdb/dx100_witness.py'))['seal_bytes']
    raw = serializer(data)
    pending = path.with_suffix(".pending")
    with pending.open('wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    pending.replace(path)
    directory = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main():
    checker = os.environ.get('SWDB_DX100_CHECKER', 'dx100.bfs.verifier.v1')
    if checker not in {'dx100.bfs.verifier.v1', 'dx100.bfs.verifier.v2'}:
        raise RuntimeError('unsupported verification contract')
    witnessed = checker == 'dx100.bfs.verifier.v2'
    trace = os.environ.get('SWDB_DX100_POST_ROI_TRACE')
    if trace is not None and trace != 'SyscallBase':
        raise RuntimeError('unsupported post-ROI trace flag')
    if witnessed and trace != 'SyscallBase':
        raise RuntimeError('v2 verification requires its explicit post-ROI SyscallBase trace')
    post_cpu = os.environ.get('SWDB_DX100_POST_ROI_CPU')
    if post_cpu is not None and (post_cpu != 'AtomicSimpleCPU' or not witnessed):
        raise RuntimeError('unsupported post-ROI CPU treatment')
    root = Path(os.environ["SWDB_DX100_MODEL_ROOT"])
    entry = root / "configs/deprecated/example/se.py"
    folder = Path(m5.options.outdir)
    observer_path = Path(__file__).with_name('dx100_host_memory.py')
    observer_sha256 = digest(observer_path)
    observer = runpy.run_path(str(observer_path))['Observer'](folder)
    observer.write('wrapper_start', observer_sha256=observer_sha256)
    last = None
    original = m5.simulate
    original_instantiate = getattr(m5, 'instantiate', None)
    stats_module = getattr(m5, 'stats', None)
    original_dump = getattr(stats_module, 'dump', None)

    def instantiate(*args, **kwargs):
        observer.write('instantiate_begin')
        result = original_instantiate(*args, **kwargs)
        observer.write('instantiate_end')
        from m5.objects import Root
        observer.requestors(Root.getInstance())
        return result

    def dump(*args, **kwargs):
        observer.write('statistics_dump_begin')
        result = original_dump(*args, **kwargs)
        observer.write('statistics_dump_end')
        return result

    def observe(*args, **kwargs):
        nonlocal last
        observer.write('simulate_begin')
        last = original(*args, **kwargs)
        observer.write('simulate_end', cause=last.getCause(), tick=int(m5.curTick()))
        return last

    m5.simulate = observe
    if original_instantiate:
        m5.instantiate = instantiate
    if original_dump:
        stats_module.dump = dump
    try:
        sys.argv[0] = str(entry)
        # m5.util.addToPath resolves relative config imports against sys.path[0],
        # which gem5 initially sets to this wrapper's directory.
        sys.path[0] = str(entry.parent)
        runpy.run_path(str(entry), run_name="__m5_main__")
    finally:
        m5.simulate = original
        if original_instantiate:
            m5.instantiate = original_instantiate
    if last is None or last.getCause() != "m5_exit instruction encountered" or last.getCode() != 0:
        raise RuntimeError("the timed guest did not reach its expected ROI exit")
    stats = folder / "stats.txt"
    sealed = folder / "roi-stats.txt"
    # The pinned Text::end flushes each guest dump. Never request another dump:
    # that would extend the intended interval beyond m5_dump_stats in BFS.
    shutil.copyfile(stats, sealed)
    with sealed.open('rb') as stream:
        os.fsync(stream.fileno())
    receipt = {
        "format": "swdb.dx100.roi-seal.v1",
        "execution_binding_sha256": os.environ["SWDB_DX100_EXECUTION_BINDING_SHA256"],
        "driver_sha256": digest(Path(__file__)),
        "host_memory_observer_sha256": observer_sha256,
        "roi_exit_tick": int(m5.curTick()),
        "roi_exit_cause": last.getCause(),
        "statistics": {"path": str(sealed), "sha256": digest(sealed)},
        "verification": {"state": "running", "max_ticks": int(os.environ["SWDB_DX100_VERIFY_MAX_TICKS"])},
    }
    if witnessed:
        parser_path = Path(__file__).resolve().parents[1] / 'swdb/dx100_witness.py'
        parser_sha256 = digest(parser_path)
        parse_trace = runpy.run_path(str(parser_path))['parse_trace']
        receipt['verification_parser'] = {'path': str(parser_path), 'sha256': parser_sha256}
        receipt['verification'].update(checker=checker, parser_sha256=parser_sha256, chunk_ticks=10**9,
            normal_exit_observed=False, stop_reason='running', simulated_ticks=0)
    save(folder / "roi-seal.json", receipt)
    print("SWDB_DX100_ROI_SEALED", flush=True)
    if trace:
        # The immutable interval and its receipt are durable before the flag is
        # enabled. v1 uses the existing log; v2 has a separate bounded stream.
        from m5 import debug
        enable_tick = int(m5.curTick())
        if witnessed:
            from m5 import trace as trace_module
            trace_path = folder / 'post-roi-syscalls.log'
            if trace_path.exists() or trace_path.is_symlink():
                raise RuntimeError('post-ROI trace output must be a new file')
            for name in ('MAATrace', 'MAARangeFuser', 'MAAIndirect'):
                debug.flags[name].disable()
            for name in ('FmtTicksOff', 'FmtStackTrace'):
                debug.flags[name].disable()
            trace_module.output(str(trace_path))
            debug.flags['FmtFlag'].enable()
        debug.flags[trace].enable()
        receipt['verification']['post_roi_trace'] = {
            'flag': trace, 'enabled_tick': enable_tick,
            'scope': 'post-seal verifier continuation only', 'output': 'simulation_log'}
        if witnessed:
            receipt['verification']['post_roi_trace'].update(path=str(trace_path),
                output='separate_simulator_trace', format_flags=['FmtFlag'],
                disabled_format_flags=['FmtTicksOff', 'FmtStackTrace'],
                disabled_roi_flags=['MAATrace', 'MAARangeFuser', 'MAAIndirect'])
        save(folder / 'roi-seal.json', receipt)
        print('SWDB_DX100_POST_ROI_TRACE ' + json.dumps(
            receipt['verification']['post_roi_trace'], sort_keys=True), flush=True)
    timed = ['system.switch_cpus' + str(index) for index in range(4)]
    caller, allowed = timed[0], list(timed)
    if post_cpu:
        # R12: the sealed interval is closed; the verifier continuation alone
        # moves to the same system's switched-out restore CPUs (atomic memory).
        from m5.objects import Root
        system = Root.getInstance().system
        pairs = list(zip(system.switch_cpus, system.cpu))
        restore = ['system.cpu' + str(index) for index in range(4)]
        if (len(pairs) != 4 or [old.path() for old, _ in pairs] != timed
                or [new.path() for _, new in pairs] != restore
                or any(old.switchedOut() or not new.switchedOut() for old, new in pairs)
                or any(new.memory_mode() != 'atomic' for _, new in pairs)):
            raise RuntimeError('post-ROI CPU switch requires the four active timed and restore CPUs')
        observer.write('post_roi_cpu_switch_begin', tick=int(m5.curTick()))
        m5.switchCpus(system, pairs, verbose=False)
        switched = int(m5.curTick())
        observer.write('post_roi_cpu_switch_end', tick=switched)
        receipt['verification']['post_roi_cpu'] = {
            'type': post_cpu, 'memory_mode': 'atomic', 'from': timed, 'to': restore,
            'requested_tick': enable_tick, 'switched_tick': switched,
            'scope': 'post-seal verifier continuation only'}
        caller, allowed = restore[0], timed + restore
        save(folder / 'roi-seal.json', receipt)
        print('SWDB_DX100_POST_ROI_CPU ' + json.dumps(receipt['verification']['post_roi_cpu'], sort_keys=True),
              flush=True)
    # This is the same instantiated machine and guest address space. It resumes
    # immediately after the m5_exit and returns the exact timed parent array.
    observer.write('verification_begin')
    if witnessed:
        terminal = receipt['verification']
        # Count from the sealed ROI exit, so a post-ROI CPU switch that drains
        # the machine is inside the continuation interval (identical otherwise).
        start_tick = enable_tick
        while terminal['simulated_ticks'] < terminal['max_ticks']:
            before_tick = int(m5.curTick())
            allowance = min(terminal['chunk_ticks'], terminal['max_ticks'] - terminal['simulated_ticks'])
            event = original(allowance)
            end_tick = int(m5.curTick())
            terminal['simulated_ticks'] = end_tick - start_tick
            if end_tick < before_tick or end_tick - before_tick > allowance:
                raise RuntimeError('post-ROI simulation exceeded its declared tick interval')
            witness = parse_trace(trace_path, enabled_tick=enable_tick, end_tick=end_tick,
                expected_cpu=caller, expected_thread=0, allowed_cpus=allowed, allow_incomplete=True)
            terminal['post_roi_trace']['sha256'] = witness['trace']['sha256']
            terminal['post_roi_trace']['bytes'] = witness['trace']['bytes']
            terminal['normal_exit_observed'] = (event.getCause() == 'exiting with last active thread context'
                                                and event.getCode() == 0)
            if witness['completed']:
                terminal['exit_witness'] = witness
            if terminal['normal_exit_observed']:
                terminal['stop_reason'] = 'normal_exit'
                break
            if witness['completed']:
                terminal['stop_reason'] = 'exit_witness'
                break
            if event.getCause() != 'simulate() limit reached' or event.getCode() != 0 or end_tick == before_tick:
                terminal['stop_reason'] = 'unexpected_event'
                break
        else:
            terminal['stop_reason'] = 'tick_limit'
        if digest(parser_path) != parser_sha256:
            raise RuntimeError('verification parser changed during execution')
    else:
        event = original(receipt["verification"]["max_ticks"])
    observer.write('verification_end', cause=event.getCause(), tick=int(m5.curTick()))
    receipt["verification"].update(state="finished", exit_tick=int(m5.curTick()),
        exit_cause=event.getCause(), exit_code=int(event.getCode()))
    save(folder / "roi-seal.json", receipt)
    print("SWDB_DX100_VERIFICATION_END " + json.dumps(receipt["verification"], sort_keys=True), flush=True)
    # Keep the transparent dump hook installed through gem5's final exit dump.


main()
