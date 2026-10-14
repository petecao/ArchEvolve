(* Probata Rocq development: sanity lemmas on the statement's definitions.
   Created 2026-10-14 ET (ticket 41); revised 2026-10-14 ET with the statements.
   Not part of the reviewed statement.  Each lemma is proven (Qed) and uses no axiom;
   "Print Assumptions" below shows it. *)
From Stdlib Require Import List Arith Lia Relations.
From Probata Require Import Vocabulary Composition Reduction.
Import ListNotations.

Local Arguments Write {loc val arg}.
Local Arguments Read {loc val arg}.
Local Arguments HistoryRead {loc val arg}.
Local Arguments Shared {loc val arg}.

(** * Composition: the memory model is the history read, not sequential consistency *)
Definition R := Composition.run nat nat nat.
Definition init0 : nat -> nat := fun _ => 0.
(* a claim: CAS from 0 to a; a failed CAS stores nothing *)
Definition sa_claim : shared_action_kind -> nat -> nat -> option nat :=
  fun _ a v => if Nat.eqb v 0 then Some a else None.
Definition all_shared : nat -> nat -> sharing_class := fun _ _ => SharedActionsOnly.

Lemma sync_lt : forall (X : R) i j, cpu_sync nat nat nat X i j -> i < j.
Proof. intros X i j H. destruct H; assumption. Qed.

Lemma hb_lt : forall (X : R) i j, hb_cpu nat nat nat X i j -> i < j.
Proof.
  intros X i j H. induction H as [i j H|i k j _ IH1 _ IH2].
  - apply sync_lt in H. exact H.
  - lia.
Qed.

Lemma hb_first : forall (X : R) i j,
  hb_cpu nat nat nat X i j -> exists k, cpu_sync nat nat nat X i k /\ k <= j.
Proof.
  intros X i j H. induction H as [i j H|i k j H1 IH1 H2 _].
  - exists j. split; [assumption | lia].
  - destruct IH1 as [m [Hs Hm]]. exists m. split; [assumption|].
    apply hb_lt in H2. lia.
Qed.

(* 1. Inside the admitted program class, a history read may return a stale value: thread 0
      claims location 0 (an SC CAS), thread 1's relaxed load still reads the initial 0,
      because nothing orders the CAS before the load.  Both threads fit SharedActionsOnly. *)
Definition X_stale : R := [(0, Shared Claim true 5 0 0); (1, HistoryRead 0 0)].

Lemma stale_run_fits : forall t,
  fits nat nat nat nat (fun l => l) all_shared X_stale t.
Proof.
  intros t i e l H Hl. unfold at_ in H.
  destruct i as [|[|i]]; simpl in H; [| |destruct i; discriminate];
    inversion H; subst; simpl in Hl; inversion Hl; subst; unfold fits_event, inside; simpl.
  - split; [reflexivity | discriminate].
  - right; right; right. split; [reflexivity | discriminate].
Qed.

Lemma stale_history_read_allowed :
  memory_ok nat nat nat init0 sa_claim X_stale (fun _ => None).
