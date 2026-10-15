(* t42 harness (2026-10-14 ET): one file, one Rocq job.  Part 1: the elaborated statement of
   every approved definition and of the theorem (Set Printing All), compared with the output
   for ticket 41's approved files.  Part 2: Rocq's own assumption listing for the theorem. *)
From Probata Require Import Vocabulary Composition.
Set Printing All.
Print Vocabulary.shared_action_kind.
Print Vocabulary.sharing_class.
Print Vocabulary.all_shared_action_kinds.
Print Vocabulary.all_sharing_classes.
Print Composition.event.
Print Composition.run.
Print Composition.at_.
Print Composition.proj.
Print Composition.program_trace.
Print Composition.program_run.
Print Composition.complete.
Print Composition.is_barrier.
Print Composition.interval.
Print Composition.in_crit.
Print Composition.inside.
Print Composition.owned.
Print Composition.loc_of.
Print Composition.written.
Print Composition.read_value.
Print Composition.is_shared.
Print Composition.device_cmd.
Print Composition.writes.
Print Composition.omp_sync.
Print Composition.cpu_sync.
Print Composition.hb_cpu.
Print Composition.sync.
Print Composition.hb.
Print Composition.rf_map.
Print Composition.source_ok.
Print Composition.not_older.
Print Composition.seen.
Print Composition.read_ok.
Print Composition.latest.
Print Composition.memory_ok.
Print Composition.count_iter.
Print Composition.omp_ok.
Print Composition.device_ok.
Print Composition.model_run.
Print Composition.fits_event.
Print Composition.fits.
Print Composition.all_fit.
Print Composition.obl_class_fit.
Print Composition.obl_owned_disjoint.
Print Composition.critical_block.
Print Composition.implements_shared_action.
Print Composition.obl_atomic_blocks.
Print Composition.iters.
Print Composition.obl_chunk_cover.
Print Composition.is_sync_point.
Print Composition.obl_uniform_control.
Print Composition.obl_team_size.
Print Composition.conflicts.
Print Composition.covered_between.
Print Composition.crosses_sync.
Print Composition.reads_loc.
Print Composition.dead_after.
Print Composition.quiet_ok.
Print Composition.obl_dx100_quiet.
Print Composition.intervals_contiguous.
Print Composition.critical_sections_contiguous.
Print Composition.reads_latest.
Print Composition.final_is.
Print Composition.iterations_once.
Print Composition.serial_outcome.
Check @Composition.parallel_composition.
Unset Printing All.
Print Assumptions Composition.parallel_composition.
