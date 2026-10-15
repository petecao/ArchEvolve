"""The ACSL call contracts of semantics.dx100_bfs_0_1 (the WP form), per-tile view. Ticket 27, WP half.

Created: 2026-10-14 ET. Imported by gen_entry.py. Each contract states consequences of the C model (model.h):
preconditions at least as strong as the model's checks, postconditions it guarantees (the per-tile predicates of
logic.acsl), so a WP proof never claims more than the CBMC form allows. Ticket 29 checks the forms agree.
"""

L = {"stream": "lowering.dxc_stream_load.dx100-mmio.1.0-e4fc4af", "gather": "lowering.dxc_gather.dx100-mmio.1.0-e4fc4af",
     "range": "lowering.dxc_range_loop.dx100-mmio.1.0-e4fc4af", "const": "lowering.dxc_const_i32.dx100-mmio.1.0-e4fc4af",
     "wait": "lowering.dxc_wait.dx100-mmio.1.0-e4fc4af", "size": "lowering.dxc_tile_size.dx100-mmio.1.0-e4fc4af",
     "pointer": "lowering.dxc_tile_pointer.dx100-mmio.1.0-e4fc4af",
     "context": "lowering.dxc_thread_context.dx100-mmio.1.0-e4fc4af"}

GHOST = ("dx_live, dx_kind[0 .. DX_K - 1], dx_dst1[0 .. DX_K - 1], dx_dst2[0 .. DX_K - 1], dx_src1[0 .. DX_K - 1], "
         "dx_src2[0 .. DX_K - 1], dx_cond[0 .. DX_K - 1], dx_regs_in[0 .. DX_K - 1], dx_regs_out[0 .. DX_K - 1], "
         "dx_reg_a[0 .. DX_K - 1], dx_reg_b[0 .. DX_K - 1], dx_reg_c[0 .. DX_K - 1], "
         "dx_region[0 .. DX_K - 1], dx_base[0 .. DX_K - 1], dx_lo[0 .. DX_K - 1], dx_hi[0 .. DX_K - 1], "
         "dx_stride[0 .. DX_K - 1], dx_index[0 .. DX_K - 1], dx_deps[0 .. DX_K - 1], dx_writes_memory[0 .. DX_K - 1], "
         "dx_tile_writer[0 .. DX_NT - 1], dx_tile_readers[0 .. DX_NT - 1], dx_reg_writer[0 .. DX_NR - 1], "
         "dx_reg_named[0 .. DX_NR - 1], dx_count")


def command(kind, d1, d2, s1, s2, c, regs=(), writes=()):
    """The common clauses of one issued command; `regs` the registers it names, `writes` those it writes."""
    r = list(regs) + ["-1"] * (3 - len(regs))
    w = list(writes) + ["-1"] * (2 - len(writes))
    return (f"requires ghost_capacity: 0 <= dx_count < DX_K;\nrequires dx_issuable({r[0]}, {r[1]}, {r[2]}, {w[0]}, {w[1]});\n",
            f"ensures dx_new_slot({kind}, {d1}, {d2}, {s1}, {s2}, {c}, {r[0]}, {r[1]}, {r[2]});\n"
            f"ensures dx_stall_covers{{Pre, Post}}({d1}, {d2});\n"
            f"ensures dx_kept{{Pre, Post}}({d1}, {d2}, {s1}, {s2}, {c}, {r[0]}, {r[1]}, {r[2]}, {w[0]}, {w[1]}, 1);\n")


stream_req, stream_ens = command("DX_STREAM_LOAD", "dst_tile", "-1", "-1", "-1", "-1",
                                 ("min_reg", "max_reg", "stride_reg"))
gather_req, gather_ens = command("DX_GATHER", "dst_tile", "-1", "idx_tile", "-1", "-1")
range_req, range_ens = command("DX_RANGE_LOOP", "dst_i_tile", "dst_j_tile", "min_tile", "max_tile", "-1",
                               ("last_i_reg", "last_j_reg", "stride_reg"), ("last_i_reg", "last_j_reg"))
alu_req, alu_ens = command("DX_ALU_SCALAR", "dst_tile", "-1", "src_tile", "-1", "-1", ("src_reg",))
store_req, store_ens = command("DX_STORE_VECTOR", "dst_tile", "-1", "idx_tile", "src_tile", "cond_tile")

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
assigns dx_reg_value[reg], {GHOST};
ensures dx_reg_value[reg] == value;
ensures dx_reg_writer[reg] == -1 && dx_reg_named[reg] == 0;
ensures \\forall integer u; 0 <= u < DX_NT && dx_uses_reg{{Pre}}(\\at(dx_tile_writer[u], Pre), reg) ==>
  dx_tile_writer[u] == -1;
