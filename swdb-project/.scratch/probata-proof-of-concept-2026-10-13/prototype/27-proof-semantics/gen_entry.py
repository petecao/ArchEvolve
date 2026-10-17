"""Write library/proof_semantics/dx100_bfs_0_1.yaml (ticket 27). Run from swdb-project with the repo path."""
import hashlib
import sys
from pathlib import Path

import yaml

ROOT = Path(sys.argv[1])
LIB = ROOT / "library"
C = "e4fc4afdf894f295442cef3604667a469fab8e62"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(rel, root="library"):
    base = LIB if root == "library" else ROOT
    return {"root": root, "path": rel, "sha256": sha(base / rel)}


def cite(path, lines):
    return {"gem5_commit": C, "path": f"src/mem/MAA/{path}", "lines": lines}


RULES = [
    ("operands", "Tile operands name one of the core's tiles and register operands one of its registers; a "
                 "command's destination tile is none of its source tiles (MAA.cc:563-566 asserts it at dispatch).",
     cite("MAA.cc", "563-566")),
    ("allocation", "get_new_tile and get_new_reg hand out the core's 8 tiles and 8 scalar registers (MAA.py "
                   "num_tiles_per_core, num_regs_per_core); one more is a hazard.", cite("MAA.py", "13-15")),
    ("regions", "add_mem_region registers one memory region (at most DX_NM); clear_mem_region forgets them. "
                "Which region a command uses, and the region stall, are ticket 28's rules.", {"owner": "Eric"}),
    ("wait_counted_roles", "wait_ready(t) returns when no unfinished command names t as src1, src2, dst1 or dst2; "
                           "a condition tile is not counted (ready counter: MAA.cc:563-580 at dispatch, 605-620 at "
                           "finish; SPD.cc:120-139; blocking read CpuSidePort.cc:295-315).", cite("MAA.cc", "563-580")),
    ("wait_transitive", "A command finishes only after the producers of its input tiles finished, so a wait also "
                        "covers those producers, transitively (IndirectAccess.cc:399-459; ALU.cc:199-246; "
                        "StreamAccess.cc:305-316).", cite("IndirectAccess.cc", "399-459")),
    ("wait_range_loop_exception", "A range loop finishes without waiting for the producers of its min, max or "
                                  "condition tiles, so coverage never passes through a range loop.",
     cite("RangeFuser.cc", "211-219")),
    ("dispatch_stall", "A command is not dispatched while its destination tile is any unfinished command's source, "
                       "destination or condition tile, and the issuing call returns only at dispatch; so issuing "
                       "it covers every uncovered command that names that tile in any role.", cite("IF.cc", "193-212")),
    ("register_write_stall", "A CPU write to a scalar register is held until no unfinished command names the "
                             "register; so maa_const covers every uncovered command that names it.",
     cite("IF.cc", "233-249")),
    ("register_overlap", "No gem5 rule orders a command after an unfinished command on a register (issue checks "
                         "tile status only), so issuing a command that shares a register with an uncovered command "
                         "where either writes it is a hazard (ticket 41, F6).", cite("IF.cc", "279-299")),
    ("memory_serial_domain", "Conservative proof-domain restriction until ticket 28: after destination-stall "
                            "coverage, a device store needs no uncovered memory command, and a device load needs "
                            "no uncovered device store. An indirect store copies a whole cache line, updates "
                            "selected words, and writes back the whole line; selected-element disjointness "
                            "therefore does not establish absence of memory interference. Domain failure is "
                            "not proven, never a refutation of the program.",
     cite("IndirectAccess.cc", "898-940, 1145-1158")),
    ("unready_read", "A CPU read of tile memory is not blocked while a command fills the tile, so reading a tile "
                     "through its tile pointer while an uncovered command writes it is a hazard (map 12 item 3).",
     cite("CpuSidePort.cc", "346-360")),
    ("cpu_write_overlap", "A CPU write to tile memory is not ordered with a running command that reads or writes "
                          "the tile element by element, so writing a tile that an uncovered command names as a "
                          "reader or writer is a hazard; reading a tile an uncovered command only reads is not.",
     cite("SPD.cc", "140-157")),
    ("unready_size_read", "A tile's size is set when its command finishes, so get_tile_size before a wait covers "
                          "the tile's writer is a hazard like an unready read (stream StreamAccess.cc:336-341; "
                          "indirect IndirectAccess.cc:470-473; range loop RangeFuser.cc:235-237).",
     cite("StreamAccess.cc", "336-341")),
    ("tile_pointer", "get_cacheable_tile_pointer gives the tile's elements in the CPU's cacheable tile range.",
     cite("CpuSidePort.cc", "346-353")),
    ("stream_values", "maa_stream_load fills dst[k] = data[min + k * stride] for k < n, n = 0 if max == min else "
                      "min(TILE_SIZE, (max - min - 1) / stride + 1), from registers min, max, stride; size n.",
     cite("StreamAccess.cc", "143-146")),
    ("stream_operands", "The stream formula is used only with stride > 0 and min <= max; anything else is a "
                        "hazard (gem5 gives a negative or undefined count).", {"owner": "Eric"}),
    ("gather_values", "maa_indirect_load fills dst[k] = data[idx[k]] (index read as uint32) for k < size(idx); "
                      "size = size(idx).", cite("IndirectAccess.cc", "413-418, 491-492")),
    ("range_loop_values", "maa_range_loop continues from registers (last_i, last_j): for i from last_i below "
                          "size(min), j from min[i] (or last_j) while j < max[i] (unsigned), step stride, it emits "
                          "(i, j) pairs until TILE_SIZE are emitted; it writes last_i, last_j back and both sizes.",
     cite("RangeFuser.cc", "84-93, 154-208, 233-237")),
    ("range_operands", "size(min) == size(max) (gem5 panics otherwise); stride > 0 and last_i >= 0 are assumed "
                       "(otherwise gem5 loops forever or reads outside the tile).", cite("RangeFuser.cc", "126-143")),
    ("alu_lt_values", "maa_alu_scalar with LT_OP on int32 fills dst[k] = (src[k] < reg) ? 1 : 0 for k < size(src); "
                      "size = size(src).", cite("ALU.cc", "357-447")),
    ("store_vector_values", "maa_indirect_store_vector, for k < size(idx) with cond[k] != 0 (or no condition): "
                            "dst[k] = the old data[idx[k]], then data[idx[k]] = src[k]; size(dst) = size(idx).",
     cite("IndirectAccess.cc", "905-933")),
    ("store_operands", "size(src) and size(cond) equal size(idx) (gem5 panics otherwise).",
     cite("IndirectAccess.cc", "399-418")),
    ("store_duplicate_order", "With a repeated index, the lanes take effect in element order (the old value a lane "
                              "returns includes earlier lanes' writes).", {"owner": "Eric"}),
]