Proof.
  split.
  - intros j t l v Hj.
    destruct Hj as [Hj|Hj]; unfold at_ in Hj;
      destruct j as [|[|j]]; simpl in Hj; try discriminate;
      try (destruct j; discriminate).
    inversion Hj; subst. split; [reflexivity|].
    intros i [[w [t' [e [He Hw]]]] Hseen]. unfold at_ in He.
    destruct i as [|[|i]]; simpl in He; try (destruct i; discriminate).
    + destruct Hseen as [Hhb | [r [t1 [e1 [e2 [v1 [s [Hr [H1 [H2 _]]]]]]]]]].
      * apply hb_first in Hhb. destruct Hhb as [k [Hs Hk]].
        assert (Hk0 : 0 < k) by (apply sync_lt in Hs; exact Hs).
        assert (k = 1) by lia. subst k.
        destruct Hs as [t0 e0 e0' Hlt H0 H1 | t0 t0' k0 a l0 v0 k' a' l' v' Hlt H0 H1].
        -- unfold at_ in *; simpl in *. inversion H0; subst. inversion H1.
        -- unfold at_ in *; simpl in *. inversion H1.
      * assert (r = 0) by lia. subst r. unfold at_ in *. simpl in *.
        inversion H1; subst. inversion H2.
    + inversion He; subst. discriminate.
  - intros j t k f a l old Hj. unfold at_ in Hj.
    destruct j as [|[|j]]; simpl in Hj; try discriminate; [|destruct j; discriminate].
    inversion Hj; subst. split; [reflexivity|]. intros i v Hi. lia.
Qed.

(* 1b. So "a history read returns the latest write" is false (the claim negative/ makes). *)
Lemma history_read_not_always_latest :
  ~ (forall rf v, memory_ok nat nat nat init0 sa_claim
                    ([(0, Shared Claim true 5 0 0); (1, HistoryRead 0 v)] : R) rf -> v = 5).
Proof.
  intros H. specialize (H (fun _ => None) 0 stale_history_read_allowed). discriminate.
Qed.

(* 2. A plain read after the thread's own write returns that write. *)
Definition X_own (v : nat) : R := [(0, Write 0 1); (0, Read 0 v)].
Lemma read_own_write : forall rf v,
  memory_ok nat nat nat init0 sa_claim (X_own v) rf -> v = 1.
Proof.
  intros rf v [Hr _].
  destruct (Hr 1 0 0 v (or_introl eq_refl)) as [Hsrc Hnew].
  assert (Hs : seen nat nat nat sa_claim (hb_cpu nat nat nat (X_own v)) (X_own v) rf 1 0 0).
  { split.
    - exists 1, 0, (Write 0 1). split; reflexivity.
    - left. apply t_step. apply (cpu_po nat nat nat (X_own v) 0 1 0 (Write 0 1) (Read 0 v));
        [lia | reflexivity | reflexivity]. }
  specialize (Hnew 0 Hs). unfold not_older, source_ok in *.
  destruct (rf 1) as [i|]; [|contradiction].
  destruct Hsrc as [Hi [t [e [He Hw]]]].
  assert (i = 0) by lia. subst i.
  unfold at_ in He. simpl in He. inversion He; subst. simpl in Hw. inversion Hw. reflexivity.
Qed.

(* 3. Must-prove control (15 item 12): read, failed CAS, re-read sees the winner's value.
      Thread 1 claims location 0 with 5; thread 0's CAS (to 7) then fails and stores
      nothing; its re-read returns 5, never the stale 0. *)
Definition X_cas (old v : nat) : R :=
  [(1, Shared Claim true 5 0 0); (0, Shared Claim true 7 0 old); (0, HistoryRead 0 v)].
Lemma failed_cas_reread_sees_winner : forall rf old v,
  memory_ok nat nat nat init0 sa_claim (X_cas old v) rf -> v = 5.
Proof.
  intros rf old v [Hr Hs].
  destruct (Hs 1 0 Claim true 7 0 old eq_refl) as [Hsrc1 Hlat1].
  assert (Hold : old = 5).
  { unfold latest, source_ok in *. destruct (rf 1) as [i|].
    - destruct Hsrc1 as [Hi [t [e [He Hw]]]]. assert (i = 0) by lia. subst i.
      unfold at_ in He. simpl in He. inversion He; subst. simpl in Hw. inversion Hw.
      reflexivity.
    - exfalso. apply (Hlat1 0 5); [lia|]. exists 1, (Shared Claim true 5 0 0).
      split; reflexivity. }
  subst old.
  destruct (Hr 2 0 0 v (or_intror eq_refl)) as [Hsrc Hnew].
  assert (Hseen : seen nat nat nat sa_claim (hb_cpu nat nat nat (X_cas 5 v)) (X_cas 5 v) rf 2 0 0).
  { split.
    - exists 5, 1, (Shared Claim true 5 0 0). split; reflexivity.
    - left. apply t_trans with 1.
      + apply t_step.
        apply (cpu_fence nat nat nat (X_cas 5 v) 0 1 1 0 Claim 5 0 0 Claim 7 0 5);
          [lia | reflexivity | reflexivity].
      + apply t_step.
        apply (cpu_po nat nat nat (X_cas 5 v) 1 2 0 (Shared Claim true 7 0 5) (HistoryRead 0 v));
          [lia | reflexivity | reflexivity]. }
  specialize (Hnew 0 Hseen). unfold not_older, source_ok in *.
  destruct (rf 2) as [i|]; [|contradiction].
  destruct Hsrc as [Hi [t [e [He Hw]]]].
  unfold at_ in He. destruct i as [|[|i]]; simpl in He; [| |lia];
    inversion He; subst; simpl in Hw; inversion Hw; reflexivity.
Qed.

(** * Reduction: the hazard definition flags an unready read *)
Local Arguments SCpu {res val core tile cmd}.
Local Arguments SRun {res val core tile cmd}.
Local Arguments Issue {res val tile cmd}.
Local Arguments CpuRead {res val tile cmd}.
Local Arguments Got {val}.
Local Arguments Ack {val}.

Definition fp_store : nat -> (nat -> nat) -> list nat * list (nat * nat) :=
  fun _ _ => ([], [(7, 1)]).               (* the command writes element 7 *)
Definition no_tiles : nat -> list nat := fun _ => [].
(* 4. Semantics negative control (12 item 9): the same thread reads what its unfinished DX100
      store writes (no wait in between): a hazard. *)
Definition A_unready : Reduction.run nat nat nat nat nat :=
  [SCpu 0 (Issue 0) Ack; SRun 0 (fun _ => 0); SCpu 0 (CpuRead 7) (Got 0)].

Lemma no_wait_before_step_2 : forall n m,
  covered nat nat nat nat nat nat no_tiles no_tiles no_tiles no_tiles (fun _ => false)
    (fun _ => false) A_unready n m -> 2 <= m.
Proof.
  intros n m Hc. induction Hc; [|assumption|assumption].
  unfold waits_at in *.
  match goal with H : exists _, _ |- _ => destruct H as [c0 [Hw|Hw]] end;
    destruct m as [|[|m]]; simpl in Hw; try discriminate; lia.
Qed.

Lemma unready_read_is_hazard :
  hazard_own nat nat nat nat nat nat nat fp_store no_tiles no_tiles no_tiles no_tiles no_tiles
    (fun _ => false) (fun _ => false) (fun _ _ => False) (fun _ _ => False) (fun _ _ => False)
    (fun _ _ => True) (fun _ _ => True) A_unready 0 2.
Proof.
  left. exists (CpuRead 7), (Got 0). split; [reflexivity|].
  left. exists 0. split; [|split].
  - split; [exists 0, 0; reflexivity|]. split; [lia|].
    intros m Hm Hc. apply no_wait_before_step_2 in Hc. lia.
  - exists 0. reflexivity.
  - exists 0, 0, (fun _ => 0). split; [reflexivity|]. split; [reflexivity|].
    simpl. left. reflexivity.
Qed.

Print Assumptions stale_run_fits.
Print Assumptions stale_history_read_allowed.
Print Assumptions history_read_not_always_latest.
Print Assumptions read_own_write.
Print Assumptions failed_cas_reread_sees_winner.
Print Assumptions unready_read_is_hazard.
Print Assumptions shared_action_kinds_exactly_five.
Print Assumptions sharing_classes_exactly_four.
