# Exact portal fusermount3 lifecycle: source research and proposed predicate

2026-10-08 ET. Source-only research; no implementation, selected-control import/main/test, SSH, FUSE/native program invocation, signals, mount changes, privilege changes, project writes, plan, semantic review seal, or cleanup clearance. Local writes comprise this note and parent-authorized passive HTTPS source downloads in /private/tmp. The original diagnostic and public identity receipts remain UNSEALED and unchanged. Oa4 remains a failed observation with no owned-process coverage/admission.

The fresh evidence supports identifying one existing document-portal auto-unmount helper. It does not prove its protected references empty. In particular, the installed libfuse release does **not** close all inherited descriptors before waiting. A narrowly reviewed deployment/lifecycle predicate can use exact public identity, installed source correspondence and genuine creation chronology; it must preserve that limitation and continue ordinary checks on the portal parent and every other live process.

## Inputs actually inspected

All temporary paths below are under /private/tmp. Each SHA is a file SHA, not a newly asserted receipt identity.

| Original | Bytes | SHA256 |
| --- | ---: | --- |
| lanl17-owned-process-field-access-diagnostic-original-20261008-a1.json | 22407 | d2d2b3c92f44f7665631a66a29f359ec37d3f5e9b46079874cabbeae1ad40068 |
| lanl17-fuse-service-public-identity-original-20261008-a1.json | 4103 | 1ea76b7519827bae6f81902c2bebd6b16e22c303fcada24257bf1bab73174489 |
| lanl-exact-account-pam-service-original-identification-20261008-a1.json | 3818 | ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa |
| lanl_consumed_detached_source_guard_r5_20261008_a1.py | 88872 | a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb |
| lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r6.py | 58750 | 488fb42df44d338204b5cff58b10e7f0ff9c7feaee6490b33ba94201ba4f7665 |

G5 process_references(), lines 803–965, and O6 owned_processes(), lines 597–709, treat any of the four UID fields matching 114316761 as owned, and also include owned descendants. Root proc ownership/effective UID does not exclude this helper. Explicit privileged-consumer identification in G5 adds evidence/checks; it is not an exemption. The exact PAM PID359656 and stable single-thread terminal-Z branches are separate and unchanged. Both ordinary live-process paths refuse inaccessible relevant references. Current fusermount refusal follows these policies; there is no existing fusermount branch.

The 06:49:16Z public original binds child PID1654291/start559081545/PPID1654279, State S/one thread, UIDs [114316761,0,0,0], GIDs all114316761, and exact five-element public role argv. The argv byte pin is 100 B / 65b3170da324600f477de2acde6ae5f47d348a3a72e74d4b47d2612ec19f9999. The option string is rw,nosuid,nodev,fsname=portal,auto_unmount,subtype=portal; the sole mount target is /run/user/114316761/doc. Protected cwd/root/exe/fd/maps/syscall/wait_channel remain UNOBSERVED.

Parent PID1654279/start559081538 has all four UIDs114316761, seven threads and /usr/libexec/xdg-document-portal as its observed executable route. Parent command bytes are 33 B / 407a0c7b9049543c6ad5bf73e3e7fbf431fec8908926f894aed0aa6e2d75903f. Its mountinfo contains one exact route: mount51, dev0:48, root /, target /run/user/114316761/doc, fuse.portal, source portal, rw,nosuid,nodev,relatime and super options rw,user_id=114316761,group_id=114316761. This is a parent-namespace observation, not an observation of the protected child's namespace.

Installed package metadata reports fuse3/libfuse3-3 3.14.0-5build1 and xdg-desktop-portal 1.18.4-1ubuntu2.24.04.3. The original native pins are /usr/bin/fusermount3 **39296** B / d278775c1528dd32efc85c2cb322423ee93aa8dcf76aaa595f7022d427910704, root-owned mode4755, and /usr/libexec/xdg-document-portal 195560 B / 44dd7e1eb2df2a4de1d8c1189a3fee4451539ffab5db6ba4d21718c6d43af3dc, root-owned mode0755. The earlier compact message's 339296 was a typo; no original pin changed.

## Release-specific primary-source result

