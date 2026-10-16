"""Native/compiler/pure controls. Run ONLY under shared B and a time/RSS guard.

No formal tools, provider, SSH or installed-verifier changes. Output is external,
fresh and incremental. Native and compiler evidence never accepts a proof.
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
GENERATOR = POC / "outslot_lowering.py"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    out = a.output.resolve()
    # worktree root includes swdb-project. Nothing is emitted inside it.
    checkout = next(parent for parent in HERE.parents if (parent / ".git").exists())
    if out == checkout or checkout in out.parents or out.exists():
        raise ValueError("fresh output outside checkout required")
    out.mkdir(parents=True)
    records = []

    def record(name, passed, **extra):
        row = {"name": name, "passed": bool(passed), **extra}
        records.append(row)
        (out / "controls.json").write_text(json.dumps({"proof_acceptance": False, "records": records}, indent=2) + "\n")
        if not passed: raise AssertionError(name)

    def run(name, argv, expect=0, diagnostic=None):
        r = subprocess.run([str(x) for x in argv], capture_output=True, text=True, timeout=30)
        (out / (name + ".stdout")).write_text(r.stdout)
        (out / (name + ".stderr")).write_text(r.stderr)
        passed = (r.returncode == expect if expect >= 0 else r.returncode != 0)
        if diagnostic: passed = passed and diagnostic in r.stderr
        record(name, passed, argv=[str(x) for x in argv], returncode=r.returncode,
               stdout_sha256=hashlib.sha256(r.stdout.encode()).hexdigest(),
               stderr_sha256=hashlib.sha256(r.stderr.encode()).hexdigest())
        return r

    generated = out / "generated"
    run("generate", [sys.executable, GENERATOR, "--output", generated])
    allocator_output = out / "allocator-correspondence-refused"
    run("allocator-correspondence-refused", [sys.executable, GENERATOR, "--require-allocator-correspondence",
        "--output", allocator_output], expect=-1, diagnostic="allocator source correspondence pending")
    record("allocator-refusal-no-emission", not allocator_output.exists())
    for name in ("gapbs_models.h", "bfs_unit.h", "dxc_summaries.h", "tdstep_standin.c", "abi-map.json"):
        record("reproduce-" + name, (generated / name).read_bytes() == (POC / "standin_outslot" / name).read_bytes())
    run("no-overwrite", [sys.executable, GENERATOR, "--output", generated], expect=-1,
        diagnostic="output must be absent")
    for name, mutation in (
        ("unknown-return", "\nint unsupported(void) { return 1; }\n"),
        ("aggregate-return", "\nstruct unsupported {int x;}; struct unsupported f(void);\n"),
        ("uninitialized-return-source", "\nint unsafe(void) { int x; return x; }\n"),
        ("aliased-out-source", "\nvoid unsafe_alias(void *p) { (void)p; }\n"),
    ):
        source = out / (name + "-source")
        shutil.copytree(POC / "standin", source)
        target = source / "gapbs_models.h"
        target.write_text(target.read_text() + mutation)
        refused = out / (name + "-output")
        run(name, [sys.executable, GENERATOR, "--source", source, "--output", refused], expect=-1,
            diagnostic="unsupported changed source")
        record(name + "-no-emission", not refused.exists())

    cc = ["/usr/bin/clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter"]
    native = cc + ["-fsanitize=address,undefined"]
    run("helper-build", native + ["-I", generated, HERE / "control.c", "-o", out / "helper"])
    run("helper-run", [out / "helper"])
    wrong_type = out / "wrong-output-type.c"
    wrong_type.write_text('#include "gapbs_models.h"\nvoid bad(struct pvector_NodeID *p) { NodeID slot; pvector_NodeID_data_out(p, &slot); }\n')
    run("wrong-output-type", cc + ["-fsyntax-only", "-I", generated, wrong_type], expect=-1,
        diagnostic="incompatible pointer types")
    for mode, include, flags in (("original", POC / "standin", []), ("outslot", generated, ["-DSWDB_OUTSLOT"])):
        run(mode + "-td-build", native + flags + ["-I", include, HERE / "td_behavior.c", "-o", out / mode])
        run(mode + "-td-run", [out / mode])
    record("td-identical-output-and-event-counts", (out / "original-td-run.stdout").read_bytes() == (out / "outslot-td-run.stdout").read_bytes())

    # Diagnostic controls concern the source read, not the output slot: neither
    # writing an uninitialized scalar to a slot nor returning it is made safe.
    for name, text in (
        ("bad-return", "int bad(void) { int uninitialized; return uninitialized; }\n"),
        ("bad-out-store", "void bad(int *out) { int uninitialized; *out = uninitialized; }\n"),
    ):
        source = out / (name + ".c"); source.write_text(text)
        run(name, cc + ["-fsyntax-only", source], expect=-1, diagnostic="uninitialized")
    # Clang's analyzer, unlike ASan, tracks this local uninitialized pointee.
    # It independently follows the pointer store through the new ABI.
    payload = out / "bad-pointed-payload.c"
    payload.write_text("static void pointer_out(int *p, int **out) {*out = p;}\n"
                       "int bad(void) {int payload; int *slot; pointer_out(&payload, &slot); return *slot;}\n")
    run("bad-pointed-payload", ["/usr/bin/clang", "--analyze", "-Xanalyzer", "-analyzer-output=text", payload],
        diagnostic="Undefined or garbage value returned to caller")
    manifest = json.loads((generated / "abi-map.json").read_text())
    record("all-22-return-interfaces", len(manifest["interfaces"]) == 22 and
           sum(row["body"] for row in manifest["interfaces"]) == 15)
    # Exact original functional TD postconditions are retained verbatim, and
    # every old returning interface call is either rewritten or input refused.
    old = (POC / "standin" / "tdstep_standin.c").read_text()
    new = (generated / "tdstep_standin.c").read_text()
    old_posts = old[old.index("    ensures visited_parent_unchanged:"):old.index("void TDStep(")]
    new_posts = new[new.index("    ensures visited_parent_unchanged:"):new.index("void TDStep(")]
    record("unchanged-td-postconditions", old_posts == new_posts)
    result = {"proof_acceptance": False, "records": records, "passed": len(records),
              "source_pins": manifest["source_pins"], "output_pins": manifest["output_pins"],
              "boundary": "native fixtures and compiler diagnostics; no ACSL parse, RTE generation, solver or C++/DX100/source correspondence proof"}
    (out / "controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": len(records), "proof_acceptance": False, "output": str(out)}))


if __name__ == "__main__": main()
