# Registered Jacobi count preparation

Created: 2026-10-06 ET. Parent dispatches; this recipe collects no uninstrumented application performance.

The source-only implementation `gapbs-pr-jacobi-analytic-v1` is the byte-identical application `src/pr_spmv.cc` (SHA-256 `ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70`), with original `PageRankPull`, flags, convergence defaults, and protected verifier/benchmark. Its explicit source baseline is itself; the historical kernel still defaults to Gauss-Seidel. The public small scale-8/edge-factor-4 add→snapshot→count test passed in 182.73 s. No observer, adapter, estimator, model or old record changed.

From the clean checked-out SWDB cwd, inside the parent's verified leased socket wrapper, run one of these with a fresh absolute raw directory and pinned LLVM 22 bin directory:

```sh
bash .scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-count-pagerank-20261006.sh cpu "$NEW_RAW" "$LLVM_BIN"
bash .scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-count-pagerank-20261006.sh dx100 "$NEW_RAW" "$LLVM_BIN"
bash .scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-count-pagerank-20261006.sh maple "$NEW_RAW" "$LLVM_BIN"
```

Each invocation requires its own raw path, copied store, source snapshot and count ID. CPU uses T1, DX100 T4, and MAPLE T2. All use the actual original source-free `gapbs.functional_trial_lambda.v1` ROI, five trials, `kron-g16-k16`, original `-g 16 -k 16 -n 5`, source-normalized-v2 and opt-in object scopes. The realized graph and convergence work come only from the fresh execution receipt. No artificial source choice or fixed sweep count is added.

The current original Jacobi source has no DX100 or MAPLE command lowering. Accordingly these are native source-count projections at the requested threads, and the script deliberately supplies no command target description. It proves host work, not an accelerator address/window/domain policy. Later public estimates must retain unknown offload stream, lowering/type, queue/coherence and resource-overlap premises. The DX functional contract requires `FUNC`; adding that macro or inventing a backend view on the original GAPBS source would change its source contract. MAPLE has no executable normative queue interface in this repository. These concrete missing observations cannot be replaced by CPU T1 counts or numerical rates.

Export compact metadata and canonical records only after validation, source-clean and release checks. Keep IR, addresses, binary, instrumented stdout and raw streams on mbit10. The parent records actual argv, helper/source hashes, compiler/runtime identity, lease and capacity. Original source/legacy implementation bytes and existing record bytes stay protected.

Final CPU service/error admission remains exactly the four BF/BC g16/g17 T1 objects.a1 characterizations. Jacobi has no transfer or band admission from them. Final estimates/reports wait for generic 11/17 closure and a fresh frozen final DX BFS reference; all nine executions must share the exact portable Python and mechanism-module hashes. The script's CPU/DX/MAPLE names choose only thread/count identities, not estimator behavior.
