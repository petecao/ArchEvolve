"""2026-10-16 ET. Exact-source per-root device initializedness components.

This finite splitter preserves the original six worlds. It creates two named
modular TUs, not a proof, generic C transformation, or whole-TD refinement.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

INPUTS = [
    {"path": "checks/device_init/normal.c", "sha256": "d7ae9477c6c7bd9d090d71e6b4e4b0d01b19baa2f851300c184af090c5a96bdc"},
    {"path": "checks/device_init/omitted-output.c", "sha256": "31bfce4101bf7fa459af68cf09c2829fb8adbb522fd8f24cac01aaf24cf051e3"},
    {"path": "standin_device_init_canonical/dxc_summaries.h", "sha256": "5bd692de0323ee209304ffdc9e9ca477ae809aad88761ed1815622e1caeb9f24"},
    {"path": "checks/device_init/omitted-output-dxc_summaries.h", "sha256": "cadb31112edaaddf288b758696249de799bc19e9ab82387570940f00387626ca"},
]
ROOTS = (
    "swdb_device_pipeline_safe", "swdb_device_missing_source",
    "swdb_device_wrong_prefix", "swdb_device_index_safe", "swdb_device_missing_index",
)
SELECTED = ("index_safe", "missing_index")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def span(raw, name):
    """Only the byte-pinned finite ASCII fixtures, with comments length-preserved."""
    code = re.sub(rb"/\*.*?\*/|//[^\n]*", lambda m: bytes(10 if c == 10 else 32 for c in m[0]), raw, flags=re.S)
    matches = list(re.finditer(rb"\bvoid\s+" + name.encode("ascii") + rb"\s*\(int\s*\*out\)\s*\{", code))
    if len(matches) != 1:
        raise RuntimeError("exact named root definition missing or ambiguous")
    start = raw.rfind(b"/*@", 0, matches[0].start())
    annotation_end = raw.find(b"*/", start) + 2
    if start < 0 or annotation_end < 2 or raw[annotation_end:matches[0].start()].strip():
        raise RuntimeError("root's original attached contract not found")
    end = matches[0].end()
    depth = 1
    while depth and end < len(code):
        depth += (code[end] == 123) - (code[end] == 125)
        end += 1
    if depth:
        raise RuntimeError("root body unterminated")
    return {"root": name, "start_byte": start, "end_byte": end,
            "first_line": raw[:start].count(b"\n") + 1,
            "last_line": raw[:end].count(b"\n") + 1,
            "sha256": digest(raw[start:end]), "bytes": end - start}


def build(source_root, output, selected=SELECTED):
    source_root, output = Path(source_root), Path(output)
    if tuple(selected) != SELECTED:
        raise RuntimeError("only the two prospectively named full-root worlds are supported")
    if output.exists() or output.is_symlink():
        raise FileExistsError("output must be fresh")
    protected = [source_root / "checks/device_init", source_root / "standin_device_init_canonical", Path(__file__)]
    target = output.resolve()
    for p in protected:
        p = p.resolve()
        if target == p or target.is_relative_to(p) or p.is_relative_to(target):
            raise RuntimeError("output overlaps immutable source or generator")
    inputs = {}
    for row in INPUTS:
        p = source_root / row["path"]
        if p.is_symlink():
            raise RuntimeError("input must be the exact regular physical source")
        raw = p.read_bytes()
        if digest(raw) != row["sha256"]:
            raise RuntimeError("physical source bytes differ: " + row["path"])
        raw.decode("utf-8", errors="strict")
        inputs[row["path"]] = raw
    normal_name, weak_name = INPUTS[0]["path"], INPUTS[1]["path"]
    normal, weak = inputs[normal_name], inputs[weak_name]
    spans = [span(normal, name) for name in ROOTS]
    for left, right in zip(spans, spans[1:]):
        if left["end_byte"] > right["start_byte"]:
            raise RuntimeError("source root spans overlap")
    worlds = [{"world": "normal:" + s["root"], "source": normal_name, **s, "retained_original": True} for s in spans]
    worlds.append({"world": "omitted-output:swdb_device_pipeline_safe", "source": weak_name,
                   **span(weak, "swdb_device_pipeline_safe"), "retained_original": True})
    rendered = {}
    generated = {}
    for tag in SELECTED:
        name = "swdb_device_" + tag
        kept = next(s for s in spans if s["root"] == name)
        chunks = []
        cursor = 0
        for s in spans:
            lo, hi = s["start_byte"], s["end_byte"]
            chunks.append(normal[cursor:lo])
            if s["root"] != name:
                chunks.append(b"\n" * normal[lo:hi].count(b"\n"))
            else:
                chunks.append(normal[lo:hi])
            cursor = hi
        chunks.append(normal[cursor:])
        # Empty omitted worlds after the kept root need no trailing blank lines.
        # Every retained source coordinate is unchanged; byte spans are explicit.
        raw = b"".join(chunks).rstrip(b"\n") + b"\n"
        emitted = span(raw, name)
        if raw[emitted["start_byte"]:emitted["end_byte"]] != normal[kept["start_byte"]:kept["end_byte"]]:
            raise RuntimeError("kept root changed")
        if any(other.encode() in raw for other in ROOTS if other != name):
            raise RuntimeError("kept root/preamble depends on another removed root")
        rendered[tag + "/site_input.c"] = raw
        rendered[tag + "/dxc_summaries.h"] = inputs[INPUTS[2]["path"]]
        generated[tag] = {"root": name, "original_world": "normal:" + name,
                          "kept_span": kept, "generated_span": emitted, "source_sha256": digest(raw),
                          "complete_body_set": [name], "helper_definition_count": 0,
                          "all_header_declarations_retained": True,
                          "other_original_worlds_remain_deferred": True,
                          "source_line_offsets_preserved": True,
                          "original_and_generated_byte_offsets_explicit": True}
    manifest = {"date_ET": "2026-10-16", "purpose": "named complete per-root diagnostic worlds; not whole-original-TU proof",
                "inputs": INPUTS, "original_worlds": worlds, "generated_worlds": generated,
                "outputs": {name: {"sha256": digest(raw), "bytes": len(raw)} for name, raw in rendered.items()},
                "root_bytes_contracts_headers_unchanged": True,
                "no_new_premise_or_proof_fact": True, "no_goal_or_function_filter": True,
                "Typed_source_Init_lifetime_TD_count_qualified": False, "proof_acceptance": False}
    # Validate and render everything before creating any output.
    output.mkdir(parents=True)
    for name, raw in rendered.items():
        p = output / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    (output / "worlds-map.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source_root, args.output)


if __name__ == "__main__":
    main()