Official fuse-3.14.0 util/fusermount.c, lines1354–1395, sends the FUSE device FD to its parent, closes that device FD, calls setsid(), changes cwd to /, blocks signals, then loops on recv(cfd). EOF/error leaves the loop and checks/unmounts the original mount target. There is no all-inherited-FD closing sweep in this release. The filesystem-UID drop/restore functions at80–94 explain why the helper can retain privileged effective/saved/fs UIDs. These source facts support a long-lived mount-lifecycle role, not a claim that all its inaccessible fields are harmless. [Exact upstream helper source](https://raw.githubusercontent.com/libfuse/libfuse/fuse-3.14.0/util/fusermount.c).

Official fuse-3.14.0 lib/mount.c, lines308–379, makes a UNIX socketpair, forks the helper, closes the other socket endpoint in the child, clears CLOEXEC on the control endpoint and executes fusermount3. With auto_unmount, the parent leaves its endpoint open instead of waiting for helper exit. Unrelated inherited non-CLOEXEC descriptors are not swept here either. [Exact upstream library source](https://raw.githubusercontent.com/libfuse/libfuse/fuse-3.14.0/lib/mount.c).

Official portal1.18.4 document-portal-fuse.c, lines3298–3340, selects subtype=portal,fsname=portal,auto_unmount and mounts the session. Lines3470–3474 construct the mountpoint from the user's runtime directory plus doc. This fits the actual fixed argv and parent mount route. It does not prove that the portal has no live document or checkout references. [Exact upstream portal source](https://raw.githubusercontent.com/flatpak/xdg-desktop-portal/1.18.4/document-portal/document-portal-fuse.c).

The Ubuntu 3.14.0-5build1 .dsc SHA256 entries match both downloaded archives. The orig tar's helper and library files are byte-identical to the official tag downloads. All four quilt patches were read; they affect include/fuse_kernel.h, example/poll_client.c, lib/helper.c and lib/fuse.c, leaving both lifecycle files unchanged. The portal orig file likewise matches its official release, and no patch in the exact Ubuntu portal series changes document-portal/document-portal-fuse.c. These are HTTPS/package-source correspondences; PGP signatures were retained but not cryptographically verified, and no compiled-binary equivalence or protected running-image observation is claimed. [Ubuntu fuse source descriptor](https://archive.ubuntu.com/ubuntu/pool/main/f/fuse3/fuse3_3.14.0-5build1.dsc), [Ubuntu portal source descriptor](https://archive.ubuntu.com/ubuntu/pool/main/x/xdg-desktop-portal/xdg-desktop-portal_1.18.4-1ubuntu2.24.04.3.dsc).

Today's official Doxygen helper source has close_inherited_fds(cfd) in its waiting path. That newer behavior must not be substituted for this installed release. [Current helper source, for the version distinction only](https://libfuse.github.io/doxygen/fusermount_8c_source.html).

## Proposed exact predicate, pending parent deployment review

This is an acceptance recipe for one role classification, not implemented code or an actual acceptance. All conjuncts must hold; missing relevant evidence refuses.

1. Bind the two unchanged original public receipts by exact returned-byte SHA/size and their original UNSEALED policies. A future parent semantic review must separately name the source/tag/package/archive/native pins and this exact child's role. No original success/exclusion/coverage flags are invented. Preserve noncircular plan/review binding and every other existing G/O gate.
2. Recheck only PID1654291 with start559081545, PPID1654279, all four UID/GID fields, public name, live S state and one thread, plus the exact 100-byte cmdline pin and five-element role argv above. Bind parent1654279/start559081538/all-user UIDs, exact command pin and observed executable route. Before/after anchors must follow the last evidence/native/mount read, with PID/start/PPID/UID unchanged. Session/group and public blocked-signal metadata can corroborate the waiting path if captured; none is currently asserted from this original. No argv/environment/authentication expansion is needed.
3. Recheck canonical nonsymlink root-owned native files, their original mode/size/SHA and full stable stat. Parent public executable linkage and installed package metadata must remain exact. Classification explicitly trusts the installed native package/deployment and this same running helper's correspondence to its release source; protected child exe/maps are still UNOBSERVED. Native SHA plus package metadata is not a formal proof of the running image. No generic name-only, root-owned-process, daemon or service exception follows.
4. Recheck the exact parent mount record, including mount/device/root/source/type/user/group/options, and physically protect that mount route and its ancestors from aliasing into selected consumed roots/R14/current17 source/raw/control routes. Child mount namespace remains UNOBSERVED. A disjoint mountpoint alone does not establish the document portal's exported documents or handles are unrelated. Keep the portal parent and all other owned/descendant processes on ordinary strict reference checks; do not classify them through this child predicate.
5. The inherited-descriptor premise needs genuine creation custody. The earlier original boot_epoch1785498067 and CLK_TCK100 imply helper birth2026-10-04T04:41:22.450Z and parent birth2026-10-04T04:41:22.380Z. These are calculations from original pins, not a fresh boot query. Before use, rebind current boot/clock/PID identity and compare helper birth against each actually selected checkout's original absent-before/fresh-create custody, physical route/object identity and retained receipt pins. Names, filesystem mtime/ctime, or a later export timestamp alone are insufficient. No selected subset or exact creation predicates are supplied here. Under the explicit deployment/lifecycle assumption, the helper could not have inherited handles to objects genuinely created after its birth; the waiting loop adds no selected-root path opens. That is a selected-object argument, not a claim its inherited FDs are empty. After socket termination, the source dereferences its fixed mount target; the exact protected route must remain disjoint.
6. Audit classification as this one auto-unmount mount-lifecycle child, recording each protected field UNOBSERVED, possible inherited descriptors retained, source/package/lifecycle assumptions, parent reference checks still required, no global reference-free/visibility/cleanup/capacity/scientific claim. No descendant/other fusermount/SSH process inherits this classification. Public identity, native/package, source correspondence, mount route or actual birth-versus-creation mismatch refuses. Missing/inaccessible ordinary relevant process fields continue to refuse. Retain existing finite byte/process/time accounting for every original/native/public/mount read and final recheck; no cap is relaxed.

Remaining actual premises are a parent review of the explicit installed-package/running-lifecycle assumptions, current interval-bound public/native/mount facts, and selected-row genuine creation evidence. The research supplies neither those attestations nor an implementation/removal plan. No kill, unmount, protected-reference probe, sudo or privilege repair is proposed.

## Passive research download pins

These sources were obtained after web-tool tag/archive fetch failures using the parent's expressly authorized read-only network downloads. Files below remain local research material; no new control or supplier was created.

| Local basename | Bytes | SHA256 |
| --- | ---: | --- |
| lanl-libfuse-official-tag-3.14.0-fusermount-research-20261008.c | 32829 | 173c7b6b74ed3f69e96f01b7b4ce2495d76fdbbc51c3fb9f5f8f96a9e79d2201 |
| lanl-libfuse-official-tag-3.14.0-mount-research-20261008.c | 13454 | ab794cc4c5dcf0044a06c9cf07c62d64d52523097b745a5cf978ec6e48f2d317 |
| lanl-portal-official-1.18.4-fuse-research-20261008.c | 97130 | aff36d56cc496e449047ad17d024139812b7160ef6d8f1e5b3eb22fbb5b76730 |
| lanl-ubuntu-fuse3-3.14.0-5build1-source-research-20261008.dsc | 2517 | d96c0cf5b45b7e58ee09b6f561173f12c70945331d337d038ed0aec31a502d92 |
| lanl-ubuntu-fuse3-3.14.0-orig-research-20261008.tar.xz | 4351852 | 96115b2a8ff34bd1e0c7b00c5dfd8297571d7e165042b94498c9a26356a9a70a |
| lanl-ubuntu-fuse3-3.14.0-5build1-debian-research-20261008.tar.xz | 17976 | 9d1ca42ee3d8d0b8f8ce84f1d032632a20c0a1ef9e1d8837fbcc9e10301fe318 |
| lanl-ubuntu-portal-1.18.4-1ubuntu2.24.04.3-source-research-20261008.dsc | 3343 | 4e30107a2658217129bcb0db8d88bab9a8f07b4c5339c7b7852b709f13eb7049 |
| lanl-ubuntu-portal-1.18.4-orig-research-20261008.tar.xz | 699380 | b858aa1e74e80c862790dbb912906e6eab8b1e4db9339cd759473af62b461e65 |
| lanl-ubuntu-portal-1.18.4-1ubuntu2.24.04.3-debian-research-20261008.tar.xz | 34352 | 9a646551b1be31a3a839cc11ecb1ace8eaa849a28aae377874b5a1dd97e48175 |
