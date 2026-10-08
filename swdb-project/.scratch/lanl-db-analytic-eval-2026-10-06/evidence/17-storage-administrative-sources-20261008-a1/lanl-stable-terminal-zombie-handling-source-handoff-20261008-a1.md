# Stable terminal zombie handling — R4r2 / observer R3

Prepared 2026-10-08 UTC. SOURCE ONLY, NOTRUN. Parent requested a narrow correction after its original public-role probe recorded two owned terminal zombies whose FD directories were inaccessible. No guard/observer definition or module was compiled, imported, lifted or called; no main/test/SSH/process control/Git/worktree/source staging/cleanup occurred. Only bounded official-source HTTPS research, local original reads, source construction, AST parsing/comparison and complete-diff reversal were performed. All originals remain byte-exact.

## Complete packet and reversible scope

- R4r2: `/private/tmp/lanl_consumed_detached_source_guard_r4_20261008_r2.py`, 84,381 bytes / SHA `78a0c850e515f6ebb589a28f53a2c99d7a6430dcf5da46aea4869368d2cd3df9`.
- Complete R4r1→R4r2 diff: `/private/tmp/lanl-consumed-detached-source-guard-r4r2-complete-r4r1-derivation-20261008.diff`, 4,355 bytes / SHA `f4aa5938a824141e5502409cc6dc5e0f9b29f07f92826681ffb9c66c72504ce2`.
- Observer R3: `/private/tmp/lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r3.py`, 54,009 bytes / SHA `5a52e36ea84122cd303c540d6c177d014e36d22c70b2d9cdcd210d863e177cc8`.
- Complete observer R2→R3 diff: `/private/tmp/lanl17-passive-consumed-source-metadata-acquisition-r3-complete-r2-derivation-20261008.diff`, 5,077 bytes / SHA `f51286ef5d8f53ab400148981defe7e3c82e4639c0db256358fc432c522571e9`.
- Original UNSEALED preparation: `/private/tmp/lanl-stable-terminal-zombie-handling-source-preparation-20261008-a1.json`, 4,640 bytes / SHA `f542a862fb0445de20c2b9d8bb43289d7df3059f34424c3b41b5cca19636fde9`.

Closed reversal of each whole diff restores original R4r1 81,694 bytes / SHA `d30481a540a40f0c4b4695e105dc25f6febf152e391b5a34861b817d0d6960a6` and original observer R2 51,132 bytes / SHA `c85df7ccad501a3e1cc5ea01d0e4da1c36c031db48f4af9e32d9e278bb585572`, respectively. Only `Guard.process_references` and `Observer.owned_processes` differ in their own files. No definition is added. All other definitions, top-level imports/assignments/constants/tables/limits, plan/review digest policies, main/error/removal behavior are unchanged. The shared exact-account service helper remains exactly 11,151 bytes / SHA `f6c4076013eaa487c0e810ba4329512657bef9b1b74a0c074a7231bcc0466883` in both variants. Its separate qualified legacy-service exception is not broadened.

## Exact Linux 6.8 source basis

The web tool was used first; exact v6.8 GitHub/raw pages returned DisabledError and the official mirror was inaccessible. A successful search surfaced current master, which was not used as version-specific evidence. Five exact `torvalds/linux/v6.8` raw HTTPS sources were then read with TLS, a 30-second per-file limit and 1 MiB per-file transport cap. The local byte snapshots are research sources, not executed modules or target observations. URL/size/SHA pins are included in the unsealed preparation.

