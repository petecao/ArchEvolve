"""gem5 entry wrapper: seal the BFS ROI, then resume its verifier.

Updated: 2026-09-25. Executed by the pinned gem5 embedded Python interpreter.
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
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def main():
    root = Path(os.environ["SWDB_DX100_MODEL_ROOT"])
    entry = root / "configs/deprecated/example/se.py"
    folder = Path(m5.options.outdir)
    observer_path = Path(__file__).with_name('dx100_host_memory.py')
    observer = runpy.run_path(str(observer_path))['Observer'](folder)
    observer.write('wrapper_start', observer_sha256=digest(observer_path))
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
    receipt = {
        "format": "swdb.dx100.roi-seal.v1",
        "execution_binding_sha256": os.environ["SWDB_DX100_EXECUTION_BINDING_SHA256"],
        "driver_sha256": digest(Path(__file__)),
        "roi_exit_tick": int(m5.curTick()),
        "roi_exit_cause": last.getCause(),
        "statistics": {"path": str(sealed), "sha256": digest(sealed)},
        "verification": {"state": "running", "max_ticks": int(os.environ["SWDB_DX100_VERIFY_MAX_TICKS"])},
    }
    save(folder / "roi-seal.json", receipt)
    print("SWDB_DX100_ROI_SEALED", flush=True)
    # This is the same instantiated machine and guest address space. It resumes
    # immediately after the m5_exit and returns the exact timed parent array.
    observer.write('verification_begin')
    event = original(receipt["verification"]["max_ticks"])
    observer.write('verification_end', cause=event.getCause(), tick=int(m5.curTick()))
    receipt["verification"].update(state="finished", exit_tick=int(m5.curTick()),
        exit_cause=event.getCause(), exit_code=int(event.getCode()))
    save(folder / "roi-seal.json", receipt)
    print("SWDB_DX100_VERIFICATION_END " + json.dumps(receipt["verification"], sort_keys=True), flush=True)
    # Keep the transparent dump hook installed through gem5's final exit dump.


main()
