"""Executable HTA source-input request. Never builds or launches anything.

File identity binding is not author authentication, effective flags proof,
functional correctness, RTL synthesis or execution-backend acceptance.
"""
import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

ROLE_DETAILS = {
    "modified_zsim": "HTA functional-unit, cache request and retirement implementation",
    "nop_decoder": "Exact surrogate NOP bytes, decoder match and four instruction actions",
    "isa_wrappers": "Key/value register mapping, clobbers, branch targets and result flags",
    "table_and_overflow": "Sentinel/hash initialization, victim/duplicate/resize and lock/recheck",
    "build_manifest": "Pinned dependencies, toolchain, build argv and source flags",
    "test_harness": "Defined inputs and full hit/miss/victim/ownership correctness checks",
    "functional_unit_rtl": "Actual RTL top, ports, widths, reset and operation/result handshake",
    "rtl_testbench": "Finite unit vectors and checked expected outputs",
    "synthesis_script": "Yosys recipe and technology-library identity references",
}
MODES = {
    "zsim_execution_driven": (
        "modified_zsim",
        "nop_decoder",
        "isa_wrappers",
        "table_and_overflow",
        "build_manifest",
        "test_harness",
    ),
    "rtl_component_only": (
        "functional_unit_rtl",
        "rtl_testbench",
        "synthesis_script",
        "build_manifest",
    ),
}
SOURCE_SUFFIXES = {
    ".cc",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".v",
    ".sv",
    ".S",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".mk",
    ".ys",
    ".tcl",
}


def request_template():
    return {
        "schema": "HTA_actual_source_request_v1",
        "status": "ORIGINAL_IMPLEMENTATION_SOURCE_NOT_BOUND",
        "paper_doi": "10.1145/3352460.3358272",
        "preferred_mode": "zsim_execution_driven",
        "source_root": None,
        "artifact_repository": None,
        "artifact_commit": None,
        "roles": {
            role: {"path": None, "sha256": None, "obligation": text}
            for role, text in ROLE_DETAILS.items()
        },
        "unbound_ABI": [
            "surrogate NOP encodings",
            "CRC32 seed/word order",
            "register packing/result flag polarity",
            "atomic retirement and fault behavior",
        ],
        "next_command": "python3 source_request.py inspect SOURCE_PACKAGE.json",
        "native_x86_execution_permitted": False,
        "source_provenance_and_semantic_acceptance": "Separate owner review required",
    }


def inspect_inputs(manifest):
    if (
        type(manifest) is not dict
        or manifest.get("schema") != "HTA_source_package_v1"
    ):
        raise ValueError("exact source-package schema required")
    mode = manifest.get("mode")
    if mode not in MODES:
        raise ValueError(
            "unsupported backend; surrogate NOPs are not native HTA semantics"
        )
    root_value = manifest.get("source_root")
    if not isinstance(root_value, str) or not root_value:
        raise ValueError("actual private source root required")
    root = Path(root_value)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("regular source directory required")
    root = root.resolve()
    files = manifest.get("files")
    if type(files) is not dict:
        raise ValueError("role/path/hash bindings required")
    bound = {}
    for role in MODES[mode]:
        item = files.get(role)
        if type(item) is not dict:
            raise ValueError("missing source role: " + role)
        relative, expected = item.get("path"), item.get("sha256")
        if not isinstance(relative, str) or not relative:
            raise ValueError("missing source path: " + role)
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("source files must stay in declared package")
        if not isinstance(expected, str) or not re.fullmatch(
            "[a-f0-9]{64}", expected
        ):
            raise ValueError("exact expected source SHA required")
        target = root / path
        if target.suffix not in SOURCE_SUFFIXES and target.name != "Makefile":
            raise ValueError(
                "source inputs only; no model/library/store reads"
            )
        walk = root
        for part in path.parts:
            walk = walk / part
            if walk.is_symlink():
                raise ValueError("no source symlink substitution")
        before = target.stat()
        if (
            not stat.S_ISREG(before.st_mode)
            or not 0 < before.st_size <= 2 * 1024 * 1024
        ):
            raise ValueError("bounded regular source file required")
        raw = target.read_bytes()
        after = target.stat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
        if (
            identity(before) != identity(after)
            or hashlib.sha256(raw).hexdigest() != expected
        ):
            raise ValueError("source changed or expected digest mismatch")
        if raw.startswith(b"\x7fELF"):
            raise ValueError("binary substitution is not source")
        bound[role] = {"path": relative, "sha256": expected, "bytes": len(raw)}
    return {
        "status": "SOURCE_ROLE_FILES_HASH_BOUND_ONLY",
        "mode": mode,
        "roles": bound,
        "author_origin_authenticated": False,
        "effective_build_flags_certified": False,
        "ISA_or_atomic_semantics_certified": False,
        "build_or_run_performed": False,
        "next_action": "Owner verifies original source lineage and actual ABI, then admits a build",
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("request")
    inspection = sub.add_parser("inspect")
    inspection.add_argument("manifest")
    args = parser.parse_args()
    result = (
        request_template()
        if args.command == "request"
        else inspect_inputs(json.loads(Path(args.manifest).read_text()))
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
