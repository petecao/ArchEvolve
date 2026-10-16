# Pinned source for the conditional fresh-SPD size gate

Copied byte-for-byte from arkhadem/DX100 at commit
e4fc4afdf894f295442cef3604667a469fab8e62, `src/mem/MAA/`.
The immutable files support source inspection and exact constructor/getter
excerpts; this is not a simulator build or a hardware-boot proof. Digests live
in `swdb.dx100_size_source.SOURCE_PINS`. MAA.hpp/MAA_gem5.hpp remain at the real
project API path, with their existing immutable header pins.

The explicit synthetic epoch fixes constructor arguments32tiles/16384words and
matching4-core address setup, before commands or other accesses. Actual source
constructors accept configuration parameters; arbitrary installed device
configuration is not inferred from these files or the header defaults.
