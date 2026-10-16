"""2026-10-16 ET: public original-TU source controls, shared B/guard required.

No native execution/formal/provider/probe/version/config command. Source/compiler
observations do not establish allocator, model, TD or counted-run acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
POC = HERE.parents[1]
PROJECT = POC.parents[3]
GENERATOR = POC / "selected_source.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    checkout = PROJECT.parent
    if out.exists() or out == checkout or checkout in out.parents:
        raise ValueError("fresh external output required")
    out.mkdir(parents=True)
    records = []

    def record(name, ok, **extra):
        records.append({"name": name, "passed": bool(ok), **extra})
        (out / "controls.json").write_bytes((json.dumps({"proof_acceptance": False,
            "native_execution": False, "records": records}, indent=2) + "\n").encode())
        if not ok:
            raise AssertionError(name)

    def run(name, output, *flags, success=True):
        result = subprocess.run([sys.executable, str(GENERATOR), "--output", str(output), *map(str, flags)],
                                capture_output=True, timeout=105)
        (out / (name + ".stdout")).write_bytes(result.stdout)
        (out / (name + ".stderr")).write_bytes(result.stderr)
        record(name, (result.returncode == 0) == success, returncode=result.returncode)
        return result

    def frozen():
        return {str(f.relative_to(POC)): hashlib.sha256(f.read_bytes()).hexdigest()
                for directory in ("standin", "standin_outslot", "standin_private_array",
                                  "standin_outslot_canonical", "standin_private_array_canonical")
                for f in (POC / directory).rglob("*") if f.is_file()}

    before = frozen()
    selected = out / "selected"
    run("full-selected-TU", selected, "--compiler-qualify")
    receipt = json.loads((selected / "selected-source.json").read_bytes())
    observations = receipt["selected_compiler_observations"]
    record("original-fork-default-array-observed", observations["actual_default"] == 16384 and
           observations["new_array_has_payload_initializer"] is False)
    record("all-source-acceptance-boundaries-refused", receipt["allocator_correspondence"] is False and
           receipt["formal_acceptance"] is False and receipt["full_TD_or_counted_admissible"] is False)
    record("full-original-TU-include-token-macro-records", observations["full_selected_TU_parsed"] is True and
           observations["physical_include_files"] > 0 and (selected / "tokens.stderr").stat().st_size > 0 and
           (selected / "macros.stdout").stat().st_size > 0)
    spec = importlib.util.spec_from_file_location("selected_source", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    td_raw = (selected / "TDStep-ast.stdout").read_bytes()
    queue_raw = (selected / "QueueBuffer-ast.stdout").read_bytes()
    main_source = selected / "source/benchmarks/gapbs/src/bfs.cc"
    baseline = module.inspect_ast(td_raw, queue_raw, main_source)
    pack = lambda roots: ("\n".join(json.dumps(root) for root in roots) + "\n").encode()
    # Exercise the reader against the actual retained compiler serializer and
    # AST, rather than a synthetic tree that assumes the reader's shape.
    td_roots = module.json_roots(td_raw)
    ids = {node["id"] for root in td_roots for node, _ in module.walk(root) if "id" in node}
    replacements = {value: "fresh-process-" + str(i) for i, value in enumerate(sorted(ids))}

    def rename(value):
        if isinstance(value, dict):
            return {k: rename(v) for k, v in value.items()}
        if isinstance(value, list):
            return [rename(v) for v in value]
        return replacements.get(value, value) if isinstance(value, str) else value

    record("within-dump-ID-renaming-preserves-stable-binding",
           module.inspect_ast(pack(rename(td_roots)), queue_raw, main_source) == baseline)
    for name in ("unmatched-capture-range", "wrong-selected-default", "initialized-new-array", "wrong-local-type"):
        td_roots, queue_roots = module.json_roots(td_raw), module.json_roots(queue_raw)
        changed = False
        for roots in (td_roots, queue_roots):
            for root in roots:
                for node, parents in module.walk(root):
                    if name == "unmatched-capture-range" and not changed and node.get("kind") == "DeclRefExpr" and node.get("referencedDecl", {}).get("name") == "lqueue" and parents and parents[-1].get("kind") == "CapturedStmt":
                        node["range"]["begin"]["offset"] += 1
                        node["range"]["end"]["offset"] += 1
                        changed = True
                    elif name == "wrong-selected-default" and node.get("kind") == "IntegerLiteral" and node.get("value") == "16384" and any(p.get("kind") == "CXXDefaultArgExpr" for p in parents):
                        node["value"] = "8192"
                        changed = True
                    elif name == "initialized-new-array" and node.get("kind") == "CXXNewExpr" and node.get("type", {}).get("qualType") == "int *":
                        node["initStyle"] = "call"
                        changed = True
                    elif name == "wrong-local-type" and node.get("kind") == "VarDecl" and node.get("name") == "lqueue":
                        node["type"]["desugaredQualType"] = "QueueBuffer<long>"
                        changed = True
        record(name + "-reader-mutation-present", changed)
        try:
            module.inspect_ast(pack(td_roots), pack(queue_roots), main_source)
        except module.Refused:
            record(name + "-reader-refused", True)
        else:
            record(name + "-reader-refused", False)
    # Changed actual producer header families must refuse before any emission;
    # these are not changes to the lowered hand model or unrelated toy fixtures.
    original_app = PROJECT / "apps/dx100"
    for name, relative, mutate in (
        ("nondefault-allocation", "benchmarks/gapbs/src/sliding_queue.h", lambda r: r.replace(b"given_size = 16384", b"given_size = 8192", 1)),
        ("initialized-allocation", "benchmarks/gapbs/src/sliding_queue.h", lambda r: r.replace(b"new T[local_size]", b"new T[local_size]()", 1)),
        ("header-macro-substitution", "benchmarks/gapbs/src/sliding_queue.h", lambda r: r + b"\n#define QueueBuffer UnknownBuffer\n"),
        ("header-physical-CRLF", "benchmarks/gapbs/src/sliding_queue.h", lambda r: r.replace(b"\n", b"\r\n")),
        ("pvector-endpoint-change", "benchmarks/gapbs/src/pvector.h", lambda r: r + b"\n#define endp beginp\n"),
    ):
        app = out / (name + "-app")
        shutil.copytree(selected / "source", app)
        shutil.copyfile(original_app / "SHA256SUMS", app / "SHA256SUMS")
        # Restore the original main input; selected main is a derived product.
        (app / "benchmarks/gapbs/src/bfs.cc").write_bytes((original_app / "benchmarks/gapbs/src/bfs.cc").read_bytes())
        target = app / relative
        prior = target.read_bytes()
        target.write_bytes(mutate(prior))
        record(name + "-physical-mutation", target.read_bytes() != prior)
        refused = out / (name + "-refused")
        run(name, refused, "--app", app, success=False)
        record(name + "-no-emission", not refused.exists())
    for name, mutate in (
        ("escaped-local-unit", lambda r: r.replace(b"lqueue.flush();", b"unknown_sink(&lqueue); lqueue.flush();", 1)),
        ("unit-nonUTF8", lambda r: r + b"\xff"),
    ):
        project = out / (name + "-project")
        for relative in ("scripts/prepare_dx100_scalar_snapshot.py", "swdb/certification.py",
                         "library/dx100/bfs_read_offload.inc", "library/dx100/dxc_lowering.hpp"):
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((PROJECT / relative).read_bytes())
        target = project / "library/dx100/bfs_read_offload.inc"
        target.write_bytes(mutate(target.read_bytes()))
        refused = out / (name + "-refused")
        run(name, refused, "--project", project, success=False)
        record(name + "-no-emission", not refused.exists())
    refused = out / "unknown-context-refused"
    run("unknown-context-refused", refused, "--define", "GEM5", success=False)
    record("unknown-context-no-emission", not refused.exists())
    record("all-frozen-inputs-preserved", frozen() == before)


if __name__ == "__main__":
    main()
