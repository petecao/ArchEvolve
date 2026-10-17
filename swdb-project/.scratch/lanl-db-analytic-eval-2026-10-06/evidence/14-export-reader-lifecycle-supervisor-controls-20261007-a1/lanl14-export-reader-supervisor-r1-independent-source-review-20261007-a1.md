# Ticket 14 supervisor R1 — final independent source review

2026-10-07 ET. Full selected R1 source, narrow diff, complete fa703 derivation, original full handoff, R1 handoff and preparation JSON read. Source bytes were hashed; removing only R1 line 126 through a read-only comparison reproduces every draft8cad byte (`cmp` exit 0). No control import, main, fixture, test, SSH, staging, Git mutation or scientific action occurred. Original f339 and draft fb5b review notes remain unchanged.

**No concrete source blocker found in selected R1.** Line 126 requires `action == context.action` before the cap, source check, launch and receipt. This closes the draft's internal API/fixture mislabelling finding; main's existing matching action path is preserved.

The full lifecycle remains covered: lines 142–147 install handlers and enable the subreaper before the selected child starts a new session; lines 156–167 run returned-leader group cleanup and original 31e descendant/adopted-orphan cleanup on every handled child exit, including early internal Git failure. The second cleanup still runs if the first raises. Survivors, cleanup errors and immutable-byte failures prevent success. Lines 149/164/168/172 preserve a returned child7 as nonzero child/supervisor status, rather than inventing success.

The two fixed 928/690 production modes, explicit native Python/SHA/cwd, C185/F6 and original 31e/bcc9 byte checks, fresh owned 0700 output and exclusive 0600 private originals, bounded compact lifecycle receipt, and absence of a CLI fixture switch are unchanged. Receipt canonical policy remains explicitly **False**; private full `cleanup.json` remains an original **unsealed** snapshot with byte pin. No full argv/environment/auth or original stdout/stderr body is returned; stream bodies are not hashed by this supervisor. Scientific admission is explicitly false.

The handoff correctly distinguishes child waits 18000/14400 from prospective GNU outer deadlines 18120/14520 and KILL60. Cleanup waits nominally total 40 seconds plus source/proc/I/O work; no total runtime guarantee exists. Actual native/cwd/argv/private paths, parent disjointness from opaque child raw/checkout arguments, current release/capacity facts and any Linux early-exit cleanup proof remain future inputs/gates. Unchanged 928 still resolves its nested validator through original `python3`; no broader interpreter guarantee is inferred. Failures before launch or during receipt I/O/SIGKILL can lack a lifecycle receipt, as the handoff explicitly states.

## Selected packet pins

| File suffix under `/private/tmp/` | Bytes | SHA-256 |
|---|---:|---|
| `lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py` | 14547 | `503fc5defcf96a5177599185a9895c00ae64b3e1b0058128b9e283ef3bd39f3f` |
| `lanl14-export-reader-supervisor-r1-narrow-derivation-20261007-a1.diff` | 831 | `f33ed921c184b62adb4419ad16ccecedf9cca40ee94e5584b09cfa71b5299edb` |
| `lanl14-export-reader-supervisor-r1-complete-fa703-derivation-20261007-a1.diff` | 18782 | `29d705206ea8528322c8c63cf7c0f7ceca6ef740fe4c0576978618015a3910eb` |
| `lanl14-export-reader-supervisor-source-handoff-20261007-a1.md` | 10141 | `851cb20caf706e991f293eaa547a0297ad9402eba7df09ad40d7315fed6a27b3` |
| `lanl14-export-reader-supervisor-r1-source-handoff-20261007-a1.md` | 2634 | `e4f4cc2f25944f1477acb6d859c53fc968e9f12368af8bebcdbab83bcf1579d0` |
| `lanl14-export-reader-supervisor-r1-source-preparation-20261007-a1.json` | 2619 | `7281a635d40255ebeed8949d0c83dade3ee3f53e9713359326580d34d66f5e0a` |

The original preparation declares canonical **True** and seal `bd94b3bf80ed101bf9196e3abb70a8ea7eb170f266cf14d3107aafe33844a505`; its NOTRUN flags remain historical source-preparation facts. This source acceptance does not assert a Linux fixture result or actual export/reader admission.
