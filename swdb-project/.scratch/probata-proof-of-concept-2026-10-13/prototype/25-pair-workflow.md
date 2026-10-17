# Pair-only workflow — 2026-10-15 ET

Updated: 2026-10-16 ET (scoped actual body and caller acceptance).

The public pair fixture now admits initialized local same-type copies and
assignments in the bounded initializedness source protocol. Previously the
valid copy constructor was treated as a scalar constructor argument and refused.
The repair requires checked initialized local pair origins for both assignment
operands and for a copy source. It preserves the original four C model bodies,
contracts and exact-content model pin. Unknown pair pointer inputs and
uninitialized scalar/field writes still refuse. Direct `first`/`second` accesses
remain fields, with no invented model proof dependencies.

Thirteen compiler/native/parser-error controls pass; the actual-only test is
skipped. ASan/UBSan C/C++ runs agree on 75 defined cases covering default values,
independent copied values, field writes and self-assignment. The wrong-field
negative has the defined witness `x=2,y=5`: the required result is 11 and its
result is 17. This finite agreement is not a formal C++ equivalence theorem.

The executable prospective actual profile is:

```sh
python scripts/probata_pair_profile.py --mode actual-wp --output OUTSIDE_CHECKOUT
```

The coordinator must supply fresh exact-source/tool admission, a single worker,
the external 8 GiB RSS/time watchdog and the actual adapter's verifier lease.
The entry supplies a prospective wall deadline; each actual call receives the
remaining budget minus 15 seconds of setup/record-writing headroom. The CLI
timeout also uses the remaining budget, and late whole-profile completion fails.
The profile entry is not a resource guard. All six records must retain the
fixture method identity, fixture evidence kind and the explicit 8 GiB job cap.
Its output must be outside the entire source checkout, including the monorepo
root and all descendants. It first proves each original
`std_pair_int_int_{ctor_default,ctor,copy_ctor,operator_assign}` body, then proves
the pair-only caller and checks all four dependency IDs/text hashes. Finally it
requires the wrong-field caller to retain an ordinary unknown/timeout obligation
with passing smoke. All six records remain `contract_fixture`; this profile does
not select a new method or close ticket25. The profile's eleven local source pins
are a scoped supplement to the coordinator's full source/runtime manifest.

The default `--mode controls` runs public lowering, native sanitizer checks,
missing-dependency refusal, a genuine changed-policy frozen-translator refusal
four explicit parser-error stand-ins, and full-checkout output refusal before
creation. Five existing vector initializedness controls also pass. Collection
does not probe actual verifier versions. Stand-ins cannot supply proven model
records or satisfy the actual profile. Retain raw output outside the checkout
for record/reference and independent cold auditing before an acceptance claim.

[Preparation evidence](../evidence/t25-pair-preparation-20261015.json).

## Scoped actual acceptance — 2026-10-16 ET

Frozen `1278f2d9` passed the six-record actual profile on mbit10. The four
original int/int pair bodies prove 31 ordinary and four smoke goals. The safe
pair caller proves 24 ordinary and nine smoke goals while pinning those four
exact current model proof records. The wrong-field caller retains one ordinary
ensures timeout, with 23 other ordinary goals Valid and all nine smoke goals
passing. Its verdict remains `not_proven`, not a refutation.

The read-only cold audit matches all six strict report-reader outcomes and
dependencies, 2,023 physical-file references across 1,005 unique hashed files,
198 source modules and eleven profile source pins. Records bind the retained
Linux project runtime/composite rather than the historical Mac composite.
Both guards exit 0 without OOM or timeout; the outer guard uses 284.70 seconds
and peaks at 784,863,232 bytes. Source stays clean and unchanged, and the lane
naturally releases. All six records remain fixture evidence. Ticket 25 remains
open for its wider standard-model and integration criteria.

[Actual audit](../evidence/probata-t25-pair-actual-audit-20261016.md),
[summary and exact record IDs](../evidence/probata-t25-pair-actual-summary-20261016.json),
[complete compact cold metadata](../evidence/probata-t25-pair-cold-audit-v3-1278f2d9-20261016.json).
