# Usage note: `__dxc_stream_load` (`intrinsic.dxc_stream_load`)

Created: 2026-10-04 ET (ticket 64). Non-normative: this note is not part of the library entry,
its content hash or its certification. It restates the entry's interface; it changes no semantics.
Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

```c++
template<class T> void __dxc_stream_load(T* base, int min_reg, int max_reg, int stride_reg, int dst_tile);
```

- `base` is a pointer. `min_reg`, `max_reg` and `stride_reg` are **register handles**
  (`c.reg[k]` of the thread's `dxc_context`), not values. `dst_tile` is a tile handle.
- Set each register's value first with `__dxc_const_i32(value, reg)`. The loaded elements are
  `base[min], base[min + stride], ...` below `max`, at most one tile (`TILE_SIZE`).
- A register read by an operation still in flight is not overwritten until a `__dxc_wait`
  covers that operation (strict check `constant_uncovered_register`).
- Strict checks: `stream_bounds` (0 <= min <= max, stride > 0), `tile_truncation`,
  `register_handle` / `thread_ownership_register` (a plain value passed as a handle).

Peter v1.1 section 3.1 and the section 5 template type `start_idx`, `end_idx` and `stride` as
`int32_t` values and pass numbers directly. On this interface they are register handles. Ticket 58's
nine samples all failed for this reason.
