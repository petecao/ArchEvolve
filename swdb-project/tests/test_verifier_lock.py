"""The machine-wide verifier lock admits at most N jobs (Yan-Ru, 2026-10-14: two slots on the Mac)."""

import subprocess
import sys
import textwrap
import time
from pathlib import Path

from swdb import verifier_lock

ROOT = Path(__file__).resolve().parents[1]

JOB = textwrap.dedent("""
    import sys, time
    sys.path.insert(0, {root!r})
    from swdb import verifier_lock as vl
    with vl.hold("job" + sys.argv[1], sys.argv[2]) as h:
        print("in", time.time(), h["lock"], flush=True)
        time.sleep(0.6)
        print("out", time.time(), flush=True)
""")


def _peak(tmp_path, slots, jobs=4):
    lock = tmp_path / "v.lock"
    (tmp_path / "v.slots").write_text(f"{slots}\n")
    script = tmp_path / "job.py"
    script.write_text(JOB.format(root=str(ROOT)))
    procs = []
    for i in range(jobs):
        procs.append(subprocess.Popen([sys.executable, str(script), str(i), str(lock)],
                                      stdout=subprocess.PIPE, text=True))
        time.sleep(0.05)
    events, used = [], set()
    for p in procs:
        out, _ = p.communicate(timeout=60)
        for line in out.splitlines():
            kind, stamp, *rest = line.split()
            events.append((float(stamp), kind))
            if rest:
                used.add(Path(rest[0]).name)
    events.sort()
    now = peak = 0
    for _, kind in events:
        now += 1 if kind == "in" else -1
        peak = max(peak, now)
    return peak, used


def test_one_slot_runs_jobs_one_at_a_time(tmp_path):
    peak, used = _peak(tmp_path, 1)
    assert peak == 1 and used == {"v.lock"}


def test_two_slots_run_at_most_two_jobs_at_once(tmp_path):
    peak, used = _peak(tmp_path, 2)
    assert peak == 2 and used == {"v.lock", "v.slot2.lock"}


def test_missing_or_bad_policy_file_means_one_slot(tmp_path):
    lock = tmp_path / "v.lock"
    assert verifier_lock.slots(lock) == 1
    (tmp_path / "v.slots").write_text("zero\n")
    assert verifier_lock.slots(lock) == 1
    (tmp_path / "v.slots").write_text("0\n")
    assert verifier_lock.slots(lock) == 1


def test_a_job_inside_the_holders_tree_takes_the_nested_lock(tmp_path):
    lock = tmp_path / "v.lock"
    with verifier_lock.hold("outer", lock) as outer:
        assert not outer["nested"]
        code = (f"import sys; sys.path.insert(0, {str(ROOT)!r}); from swdb import verifier_lock as vl\n"
                f"with vl.hold('inner', {str(lock)!r}) as h: print(h['nested'], h['lock'])")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30).stdout
    assert out.split() == ["True", str(lock / "nested")]
