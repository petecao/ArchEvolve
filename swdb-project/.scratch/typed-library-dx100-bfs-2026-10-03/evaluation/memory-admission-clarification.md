# NUMA admission correction

Updated: 2026-10-03 ET.

The user's question exposed an overly conservative operational refusal: selected-node
MemFree was treated as all allocatable RAM. That excluded normal Linux file-cache
reclamation. The prior own-file cache inventory concerned explicit eviction of a
bounded owned list; it did not establish what the kernel could reclaim during an
ordinary strictly bound allocation. No manual eviction is required for this correction.

At 10:38 ET, a live read-only mbit10 observation reported node 0 MemFree 31,492,620 KiB,
Inactive(file) 23,811,664 KiB, Mapped 949,760 KiB, Shmem 6,440 KiB, Dirty 312 KiB,
Writeback 0 and Unevictable 39,068 KiB. The conservative estimate is about
36.913 GiB after a 4 GiB reserve. Global MemAvailable is excluded. This transcription
comes from live tool output; no separately retained raw-file receipt or hash is claimed.
The actual launch must reobserve current counters under its socket lease.

Linux distinguishes MemFree from the estimate of RAM available to start an application;
the latter accounts for reclaimable file pages while reserving cache and zone capacity.
Strict MPOL_BIND restricts eligible nodes during reclamation and allocation.
Primary references: [Linux 6.8 proc memory accounting](https://www.kernel.org/doc/html/v6.8/filesystems/proc.html#meminfo)
and [Linux 6.8 NUMA memory policy](https://www.kernel.org/doc/html/v6.8/admin-guide/mm/numa_memory_policy.html).

The corrected public preflight keeps literal `free_memory_bytes` and separately records
`estimated_memory_capacity_bytes`. Its conservative local rule is:

```
eligible = max(0, inactive_file - mapped - shmem - dirty - writeback - unevictable)
credit = floor(eligible / 2)
reserve = max(4 GiB, ceil(node_total / 16), observed_selected_node_zone_reserve)
capacity = max(node_free, min(node_total, node_free + credit - reserve))
```

No active cache, slab or other-node/global memory contributes credit. Zone reserve
conservatively sums each selected zone's capped managed/high/boost/protection
accounting; counting boost twice when already included in high is conservative.
Managed-zone byte totals must reconcile with node MemTotal. Missing/incomplete proof
uses MemFree only. Known contradictory memory or zone accounting refuses even when
unused memory would otherwise satisfy the budget. No allocation probe occurs.

The estimate is not a reservation or a guarantee of execution success. Ordinary
kernel reclaim can affect host wall time; scientific ratios remain simulated gem5
ROI counts under the pinned treatment. Admission is rechecked by the driver and
public execute path. Socket binding, timeouts and existing runtime checks remain
in force. Actual 32.178–32.642 GiB simulator peaks still justify the 36 GiB budget.
The 16GB guest/MMIO model and prepared binaries/protocol remain unchanged.

Both final independent review axes pass. Final affected files pass 39 cases in 7.47s;
22 new cases bring reconciled local identities to 3,727 = 3,691 pass + 36 skip, with no
unresolved failures. The original 33-pass receipt and intermediate fixture failures
are retained; the latter exposed an ARM page-size assumption and assertion-edit
mistakes in new tests, corrected before dispatch. Final receipt:
[memory-admission-final-a5-junit-20261003.xml](memory-admission-final-a5-junit-20261003.xml),
SHA256 `e07a8c4395e1e9658d401df1376728ee5916e080682b7d7588bb49f6f182786a`.

This correction does not establish L3, target timing or gain. Those still require
the actual companion and timed evaluations.
