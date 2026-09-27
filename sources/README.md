# Source references

The repositories below were fetched into Desktop/ArchEvolve for source inspection. They are shallow, sparse checkouts at detached commits. The selected files are complete; the checkout does not include all simulation infrastructure, graph datasets, or built dependencies.

| Repository | Recorded commit | Local source |
|---|---|---|
| [DX100 artifact](https://github.com/arkhadem/DX100) | `e4fc4afdf894f295442cef3604667a469fab8e62` | [Modified BFS reference](https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/gapbs/src/bfs.cc), locally under `sources/DX100`, plus GAPBS/API headers |
| [Upstream GAPBS](https://github.com/sbeamer/gapbs) | `2972aeb2703165bafd921222f4ed7196f542d3a8` | [Upstream BFS reference](https://github.com/sbeamer/gapbs/blob/2972aeb2703165bafd921222f4ed7196f542d3a8/src/bfs.cc), locally under `sources/gapbs-upstream`, plus `src` headers |

[manifest.json](manifest.json) records exact revisions, selected paths, BFS line counts, and SHA-256 values. [bfs-upstream-to-dx100.diff](bfs-upstream-to-dx100.diff) compares those snapshots. The upstream snapshot is a reference, not a verified historical base of the artifact's changes.

The nested repositories are ignored by the outer project's `.gitignore`. Their original source and license files remain intact. No benchmark build, simulation, profiling, or correctness run has been performed.

The saved source comparison includes GAPBS source excerpts. Its [original license](licenses/GAPBS-LICENSE.txt) is retained here; it is not a license declaration for the rest of the ArchEvolve project.

To recreate a missing DX100 checkout:

```sh
git clone --depth 1 --filter=blob:none --sparse https://github.com/arkhadem/DX100.git sources/DX100
git -C sources/DX100 sparse-checkout set benchmarks/gapbs/src benchmarks/API
git -C sources/DX100 fetch --depth 1 origin e4fc4afdf894f295442cef3604667a469fab8e62
git -C sources/DX100 checkout --detach e4fc4afdf894f295442cef3604667a469fab8e62
```

For upstream, use `https://github.com/sbeamer/gapbs.git`, local path `sources/gapbs-upstream`, sparse path `src`, and commit `2972aeb2703165bafd921222f4ed7196f542d3a8`.

See [the source review](../docs/bfs-source-review.md) before choosing a function/build variant for feature extraction. Build instructions in external READMEs are reference material; they were not executed as part of this inspection.