GHOST_ASSIGNS = ("dx_live, dx_kind[0 .. DX_K - 1], dx_dst1[0 .. DX_K - 1], dx_dst2[0 .. DX_K - 1], "
                 "dx_src1[0 .. DX_K - 1], dx_src2[0 .. DX_K - 1], dx_cond[0 .. DX_K - 1], dx_regs_in[0 .. DX_K - 1], "
                 "dx_regs_out[0 .. DX_K - 1], dx_region[0 .. DX_K - 1], dx_base[0 .. DX_K - 1], dx_lo[0 .. DX_K - 1], "
                 "dx_hi[0 .. DX_K - 1], dx_stride[0 .. DX_K - 1], dx_index[0 .. DX_K - 1], dx_deps[0 .. DX_K - 1], "
                 "dx_writes_memory[0 .. DX_K - 1], dx_tile_writer[0 .. DX_NT - 1], dx_tile_readers[0 .. DX_NT - 1], "
                 "dx_reg_writer[0 .. DX_NR - 1]")
COVER_ASSIGNS = ("dx_live, dx_deps[0 .. DX_K - 1], dx_tile_writer[0 .. DX_NT - 1], dx_tile_readers[0 .. DX_NT - 1], "
                 "dx_reg_writer[0 .. DX_NR - 1]")

