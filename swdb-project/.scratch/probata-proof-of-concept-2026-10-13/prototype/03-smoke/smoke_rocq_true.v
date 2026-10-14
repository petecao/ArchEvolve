(* Ticket 03 smoke check for Rocq (2026-10-14 ET): a tiny true theorem, by induction and by
   the Stdlib's lia. `rocq compile` must accept this file; Print Assumptions must report
   "Closed under the global context" (no axioms). *)
From Stdlib Require Import Lia.

Theorem add_zero_r : forall n : nat, n + 0 = n.
Proof.
  induction n as [| n IH]; simpl.
  - reflexivity.
  - rewrite IH. reflexivity.
Qed.

Theorem bump_gt : forall x : nat, x <= 100 -> x + 1 > x.
Proof. intros x _. lia. Qed.

Print Assumptions add_zero_r.
Print Assumptions bump_gt.
