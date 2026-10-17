# Historical original matrix frontier at 9b75f4a2

Updated: 2026-10-15 ET. These are actual WP results at the frozen source,
not acceptance under the repaired translator. Overall ticket24 remains claimed.

| Original case | Ordinary valid/open | Smoke valid | Frozen acceptance |
| --- | --- | --- | --- |
| DXC summary | 4/0 | 1 | accepted |
| DXC safe | 9/0 | 3 | accepted |
| DXC corrected +4 seed | 8/1 ensures timeout | 3 | accepted negative |
| Classes safe | 146/0 | 11 | accepted |
| Classes seed | 146/1 invariant-preserved timeout | 11 | accepted negative |
| OpenMP safe | 67/0 | 8 | accepted |
| OpenMP seed | 66/1 invariant-established timeout | 8 | accepted negative |
| Floats safe | 41/3 initializedness timeouts | 5 | failed safe acceptance |

The class rows each retain 46 initializedness goals; OpenMP each retains 18,
and floats retains 12. Negative timeouts are attributable open ordinary goals,
not solver refutations. All eight rows passed setup, actually launched, and
retain RTE, all initializedness, smoke, no-cache and x86_64 mandatory options.
No later float seed/std/atomics/MAA/lifetime rows ran before stop-on-failure.
The separate Ring and allocation pair receipts retain their earlier freeze.

The exclusive exact-environment [compact audit](t24-historical-frontier-9b75-mbit10-20261015.json)
checks all 983 physical source hashes/Git blobs, eight records, 97 report/log
instances and 644 artifact file instances with zero integrity errors. It checks
original full fixture variants/clauses/hints, fresh dependency/source bindings,
member certificates/normalized selected entries, setup and naming pins. The
first default-SSH reader receipt remains unchanged: its environment lacked
clang++, yielding an unavailable-tool aggregate mismatch. Replaying exactly
the retained launch environment resolves the historical translator hash
`5d9a246e9d803e56ade4d6b4bc5c30c8cbf42b4e5064153e652f2c05ffed732d`.
The new receipt decomposes parser, actual driver, wrapper and header-tree hashes;
it does not upgrade the separate native linked-DSO identity boundary.

Generation 571 released at 20:45:33Z: exit 1 after 2,368.46 seconds,
peak RSS 2,169,536,512 bytes, no OOM or whole-job timeout, source unchanged.
The retained 20:51Z read-only process receipt found no matching run-prefix
survivors and no access-denied processes. Raw solver artifacts stay on mbit10.

Current-source replay is still necessary after atomic/enum admission repair
and the separately reviewed ordinary float initializedness hints. Existing
historical records are neither rewritten nor borrowed as current-method proofs.
