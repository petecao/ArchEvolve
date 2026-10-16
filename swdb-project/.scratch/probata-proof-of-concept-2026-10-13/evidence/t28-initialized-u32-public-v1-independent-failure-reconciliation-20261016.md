# Independent settled initialized-u32 V1 failure reconciliation

**V1 is FAILED.** The single selected JUnit case has one assertion failure, zero errors and zero skips. The failure is the unspaced frame-substring assertion at `tests/test_dx100_initialized_register.py:20`; no workflow-success claim is warranted.

The public route had already persisted `proof.contract.dx100_initialized_register_partial_fixture.v1.20261016t152357z.84353b9a` with `not_proven/tool_crash`, its partial-summary subject and the named stand-in marker. The retained handler says the named Frama stand-in exited99. Its five report pins match, and all75 artifact-manifest pin instances match. Record tool/prover labels are method metadata, not evidence that those real tools ran.

The actual generated caller clause is `assigns REG_count , SPD_count , region_count , __swdb_dx_reg_words [ 0 .. 1 ] ;`. Its lexical frame entries are exactly the four expected locations; whitespace differs from the failed substring. This supports a narrow token-aware test correction. It is not a source/body or frame-soundness theorem. The test’s later assertions did not execute; passive reading separately finds `terminates \false` and all three expected source-definition kinds.

The root outer receipt reports exit1,33.508933709s and2,837,250,048 bytes peak RSS, without timeout or OOM. c6 reports exit1,33.373200542s,2,691.8125MiB, no inspection events/failure and no unconfirmed children. Entry source-before/after13 rows are identical; root records complete source/runtime unchanged and three finite empty selected-tool/no-denial sweeps with all three leases absent. These are retained settlement observations; this reviewer did not rerun live process checks. Total root raw at its receipt was29,376,873 bytes.

V1 raw, records and receipts remain unchanged. No actual compiler/native/formal/SSH/test rerun or project import occurred during reconciliation. No actual formal, native caller, body, hardware/current0.2 or ticket acceptance follows. A separately reviewed test-only successor and independently admitted fresh workflow would be new evidence; it cannot relabel this failure.
