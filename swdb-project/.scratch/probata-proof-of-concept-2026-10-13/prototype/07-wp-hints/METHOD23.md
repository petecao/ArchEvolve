# Method23: exact task identity and fresh baseline initialization — 2026-10-15 ET

**Prospective protocol. This document does not authorize an actual launch.**
Run25 and its producer `798e9bb3` remain immutable. Its terminal positive replay
stopped at 39.48 counted minutes after three environment-inspection denials spanning
32.239667 ms. The failed process's executable, ownership, parent lineage and OS or
exec cause are unknown. Neither a long-lived denial nor recovery within a longer
window is established by that experiment.

## Narrow availability policy

Only environment inspections receive a 200 ms continuous-clock retry deadline and
an independent cap of 21 attempts, with gaps of at most 10 ms. Other observations retain
the three-attempt policy. Every observation/retry still validates the immutable
captured PID/birth before and after the OS operation. Confirmed gone/reused
identities remain distinct from live or unknown denied observations. No lineage
fallback or denied-as-absent marker interpretation is added.

The 200 ms value is a prospective availability hypothesis, not a calibrated bound
on macOS startup or an explanation of run25's denial. The public controlled case
models 150 ms of denial on one live identity, which the old policy refused. Its
recovery under the new policy does not show the old unidentified process would
have recovered. A truly persistent live/unknown denial still fails closed and
uncertainty during cleanup still quarantines the private lease.

A newly admitted retry is checked against the deadline before identity inspection
and again immediately before the requested OS operation. A delayed sleep cannot
start a fresh retry after observed expiry. The original denied observation stays
immutable; a separate timestamped expiry decision records why no retry began.
An already admitted OS call may finish later; source-level admission is not an
atomic kernel start-time guarantee.

All inspection pauses remain inside the continuous resource clock and the same
experiment clock; none earns queue-wait exclusion. Mandatory known-scope RSS and
elapsed-time checks follow inspection, and can refuse an over-budget job after a
recovered denial. This extends an individual inspection pause and therefore the
possible sampling/stop latency. A 200 ms retry deadline limits the retry policy;
OS calls/scheduling may finish later. There is no hard realtime latency guarantee,
kernel memory quota or hostile-process containment claim.

Only matching run-marker presence is retained; unrelated environment values are
never logged. Fresh marker discovery and immutable original-root identity rules
are unchanged. A PID replacement lacking the exact run marker is not adopted or signaled.
Independent fresh marker-verified renewal of a nonroot identity remains allowed;
the original root identity is never replaced.

## Controls and remaining work

The pre-agreed public seam is the real counted_verifier CLI and its exit, retained
summary and lease result. OS inspection is injected at the psutil boundary; the
new controls do not call private ownership helpers. Real small Python children
provide lifecycle observations, and PID reuse is modeled at that system boundary
rather than forced in the kernel. No provider/solver is launched.

The retained old-policy RED is one 150 ms denial control. The repaired source passed a composed GREEN suite of 36 controls and one
additional permanent expiry regression. The suite covers 27 existing runner
controls, the new public cases and independent cleanup/deadline controls. The new cases cover transient recovery,
persistent live refusal/quarantine, unknown identity without signaling, PID reuse
with a foreign marker, an actual unmarked foreign process outside RSS/kill scope,
retained sampled RSS/deadline refusal after recovery, and refusal to start a new
retry after an injected OS sleep overshoot. Token values and private
fixture environment values are not persisted in reports.

The narrow guard repair has an exact-byte independent PASS and is integrated.
Actual launch of the complete method below requires an exact-byte independent
review, clean published source freeze, live preflight and coordinator admission. Preliminary
source passed 254 composed controlled cases in 77.30 seconds. Independent review
then found three additional refusal-boundary gaps, reproduced and repaired below;
that earlier suite alone does not validate the repaired final source. Controlled
checks and the real component remain separate from scientific acceptance.

## Exact active task reader

