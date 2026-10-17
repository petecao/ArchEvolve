# P1 normal stop, release and after custody

Updated: 2026-10-08 15:02 ET.

**p1 attempt1 stopped normally at plateau after four completed iterations, eight candidate rows and nine completed provider calls. Original stop, release32 and B08 AFTER custody succeeded. Final strict scientific audit and pair admission remain pending.** No stopped state was resumed. p2–p4 remain queued at this checkpoint.

| Original | Bytes | SHA256 |
|---|---:|---|
| Stopped receipt | 1355 | `6868ce197cf840f3a4d1869f8f92c0c70ef7208c8599bade0642c9d215be1a7b` |
| Native lane | 1085 | `e3096fa6b2f1c0ca0335f242f6d7614ae7048c43c5012e5ed33b15120bee46d4` |
| Release32 | 9431 | `c6ed81b5c820637a2ae4284a5d3b116a28c36c054f3ef71eacc803b06c1f04be` |
| B08 AFTER | 35637 | `aed96b7d00fed15d9f69a7eb609cc194cafd62964c95c95a401840708963a47a` |
| P2 BEFORE | 3148 | `766efc494edb201820d503b58c4666a16d88e96d525256698cc6d21da9bdb4f7` |

Root verified original canonical True seals and BEFORE/dispatch/stop/release/AFTER links. Public/runner/wrapper/lane exit codes are all integer zero, no infrastructure error, source clean and no owned survivors. Native R2 observations before32, beforeAFTER and afterAFTER confirm released node0 generation511, no matching kernel lock and absent daemon/FD9. Node0 was reserved through the last check. Actual stopped state/ledger is projected in AFTER; original state and raw output remain remote. Advisory monitor14:49 confirms the matching plateau summary. Eligible flags and paired receipts observed are zero; final report is still required.

Native10510/00c269 socket_lane.sh emits whole-second UTC at line91. Its original lane end18:48:28Z and helper stop end18:48:28.810375+00:00 occupy the same second. ReaderR1 and authorR3 had an overly precise extra comparison. Narrow readerR2 (7926B/6ecee4f1) and finalizerR4 (18684B/5f74373d) require canonical native whole-second format, preserve strict stop start<end, allow only stop end<lane end+1 second, and require native observation after both exact original ends. Originals are never rewritten. Root and independent source reviews passed. Frozen producer32/B08/auditor already use exact stop≤release≤AFTER and need no correction. ReaderR2 and authorR4 actually ran successfully; original release32 and B08 returned zero.

Fresh14:59 ET host observation: all socket/legacy leases released; PRIMARY and its origin/R source remain `5e12a9796432654d88def24ecea617d16ca605b2`; source clean, protected retention lock preserved. P2 BEFORE state absent, no provider directories. MemAvailable125551067136B; /data1 free23213293568B; /data39732342784B; load1.07 and GPU idle. Single-lane floors pass, concurrent44GiB floor does not. Existing Quicksilver activity is preserved; choose serial node0 only after independent p1 custody review. These observations are dated evidence, not a future lease reservation.

The bounded local decoder initially looked for a nonexistent stdout.original, then read the actual stdout without any remote rerun. Its p2 check initially assumed the absent-state mapping had no null fields; the original includes file:null/projection:null. Checking present=False corrected the local assertion without rewriting or recollecting originals. All captures were successful and byte-preserved.

`original-inventory.json` records exact paths, sizes and hashes. This archive is unsealed administrative preservation, not final trajectory admission or D30 acceptance. Scientific source/policy/budgets/full catalogs and original before/dispatch remain unchanged. Ticket17 stays claimed; all final acceptance boxes stay unchecked. Finalize/report/audit/full Standards+Spec review and ticket/Git synchronization remain required.

Independent actual custody review passed at15:01 ET, including all original canonical True seals, seven release inputs, linked AFTER, nine completed counted calls and native-before/after g511 checks. This is interim reuse readiness, not final scientific audit. Later-campaign private generatorR1/c424 also passed root and independent source review; actual future dispatch/lane pins are required.
