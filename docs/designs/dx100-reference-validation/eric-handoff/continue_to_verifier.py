"""gem5 config wrapper: freeze the explicit BFS ROI dump, then finish verification.

Runs unchanged pinned se.py/BFS. A normal guest exit and BFSVerifier PASS are
separate observations; the existing collector must still check the guest output.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys

COUNTERS = ("system.maa.numInst_INDRD", "system.maa.numInst_RANGE")
BEGIN = "---------- Begin Simulation Statistics ----------"
END = "---------- End Simulation Statistics   ----------"
NORMAL_EXIT = "exiting with last active thread context"


def freeze_roi(raw, read_counter):
    """Preserve one complete dump; expose actual registered zeros separately."""
    if raw.count(BEGIN) != 1 or raw.count(END) != 1 or raw.index(BEGIN) > raw.index(END):
        raise ValueError("Expected exactly one complete explicit ROI dump before verification")
    values = {}
    for line in raw.splitlines():
        fields = line.split()
        if fields and fields[0] in COUNTERS:
            if fields[0] in values:
                raise ValueError("Duplicate ROI instruction counter")
            values[fields[0]] = float(fields[1])
    actual, additions = {}, []
    for name in COUNTERS:
        value = read_counter(name)  # Missing registration is an error, never zero.
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or int(value) != value:
            raise ValueError("Invalid registered instruction counter: " + name)
        actual[name] = value
        if name in values:
            if values[name] != value:
                raise ValueError("ROI dump and registered counter differ: " + name)
        elif value == 0:
            additions.append(name + " 0 # explicit registered zero; stock text output suppresses zero\n")
        else:
            raise ValueError("Positive registered counter missing from explicit ROI dump: " + name)
    projection = raw.replace(END, "".join(additions) + END)
    return projection, actual


def continue_after_roi(original, m5, read_counter, outdir, verify_ticks, events, *args, **kwargs):
    if type(verify_ticks) is not int or verify_ticks <= 0:
        raise ValueError("A positive finite verification tick budget is required")
    first = original(*args, **kwargs)
    events.append({"role": "roi_exit", "cause": first.getCause(), "code": first.getCode(), "tick": m5.curTick()})
    if first.getCause() != "m5_exit instruction encountered" or first.getCode() != 0:
        raise ValueError("Expected the single-trial BFS ROI m5_exit before continuation")
    stats_path = outdir / "stats.txt"
    raw_bytes = stats_path.read_bytes()
    projection, actual = freeze_roi(raw_bytes.decode(), read_counter)
    for name in ("roi.stats.txt", "roi.stats.explicit-counters.txt", "roi-counter-values.json"):
        if (outdir / name).exists():
            raise ValueError("Preserve existing ROI snapshots; use a fresh output directory")
    (outdir / "roi.stats.txt").write_bytes(raw_bytes)
    (outdir / "roi.stats.explicit-counters.txt").write_text(projection)
    snapshot = {"snapshot_tick": m5.curTick(), "instruction_counters": actual,
                "raw_roi_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "projected_roi_sha256": hashlib.sha256(projection.encode()).hexdigest(),
                "method": "Read actual registered ScalarInfo.value after guest ROI dump. Only omitted, registered zero instruction counters are appended; no reset or extra dump is issued."}
    (outdir / "roi-counter-values.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    # Respect the original run's remaining time budget as well as the explicit
    # continuation budget. benchCheckpoints(options, maxtick, cptdir) is pinned.
    maxtick = args[1] if len(args) >= 2 else kwargs.get("maxtick")
    if maxtick is not None:
        verify_ticks = min(verify_ticks, int(maxtick) - int(m5.curTick()))
    if verify_ticks <= 0:
        raise ValueError("No simulated ticks remain for verification")
    final = m5.simulate(verify_ticks)
    events.append({"role": "post_roi_guest_exit", "cause": final.getCause(), "code": final.getCode(), "tick": m5.curTick()})
    if final.getCause() != NORMAL_EXIT or final.getCode() != 0:
        raise ValueError("Verification continuation did not reach a normal zero-code guest exit")
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dx100-source-root", type=Path, required=True)
    parser.add_argument("--verify-max-ticks", type=int, required=True)
    if "--" not in sys.argv:
        parser.error("Separate wrapper options from stock se.py options with --")
    split = sys.argv.index("--")
    options = parser.parse_args(sys.argv[1:split])
    if options.verify_max_ticks <= 0:
        parser.error("--verify-max-ticks must be positive")
    se_args = sys.argv[split + 1:]
    source = options.dx100_source_root.resolve()
    sys.path.insert(0, str(source / "configs"))
    import m5
    from m5.objects import Root
    from common import Simulation

    outdir = Path(m5.options.outdir).resolve()
    events, hooked, completed = [], [], False
    original = Simulation.benchCheckpoints

    def registered_counter(name):
        stat = Root.getInstance().resolveStat(name)
        if stat is None:
            raise ValueError("Required registered counter is absent: " + name)
        return stat.value

    def hook(*args, **kwargs):
        if hooked:
            raise ValueError("Expected one benchCheckpoints call")
        hooked.append(True)
        return continue_after_roi(original, m5, registered_counter, outdir,
                                  options.verify_max_ticks, events, *args, **kwargs)

    Simulation.benchCheckpoints = hook
    target = source / "configs/deprecated/example/se.py"
    sys.argv = [str(target), *se_args]
    try:
        runpy.run_path(str(target), run_name="__m5_main__")
        if not hooked or len(events) != 2:
            raise ValueError("The required ROI/verification event chain was not observed")
        completed = True
    finally:
        Simulation.benchCheckpoints = original
        receipt = {"guest_completed": completed, "events": events,
                   "verification_status": "Requires exactly one BFSVerifier PASS in guest output; normal exit alone is insufficient.",
                   "roi_stats": "roi.stats.explicit-counters.txt", "stats_block_index": 0,
                   "raw_roi_stats": "roi.stats.txt", "counter_snapshot": "roi-counter-values.json",
                   "wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "exit-events.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ in ("__main__", "__m5_main__"):
    main()
