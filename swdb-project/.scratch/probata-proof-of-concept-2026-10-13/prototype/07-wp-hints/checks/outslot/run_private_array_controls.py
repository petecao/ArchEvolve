"""Run only inside shared B + an external time/RSS guard. No formal tools.

Undefined initializedness negatives are analyzed, never natively executed.
All same-path fixtures include the actual generated constructor/binder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
POC = HERE.parents[1]
GENERATOR = POC / "private_array_lowering.py"
CHECKOUT = next(p for p in HERE.parents if (p / ".git").exists())
UNIT = CHECKOUT / "swdb-project/library/dx100/bfs_read_offload.inc"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args(); out = a.output.resolve()
    if out.exists() or out == CHECKOUT or CHECKOUT in out.parents:
        raise ValueError("fresh output outside checkout required")
    out.mkdir(parents=True)
    records = []

    def record(name, passed, **kw):
        records.append({"name": name, "passed": bool(passed), **kw})
        (out / "controls.json").write_text(json.dumps({"proof_acceptance": False, "records": records}, indent=2) + "\n")
        if not passed: raise AssertionError(name)

    def run(name, argv, expect=0, diagnostic=None):
        r = subprocess.run([str(x) for x in argv], cwd=out, text=True, capture_output=True, timeout=30)
        (out / (name + ".stdout")).write_text(r.stdout)
        (out / (name + ".stderr")).write_text(r.stderr)
        ok = r.returncode == expect if expect >= 0 else r.returncode != 0
        if diagnostic: ok = ok and diagnostic in r.stderr
        record(name, ok, argv=[str(x) for x in argv], returncode=r.returncode,
               stdout_sha256=hashlib.sha256(r.stdout.encode()).hexdigest(),
               stderr_sha256=hashlib.sha256(r.stderr.encode()).hexdigest())
        return r

    generated = out / "generated"
    run("generate", [sys.executable, GENERATOR, "--output", generated])
    manifest = json.loads((generated / "private-array-map.json").read_bytes())
    record("exact-ten-site-families", set(manifest["same_path_controls"]) == {
        "positive", "missing-store", "wrong-cell", "uninitialized-scalar", "copy-positive", "history-positive",
        "reentry-positive", "reentry-missing-store", "modular-entry-positive", "modular-entry-missing-store"})
    for name in (*manifest["output_pins"], "private-array-map.json"):
        record("reproduce-" + name, (generated / name).read_bytes() == (POC / "standin_private_array" / name).read_bytes())
    refusal = out / "allocator-refused"
    run("allocator-gate-refused", [sys.executable, GENERATOR, "--require-allocator-correspondence", "--output", refusal],
        expect=-1, diagnostic="allocator correspondence pending")
    record("allocator-gate-no-emission", not refusal.exists())
    # Preserve physical-byte admission at both the previous model and real unit.
    changed = out / "changed-source"; shutil.copytree(POC / "standin_outslot", changed)
    q = changed / "gapbs_models.h"; q.write_bytes(q.read_bytes().replace(b"\n", b"\r\n"))
    run("changed-physical-source-refused", [sys.executable, GENERATOR, "--source", changed, "--output", out / "changed-refused"],
        expect=-1, diagnostic="unsupported changed source")
    constructor = b"QueueBuffer<NodeID> lqueue(queue);"
    unit_raw = UNIT.read_bytes()
    if unit_raw.count(constructor) != 1 or unit_raw.count(b"lqueue.flush();") != 1:
        raise ValueError("unexpected real unit source sites")
    for name, value in (
        ("escaped-local", unit_raw.replace(constructor, constructor + b" extern void unknown_sink(void*); unknown_sink(&lqueue);")),
        ("post-destroy-use", unit_raw.replace(b"lqueue.flush();", b"lqueue.~QueueBuffer(); lqueue.push_back(9);")),
        ("generic-size", unit_raw.replace(constructor, b"QueueBuffer<NodeID> lqueue(queue, 3);")),
    ):
        unit = out / (name + ".inc"); unit.write_bytes(value)
        refused = out / (name + "-refused")
        run(name, [sys.executable, GENERATOR, "--unit", unit, "--output", refused], expect=-1,
            diagnostic="unsupported changed source unit")
        record(name + "-no-emission", not refused.exists())
    cc = ["/usr/bin/clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter"]
    native = cc + ["-fsanitize=address,undefined"]
    run("private-helper-build", native + ["-I", generated, HERE / "private_array_native.c", "-o", out / "private-helper"])
    run("private-helper-run", [out / "private-helper"])
    for mode, include, flags in (("original", POC / "standin", []),
                                 ("outslot", POC / "standin_outslot", ["-DSWDB_OUTSLOT"]),
                                 ("private", generated, ["-DSWDB_OUTSLOT", "-DSWDB_PRIVATE_ARRAY"])):
        run(mode + "-td-build", native + flags + ["-I", include, HERE / "td_behavior.c", "-o", out / mode])
        run(mode + "-td-run", [out / mode])
    record("three-way-td-values-and-event-counts", len({(out / (mode + "-td-run.stdout")).read_bytes()
           for mode in ("original", "outslot", "private")}) == 1)
    wrong = out / "wrong-extent.c"
    wrong.write_text('#include "gapbs_models.h"\nvoid bad(struct QueueBuffer_NodeID *b, struct SlidingQueue_NodeID *q) { NodeID storage[1]; QueueBuffer_NodeID_QueueBuffer(b,q,16384,&storage); }\n')
    run("wrong-typed-extent", cc + ["-fsyntax-only", "-I", generated, wrong], expect=-1,
        diagnostic="incompatible pointer types")
    for name in manifest["same_path_controls"]:
        r = run("analyze-" + name, ["/usr/bin/clang", "--analyze", "-Xanalyzer", "-analyzer-output=text", "-I", generated,
                                  generated / "sites" / (name + ".c")])
        if "positive" in name:
            record(name + "-no-uninitialized-diagnostic", not r.stderr.strip())
        else:
            record(name + "-source-read-diagnostic", r.stderr.count("warning:") == 1 and
                   "[core.uninitialized.Assign]" in r.stderr and
                   str(generated / "sites" / (name + ".c")) + ":" in r.stderr,
                   boundary="compiler analyzer only; exact formal init-map/ordinary/smoke gates remain unrun")
    result = {"proof_acceptance": False, "records": records, "passed": len(records),
              "input_pins": manifest["parent_outslot_source_pins"], "output_pins": manifest["output_pins"],
              "allocator_correspondence": manifest["allocator_correspondence"],
              "boundary": "native defined-execution and compiler analyzer controls only; no formal initializedness, alignment, lifetime or source correspondence acceptance"}
    (out / "controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": len(records), "proof_acceptance": False, "output": str(out)}))


if __name__ == "__main__": main()
