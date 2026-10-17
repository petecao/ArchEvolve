# Ticket11 future metadata cost audit

Read-only audit at frozen C `f893fed400347ed23d92e917d8bde21b75e5375d`, F6 `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`. No Store construction, broad validation/test, native/provider command, source change, active-helper change or dispatch was performed for this audit. Paths below are within `swdb-project/` at C. It supplements the original metadata-cost audit.

## Exact successful-path counts

| Public CLI stage | Full Store constructions | Full catalogue schema+semantic passes | SQLite rebuilds |
|---|---:|---:|---:|
| collect-cpu-native-validation | 2 | 1 | 0 |
| freeze-cpu-error-band | 2 | 1 | 0 |
| validate-cpu-error-band | 2 | 1 | 0 |
| freeze-protocol (team mode) | 5 | 3 | 1 |
| estimate (team mode) | 3 | 1 | 0 |
| validate | 1 | 1 | 0 |

Native collection and both band commands are absent from `archevolve.EVIDENCE_COMMANDS` (`swdb/archevolve.py:12-16,121-126`), so their public CLI guard adds no Store. They still apply explicit `require_team_safe` using the handler's existing Store. Native collector constructs its Store at `cpu_native_validation.py:59`, then `writer.commit` at207. Development/heldout handlers construct a Store at `cpu_error_band.py:134,190`, then commit at162/208. Writer independently loads and validates the whole catalogue under lock (`writer.py:95-134`); these handlers do not call `workflow.persist` or SQLite build. The public freeze/estimate counts retain the original audit's additional team guard load. Standalone validate constructs one Store (`validate.py:23-27`).

The current development/heldout runner adds an initial Store and one reload after each of its two band writes. Thus each whole phase performs **12 full Store constructions and5 full catalogue validation passes, with0 SQLite rebuilds**, excluding exporter work: initial1 + two collect stages4 + two band stages4 + two reloads2 + final validate1. Its initial model/target pin reads and post-band identity reads add digest/selected-record work, not further Stores. The future report runner performs **19 full Store constructions,9 full catalogue validation passes and2 SQLite rebuilds**: initial1 + two freezes10 + two estimates6 + final saved-pin reload1 + final validate1. Exporters each add a further Store and selected identity/admission work outside those runner counts, without another broad validation.

## Work beyond the table

The new estimate persists its target snapshot, aggregate and five trial region predictions, binding, legacy reconciliation and parameter report (`analytic.py:649-688`). Every later writer rechecks all prior records. Development bands copy the aggregate estimate regions into the retained pair (`cpu_error_band.py:124`) and revalidate exact estimate/characterization/protocol/native identities. Heldout validation also checks the development band recursively (`:67-72,166-184,290-337`), retaining unchanged width/state. These are additional selected schema/payload, hashing, region-copy and semantic checks inside the listed passes; they do not create additional full Stores. Report protocols pin a band snapshot and dependency closure, and report estimates retain unchanged per-region costs plus the admitted band. The future catalogue is enriched by those artifacts even though native observation records themselves are comparatively compact; exact future sizes are unavailable.

The parse cache stores at most256MiB of **canonical JSON text** and clears the whole cache on overflow (`access.py:53-91`). YAML byte totals alone cannot prove cache overflow. If the actual compact serialized catalogue crosses that threshold, repeated sequential scans can become cold/churn instead of simply scaling a warm-cache time. Separate CLI processes always start with separate caches. Therefore neither pass counts nor YAML growth determine a linear wall-time multiplier.

## What is measured and what is illustrative

Parent filesystem-only receipt `/private/tmp/lanl-model-catalog-size-latest-20261007.json`, checked06:42:56Z, reports base665 YAML files **324,332,488B**, current669 **379,897,957B**, and the first BFSg16 estimate exactly **53,583,441B**. The four immutable input characterization files are14,485,038/14,548,815B (BFSg16/g17) and17,282,501/17,343,787B (BCg16/g17). Those graph/input file sizes do not establish forecast or catalogue-processing time scaling.

Parent reports actual same-C BC public freeze **1266.086438s** and first BFSg16 public estimate **729.741s**, both successful. Remaining three estimate sizes/times, complete model catalogue size, actual full-validation time, future native/band/report stage times and compact-cache size are unknown. As a size illustration only, if each remaining estimate had the first estimate's byte size, the catalogue would become540,648,280B (about1.67x the base) before native/band/report additions. This is neither an observed future size nor a time prediction.

## Cap assessment before outcomes

Current band/default metadata and validation cap1400, collection-process cap2100, and report-freeze cap1800 are **unproved** after all four estimates accumulate. The new1800 report-freeze cap is based on an earlier catalogue before the four large forecasts; it has534s over the observed BC freeze, but no established enriched-catalogue bound. The729.741s first estimate similarly cannot bound an estimate after more records/bands exist. Current whole-phase budgets are finite administrative ceilings, not measured science runtimes.

The scientific **900s native collector deadline is fixed separately**: it starts after Store/count/protocol/environment preflight (`cpu_native_validation.py:59-88`), supplies every actual collector command's remaining timeout (`:89-99`), and covers build/correctness/timing operations. The timing ends at164; writer validation/persistence happens later at207, outside that native deadline. Raising only an enclosing collection-process timeout can accommodate pre/post metadata without extending a native command or five-trial recipe. Timeout after timing but during metadata must preserve completed raw observations rather than repeat outcomes blindly.

A defensible one-time conservative administrative option, chosen **before application outcomes**, is metadata/band/estimate/validation2400s, enclosing collection3600s (still native900), and report protocol-freeze3600s; development/heldout inner18000/outer18300 and report inner16800/outer17100 then allow their sums plus bounded parent loads/copy/cleanup. These remain unproved finite limits, not new scientific timing budgets or claims of likely duration. Parent can instead await the completed model sizes/stage times before selecting a smaller envelope. Any chosen variant needs a distinct helper, explicit cap-only byte/AST reversal, existing portable mocks, immutable C/F6/raw-a3/17a1/OpenMP references, unchanged two per-kernel widths and no outcome retuning. **No such control revision was created or executed by this audit.**

Correction before any future dispatch: the initial note reported18 overall report Stores and omitted the selected runner’s final saved-pin reload. Decoded selected RUNNER_TEMPLATE lines141–142 construct a Store for perform_report and a second Store for the saved target/calibration/characterization pin checks before public validate. Correct count19; no extra validation pass. Development/heldout count12 is unchanged: its line70 reload is model-only and excluded from those two admitted public phases. The initial note is retained separately as `lanl-ticket11-future-metadata-cost-audit-20261007-initial18stores.md` for transparent custody.