ensures dx_kept{{Pre, Post}}(-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0);"""),
    ("wait_ready", "void wait_ready(int tile)", [L["wait"]],
     ["operands", "wait_counted_roles", "wait_transitive", "wait_range_loop_exception"], f"""\
requires 0 <= tile < DX_NT;
assigns {GHOST};
ensures dx_wait_covers{{Pre, Post}}(tile);
ensures dx_kept{{Pre, Post}}(-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0);"""),
    ("get_tile_size", "unsigned short get_tile_size(int tile)", [L["size"]], ["operands", "unready_size_read"], """\
requires 0 <= tile < DX_NT;
requires dx_tile_writer[tile] == -1;
assigns \\nothing;
ensures \\result == dx_tile_size[tile];"""),
    ("get_cacheable_tile_pointer", "int *get_cacheable_tile_pointer(int tile)", [L["pointer"]],
     ["operands", "tile_pointer"], """\
requires 0 <= tile < DX_NT;
assigns \\nothing;
ensures \\result == &dx_tile_data[tile][0];"""),
    ("maa_stream_load", "void maa_stream_load(int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, "
                        "int cond_tile)", [L["stream"]],
     ["operands", "stream_operands", "stream_values", "dispatch_stall", "register_overlap", "memory_serial_domain"], f"""\
requires 0 <= min_reg < DX_NR && 0 <= max_reg < DX_NR && 0 <= stride_reg < DX_NR && 0 <= dst_tile < DX_NT;
requires memory_domain: dx_memory_clear_after_stall(dst_tile, -1, 0);
requires cond_tile == -1;
requires dx_reg_value[stride_reg] > 0 && dx_reg_value[min_reg] <= dx_reg_value[max_reg];
{stream_req}requires \\forall integer k; 0 <= k < DX_TS && dx_reg_value[min_reg] + k * dx_reg_value[stride_reg] <
  dx_reg_value[max_reg] ==> \\valid_read(data + (dx_reg_value[min_reg] + k * dx_reg_value[stride_reg]));
requires source_initialized: \\forall integer k; 0 <= k < DX_TS && dx_reg_value[min_reg] + k * dx_reg_value[stride_reg] <
  dx_reg_value[max_reg] ==> \\initialized(data + (dx_reg_value[min_reg] + k * dx_reg_value[stride_reg]));
assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST};
{stream_ens}ensures dx_base[dx_tile_writer[dst_tile]] == data && dx_lo[dx_tile_writer[dst_tile]] == \\old(dx_reg_value[min_reg]) &&
  dx_hi[dx_tile_writer[dst_tile]] == \\old(dx_reg_value[max_reg]) &&
  dx_stride[dx_tile_writer[dst_tile]] == \\old(dx_reg_value[stride_reg]);
ensures \\let lo = \\old(dx_reg_value[min_reg]); \\let hi = \\old(dx_reg_value[max_reg]);
  \\let st = \\old(dx_reg_value[stride_reg]); \\let n = (hi == lo ? 0 : (hi - lo - 1) / st + 1);
  dx_tile_size[dst_tile] == (n < DX_TS ? n : DX_TS) &&
  (\\forall integer k; 0 <= k < DX_TS && k < n ==> dx_tile_data[dst_tile][k] == \\old(data[lo + k * st]));"""),
    ("maa_indirect_load", "void maa_indirect_load(int *data, int idx_tile, int dst_tile, int cond_tile)",
     [L["gather"]], ["operands", "gather_values", "dispatch_stall", "memory_serial_domain"], f"""\
requires 0 <= idx_tile < DX_NT && 0 <= dst_tile < DX_NT && dst_tile != idx_tile && cond_tile == -1;
requires memory_domain: dx_memory_clear_after_stall(dst_tile, -1, 0);
{gather_req}requires \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS ==>
  \\valid_read(data + (unsigned int)dx_tile_data[idx_tile][k]);
requires source_initialized: \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS ==>
  \\initialized(data + (unsigned int)dx_tile_data[idx_tile][k]);
assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST};
{gather_ens}ensures dx_base[dx_tile_writer[dst_tile]] == data && dx_index[dx_tile_writer[dst_tile]] == idx_tile;
ensures dx_tile_size[dst_tile] == \\old(dx_tile_size[idx_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_tile_size[idx_tile]) && k < DX_TS ==>
  dx_tile_data[dst_tile][k] == \\old(data[(unsigned int)dx_tile_data[idx_tile][k]]);"""),
    ("maa_range_loop", "void maa_range_loop(int last_i_reg, int last_j_reg, int min_tile, int max_tile, "
                       "int stride_reg, int dst_i_tile, int dst_j_tile, int cond_tile)", [L["range"]],
     ["operands", "range_operands", "range_loop_values", "dispatch_stall", "register_overlap"], f"""\
requires 0 <= last_i_reg < DX_NR && 0 <= last_j_reg < DX_NR && 0 <= stride_reg < DX_NR && last_i_reg != last_j_reg;
requires 0 <= min_tile < DX_NT && 0 <= max_tile < DX_NT && 0 <= dst_i_tile < DX_NT && 0 <= dst_j_tile < DX_NT;
requires dst_i_tile != dst_j_tile && dst_i_tile != min_tile && dst_i_tile != max_tile && dst_j_tile != min_tile &&
  dst_j_tile != max_tile && cond_tile == -1;
requires dx_tile_size[min_tile] == dx_tile_size[max_tile] && dx_reg_value[stride_reg] > 0 && dx_reg_value[last_i_reg] >= 0;
requires 0 <= dx_tile_size[min_tile] <= DX_TS;
{range_req}assigns dx_tile_data[dst_i_tile][0 .. DX_TS - 1], dx_tile_data[dst_j_tile][0 .. DX_TS - 1], dx_tile_size[dst_i_tile],
  dx_tile_size[dst_j_tile], dx_reg_value[last_i_reg], dx_reg_value[last_j_reg], {GHOST};
{range_ens}ensures 0 <= dx_tile_size[dst_i_tile] <= DX_TS && dx_tile_size[dst_j_tile] == dx_tile_size[dst_i_tile];
ensures \\old(dx_reg_value[last_j_reg]) == -1 && \\old(dx_reg_value[last_i_reg]) < \\old(dx_tile_size[min_tile]) &&
  (unsigned int)\\old(dx_tile_data[min_tile][dx_reg_value[last_i_reg]]) <
  (unsigned int)\\old(dx_tile_data[max_tile][dx_reg_value[last_i_reg]]) ==>
  dx_tile_size[dst_j_tile] >= 1 && dx_tile_data[dst_i_tile][0] == \\old(dx_reg_value[last_i_reg]) &&
  dx_tile_data[dst_j_tile][0] == \\old(dx_tile_data[min_tile][dx_reg_value[last_i_reg]]);"""),
    ("maa_alu_scalar", "void maa_alu_scalar(int src_tile, int src_reg, int dst_tile, int op, int cond_tile)", [],
     ["operands", "alu_lt_values", "dispatch_stall", "register_overlap"], f"""\
requires 0 <= src_tile < DX_NT && 0 <= src_reg < DX_NR && 0 <= dst_tile < DX_NT && dst_tile != src_tile;
requires op == DX_LT_OP && cond_tile == -1;
{alu_req}assigns dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST};
{alu_ens}ensures dx_tile_size[dst_tile] == \\old(dx_tile_size[src_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_tile_size[src_tile]) && k < DX_TS ==>
  dx_tile_data[dst_tile][k] == (\\old(dx_tile_data[src_tile][k]) < \\old(dx_reg_value[src_reg]) ? 1 : 0);"""),
    ("maa_indirect_store_vector", "void maa_indirect_store_vector(int *data, int idx_tile, int src_tile, "
                                  "int cond_tile, int dst_tile)", [],
     ["operands", "store_operands", "store_vector_values", "store_duplicate_order", "dispatch_stall", "memory_serial_domain"], f"""\
requires 0 <= idx_tile < DX_NT && 0 <= src_tile < DX_NT && (cond_tile == -1 || 0 <= cond_tile < DX_NT);
requires 0 <= dst_tile < DX_NT && dst_tile != idx_tile && dst_tile != src_tile && dst_tile != cond_tile;
requires memory_domain: dx_memory_clear_after_stall(dst_tile, -1, 1);
requires (\\forall integer swdb_tile; 0 <= swdb_tile < DX_NT ==>
  \\base_addr(data) != \\base_addr(dx_tile_data[swdb_tile])) &&
  \\base_addr(data) != \\base_addr(&dx_tile_size[0]) && \\base_addr(data) != \\base_addr(&dx_reg_value[0]);
requires dx_tile_size[src_tile] == dx_tile_size[idx_tile] &&
  (cond_tile == -1 || dx_tile_size[cond_tile] == dx_tile_size[idx_tile]);
{store_req}requires \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS &&
  (cond_tile == -1 || dx_tile_data[cond_tile][k] != 0) ==> \\valid(data + (unsigned int)dx_tile_data[idx_tile][k]);
requires source_initialized: \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS &&
  (cond_tile == -1 || dx_tile_data[cond_tile][k] != 0) ==> \\initialized(data + (unsigned int)dx_tile_data[idx_tile][k]);
requires store_frame_bound: 0 <= dx_store_bound;
requires store_indices: \\forall integer k; 0 <= k < dx_tile_size[idx_tile] && k < DX_TS &&
  (cond_tile == -1 || dx_tile_data[cond_tile][k] != 0) ==>
  0 <= (unsigned int)dx_tile_data[idx_tile][k] < dx_store_bound;
assigns data[0 .. dx_store_bound - 1],
  dx_tile_data[dst_tile][0 .. DX_TS - 1], dx_tile_size[dst_tile], {GHOST};
{store_ens}ensures dx_base[dx_tile_writer[dst_tile]] == data && dx_index[dx_tile_writer[dst_tile]] == idx_tile;
ensures dx_tile_size[dst_tile] == \\old(dx_tile_size[idx_tile]);
ensures \\forall integer k; 0 <= k < \\old(dx_store_bound) && \\at(\\initialized(data + k), Pre) ==>
  \\initialized(data + k);
ensures \\old(dx_tile_size[idx_tile]) >= 1 && (cond_tile == -1 || \\old(dx_tile_data[cond_tile][0]) != 0) ==>
  dx_tile_data[dst_tile][0] == \\old(data[(unsigned int)dx_tile_data[idx_tile][0]]);"""),
]

# These are explicitly trusted preservation contracts, not body proofs. The
# corresponding C storage is initialized statically/by harness draws; ordinary
# CPU stores cannot clear initialization, and all model memory reads above have
# explicit caller obligations. Ticket 29 validates the forms independently.
INITIALIZED_OUTPUTS = {
    "get_cacheable_tile_pointer": r"\initialized(\result + (0 .. DX_TS - 1))",
    "maa_stream_load": r"\initialized(dx_tile_data[dst_tile] + (0 .. DX_TS - 1))",
    "maa_indirect_load": r"\initialized(dx_tile_data[dst_tile] + (0 .. DX_TS - 1))",
    "maa_alu_scalar": r"\initialized(dx_tile_data[dst_tile] + (0 .. DX_TS - 1))",
    "maa_indirect_store_vector": r"\initialized(dx_tile_data[dst_tile] + (0 .. DX_TS - 1))",
    "maa_range_loop": (r"\initialized(dx_tile_data[dst_i_tile] + (0 .. DX_TS - 1)) && "
                       r"\initialized(dx_tile_data[dst_j_tile] + (0 .. DX_TS - 1))"),
}
CALLS = [(n, p, lw, [*rules, "initialized_state"],
          "requires initialized_state: dx_state_initialized;\n" + contract +
          "\nensures dx_state_initialized;" +
          ("\nensures " + INITIALIZED_OUTPUTS[n] + ";" if n in INITIALIZED_OUTPUTS else ""))
         for n, p, lw, rules, contract in CALLS]

QUERIES = [("swdb_dx_in_footprint", "int swdb_dx_in_footprint(int tile, const int *addr)", """\
requires 0 <= tile < DX_NT;
assigns \\nothing;
ensures \\result == 1 <==> (dx_tile_writer[tile] >= 0 && dx_in_footprint(dx_tile_writer[tile], (int *)addr));""")]

# What WP adds around a unit that calls into this proof semantics (the CBMC form has the same in its harness).
WP = {
    "probes": [
        {"macro": "SWDB_TILE_READ", "prototype": "int *swdb_tile_read_probe(int *addr)",
         "contract": "requires dx_read_ok(addr);\nrequires initialized_read: \\initialized(addr);\n"
                     "assigns \\nothing;\nensures \\result == addr;\nensures \\initialized(\\result);\n"},
        {"macro": "SWDB_TILE_WRITE", "prototype": "int *swdb_tile_write_probe(int *addr)",
         "contract": "requires dx_write_ok(addr);\nassigns \\nothing;\nensures \\result == addr;\n"},
    ],
    "unit_requires": "dx_idle && dx_state_initialized",
    "separate_from": ["dx_tile_data", "dx_tile_size", "dx_reg_value"],
}