L = {"stream": "lowering.dxc_stream_load.dx100-mmio.1.0-e4fc4af", "gather": "lowering.dxc_gather.dx100-mmio.1.0-e4fc4af",
     "range": "lowering.dxc_range_loop.dx100-mmio.1.0-e4fc4af", "const": "lowering.dxc_const_i32.dx100-mmio.1.0-e4fc4af",
     "wait": "lowering.dxc_wait.dx100-mmio.1.0-e4fc4af", "size": "lowering.dxc_tile_size.dx100-mmio.1.0-e4fc4af",
     "pointer": "lowering.dxc_tile_pointer.dx100-mmio.1.0-e4fc4af",
     "context": "lowering.dxc_thread_context.dx100-mmio.1.0-e4fc4af"}

CALLS = [
    ("get_new_tile", "int get_new_tile(void)", [L["context"]], ["allocation"], """\
requires dx_next_tile < DX_NT;
assigns dx_next_tile, dx_tile_owner[dx_next_tile];
ensures \\result == \\old(dx_next_tile) && dx_next_tile == \\old(dx_next_tile) + 1;
ensures dx_tile_owner[\\result] == 0;"""),
    ("get_new_reg", "int get_new_reg(void)", [L["context"]], ["allocation"], """\
requires dx_next_reg < DX_NR;
assigns dx_next_reg, dx_reg_owner[dx_next_reg];
ensures \\result == \\old(dx_next_reg) && dx_next_reg == \\old(dx_next_reg) + 1;
ensures dx_reg_owner[\\result] == 0;"""),
    ("add_mem_region", "void add_mem_region(void *start, void *end)", [], ["regions"], """\
requires dx_regions < DX_NM;
assigns dx_regions;
ensures dx_regions == \\old(dx_regions) + 1;"""),
    ("clear_mem_region", "void clear_mem_region(void)", [], ["regions"], """\
assigns dx_regions;
ensures dx_regions == 0;"""),
    ("maa_const", "void maa_const(int value, int reg)", [L["const"]], ["operands", "register_write_stall"], f"""\
requires 0 <= reg < DX_NR;
requires dx_ghost_ok;
assigns dx_reg_value[reg], {COVER_ASSIGNS};
ensures dx_reg_value[reg] == value;
ensures dx_live == (\\old(dx_live) & ~\\old(dx_close(dx_reg_users(reg, DX_K), DX_K)));
ensures dx_links_after_cover{{Pre, Post}};
ensures dx_ghost_ok;"""),
    ("wait_ready", "void wait_ready(int tile)", [L["wait"]],
     ["operands", "wait_counted_roles", "wait_transitive", "wait_range_loop_exception"], f"""\
requires 0 <= tile < DX_NT;
requires dx_ghost_ok;
assigns {COVER_ASSIGNS};
ensures dx_live == (\\old(dx_live) & ~\\old(dx_close(dx_counted(tile, DX_K), DX_K)));
ensures dx_links_after_cover{{Pre, Post}};
ensures dx_ghost_ok;"""),
    ("get_tile_size", "unsigned short get_tile_size(int tile)", [L["size"]], ["operands", "unready_size_read"], """\
requires 0 <= tile < DX_NT;
requires dx_read_ready(tile);
assigns \\nothing;
ensures \\result == dx_tile_size[tile];"""),
    ("get_cacheable_tile_pointer", "int *get_cacheable_tile_pointer(int tile)", [L["pointer"]],
     ["operands", "tile_pointer"], """\
requires 0 <= tile < DX_NT;
assigns \\nothing;
ensures \\result == &dx_tile_data[tile][0];"""),
    ("maa_stream_load", "void maa_stream_load(int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, "
                        "int cond_tile)", [L["stream"]],
     ["operands", "stream_operands", "stream_values", "dispatch_stall", "register_overlap"], f"""\
requires 0 <= min_reg < DX_NR && 0 <= max_reg < DX_NR && 0 <= stride_reg < DX_NR && 0 <= dst_tile < DX_NT;
requires cond_tile == -1;
requires dx_reg_value[stride_reg] > 0 && dx_reg_value[min_reg] <= dx_reg_value[max_reg];
requires dx_ghost_ok;
requires dx_may_issue(dst_tile, -1, (1 << min_reg) | (1 << max_reg) | (1 << stride_reg), 0);
requires \\forall integer k; 0 <= k < DX_TS && dx_reg_value[min_reg] + k * dx_reg_value[stride_reg] <
  dx_reg_value[max_reg] ==> \\valid_read(data + (dx_reg_value[min_reg] + k * dx_reg_value[stride_reg]));
assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST_ASSIGNS};
ensures dx_issued{{Pre, Post}}(DX_STREAM_LOAD, dst_tile, -1, -1, -1, -1,
  (1 << min_reg) | (1 << max_reg) | (1 << stride_reg), 0);
ensures \\let lo = \\old(dx_reg_value[min_reg]); \\let hi = \\old(dx_reg_value[max_reg]);
  \\let st = \\old(dx_reg_value[stride_reg]); \\let n = (hi == lo ? 0 : (hi - lo - 1) / st + 1);
  dx_tile_size[dst_tile] == (n < DX_TS ? n : DX_TS) &&
  (\\forall integer k; 0 <= k < DX_TS && k < n ==> dx_tile_data[dst_tile][k] == \\old(data[lo + k * st]));
ensures dx_ghost_ok;"""),
    ("maa_indirect_load", "void maa_indirect_load(int *data, int idx_tile, int dst_tile, int cond_tile)",
     [L["gather"]], ["operands", "gather_values", "dispatch_stall"], f"""\
requires 0 <= idx_tile < DX_NT && 0 <= dst_tile < DX_NT && dst_tile != idx_tile && cond_tile == -1;
requires dx_ghost_ok && dx_may_issue(dst_tile, -1, 0, 0);
requires \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS ==>
  \\valid_read(data + (unsigned int)dx_tile_data[idx_tile][k]);
assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST_ASSIGNS};
ensures dx_issued{{Pre, Post}}(DX_GATHER, dst_tile, -1, idx_tile, -1, -1, 0, 0);
ensures dx_tile_size[dst_tile] == \\old(dx_tile_size[idx_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_tile_size[idx_tile]) && k < DX_TS ==>
  dx_tile_data[dst_tile][k] == \\old(data[(unsigned int)dx_tile_data[idx_tile][k]]);
ensures dx_ghost_ok;"""),
    ("maa_range_loop", "void maa_range_loop(int last_i_reg, int last_j_reg, int min_tile, int max_tile, "
                       "int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile)", [L["range"]],
     ["operands", "range_operands", "range_loop_values", "dispatch_stall", "register_overlap"], f"""\
requires 0 <= last_i_reg < DX_NR && 0 <= last_j_reg < DX_NR && 0 <= stride_reg < DX_NR && last_i_reg != last_j_reg;
requires 0 <= min_tile < DX_NT && 0 <= max_tile < DX_NT && 0 <= dst_i_tile < DX_NT && 0 <= dst_j_tile < DX_NT;
requires dst_i_tile != dst_j_tile && dst_i_tile != min_tile && dst_i_tile != max_tile && dst_j_tile != min_tile &&
  dst_j_tile != max_tile && cond_tile == -1;
requires dx_tile_size[min_tile] == dx_tile_size[max_tile] && dx_reg_value[stride_reg] > 0 && dx_reg_value[last_i_reg] >= 0;
requires dx_ghost_ok;
requires dx_may_issue(dst_i_tile, dst_j_tile, (1 << last_i_reg) | (1 << last_j_reg) | (1 << stride_reg),
  (1 << last_i_reg) | (1 << last_j_reg));
assigns dx_tile_data[dst_i_tile][0 .. DX_TS - 1], dx_tile_data[dst_j_tile][0 .. DX_TS - 1], dx_tile_size[dst_i_tile],
  dx_tile_size[dst_j_tile], dx_reg_value[last_i_reg], dx_reg_value[last_j_reg], {GHOST_ASSIGNS};
ensures dx_issued{{Pre, Post}}(DX_RANGE_LOOP, dst_i_tile, dst_j_tile, min_tile, max_tile, -1,
  (1 << last_i_reg) | (1 << last_j_reg) | (1 << stride_reg), (1 << last_i_reg) | (1 << last_j_reg));
ensures 0 <= dx_tile_size[dst_i_tile] <= DX_TS && dx_tile_size[dst_j_tile] == dx_tile_size[dst_i_tile];
ensures \\forall integer k; 0 <= k < dx_tile_size[dst_i_tile] ==>
  \\let i = dx_tile_data[dst_i_tile][k]; \\old(dx_reg_value[last_i_reg]) <= i < \\old(dx_tile_size[min_tile]) &&
  (unsigned int)dx_tile_data[dst_j_tile][k] < \\old((unsigned int)dx_tile_data[max_tile][i]);
ensures dx_ghost_ok;"""),
    ("maa_alu_scalar", "void maa_alu_scalar(int src_tile, int src_reg, int dst_tile, int op, int cond_tile)", [],
     ["operands", "alu_lt_values", "dispatch_stall", "register_overlap"], f"""\
requires 0 <= src_tile < DX_NT && 0 <= src_reg < DX_NR && 0 <= dst_tile < DX_NT && dst_tile != src_tile;
requires op == DX_LT_OP && cond_tile == -1;
requires dx_ghost_ok && dx_may_issue(dst_tile, -1, 1 << src_reg, 0);
assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST_ASSIGNS};
ensures dx_issued{{Pre, Post}}(DX_ALU_SCALAR, dst_tile, -1, src_tile, -1, -1, 1 << src_reg, 0);
ensures dx_tile_size[dst_tile] == \\old(dx_tile_size[src_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_tile_size[src_tile]) && k < DX_TS ==>
  dx_tile_data[dst_tile][k] == (\\old(dx_tile_data[src_tile][k]) < \\old(dx_reg_value[src_reg]) ? 1 : 0);
ensures dx_ghost_ok;"""),
    ("maa_indirect_store_vector", "void maa_indirect_store_vector(int *data, int idx_tile, int src_tile, "
                                  "int cond_tile, int dst_tile)", [],
     ["operands", "store_operands", "store_vector_values", "store_duplicate_order", "dispatch_stall"], f"""\
requires 0 <= idx_tile < DX_NT && 0 <= src_tile < DX_NT && (cond_tile == -1 || 0 <= cond_tile < DX_NT);
requires dst_tile == -1 || (0 <= dst_tile < DX_NT && dst_tile != idx_tile && dst_tile != src_tile);
requires dx_tile_size[src_tile] == dx_tile_size[idx_tile] &&
  (cond_tile == -1 || dx_tile_size[cond_tile] == dx_tile_size[idx_tile]);
requires dx_ghost_ok && dx_may_issue(dst_tile, -1, 0, 0);
requires \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS &&
  (cond_tile == -1 || dx_tile_data[cond_tile][k] != 0) ==> \\valid(data + (unsigned int)dx_tile_data[idx_tile][k]);
assigns *(data + {{ (unsigned int)dx_tile_data[idx_tile][k] | integer k; 0 <= k < DX_TS }}),
  dx_tile_data[0 .. DX_NT - 1][0 .. DX_TS - 1], dx_tile_size[0 .. DX_NT - 1], {GHOST_ASSIGNS};
ensures dx_issued{{Pre, Post}}(DX_STORE_VECTOR, dst_tile, -1, idx_tile, src_tile, cond_tile, 0, 0);
ensures dst_tile >= 0 ==> dx_tile_size[dst_tile] == \\old(dx_tile_size[idx_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_tile_size[idx_tile]) && k < DX_TS &&
  (cond_tile == -1 || \\old(dx_tile_data[cond_tile][k]) != 0) ==>
  \\exists integer k2; 0 <= k2 < \\old(dx_tile_size[idx_tile]) && k2 < DX_TS &&
    \\old(dx_tile_data[idx_tile][k2]) == \\old(dx_tile_data[idx_tile][k]) &&
    data[(unsigned int)\\old(dx_tile_data[idx_tile][k])] == \\old(dx_tile_data[src_tile][k2]);
ensures dx_ghost_ok;"""),
]

