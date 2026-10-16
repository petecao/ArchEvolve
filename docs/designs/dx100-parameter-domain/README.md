# DX100 bounded-explorer parameter handoff — October 16

This answers Josh's request against public artifact **`e4fc4afdf894f295442cef3604667a469fab8e62`**, including its gem5 model, config forwarding, software API and modified BFS. The [machine-readable contract](contract.yaml) contains all 26 declared numeric/Boolean model knobs, their exact defaults, CLI availability, necessary constraints, software changes and 17 pinned source hashes/links. It is an exchange format; Josh's explorer schema has not been assumed.

## Suggested message to Josh

For DX100, I'd start with `num_tile_elements ∈ {1024, 2048, 4096, 8192, 16384, 32768}`, default **16384**, with the remaining reference geometry frozen initially. Those six values are explicitly handled by the pinned BFS kernel and appear in the authors' tile-sensitivity results. Please label them **kernel-supported / author-reported candidates**; the independently correctness-validated configuration list remains empty in this handoff.

The reference is 4 cores, 1 DX100 instance, 8 physical 32-bit tiles/core, 8 scalar slots/core, 8 instruction slots/core, row-table rows/slice 64, burst entries/subslice-row 8, row configuration-cache 16, initial slices 32, request-table 128 addresses×16 entries/address, 16 ALU lanes, 4 scratchpad read and 4 write ports/instance and 1-cycle latency defaults. Effective launcher/config.ini settings override these declared defaults.

The important couplings are:

- **Tile size and software:** simulator `num_tile_elements` must match compiled `TILE_SIZE`. Tile size changes MMIO region sizes and pointer strides, so rebuild the kernel for every size. Other BFS sizes need kernel dispatch changes; a general hardware requirement that tile size be a power of two is unresolved.
- **Storage:** scratchpad payload is `4 × cores × tiles_per_core × tile_elements` bytes, or 2 MiB at reference. Offset-table allocation follows tile length automatically. Row/request tables have separate geometry; no equality tying their capacity to tile length has been established.
- **Lengths and operand IDs:** tile lengths use `uint16_t`; full-tile production requires `N≤65535` with the current bookkeeping. This is a necessary representability bound, not a validated interval. Operand IDs occupy 8-bit fields with `0xff` reserved: use IDs 0–254. Wide 64-bit values reserve two adjacent 32-bit slots; changing these formats requires API/model/decoder audits.
- **Threads:** the pinned BFS allocates **8 tiles and 8 scalar slots per worker**, and indexes per-worker arrays of length `NUM_CORES`. At reference, admit at most 4 workers with exclusive allocation/lifetimes. The separate five-tile hybrid sketch has its own resource contract.
- **Cores/instances:** require positive counts and `cores % instances == 0`. Keep power-of-two core counts for the current address decoder/interleaving. Stock API memory-map branches support `{4,8,16}` cores; this is source support, not validation of all instance combinations. Changing per-core tile/register counts requires editing/parameterizing the API's unconditional 8-slot definitions and rebuilding.
- **Row-table slices:** bind actual DRAM topology first. Let `B=channels×ranks×bankgroups×banks` and `Smin=2×channels×ranks`. The implementation enumerates `Smin,2Smin,…,B`; the ratio must fit the integral doubling/halving geometry and bank divisibility/coverage checks. With reconfiguration off, `initial_slices` must belong to that family. Keep 32 only when the selected topology admits it.
- **Other knobs:** row/request capacities, lane/port counts, instruction depth, timing and mode flags are exposed in the model, but their complete legal/validated domains remain unresolved. Freeze them initially. Positive counts and representable/integral geometry are necessary, and request-table per-address entry exhaustion can assert. Please avoid manufacturing ranges from `Param.Unsigned`.

I suggest retaining separate fields for **reference default**, **source-supported candidate**, **necessary constraints**, **validated tuple/receipt**, and **unresolved domain**. Each accepted tile point should have a matching binary/configuration and BFS correctness/intended-path check. Changing tile size also changes software batching/fallback behavior in this kernel, so its performance sweep is a HW/SW experiment.

## Complete declared knob inventory

