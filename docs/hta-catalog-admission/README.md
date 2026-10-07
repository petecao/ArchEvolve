# Flat-HTA key-map mechanisms and overflow ownership

Flat-HTA (MICRO 2019) accelerates hash-table operations by hashing a fixed-size
key to one cache line, comparing its resident key/value slots in a functional
unit, and returning branch/result information. Hardware resolves common local
cases while software handles overflow and resizing. The inspected x86-64
interface carries one to four opaque 64-bit key words and one value word.

Revision 0.1.16 adds explicit integer-word lookup, update, swap and delete
mappings with seven located claims and seven mechanisms. An invalid slot can
resolve an absent lookup; a deleted slot must still permit software overflow
search. Deleted slots can be reused. Full-line update falls through without
mutation, whereas full-line swap installs the new pair and returns a victim
for software maintenance. That victim is not the old value of the requested key.
These operations grant no generic gather, CAS or FP-key behavior.

The [portable table helper](../../examples/mechanism-scaffolds/hta/table_contract.py)
models the raw line operations and an exclusive-owner software consumer. A
synthetic mixed-operation counterexample shows how skipping all software cleanup
on a taken branch can leave a stale overflow key after tombstone reuse, which
reappears after deletion. The declared single-threaded consumer removes duplicate
software ownership on every insertion/deletion. This is a tested integration
obligation, not a proven fault in an authenticated published wrapper. The catalog
labels that claim as research inference, separately from primary paper facts.

Supplied line/hash receipts, normalized packing and selected swap victims are
helper conventions. The model executes no CRC, memory request, ISA or concurrent
atomic operation. Sentinel values are legal keys in their own hashed line; the
paper's sentinels hash away from the line they mark.

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/hta -p 'test_*.py'
```

Actual concurrent use requires atomic hardware instructions plus fallback line
locks and a lookup recheck after lock acquisition. Thread-safe insertion first
tries no-eviction update, then swaps under the fallback lock. The real compiler,
ISA packing, hash, physical access, wrapper, atomic protocol and resizing remain
implementation obligations. Hierarchical-HTA stash/coherence behavior is outside
this Flat-HTA record.

The [primary binding](primary-binding.json) identifies the cached paper by hash
and DOI. Sections 3.1–4.4, physical PDF pages 4–6 and Figures 4–9 ground the
line format, branch interface, functional unit and software fallback. No corpus
PDF is copied.
