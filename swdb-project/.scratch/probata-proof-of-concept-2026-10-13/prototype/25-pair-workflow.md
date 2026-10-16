# Pair-only workflow — 2026-10-15 ET

The public pair fixture now admits initialized local same-type copies and
assignments in the bounded initializedness source protocol. Previously the
valid copy constructor was treated as a scalar constructor argument and refused.
The repair requires checked initialized local pair origins for both assignment
operands and for a copy source. It preserves the original four C model bodies,
contracts and exact-content model pin. Unknown pair pointer inputs and
uninitialized scalar/field writes still refuse. Direct `first`/`second` accesses
remain fields, with no invented model proof dependencies.

Twelve compiler/native/parser-error controls pass; the actual-only test is
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
The profile entry is not a resource guard. It first proves each original
`std_pair_int_int_{ctor_default,ctor,copy_ctor,operator_assign}` body, then proves
the pair-only caller and checks all four dependency IDs/text hashes. Finally it
requires the wrong-field caller to retain an ordinary unknown/timeout obligation
with passing smoke. All six records remain `contract_fixture`; this profile does
not select a new method or close ticket25. The profile's eleven local source pins
are a scoped supplement to the coordinator's full source/runtime manifest.

The default `--mode controls` runs public lowering, native sanitizer checks,
missing-dependency refusal, a genuine changed-policy frozen-translator refusal
and four explicit parser-error stand-ins. Collection
does not probe actual verifier versions. Stand-ins cannot supply proven model
records or satisfy the actual profile. Retain raw output outside the checkout
for record/reference and independent cold auditing before an acceptance claim.

[Preparation evidence](../evidence/t25-pair-preparation-20261015.json).