QUERIES = [("swdb_dx_in_footprint", "int swdb_dx_in_footprint(int tile, const int *addr)", """\
requires 0 <= tile < DX_NT;
assigns \\nothing;
ensures \\result == 1 <==> (dx_tile_writer[tile] >= 0 && dx_in_footprint(dx_tile_writer[tile], (int *)addr));""")]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_wp import CALLS, QUERIES, WP  # noqa: E402,F811  (the WP-form contracts, ticket 27 WP half)

RULES.append(("initialized_state", "The working C model has initialized fixed device storage: static globals "
              "start initialized and harness state draws assign initialized tile values. Trusted call contracts "
              "preserve dx_state_initialized, requiring initialized ordinary-memory cells before reading them; "
              "ordinary CPU stores preserve initialized storage after their RHS initialization obligations. "
              "This is a model representation invariant, not an assumed caller-buffer premise or a body proof; "
              "ticket 29 checks contract/body agreement.", {"owner": "SWDB proof-semantics model"}))

SOURCES = [
    {**pin("dx100/dxc_lowering.hpp"), "role": "lowerings"},
    {**pin("dx100/bfs_read_offload.inc"), "role": "offload"},
    {**pin("dx100/peter-section5.patch"), "role": "setup"},
    {**pin("apps/dx100/benchmarks/gapbs/src/bfs.cc", root="project"), "role": "function", "function": "TDStepMAA"},
]