A null legal domain in the YAML means unresolved. A Boolean's representable values do not establish both modes' correctness or API compatibility. The default initial explorer varies only the six BFS tile sizes; every other knob is frozen pending evidence. CLI-null fields need explicit forwarding/configuration work before exposing them as usable explorer knobs.

| Model parameter | Declared reference default | Stock option |
|---|---:|---|
| `num_tiles_per_core` | `8` | `--maa_num_tiles_per_core` |
| `num_tile_elements` | `16384` | `--maa_num_tile_elements` |
| `num_regs_per_core` | `8` | `--maa_num_regs_per_core` |
| `num_instructions_per_core` | `8` | `--maa_num_instructions_per_core` |
| `num_row_table_rows_per_slice` | `64` | `--maa_num_row_table_rows_per_slice` |
| `num_row_table_entries_per_subslice_row` | `8` | `--maa_num_row_table_entries_per_subslice_row` |
| `num_row_table_config_cache_entries` | `16` | `--maa_num_row_table_config_cache_entries` |
| `num_request_table_addresses` | `128` | `--maa_num_request_table_addresses` |
| `num_request_table_entries_per_address` | `16` | `--maa_num_request_table_entries_per_address` |
| `reconfigure_row_table` | `false` | `--maa_reconfigure_row_table` |
| `no_reorder` | `false` | `--maa_no_reorder` |
| `force_cache_access` | `false` | `--maa_force_cache_access` |
| `num_initial_row_table_slices` | `32` | `--maa_num_initial_row_table_slices` |
| `spd_read_latency` | `1` | `--maa_spd_read_latency` |
| `spd_write_latency` | `1` | `--maa_spd_write_latency` |
| `num_spd_read_ports_per_maa` | `4` | `--maa_num_spd_read_ports_per_maa` |
| `num_spd_write_ports_per_maa` | `4` | `--maa_num_spd_write_ports_per_maa` |
| `rowtable_latency` | `1` | `--maa_rowtable_latency` |
| `ALU_lane_latency` | `1` | `--maa_ALU_lane_latency` |
| `num_ALU_lanes` | `16` | `--maa_num_ALU_lanes` |
| `cache_snoop_latency` | `1` | Unresolved forwarding / direct SimObject configuration |
| `max_outstanding_cache_side_packets` | `512` | Unresolved forwarding / direct SimObject configuration |
| `max_outstanding_cpu_side_packets` | `512` | Unresolved forwarding / direct SimObject configuration |
| `num_memory_channels` | `2` | `--mem-channels` |
| `num_cores` | `4` | `--num-cpus` |
| `num_maas` | `1` | `--maa_num_maas` |

## Row-table and cost accounting

For `S` slices, `R` rows/slice and `E` burst entries/subslice-row:

- subslices per slice: `B/S`;
- row slots: `S×R`;
- burst-entry slots per row: `E×B/S`;
- nominal total burst-entry slots: `R×E×B`.

The implementation doubles slices and halves per-row capacity across alternatives, preserving that nominal total. Actual metadata, offset lists and control still need their own accounting. The simulator allocates alternative configuration objects; summing their host allocations would misrepresent a reconfigurable hardware implementation.

The existing physical cost proxy `0.495 + 3.566×N/16384` mm² is bound to 32 tiles and the paper's 28 nm scope. Cost arithmetic accepting an integer does not certify that kernel/hardware configuration. Tile count, tables, ports and lane changes require their own area effects. See the [hardware catalog handoff](../../hardware-catalog-handoff.md) for the source/version boundary.

## Evidence and admission

The YAML pins source files to their Git object content, independently of the live DX100 checkout. Source defaults were extracted from the SimObject AST, CLI names checked against Options.py, coupling constraints inspected in the implementation and BFS/API allocations checked directly. [Published performance provenance](published-dx100-calibration.json) retains the author-reported evidence tier.

Before calling a point validated, retain the complete tuple, source/binary/config.ini/input/root/thread/ROI identities, correctness result and intended-path witness. Use actual DRAM organization for slice checks and match API/kernel geometry to the effective simulator configuration. Unresolved dimensions stay fixed or explicitly blocked until their domains are established.
