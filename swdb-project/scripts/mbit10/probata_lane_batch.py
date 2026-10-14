"""Write the batch plans of Probata ticket 57's mbit10 run (proof workers in a socket lane).

Created: 2026-10-14 ET. Run with the swdb test venv (the seed builder imports the test kit):

  PY=/data1/yanruj/venvs/swdb-test/bin/python
  $PY scripts/mbit10/probata_lane_batch.py seed <run>/seed            # certified fixture candidate
  $PY scripts/mbit10/probata_lane_batch.py plans <run> --seed <run>/seed [--probe <probe batch.json>]
  bash scripts/mbit10/prove_in_lane.sh 1 <run>/probe.yaml  --records <run>/seed/records   # ulimit -v probe
  bash scripts/mbit10/prove_in_lane.sh 1 <run>/batch.yaml  --records <run>/seed/records   # 6 workers
  bash scripts/mbit10/prove_in_lane.sh 1 <run>/alone.yaml  --records <run>/seed/records   # the same, 1 worker
  bash scripts/mbit10/prove_in_lane.sh 1 <run>/oom.yaml    --records <run>/seed/records   # watchdog control

Plans:
- probe.yaml: each lineup tool from ticket 56 runs its safe smoke program once under an 8 GB
  `ulimit -v` (address_space_cap); a tool that gives its expected verdict "starts under the cap".
- batch.yaml: 07's smoke programs (CBMC, crux-llvm, Frama-C/WP; safe and seeded bug) in two
  configurations (A: each tool's default solver path; B: an alternative one), 12 tool jobs, plus 4
  scripted `swdb prove` jobs (2 configurations); written GROUPED (all A first), so the batch reorders
  it and records that. The cap goes only on tools the probe saw start under it.
- alone.yaml: the same jobs with 1 worker (each job runs alone), for `swdb prove-lane compare`.
- oom.yaml: a tool job and a `swdb prove` job that each climb past 8 GB beside 4 calm jobs.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

HOME = Path(__file__).resolve().parents[2]
SMOKE07 = HOME / ".scratch/formal-verification-2026-10-09/prototype/07-smoke"
SMOKE03 = HOME / ".scratch/probata-proof-of-concept-2026-10-13/prototype/03-smoke"
ENV = ". /data1/yanruj/probata-verifiers/env.sh && "
FUNCTION = "DOBFS"
ASSUMPTION = {"kind": "trusted_tool", "reference": {"id": "clang-22.1.8", "sha256": "a" * 64},
              "sentence": "clang 22.1.8 compiles the proof unit correctly."}
GIB = 1024 ** 3


def _bug(variant):
    return " -DBUGGY" if variant == "buggy" else ""


def _cbmc(variant, config):
    solver = "" if config == "A" else " --z3"
    return {"command": ["bash", "-c", f"{ENV}cbmc --trace{solver}{_bug(variant)} smoke.c"],
            "inputs": ["inputs/smoke.c"], "tool": "cbmc",
            "verdicts": [{"verdict": "proven", "exit": 0, "output": "VERIFICATION SUCCESSFUL"},
                         {"verdict": "refuted", "exit": 10, "output": "VERIFICATION FAILED",
                          "counterexample": r"^\s+(x|y)=-?\d"}]}


def _crux(variant, config):
    mode = "" if config == "A" else " --force-offline-goal-solving"
    return {"command": ["bash", "-c", f"{ENV}clang++ --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 -c -emit-llvm "
                                      f"-g -I$CRUX/c-src/includes{_bug(variant)} smoke_crux.cpp -o smoke_crux.bc && "
                                      f"crux-llvm --no-compile --solver=z3{mode} --output-directory=out "
                                      f"$PWD/smoke_crux.bc"],
            "inputs": ["inputs/smoke_crux.cpp"], "tool": "crux-llvm",
            "verdicts": [{"verdict": "proven", "exit": 0, "output": "Overall status: Valid"},
                         {"verdict": "refuted", "output": "Overall status: Invalid",
                          "counterexample": r"Counterexample|x\b|failed"}]}


def _wp(variant, config):
    prover = "alt-ergo" if config == "A" else "z3"
    extra = " -cpp-extra-args=-DBUGGY" if variant == "buggy" else ""
    return {"command": ["bash", "-c", f"{ENV}eval \"$(opam env --switch=framac-33 --set-switch)\" && frama-c "
                                      f"-machdep x86_64 -wp -wp-rte -wp-cache none -wp-prover {prover} -wp-par 1"
                                      f"{extra} smoke_wp.c"],
            "inputs": ["inputs/smoke_wp.c"], "tool": "frama-c-wp",
            "verdicts": [{"verdict": "proven", "exit": 0, "output": r"Proved goals:\s+(\d+) / \1\b"},
                         {"verdict": "not_proven", "exit": 0, "output": "Timeout",
                          "failure_class": "timeout"},
                         {"verdict": "not_proven", "exit": 0, "output": "Proved goals:", "failure_class": "unknown"}]}


SUBJECT_TOOLS = {"cbmc": _cbmc, "crux": _crux, "wp": _wp}

PROBES = {   # tool -> (command, inputs, expected output) of its safe smoke program (ticket 56's smoke.sh)
    "cbmc": _cbmc("safe", "A"), "crux-llvm": _crux("safe", "A"), "frama-c-wp": _wp("safe", "A"),
    "saw": {"command": ["bash", "-c", f"{ENV}clang -c -emit-llvm -g -O0 smoke_saw.c -o smoke_saw.bc && "
                                      "PATH=$SAWBIN:$PATH saw smoke_saw.saw"],
            "inputs": ["inputs/smoke_saw.c", "inputs/smoke_saw.saw"],
            "verdicts": [{"verdict": "proven", "exit": 0, "output": "Proof succeeded! smoke"}]},
    "civl": {"command": ["bash", "-c", f"{ENV}mkdir -p jtmp && $JAVA -Xmx4g -Djava.io.tmpdir=$PWD/jtmp "
                                       "-Duser.home=$HOME -jar $CIVL_JAR verify smoke_civl.c"],
             "inputs": ["inputs/smoke_civl.c"],
             "verdicts": [{"verdict": "proven", "exit": 0, "output": "All errors marked with '\\+' are absent"}]},
    "genmc": {"command": ["bash", "-c", f"{ENV}$GENMC --rc11 --print-error-trace -- smoke_genmc.c"],
              "inputs": ["inputs/smoke_genmc.c"],
              "verdicts": [{"verdict": "proven", "exit": 0, "output": "No errors were detected\\."}]},
    "rocq": {"command": ["bash", "-c", f"{ENV}eval \"$(opam env --switch=rocq-9 --set-switch)\" && "
                                       "rocq compile smoke_rocq_true.v"],
             "inputs": ["inputs/smoke_rocq_true.v"],
             "verdicts": [{"verdict": "proven", "exit": 0, "output": "Closed under the global context"}]},
    "z3": {"command": ["bash", "-c", f"{ENV}z3 --version"],
           "verdicts": [{"verdict": "proven", "exit": 0, "output": "Z3 version 5\\.1\\.0"}]},
    "cvc5": {"command": ["bash", "-c", f"{ENV}cvc5 --version"],
             "verdicts": [{"verdict": "proven", "exit": 0, "output": "cvc5 version 1\\.2\\.1"}]},
}


def seed(args):
    sys.path.insert(0, str(HOME / "tests"))
    os.environ.setdefault("SWDB_FIXTURE_HOST", "swdb-fixture-host")     # build the seed as the fixture host
    from test_proof_records import build_proof_seed
    args.folder.mkdir(parents=True)
    candidate = build_proof_seed(args.folder)
    (args.folder / "candidate.txt").write_text(candidate + "\n")
    print(json.dumps({"seed": str(args.folder), "candidate": candidate}))


def _alloc(gib):
    return ["python3", "-c",
            f"import time\nb=[]\nfor _ in range({int(gib * 10)}):\n b.append(b'\\x01'*(100*1024*1024))\n"
            " time.sleep(0.05)\ntime.sleep(2)\nprint('done')"]


def _tool_job(config, subject, spec, cap=False):
    tool = {key: value for key, value in spec.items() if key != "tool"}
    tool.update(bounds={"threads": 1}, address_space_cap=cap)
    return {"configuration": config, "subject": subject, "tool": tool}


def plans(args):
    run = args.run.resolve()
    inputs = run / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for name in ("smoke.c", "smoke_crux.cpp", "smoke_wp.c"):
        shutil.copy2(SMOKE07 / name, inputs / name)
    for name in ("smoke_saw.c", "smoke_saw.saw", "smoke_civl.c", "smoke_genmc.c", "smoke_rocq_true.v"):
        shutil.copy2(SMOKE03 / name, inputs / name)
    candidate = (args.seed / "candidate.txt").read_text().strip()
    capped = set()
    if args.probe:
        probe = json.loads(args.probe.read_text())
        capped = {job["subject"] for job in probe["jobs"] if job.get("verdict") == "proven"}
    scripts = run / "scripts"
    scripts.mkdir(exist_ok=True)

    def script(name, **data):
        data.setdefault("bounds", {"threads": 1})
        data.setdefault("assumptions", [ASSUMPTION])
        path = scripts / f"{name}.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        return f"scripts/{name}.yaml"

    def prove(config, subject, path):
        return {"configuration": config, "subject": subject,
                "prove": ["--candidate", candidate, "--function", FUNCTION, "--adapter", "scripted", "--script", path]}

    proven = script("fixture-proven", verdict="proven")
    refuted = script("fixture-refuted", verdict="refuted", counterexample={"x": 41})
    jobs = []
    for config in ("A", "B"):                         # grouped on purpose: the batch interleaves it
        for subject, make in SUBJECT_TOOLS.items():
            for variant in ("safe", "buggy"):
                spec = make(variant, config)
                jobs.append(_tool_job(config, f"{subject}-{variant}", spec, cap=spec["tool"] in capped))
        jobs += [prove(config, "fixture-proven", proven), prove(config, "fixture-refuted", refuted)]
    common = {"plan": "proof_lane_batch.1", "machine": "mbit10", "rss_cap_bytes": 8 * GIB, "job_timeout_seconds": 900}
    written = {}
    for name, extra in (("batch", {"workers": 6}), ("alone", {"workers": 1})):
        data = {**common, "batch": f"batch.t57.{args.stamp}.{name}", **extra, "jobs": jobs}
        written[name] = _write(run / f"{name}.yaml", data)
    probe_jobs = [_tool_job("ulimit-v", tool, spec, cap=True) for tool, spec in PROBES.items()]
    written["probe"] = _write(run / "probe.yaml", {**common, "batch": f"batch.t57.{args.stamp}.probe", "workers": 6,
                                                   "jobs": probe_jobs})
    hungry = script("fixture-hungry", verdict="proven", run=_alloc(9))
    calm = [_tool_job("oom", f"calm-{subject}", SUBJECT_TOOLS[subject]("safe", "A")) for subject in ("cbmc", "wp")]
    oom_jobs = [{"configuration": "oom", "subject": "hungry-tool",
                 "tool": {"command": _alloc(9), "bounds": {"threads": 1}}},
                prove("oom", "hungry-prove", hungry), *calm, prove("oom", "calm-prove", proven),
                _tool_job("oom", "calm-crux", SUBJECT_TOOLS["crux"]("safe", "A"))]
    written["oom"] = _write(run / "oom.yaml", {**common, "batch": f"batch.t57.{args.stamp}.oom", "workers": 6,
                                               "jobs": oom_jobs})
    print(json.dumps({"run": str(run), "capped_tools": sorted(capped), "plans": written}, indent=1))


def _write(path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return str(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("seed")
    sub.add_argument("folder", type=Path)
    sub.set_defaults(handler=seed)
    sub = commands.add_parser("plans")
    sub.add_argument("run", type=Path)
    sub.add_argument("--seed", type=Path, required=True)
    sub.add_argument("--probe", type=Path, help="batch.json of the probe batch: cap only the tools that started under it")
    sub.add_argument("--stamp", default="r1")
    sub.set_defaults(handler=plans)
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
