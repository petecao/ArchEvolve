# Complete uint32 choice domains

2026-10-16 ET. Inert source-only successor of frozen model entry V1.

The V1 choice-table budget 1..256 limits how many independent draws exist. Its unrelated alternatives<=256 guard incorrectly refuses the exact size backend's unknown initial tile-size choice, whose 16385 alternatives cover 0..16384. V2 removes only that upper-domain guard. Every positive unsigned32 alternatives value remains covered by a full-domain uint32 draw modulo alternatives: for every desired answer x<alternatives, the allowed draw x maps to x. Zero alternatives and exhausted draw budgets still fail checked properties. No desired value or source premise is assumed.

All original 26 per-call contracts, 27 declarations, 132 typed/arity bodies, four exact backend bodies, ABI/atlas/MMIO gates and source-consumer requirements remain unchanged. The old binder/dispatch pins here deliberately remain V1's frozen assembly basis; their later locator-only successors are separately reviewed source consumers. This proposal adds no receiver state, reset, payload initializedness, ownership, compiler execution, native/formal result, production registration or current 0.2 acceptance. Runtime receiver/numeric and independent draw initialization remain explicit required producer work.

Eight no-child controls cover the full 16385-answer size domain, invalid budgets, all old model/refusal behavior and a complete textual inverse restoring frozen V1. The generated example still uses only synthetic ABI/ordinary addresses. Root admission and independent review remain required for any actual tool consumption.
