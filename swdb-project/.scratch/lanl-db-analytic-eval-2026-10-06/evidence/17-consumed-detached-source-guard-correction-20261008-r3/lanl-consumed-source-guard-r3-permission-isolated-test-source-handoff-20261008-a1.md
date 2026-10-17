# R3 isolated permission contract fixture — source handoff

2026-10-07 ET / 2026-10-08 UTC. SOURCE ONLY; NOT RUN.

Selected fixture: /private/tmp/lanl_consumed_source_guard_r3_permission_isolated_test_source_20261008.py; 12189 bytes / SHA cda7f3cdc0ca496e85ab6addd90a1a8688f47460cd1732455a3c0623866a47f4. Selected unchanged R3: /private/tmp/lanl_consumed_detached_source_guard_r3_20261008.py; 69303 bytes / SHA 552cd7424138adcf025db119e0a132e0bc70d733d61aaaddda0effe2932c5371. The future fixture reads only this pinned source, parses it, and lifts Refused, require, stamp, inside, tracked_mode_equivalent, and exactly Guard.check_private_root/private_ancestor/privacy_gate/path. The target initializer, main, Git, process, file-read, removal, receipt and other guard methods are neither lifted nor imported. The original selected AST bodies are copied without rewriting. Four pure functions and four permission methods have a closed stdlib/synthetic namespace. Explicit UID424242 replaces production UID114316761 ONLY in that isolated namespace; no production source changes.

Eight distinct unittest bodies check the administrative permission contract: literal owned0700 roots admit existing optional-write modes and record both ancestors;0701/0755 roots refuse even readonly descendants; foreign root/leaf UID refuses; root/ancestor/leaf symlinks refuse; replaced root inode refuses while recorded snapshots stay independent and legitimate root timestamp/nlink observations may advance; data-root siblings/unrelated paths receive no write exception; ordinary special-bit/auth refusals and exact literal PRIMARY02777 exception remain; Git100644/100755 physical equivalence accepts only optional022 after privacy, independently enumerated changed read/execute/owner/special bits refuse. Direct mode-helper tests explicitly distinguish a boolean proof input from path tests that obtain the actual source-derived root proof. No Git blob/source validation is claimed by this isolated fixture.

All path/stat data is in memory. VirtualPath implements a small passive pathlib protocol over a SYNTHETIC metadata table and never reads, creates, chmods, links, removes or resolves any actual filesystem path. Literal production path spelling is retained to exercise the unchanged source comparisons, but it denotes only virtual objects in the fixture. A future reviewed invocation reads the one source pin above; unittest and stdlib imports are fixture infrastructure, with no target module import, entire target compile, target main, Guard initializer, actual plan/raw/source body, proc/Git/SSH/Store/native/provider/scientific/cleanup action. No temp sandbox or actual permission changes are needed.

Preparation performed byte reads, SHA and ast.parse inventory only; no fixture import/lift/compile/test body or main has run. Expected count is exactly eight actual unittest methods, with separately visible subcases; no denominator padding or old six-body R2 binding/journal test is included or repeated. Future ONE finite native local batch and exact interpreter/argv/streams/receipt belong to the parent's review, not this preparation. The R3 target, original R2/NOTRUN history, source reviews and six-body synthetic history remain untouched. No scientific admission, guard read-only clearance, live mode/privacy proof or removal capacity claim follows from source preparation or a future synthetic result.

Test methods:

- test_literal_private_700_admits_existing_write_modes_and_records_roots
- test_701_and_755_private_roots_refuse_even_a_readonly_target
- test_foreign_root_and_foreign_leaf_remain_refused
- test_symlink_root_ancestor_and_leaf_are_never_privacy_proofs
- test_replaced_root_inode_refuses_and_captured_facts_are_independent
- test_private_scope_does_not_cover_data_siblings_or_unrelated_paths
- test_special_bits_auth_denials_and_exact_primary_exception_stay_intact
- test_tracked_git_modes_accept_only_optional_022_with_a_privacy_proof
