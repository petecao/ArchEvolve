# LANL metadata cost audit

Date: 2026-10-07 ET. Read-only source audit; no SSH, full-catalog execution, application/provider execution, or source/protocol mutation.

Frozen checkout: `/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve`, branch `codex/lanl-ticket11`, commit `f893fed400347ed23d92e917d8bde21b75e5375d` (C). Recomputed F6 by reading the 185 Python source files with the same sorted-file/canonical-JSON algorithm as `estimate_protocol.estimator_identity`: `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`. Source/schema Git status was empty. All references below are inside `swdb-project/` at C.

## What explains the cost

Each public team-mode metadata subprocess starts with an empty per-process parse cache. `Store` discovers and loads every record, even when the command needs one ID (`swdb/store.py:43-50`). Its first load includes parsing, JSON serialization, a JSON round-trip equality check for cacheability, filesystem stamps, and indexing (`swdb/access.py:69-92`). The observed approximately 178 seconds therefore is not a measurement of YAML parsing alone.

Every writer commit loads the entire catalog under an exclusive lock, validates all records including the proposed new record, then writes (`swdb/writer.py:75-97,125-134`). Validation rebuilds vocab/schema context, runs JSON Schema on every record, then all semantic hooks on schema-valid records (`swdb/validate.py:36-81`). Schema validators are cached only within that one `SchemaSet`; each pass recreates the set and runs `check_schema` once per present kind (`swdb/schemas.py:41-60`).

## Exact successful-path pass counts

Counts assume the unchanged team policy used by this evaluation, valid input, no competing writer wait, and no unexpected nested application hook failure.

| Public command | Full `Store` constructions | Full record schema + semantic passes | Derived SQLite rebuilds |
| --- | ---: | ---: | ---: |
| `python3 -m swdb freeze-protocol` | **5** | **3** | **1** |
| `python3 -m swdb estimate` | **3** | **1** | **0** |
| `python3 -m swdb.cpu_service_binding` | **2** | **1** | **0** |
| `python3 -m swdb validate` | **1** | **1** | **0** |

The freeze handler alone has four stores; estimate handler alone has two. Public `swdb` main adds the fifth/third: `cli.py:276-278` invokes the ArchEvolve guard, whose evidence-command set includes freeze and estimate (`archevolve.py:12-16`), and whose team-mode path loads a full store (`archevolve.py:121-134`). An Extensa context bypasses this guard (`archevolve.py:122-123`), giving four/two stores respectively; that changes evidence policy and is not an administrative index-disable option for this team evaluation. The standalone service-binding module calls its own `main`, so it does not incur that extra guard store.

Freeze: guard load → `freeze_protocol` preflight (`bfs_protocol.py:688`) → `_save_immutable` second preflight (`:218`) → writer load/full validation → `workflow.persist` index rebuild. The two preflights also validate typed library/campaign files if present (`validate.py:23-32`); writer validation is the record-store check. `db.build` makes a fresh full store and serializes every canonical record into SQLite; it does not add a fourth full record validation (`db.py:150-183`).

Estimate: guard load → `analytic.estimate` load (`analytic.py:602`) → selected-record validation/model/pin work → writer load/full validation (`:688`). It never calls `workflow.persist` or `db.build`.

Binder: `cpu_service_binding.bind` load (`cpu_service_binding.py:240`) → selected-record validation/compatibility and immutable target construction → writer load/full validation (`:356`). Read-only AST extraction from `/private/tmp/lanl-dispatch-cpu-model-validation-a2.py` confirms its saved model branch uses this public module with four characterization scopes and nine calibration IDs. This means at least 14 separate `_load` schema/payload checks before the full writer pass: one target, four characterizations, nine calibrations (`:241-259`; `_load` is `analytic.py:123-140`). The original unsuffixed helper was absent; the a2 template supplies the module/argv evidence, not a new execution.

## Repeated semantic work

- A characterization's semantic validation hashes almost its entire data for the receipt identity, checks aggregate and trial count structures, and for verified data hashes its counted payload again (`analytic.py:692-757,803-809`; `analytic_binding.py:135-141,203-210`). Additional feature/binding checks depend on record contents.
- The bound target includes all scope characterization IDs in `calibration_sources` (`cpu_service_binding.py:346`). Frozen estimated protocols therefore include these large records in their reachable dependency closure. Closure discovery recursively walks their data (`extensa_boundary.py:175-201`).
- Each estimated protocol's semantic hook calls `validate_frozen` (`bfs_protocol.py:189-192`). It hashes every pinned dependency once and then recomputes the closure and hashes every dependency again (`estimate_protocol.py:32-35,102-116`). Two protocols sharing the same target repeat this work. Separately, estimate binding explicitly validates its selected frozen protocol again (`estimate_protocol.py:119-160`). No shared semantic-digest memo is used in these paths.
- Cached record loads still call `json.loads` to give callers fresh objects. The cache has a 256 MiB canonical-JSON-text limit and clears the **whole cache** when the next serialized record would exceed it (`access.py:53-91`). If total serialized catalog text exceeds that cap, sequential repeated scans can churn instead of staying warm. The reported approximately 310 MB YAML source size alone does **not** prove that condition; canonical JSON size was not measured. No process cache survives the next CLI subprocess.

## Publication and supported controls

`workflow.persist` commits canonical metadata **before** unconditionally calling `db.build`, then returns data for CLI emission (`workflow.py:82-96`). The observed durable BFS protocol with an unfinished CLI is consistent with its remaining index load/serialization; protocol existence alone does not establish successful CLI/index completion.

No documented/public C flag or environment switch was found to skip that rebuild while preserving this same freeze command. Freeze accepts `--db`, which selects the destination (`cli.py:29-39,236-243`), but `workflow.persist` always calls `db.build(records, db_path or default)`. No index-disable environment variable occurs in that pipeline. Binder/estimate omit rebuilding by their existing implementation, not by a switch. C, F6, a3, canonical outputs, controls, and recipes remain fixed.

## Administrative envelope only

Parent-supplied remote observations, not newly collected here: approximately 665 records/310 MB, first `Store` approximately 178 s, binder approximately 550 s, BFS freeze exceeded 1100 s after publishing its immutable protocol. These are whole-stage observations without an isolated profiler breakdown.

As a **conditional illustration only**, if each full store traversal cost 178 s, freeze starts with about **890 s** of store work before three validation passes, index serialization, and output; estimate starts with about **534 s** before one full validation, selected schema/pin/model/report work, and output; binder starts with about **356 s** before selected checks and one full validation. These are not measured per-pass times or predictions: cache behavior, record growth, retained protocols, host conditions, and lock waits change them.

The current 1800 s missing-metadata cap accommodates more administrative work than the observed >1100 s freeze but is not a proven upper bound. A future 1400 s freeze cap has materially less headroom; 1400 s final validation covers a different, one-load/one-validation path and cannot be used as a freeze-duration bound. Administrative timeouts can expire after a durable canonical write. Nothing here changes or recommends extending the scientific 900 s native collector budget, sampling, pairing, estimator recipe, service transfer premises, or raw outputs. Existing full-catalog tests were left untouched.
