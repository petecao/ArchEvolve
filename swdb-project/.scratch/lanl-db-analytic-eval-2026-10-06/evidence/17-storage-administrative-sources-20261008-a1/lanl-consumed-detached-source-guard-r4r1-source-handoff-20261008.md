# Exact legacy account service exclusion — source-only R4r1 handoff

Prepared 2026-10-07 ET / 2026-10-08 UTC. No R4 helper, module, main, test, SSH, permission change, removal, worktree action, or Git mutation ran. This is a storage-inspection source derivative, not actual visibility or cleanup admission. Parent owns review and any later invocation.

## Selected preparation and preserved history

- R3: `/private/tmp/lanl_consumed_detached_source_guard_r3_20261008.py`, 69,303 B, SHA `552cd7424138adcf025db119e0a132e0bc70d733d61aaaddda0effe2932c5371`. Exact original remains unchanged.
- Initial R4 NOTRUN draft: `/private/tmp/lanl_consumed_detached_source_guard_r4_20261008.py`, 81,187 B, SHA `e87bdc21532f6c8c945b6c658b2c93f1cd6ae300538d73b979f5a84f45bd260f`. Its after-pair stat anchor preceded the last status/command/cgroup reads. This source-only ordering gap was caught before invocation; draft remains exact.
- Selected R4r1: `/private/tmp/lanl_consumed_detached_source_guard_r4_20261008_r1.py`, 81,694 B, SHA `d30481a540a40f0c4b4695e105dc25f6febf152e391b5a34861b817d0d6960a6`.
- Complete R3→R4r1 diff: `/private/tmp/lanl-consumed-detached-source-guard-r4r1-complete-r3-derivation-20261008.diff`, 14,255 B, SHA `76567dff2762a29e484c18105ada01644aa4e42908d82b8a3a577a271f909ca3`.
- Narrow draft→R4r1 diff: `/private/tmp/lanl-consumed-detached-source-guard-r4r1-final-identity-interval-derivation-20261008.diff`, 1,101 B, SHA `bd77d86f400ee2f37400ce74f1843f0e725cf04cafb01a540cbc8e005b0fe4bc`. One final stat/start/PPID check for child and parent closes the interval after all final public/original-file reads.
- Original complete R3→draft diff: `/private/tmp/lanl-consumed-detached-source-guard-r4-complete-r3-derivation-20261008.diff`, 13,738 B, SHA `b2f6b028c0debaf97ea7c6046a29e2bb37421589fc1fa8a0fc8701c101fa8725`.
- Original UNSEALED source preparation: `/private/tmp/lanl-consumed-detached-source-guard-r4r1-source-preparation-20261008.json`, 3,167 B, SHA `157883589f4987953507552ebad885704d26ce56842fd9bec602266cb5abae75`. It reports source reads/creation, AST syntax/structure comparison and literal reversal only, not runtime tests.

All preexisting definitions except `Guard.process_references`, all original imports/assignments/constants, 18 rows, 22 original receipts, limits, configured coverage, reviewed configuration normalization, removal/journal/publication functions and scientific source remain exact. One new global helper is added. Draft→R4r1 literal reversal restores the exact draft; the draft's closed literal insertions reverse to exact R3. No older preparation text was rewritten.

## One reusable predicate, no permission-exception plugin

`exact_account_pam_service_identification(identification_pin, parent_review_identity_sha256, check_deadline, charge_bytes)` occupies selected lines 98–275. Its exact source span is 11,151 B / SHA `f6c4076013eaa487c0e810ba4329512657bef9b1b74a0c074a7231bcc0466883`; structural AST SHA `f2a22d26ad7092633ab99b9d0134585800b01a1d6690f19d6af6e27c11aa7d90`.

The helper depends only on existing `P`, `BASE`, `UID`, `LIMITS`, `require`, `sha`, `strict_json`, `stamp`, and imported `os`, `re`, `stat`. It calls no Guard constructor, plan/removal method, Git action, process kill, or selected main. Reusers must copy/use this exact helper and dependencies under an independently checked source pin, bind the ordinary original identification pin to their genuine reviewed configuration, and provide their own existing finite deadline/read-byte accounting callbacks. No fake R3 plan, table monkeypatch, alternative service PID, or general unreadable-process waiver is supported. Callback use does not enlarge any existing inspection/scientific cap.

