# index_features

Created 2026-09-22 (Eastern). Updated 2026-09-22.

A small C++ tool that computes exact index-stream features of a gapbs graph. It
builds the graph with gapbs's own `Builder` (`apps/gapbs/src`, upstream commit
`2972aeb`, unchanged), so it gets exactly the graph the kernel sees. It then walks the
neighbor IDs in the kernel's visit order. No sampling, no counters, serial.

## Build

From the repo root, on the Mac or on mbit10:

```sh
c++ -std=c++11 -O3 -Wall -I apps/gapbs/src tools/index_features/index_features.cc -o <out>
```

The build needs no OpenMP. On mbit10, g++ may warn about gapbs's `#pragma omp`
lines; that is expected. Adding `-fopenmp` there only speeds up graph generation.
The graph is the same either way: gapbs seeds its generator per block, and
`SquishCSR` sorts every neighbor list.

**Use the same C++ standard library as the kernel binary.** gapbs's Kronecker
generator (`-g`) relabels vertices with `std::shuffle` (`Generator::PermuteIDs`),
and the C++ standard leaves that algorithm to each library. libstdc++ (g++) and
libc++ (Apple clang) therefore give the same graph with different vertex IDs.

On 2026-09-22 on the Mac, `-g 16 -k 16` gave identical label-free features
(`L`, `D`, `duplicate_ratio`, and the degree statistics) under Apple clang/libc++
and Homebrew g++-16/libstdc++. The order-dependent features differed:
`sequential_fraction` was 0.01096 under clang and 0.00981 under g++, and the reuse
histograms also changed.

`-u` graphs do not go through `PermuteIDs` and were byte-identical. The g++
serial and g++ `-fopenmp` builds gave byte-identical JSON for `-g 16`.

On mbit10, both gapbs and this tool build with g++ 13.3 and libstdc++, so the
graphs match. Mac numbers for `-g` graphs describe the libc++ labeling only. Record
the compiler with every profile.

## Command line

```text
index_features [--order ORDER] [--element-bytes N] [--line-bytes N] [--out PATH|-] -- <gapbs graph args>
```

| Option | Default | Meaning |
|---|---|---|
| `--order` | `in_neighbors_by_vertex` | Visit order (see below). |
| `--element-bytes` | `4` | Bytes per element of the array the indices point into. |
| `--line-bytes` | `64` | Cache-line size in bytes. |
| `--out` | `-` | JSON output file, or `-` for stdout. |
| `--help` | | Print usage and exit 0. |

Everything after `--` goes to gapbs's `CLBase::ParseArgs`, as it would for a gapbs
kernel: `-g <scale>` (Kronecker), `-u <scale>` (uniform random), `-k <degree>`
(default 16), `-f <file>` (for example `.el`, `.sg`), `-s` (symmetrize), and `-m`.
gapbs symmetrizes generated graphs itself.

Example:

```sh
index_features --order in_neighbors_by_vertex --element-bytes 4 --line-bytes 64 \
  --out features.json -- -g 16 -k 16
```

Bad arguments make the tool exit with status 2 and print a message on stderr. Bad
arguments include an unknown tool option, a missing `--`, an unknown or incomplete
gapbs option, a stray positional argument, a non-numeric or out-of-range `-g`, `-u`,
or `-k`, a non-positive byte size, and no graph input. A gapbs failure, such as a
missing input file, exits non-zero with gapbs's own status and message. A failed run
writes no JSON file.

### Stdout and gapbs's own output

gapbs prints `Read Time:`, `Generate Time:`, `Build Time:`, and its diagnostics to
stdout. While gapbs parses arguments and builds the graph, the tool points stdout at
stderr (with `dup2`), and restores it afterward. So:

- `--out <path>` (recommended for callers): the JSON goes to the file, and stdout
  stays empty.
- `--out -`: stdout carries exactly one JSON line.

In both modes, gapbs's lines appear on stderr.

### Visit orders

- `in_neighbors_by_vertex`: `for u = 0..N-1` in increasing order, then
  `for v in g.in_neigh(u)` in stored order. This is exactly the gather order of gapbs
  `PageRankPullGS` / `PageRankPull`.
- `out_neighbors_by_vertex`: the same with `g.out_neigh(u)`.

The builder sorts every neighbor list and removes self loops and duplicate edges.
For an undirected (symmetrized) graph, `in_neigh` and `out_neigh` are the same lists.

## Output

One JSON object with the keys always in this order. Integers are printed as
integers. Ratios are printed with the fewest digits (15 to 17 significant) that read
back as the same double, and always contain a `.` or an exponent.

```json
{"tool": "index_features", "tool_version": 1, "order": "in_neighbors_by_vertex",
 "element_bytes": 4, "line_bytes": 64,
 "line_mapping": "line = floor(index*element_bytes/line_bytes), array assumed line-aligned",
 "graph": {"num_nodes": 65536, "num_edges_directed": 1819292, "directed": false},
 "stream_length": 1819292, "distinct_indices": 46715,
 "duplicate_ratio": 0.9743224287250205, "sequential_fraction": 0.010960863325328384,
 "same_line_fraction": 0.06686121131803544,
 "reuse_distance_histogram": {"unit": "elements", "cold": 46715,
   "buckets": [{"bucket": 0, "lo": 0, "hi": 0, "count": 20}, ...]},
 "line_reuse_distance_histogram": {"unit": "lines", "distinct": 4096, "cold": 4096,
   "buckets": [{"bucket": 0, "lo": 0, "hi": 0, "count": 121640}, ...]},
 "degree": {"which": "in", "mean": 27.76019287109375, "max": 9869,
   "gini": 0.8680952962123281, "cv": 4.866839364898925}}
```

