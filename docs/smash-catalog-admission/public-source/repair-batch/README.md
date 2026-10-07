# Coherent SMASH constructor, width and metadata repair batch

This portable source-preparation package composes the previously reviewed
zero-CTZ/typed-indexer parent `a08109ea…` with constructor extent admission,
setter width, reader width and upper-bitmap allocation/initialization repairs.
It writes new private outputs, not the source parent, catalog or a model.

The before fixtures reproduce a last-block ASan overflow and signed-square
UBSan failure in the original constructor domain. The upper-constructor fixture
first reproduces reader shift32 rejection; fixing that reader in isolation then
exposes the level1 packed-buffer overflow. The final source passes new cases at
both upper levels with 1/16/17/64/65 groups, selected/unselected bits, declared
extents and zero metadata tails. The original level2 overflow is supported by
its matching source pattern, not a separately executed before case.

The successor grows metadata to `ceil(groups * packed_width / 64)` words before
writes and initializes new words to zero. That zero is bitmap metadata, not
fabricated NZA payload. Incomplete or mixed-ratio layouts reject before writes
with exit 98; allocation failure exits 99. These conservative domains do not
claim arbitrary original-layout equivalence.

From the repository root, supply the exact privately materialized parent:

```sh
python3 examples/mechanism-scaffolds/smash-source-repair/prepare_batch.py \
  --parent-a081 /path/to/exact/a081/bitmap.h --output /tmp/new-smash-batch
```

Recreate only the new finite fixture extracts in another private directory:

```sh
python3 examples/mechanism-scaffolds/smash-source-repair/smash_public_packed_capacity_2026_10_07/prepare_fixtures.py \
  --setter-parent /tmp/new-smash-batch/setter/bitmap.h \
  --final-header /tmp/new-smash-batch/final/bitmap.h --output /tmp/new-smash-fixtures
```

No full upstream header or extracted `.inc` snapshot is distributed. The package
contains owned transformations, geometry helper and fixture drivers; exact parent
hashes protect the local extraction. [Batch identities](batch-receipt.json) and
[portable file hashes](portable-files.json) preserve each stage. Existing sanitizer
outcomes are reused; publication does not rerun numerical or simulation evidence.

NZA payload initialization, CSR/input shape, whole-indexer EOF/progress, actual
consumer arithmetic and whole-kernel numerical validation remain separate. This
batch changes no catalog capability and grants no BMU or performance acceptance.