In the versioned `do_exit` implementation, `exit_mm`, `exit_files` and `exit_fs` precede `exit_notify`; the latter assigns `EXIT_ZOMBIE`. `exit_mm` clears the exiting task's `mm`. This establishes an inference about that task's pointer slots, not a global absence of references. A leader may reach this exit state while other threads remain, so the new handling additionally requires one reported thread. [Linux v6.8 exit ordering, lines 858–891](https://github.com/torvalds/linux/blob/v6.8/kernel/exit.c#L858-L891), [zombie publication and thread-group condition, lines 729–757](https://github.com/torvalds/linux/blob/v6.8/kernel/exit.c#L729-L757), [exit_mm, lines 538–575](https://github.com/torvalds/linux/blob/v6.8/kernel/exit.c#L538-L575).

`exit_files` clears `tsk->files` before dropping its file-table reference. Shared references owned by other tasks can remain. [Linux v6.8 fs/file.c, lines 456–466](https://github.com/torvalds/linux/blob/v6.8/fs/file.c#L456-L466).

`exit_fs` clears `tsk->fs`; the shared filesystem object is released only when its users are gone. [Linux v6.8 fs/fs_struct.c, lines 95–110](https://github.com/torvalds/linux/blob/v6.8/fs/fs_struct.c#L95-L110).

Proc status uses the common task-state mapping, including the zombie label; proc stat obtains its state through that same mapping. Public Threads is reported from the thread-group count. [Linux v6.8 proc state mapping, lines 126–145](https://github.com/torvalds/linux/blob/v6.8/fs/proc/array.c#L126-L145), [status state, lines 181–182](https://github.com/torvalds/linux/blob/v6.8/fs/proc/array.c#L181-L182), [stat state, lines 488–490](https://github.com/torvalds/linux/blob/v6.8/fs/proc/array.c#L488-L490), [Threads, lines 268–291](https://github.com/torvalds/linux/blob/v6.8/fs/proc/array.c#L268-L291).

The shared state index combines task and exit state, and the character mapping includes Z. [Linux v6.8 sched.h, lines 1570–1607](https://github.com/torvalds/linux/blob/v6.8/include/linux/sched.h#L1570-L1607).

This preparation does not independently establish the running host's kernel release, patch set or unmodified implementation. The reviewed Linux 6.8 terminal mm/files/fs invariant is an explicit OS assumption. No new parent review/seal, historical fact, global visibility or cleanup clearance is manufactured from it.

## New branch and audit

The source change is restricted to stable terminal zombies in the existing relevant-process scope. It requires captured public status state exactly Z and captured Threads exactly 1; a fresh before-stat state Z with the captured PPID; fresh public status state Z, the same PID/PPID and four UID values, and Threads 1; then a fresh after-stat still Z with the same PID start ticks and PPID. Missing/reaped/reused/changed identity, duplicate fresh status fields, live/non-Z state or more than one thread fails the terminal branch. It does not substitute a permissive exception for an unreadable live process.

R4r2 replaces its inherited requirement to read a zombie's maps and list its FDs. Observer R3 adds this branch before the unchanged ordinary live reference checks and records Threads in its existing public snapshot. Both return separate `stable_single_thread_terminal_zombie_audits` containing only PID/start/PPID/UID/state/thread counters and the original fresh public-status size/SHA. FD/cwd/root/exe/maps remain explicitly UNOBSERVED, the kernel invariant is labeled an assumption, and other-thread/live-consumer exemptions and global-reference-free/cleanup-clearance claims are false. The exact-account service call order and all non-zombie checks remain unchanged.

Every additional public status/stat read uses the original bounded `proc_read` and cumulative byte counter. Per-proc read 16 MiB, cumulative 16 GiB, deadlines/process/FD/output limits and source/lease/raw/Git preservation policies are unchanged. Observer audit bytes use the existing compact-output charge. No new CLI, supplier, wrapper, selection, kill/reap or permission repair is introduced.

## Original observation and remaining actual gates

The existing original `/private/tmp/lanl-inaccessible-owned-process-public-role-original-20261008-a1.json` is UNSEALED and unchanged. It recorded PID2128956/bash and PID3570805/qs as stable public Z/Threads1 identities; those are historical motivating facts, not values hardcoded into a blanket exception or a new original observation. Its exact file pin is retained in the unsealed preparation.

Parent E2's inherited zombie skip is unchanged. The live SSH transport and any other inaccessible relevant live consumer still cause refusal. No actual E/default inspection, observer acquisition, R4 plan/main/removal, finalR selection, capacity or scientific agreement is established here. Parent owns full source review, actual runtime/native/kernel assumptions, any later explicit input plan and actual action. Original R4r1, observer R2, semantic review and all past NOTRUN/runtime policies remain intact.
