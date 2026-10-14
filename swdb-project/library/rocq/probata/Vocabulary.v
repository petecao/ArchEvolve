(* Probata Rocq development: closed vocabularies.  Created 2026-10-14 ET (ticket 41).
   Map decisions: 15 items 2 and 5; 16 Later changes (the YAML kinds, the sharing-class
   names and these constructors map one to one; ticket 44 checks that). *)
From Stdlib Require Import List.
Import ListNotations.

(** The five shared-action kinds (15 item 5).  A new kind bumps the method version. *)
Inductive shared_action_kind : Set :=
| Claim          (* write-once CAS: BFS parent, BC depths (bc.cc:106-107) *)
| MinUpdate      (* CAS loop: SSSP dist (sssp.cc:157-167) *)
| AtomicAddOr    (* atomic add or OR: BC path_counts, set_bit_atomic (bc.cc:110-113) *)
| OmpReduction   (* OpenMP reduction: PR error (pr.cc:218) *)
| QueueReserve.  (* fetch_and_add on a queue tail: queue flush (sliding_queue.h:114-118) *)

(** The four sharing classes (15 item 2), one per array per barrier interval. *)
Inductive sharing_class : Set :=
| ReadOnly            (* no thread writes it in the interval *)
| ThreadOwned         (* only the thread that owns an element touches it *)
| SharedActionsOnly   (* changed only through shared actions; reads race by design *)
| LockProtected.      (* touched only inside critical sections *)

Definition all_shared_action_kinds : list shared_action_kind :=
  [Claim; MinUpdate; AtomicAddOr; OmpReduction; QueueReserve].

Definition all_sharing_classes : list sharing_class :=
  [ReadOnly; ThreadOwned; SharedActionsOnly; LockProtected].

(** Sanity: the enumerations are closed and have exactly five and four members. *)
Lemma shared_action_kinds_complete : forall k, In k all_shared_action_kinds.
Proof. destruct k; simpl; tauto. Qed.

Lemma shared_action_kinds_exactly_five :
  length all_shared_action_kinds = 5 /\ NoDup all_shared_action_kinds.
Proof.
  split; [reflexivity|].
  repeat constructor; simpl; intuition discriminate.
Qed.

Lemma sharing_classes_complete : forall c, In c all_sharing_classes.
Proof. destruct c; simpl; tauto. Qed.

Lemma sharing_classes_exactly_four :
  length all_sharing_classes = 4 /\ NoDup all_sharing_classes.
Proof.
  split; [reflexivity|].
  repeat constructor; simpl; intuition discriminate.
Qed.
