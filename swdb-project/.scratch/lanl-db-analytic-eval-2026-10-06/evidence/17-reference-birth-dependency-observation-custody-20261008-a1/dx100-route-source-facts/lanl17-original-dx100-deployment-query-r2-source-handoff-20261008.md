# Passive deployment query R2

Updated: 2026-10-08 ET. Source-only correction; both original and R2 query mains NOT RUN.

The first query incorrectly required PRIMARY directories to inherit BASE's GID. Parent supplied the exact original PRIMARY directory identity: device2097, inode54935911, UID114316761, GID0, directory mode02777. BASE remains the original private0700 directory. R2 adds that five-field literal identity and qualifies GID0 only for canonical owned directories at/below that exact PRIMARY. Before each such route check, PRIMARY must match its fixed identity; normal full root stat witnesses remain checked before/after every Git call and at final publication. Directory SUID/sticky, symlinks, wrongowner, wrongdevice and any redirected PRIMARY still refuse. Existing read() rules for files remain exact, including native/source/target handling. C and non-PRIMARY routes still require BASE's GID. No global group/mode waiver or chmod is added.

Complete byte reversal removes exactly the new PRIMARY_IDENTITY assignment and restores directory's original body. AST comparison finds only directory changed; all other function/class ASTs, imports, limits, main and entrypoint remain byte/AST exact. The new literal is a parent-supplied physical prerequisite, not a target/binding/science observation. No old source/handoff edits, tests, imports, query/main executions, source publication, SSH or project changes were performed.

Retain the original 14,966B/cbf44 source and original3994B/d808 handoff. Use this distinct R2 only after parent full source/argv review. Future parent invocation is native `/usr/bin/python3.12 -B <owned private external R2 source> --expected-primary40 c2d9bb33115dc8f3a95c19afcb268c80f1388e40 --query-source-sha256 <exact R2 SHA below>`; a genuinely delivered descendant may be supplied explicitly instead. Original C/native/source/record/target/retention/hooks checks and finite limits are unchanged. A private exclusive0600 external query file remains required; stdin support was not added. Parent controls physical source publication and actual execution.

- `/private/tmp/lanl17_read_original_dx100_deployment_prerequisites_20261008_a1_r2.py`: 15383 B / SHA `9110d17ab02836bc49161ba28d659087f810784eef794502a6c384d607ec8de2`

- `/private/tmp/lanl17-original-dx100-deployment-query-r2-complete-a1-derivation-20261008.diff`: 1467 B / SHA `9b232ee0c48a175114b5d2e7ae494933e4bd32c61f3ddecb240270b612f26c11`

- `/private/tmp/lanl17-original-dx100-deployment-query-r2-static-source-review-20261008.json`: 1292 B / SHA `f4baa5f276f95a8250b440d32aed1f70132ead2ba30007443289ba11f0116f2a`
