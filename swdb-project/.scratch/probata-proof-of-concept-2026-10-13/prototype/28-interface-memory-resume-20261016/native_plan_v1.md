# INERT memory53 Mac native profile — 2026-10-16 ET

**NOT EXECUTED. Root source/runtime/resource admission is required.**

1. One compatible whole-tree guard must enforce **180 seconds / 4 GiB**, one worker,
   with token/tag, shared slot and independent process/inspection cleanup. The entry
   uses a 165-second internal budget. Output must be fresh beneath
   `/private/tmp/probata-resume-20261016-t28-memory53-native-v1`; preserve failures
   and inspection receipts and stop at the first failure. There is no retry.
2. Reuse the exact public-V3 augmented 7,605-file runtime policy, hash
   `4171556ed48f8612eb364a88741831a3bfc9259d34c25750e8717dadeab408a1`.
   `native_source_policy_v1.json` additionally binds 14 source/preparation files
   and three physical LLVM22 ASan/UBSan inputs. Entry, policies and all declared
   inputs are rehashed before/after. Loader/system linker/dynamic-membership TCB
   remains open; matching physical pins alone does not close it.
3. Exact LLVM22 Clang preprocesses the original immutable harness once in C11 and
   once in C++17 with the sanitizer/language flags, `-MD -MF` dependency output and
   separate complete stdout/stderr. **First dependency hashes are collected AFTER
   preprocessing**, then rechecked after capture and compile. This cannot prove
   which bytes the preprocessor read before capture or exclude a concurrent
   change-and-restoration. That timing boundary is explicit TCB. Frozen `.i`/`.ii`
   files are pinned, then compiled with the same language/sanitizer flags and
   explicit preprocessed-language modes. Original C/headers are never edited.
4. Each binary must exit0, emit exactly the expected JSON for **53 preparation
   controls**, and produce empty stderr. ASan/UBSan halt on errors; unsupported
   Mac leak checking is disabled, and symbolization is disabled to avoid a separate
   symbolizer child. These controls supply no actual memory effect/history/value,
   original source caller, public proof, hardware or cross-host timing result.
5. The child environment is closed; entry/child bytecode prefixes must remain
   absent. The 50-GiB free floor plus 256-MiB allowance stays in force. Output is
   postchecked at 128 MiB between stages and 256 MiB including final receipts;
   these are postchecks, not a filesystem quota. Raw data, frozen input, used
   dependency pins, binaries, complete command arrays and logs stay in the fresh
   host raw folder. Root owns final admission and retained-evidence review.

`native_command_v1.json` records inert entry argv and exact source/entry/policy
pins. Root must supply its freshly admitted guard; dispatching its inner argv
alone does not provide the required whole-tree resource or cleanup guarantees.
No actual proof/body/pair/current0.2/full-ticket28 acceptance is established.
