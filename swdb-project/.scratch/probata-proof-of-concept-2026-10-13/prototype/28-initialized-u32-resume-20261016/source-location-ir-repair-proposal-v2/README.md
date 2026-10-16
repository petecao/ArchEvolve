The first retained replay passed the repaired source assertion boundary and
stopped at the unchanged LLVM checker. Its refusal is preserved in the V1
proposal directory. This successor keeps that SourceLoc repair byte-for-byte.

The retained LLVM uses signed i32 `x < 33`, taking the true edge to continuation
and the false edge to the original assertion abort. The older admitted form
uses signed i32 `x > 32`, taking the true edge to abort. These pairs have the
same behavior for every signed i32 value: the integer intervals ending at 32
and beginning at 33 partition that domain. No program arithmetic is added.
LLVM's primary [comparison](https://llvm.org/docs/LangRef.html#icmp-instruction)
and [branch](https://llvm.org/docs/LangRef.html#br-instruction) definitions give
the predicate and edge meanings used here.

The new helper accepts only those two complete forms for the bounded probe or
the caller's two counter assertions. It retains the original complete
instruction and SSA checker, including the operand, poststore reload, abort
call, unreachable block and continuation identities. Each comparison SSA must
occur exactly twice: its definition and its sole branch consumer. Reversing
only the predicate, using unsigned comparison, changing the threshold or
operand, adding an effect/use, or mixing caller forms is refused.

The original source assertions, caller, answers 711/1107, proof clauses and
frame remain unchanged. Eighteen compiler-free controls cover the old refusal,
both admitted pairs, refusal mutations, exact V1 inverse, reader inverse and
all previous SourceLoc controls. A first control run exposed an unescaped
parenthesis in a synthetic regex fixture; only that fixture was corrected.

The exact retained AST, preprocessed source and LLVM stay on mbit10. A separate
reviewed read-only replay must pass before integration. Its result is a
diagnostic observer check and supplies no new compiler, native, WP or public
proof verdict.