In R4's real Guard path, `account_service_identification_pin` is a required ordinary file-pin field. The existing unchanged parent reviewed-configuration digest covers this field, including every configured byte. `self.pin_fact` enrolls it in the original stable inventory; the helper independently checks returned bytes/stat again. The existing parent review is verified before process inspection. The helper's review-ID argument records this inherited caller binding; it does not independently verify an external parent review document.

## Exact inputs and current checks

The original identification file is fixed to `/data1/yanruj/lanl-account-pam-service-identification-20261008-a1/identification.json`, 3,818 B / SHA `ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa`. Local byte-exact original `/private/tmp/lanl-exact-account-pam-service-original-identification-20261008-a1.json` has the same pin. Its original format is `swdb.exact-account-pam-service-original-identification.v1`, `sealed:false`, with no identity seal. The source does not reseal or normalize it. It checks the exact original format and explicit retained no-clearance/parent-semantic-boundary fields.

Fixed live predicate:

- Child PID 359656 / start 40749693 / PPID 359655 / Name `(sd-pam)`, all four UID and GID values 114316761, sleeping state S, one thread, zero tracer and pending/shared-pending signal masks.
- Parent PID 359655 / start 40749691 / PPID 1 / Name `systemd`, the same exact four UID/GID values.
- Both: CapInh/CapPrm/CapEff/CapAmb numeric zero. CapBnd is exactly `000001ffffffffff`; it is deliberately not required zero.
- Child command 9 B / `971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370`; parent command 49 B / `a4eb13854c1664d48464c575a8c86538e8a379ecd5e1e40ab6c56b61b9b9ffb5`. Both cgroup bytes 70 / `f6b0978005408a4cbf4759816cf4703b0e097284eabe55f01f1cea870640e455`.
- Boot epoch 1785498067 / SC_CLK_TCK 100. These are current read checks, not mtime-derived creation claims.
- Parent executable link exactly `/usr/lib/systemd/systemd`; root-owned single-link regular mode0755 native file 100,816 B / `b472aadf808bef87c0eb203056a77cb64bd268b71b756306013a53de68a94173`.
- Root-owned single-link regular mode0755 `/usr/lib/systemd/systemd-executor`, 137,792 B / `b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044`, with the `(sd-pam)` literal. Both native full stable-content stat tuples must equal their exact original identification-file pins.

Public status/stat/command/cgroup identity is checked before and after native-file reads. Final child/parent stat/start/PPID checks follow the final original-file read. Current native/original files use O_NOFOLLOW, FD and pathname returned-byte/stat agreement, one-link/type/ownership, root-native mode and exact byte/SHA checks. Atime is excluded by the existing stable-content tuple. Original private BASE ancestry is checked and fixed through the call. Reads are bounded and charged to the caller; no protected child link/FD/map/configuration/environment/PAM body is read. SigBlk is reported as observed and excluded from the equality/predicate: temporary signal-wait unblocking is not interpreted as failure or proof of an unrelated role.

## Honest exclusion and inherited meaning

Only PID359656 gets the `excluded_exact_system_service` role after the current helper checks. The parent and every service descendant retain the ordinary consumer path. All other owned, explicitly identified or owned-descendant consumers still require readable reference checks; inaccessible ones refuse. Missing/changed actual service identity/native/original bytes fail closed. No broad root/sudo/security gate or reference substitute is introduced.

The audit explicitly marks child `fd`, `cwd`, `root`, `exe`, `maps`, `syscall`, and meaningful wait channel `UNOBSERVED`; `reference_free_claimed:false` and global privileged visibility/clearance false. Checking the native executor file does not observe the child executable mapping. That relationship is an inherited trusted OS-role interpretation.

The actual parent review must substantively bind the original public probe, the trusted systemd v255.4 PAM lifecycle and Linux v6.8 signal-wait citations, and accepted original fresh-creation custodies showing this long-lived service precedes E and the exact selected source checkouts. Neither source preparation nor file mtimes establish that chronology or physical-reference freedom. The accepted original identification document contains original E prereg/export receipt pins `70a8a1a4…` and `02b369f0…`; full selected-checkout custody semantics remain the parent's original receipt/source review boundary.

The method returns the exact exclusion audit separately from its count of ordinary consumers. The prior overbroad `inaccessible_relevant_owned_or_identified_consumer_refuses` wording is replaced by `inaccessible_ordinary_owned_or_identified_consumer_refuses`; it is not left asserting universal visibility. Initial/latest full audit and bounded per-call classification witnesses are retained in eventual administrative facts. No actual R4 inspection, source-row eligibility, all-process visibility, cleanup success, recovered bytes, capacity admission, or scientific admission is claimed by this preparation.
