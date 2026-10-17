# Prospective g17 input registration

Updated: 2026-10-06 20:25 ET. Ticket 11 prerequisite; ticket09 custody is unchanged.

The new typed `records/inputs/kron-g17-k16.yaml` admits `-g 17 -k 16` to both
registered native baseline adapters. It preserves the GAPBS source family and
fixed seed 27491095 from `apps/gapbs/src/util.h`, including block reseeding, ID
permutation and trial SourcePicker behavior. Source-file hashes and the original
g16 file hash are recorded in [the public proof](11-prospective-g17-input-proof.json).
Only the selected generator scale changes; realized vertices/edges/density remain
null, with unknown basis. No g17 graph, timing or application outcome was collected.

The public RED rejected the missing input for both baseline adapters. After
registration, both progressed through actual source/input/ROI preparation and
stopped at an intentionally unavailable LLVM toolchain, before output-directory
creation or application execution. The final six-case integrated gate passed in
106.63 seconds; canonical validation accepted 614 records. Public `view` retains
unknown counts/metrics because no profile exists. Normal/exceptional command
composition and actual OpenMP bounded views remain green on the merged source.

[The exact g16/g17 T1 commands](11-object-scopes-counting-runbook.md) use five
trials, explicit `--object-scopes`, unchanged v2 normalization, fresh IDs and the
verified Linux libomp path. Four complete command argument lists passed parser
checks with help-only execution. Parent combines the separately owned primitive
semantics, syncs clean source and dispatches actual counts. The runtime/object
headers remain byte-identical to tested implementation 8bbb890.

The stable 09 count-policy foundation 9cd07a8 and latest integration 31898b6 were
consumed before the final gate. The schema merge retained both additive contracts.
The command fixture builder is shared from `testkit.analytic`; there is no duplicate
helper or test-module import. All preexisting record bytes, the g16 registration
and other ticket issue/map bytes remain unchanged.
