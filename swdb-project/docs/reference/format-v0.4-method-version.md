# Method-version files (`library/methods/<version>.yaml`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 11.
Updated: 2026-10-14 15:43 ET (fix-21): lifecycle (current = frozen; drafts only by name), the first real
draft `library/methods/probata-draft-1.yaml`.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/11-method-version-and-failure-classes.md`;
design: `.scratch/formal-verification-2026-10-09/spec.md` ("Records and levels"), map 26 item 3, S8.
Schema: `schemas/library/method_version.schema.json`. Code: `swdb/method_version.py`.

**In one line:** one reviewed file per method version lists everything a candidate artifact's
proofs use apart from the rewrite contract, the candidate artifact and the proof semantics; every
proof record pins it by ID and file sha256.

## Rules

- **Where:** `library/methods/<version>.yaml`, ID `method.<version>` (the file name).
- **Never edited in place.** Changing any byte makes a new method version (glossary): write a new
  file with a higher `sequence`. A proof record whose pin's sha256 no longer matches its file fails
  `swdb validate`; the fix is a new file, never an edited record.
- **Old files stay**, so old pins still resolve.
- **Lifecycle: `status` is `draft` or `frozen`.**
  - **Current = frozen.** The current method version is the **frozen** one with the highest
    `sequence`. `swdb prove` pins it by default. A library with no frozen file has no current
    method version.
  - **A draft is used only when named:** `swdb prove --method-version <id>`, or the campaign file's
    `method_version` (the bounded gate and the WP phase then run under it). A draft never becomes
    current, so committing one changes no default.
  - **The bounded gate** runs when the campaign pins a method version, or when a frozen one exists.
    A library holding only drafts keeps it off.
  - **Level rule:** a record keeps counting under the current frozen version, and under a draft whose
    `sequence` is higher than that version's. A record under an older frozen version, or under a draft
    a frozen version has overtaken, stops counting.
  - **Sequences:** two frozen files never share a `sequence`; a draft may share one (drafts are not
    ordered).
- **Drafts and the freeze.** A draft may mark a section `{not_yet_built: <sentence>}`; a frozen file
  may not. The ticket that lands a section writes the next draft. Ticket 59 is the freeze: after
  Yan-Ru's review it writes a **new** file with `status: frozen` and the next `sequence` (a status
  flip is a byte change, so it is a new method version; the draft's pins keep resolving). Records under
  the draft stop counting then; 59 replays them under the frozen version.
- **Evidence kind:** `contract_fixture` (tests) or `execution` (a real method version, ticket 21).
- **The first real draft:** `library/methods/probata-draft-1.yaml` (`method.probata-draft-1`,
  sequence 1). The Mac lineup: clang 22.1.8; CBMC 6.11 as the bounded verifier (Yan-Ru, 2026-10-14
  13:19 ET); CIVL 1.23; GenMC 0.19.0; Frama-C/WP 33.0 with Alt-Ergo 2.6.4, Z3 5.1.0 and CVC5 1.2.1;
  Rocq 9.3.0. Starting budgets. WP flags include `-wp-par 1` (ticket 08: hard goals on the Mac) and
  `-machdep x86_64`. CBMC flags: `--sat-solver cadical` (the adapter adds `--unwind K` and
  `--unwinding-assertions`). Translators: the C lowering tool and the CBMC translator, each by its
  source sha256; a change to either tool needs a new draft before the WP or CBMC adapter accepts it.
  The logic library is ticket 26's four shared files at version 1.0, with `logic.sum` 1.0 as the sum
  library; an edit to any of them needs a new draft. Sections later tickets build are `not_yet_built`.
- **`swdb prove-logic --method-version <id>`** names a draft the same way as `swdb prove`.

## Fields

| Field | Meaning |
|---|---|
| `id`, `kind` (`method_version`), `sequence`, `status`, `created`, `evidence_kind`, `description` | identity and state. `evidence_kind`: `contract_fixture` (tests) or `execution` (a real method version; ticket 21): proof records under a fixture method version stay `contract_fixture` evidence |
| `lineup` | every tool, solver and front end: `{role, tool, version, flags, commit?}`. `version` is one exact version (digits and dots: no range, wildcard or `latest`); `flags` is required (an explicit `[]` passes) |
| `civl` | CIVL settings (its k is in `budgets`) |
| `genmc` | GenMC settings |
| `openmp_runtime` | the OpenMP runtime |
| `c_lowering` | `subset`, `translators`, `naming_rules` (references `{id, sha256}`) |
| `acsl_version` | the ACSL language version |
| `proof_hint_vocabulary` | the allowed proof-hint kinds |
| `checks` | `proof_setup_check`, `proof_hint_check`, `verdict_reading`, each `{version}` |
| `budgets` | per candidate: `hint_rounds` (start 10), `hint_loop_wall_minutes` (60), `bounded_job_minutes` (15), `counterexample_repair_rounds` (5) (25 item 2); `wp_seconds_per_solver` (30; 13 item 11); `civl_k` (3, at least 2; 15 item 9, S8) |
| `prompts` | the prompts, as references |
| `shared_action_kinds` | the shared-action kinds |
| `sharing_classes` | the sharing-class names (S8) |
| `logic_library` | `{id, sha256, files?, sum_library}`: the shared logic library, the sum library included. `files` pins each shared file as `{id, version, sha256}` (ticket 26's pin form; a reference may carry an exact `version`); `sha256` is then the digest of that list (`swdb.artifacts.digest`); `sum_library` pins `logic.sum` |
| `models` | `std_vector`, `std_pair` (S8) |
| `rocq_development` | `{id, sha256, composition_theorem, dx100_reduction_lemma}` (S8; tickets 41-43) |
| `ghost_capacity_k` | ghost capacity K |

`swdb validate` names each missing section, part or budget. Kept out, as decided: the proof
semantics (its own version, owned by the hardware target) and the level rule (versioned apart, so
a rule change never voids proofs).

## For later tickets

- `swdb.method_version.current(library_root)` (frozen only), `.named(library_root, id)`,
  `.select(library_root, id=None)` (named, else current; `LookupError` with the reason),
  `.counting(library_root)` (the level rule's `{id: sha256}`), `.pin(version)`,
  `.pin_problem(pin, library_root)`, `.load(library_root)`, `.sections()`.
- `swdb.bounded_gate.method_version_of(library_root, pinned=None)`: the campaign's method version.
  The gate passes its pin to `TargetAdapter.prepare_proofs(store_dir, method=...)` and to `swdb prove`.
- The repair cap (`swdb.counterexample_repair.cap(records, proof)`) reads the method version the
  refuted proof record pins.
- 14 reads `budgets.bounded_job_minutes` and `budgets.civl_k`; 16 reads the per-candidate budgets;
  36 confirms each run matches the file; 59 refuses `not_yet_built` and freezes a version.
