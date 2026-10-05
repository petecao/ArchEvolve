# Certification evaluator files

Created: 2026-10-05 ET (code-review fix F11; agent-decided under Yan-Ru's delegation, revisable).

These folders hold the trusted C++ that `swdb certify` compiles beside a candidate: evaluator
preludes, record writers, seams with their library faults, evaluator-owned drivers (`main`), and the
certification evaluator process of certify 1.5 and later. None of it is a library entry, and none of
it ever ships to a provider workspace. Which files each certify command version reads, with its frozen
digest, is the version table in `swdb/certification_procedures.py`; the records list the same files
in `command.sources`.

## Layout

| Folder | Command family and versions | Files |
|---|---|---|
| `library/dx100/certification/` | candidate 1.3 (ticket 70) | `candidate_prelude.hpp`, `record.cc`, `seams.cc` (one object per fault), `bfs_driver.inc`, `bc_driver.inc` |
| `library/dx100/certification/v1_4/` | candidate 1.4 (ticket 76); `record.cc`, `seams.cc` and `prelude.hpp` also run in 1.5 and 1.6 | `prelude.hpp`, `record.cc`, `seams.cc` (every fault, chosen by the run plan), `bfs_driver.inc`, `bc_driver.inc` |
| `library/dx100/certification/v1_5/` | candidate 1.5 and 1.6 (ticket 78); its shared core also serves native 1.5 and library-operation 1.2 | `evaluator.cc`, `evaluator_core.inc`, `evaluator_context.hpp`, `client.cc`, `client_core.inc`, `client/MAA_functional.hpp`, `arena.hpp`, `prelude.hpp`, `bfs_driver.inc`, `bc_driver.inc` |
| `library/native/certification/` | native 1.3 (ticket 75) | `candidate_prelude.hpp`, `record.cc`, `seams.cc` |
| `library/native/certification/v1_4/` | native 1.4; also the evaluator side of native 1.5 | `prelude.hpp`, `record.cc`, `seams.cc` |
| `library/native/certification/v1_5/` | native 1.5 | `evaluator.cc`, `client.cc` (both include the dx100 `v1_5` cores) |
| `library/library_operations/certification/v1_1/` | library operation 1.1 (ticket 77); `record.cc` also in 1.2 | `record.cc`, `driver.cc` |
| `library/library_operations/certification/v1_2/` | library operation 1.2 (ticket 78) | `evaluator.cc`, `runner.cc`, `call.hpp` (includes the dx100 `v1_5/arena.hpp` of this checkout) |

The strict layer (`library/dx100/strict/`) and the canonical lowering header
(`library/dx100/dxc_lowering.hpp`) are read by every candidate version.

## Pinned files

Some of these files are pinned by sha256 and must never change:

- `library/profiles/native_bfs_tdstep.yaml` pins the native 1.3 and 1.4 files and the two BFS drivers
  `dx100/certification/bfs_driver.inc` and `dx100/certification/v1_4/bfs_driver.inc` (keys `harness`
  and `harness_v14`, a legacy name for these evaluator files); the native contract pins the profile.
- The other files are not pinned by any entry, profile or certificate. The candidate 1.3 and 1.4 ones
  are frozen by `tests/test_certification_procedures.py` (a change needs a new version), and every
  version's files by its frozen manifest digest.

## Why the shared 1.5 code stays under `dx100/`

The `v1_5` arena, client and evaluator cores serve DX100, native-CPU and library-operation runs, so
a neutral folder would describe them better. They stay here: moving them would change the compile
command lines and source manifests of the frozen versions candidate 1.5, native 1.5 and
library-operation 1.2, which would then need new version labels for no behavior change. A future
version that changes these files can move them.

## Retiring old versions

Candidate 1.3 (the DX100 path) and library-operation 1.0 and 1.1 are still runnable so that earlier
records can be repeated exactly. From 2026-10-05 every new record carries the git commit it ran
(`command.code`), so a version can be retired once nothing needs to repeat a record made without
that field; ticket 78 records this.
