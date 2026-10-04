# Usage note: `__dxc_const_i32` (`intrinsic.dxc_const_i32`)

Created: 2026-10-04 ET (ticket 64). Non-normative: this note is not part of the library entry,
its content hash or its certification. It restates the entry's interface; it changes no semantics.
Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

```c++
void __dxc_const_i32(int32_t value, int reg);
```

- The only way a scalar value reaches a DX100 register. `reg` is a register handle from the
  calling thread's `dxc_context` (`c.reg[0]` .. `c.reg[7]`).
- Every operand named `*_reg` in `__dxc_stream_load`, `__dxc_range_loop` and
  `__dxc_alu_scalar` takes such a handle, never the value itself.
- Overwriting a register that an operation not yet covered by `__dxc_wait` still reads fails
  the strict check `constant_uncovered_register`.
