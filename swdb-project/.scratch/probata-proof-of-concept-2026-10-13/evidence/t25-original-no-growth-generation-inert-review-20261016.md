# ORIGINAL no-growth generation: independent inert entry review

Date: 2026-10-16 ET. Reviewer: `prefix10_review`.

**PASS for the immutable V2 preparation, conditional on separate root admission.**
The V1 preparation required changes and remains unexecuted. V2 closes both
prelaunch findings. This review used source reads, Python standard-library
AST/JSON/hash operations and read-only Git. It did not run the author, controls,
entry, project imports, compiler, native reader, verifier, solver, SSH or tests.

## Exact reviewed bytes

All paths below are under
`prototype/25-original-no-growth-generation-20261016/`. SHA-256 values were
independently recomputed, including every packet reference with a path, size and
digest.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `inert-c978393b-v2/entry.py` | 27,434 | `20fd7729f8e17c1766accb283a24cc8a725a69c6b38ff44a8642c86ea19a377c` |
| `inert-c978393b-v2/expected.json` | 145,973 | `1deab3e496cefa645950e22033860602aa7d13f95518962e7b48abf0e00c8a7b` |
| `inert-c978393b-v2/root-command.json` | 74,659 | `e52e83ee3afa14731a908880b151e654cd49696cb8f9660c3bfdff6d22f6a24f` |
| `inert-c978393b-v2/packet.json` | 6,476 | `0c94a7a757749f383cb8e4491455b2b075d55ff17f2508f118f0c579d9a311f8` |
| `author-v2.py` | 12,209 | `5c6d1337fc0be3fb659ef1527d911e527bc9d7fb44089e54b23857ecb8e14dc0` |
| `entry-template-v2.py` | 21,427 | `5fac7d63d00e3f8ad8375726812802346ef329769e856eeebb03eefda60e50f3` |
| `guard-controls-v2.py` | 8,506 | `6e51b2307efc4e72bd8bccee4634a3aa7949d1805346b72f5c5eec4399973fd3` |
| `guard-controls-v2.json` | 835 | `b77de2e17e6cd6ea6f91b981d715947b66a485540cf6b252a0cf071685289617` |

The preserved V1 packet remains
`7f772743f7914cba64068167dabca7769a74a73665c3d4585bbdbb04911fcf2f`.
The reviewed focused10 predecessor remains
`fed0e1ff46d33afbf38f032e2ef39481fb23378b7ebef711301582d38fad61c1`.

## Source, insertion and transport checks

- All 322 package blob pins and six consumer-root Git object pins match exact
  `c978393b119a3614229a37f0f2c8ca2a097c750b`. The selected remote project remains
  `/data1/yanruj/probata-resume-20261016-c978393b/swdb-project`. This is an offline
  source-policy check; fresh remote physical equality is an admission requirement.
- Original C++ is `1172e62dbff5076d25471285afcfa17927707dbe6fae121d9570109d39e62b57`.
  Retained genuine original C is
  `7082d6fc081e23547bf792f8029277695b83d933913545f290f66353ee5841ec`.
  The complete cached anchor file is
  `121a77c8994f705a651bc43c646d8b2da9e5deeb30a4eee145e1e9afa3a27252`.
  Both cached copies match their retained inputs. The sole added root annotation
  has exactly the frozen requires/assigns/ensures clauses. Inverse removal restores
  every original C byte; merged input is
  `aa223d8554e36fc8064f08b3bea3439358d266b4568a5a864a65955b94b1784a`.
  Original model definitions/contracts, source calls, captured alias, guarded read,
  destructor/return and fallthrough cleanup remain present. The source-view module
  is not used.
- The entry requires fresh lowering equality and exact portable anchor/model/event
  lineage, then independently checks original-TU provenance. Full fresh Linux
  anchors are retained; the historical full Mac certificate is a pinned reference,
  not an asserted Linux byte match (`entry.py:377–402`).
- All ten selected installed runtime-source pins match physically in this review.
  V2 expectation differs from V1 only by
  `/resource_policy/metadata_reserve_bytes = 1048576`; source, runtime, contract and
  generation policy remain identical.
- The entry reconstructs byte-for-byte from its V2 template, six unchanged reviewed
  helper bodies and expected digest. Reversing the four digest/payload substitutions
  and the documented output-name substitutions restores the reviewed predecessor
  command exactly. Both compressed embedded payloads roundtrip to the pinned bytes.
  Bootstrap size is 74,393 bytes, below the 120,000-byte transport allowance.

## Guard findings and V2 closure

V1 had two blocking mechanical gaps: exceptions after spawning could bypass
termination/reaping, and common-fragment copies could grow aggregate output past
the budget after the live monitor stopped. The immutable V1 packet is preserved.

V2 puts every post-spawn path under `finally`: it attempts session termination,
known-descendant termination and bounded reaping, preserving an existing primary
exception and refusing successful classification on cleanup errors
(`entry.py:121–195`). Raw census tolerates concurrent disappearance while propagating
other I/O errors (`198–212`). Per-file allowance subtracts existing output and the
metadata reserve. Live aggregate polling remains present. Fragment and census
metadata writes check projected aggregate growth before writing; final result and
manifest writes also check their projected size (`215–281`, `441–448`). These
changes address the two reported findings without changing generation semantics.

The pinned control source uses fake process, watchdog and OS-signal boundaries.
Its retained receipt reports 9/9 passing controls, no real children/signals/project
imports/native calls, and binds the exact V2 template. Cases cover callback,
watcher entry/exit, poll/wait exceptions, normal-exit stragglers, disappearing versus
permission-error files, and refusal before fragment/census metadata growth. The
review checked this source and receipt without executing them. They establish
scripted guard behavior, not actual resource measurements.

## Generation and evidence boundary

The pinned runtime source confirms `-wp-gen` reaches common task generation before
the `ProverWhy3.build_proof_task` early return, ahead of driver-task construction
and solver invocation. `-wp-no-why3-detect` disables the configuration autodetection
branch. The entry avoids `_tools`, solver/version probes, public proof jobs and
proof records. Native-reader compilation and foundation preparation are confined
to a later admitted execution.

The original root retains ordinary, RTE, initialization, frame and smoke settings;
there is no `-wp-prop` filter. The census requires complete native inventory,
ordinary and smoke families, required reports, unique native ownership of each
fresh common-log fragment, and fragments for every noninternal goal. Missing or
ambiguous evidence refuses completion while retaining partial files. Fragments
are exact byte slices of the full log with ranges and hashes; they are diagnostic
common theories, not promised standalone SMT files or submitted-byte attestations.
Internal simplifier `Valid` rows cannot become proof acceptance.

Root still owns fresh interpreter/tool/config/import/foundation/source equality,
the reviewed outer wrappers, launch metadata, free socket-lane lease and actual
resource/result checks. The inherited `SWDB_VERIFIER_LOCK` check validates a marker;
it does not acquire an advisory lock. The actual exclusion mechanism must be the
coordinator's live lane ownership. Prospective policy is 8 GiB, one worker,
210 seconds Frama-C, 300 seconds profile, 420 seconds whole worker, 540 seconds
outer guard, and 1 GiB raw output with a 1 MiB metadata reserve.

This PASS permits root to consider that bounded diagnostic. It establishes no
actual generation, model-body proof, source-runtime correspondence, Typed/Heap
coordinate bridge, caller proof, public/full-body acceptance or ticket closure.
Original callee contracts remain unproved hypotheses requiring later review.
