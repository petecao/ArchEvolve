(* Ticket 03 smoke check for Rocq (2026-10-14 ET): a false theorem, the analog of map 07's
   seeded bug (y != 42 fails at x = 41). `rocq compile` must reject this file: lia cannot
   prove it, and Qed must not accept an unfinished proof. *)
From Stdlib Require Import Lia.

Theorem bump_not_42 : forall x : nat, x <= 100 -> x + 1 <> 42.
Proof. intros x _. lia. Qed.
