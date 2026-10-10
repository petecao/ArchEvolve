# 10 — The estimation role fills unknowns

Created: 2026-10-06
Updated: 2026-10-06 ET
**Type:** slice
**Status:** resolved
**Blocked by:** 09
**Spec:** `../spec.md`
**Time estimate:** 4–6 h

**What to build:** A new agent role in the provider launcher, with strict input and output schemas. Input: the characterization, the profile and the target description's unknown entries. Output: a value and a reason per unknown, with basis `estimated`, which becomes a new target-description version (D19). Estimates that depend on a filled value list it and show how much the result moves if it is halved or doubled.

## Acceptance

- [x] Tests use a stub provider.
- [x] A value for an already-known parameter is rejected.
- [x] The role's workspace holds no timings, evaluator code or other candidates.
- [x] Provider pins and audit are the same as for the other roles.

## Answer

Resolved: 2026-10-06 ET. The public `fill-target-parameters` command freezes one
new target-description version from the exact three sanitized inputs. Closed
input/output contracts reject known overrides, wrong units/domains, duplicate or
missing answers, unrecognized numeric contexts and structural service-transfer
gaps before launch. The role uses the existing provider pins, guard/audit, read-only
workspace and login/process cleanup. Successful all-null outputs also freeze the
base ID/version; historical records and observation policy remain immutable.

The final source `a7a9b9e` passed 27 public role cases; earlier vertical slices and
source/receipt evidence are in [portable proof](../evidence/10-portable-proof-20261006.json)
and [structural compatibility proof](../evidence/10-compatibility-proof-20261006.json).
The [reference](../../../docs/reference/estimation-role.md) documents the command,
three-file limit, output rules, structural refusals and complete-trial sensitivity.

| Actual attempt | Result |
|---|---|
| a1 | Login configuration lost by lane environment; no inference or new record |
| a2 | Guarded Codex inference completed once; original runner's wrapper/native equality assertion then failed |
| a2 postfill a1 | Independently verified both executable identities; fresh leased protocol/estimate/validation passed, without repeating inference |

The [actual compact receipt](../evidence/10-estimation-role-mbit10-20261006-a2-postfill-a1.json)
is sealed as `61528624…`; [original a2 custody](../evidence/10-estimation-role-postfill-custody-mbit10-20261006-a2.json)
retains exit 1/error verbatim, and [a1 failure](../evidence/10-estimation-role-failed-mbit10-20261006-a1.json)
remains separate. The postfill acceptance `69b79681…` passed at 2026-10-06 22:55 ET
with 620 records valid. Only three new canonical records and compact metadata
were exported; prompt/provider streams, authentication and raw IR stay remote.

Seven numerical assumptions are `estimated`; floating-point throughput and setup
seconds per event remain `unknown`. Known facts, input/source/count identities,
policy and controls are unchanged. Whole-call seconds, ratio, error band, all five
trial totals and the seven half/base/double sensitivity impacts/ranks remain null
because structural host-memory/runtime/composition coverage is incomplete. No
accuracy, CPU error-band or hardware/gem5 agreement is claimed.

After merging integration `97ca4df`, eight affected public paths passed. The
functional copied zero-work fixture reached RED because it removed the count but
kept its new sealed target/protocol dependencies; pruning that copied dependency
closure reached GREEN (1 passed, 61.08 s). All canonical records remain intact:
631 valid, all 628 prior YAML files and 876 protected record/library/application
blobs byte-preserved, exactly three canonical additions. The
[integrated closeout proof](../evidence/10-integrated-closeout-proof-20261006.json)
records source/bundle identities and preservation. Historical actual bundle
`b238c61b…` stays frozen; later implementation `e3216982…` requires a fresh protocol
for new execution. Other ticket states and native observer/source/count bytes
are preserved.


2026-10-07 ET retention note: [Three original ignored generated inputs](../evidence/10-ignored-generated-input-retention-20261007/README.md) are retained byte for byte with the original unsealed five-file inventory. Their three plan input hashes and 101,164-byte total match the earlier archived preparation; no preparation/provider/native/test execution or scientific acceptance was repeated. Existing resolved status and actual evaluation history remain unchanged.
