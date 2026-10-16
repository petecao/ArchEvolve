# Mixed integer/pointer pair workflow

Created: 2026-10-16 ET. Preparation only; no compiler, native, WP or CBMC run yet.

The fixture keeps both pointees local and compares pointer identity without
reading through either pointer. Default, value, copy and assignment calls use
the original four `std_pair_int_int_ptr_*` models. The scalar contract is
`assigns \nothing; ensures \result == x+3;`, with the existing bounded scalar
legality clause. Mutating the original value or copied pointer must not change
the earlier assigned pair. The false identity branch has a defined counterexample
for every legal input; bounded refutation must replay on the original C++.

The public controls cover 75 C11/C++17 sanitizer agreement cases, unknown pointer
input refusal, current model dependency refusal, and four explicit parser-error
stand-ins. They cannot provide a proven model record. The gated actual profile
requires four original model-body records, a safe caller with exact current
model record pins, a wrong caller retaining an ordinary WP unknown/timeout with
passing smokes, and CBMC safe/refuted records with native agreement/C++ replay.
All eight records remain `contract_fixture`; pointer provenance beyond these
fresh source locals, float/NaN semantics and other pair types remain unverified.

`probata_pair_pointer_profile.py` is a prospective profile, not a resource guard.
Root must supply exact published source/runtime admission, explicit actual WP
lineup, fresh external raw storage, one worker, and an 8 GiB/time guard before
executing controls or the actual test. Both modes refuse output inside the full
checkout. Complete actual outcomes and independent cold audit are still pending.