sys.path.insert(0, str(ROOT))
from swdb import proof_semantics  # noqa: E402

inventory = proof_semantics.inventory(LIB, SOURCES)
offload_calls = set(proof_semantics.inventory(LIB, SOURCES[:3]))
tdstep_calls = set(proof_semantics.inventory(LIB, SOURCES[3:]))


def used_by(name):
    return [label for label, found in (("bfs_read_offload", offload_calls), ("TDStepMAA", tdstep_calls))
            if name in found]

entry = {
    "id": "semantics.dx100_bfs_0_1",
    "kind": "proof_semantics",
    "formal_frame": 1,
    "version": "0.1",
    "sequence": 1,
    "target": "dx100-mmio",
    "description": ("DX100 proof semantics, working version 0.1 (ticket 27): the dx100-mmio 1.0-e4fc4af calls the "
                    "BFS read offload's lowerings and the authors' TDStepMAA make. Values as if each command finished "
                    "at issue; hazards checked against ghost state (K = 32 uncovered commands per thread). Ticket 28 "
                    "supersedes it (remaining calls, memory overlap, region stall, ownership)."),
    "provenance": {"origin": {"probata_ticket": "27", "created": "2026-10-14 ET",
                              "research": ".scratch/formal-verification-2026-10-09/research/14-dx100-wait-rule.md",
                              "rocq": "library/rocq/probata/Reduction.v (ticket 41: F2, F5, F6)"}},
    "hardware_interface": {"id": "dx100-mmio", "version": "1.0-e4fc4af", "gem5_commit": C},
    "constants": {"DX_K": 32, "DX_NT": 8, "DX_NR": 8, "DX_NM": 8, "DX_TS": 2},
    "inventory": {"read": "2026-10-14 ET (ticket 27 start)", "sources": SOURCES, "calls": inventory},
    "ghost": {"acsl": pin("proof_semantics/dx100_bfs/ghost.acsl"), "capacity": {"commands": 32}},
    "model": {"state": pin("proof_semantics/dx100_bfs/state.h"), "c": pin("proof_semantics/dx100_bfs/model.h"),
              "logic": pin("proof_semantics/dx100_bfs/logic.acsl")},
    "clauses": [],
    "rules": [{"id": i, "statement": s, **({"cites": c} if "gem5_commit" in c else {"assumed": c})}
              for i, s, c in RULES],
    "calls": [{"call": n, "prototype": p, "lowerings": lw, "used_by": used_by(n),
               "rules": r, "contract": ct + "\n"} for n, p, lw, r, ct in CALLS],
    "queries": [{"query": n, "prototype": p, "contract": ct + "\n"} for n, p, ct in QUERIES],
    "wp": WP,
}
(LIB / "proof_semantics" / "dx100_bfs_0_1.yaml").write_text(
    "# DX100 proof semantics 0.1 (Probata proof of concept ticket 27). Created: 2026-10-14 ET.\n"
    "# Format: docs/reference/format-v0.4-proof-semantics.md. Every rule cites gem5 DX100 at e4fc4af or names an owner.\n"
    + yaml.safe_dump(entry, sort_keys=False, width=110))
print("calls", inventory)