(That is real output for `-- -g 16 -k 16` from the Mac build, which uses Apple clang
and libc++, with the bucket lists shortened. A g++ build labels the Kronecker graph
differently; see Build.)

### Field definitions

The **index stream** `i[0..L-1]` is the sequence of neighbor IDs `v` in visit order,
one entry per directed edge visited.

| Field | Definition |
|---|---|
| `tool`, `tool_version` | `"index_features"`, `1`. The version goes up when a definition changes. |
| `order`, `element_bytes`, `line_bytes` | The options used. |
| `line_mapping` | `line(x) = floor(x * element_bytes / line_bytes)`. This assumes the target array starts on a line boundary. |
| `graph.num_nodes` | `g.num_nodes()` (for `.el` input, the largest ID + 1). |
| `graph.num_edges_directed` | `g.num_edges_directed()`, after gapbs removes self loops and duplicates. |
| `graph.directed` | `g.directed()`. It is `false` for `-g`, `-u`, and `-s`. |
| `stream_length` | `L`. It always equals the sum of the walked degrees, which is `num_edges_directed`. |
| `distinct_indices` | `D`, the number of distinct values in the stream. |
| `duplicate_ratio` | `(L − D) / L`, the fraction of index reads that repeat an index already seen in the same sweep. It is `0` if `L = 0`. |
| `sequential_fraction` | `#{k : i[k+1] = i[k] + 1} / (L − 1)`. It is `0` if `L < 2`. |
| `same_line_fraction` | `#{k : line(i[k+1]) = line(i[k])} / (L − 1)`. It is `0` if `L < 2`. |
| `reuse_distance_histogram` | For each access at position `k` to `x`, where `x` was last accessed at `p`: the reuse distance is the number of **distinct** indices at positions strictly between `p` and `k`, so an immediate repeat has distance 0. First accesses are not bucketed. They are counted in `cold` (= `D`). |
| `buckets` | log2 buckets: bucket 0 holds distance 0, and bucket `b ≥ 1` holds distances in `[2^(b−1), 2^b − 1]`, given as `lo` and `hi`. Every bucket from 0 through the highest non-empty one is listed, including empty ones in between. `cold + sum(count) = L`. |
| `line_reuse_distance_histogram` | The same definition over the line stream `line(i[k])`, counting distinct lines. `distinct` is the number of distinct lines, which equals its `cold`. |
| `degree.which` | `"in"` for `in_neighbors_by_vertex` and `"out"` for `out_neighbors_by_vertex`: the degree the ranged step walks. |
| `degree.mean`, `degree.max` | Taken over **all** `N` vertices, including those with degree 0. `mean = L / N`. |
| `degree.gini` | `G = Σ_{i=1..N} (2i − N − 1) d_(i) / (N Σ d)`, with `d_(i)` sorted in ascending order and computed exactly from the sorted degrees. It is `0` when the degree sum is 0 (and comes out 0 when all degrees are equal). |
| `degree.cv` | Population standard deviation divided by the mean. It is `0` when the mean is 0. |

## Algorithm and cost

The tool makes three serial passes over the stream.

1. The first pass computes `L`, the sequential steps, and the same-line steps.
2. The second pass computes element reuse distances.
3. The third pass computes line reuse distances.

Reuse distances use a Fenwick tree (BIT) over stream positions, which runs in
O(L log L) time. The tree marks the latest position of each value. When value `x` is
seen again at `k` after `p`, the number of marks in `(p, k)` is the distance, which
equals `total marks − prefix(p)`. The tool then moves the mark from `p` to `k`. The
passes use one `int32` BIT (`4L` bytes) and one `int64` last-position table
(`8N` bytes, or `8 × lines` bytes in the line pass), one pass at a time, plus the
graph. Counters are 64-bit.

The algorithm was cross-checked on `-g 10 -k 16` with `--line-bytes 32` against an
independent brute-force LRU-stack computation in Python (2026-09-22). All histograms,
fractions, the Gini coefficient, and the coefficient of variation matched exactly.

Measured on the Mac (Apple Silicon, Apple clang 21, `-O3`, serial) on 2026-09-22,
with `/usr/bin/time -l`:

| Graph args | L | Wall time | Max RSS |
|---|---|---|---|
| `-g 16 -k 16` | 1,819,292 | 0.31 s | 21 MB |
| `-u 16 -k 16` | 2,096,552 | 0.25 s | 21 MB |
| `-g 20 -k 16` | 31,399,382 | 10.0 s | 300 MB |
| `-g 22 -k 16` | 128,311,450 | 30.9 s | 1.19 GB |

## Tests

`tests/test_index_features.py` compiles the tool with the build command above and
runs it as a separate process. It checks the following:

- The features of `tests/fixtures/index_features/tiny.el` match hand-computed values
  in the directed-in, directed-out, symmetrized (`-s`), and default-line-size cases.
  The hand computation is written out in `expected.yaml`.
- Bad arguments exit non-zero.
- A `-g 10 -k 16` Kronecker graph is internally consistent.

```sh
python3 -m pytest -q tests/test_index_features.py
```
