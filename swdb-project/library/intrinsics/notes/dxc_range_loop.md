# Usage note: `__dxc_range_loop` (`intrinsic.dxc_range_loop`)

Created: 2026-10-04 ET (ticket 64). Non-normative: this note is not part of the library entry,
its content hash or its certification. It restates the entry's interface; it changes no semantics.
Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

```c++
void __dxc_range_loop(int last_i_reg, int last_j_reg, int lower_tile, int upper_tile,
                      int stride_reg, int rows_tile, int cols_tile);
```

## Operand kinds

Every operand is a handle, never a value.

| Operand | Kind | Holds |
|---|---|---|
| `last_i_reg` | register handle (`c.reg[k]` of the thread's `dxc_context`) | next row index into the bound tiles |
| `last_j_reg` | register handle | column cursor within that row; `-1` means "row not started" |
| `lower_tile`, `upper_tile` | tile handles (`c.tile[k]`) | row start and row end bounds, equal sizes |
| `stride_reg` | register handle | column step, a value > 0 (1 for CSR rows) |
| `rows_tile`, `cols_tile` | tile handles | output `(i, j)` pairs |

A register's value is set only with `__dxc_const_i32(value, reg)`. Passing a number where a
register handle is expected fails the strict layer's `register_handle` or
`thread_ownership_register` check.

## Continuation convention

- Before the first call of a batch (each new pair of bound tiles), set
  `last_i_reg` to **0** and `last_j_reg` to **-1**:
  `__dxc_const_i32(0, last_i_reg); __dxc_const_i32(-1, last_j_reg);`
- Do not reset them between the calls of one batch. Each call reads them, emits at most one
  tile of `(i, j)` pairs, and writes back where it stopped.
- Repeat the call until the output tile is empty: `__dxc_wait(cols_tile)`, then
  `__dxc_tile_size(cols_tile) == 0` ends the batch.
- `last_i_reg = -1` is **invalid**. Only `last_j_reg` uses -1.

The strict layer's `range_bounds` check enforces: equal bound-tile sizes, stride > 0 and
`0 <= last_i <= bound-tile size`.

## Sources

- Peter v1.1 (`docs/bfs-intrinsics-spec-yanru.md` at `0b56895`), section 3.3 preconditions:
  `last_i_reg` initialized to `0` and `last_j_reg` to `-1` at the start of a batch. The section 3.3
  and section 5 code types `stride` as `int32_t` and writes `dxc_reg_t last_i = 0;`; on this
  interface those operands are register handles set by `__dxc_const_i32`.
- The authors' functional model, `apps/dx100/benchmarks/API/MAA_functional.hpp` line 734:
  "for each tile of i, set last_i_reg to 0 and last_j_reg to -1".
- The strict layer, `library/dx100/strict/MAA_functional.hpp` `maa_range_loop` (`range_bounds`).
- The certified ticket 20 lowering use (receipt chain in ticket 13) follows the same convention.
