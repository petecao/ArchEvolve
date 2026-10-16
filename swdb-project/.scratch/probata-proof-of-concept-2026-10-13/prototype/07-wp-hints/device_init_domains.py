"""2026-10-16 ET: prospective source-backed device read/write initializedness.

Exact four-input adapter. Historical models stay unchanged. This is a contract
correction under the declared command TCB, never a proof hint or proof record.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = {'gapbs_models.h': 'eb71f37abca6accc9d50242e50f6affd5e1621508f0529cecadda9fb746b5ddb', 'tdstep_standin.c': 'ab8e1f4c833805c21d291a152e8fcebd62b66bfc945b16d19c344063657b07c5', 'bfs_unit.h': 'a9f3bb9954057676acd2216e05c4051f0782198ed44c7f3088cb309d09eb1d69', 'dxc_summaries.h': 'fc575618bfa6217e23808cc7f9c8963b6059b666b4a0e058e4115e0ad869199e'}


def amend_contract(text, name, requires, ensures):
    pos = text.index("void " + name + "(")
    begin = text.rfind("/*@", 0, pos)
    end = text.index("*/", begin)
    old = text[begin:end + 2]
    if old.count("    terminates ") != 1 or old.count("    exits ") != 1:
        raise ValueError("unsupported command contract context")
    new = old.replace("    terminates ", requires + "    terminates ", 1)
    new = new.replace("    exits ", ensures + "    exits ", 1)
    return text[:begin] + new + text[end + 2:], {"old": old, "new": new,
        "added_requires": requires, "added_ensures": ensures}


def build(source):
    raw = {name: (source / name).read_bytes() for name in PINS}
    for name, value in raw.items():
        if hashlib.sha256(value).hexdigest() != PINS[name]:
            raise ValueError("unsupported changed physical source: " + name)
    files = {name: value.decode("utf-8", errors="strict") for name, value in raw.items()}
    effects = {}
    files["dxc_summaries.h"], effects["__dxc_stream_load"] = amend_contract(
        files["dxc_summaries.h"], "__dxc_stream_load",
        r"""    requires \initialized(base + (dxc_reg[minimum] .. dxc_reg[maximum] - 1));
    requires \valid(dxc_tile_data[dst] + (0 .. TILE_SIZE - 1));
""",
        r"""    ensures \initialized(dxc_tile_data[dst] + (0 .. dxc_tile_len[dst] - 1));
""")
    files["dxc_summaries.h"], effects["__dxc_gather"] = amend_contract(
        files["dxc_summaries.h"], "__dxc_gather",
        r"""    requires \valid_read(dxc_tile_data[index] + (0 .. dxc_tile_len[index] - 1));
    requires \initialized(dxc_tile_data[index] + (0 .. dxc_tile_len[index] - 1));
    requires \forall integer i; 0 <= i < dxc_tile_len[index] ==>
      \initialized(base + dxc_tile_data[index][i]);
    requires \valid(dxc_tile_data[dst] + (0 .. TILE_SIZE - 1));
""",
        r"""    ensures \initialized(dxc_tile_data[dst] + (0 .. dxc_tile_len[dst] - 1));
""")
    files["dxc_summaries.h"], effects["__dxc_range_loop"] = amend_contract(
        files["dxc_summaries.h"], "__dxc_range_loop",
        r"""    requires \valid_read(dxc_tile_data[lower] + (0 .. dxc_tile_len[lower] - 1));
    requires \valid_read(dxc_tile_data[upper] + (0 .. dxc_tile_len[upper] - 1));
    requires \initialized(dxc_tile_data[lower] + (0 .. dxc_tile_len[lower] - 1));
    requires \initialized(dxc_tile_data[upper] + (0 .. dxc_tile_len[upper] - 1));
    requires \valid(dxc_tile_data[rows] + (0 .. TILE_SIZE - 1));
    requires \valid(dxc_tile_data[columns] + (0 .. TILE_SIZE - 1));
""",
        r"""    ensures \initialized(dxc_tile_data[rows] + (0 .. dxc_tile_len[rows] - 1));
    ensures \initialized(dxc_tile_data[columns] + (0 .. dxc_tile_len[columns] - 1));
""")
    manifest = {"method": "t07-device-initializedness-domains-v1", "date_ET": "2026-10-16",
        "input_pins": PINS, "contract_changes": effects,
        "preserved": ["all C tokens", "TD functional postconditions", "all prior command requires/ensures/assigns/termination/exits", "all unchanged gapbs helper bytes", "all historical model directories"],
        "semantics_boundary": "Successful command reads/writes under the existing as-if-completed-at-issue plus separate pending-hazard abstraction; no hardware liveness/completion-at-issue theorem.",
        "untouched_tail_initializedness": "No guarantee; only actually produced prefixes are promised initialized.",
        "source_basis": {"selected_wrapper": "__dxc_stream_load/gather/range_loop map to maa_stream_load/maa_indirect_load/maa_range_loop<int>",
                         "functional_store_lines": {"stream": [531, 550], "gather": [573, 592], "range": [736, 781]},
                         "target_semantics": "Opaque normal-return command/library TCB; existing async coverage/hazard contracts remain unchanged. Functional bodies do not prove hardware visibility or complete range continuation equivalence."},
        "proof_acceptance": False, "TD_or_counted_admissible": False,
        "output_pins": {n: hashlib.sha256(v.encode("utf-8")).hexdigest() for n, v in files.items()}}
    return files, manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=HERE / "standin_private_array_canonical")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists() or a.output.is_symlink(): raise ValueError("fresh output required")
    files, manifest = build(a.source)
    a.output.mkdir(parents=True)
    for name, value in files.items(): (a.output / name).write_bytes(value.encode("utf-8"))
    (a.output / "device-init-map.json").write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__": main()
