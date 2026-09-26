# Native selected-region comparisons

Updated: 2026-09-26 ET.

The additive `native_diagnostic_profile.v1` evidence treatment compares the
separate CPU observations produced by `bfs-profile`. It never reads invented
regions from the primary evaluation's `profiling` field. Existing legacy region
pairs retain their original rules; selecting this treatment requires a new
prospective protocol version and observations made after its freeze.

Each native `region_pairs` entry retains the semantic correspondence, baseline
and candidate region IDs, `scope` (`accumulated` or `per_invocation`), and
`attribution` (`inclusive` or `exclusive`). Add these fields:

```yaml
evidence: native_diagnostic_profile.v1
diagnostic_repetitions: 1
collector:
  backend: libclang-cindex
  clock: CLOCK_THREAD_CPUTIME_ID
  library_sha256: <exact libclang hash>
  pass_sha256: <exact discovery pass hash>
  collector_sha256: <exact bfs_profiling.py hash>
  runtime_sha256: <exact scope runtime hash>
```

`diagnostic_repetitions` is an integer from 1 to 10 and cannot exceed the primary
sampling repetitions. All native pairs in one protocol use the same diagnostic
repetition count. The diagnostic count is separate from the primary sample count:
one diagnostic execution per source does not become five wall-time samples.
The source position indexes the primary evaluation's complete ordered source
list, and every diagnostic cell must exist in the primary grid.

The `compare-evaluations` request supplies `region_packages`, mapping each of
the two actual native evaluation IDs to its sealed `profile_package` ID. The
package must reference that evaluation and its exact `region_profile`. A package
from an earlier pilot cannot stand in for a fresh frozen baseline package. The
native campaign driver collects the current baseline package when this treatment
is selected and passes both actual package IDs. Its existing overall and per-stage
budgets remain in force; extra profiling does not extend them.

Comparison checks the current package and profile content identities, source
snapshot, graph, source order, machine, configuration, threads, ROI, primary
binary, diagnostic binary, compiler and flags, runtime and collector identities.
It rehashes the diagnostic build files and reconstructs the source-to-counter
instrumentation mapping from the verified source extents. Each diagnostic run
needs a matching completed execution stage after freeze. Its parent output is
structurally checked again against the exact canonical graph, and its per-trial
region JSON is parsed and hashed. The sum of those raw observations must equal
the region's retained accumulated counters. Missing or stale raw data, duplicate
cells, unentered selected regions, invalid counters, or incompatible bindings
reject the comparison with a durable reason.

Comparison creation therefore runs where these raw artifacts are available.
Native profiles currently store per-trial durations in raw reports and only
accumulated values in region rows. Local metadata alone cannot recover the
per-source distribution. A completed comparison retains its raw references and
sample values for later metadata retrieval; retrieval does not pretend to
recheck unavailable remote bytes.

The result reports the geometric mean of per-source median CPU-duration ratios.
`per_invocation` divides each diagnostic duration by its own invocation count
before computing the median. `exclusive` means the selected lexical scope with
nested guarded scopes subtracted, including loops nested inside functions; it
does not use the separate function-ranking sum. Instrumentation overhead remains
included. Thread CPU time excludes descheduled time and is a different quantity
from native BFS wall time. Region results always have `primary_bfs_roi: false`
and `gain_claim: false`, with no diagnostic confidence interval or profitability
verdict. The primary BFS result and its frozen wall-time decision remain separate.

The public regression uses all 24 compiler-discovered regions from the retained
upstream scale-18 profile as its source/layout template, paired with explicitly
synthetic per-trial counters and fixture evaluations. It tests the actual
collected representation without treating fixture durations as empirical evidence.
