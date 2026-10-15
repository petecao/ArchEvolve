# Original float loop initializedness hints

2026-10-15 ET. **Compiler/merge correction only; actual safe/seeded WP acceptance is pending.**

The retained original matrix at `/data/yanruj/EvolveSWDB_runs/probata-resume-t24-pending-9b75f4a2` stopped on `floats:safe`: 41 ordinary Valid, 5 smoke Valid, and three ordinary initialization timeouts, among 12 initialization goals. Exact record: `proof.wp24-safe.candidate-1.20261015t204154z.1f9883a8`.

The open goals `_rte_initialization_2`, `_5`, and `_7` map respectively to `r.value` in the loop compound update, `r.weight` in that update, and `r.value` after the loop. Retained `wp-normalized.c` lines 99, 103, and 126 show those predicates. Both the unchanged C++ fixture and its actual generated C explicitly write `r.value=0.0` and `r.weight=scale*0.5f` before the loop. The existing hints carry numerical bounds and `loop assigns i, r.value`, but no field initializedness facts. This identifies missing loop initializedness persistence; no lost initializer was found in the lowering. The timeout itself is not proof that the new hints suffice.

`tests/test_wp_subset.py` now adds two ordinary loop invariants at `swdb_float_unit.loop1.head`: `\initialized(&r.value)` and `\initialized(&r.weight)`. Their establishment follows the preceding field assignments; preservation still must be proved against the loop body. The weight field is unchanged, while each value update reads initialized fields and an initialized bounded input element before writing value. The invariants cover fields individually and make no claim about aggregate padding. Original source, contracts, numerical bounds, frame and variant stay unchanged. No assumption, RTE removal, source rewrite, solver flag or production lowerer change was introduced.

The compiler-only public `swdb lower` plus deterministic `hint_check.merge` regression failed first on the missing value invariant, then passed with both field invariants. It checks their placement as loop invariants and that erasing annotations recovers the exact ordinary C. It also preserves the original explicit initializers and excludes an aggregate padding initialization claim. The diagnosed case is in ticket21's shared regression corpus: `tests/fixtures/proof/regression_corpus/wp-float-loop-field-initialization.yaml`.

One sequential worker used the selected Python 3.12.6 and pinned LLVM 22.1.8 under the 8 GiB RSS watchdog. RED: 1 failed, 1.95 s guarded wall, 140,492,800 B peak. GREEN: 1 passed, 1.29 s guarded wall, 157,941,760 B peak. No WP or solver ran. The compiler slot was released directly to ticket24's atomic repair owner after GREEN.

The old five-hint YAML hash `83fa1ae941e06ba9213b44d90bce3945bfb3466d0c73748330a9b7bd6e61e8d6` matches the actual retained remote hints exactly. The new seven-hint YAML hash is `0d7e18cae18f823b5d8fd4b07ee988ea751ea21a4fbac647b048992055efd635`. Original float fixture hash remains `c41740bfaced1d9f04a499865b0f09b0f7a34c38756581ffa8d13a66a4870d8d`.

Exact predicates, paths, flags, source/hint hashes, and RED/GREEN resource records are in [the compact evidence](t24-float-initialization-hints-20261015.json). Local raw compiler-only evidence is `/private/tmp/probata-t24-float-init-20261015/`; no raw remote proof output was transferred.

Next acceptance step belongs to the coordinator: fresh remote `t24-original-matrix.py --groups floats --cases floats:safe,floats:seeded --stop-on-failure` at the merged exact source. Preserve every RTE/init/smoke goal, require all ordinary invariant establishment/preservation goals and smoke checks Valid for safe, and retain an attributable ordinary failure for the unchanged seeded value=1 bug. At least the original 12 initialization obligations must remain represented. Compiler/merge GREEN is not a proof result.
