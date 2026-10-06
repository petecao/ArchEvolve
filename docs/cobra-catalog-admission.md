# COBRA tuple-binning reference, revision 0.1.7

The catalog includes `cobra-hpca2022-tuple-binning`, the reviewed base-COBRA Neighbor-Populate Binning mapping. It has one required `write / tuple_bin` operation: hardware materializes complete index/value tuples into allocated private bins. CPU Accumulate later performs destination writes and offset updates. This does not add generic scatter, atomic updates, reduction, old values or COBRA-COMM.

An exact inspection query is:

```sh
python -m archevolve.hardware_catalog query --operation write --subtype tuple_bin --design cobra-hpca2022-tuple-binning
```

Untyped inspection returns `mapping_reference`. Requested byte-address patterns, payload types and index widths return `needs_evidence`; C-Buffers are not ordinary byte-addressable destinations, and tuple size alone establishes no typed domain. Old-value requests remain excluded even when other requested capabilities lack evidence. Ordinary BFS generation does not infer this transformation.

The record retains `bininit`, `binupdate`, `binflush`, the unnamed LLC offset initializer, full tuple association/multiplicity, hierarchical disorder, private storage and cache reservation. ROB retirement is not downstream drain. Phase release must establish stopped producers, intermediate FIFO drain, outstanding bin writes, inter-core joining and consumer visibility. VA=PA/OS support, preemption, counts/capacity, reorder/numeric legality, progress and executable ABI remain obligations. No public runnable source was established; paper-reported Sniper/Pin/DES/CACTI use is not executable artifact evidence.

The admitted record and its source/claim objects equal the [reviewed proposal](proposals/cobra-hpca2022/proposed-addition.json), exact commit `62cc6b6a658dcc09dfd42941953149516e75241b`. [Independent review](review/cobra-hpca2022/README.md) accepted descriptive mapping admission after primary inspection, nine additional adversarial query cases and two synthetic normal-consumer projections, reusing the hash-bound producer's 20/88 checks. Synthetic projection establishes no workload equivalence or target correctness/performance.

Current revision 0.1.7 has nine records across seven families, 45 operation records, 109 claims and 32 source records. Previous eight records and their operations remain unchanged. DRT remains outside v0 as research. Proposal/review scripts reproduce historical in-memory addition against their pinned base; after admission, use normal catalog validation and `tests/test_cobra_catalog_admission.py` for the installed record rather than adding it twice.

Integration validation: normal catalog validation and all 100 software tests pass. Focused checks retain exact proposal content, the previous eight records, unchanged generic BFS selection, typed/old-value exclusions and complete source contracts in the generated handoff. This is software representation validation, not COBRA execution or workload/numerical certification.
