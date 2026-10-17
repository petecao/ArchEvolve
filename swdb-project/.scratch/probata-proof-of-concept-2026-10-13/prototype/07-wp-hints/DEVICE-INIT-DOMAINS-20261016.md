# Device command read/write initializedness domains

2026-10-16 ET. Prospective source preparation only; full TD/count admission remains closed.

The previous device summaries assign mathematical tile values without promising initialized payload cells. Under the strict initializedness policy used by the accepted helper component, an opaque value equality is insufficient to justify a later C payload read. This successor states the actual successful command read/write domains under the existing declared command/library TCB.

`device_init_domains.py` verifies raw SHA-256 for four canonical inputs before strict UTF-8 decoding, and emits a separate `standin_device_init_canonical/` directory plus an exact old/new contract map. All44files in the five historical model directories remain unchanged. The gapbs helper header, TD source and BFS postcondition header are byte-identical to the previous canonical inputs. Only three device contracts gain clauses; their prior requires/ensures/frames/termination/exits and all C tokens remain unchanged.

| Command | Source read domain | Output promise |
|---|---|---|
| Stream | Existing valid selected source range plus initialized cells | Live destination capacity; initialized produced prefix only |
| Gather | Live initialized index prefix and initialized selected base cells; existing base validity retained | Live destination capacity; initialized produced prefix only |
| Range | Live initialized lower/upper bound prefixes | Live row/column destination capacity; initialized produced prefixes only |

The existing TD `spd` domain already supplies live tile capacity. Incoming CSR, queue and parent initializedness comes from the existing caller domain; intermediate tile initializedness must follow actual producing commands. This repair adds no TD-entry initialized prefix, guessed Init value, reset/havoc operation, output-tail initialization, source algorithm change, proof hint or new desired-result caller premise.

The source wrapper maps these calls to `maa_stream_load`, `maa_indirect_load`, and `maa_range_loop<int>`. Retained exact functional bodies store each produced element (stream531–550, gather573–592, range736–781). Those source stores support the read/write interpretation; they do not prove hardware visibility or full range-continuation equivalence. Opaque normal-return semantics, the existing completed-at-issue value abstraction and separate pending-dependency/hazard coverage remain explicit TCB. A wait grants existing coverage; the repair does not assert that asynchronous hardware completed physically at issue or prove liveness.

Three public-generator red-to-green slices are retained externally. The first RED successfully ran the old generator and failed the independent source-effect checklist on missing stream clauses; later REDs exposed the next absent family before its implementation. Final28pure controls pass under shared B+c6 in0.533177seconds32.40625MiB, no inspection events/timeouts/OOM/unconfirmed children. They check deterministic output, exact old-clause/C-token/TD/helper preservation, no tail promise, raw-byte CRLF/altered/non-UTF8 refusals and no emission on invalid source. The structural checklist is not an ACSL parser or logical proof. No compiler, native observer, formal tool, prover, provider or SSH job ran for this repair.

Evidence: `../../evidence/t07-device-init-domains-preparation-20261016.json` retains every stage's raw membership/hashes/resources and all44historical byte/Git pins. The first stream stage sources were retained after execution before any mutation, explicitly recorded; later stages snapshot sources before execution. Existing successful helper proof acceptance applies only to its unchanged header bytes and declared TCB.

Before another counted TD run, independently review this exact source/contract map; root must admit fresh ACSL parsing with a complete goal/property/Extern graph and meaningful same-path positive/missing-input/missing-output/wrong-cell initializedness controls. Those formal controls are planned and have not run. No unsafe native negative is permitted. Then root can assess the exact source/profile/private-frame and remaining device/caller qualification, and admit the fresh counted method. The whole ticket is not resolved by this preparation.
