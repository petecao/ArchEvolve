# Ticket 14 supervisor R1 — context/action custody binding

2026-10-07 ET. Source-only revision after parent full reading of draft8cad and complete e2d9 derivation. No target import, main, test, fixture, SSH, staging, Git operation, native application, cleanup, exporter or reader invocation occurred. No harness has been prepared.

Selected proposed source: `/private/tmp/lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py`, 14,547 bytes, SHA-256 `503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f`.

The **only** source change is the explicit internal API assertion immediately after the admitted-action assertion:

```python
require(action==context.action,'selected context/action identity differs')
```

Main already passed the same action through load_context and supervise. This assertion prevents an internal/fixture caller from checking one context's selected source bytes but publishing the other action's selected-source identity. Removing this one exact line reproduces every original draft byte. No code, cleanup, status, private file, administrative cap or scientific scope changes accompany it.

| Exact derivation | Bytes | SHA-256 |
| --- | ---: | --- |
| `/private/tmp/lanl14-export-reader-supervisor-r1-narrow-derivation-20261007-a1.diff` | 831 | `f33ed921c184b62adb4419ad16ccecedf9cca40ee94e5584b09cfa71b5299edb` |
| `/private/tmp/lanl14-export-reader-supervisor-r1-complete-fa703-derivation-20261007-a1.diff` | 18782 | `29d705206ea8528322c8c63cf7c0f7ceca6ef740fe4c0576978618015a3910eb` |

Draft8cad, its original complete e2d9 diff, full handoff851c and preparation True4d71 remain exact, separate preparation history. The original full handoff documents all inherited sources, deliberate changes, required future actual native/argv/cwd/output facts and limitations. For any future reviewed invocation replace only the supervisor source path and `--supervisor-sha256` with this R1 path/hash; all production mode/source/tail/cap/cleanup/C/F6/one-GNU semantics are unchanged. No actual executable/path/argv/cwd/environment is supplied here.

The parent proposes one future meaningful Linux lifecycle smoke of early exit7, owned same-group and escaped-session descendants, and unrelated sibling survival. This derivative has no actual proof; an internal fixture receipt would be labelled `fixture:true` and scientific admission remains false. Production cap values stay exporter18000 and reader14400; outer administrative deadlines remain child allowance+120, KILL60. Source review does not prove any duration or actual cleanup. No harness or additional test case has been constructed.
