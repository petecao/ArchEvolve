# Provider guard fixtures (campaign a8)

Created: 2026-10-05 (Eastern Time), ticket 74.

Byte copies of the guard receipts of native campaign `extensa-native-bfs-20261005-a8` calls 1 (setup
profiling) and 6 (iteration 5) on mbit10, from
`/data/yanruj/EvolveSWDB_runs/extensa/extensa-native-bfs-20261005-a8/provider/extensa-native-bfs-20261005-a8.call{1,6}/`:

| File | sha256 |
|---|---|
| `a8-call1.resource-overrun.json` | `94cd7c7d...` |
| `a8-call1.guard-audit.json` | `177d1830...` |
| `a8-call6.resource-overrun.json` | `8449345d...` |
| `a8-call6.guard-audit.json` | `6995e804...` |

Each tree is strace (1 thread) plus Codex 0.153.0 (16 threads: `codex`, `codex-main`, 12
`tokio-rt-worker`, 2 `notify-rs inotify`), stopped about 0.5 s after launch for `threads=17` against
the old aggregate 16-thread cap, before any tool command. Both calls were counted as `guard_refused`;
ticket 74 classifies them as harness limits (uncounted).
