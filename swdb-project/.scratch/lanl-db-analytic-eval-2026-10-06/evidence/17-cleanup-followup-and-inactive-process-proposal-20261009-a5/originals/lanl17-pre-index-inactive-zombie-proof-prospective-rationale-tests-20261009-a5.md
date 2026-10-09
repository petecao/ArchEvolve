Prepared 2026-10-09 02:03 ET (2026-10-09T06:03:10.287520+00:00). SOURCE-ONLY proposal; UNSELECTED / NOTRUN.

Original observer36052 B/SHA be2f68c21a72b4de5deee05f17f48a8cd09342cf3a6e7e17280ff72414dc3fd4 remains immutable. The user's specific prohibition on immutable R5 changes and UID/state exceptions takes precedence over broad project approval. An explicit user override is required before selecting a replacement, followed by independent source review, adversarial tests and fresh payload/config approval. No target source/control/import/test/remote execution or guard modification occurred.

Actual01:19/01:38 ET diagnostics bind account-owned process directories to stable zombie bash2299635/start600551347 and qs3570805/start499874091 with root-owned stat/status leaves. R5 currently refuses these leaves before state parsing. The alternative changes only inactive_owned_identity: anchored numeric account-owned directory; regular root-or-account stat/status/cmdline leaves read through O_NOFOLLOW fd-relative descriptors; bounded reads and allnine stat fields on open/read/reread; truly empty cmdline before/after; statZ/X and positive stable startticks; exact statusPid/Tgid/PPid/state agreement; allfour statusUIDs equal the account. Compare complete stat/status bytes and leaf pins on reread. Permission failure, disappearance, reused PID, malformed/ambiguous metadata or nonterminal state becomes unknown through the unchanged caller. NUL-only/nonempty cmdline refuses; no PID/name exceptions. Return schema unchanged.

Matching-consumer, native-lock/daemon, exact self/parent, sourceR/F6, completion, ownership, floors and scientific paths remain exact. kernel_bytes is unchanged. RecoveryR6 is untouched; sleeping PAM is not accepted. Capacity and all other guards remain independently mandatory. No historical proof, no-use, cleanup/index or scientific approval is fabricated.

Static checks performed: exact original size/SHA; derived AST parse; only inactive_owned_identity differs; allother 34 functions/classes AST-identical. Prospective full source computed IN MEMORY ONLY: 38606 B/SHA 711e4c7f99365c879f872781813a868e2a0365b8b6ee4d407f6747a6bca690f2; no duplicate full source saved. Patch 4460 B/SHA 70c287dd7e599682f4a444ccba933048f6dea6eda2eb6985ef5009ec16487d95. These checks are not behavioral test proof.

Targeted adversarial verification plan (NOTRUN; required before selection):

| Fixture/fault | Required outcome |
|---|---|
| Stable owned directory, root-owned regular leaves, four accountUIDs, canonicalZ, empty cmdline | Same compact inactive identity; no name/PID dependency |
| Account-owned leaves or canonicalX | Accepted with identical guards |
| S/R/D/T, fabricated empty cmdline, NUL-only/nonempty cmdline, status/stat state mismatch | Unknown; never clearance |
| Any of fourUIDs differs; wrongPid/Tgid/PPid; missing/duplicate/nonnumeric identity; truncated/oversize status/stat | Unknown |
| ProcdirUID/inode/start changes beforeopen/between/after; each ofnine directory/leaf fields changes; status/stat bytes change | Unknown including samePID reuse |
| Leaf symlink/foreignowner/wrongtype; EACCES/missingPID/leaf; read/close failure; deadline | Unknown, no fallback/chmod/sudo |
| Emptycmdline changes on reread or malformedcanonicalState | Unknown |
| Caller integration: matching consumer present, nativeheld, capacityfail, changedsource or incompletecompletion | Existing corresponding gate still blocks |
| Exception during each read; output privacy | Descriptors close; no rawstat/status/comm/argv/auth/provider output |

Use an isolated deterministic fd/stat/read fault harness rather than live /proc mutation. Tests must exercise the original caller's unknown propagation and exact unchanged guards, not merely mirror parsing. After explicit override only, separately authorize bounded exact-process validation and a fresh complete no-use/native/source/floor observation; no mock result supplies host clearance.

Primary sources: [kernel proc documentation](https://docs.kernel.org/filesystems/proc.html) defines status identity/state data; [proc_pid_status(5)](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html) defines four UID ordering, Pid/Tgid and Z/X; [proc_pid(5)](https://man7.org/linux/man-pages/man5/proc_pid.5.html) documents root ownership of nondumpable process entries. These support the ownership interpretation, not future PID inactivity. Retained original source inference802d8f2a plus addendum and actual diagnosticsc9397a69/fa753745 remain unchanged.
