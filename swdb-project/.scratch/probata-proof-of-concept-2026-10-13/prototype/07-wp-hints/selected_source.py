"""2026-10-16 ET: exact DX100 selected-source gate; no formal acceptance.

Use only under shared B plus a time/RSS guard. The optional compiler observation
is a full original-TU source check, never a C++/C refinement or allocator proof.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
MANIFEST_SHA = "8cc8eb45740c436260623bda72b765524ec4692ddfee5c1c7dfd5f48ca8caf9a"
BFS = "benchmarks/gapbs/src/bfs.cc"
BFS_SHA = "6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465"
PINS = {
    "scripts/prepare_dx100_scalar_snapshot.py": "34e27805753ecff9d5bf789166c13a061991c8278c94a48e42482ca0d473dc3c",
    "swdb/certification.py": "d367488b77df43a7e747ad55974d1b5fc787f63c42611984dacb3c0c03a7abf6",
    "library/dx100/bfs_read_offload.inc": "3c5867a2b8919806f681603836bd0cff448f21634485abf84e49ed71f25515ef",
    "library/dx100/dxc_lowering.hpp": "7c18bd44f329e445ba99abfd09423e40b3d685dc52a951267a61ade8417c627c",
}
COMPILER = Path("/opt/homebrew/opt/llvm/bin/clang++")
COMPILER_SHA = "305697d3868243dca6e4aabf4f628df7de135d701eb4fd78f6a5d7528fef4395"
SDK = Path("/Library/Developer/CommandLineTools/SDKs/MacOSX27.0.sdk")
SDK_SETTINGS_SHA = "7b93ad7e534cc4b31c6a4e39d19b5e0288acf2168c2649479a796d1cb51939fb"
ENV_SELECTORS = {"CPATH", "CPLUS_INCLUDE_PATH", "C_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "INCLUDE", "SDKROOT", "CCC_OVERRIDE_OPTIONS"}


class Refused(ValueError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def exact(path, pin):
    raw = path.read_bytes()
    if sha(raw) != pin:
        raise Refused("changed physical source: " + str(path))
    return raw


def selected_inputs(project, app):
    """Verify physical bytes before decoding, invoking producers or emission."""
    manifest = exact(app / "SHA256SUMS", MANIFEST_SHA).decode("utf-8", errors="strict")
    files = {}
    for line in manifest.splitlines():
        pin, relative = line.split("  ", 1)
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise Refused("invalid pinned source path")
        # No other kernel/example implementation is read or copied.
        if path.suffix in {".h", ".hpp"} or relative == BFS:
            files[relative] = exact(app / relative, pin)
    if sha(files[BFS]) != BFS_SHA:
        raise Refused("wrong original BFS source")
    producer = {relative: exact(project / relative, pin) for relative, pin in PINS.items()}
    return files, producer


def compose(project, files, producer):
    """Execute only the actual pinned producer function definitions."""
    env = {"hashlib": hashlib, "re": re, "Failure": Refused, "PIN": BFS_SHA, "ROOT": project}
    definitions = []
    for relative, name in (("scripts/prepare_dx100_scalar_snapshot.py", "scalar_source"),
                           ("swdb/certification.py", "peter_source")):
        tree = ast.parse(producer[relative].decode("utf-8", errors="strict"))
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
        if len(nodes) != 1:
            raise Refused("missing/ambiguous exact source producer")
        node = nodes[0]
        definitions.append({"path": relative, "function": name, "line": node.lineno,
                            "end_line": node.end_lineno, "physical_sha256": PINS[relative]})
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(project / relative), "exec"), env)
    original = files[BFS].decode("utf-8", errors="strict")
    selected = env["peter_source"](env["scalar_source"](original)).encode("utf-8")
    # Production peter_source reads this physical include: guard it on both sides.
    exact(project / "library/dx100/bfs_read_offload.inc", PINS["library/dx100/bfs_read_offload.inc"])
    return selected, definitions


def json_roots(raw):
    text = raw.decode("utf-8", errors="strict")
    decoder, index, rows = json.JSONDecoder(), 0, []
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index == len(text):
            break
        row, index = decoder.raw_decode(text, index)
        rows.append(row)
    return rows


def walk(node, parents=()):
    yield node, parents
    for child in node.get("inner", []):
        yield from walk(child, (*parents, node))


def inspect_ast(td_raw, queue_raw, main):
    """Exact retained AST observations. IDs are comparable only within td_raw."""
    td = [row for row in json_roots(td_raw)
          if row.get("kind") == "FunctionDecl" and row.get("name") == "TDStep"]
    if len(td) != 1 or Path(td[0].get("loc", {}).get("file", "")).resolve() != main.resolve():
        raise Refused("selected TDStep is not the exact main-TU definition")
    declarations = {n["id"]: n for n, _ in walk(td[0]) if n.get("kind") == "VarDecl" and n.get("name") == "lqueue"}
    if len(declarations) != 1:
        raise Refused("TDStep local buffer origin is ambiguous")
    local = next(iter(declarations.values()))
    if local.get("type", {}).get("desugaredQualType") != "QueueBuffer<int>":
        raise Refused("TDStep local buffer is not the exact NodeID specialization")
    constructions = [n for n, _ in walk(local) if n.get("kind") == "CXXConstructExpr"]
    if len(constructions) != 1 or constructions[0].get("ctorType", {}).get("qualType") != "void (SlidingQueue<int> &, size_t)":
        raise Refused("wrong QueueBuffer constructor resolution")
    defaults = [n for n, _ in walk(constructions[0]) if n.get("kind") == "CXXDefaultArgExpr"]
    if len(defaults) != 1 or [n.get("value") for n, _ in walk(defaults[0]) if n.get("kind") == "IntegerLiteral"] != ["16384"]:
        raise Refused("actual selected constructor default is not16384")
    references, captures = {}, []
    for node, parents in walk(td[0]):
        if node.get("kind") != "DeclRefExpr" or node.get("referencedDecl", {}).get("id") != local["id"]:
            continue
        span = node.get("range", {})
        key = (span.get("begin", {}).get("offset"), span.get("end", {}).get("offset", -1) + span.get("end", {}).get("tokLen", 0))
        member = next((a for a in reversed(parents) if a.get("kind") == "MemberExpr"), None)
        call = next((a for a in reversed(parents) if a.get("kind") == "CXXMemberCallExpr"), None)
        if member is not None and call is not None and member.get("name") in {"push_back", "flush"}:
            references[key] = member["name"]
        elif parents and parents[-1].get("kind") == "CapturedStmt" and any(a.get("kind") == "OMPForDirective" for a in parents):
            captures.append(key)
        else:
            raise Refused("local buffer escapes or has an unsupported source use")
    if any(key not in references or references[key] != "push_back" for key in captures):
        raise Refused("OpenMP capture lacks an exact same-variable/source-range member use")
    if sorted(references.values()) != ["flush", "push_back", "push_back"]:
        raise Refused("local buffer source uses differ from two pushes and final flush")
    specializations = {n["id"]: n for root in json_roots(queue_raw)
                       for n, _ in walk(root) if n.get("kind") == "ClassTemplateSpecializationDecl" and n.get("completeDefinition")
                       and any(c.get("kind") == "TemplateArgument" and c.get("type", {}).get("qualType") == "int" for c in n.get("inner", []))}
    if len(specializations) != 1:
        raise Refused("exact typed QueueBuffer definition missing/ambiguous")
    specialized = next(iter(specializations.values()))
    fields = {n["name"]: n["type"].get("desugaredQualType", n["type"]["qualType"])
              for n in specialized.get("inner", []) if n.get("kind") == "FieldDecl"}
    if fields != {"in": "unsigned long", "local_queue": "int *", "sq": "SlidingQueue<int> &", "local_size": "const unsigned long"}:
        raise Refused("selected QueueBuffer field/type map differs")
    news = [n for n, _ in walk(specialized) if n.get("kind") == "CXXNewExpr"]
    deletes = [n for n, _ in walk(specialized) if n.get("kind") == "CXXDeleteExpr"]
    if len(news) != 1 or news[0].get("isArray") is not True or news[0].get("type", {}).get("qualType") != "int *" or len(news[0].get("inner", [])) != 1 or news[0].get("initStyle"):
        raise Refused("source new[] has an initializer or an unsupported allocation shape")
    if len(deletes) != 1 or deletes[0].get("isArray") is not True:
        raise Refused("source destruction is not exact array delete")
    span = local["range"]
    return {"field_map": fields, "actual_default": 16384,
            "new_array_has_payload_initializer": False,
            "stable_source_binding": {"main_sha256": sha(main.read_bytes()), "function": "TDStep",
                "declaration_kind": "VarDecl", "declaration_name": "lqueue",
                "declaration_byte_range": [span["begin"]["offset"], span["end"]["offset"] + span["end"]["tokLen"]],
                "use_kind": "CXXMemberCallExpr/MemberExpr/DeclRefExpr",
                "source_uses": [{"byte_range": list(k), "method": v} for k,v in sorted(references.items())],
                "implicit_capture_kind": "OMPForDirective/CapturedStmt/DeclRefExpr",
                "implicit_capture_byte_ranges": [list(key) for key in captures]},
            "OMP_capture_semantics": "Same-variable IDs checked only within this TDStep AST; captures require exact matching source-use ranges; threads=1 source scope only, no generic OpenMP/noescape theorem",
            "normal_allocation_operator": {k:v for k,v in news[0].get("operatorNewDecl", {}).items() if k != "id"},
            "normal_deallocation_operator": {k:v for k,v in deletes[0].get("operatorDeleteDecl", {}).items() if k != "id"},
            "dump_local_IDs_retained_only_in_raw_AST": True}


def compiler_observations(out, main, deadline):
    exact(COMPILER, COMPILER_SHA)
    exact(SDK / "SDKSettings.json", SDK_SETTINGS_SHA)
    selectors = sorted(ENV_SELECTORS & os.environ.keys())
    if selectors:
        raise Refused("ambient compiler source selector names refused: " + ",".join(selectors))
    source = out / "source"
    base = [str(COMPILER), "--no-default-config", "-isysroot", str(SDK), "-x", "c++", "-std=c++11", "-fopenmp", "-pthread", "-DFUNC",
            "-I" + str(source / "benchmarks/API"), "-I" + str(main.parent),
            "-I/opt/homebrew/opt/libomp/include"]
    # No version, target-discovery or resource-directory probe. Selected target
    # and type widths are retained from this actual compilation's macro table.
    env = {"HOME": "/Users/yanrujhou", "PATH": "/usr/bin:/bin:/opt/homebrew/bin",
           "TMPDIR": str(out / "tmp"), "LC_ALL": "C"}
    marker = os.environ.get("SWDB_VERIFIER_RUN_TOKEN")
    if not marker:
        raise Refused("shared guarded-worker marker missing")
    env["SWDB_VERIFIER_RUN_TOKEN"] = marker
    commands, closure = [], []
    steps = [("preprocessed", ["-E", "-MD", "-MF", str(out / "includes.d")]),
             ("syntax", ["-fsyntax-only"]),
             ("macros", ["-E", "-dM"]),
             ("tokens", ["-fsyntax-only", "-Xclang", "-dump-tokens"]),
             ("TDStep-ast", ["-fsyntax-only", "-Xclang", "-ast-dump=json", "-Xclang", "-ast-dump-filter=TDStep"]),
             ("QueueBuffer-ast", ["-fsyntax-only", "-Xclang", "-ast-dump=json", "-Xclang", "-ast-dump-filter=QueueBuffer"])]
    for name, flags in steps:
        for row in closure:
            exact(Path(row["path"]), row["sha256"])
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Refused("source compiler internal deadline exhausted")
        argv = [*base, *flags, str(main)]
        with (out / (name + ".stdout")).open("wb") as stdout, (out / (name + ".stderr")).open("wb") as stderr:
            result = subprocess.run(argv, cwd=source, env=env, stdout=stdout, stderr=stderr, timeout=remaining)
        commands.append({"name": name, "argv": argv, "returncode": result.returncode})
        write(out / "compiler-commands.json", commands)
        if result.returncode:
            raise Refused("full selected-TU compiler step refused: " + name)
        if name == "preprocessed":
            dependency = (out / "includes.d").read_text().replace("\\\n", " ").split(":", 1)[1]
            paths = sorted({Path(name).resolve() for name in shlex.split(dependency)})
            closure = [{"path": str(path), "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size} for path in paths]
            write(out / "physical-include-closure.json", closure)
        for row in closure:
            exact(Path(row["path"]), row["sha256"])
    macros = (out / "macros.stdout").read_text()
    required = ["#define FUNC 1", "#define TILE_SIZE 16384", "#define NUM_CORES 4",
                "#define __SIZEOF_INT__ 4", "#define __SIZEOF_POINTER__ 8"]
    if any(line not in macros.splitlines() for line in required) or "#define _OPENMP " not in macros:
        raise Refused("selected FUNC/OpenMP/default-size/type-width context differs")
    # This is a retained physical dependency closure, not a claim that a future
    # recheck could omit rerunning the exact compiler/header selection.
    expected_queue = (main.parent / "sliding_queue.h").resolve()
    if expected_queue not in paths or sha(expected_queue.read_bytes()) != "3d5a1d3cff924737c2fc7c6b4fcbb859270f1fcc626c25aac4c780b7b6f4c02c":
        raise Refused("selected QueueBuffer header missing from original-TU closure")
    write(out / "physical-include-closure.json", closure)
    observed = inspect_ast((out / "TDStep-ast.stdout").read_bytes(),
                           (out / "QueueBuffer-ast.stdout").read_bytes(), main)
    exact(COMPILER, COMPILER_SHA)
    exact(SDK / "SDKSettings.json", SDK_SETTINGS_SHA)
    for row in closure:
        exact(Path(row["path"]), row["sha256"])
    return {**observed, "full_selected_TU_parsed": True, "compiler_path": str(COMPILER),
            "compiler_resolved": str(COMPILER.resolve()), "compiler_sha256": COMPILER_SHA,
            "explicit_SDK": str(SDK), "SDK_settings_sha256": SDK_SETTINGS_SHA,
            "ambient_driver_configs_disabled": True,
            "physical_include_files": len(closure),
            "include_closure_boundary": "discovery preprocessing identifies inputs; every later syntax/macro/token/AST compiler run bracketed by exact physical rehashes; filesystem sampling is not atomic",
            "host_context": "selected local compiler/macOS ABI; remote Linux/GEM5 ABI and link-time allocator replacement unqualified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--app", type=Path, default=PROJECT / "apps/dx100")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compiler-qualify", action="store_true")
    args = parser.parse_args()
    project, app, out = args.project.resolve(), args.app.resolve(), args.output.resolve()
    checkout = PROJECT.parent.resolve()
    if out.exists() or out == checkout or checkout in out.parents:
        raise Refused("fresh output outside checkout required")
    files, producer = selected_inputs(project, app)
    selected, definitions = compose(project, files, producer)
    out.mkdir(parents=True)
    (out / "tmp").mkdir()
    source = out / "source"
    for relative, raw in files.items():
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(selected if relative == BFS else raw)
    main_source = source / BFS
    (main_source.parent / "swdb_dxc_lowering.hpp").write_bytes(producer["library/dx100/dxc_lowering.hpp"])
    receipt = {"date": "2026-10-16 ET", "source_selection_only": True,
               "allocator_correspondence": False, "formal_acceptance": False,
               "full_TD_or_counted_admissible": False, "selected_main_sha256": sha(selected),
               "original_main_sha256": BFS_SHA, "producer_functions": definitions,
               "original_source_pins": {name: sha(raw) for name, raw in files.items()},
               "project_producer_pins": PINS, "selected_compiler_observations": None,
               "refinement_boundaries": ["successful normal allocation only; allocation failure/hooks/exceptions not qualified",
                   "threads=1 caller restriction; compile-time NUM_CORES4 is API capacity, not observed runtime thread count",
                   "unobservable allocation identity, nonescape, same-array lifetime and private-frame relation need independent source-refinement review",
                   "Typed payload initializedness and lexical retirement/reentry require actual root-admitted components",
                   "symbolic incoming SlidingQueue and default typed Graph/pvector caller domains remain independent; -m/arbitrary raw Graph refused",
                   "C++/C reference/member/layout/atomic/device correspondence and full RTE not established"]}
    write(out / "selected-source.json", receipt)
    if args.compiler_qualify:
        receipt["selected_compiler_observations"] = compiler_observations(out, main_source, time.monotonic() + 90)
    # Input and staged source unchanged checks cover all producer/header bytes.
    if selected_inputs(project, app) != (files, producer):
        raise Refused("physical producer inputs changed during source gate")
    if main_source.read_bytes() != selected:
        raise Refused("selected main source changed")
    for relative, raw in files.items():
        if relative != BFS and (source / relative).read_bytes() != raw:
            raise Refused("staged selected header changed")
    write(out / "selected-source.json", receipt)


if __name__ == "__main__":
    main()
