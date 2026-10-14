(* Negative check (ticket 41), 2026-10-14 ET.  This file MUST NOT compile.
   It claims that a history read always returns the latest write (sequential consistency):
   after thread 0's CAS stores 5, thread 1's relaxed load must read 5.  Sanity.v proves the
   opposite (stale_history_read_allowed, history_read_not_always_latest), so no proof can
   exist; the build expects "rocq compile" to fail here.  If it ever compiles, the memory
   model has collapsed to SC or a proof step is unsound. *)
From Stdlib Require Import List Arith Lia.
From Probata Require Import Vocabulary Composition Sanity.
Import ListNotations.

Local Arguments Shared {loc val arg}.
Local Arguments HistoryRead {loc val arg}.

Lemma history_read_is_latest_FALSE : forall rf v,
  memory_ok nat nat nat init0 sa_claim
    ([(0, Shared Claim true 5 0 0); (1, HistoryRead 0 v)] : R) rf -> v = 5.
Proof.
  intros rf v [Hr _].
  destruct (Hr 1 1 0 v (or_intror eq_refl)) as [Hsrc Hnew].
  unfold source_ok in Hsrc. destruct (rf 1) as [i|].
  - (* the read takes the CAS at position 0: then v = 5 *)
    destruct Hsrc as [Hi [t [e [He Hw]]]]. assert (i = 0) by lia. subst i.
    unfold at_ in He. simpl in He. inversion He; subst. simpl in Hw. inversion Hw.
    reflexivity.
  - (* the read takes the initial value: v = 0, and nothing orders the CAS before the
       read, so this branch is unprovable; Rocq must reject the file here. *)
    simpl in Hsrc. exact Hsrc.
Qed.