The opt-in `--fresh-baseline-start` flag requires the complete method22 foundation
and also enables the machine-ID reader. It uses the pinned Frama-C33.0
`Wp.Wpo.get_gid` and `Wp.Wpo.pp_goal` on the same generated goal object, registered
after WP through `Boot.Main.extend`. Installed native report source uses that
same `po_gid` for its goal field. The primary
[Wpo interface](https://www.frama-c.com/api/frama-c-wp/Wp/Wpo/index.html) exposes the
three relevant operations: `get_gid`, `iter_on_goals` and `pp_goal`.

Each first-page request copies the frozen exporter source into a fresh task
directory, compiles it there with the pinned local OCaml toolchain, then generates
selected active-candidate VCs with `-wp-prover none`. The run resource guard covers
compilation and generation together. No compiled artifact is shared between hosts.
The exporter emits a duplicate-refusing ID-to-rendered-task index. Selection is
exact ID equality; human header ordinals, singleton `_requires` suffix guesses,
source line ranges and split numbering no longer determine identity.

The Python reader rejects a missing, malformed, empty or duplicate-key index or
missing requested ID. It retains the full rendered task and index hashes,
exporter source and binary hashes, active hint-set/source/header hashes and raw
generation-log hash. Offset pages return at most 14,000 characters, with total
length, omitted/remaining counts and explicit truncation. Later pages require the
same task hash and validate retained artifacts without a new verifier launch.
The exact generated directory's C source, headers and copied exporter source are
also checked against the expected hashes after generation and again on every
cached page. Its directory must remain inside the current run. Changed or missing
artifacts cause an explicit refusal. After generation and working-state handling,
the MCP handler observes the search clock again; text completed after the soft
stop is censored, with a retained deadline-censored receipt and all time charged.
This is an observed admission gate, not an atomic kernel delivery-time guarantee.
Scope remains one open
goal of the authoritative active candidate; no arbitrary path or previous-run
reader is exposed. The full rendered task is an explanatory artifact, never a
proof verdict.

Compiler-only API checks passed. Component1 ran cleanly but its tasks were trivial
and the native solver-session report was absent under none-prover mode, so it did
not meet its intended runtime validation. Component2 retained the default fatal
parser refusal for invalid ACSL clause order. A separately reviewed corrected
component3 passed its independent runtime API/context/resource audit. The revised
check compares the complete
unique generated-ID sets from the exporter and the existing pinned
`swdb/proof_report.ml` inventory, plus printed goal count and concrete generic
source/property/call metadata. Both hooks observe the same Wpo database: equality
checks exporter agreement and hook timing, not an independent derivation of
Frama-C obligation completeness. Native report absence remains explicit. Inventory
verdict strings omit prover identity; the exact none-prover invocation and runtime
evidence support the no-external-prover boundary. Nontrivial contextual premises
and conclusions were observed: 15 unique generated/index IDs and printed goal
headers agree, all rendered texts occur in the log, and five tasks contain
nontrivial contextual premises/conclusions, including both intended call forms.
The exact 14 inputs remain unchanged. The guard exited0 in0.591254 seconds with
101.265625 MiB peak sampled RSS, no inspection failure and no unconfirmed child.
Three independent metadata scans found rootPID70522 absent and no component
path/cwd matches or inspection denials, with both shared leases absent. No exact
marker was archived; no environment scan or exact-token absence is claimed.

The independent runtime receipt is retained outside Git at
`/private/tmp/probata-t07-method23-component3-independent-runtime-review.json`,
SHA-256`d545b5f1ada6974661ae4de8eaac3772788d1815e5ea2e24d6a760584aa5a512`.
This validates the declared API/exporter agreement boundary only.

## Fresh own baseline as the empty initial diagnostic

The new method runs the same fresh full all-function/smoke baseline at 10 seconds
inside its original continuous clock. Only a complete checked baseline with
unchanged canonical source/headers, exact frozen invocation and a present passed
smoke inventory can initialize the genuinely empty incumbent. Its diagnostic
projection contains the baseline's non-smoke TDStep and global-lemma observations.
Other baseline goals and every final obligation remain retained and mandatory.

`baseline-initial.json` records the actual baseline mode, full/subset inventories,
exact selected IDs, source/header hashes, report/log/resource-summary hashes and
fresh run identity. It explicitly disclaims cross-mode formula equivalence. The
incumbent points at the real baseline directory and is labeled `fresh-baseline`;
no round directory, round report or round completion is fabricated. The terminal
reader receives the current driver's expected output root, requires exactly its
own `round-0` before reading baseline artifacts, and compares the receipt with that
current run's metadata. It revalidates the provenance and projection, and admits
it only while hints remain empty. Any accepted provider candidate has its own complete ordinary round
and uses the existing round verification path.

There is no mechanical seed insertion, hint provenance exception, historical
baseline import, clock reset or supplied concrete frame. Previously-proven guards
come solely from the current run's fresh baseline observations. A read-only
historical diagnosis found identical 155-ID/status subsets for one baseline and
its duplicate empty round, costing 4.40 extra minutes. That is motivation only;
no old result or concrete hint enters the new run. Baseline mode and round-s can
differ in selection, smoke generation, strategies, cache and statuses. Replacing
the initial round changes scheduling and initial diagnostic/pass-set provenance;
no formula identity or measured future time recovery is claimed.

## Unchanged final gates

The proposed method keeps method22's 33-minute proof-tool stop, natural return
through the hard 36-minute provider cap, and original 60-minute total. All work,
including source compilation, new task reads, retries and required accounting,
counts. Only independently validated matching queue wait can be excluded. The
remaining nominal 24 minutes includes a minimum 8-minute negative reserve; its
sufficiency remains unproven.

Zero mechanically authored hints, complete scoped Codex operation-to-record
ancestry and natural complete usage receipts for every provider call remain
mandatory. The dated literal-Codex-origin acceptance review supersedes the older
undecided mechanical-seed interpretation; no old seed provenance is rewritten.
One fresh full all-function/cache-none/30-second positive/smoke replay still runs
even if diagnostic goals remain open. Every ordinary and hint obligation must
pass, then the exact same hints must complete the covering-wait-removal negative
inside the same clock with the original hazard check not proven and not refuted.
All final publication/completion/clean-exit gates remain in force. No component or
controlled test can close ticket07 or substitute for this counted acceptance.

## Independent review repairs

The first static review found three concrete gaps: a self-consistent old baseline
root could pass self-anchored verification; late-generated task text could reach
the provider past the soft stop; and cached pages did not revalidate the actual
generated source/header/exporter copies. Public driver/MCP regressions reproduced
each before fixes. The old-root test creates a genuine separate earlier synthetic
run through the driver, then retargets the current incumbent; it does not invent
old report fields. The repaired gate refuses it before any terminal launch.
The late-task control retains generation artifacts but returns no task content.
Six first/cached-page input mutations now refuse instead of disclosing task text.
The repaired reader suite passed24controls in13.39seconds and eight baseline
controls passed the root-binding repair. Independent composed verification then
passed264controls in82.87seconds, including two separate resource regressions.
That review closed the three initial findings and identified one additional
active-candidate edge before granting approval. No control invokes an actual provider or theorem
solver. The dated initial findings and source snapshots are retained outside Git
at `/private/tmp/probata-t07-method23-initial-static-findings.json`.

If a read spans temporary debt expiry, the ordinary working-state refresh can
roll back to the incumbent while the global search clock still permits work.
The handler now captures that refreshed state and censors the old task if its
candidate identity changed. The public regression first creates genuine temporary
debt through `propose_edit`, resumes its retained controlled session near expiry,
and generates across the expiry. This controlled fixture configuration models
elapsed time; the actual method never resets or imports an experiment clock.
The RED disclosed the expired task after rollback; the repaired response retains
the artifacts/accounting and instructs the provider to refresh the active state,
with no old task text. Twenty-five current reader controls plus the legacy paging
control pass26tests in16.25seconds. Final exact-byte independent rereview is a mandatory prelaunch gate; no broader
suite rerun is implied by that localized result.
