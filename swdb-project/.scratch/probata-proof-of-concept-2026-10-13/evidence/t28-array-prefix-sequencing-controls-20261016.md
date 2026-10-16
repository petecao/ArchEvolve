# Array prefix sequencing boundary

2026-10-16 ET. Executable source `e4cd1a6e`, patch `bfa68c8a`; frozen901 remains immutable.

The new Clang scalar `array_filler` prefix route previously admitted general expressions. C++ list-initializer sequencing cannot be carried into C initializer evaluation without a checked correspondence. The successor restricts this new route to literal scalar leaves, checked cast/constant/parenthesis wrappers and unary `+`, `-`, `!`, `~`. Reads, calls, modifications, binary/conditional expressions and unknown forms refuse. The old explicit-inner route is unchanged.

Three public lowering RED controls reproduced acceptance of increments, a same-array read, and calls. All seven focused controls then passed, including two defined ASan/UBSan C/C++ comparisons preserving constant prefixes7 and7,2 plus implicit zero remainder. The stationary composed profile passed9 in48.25s (guard48.642s, peak2,451,685,376B, noOOM/timeout), including two closed stream scripted preparations. Both adapters intentionally exited99; no actual proof is claimed.

One earlier scripted profile was invalidated by an integration sync during execution: the method identity gate correctly refused a changed translator. It is preserved and excluded from final acceptance. The source was held stationary for the final9. Raw and exact source pins are in the adjacent JSON. No solver policy, fixture source, contract, legacy0.1, or old actual producer was changed. Whole28 remains open.
