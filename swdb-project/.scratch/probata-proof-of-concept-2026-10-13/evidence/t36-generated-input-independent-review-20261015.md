# Ticket 36 generated-input prelaunch control review

Updated: 2026-10-15 ET. Read-only inspection of the current test diff and retained GREEN command/log/resources. No test, compiler, Frama-C, solver, provider or remote job was invoked by this reviewer.

**PASS — the targeted acceptance coverage gap is closed.** Test source SHA-256 is `f54cdb21c41ea56265ed58b4b4f29101faeb96d9278f5572359a75d42188923b`. Production source is unchanged. The public `swdb prove --adapter wp` control uses the production adapter and setup policy. Its external reader-compiler stand-in mutates the already copied `wp_input.c` from `return n;` to `return n + 1;` during report-reader compilation, before the adapter's final `check_generated`. The test requires the exact `[input_hash]` rule and generated-input mismatch diagnostic, confirms compilation and retained mutation markers, verifies changed bytes, and requires both no verifier marker and no proof YAML. It therefore exercises the real final prelaunch byte comparison rather than a caller-supplied wrong initial manifest.

The exact selected command explicitly sets parent `SWDB_FRAMA_C=none`. `wp_setup.prove` supplies only the isolated Python `frama.py` and `ocamlfind.py` external stand-ins; the former returns a version or exits on non-WP checks, and the final mismatch stops before its WP marker. Why3's fixture prover commands are `/usr/bin/false`. This command reaches real clang AST/lowering work but no installed Frama-C/WP/solver. Its passing synthetic admission control establishes no theorem.

Retained GREEN log: one pass in 2.80 s. Resource receipt: exit0, wall3.427696 s, peak198,541,312 bytes, no timeout/OOM. The earlier admitted attempt had already reached the expected refusal but then attempted to read intentionally cleaned scratch; retaining the mutation text fixes the test's evidence access without changing production behavior. The earlier sandbox watchdog `sysctl` permission failure is excluded from acceptance. Neither earlier result is overwritten or described as passing.

No remaining blocker in this targeted control. Ticket-level disposition still awaits setup129 terminal closure and the final evidence crosswalk.
