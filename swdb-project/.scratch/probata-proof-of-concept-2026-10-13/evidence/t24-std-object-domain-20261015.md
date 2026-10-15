# Ticket 24: explicit std empty-range domain, 2026-10-15 ET

The original current-source std safe caller remains **not proven**. Its actual record retains 46 valid ordinary goals, one pointer-formation timeout, 13 valid smoke goals and five initialization obligations. All five fresh standard-model records passed. The final immutable current-source frontier audit is preserved in `t24-current-std-frontier-0e7f2327-20261015.json`: zero artifact integrity errors, one caller acceptance failure. No later original groups ran in that stopped profile.

The original source evaluates `a + n` before `std::copy`. At n=0 its empty validity/initialization/separation ranges supply no object fact for arbitrary non-null endpoints. The unchanged generated assertion requires null-plus-zero or an object/one-past origin. Consequently this is a real original-contract domain gap as well as a conservative proxy boundary; a timeout is not a solver counterexample. We do not remove the assertion or add an adapter assumption.

C++17 defines array/one-past pointer arithmetic and null-plus-zero in [expr.add](https://timsong-cpp.github.io/cppwp/n4659/expr.add). Valid empty iterator ranges and value-initialized forward iterators are addressed in [iterator requirements](https://timsong-cpp.github.io/cppwp/n4659/iterator.requirements.general) and [forward iterators](https://timsong-cpp.github.io/cppwp/n4659/forward.iterators); [copy](https://timsong-cpp.github.io/cppwp/n4659/alg.copy) performs zero assignments for an empty range. Merely copying an invalid pointer value is implementation-defined under [basic.stc](https://timsong-cpp.github.io/cppwp/n4659/basic.stc), so the diagnostics do not label every dangling-pointer copy UB. Arbitrary non-object/dangling arithmetic and iterator use are outside the portable domain supplied here.

The new separately named contract `contract.fixture_wp24_std_models_object_domain` retains the exact original source, function, array domains, numerical constraints, frame and postcondition. It adds only this disclosed conservative sufficient condition for each p in {a,b}:

```acsl
requires n == 0 ==> (p == \null || \valid_read(p) ||
  (\base_addr(p - 1) == \base_addr(p) && \valid_read(p - 1)));
```

The original contract canonical SHA-256 is `13fd0509e48eb0d9f45e8e6edc9a0fd5a4fec66d45f3e3cc525ee072b09c57d9`; the qualified contract is `762deba8e2d8dc8961500d26209a6857553993225eadb0da6a12a8ba3b0c341a`. Null, readable live bases, readable-predecessor one-past and original n>0 ranges remain covered. C++17 permits zero-element allocation ([expr.new](https://timsong-cpp.github.io/cppwp/n4659/expr.new)); a live zero-size allocation may have no readable element or predecessor, so it remains unsupported by this proxy, **not classified UB**. The new witness cannot be described as unchanged-original success.

The original C++17 TU and actual lowered C, compiled separately with ASan+UBSan, agreed for null+0, live-base empty, live-one-past empty and n=1 controls. Zero-size allocation also ran successfully but is separately diagnostic. Quiet dangling/nonobject runs establish no semantics. An intentional bad read failed under UBSan in both binaries. Native observations are neither WP acceptance nor finite-domain exhaustive agreement; `t24-std-empty-domain-native-20261015.json` pins commands, sources, binaries, outputs and resources. Independent design review is preserved alongside this note.

The targeted `prototype/t24-std-object-domain.py` keeps the old seed read-only, copies records/library into a new output tree, and retains the original failed record as `std_models_original_contract_gap`. It requires the exact diagnosed 0e7 manifest, exact current production source file set/bytes, current translator/setup/method/model text and range-qualification pins. The five previously proved model IDs must be selected by ordinary public dependency eligibility. There is no trusted-ID override or dependency bypass. Only the qualified safe and seeded callers launch; all RTE, initialization, smoke, timeout and resource checks remain mandatory. Safe must prove; seeded must retain an attributable ordinary open obligation. Actual qualified acceptance is pending.

Assumption: the already independently reviewed current 0e7 model records remain ordinarily eligible in the exact launch tool environment. If eligibility fails, the public invocation must refuse; the runner does not weaken that decision. Runtime bytes remain exactly 0e7; this commit adds tests, fixture qualification, profile and evidence only. Existing source/evidence paths and historical verdicts are preserved.

Suggested reviewed remote profile (root owns socket dispatch):

```sh
python .scratch/probata-proof-of-concept-2026-10-13/prototype/t24-std-object-domain.py \
  --expected-commit REVIEWED_SOURCE_SHA \
  --from-seed /data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t24/matrix/seed \
  --output "$PROBATA_OUTPUT/matrix" --public-timeout-seconds 1800
```

Budget: one worker, 8 GiB whole-worker cap, 30-minute whole-run allowance plus wrapper cleanup margin, 1 GiB output allowance; expected two actual calls in roughly 8–15 minutes. No model solver replay is requested. A preflight-only run can add `--check-only` with a separate fresh output path.
