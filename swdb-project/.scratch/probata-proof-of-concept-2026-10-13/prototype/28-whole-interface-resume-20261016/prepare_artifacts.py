"""2026-10-16 ET. Compiler-free source preparation; no public admission.

Execute only this owned preparation directory and pinned stdlib-only renderer
AST. Inputs are frozen before rendering and rehashed before artifact publication.
The source-site/ABI fixtures are synthetic descriptions, never compiler evidence.
"""
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
BACKEND = HERE.parent / "28-proof-semantics"
RENDERERS = ("numeric_values", "deferred_state", "typed_state", "command_state", "action_state",
             "region_state", "register_state", "tile_image", "size_state", "setup_state")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_owned(name):
    path = HERE / (name + ".py")
    tree = ast.parse(path.read_bytes())
    allowed = {"ast", "hashlib", "json", "pathlib", "re"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name not in allowed for alias in node.names):
                raise ValueError("non-stdlib preparation import")
        elif isinstance(node, ast.ImportFrom) and node.module not in allowed:
            raise ValueError("non-stdlib preparation import")
    namespace = {"__file__": str(path), "__name__": "source_preparation"}
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


def input_paths():
    paths = [PROJECT / "apps/dx100/benchmarks/API" / name for name in ("MAA.hpp", "MAA_gem5.hpp")]
    paths += [PROJECT / "tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json"]
    fixture = PROJECT / "tests/fixtures/proof/dx100/gem5-e4fc4af"
    paths += [fixture / name for name in ("IF.cc", "MAA.cc", "SPD.cc", "SPD.hh", "CpuSidePort.cc")]
    upstream = Path("/private/tmp/probata-ticket28-interface-upstream-20261015")
    paths += [upstream / name for name in ("ALU.cc", "IndirectAccess.cc", "StreamAccess.cc")]
    paths += [BACKEND / (name + ".py") for name in RENDERERS]
    paths += [HERE / (name + ".py") for name in ("whole_interface", "wrappers", "prepare_artifacts", "test_whole_interface")]
    return paths


def write_artifacts():
    paths = input_paths()
    before = {str(path.resolve()): sha(path.read_bytes()) for path in paths}
    api, wrappers = load_owned("whole_interface"), load_owned("wrappers")
    declarations = api["inventory"](PROJECT)
    # A single explicit fixture profile suffices to enumerate type-instance keys;
    # neither this profile nor the generated constants are compiler observations.
    abi = {"byte_order": "little", "int_bits": 32, "pointer_bits": 64,
           "canonical_types": dict(zip(api["TYPE_KEYS"],
             ("unsigned int", "int", "float", "unsigned long long", "long long", "double"))),
           "sizes": [4, 4, 4, 8, 8, 8], "alignments": [4, 4, 4, 8, 8, 8]}
    api["validate_abi"](abi)
    instances = []
    for row in declarations:
        for dtype in range(6) if row["template"] else (None,):
            canonical = abi["canonical_types"][api["TYPE_KEYS"][dtype]] if dtype is not None else None
            cname = row["name"] + ("_" + canonical.replace(" ", "_") if canonical else "")
            if row["name"] == "get_new_reg":
                cname += "_args" + str(row["formal_arity"])
            descriptor = {"name": row["name"], "formal_arity": row["formal_arity"], "dtype": dtype,
                          "canonical_type": canonical, "c_name": cname, "source_declaration": row["declaration"],
                          "header_sha256": row["header_sha256"], "header_body_sha256": row["body_sha256"],
                          "abi_sha256": sha(json.dumps(abi, sort_keys=True, separators=(",", ":")).encode()),
                          "private_adapter": "dwi_" + row["name"] + ("_initialized" if row["name"] == "get_new_reg" and row["formal_arity"] else "")}
            instances.append({"name": row["name"], "line": row["line"], "arity": row["formal_arity"],
                              "dtype": dtype, "effective_dtype": 1 if row.get("packet", {}).get("dtype") == "int32_t" else dtype,
                              "signature": api["signature"](row, canonical), "c_name": cname,
                              "canonical_type": canonical,
                              "synthetic_private_dispatch_plan": api["dispatch_plan"](descriptor, declarations, abi)})
    if len(instances) != 132 or len({row["c_name"] for row in instances}) != 132:
        raise ValueError("closed 132-instance overload inventory differs")
    by_name = {}
    for row in declarations:
        by_name.setdefault(row["name"], []).append(api["contract"](row))
    data = {
        "declarations.json": declarations,
        "contracts.json": {"date": "2026-10-16", "scope": "owned source/MMIO per-call recipes; PREPARATION_ONLY",
                           "contract_count": len(by_name), "contracts": by_name},
        "type-instances.json": {"date": "2026-10-16", "abi_status": "SYNTHETIC_FIXTURE_NOT_COMPILER_OBSERVED",
                                "abi": abi, "instances": instances},
    }
    outputs = {name: (json.dumps(value, indent=2, sort_keys=True) + "\n").encode() for name, value in data.items()}
    outputs["whole_backend.h"] = wrappers["render_backend"](PROJECT, expected_pins=before).encode()
    outputs["whole_adapters.h"] = wrappers["render_adapters"](declarations).encode()
    after = {str(path.resolve()): sha(path.read_bytes()) for path in paths}
    if before != after:
        raise ValueError("source changed during preparation")
    manifest = {"date": "2026-10-16", "status": "SOURCE_PREPARATION_ONLY",
                "claims": {"declarations": 27, "names": 26, "packet_maps": 11, "synthetic_type_instances": 132},
                "source_inputs": [{"path": str(path.resolve()), "bytes": path.stat().st_size,
                                   "sha256": before[str(path.resolve())]} for path in paths],
                "outputs": [{"path": str(HERE / name), "bytes": len(value), "sha256": sha(value)}
                            for name, value in sorted(outputs.items())],
                "premises": api["PREMISES"],
                "compiler_or_native_execution": False,
                "public_admission": False,
                "source_archive_boundary": "local retained source bytes rehashed; upstream capture provenance remains root-owned",
                "remaining": ["admitted full-TU producer and actual compiler ABI profile", "closed source-bound family deferred-value builders",
                              "compiler-bound typed scalar and CPU C-object/guest/physical access mapping",
                              "frozen source replay and public synthetic proof/refusal verdicts"]}
    # Restrict mutation to this owned directory. The retained manifests pin the
    # source bytes used to prepare outputs; no runtime or tool is invoked here.
    for name, value in outputs.items():
        (HERE / name).write_bytes(value)
    (HERE / "source-preparation.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


if __name__ == "__main__":
    write_artifacts()
