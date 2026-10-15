(* Probata Rocq development: the parallel composition theorem (statement only).
   Created 2026-10-14 ET (ticket 41).  Revised 2026-10-14 ET after Codex's adversarial review
   and the main session's decisions (F1, F2, M1-M10).  Revised 2026-10-14 ET by the main
   session under Yan-Ru's delegation (ticket 41, Later changes): omp_ok requires well-bracketed
   critical sections (ticket 42's stray-Exit counterexample).  Revised 2026-10-15 ET:
   F1 excludes commands reading lock-protected data (ticket 41 fix (a)). Proof: ticket 42.
   Review guide: HYPOTHESES.md.  Map decisions: 15 items 1-7; 16 item 4 and Later changes;
   26 item 4; 12 items 4, 7.

   Reading order: 1 parameters, 2 events and runs, 3 memory model, 4 OpenMP rules,
   5 DX100 reads, 6 per-candidate obligations, 7 conclusion, 8 theorem. *)
From Stdlib Require Import List Arith Relations.
From Probata Require Import Vocabulary.
(* BEGIN t42 imports *)
From Stdlib Require Import Lia Bool PeanoNat.
(* END t42 imports *)
Import ListNotations.

Section Composition.

(** * 1. Parameters.  The theorem holds for every choice of them. *)
Variables loc arr val arg : Type.
Variable array_of : loc -> arr.        (* the array a location belongs to *)
Variable is_tile : loc -> Prop.        (* the location is a DX100 tile element, not memory *)
Variable init : loc -> val.            (* memory when the parallel region starts *)
Variable sa_new : shared_action_kind -> arg -> val -> option val.
  (* a shared action of kind k with argument a, finding old value v, stores w when
     sa_new k a v = Some w, and stores nothing (a failed CAS) when it is None *)
Variable N : nat.                      (* symbolic thread count; thread ids 0 .. N-1 *)
Variable team_size : nat.              (* threads the OpenMP runtime starts *)
Variable cls : nat -> arr -> sharing_class.
  (* class of each array in each barrier interval; the C lowering proposes it *)
(* w numbers worksharing constructs in the order a thread reaches them (uniform control
   makes the w-th one the same construct for every thread). *)
Variable space : nat -> list nat.      (* iteration space of worksharing construct w *)
Variable split_by_tid : nat -> bool.   (* true: the code splits construct w by thread id *)
Variable chunk : nat -> nat -> list nat.  (* chunk w t: the iterations that split gives thread t *)

(** * 2. Events and runs *)
Inductive event : Type :=
| Read (l : loc) (v : val)          (* plain read *)
| Write (l : loc) (v : val)         (* plain write *)
| HistoryRead (l : loc) (v : val)   (* a read that races by design: a relaxed atomic load *)
| Shared (k : shared_action_kind) (fence : bool) (a : arg) (l : loc) (old : val)
    (* one shared action: an atomic read-modify-write that reads old (15 items 3, 5).
       fence = true for __sync_* builtins, which GCC documents as full barriers;
       fence = false for a relaxed atomic such as a plain `omp atomic` *)
| DeviceRead (c : nat) (l : loc) (v : val)
    (* one element read by this thread's DX100 command c, placed at issue *)
| DeviceWrite (c : nat) (l : loc) (v : val)  (* one element write by command c, at issue *)
| DeviceCovered (c : nat)
    (* ghost: a wait of this thread covers command c here (proof-semantics coverage) *)
| Own (l : loc)                     (* ghost: this thread owns l until its next barrier *)
| Enter | Exit                      (* start and end of a critical section *)
| Workshare (w : nat)               (* the thread reaches worksharing construct w *)
| Iter (w : nat) (i : nat)          (* the thread starts iteration i of construct w *)
| Barrier.

(* The thread-indexed program: thread t, having done trace tr, may do event e next.
   Read events may carry any value; the rules below decide which values a run allows. *)
Variable step : nat -> list event -> event -> Prop.
Variable done : nat -> list event -> Prop.   (* thread t has finished after trace tr *)

(* A run lists every event of every thread in the order they take effect. *)
Definition run := list (nat * event).
Definition at_ (X : run) (i t : nat) (e : event) : Prop := nth_error X i = Some (t, e).
Definition proj (X : run) (t : nat) : list event :=
  map snd (filter (fun p => Nat.eqb (fst p) t) X).

Definition program_trace (t : nat) (tr : list event) : Prop :=
  forall pre e post, tr = pre ++ e :: post -> step t pre e.
Definition program_run (X : run) : Prop := forall t, program_trace t (proj X t).
Definition complete (X : run) : Prop := forall t, t < N -> done t (proj X t).

Definition is_barrier (e : event) : bool := match e with Barrier => true | _ => false end.
(* barrier interval of thread t's event at position i = barriers t passed before it *)
Definition interval (X : run) (t i : nat) : nat :=
  length (filter is_barrier (proj (firstn i X) t)).
Fixpoint in_crit (tr : list event) (b : bool) : bool :=
  match tr with
  | [] => b | Enter :: tr' => in_crit tr' true | Exit :: tr' => in_crit tr' false
  | _ :: tr' => in_crit tr' b
  end.
Definition inside (X : run) (t i : nat) : bool := in_crit (proj (firstn i X) t) false.
Definition owned (X : run) (t i : nat) (l : loc) : Prop :=
  exists j, j < i /\ at_ X j t (Own l) /\ interval X t j = interval X t i.

Definition loc_of (e : event) : option loc :=
  match e with
  | Read l _ | Write l _ | HistoryRead l _ | Shared _ _ _ l _
  | DeviceRead _ l _ | DeviceWrite _ l _ => Some l
  | _ => None
  end.
Definition written (e : event) : option (loc * val) :=
  match e with
  | Write l v | DeviceWrite _ l v => Some (l, v)
  | Shared k _ a l old => match sa_new k a old with Some w => Some (l, w) | None => None end
  | _ => None
  end.
Definition read_value (e : event) : option (loc * val) :=
  match e with
  | Read l v | HistoryRead l v | DeviceRead _ l v => Some (l, v)
  | Shared _ _ _ l old => Some (l, old)
  | _ => None
  end.
Definition is_shared (e : event) : bool := match e with Shared _ _ _ _ _ => true | _ => false end.
Definition device_cmd (e : event) : option nat :=
  match e with DeviceRead c _ _ | DeviceWrite c _ _ => Some c | _ => None end.
Definition writes (X : run) (i : nat) (l : loc) (v : val) : Prop :=
  exists t e, at_ X i t e /\ written e = Some (l, v).

(** * 3. Memory model: the history read (15 item 3) *)
(* OpenMP's memory ordering (assumption entry: OpenMP 5.2 runtime): a barrier orders every
   event before it before every event of a later interval; leaving critical orders before
   the next entry. *)
Inductive omp_sync (X : run) (i j : nat) : Prop :=
| omp_sync_barrier t t' e : i < j -> at_ X i t Barrier -> at_ X j t' e ->
    interval X t i < interval X t' j -> omp_sync X i j
| omp_sync_critical t t' : i < j -> at_ X i t Exit -> at_ X j t' Enter -> omp_sync X i j.
(* CPU ordering (platform entry): program order, and the order between fenced atomics.
   A `__sync_*` builtin compiles to a fully fenced read-modify-write on the pinned compiler
   and ISA, so all of them are totally ordered and each orders every access before it
   before every access after it in that order (cpu_fence; M1).  This is stronger than
   C++'s seq_cst read-modify-write and is stated as its own platform assumption. *)
Inductive cpu_sync (X : run) (i j : nat) : Prop :=
| cpu_po t e e' : i < j -> at_ X i t e -> at_ X j t e' -> cpu_sync X i j
| cpu_fence t t' k a l v k' a' l' v' : i < j -> at_ X i t (Shared k true a l v) ->
    at_ X j t' (Shared k' true a' l' v') -> cpu_sync X i j.
Definition hb_cpu (X : run) : nat -> nat -> Prop := clos_trans nat (cpu_sync X).
(* Full ordered-before: the CPU ordering plus OpenMP's barrier and critical ordering. *)
Inductive sync (X : run) (i j : nat) : Prop :=
| sync_cpu : cpu_sync X i j -> sync X i j
| sync_omp : omp_sync X i j -> sync X i j.
Definition hb (X : run) : nat -> nat -> Prop := clos_trans nat (sync X).

(* rf j: the position of the write read at position j; None = the initial value. *)
Definition rf_map := nat -> option nat.
Definition source_ok (X : run) (l : loc) (v : val) (s : option nat) (bound : nat) : Prop :=
  match s with None => v = init l | Some i => i < bound /\ writes X i l v end.
Definition not_older (s : option nat) (i : nat) : Prop :=
  match s with None => False | Some i' => i <= i' end.
(* The writes to l the reader at j has seen: ordered before j, or no newer than what the
   same thread already read from l (its own reads and writes). *)
Definition seen (H : nat -> nat -> Prop) (X : run) (rf : rf_map) (j : nat) (l : loc)
    (i : nat) : Prop :=
  (exists v, writes X i l v) /\
  (H i j \/
   exists r t e e' v s, r < j /\ at_ X r t e /\ at_ X j t e' /\
     read_value e = Some (l, v) /\ rf r = Some s /\ i <= s).
(* History read: a value the location already held (source before bound), never older
   than the newest write the reader has seen. *)
Definition read_ok (H : nat -> nat -> Prop) (X : run) (rf : rf_map) (j : nat) (l : loc)
    (v : val) (bound : nat) : Prop :=
  source_ok X l v (rf j) bound /\ forall i, seen H X rf j l i -> not_older (rf j) i.
Definition latest (X : run) (l : loc) (j : nat) (s : option nat) : Prop :=
  match s with
  | None => forall i v, i < j -> ~ writes X i l v
  | Some i => i < j /\ forall i' v, i < i' < j -> ~ writes X i' l v
  end.

(* Assumption entry, platform choice: the pinned compiler and ISA implement RC11, and each
   `__sync_*` builtin is a fully fenced read-modify-write (cpu_fence; M1).  Atomic
   read-modify-writes read the latest write (mo order = run order); a failed CAS writes
   nothing. *)
Definition memory_ok (X : run) (rf : rf_map) : Prop :=
  (forall j t l v, at_ X j t (Read l v) \/ at_ X j t (HistoryRead l v) ->
     read_ok (hb_cpu X) X rf j l v j) /\
  (forall j t k f a l old, at_ X j t (Shared k f a l old) ->
     source_ok X l old (rf j) j /\ latest X l j (rf j)).

(** * 4. OpenMP rules (15 item 4).  Assumption entry, trusted tool: OpenMP 5.2 runtime. *)
Definition count_iter (X : run) (w i : nat) : nat :=
  length (filter (fun p => match snd p with
                           | Iter w' i' => andb (Nat.eqb w w') (Nat.eqb i i')
                           | _ => false end) X).
(* critical is a structured block (OpenMP 5.2): in a thread's events an Exit closes the open
   critical section, and an Enter opens one only while none is open *)
Fixpoint brackets_ok (tr : list event) (open : bool) : bool :=
  match tr with
  | [] => true
  | Enter :: tr' => if open then false else brackets_ok tr' true
  | Exit :: tr' => if open then brackets_ok tr' false else false
  | _ :: tr' => brackets_ok tr' open
  end.
Definition omp_ok (X : run) (rf : rf_map) : Prop :=
  (* barrier and critical order memory: no CPU read is older than a write ordered before it
     through them (omp_sync, inside hb) *)
  (forall j t l v, at_ X j t (Read l v) \/ at_ X j t (HistoryRead l v) ->
     forall i, seen (hb X) X rf j l i -> not_older (rf j) i) /\
  (* thread ids are distinct, 0 .. team_size-1 *)
  (forall i t e, at_ X i t e -> t < team_size) /\
  (* a barrier waits for all threads: no event after barrier k before every thread's barrier k *)
  (forall j t' e' k t, at_ X j t' e' -> k < interval X t' j -> t < team_size ->
     exists i, i < j /\ at_ X i t Barrier /\ interval X t i = k) /\
  (* critical excludes other threads *)
  (forall i j t t', i < j -> at_ X i t Enter -> at_ X j t' Enter -> t <> t' ->
     exists x, i < x < j /\ at_ X x t Exit) /\
  (* omp for gives each iteration to exactly one thread, under any schedule *)
  ((forall t, t < team_size -> done t (proj X t)) ->
   forall w, split_by_tid w = false ->
   (forall t, t < team_size -> In (Workshare w) (proj X t)) ->
   forall i, count_iter X w i = if in_dec Nat.eq_dec i (space w) then 1 else 0) /\
  (* critical sections are well bracketed in every thread (structured blocks; ticket 42's
     stray-Exit counterexample) *)
  (forall t, brackets_ok (proj X t) false = true).

(** * 5. DX100 reads by this thread's commands (15 item 7; 12 item 4).
    Assumption entry, proof semantics: a DX100 read returns a value the location held while
    the command ran (before the wait that covers it), never older than the stores made
    before issue, and never a later write of the issuing thread itself. *)
Definition device_ok (X : run) (rf : rf_map) : Prop :=
  forall j t c l v, at_ X j t (DeviceRead c l v) ->
    read_ok (hb X) X rf j l v (length X) /\
    forall i, rf j = Some i -> j < i ->
      (forall q, j < q <= i -> ~ at_ X q t (DeviceCovered c)) /\ ~ exists e, at_ X i t e.

Definition model_run (X : run) (rf : rf_map) : Prop :=
  program_run X /\ memory_ok X rf /\ device_ok X rf /\ omp_ok X rf.

(** * 6. Per-candidate obligations (WP proves each one; HYPOTHESES.md names them) *)
(* Which accesses a sharing class allows (15 items 2, 3, 7).  crit: inside critical;
   own: the thread owns the location in this interval. *)
Definition fits_event (c : sharing_class) (crit own : Prop) (e : event) : Prop :=
  match e with
  | Read _ _ => c = ReadOnly \/ (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
  | HistoryRead _ _ | DeviceRead _ _ _ =>
      c = ReadOnly \/ (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
      \/ (c = SharedActionsOnly /\ ~ crit)
  | Write _ _ | DeviceWrite _ _ _ => (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
  | Shared _ _ _ _ _ => c = SharedActionsOnly /\ ~ crit
    (* a critical section touches no shared-actions-only location (Codex round 3) *)
  | _ => True
  end.
Definition fits (X : run) (t : nat) : Prop :=
  forall i e l, at_ X i t e -> loc_of e = Some l ->
    fits_event (cls (interval X t i) (array_of l)) (inside X t i = true) (owned X t i l) e.
Definition all_fit (X : run) : Prop := forall t, t < N -> fits X t.

(* class_fit: thread t's accesses fit their sharing classes whenever every other thread's
   accesses do so far (race freedom, 15 item 2). *)
Definition obl_class_fit : Prop :=
  forall X rf n t, model_run X rf -> t < N ->
    (forall t', t' < N -> t' <> t -> fits (firstn n X) t') -> fits (firstn n X) t.

(* owned_disjoint: owned ranges, tiles and registers are disjoint for t <> t'. *)
Definition obl_owned_disjoint : Prop :=
  forall X rf t t' i i' l, model_run X rf -> all_fit X -> t <> t' ->
    at_ X i t (Own l) -> at_ X i' t' (Own l) -> interval X t i <> interval X t' i'.

(* atomic_blocks: each critical section implements one named shared action (k, a) on one
   location l: its first access to l reads old; it writes only l and leaves what the action
   stores, or writes nothing when the action stores nothing.  Multi-location critical
   sections are not supported (M3). *)
Definition critical_block (tr blk : list event) : Prop :=
  exists pre post, tr = pre ++ Enter :: blk ++ Exit :: post /\ ~ In Enter blk /\ ~ In Exit blk.
Definition implements_shared_action (blk : list event) : Prop :=
  exists k a l old,
    (exists pre e post, blk = pre ++ e :: post /\ is_shared e = false /\
       read_value e = Some (l, old) /\ forall e', In e' pre -> loc_of e' <> Some l) /\
    match sa_new k a old with
    | None => forall e, In e blk -> written e = None          (* the action stores nothing *)
    | Some w =>
        (forall e l' v, In e blk -> written e = Some (l', v) -> l' = l) /\
        (exists pre e post, blk = pre ++ e :: post /\ written e = Some (l, w) /\
           forall e', In e' post -> written e' = None)
    end.
(* ... and holds no barrier (OpenMP 5.2 forbids a barrier nested in critical). *)
Definition obl_atomic_blocks : Prop :=
  forall t tr blk, t < N -> program_trace t tr -> critical_block tr blk ->
    implements_shared_action blk /\ ~ In Barrier blk.

(* chunk_cover: chunk splits computed from the thread id cover the space exactly once. *)
Fixpoint iters (w : nat) (tr : list event) : list nat :=
  match tr with
  | [] => [] | Iter w' i :: tr' => if Nat.eqb w w' then i :: iters w tr' else iters w tr'
  | _ :: tr' => iters w tr'
  end.
Definition obl_chunk_cover : Prop :=
  (forall w, split_by_tid w = true ->
     (forall i, In i (space w) <-> exists t, t < N /\ In i (chunk w t)) /\
     (forall t t' i, t < N -> t' < N -> t <> t' -> In i (chunk w t) -> ~ In i (chunk w t')) /\
     (forall t, NoDup (chunk w t))) /\
  (forall X rf t w, model_run X rf -> complete X -> all_fit X -> t < N ->
     split_by_tid w = true -> In (Workshare w) (proj X t) -> iters w (proj X t) = chunk w t).

(* uniform_control: any two threads reach the same barriers and worksharing constructs. *)
Definition is_sync_point (e : event) : bool :=
  match e with Barrier | Workshare _ => true | _ => false end.
Definition obl_uniform_control : Prop :=
  forall X rf t t', model_run X rf -> complete X -> all_fit X -> t < N -> t' < N ->
    filter is_sync_point (proj X t) = filter is_sync_point (proj X t').

(* team_size: the team has N threads (11's run-time guard). *)
Definition obl_team_size : Prop := team_size = N.

(* dx100_quiet (F1, refined by the main session's decision): in thread t's trace,
   (a) no own CPU access conflicts with a DX100 command's element before the wait that
       covers the command (12 items 3-4);
   (b) a command may stay uncovered past a barrier, or past the exit of a critical section
       it was issued in, only if it writes tile elements only (no memory) and those tile
       elements are dead there: never read again before a later command overwrites them
       (12 item 7: a DX100 store inside critical finishes before the lock is released).
       It must also read no LockProtected location: such reads must finish under the lock.
       The command must have outputs; that its reads reach nothing but those outputs is
       part of the lowering obligation cover_sound (HYPOTHESES.md). *)
Definition conflicts (d e : event) : Prop :=
  match d, e with
  | DeviceRead _ l _, (Write l' _ | Shared _ _ _ l' _) => l = l'
  | DeviceWrite _ l _, (Read l' _ | Write l' _ | HistoryRead l' _ | Shared _ _ _ l' _) => l = l'
  | _, _ => False
  end.
Definition covered_between (tr : list event) (c p q : nat) : Prop :=
  exists m, p < m < q /\ nth_error tr m = Some (DeviceCovered c).
(* command c crosses a barrier, or the exit of a critical section it was issued in,
   without a covering wait *)
Definition crosses_sync (tr : list event) (c : nat) : Prop :=
  exists p q d e, nth_error tr p = Some d /\ device_cmd d = Some c /\ p < q /\
    nth_error tr q = Some e /\
    (e = Barrier \/ (e = Exit /\ in_crit (firstn p tr) false = true)) /\
    ~ covered_between tr c p q.
Definition reads_loc (e : event) (l : loc) : Prop :=
  match read_value e with Some (l', _) => l' = l | None => False end.
Definition dead_after (tr : list event) (c : nat) : Prop :=
  (exists p l v, nth_error tr p = Some (DeviceWrite c l v)) /\
  forall p l v, nth_error tr p = Some (DeviceWrite c l v) ->
    is_tile l /\
    forall r e, p < r -> nth_error tr r = Some e -> reads_loc e l ->
      exists w c' v', p < w < r /\ nth_error tr w = Some (DeviceWrite c' l v') /\ c' <> c.
(* Sharing class is evaluated at each read's own barrier interval, just as in fits.
   Group all element reads by command id, including multi-element commands. *)
Definition reads_no_lock_protected (tr : list event) (c : nat) : Prop :=
  forall p l v, nth_error tr p = Some (DeviceRead c l v) ->
    cls (length (filter is_barrier (firstn p tr))) (array_of l) <> LockProtected.
(* An asynchronous read retains its sharing class until a cover has completed.
   The cover event itself is included: a class change at a barrier must wait for
   the outstanding access before the new interval starts. This is lifetime safety,
   not a promise that all arrays keep the same class for the whole region. *)
Definition reads_class_stable (tr : list event) : Prop :=
  forall p c l v q e, nth_error tr p = Some (DeviceRead c l v) ->
    p < q -> nth_error tr q = Some e -> ~ covered_between tr c p q ->
    cls (length (filter is_barrier (firstn q tr))) (array_of l) =
    cls (length (filter is_barrier (firstn p tr))) (array_of l).
Definition quiet_ok (tr : list event) : Prop :=
  (forall p d c, nth_error tr p = Some d -> device_cmd d = Some c ->
     forall m e, p < m -> nth_error tr m = Some e -> conflicts d e -> covered_between tr c p m) /\
  (forall c, crosses_sync tr c -> dead_after tr c /\ reads_no_lock_protected tr c) /\
  reads_class_stable tr.
Definition obl_dx100_quiet : Prop :=
  forall X rf t, model_run X rf -> complete X -> all_fit X -> t < N -> quiet_ok (proj X t).

(** * 7. Conclusion: the run ends as a serial order of its shared actions would *)
Definition intervals_contiguous (Y : run) : Prop :=
  forall i j t t' e e', i < j -> at_ Y i t e -> at_ Y j t' e' -> interval Y t i <= interval Y t' j.
Definition critical_sections_contiguous (Y : run) : Prop :=
  forall i x t, at_ Y i t Enter -> at_ Y x t Exit -> i < x ->
    (forall m, i < m < x -> ~ at_ Y m t Enter /\ ~ at_ Y m t Exit) ->
    forall m, i < m < x -> exists e, at_ Y m t e.
(* Every shared action, and every read of a location outside SharedActionsOnly, reads the
   latest write before it, except the dead reads of a command that crosses a barrier or a
   critical exit uncovered (F1; their values reach only dead tile elements). *)
Definition reads_latest (Y : run) (rf : rf_map) : Prop :=
  forall j t e l v, at_ Y j t e -> read_value e = Some (l, v) ->
    (is_shared e = true \/
     (cls (interval Y t j) (array_of l) <> SharedActionsOnly /\
      ~ exists c, device_cmd e = Some c /\ crosses_sync (proj Y t) c)) ->
    source_ok Y l v (rf j) j /\ latest Y l j (rf j).
Definition final_is (X : run) (l : loc) (v : val) : Prop :=
  (exists i, writes X i l v /\ forall i' v', i < i' -> ~ writes X i' l v') \/
  (v = init l /\ forall i v', ~ writes X i l v').
Definition iterations_once (Y : run) : Prop :=
  forall w, (exists t, t < N /\ In (Workshare w) (proj Y t)) ->
    forall i, count_iter Y w i = if in_dec Nat.eq_dec i (space w) then 1 else 0.

Definition serial_outcome (X Y : run) (rf' : rf_map) : Prop :=
  (forall t, proj Y t = proj X t) /\               (* each thread does exactly what it did in X *)
  intervals_contiguous Y /\                        (* barrier intervals one after another *)
  critical_sections_contiguous Y /\                (* a critical section runs alone *)
  (forall t blk, critical_block (proj Y t) blk -> implements_shared_action blk) /\
  reads_latest Y rf' /\                            (* serial: no stale value but by design *)
  memory_ok Y rf' /\ omp_ok Y rf' /\ device_ok Y rf' /\  (* racing reads stay history reads *)
  (forall l v, final_is X l v <-> final_is Y l v) /\  (* same final memory *)
  iterations_once Y.                               (* every iteration exactly once *)

(* BEGIN t42 lemmas *)

(** Small list and projection facts used throughout the proof. *)
Lemma t42_nth_error_firstn {A : Type} (xs : list A) n i a :
  nth_error (firstn n xs) i = Some a <->
  i < n /\ nth_error xs i = Some a.
Proof.
  revert xs i.
  induction n as [|n IH]; intros xs i.
  - split.
    + intro H. destruct i; inversion H.
    + intros [Hi _]. lia.
  - destruct xs as [|x xs].
    + split.
      * intro H. destruct i; inversion H.
      * intros [_ H]. destruct i; inversion H.
    + destruct i as [|i].
      * simpl. split; intro H.
        -- split; [lia | exact H].
        -- destruct H as [_ H]. exact H.
      * simpl. rewrite IH. split.
        -- intros [Hi Hnth]. split; [lia | exact Hnth].
        -- intros [Hi Hnth]. split; [lia | exact Hnth].
Qed.

Lemma t42_at_firstn (X : run) n i t e :
  at_ (firstn n X) i t e <-> i < n /\ at_ X i t e.
Proof.
  unfold at_. apply t42_nth_error_firstn.
Qed.

Lemma t42_firstn_firstn_le {A : Type} (xs : list A) i n :
  i <= n -> firstn i (firstn n xs) = firstn i xs.
Proof.
  revert xs n.
  induction i as [|i IH]; intros xs n Hin; [reflexivity |].
  destruct n as [|n]; [lia |].
  destruct xs as [|x xs]; [reflexivity |].
  simpl. f_equal. apply IH. lia.
Qed.

Lemma t42_firstn_succ_some {A : Type} (xs : list A) i a :
  nth_error xs i = Some a ->
  firstn (S i) xs = firstn i xs ++ [a].
Proof.
  revert xs.
  induction i as [|i IH]; intros xs Hnth.
  - destruct xs as [|x xs]; simpl in Hnth; [discriminate |].
    inversion Hnth. reflexivity.
  - destruct xs as [|x xs]; simpl in Hnth; [discriminate |].
    simpl. f_equal. apply IH. exact Hnth.
Qed.

Lemma t42_firstn_succ_none {A : Type} (xs : list A) i :
  nth_error xs i = None -> firstn (S i) xs = firstn i xs.
Proof.
  revert xs.
  induction i as [|i IH]; intros xs Hnth.
  - destruct xs as [|x xs]; simpl in *; [reflexivity | discriminate].
  - destruct xs as [|x xs]; simpl in *; [reflexivity |].
    f_equal. apply IH. exact Hnth.
Qed.

Lemma t42_at_unique (X : run) i t e t' e' :
  at_ X i t e -> at_ X i t' e' -> t = t' /\ e = e'.
Proof.
  unfold at_. intros H H'. rewrite H in H'. inversion H'. auto.
Qed.

Lemma t42_proj_app (A B : run) t :
  proj (A ++ B) t = proj A t ++ proj B t.
Proof.
  unfold proj. rewrite filter_app, map_app. reflexivity.
Qed.

Lemma t42_proj_snoc_same (A : run) t e :
  proj (A ++ [(t, e)]) t = proj A t ++ [e].
Proof.
  rewrite t42_proj_app. unfold proj. simpl. rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma t42_proj_snoc_other (A : run) u t e :
  u <> t -> proj (A ++ [(u, e)]) t = proj A t.
Proof.
  intro Hut. rewrite t42_proj_app.
  assert (Hnil : proj [(u, e)] t = []).
  { unfold proj. simpl. destruct (Nat.eqb u t) eqn:Hutb; [|reflexivity].
    apply Nat.eqb_eq in Hutb. contradiction. }
  rewrite Hnil. apply app_nil_r.
Qed.

Lemma t42_in_proj (X : run) t e :
  In e (proj X t) <-> In (t, e) X.
Proof.
  unfold proj. induction X as [|[u d] X IH]; [simpl; tauto |].
  simpl. destruct (Nat.eqb u t) eqn:Hut.
  - apply Nat.eqb_eq in Hut. subst u. simpl. rewrite IH.
    split; intros [H | H]; [left; congruence | right; exact H |
                            left; congruence | right; exact H].
  - apply Nat.eqb_neq in Hut. rewrite IH. split.
    + intro H. right. exact H.
    + intros [H | H]; [inversion H; contradiction | exact H].
Qed.

(** Prefixes do not change any state observed at a position they retain. *)
Lemma t42_interval_firstn (X : run) n t i :
  i <= n -> interval (firstn n X) t i = interval X t i.
Proof.
  intro Hin. unfold interval.
  rewrite t42_firstn_firstn_le by exact Hin. reflexivity.
Qed.

Lemma t42_inside_firstn (X : run) n t i :
  i <= n -> inside (firstn n X) t i = inside X t i.
Proof.
  intro Hin. unfold inside.
  rewrite t42_firstn_firstn_le by exact Hin. reflexivity.
Qed.

Lemma t42_owned_firstn (X : run) n t i l :
  i < n -> (owned (firstn n X) t i l <-> owned X t i l).
Proof.
  intro Hin. unfold owned. split.
  - intros [j [Hji [Hat Heq]]].
    exists j. split; [exact Hji |]. split.
    + apply (proj1 (t42_at_firstn X n j t (Own l))) in Hat. exact (proj2 Hat).
    + rewrite t42_interval_firstn in Heq by lia.
      rewrite t42_interval_firstn in Heq by lia. exact Heq.
  - intros [j [Hji [Hat Heq]]].
    exists j. split; [exact Hji |]. split.
    + apply (proj2 (t42_at_firstn X n j t (Own l))). split; [lia | exact Hat].
    + rewrite t42_interval_firstn by lia.
      rewrite t42_interval_firstn by lia. exact Heq.
Qed.

Lemma t42_fits_event_owned_mono c crit own own' e :
  (own -> own') ->
  fits_event c crit own e -> fits_event c crit own' e.
Proof.
  destruct e; simpl; intuition.
Qed.

Lemma t42_fits_firstn (X : run) n t :
  fits (firstn n X) t <->
  forall i e l, i < n -> at_ X i t e -> loc_of e = Some l ->
    fits_event (cls (interval X t i) (array_of l))
      (inside X t i = true) (owned X t i l) e.
Proof.
  unfold fits. split.
  - intros Hfit i e l Hin Hat Hloc.
    specialize (Hfit i e l).
    rewrite t42_interval_firstn in Hfit by lia.
    rewrite t42_inside_firstn in Hfit by lia.
    specialize (Hfit ltac:(apply (proj2 (t42_at_firstn X n i t e)); auto) Hloc).
    pose proof (t42_owned_firstn X n t i l Hin) as Hown.
    eapply t42_fits_event_owned_mono; [exact (proj1 Hown) | exact Hfit].
  - intros Hfit i e l Hat Hloc.
    apply (proj1 (t42_at_firstn X n i t e)) in Hat.
    destruct Hat as [Hin Hat].
    rewrite t42_interval_firstn by lia.
    rewrite t42_inside_firstn by lia.
    specialize (Hfit i e l Hin Hat Hloc).
    pose proof (t42_owned_firstn X n t i l Hin) as Hown.
    eapply t42_fits_event_owned_mono; [exact (proj2 Hown) | exact Hfit].
Qed.

(** A1: every event in a modeled run belongs to one of the [N] threads. *)
Lemma t42_threads_below_N :
  obl_team_size -> forall X rf, omp_ok X rf ->
  forall i t e, at_ X i t e -> t < N.
Proof.
  intros Hteam X rf Homp i t e Hat.
  unfold obl_team_size in Hteam.
  destruct Homp as [_ [Hthreads _]]. pose proof (Hthreads i t e Hat). lia.
Qed.

(** A2: the rely-style class premise implies that every thread fits. *)
Lemma t42_all_fit_from_class :
  obl_class_fit -> forall X rf, model_run X rf -> all_fit X.
Proof.
  intros Hclass X rf Hmodel.
  assert (Hprefix : forall n, all_fit (firstn n X)).
  {
    intro n. induction n as [|n IH].
    - intros t Ht. apply (proj2 (t42_fits_firstn X 0 t)).
      intros i e l Hi. lia.
    - destruct (nth_error X n) as [[owner ev] |] eqn:Hnth.
      + intros t Ht. destruct (Nat.eq_dec t owner) as [Hto | Hto].
        * subst t. eapply Hclass; eauto.
          intros u Hu Huo. apply (proj2 (t42_fits_firstn X (S n) u)).
          intros i e l Hi Hat Hloc.
          assert (i < n \/ i = n) as [Hin | ->] by lia.
          -- apply (proj1 (t42_fits_firstn X n u) (IH u Hu) i e l Hin Hat Hloc).
          -- exfalso. apply Huo. symmetry.
             exact (proj1 (t42_at_unique X n owner ev u e Hnth Hat)).
        * apply (proj2 (t42_fits_firstn X (S n) t)).
          intros i e l Hi Hat Hloc.
          assert (i < n \/ i = n) as [Hin | ->] by lia.
          -- apply (proj1 (t42_fits_firstn X n t) (IH t Ht) i e l Hin Hat Hloc).
          -- exfalso. apply Hto. symmetry.
             exact (proj1 (t42_at_unique X n owner ev t e Hnth Hat)).
      + intros t Ht. apply (proj2 (t42_fits_firstn X (S n) t)).
        intros i e l Hi Hat Hloc.
        assert (i < n \/ i = n) as [Hin | ->] by lia.
        * apply (proj1 (t42_fits_firstn X n t) (IH t Ht) i e l Hin Hat Hloc).
        * unfold at_ in Hat. rewrite Hnth in Hat. discriminate.
  }
  specialize (Hprefix (length X)). rewrite firstn_all in Hprefix. exact Hprefix.
Qed.

(** Counting barriers directly in the global prefix makes interval arithmetic simple. *)
Definition t42_is_barrier_of (t : nat) (p : nat * event) : bool :=
  andb (Nat.eqb (fst p) t) (is_barrier (snd p)).

Lemma t42_interval_count (X : run) t i :
  interval X t i = length (filter (t42_is_barrier_of t) (firstn i X)).
Proof.
  unfold interval, proj, t42_is_barrier_of.
  remember (firstn i X) as A. clear HeqA X i.
  induction A as [|[u e] A IH]; [reflexivity |].
  simpl. destruct (Nat.eqb u t) eqn:Hut; destruct e; simpl;
    try rewrite IH; reflexivity.
Qed.

Lemma t42_filter_firstn_step {A : Type} (f : A -> bool) (xs : list A) i :
  length (filter f (firstn i xs)) <=
  length (filter f (firstn (S i) xs)).
Proof.
  revert xs. induction i as [|i IH].
  - intros [|x xs]; simpl; apply Nat.le_0_l.
  - intros [|x xs]; [simpl; apply Nat.le_refl |].
    simpl. destruct (f x) eqn:Hfx; try rewrite Hfx; simpl.
    + apply le_n_S. apply IH.
    + apply IH.
Qed.

Lemma t42_interval_step_le (X : run) t i :
  interval X t i <= interval X t (S i).
Proof.
  repeat rewrite t42_interval_count. apply t42_filter_firstn_step.
Qed.

Lemma t42_interval_mono (X : run) t i j :
  i <= j -> interval X t i <= interval X t j.
Proof.
  intro Hij. induction Hij.
  - apply Nat.le_refl.
  - eapply Nat.le_trans; [exact IHHij | apply t42_interval_step_le].
Qed.

Lemma t42_interval_succ_barrier (X : run) t i :
  at_ X i t Barrier -> interval X t (S i) = S (interval X t i).
Proof.
  intro Hat. unfold at_ in Hat.
  repeat rewrite t42_interval_count.
  rewrite (t42_firstn_succ_some X i (t, Barrier) Hat).
  rewrite filter_app. unfold t42_is_barrier_of. simpl. rewrite Nat.eqb_refl.
  simpl. rewrite length_app. simpl. lia.
Qed.

Lemma t42_barrier_interval_lt (X : run) t i j :
  i < j -> at_ X i t Barrier -> interval X t i < interval X t j.
Proof.
  intros Hij Hat.
  pose proof (t42_interval_mono X t (S i) j ltac:(lia)) as Hmono.
  rewrite t42_interval_succ_barrier in Hmono by exact Hat. lia.
Qed.

(** A3: OpenMP's barrier condition already puts the run in interval order. *)
Lemma t42_intervals_contiguous :
  obl_team_size -> forall X rf, omp_ok X rf -> intervals_contiguous X.
Proof.
  intros Hteam X rf Homp i j t t' e e' Hij Hati Hatj.
  destruct Homp as [_ [Hthreads [Hbarrier _]]].
  destruct (Nat.le_gt_cases (interval X t i) (interval X t' j)) as [Hle | Hgt].
  - exact Hle.
  - assert (Ht' : t' < team_size) by (eapply Hthreads; eauto).
    destruct (Hbarrier i t e (interval X t' j) t' Hati ltac:(lia) Ht')
      as [q [Hqi [Hatq Heqq]]].
    pose proof (t42_barrier_interval_lt X t' q j ltac:(lia) Hatq) as Hlt.
    lia.
Qed.

(** Toolkit for the critical-section state carried by a thread projection. *)
Lemma t42_in_crit_app (a b : list event) state :
  in_crit (a ++ b) state = in_crit b (in_crit a state).
Proof.
  revert state. induction a as [|e a IH]; intro state; [reflexivity |].
  destruct e; simpl; apply IH.
Qed.

Lemma t42_in_crit_snoc_true (tr : list event) e :
  in_crit (tr ++ [e]) false = true ->
  e = Enter \/ (e <> Exit /\ in_crit tr false = true).
Proof.
  rewrite t42_in_crit_app. destruct e; simpl; intro H;
    try (right; split; [discriminate | exact H]).
  - left. reflexivity.
  - discriminate.
Qed.

Lemma t42_inside_true_witness (X : run) t m :
  inside X t m = true ->
  exists q, q < m /\ at_ X q t Enter /\
    forall r, q < r < m -> ~ at_ X r t Exit.
Proof.
  induction m as [|m IH].
  - unfold inside. simpl. discriminate.
  - intro Hinside. destruct (nth_error X m) as [[u e] |] eqn:Hnth.
    + pose proof (t42_firstn_succ_some X m (u, e) Hnth) as Hfirst.
      destruct (Nat.eq_dec u t) as [Hut | Hut].
      * subst u. unfold inside in Hinside. rewrite Hfirst in Hinside.
        rewrite t42_proj_snoc_same in Hinside.
        apply t42_in_crit_snoc_true in Hinside.
        destruct Hinside as [He | [Hne Hprevious]].
        -- subst e. exists m. split; [lia |]. split; [exact Hnth |].
           intros r Hr. lia.
        -- change (inside X t m = true) in Hprevious.
           destruct (IH Hprevious) as [q [Hqm [Hatq Hexit]]].
           exists q. split; [lia |]. split; [exact Hatq |].
           intros r [Hqr Hrm] Hatr.
           destruct (Nat.eq_dec r m) as [-> | Hneq].
           ++ apply Hne. exact (proj2 (t42_at_unique X m t e t Exit Hnth Hatr)).
           ++ assert (Hrl : r < m) by lia.
              apply (Hexit r); [split; assumption | exact Hatr].
      * unfold inside in Hinside. rewrite Hfirst in Hinside.
        rewrite t42_proj_snoc_other in Hinside by exact Hut.
        change (inside X t m = true) in Hinside.
        destruct (IH Hinside) as [q [Hqm [Hatq Hexit]]].
        exists q. split; [lia |]. split; [exact Hatq |].
        intros r [Hqr Hrm] Hatr.
        destruct (Nat.eq_dec r m) as [-> | Hneq].
        -- apply Hut. exact (proj1 (t42_at_unique X m u e t Exit Hnth Hatr)).
        -- assert (Hrl : r < m) by lia.
           apply (Hexit r); [split; assumption | exact Hatr].
    + unfold inside in Hinside.
      rewrite t42_firstn_succ_none in Hinside by exact Hnth.
      change (inside X t m = true) in Hinside.
      destruct (IH Hinside) as [q [Hqm [Hatq Hexit]]].
      exists q. split; [lia |]. split; [exact Hatq |].
      intros r [Hqr Hrm] Hatr.
      destruct (Nat.eq_dec r m) as [-> | Hneq].
      * unfold at_ in Hatr. rewrite Hnth in Hatr. discriminate.
      * assert (Hrl : r < m) by lia.
        apply (Hexit r); [split; assumption | exact Hatr].
Qed.

(** A4a: no other thread can enter during a critical-section window. *)
Lemma t42_window_no_other_enter (X : run) rf i x t u :
  omp_ok X rf ->
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  t <> u -> forall m, i < m < x -> ~ at_ X m u Enter.
Proof.
  intros Homp Henter Hexit Hix Hwindow Htu m Him Henteru.
  destruct Homp as [_ [_ [_ [Hcritical _]]]].
  destruct (Hcritical i m t u (proj1 Him) Henter Henteru Htu)
    as [q [[Hiq Hqm] Hexitq]].
  exact (proj2 (Hwindow q ltac:(lia)) Hexitq).
Qed.

(** A4b: another thread is outside critical throughout such a window. *)
Lemma t42_window_other_outside (X : run) rf i x t u m :
  omp_ok X rf ->
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  t <> u -> i < m < x -> inside X u m = false.
Proof.
  intros Homp Henter Hexit Hix Hwindow Htu Him.
  destruct (inside X u m) eqn:Hinside; [exfalso | reflexivity].
  destruct (t42_inside_true_witness X u m Hinside)
    as [q [Hqm [Henterq Hnoexit]]].
  destruct (Nat.lt_trichotomy q i) as [Hqi | [Hqi | Hiq]].
  - destruct Homp as [_ [_ [_ [Hcritical _]]]].
    destruct (Hcritical q i u t Hqi Henterq Henter ltac:(congruence))
      as [r [[Hqr Hri] Hexitr]].
    apply (Hnoexit r); [split; [exact Hqr | lia] | exact Hexitr].
  - subst q. apply Htu. exact (proj1 (t42_at_unique X i t Enter u Enter Henter Henterq)).
  - eapply (t42_window_no_other_enter X rf i x t u Homp Henter Hexit Hix Hwindow Htu q);
      [lia | exact Henterq].
Qed.

(** Position/splitting facts for isolating a window in a global run. *)
Lemma t42_at_split (X : run) i t e :
  at_ X i t e ->
  exists A B, X = A ++ (t, e) :: B /\ length A = i.
Proof.
  revert X. induction i as [|i IH]; intros [|p X] Hat; unfold at_ in Hat; simpl in Hat.
  - discriminate.
  - inversion Hat. subst p. exists [], X. auto.
  - discriminate.
  - destruct (IH X Hat) as [A [B [HX Hlen]]].
    subst X. exists (p :: A), B. simpl. auto.
Qed.

Lemma t42_nth_after_prefix {A : Type} (pre : list A) a rest k :
  nth_error (pre ++ a :: rest) (S (length pre + k)) = nth_error rest k.
Proof.
  induction pre as [|p pre IH]; [reflexivity |]. simpl. exact IH.
Qed.

Lemma t42_two_at_split (X : run) i x t e u d :
  i < x -> at_ X i t e -> at_ X x u d ->
  exists A B C,
    X = A ++ (t, e) :: B ++ (u, d) :: C /\
    length A = i /\ x = S (i + length B).
Proof.
  intros Hix Hati Hatx.
  destruct (t42_at_split X i t e Hati) as [A [R [HX HlenA]]].
  rewrite HX in Hatx. unfold at_ in Hatx.
  replace x with (S (length A + (x - S i))) in Hatx by lia.
  rewrite t42_nth_after_prefix in Hatx.
  destruct (t42_at_split R (x - S i) u d Hatx) as [B [C [HR HlenB]]].
  exists A, B, C. subst R. split; [exact HX |]. split; [exact HlenA | lia].
Qed.

Lemma t42_nth_error_lt {A : Type} (xs : list A) i a :
  nth_error xs i = Some a -> i < length xs.
Proof.
  revert i. induction xs as [|x xs IH].
  - intros i H. destruct i; discriminate.
  - intros [|i] H.
    + simpl. lia.
    + simpl in H. simpl. specialize (IH i H). lia.
Qed.

Lemma t42_nth_error_in {A : Type} (xs : list A) i a :
  nth_error xs i = Some a -> In a xs.
Proof.
  revert i. induction xs as [|x xs IH]; intros [|i] H; simpl in H; try discriminate.
  - inversion H. left. reflexivity.
  - right. apply (IH i H).
Qed.

Lemma t42_in_nth_error {A : Type} (xs : list A) a :
  In a xs -> exists i, nth_error xs i = Some a.
Proof.
  induction xs as [|x xs IH]; simpl; intro H; [contradiction |].
  destruct H as [-> | H].
  - exists 0. reflexivity.
  - destruct (IH H) as [i Hi]. exists (S i). exact Hi.
Qed.

Lemma t42_nth_error_app_left {A : Type} (xs ys : list A) i :
  i < length xs -> nth_error (xs ++ ys) i = nth_error xs i.
Proof.
  revert i. induction xs as [|x xs IH].
  - intros i Hi. simpl in Hi. lia.
  - intros [|i] Hi; [reflexivity |]. simpl. apply IH. simpl in Hi. lia.
Qed.

Lemma t42_in_middle_at (A B C : run) a b p :
  In p B ->
  exists m, length A < m < S (length A + length B) /\
    nth_error (A ++ a :: B ++ b :: C) m = Some p.
Proof.
  revert B. induction A as [|z A IH]; intros B Hin.
  - destruct (t42_in_nth_error B p Hin) as [k Hk].
    exists (S k). split.
    + pose proof (t42_nth_error_lt B k p Hk). simpl. lia.
    + simpl. rewrite t42_nth_error_app_left by (eapply t42_nth_error_lt; eauto).
      exact Hk.
  - destruct (IH B Hin) as [m [Hbounds Hnth]].
    exists (S m). simpl. split; [lia | exact Hnth].
Qed.

Lemma t42_nth_between (A B C : run) a b m p :
  length A < m < S (length A + length B) ->
  nth_error (A ++ a :: B ++ b :: C) m = Some p -> In p B.
Proof.
  revert m. induction A as [|z A IH]; intros m Hbounds Hnth.
  - destruct m as [|m]; [simpl in Hbounds; lia |].
    simpl in Hnth. apply (t42_nth_error_in B m p).
    rewrite <- Hnth. symmetry. apply t42_nth_error_app_left. simpl in Hbounds. lia.
  - destruct m as [|m]; [simpl in Hbounds; lia |].
    simpl in Hnth, Hbounds. eapply IH; eauto. lia.
Qed.

Lemma t42_proj_cons_same (X : run) t e :
  proj ((t, e) :: X) t = e :: proj X t.
Proof.
  unfold proj. simpl. rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma t42_proj_window (A B C : run) t e d :
  proj (A ++ (t, e) :: B ++ (t, d) :: C) t =
  proj A t ++ e :: proj B t ++ d :: proj C t.
Proof.
  rewrite t42_proj_app. rewrite t42_proj_cons_same.
  rewrite t42_proj_app. rewrite t42_proj_cons_same. reflexivity.
Qed.

(** A4c, first part: the window is an actual critical block in the projection. *)
Lemma t42_window_critical_block (X : run) i x t :
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  exists blk, critical_block (proj X t) blk /\
    forall m e, i < m < x -> at_ X m t e -> In e blk.
Proof.
  intros Henter Hexit Hix Hwindow.
  destruct (t42_two_at_split X i x t Enter t Exit Hix Henter Hexit)
    as [A [B [C [HX [HlenA HlenX]]]]].
  exists (proj B t). split.
  - unfold critical_block. exists (proj A t), (proj C t). split.
    + rewrite HX. apply t42_proj_window.
    + split; intro Hin.
      * apply t42_in_proj in Hin.
        destruct (t42_in_middle_at A B C (t, Enter) (t, Exit) (t, Enter) Hin)
          as [m [Hbounds Hatm]].
        apply (proj1 (Hwindow m ltac:(lia))). unfold at_. rewrite HX. exact Hatm.
      * apply t42_in_proj in Hin.
        destruct (t42_in_middle_at A B C (t, Enter) (t, Exit) (t, Exit) Hin)
          as [m [Hbounds Hatm]].
        apply (proj2 (Hwindow m ltac:(lia))). unfold at_. rewrite HX. exact Hatm.
  - intros m e Hm Hatm. apply (proj2 (t42_in_proj B t e)).
    apply (t42_nth_between A B C (t, Enter) (t, Exit) m (t, e)); [lia |].
    rewrite <- HX. exact Hatm.
Qed.

Lemma t42_window_no_barrier (X : run) i x t :
  obl_atomic_blocks -> program_run X -> t < N ->
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  forall m, i < m < x -> ~ at_ X m t Barrier.
Proof.
  intros Hatomic Hprogram Ht Henter Hexit Hix Hwindow m Hm Hatm.
  destruct (t42_window_critical_block X i x t Henter Hexit Hix Hwindow)
    as [blk [Hblock Hmembers]].
  destruct (Hatomic t (proj X t) blk Ht (Hprogram t) Hblock) as [_ Hnobarrier].
  apply Hnobarrier. eapply Hmembers; eauto.
Qed.

Lemma t42_interval_step_eq (X : run) t i :
  ~ at_ X i t Barrier -> interval X t (S i) = interval X t i.
Proof.
  intro Hno. destruct (nth_error X i) as [[u e] |] eqn:Hnth.
  - assert (Hp : t42_is_barrier_of t (u, e) = false).
    { unfold t42_is_barrier_of. change ((Nat.eqb u t && is_barrier e) = false).
      destruct (Nat.eqb u t) eqn:Hut.
      - apply Nat.eqb_eq in Hut. subst u. try rewrite Nat.eqb_refl. simpl.
        destruct e; try reflexivity.
        exfalso. apply Hno. exact Hnth.
      - reflexivity. }
    assert (Hnil : filter (t42_is_barrier_of t) [(u, e)] = []).
    { change ((if t42_is_barrier_of t (u, e) then [(u, e)] else []) = []).
      rewrite Hp. reflexivity. }
    repeat rewrite t42_interval_count.
    rewrite (t42_firstn_succ_some X i (u, e) Hnth).
    rewrite filter_app. rewrite Hnil. rewrite app_nil_r. reflexivity.
  - repeat rewrite t42_interval_count.
    rewrite (t42_firstn_succ_none X i Hnth). reflexivity.
Qed.

Lemma t42_interval_eq_without_barrier (X : run) t i j :
  i <= j ->
  (forall q, i <= q < j -> ~ at_ X q t Barrier) ->
  interval X t i = interval X t j.
Proof.
  revert i. induction j as [|j IH]; intros i Hij Hno.
  - assert (i = 0) by lia. subst i. reflexivity.
  - destruct (Nat.eq_dec i (S j)) as [-> | Hneq]; [reflexivity |].
    assert (Hij' : i <= j) by lia.
    transitivity (interval X t j).
    + apply IH; [exact Hij' |]. intros q Hq. apply Hno. lia.
    + symmetry. apply t42_interval_step_eq. apply Hno. lia.
Qed.

Lemma t42_window_same_thread_interval (X : run) i x t :
  obl_atomic_blocks -> program_run X -> t < N ->
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  forall m e, i <= m <= x -> at_ X m t e -> interval X t i = interval X t m.
Proof.
  intros Hatomic Hprogram Ht Henter Hexit Hix Hwindow m e Hm Hatm.
  apply t42_interval_eq_without_barrier; [lia |].
  intros q Hq Hatq. destruct (Nat.eq_dec q i) as [-> | Hqi].
  - pose proof (proj2 (t42_at_unique X i t Enter t Barrier Henter Hatq)). discriminate.
  - eapply (t42_window_no_barrier X i x t Hatomic Hprogram Ht Henter Hexit Hix Hwindow q);
      [lia | exact Hatq].
Qed.

(** A4c, final part: every event in the window has the window's interval. *)
Lemma t42_window_interval (X : run) i x t :
  obl_atomic_blocks -> program_run X -> t < N -> intervals_contiguous X ->
  at_ X i t Enter -> at_ X x t Exit -> i < x ->
  (forall q, i < q < x -> ~ at_ X q t Enter /\ ~ at_ X q t Exit) ->
  forall m u e, i <= m <= x -> at_ X m u e -> interval X u m = interval X t i.
Proof.
  intros Hatomic Hprogram Ht Hordered Henter Hexit Hix Hwindow m u e Hm Hatm.
  pose proof (t42_window_same_thread_interval X i x t Hatomic Hprogram Ht
    Henter Hexit Hix Hwindow x Exit ltac:(lia) Hexit) as Hend.
  destruct (Nat.eq_dec m i) as [-> | Hmi].
  - pose proof (proj1 (t42_at_unique X i t Enter u e Henter Hatm)) as ->. reflexivity.
  - destruct (Nat.eq_dec m x) as [-> | Hmx].
    + pose proof (proj1 (t42_at_unique X x t Exit u e Hexit Hatm)) as ->.
      symmetry. exact Hend.
    + pose proof (Hordered i m t u Enter e ltac:(lia) Henter Hatm) as Hleft.
      pose proof (Hordered m x u t e Exit ltac:(lia) Hatm Hexit) as Hright.
      lia.
Qed.

(** Milestone 2: one adjacent transposition and its structural invariants. *)
Fixpoint t42_sw (p i : nat) : nat :=
  match p, i with
  | 0, 0 => 1
  | 0, 1 => 0
  | 0, S (S i') => S (S i')
  | S p', 0 => 0
  | S p', S i' => S (t42_sw p' i')
  end.

Fixpoint t42_swap_run (X : run) (p : nat) : run :=
  match p, X with
  | 0, a :: b :: rest => b :: a :: rest
  | S p', a :: rest => a :: t42_swap_run rest p'
  | _, _ => X
  end.

Definition t42_swap_rf (p : nat) (rf : rf_map) : rf_map :=
  fun j => option_map (t42_sw p) (rf (t42_sw p j)).

Definition t42_adjacent (X : run) p t1 e1 t2 e2 : Prop :=
  exists A B, length A = p /\ X = A ++ (t1, e1) :: (t2, e2) :: B.

Definition t42_events_conflict (e1 e2 : event) : Prop :=
  exists l, loc_of e1 = Some l /\ loc_of e2 = Some l /\
    ((exists v, written e1 = Some (l, v)) \/
     (exists v, written e2 = Some (l, v))).

Definition t42_indep (X : run) p : Prop :=
  exists t1 e1 t2 e2,
    t42_adjacent X p t1 e1 t2 e2 /\ t1 <> t2 /\
    ~ sync X p (S p) /\ ~ sync (t42_swap_run X p) p (S p) /\
    ~ t42_events_conflict e1 e2.

Lemma t42_sw_involutive p i : t42_sw p (t42_sw p i) = i.
Proof.
  revert i. induction p as [|p IH].
  - intros [|[|i]]; reflexivity.
  - intros [|i]; [reflexivity |]. simpl. rewrite IH. reflexivity.
Qed.

Lemma t42_sw_injective p i j : t42_sw p i = t42_sw p j -> i = j.
Proof.
  intro H. rewrite <- (t42_sw_involutive p i), <- (t42_sw_involutive p j).
  now rewrite H.
Qed.

Lemma t42_sw_p p : t42_sw p p = S p.
Proof.
  induction p; simpl; [reflexivity | now rewrite IHp].
Qed.

Lemma t42_sw_Sp p : t42_sw p (S p) = p.
Proof.
  induction p; simpl; [reflexivity | now rewrite IHp].
Qed.

Lemma t42_sw_other p i :
  i <> p -> i <> S p -> t42_sw p i = i.
Proof.
  revert i. induction p as [|p IH]; intros i Hip HiS.
  - destruct i as [|[|i]]; [contradiction | contradiction | reflexivity].
  - destruct i as [|i]; [reflexivity |]. simpl. f_equal.
    apply IH.
    + intro H. apply Hip. now f_equal.
    + intro H. apply HiS. now f_equal.
Qed.

Lemma t42_sw_order p i j :
  i < j -> ~ (i = p /\ j = S p) -> t42_sw p i < t42_sw p j.
Proof.
  intros Hij Hcross.
  destruct (Nat.eq_dec i p) as [-> | Hip].
  - destruct (Nat.eq_dec j (S p)) as [-> | HjS].
    + exfalso. apply Hcross. auto.
    + rewrite t42_sw_p, t42_sw_other by lia. lia.
  - destruct (Nat.eq_dec i (S p)) as [-> | HiS].
    + rewrite t42_sw_Sp, t42_sw_other by lia. lia.
    + destruct (Nat.eq_dec j p) as [-> | Hjp].
      * rewrite t42_sw_other by assumption. rewrite t42_sw_p. lia.
      * destruct (Nat.eq_dec j (S p)) as [-> | HjS].
        -- rewrite t42_sw_other by assumption. rewrite t42_sw_Sp. lia.
        -- rewrite t42_sw_other by assumption. rewrite t42_sw_other by assumption. lia.
Qed.

Lemma t42_swap_run_length X p : length (t42_swap_run X p) = length X.
Proof.
  revert X. induction p as [|p IH]; intros X.
  - destruct X as [|a [|b X]]; reflexivity.
  - destruct X as [|a X]; [reflexivity |]. simpl. rewrite IH. reflexivity.
Qed.

Lemma t42_swap_run_split (A B : run) a b p :
  length A = p ->
  t42_swap_run (A ++ a :: b :: B) p = A ++ b :: a :: B.
Proof.
  revert p. induction A as [|x A IH]; intros p Hlen.
  - simpl in Hlen. subst p. reflexivity.
  - destruct p as [|p]; [simpl in Hlen; discriminate |].
    simpl in Hlen. simpl. f_equal. apply IH. lia.
Qed.

Lemma t42_nth_error_app_here {A : Type} (pre : list A) a rest :
  nth_error (pre ++ a :: rest) (length pre) = Some a.
Proof.
  induction pre as [|x pre IH]; [reflexivity |]. simpl. exact IH.
Qed.

Lemma t42_adjacent_at X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 ->
  at_ X p t1 e1 /\ at_ X (S p) t2 e2.
Proof.
  intros [A [B [Hlen ->]]]. unfold at_. split.
  - rewrite <- Hlen. apply t42_nth_error_app_here.
  - replace (S p) with (S (length A + 0)) by lia.
    rewrite t42_nth_after_prefix. reflexivity.
Qed.

Lemma t42_adjacent_bound X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> S p < length X.
Proof.
  intro Hadj. destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [_ H].
  unfold at_ in H. eapply t42_nth_error_lt; eauto.
Qed.

Lemma t42_adjacent_swap X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 ->
  t42_adjacent (t42_swap_run X p) p t2 e2 t1 e1.
Proof.
  intros [A [B [Hlen ->]]]. exists A, B. split; [exact Hlen |].
  rewrite t42_swap_run_split by exact Hlen. reflexivity.
Qed.

Lemma t42_swap_run_involutive X p :
  S p < length X -> t42_swap_run (t42_swap_run X p) p = X.
Proof.
  revert X. induction p as [|p IH]; intros X Hbound.
  - destruct X as [|a [|b X]]; simpl in Hbound; try lia. reflexivity.
  - destruct X as [|a X]; simpl in Hbound; [lia |].
    simpl. f_equal. apply IH. lia.
Qed.

Lemma t42_nth_error_swap X p i :
  S p < length X ->
  nth_error (t42_swap_run X p) (t42_sw p i) = nth_error X i.
Proof.
  revert X i. induction p as [|p IH]; intros X i Hbound.
  - destruct X as [|a [|b X]]; simpl in Hbound; try lia.
    destruct i as [|[|i]]; reflexivity.
  - destruct X as [|a X]; simpl in Hbound; [lia |].
    destruct i as [|i]; [reflexivity |]. simpl. apply IH. lia.
Qed.

Lemma t42_at_swap_iff X p t1 e1 t2 e2 i t e :
  t42_adjacent X p t1 e1 t2 e2 ->
  (at_ (t42_swap_run X p) (t42_sw p i) t e <-> at_ X i t e).
Proof.
  intro Hadj. unfold at_. rewrite t42_nth_error_swap.
  - reflexivity.
  - eapply t42_adjacent_bound; eauto.
Qed.

Lemma t42_at_swap_reverse X p t1 e1 t2 e2 i t e :
  t42_adjacent X p t1 e1 t2 e2 ->
  (at_ (t42_swap_run X p) i t e <-> at_ X (t42_sw p i) t e).
Proof.
  intro Hadj.
  pose proof (t42_at_swap_iff X p t1 e1 t2 e2 (t42_sw p i) t e Hadj) as H.
  rewrite t42_sw_involutive in H. exact H.
Qed.

Lemma t42_proj_pair_swap t1 e1 t2 e2 t :
  t1 <> t2 ->
  proj [(t2, e2); (t1, e1)] t = proj [(t1, e1); (t2, e2)] t.
Proof.
  intro Hdiff. unfold proj. simpl.
  destruct (Nat.eqb t1 t) eqn:H1; destruct (Nat.eqb t2 t) eqn:H2;
    try reflexivity.
  apply Nat.eqb_eq in H1. apply Nat.eqb_eq in H2. subst. contradiction.
Qed.

Lemma t42_proj_swap X p t1 e1 t2 e2 t :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  proj (t42_swap_run X p) t = proj X t.
Proof.
  intros [A [B [Hlen ->]]] Hdiff.
  rewrite t42_swap_run_split by exact Hlen.
  change
    (proj (A ++ ([(t2, e2); (t1, e1)] ++ B)) t =
     proj (A ++ ([(t1, e1); (t2, e2)] ++ B)) t).
  repeat rewrite t42_proj_app. rewrite t42_proj_pair_swap by exact Hdiff. reflexivity.
Qed.

Lemma t42_proj_cons_congr u d (A B : run) t :
  proj A t = proj B t -> proj ((u, d) :: A) t = proj ((u, d) :: B) t.
Proof.
  unfold proj. simpl. destruct (Nat.eqb u t); simpl; intro H; now rewrite H.
Qed.

Lemma t42_proj_prefix_swap X p t1 e1 t2 e2 i t e :
  at_ X p t1 e1 -> at_ X (S p) t2 e2 -> t1 <> t2 ->
  at_ X i t e ->
  proj (firstn (t42_sw p i) (t42_swap_run X p)) t = proj (firstn i X) t.
Proof.
  revert X i. induction p as [|p IH]; intros X i H1 H2 Hdiff Hi.
  - destruct X as [|[u1 d1] [|[u2 d2] X]]; unfold at_ in H1, H2; simpl in H1, H2;
      try discriminate.
    inversion H1. inversion H2. subst u1 d1 u2 d2.
    destruct i as [|[|i]].
    + unfold at_ in Hi. simpl in Hi. inversion Hi. subst t e.
      simpl. unfold proj. simpl. destruct (Nat.eqb t2 t1) eqn:Hb; [|reflexivity].
      apply Nat.eqb_eq in Hb. exfalso. apply Hdiff. symmetry. exact Hb.
    + unfold at_ in Hi. simpl in Hi. inversion Hi. subst t e.
      simpl. unfold proj. simpl. destruct (Nat.eqb t1 t2) eqn:Hb; [|reflexivity].
      apply Nat.eqb_eq in Hb. exfalso. apply Hdiff. exact Hb.
    + simpl. change
        (proj ([(t2, e2); (t1, e1)] ++ firstn i X) t =
         proj ([(t1, e1); (t2, e2)] ++ firstn i X) t).
      repeat rewrite t42_proj_app. rewrite t42_proj_pair_swap by exact Hdiff. reflexivity.
  - destruct X as [|[u d] X]; unfold at_ in H1, H2, Hi; simpl in H1, H2, Hi;
      try discriminate.
    destruct i as [|i].
    + reflexivity.
    + simpl. apply t42_proj_cons_congr. apply IH; assumption.
Qed.

Lemma t42_event_order_swap X p t1 e1 t2 e2 i j t e d :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  at_ X i t e -> at_ X j t d -> i < j ->
  t42_sw p i < t42_sw p j.
Proof.
  intros Hadj Hdiff Hati Hatj Hij. apply t42_sw_order; [exact Hij |].
  intros [-> ->].
  destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [H1 H2].
  pose proof (proj1 (t42_at_unique X p t1 e1 t e H1 Hati)) as Ht1.
  pose proof (proj1 (t42_at_unique X (S p) t2 e2 t d H2 Hatj)) as Ht2.
  apply Hdiff. congruence.
Qed.

Lemma t42_interval_swap X p t1 e1 t2 e2 i t e :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 -> at_ X i t e ->
  interval (t42_swap_run X p) t (t42_sw p i) = interval X t i.
Proof.
  intros Hadj Hdiff Hat. unfold interval.
  destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [H1 H2].
  rewrite (t42_proj_prefix_swap X p t1 e1 t2 e2 i t e H1 H2 Hdiff Hat).
  reflexivity.
Qed.

Lemma t42_inside_swap X p t1 e1 t2 e2 i t e :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 -> at_ X i t e ->
  inside (t42_swap_run X p) t (t42_sw p i) = inside X t i.
Proof.
  intros Hadj Hdiff Hat. unfold inside.
  destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [H1 H2].
  rewrite (t42_proj_prefix_swap X p t1 e1 t2 e2 i t e H1 H2 Hdiff Hat).
  reflexivity.
Qed.

Lemma t42_owned_swap X p t1 e1 t2 e2 i t e l :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 -> at_ X i t e ->
  (owned (t42_swap_run X p) t (t42_sw p i) l <-> owned X t i l).
Proof.
  intros Hadj Hdiff Hati. unfold owned. split.
  - intros [k [Hki [Hatk Heq]]].
    exists (t42_sw p k). split.
    + pose proof (t42_event_order_swap (t42_swap_run X p) p t2 e2 t1 e1
        k (t42_sw p i) t (Own l) e
        (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence)
        Hatk ltac:(apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t e Hadj)); exact Hati)
        Hki) as Hord.
      rewrite t42_sw_involutive in Hord. exact Hord.
    + split.
      * apply (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 k t (Own l) Hadj)). exact Hatk.
      * assert (HatkX : at_ X (t42_sw p k) t (Own l)).
        { apply (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 k t (Own l) Hadj)). exact Hatk. }
        pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p k) t (Own l)
          Hadj Hdiff HatkX) as HIk.
        pose proof (t42_interval_swap X p t1 e1 t2 e2 i t e Hadj Hdiff Hati) as HIi.
        rewrite t42_sw_involutive in HIk. rewrite HIk, HIi in Heq. exact Heq.
  - intros [j [Hji [Hatj Heq]]].
    exists (t42_sw p j). split.
    + eapply t42_event_order_swap; eauto.
    + split.
      * apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t (Own l) Hadj)). exact Hatj.
      * rewrite (t42_interval_swap X p t1 e1 t2 e2 j t (Own l) Hadj Hdiff Hatj).
        rewrite (t42_interval_swap X p t1 e1 t2 e2 i t e Hadj Hdiff Hati).
        exact Heq.
Qed.

Lemma t42_sw_lt_length p n i :
  S p < n -> i < n -> t42_sw p i < n.
Proof.
  intros Hp Hi.
  destruct (Nat.eq_dec i p) as [-> | Hip].
  - rewrite t42_sw_p. lia.
  - destruct (Nat.eq_dec i (S p)) as [-> | HiS].
    + rewrite t42_sw_Sp. lia.
    + rewrite t42_sw_other by assumption. exact Hi.
Qed.

Lemma t42_sw_length p n :
  S p < n -> t42_sw p n = n.
Proof.
  intro H. apply t42_sw_other; lia.
Qed.

Lemma t42_written_loc e l v :
  written e = Some (l, v) -> loc_of e = Some l.
Proof.
  destruct e as
    [l0 v0 | l0 v0 | l0 v0 | k f a l0 old | c l0 v0 | c l0 v0 |
     c | l0 | | | w | w n |]; simpl; try congruence.
  destruct (sa_new k a old); congruence.
Qed.

Lemma t42_read_value_loc e l v :
  read_value e = Some (l, v) -> loc_of e = Some l.
Proof.
  destruct e; simpl; congruence.
Qed.

Lemma t42_events_conflict_sym e1 e2 :
  t42_events_conflict e1 e2 -> t42_events_conflict e2 e1.
Proof.
  intros [l [H1 [H2 [Hwrite | Hwrite]]]].
  - exists l. repeat split; auto.
  - exists l. repeat split; auto.
Qed.

Lemma t42_access_order_swap X p t1 e1 t2 e2 i j u d v e l :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  at_ X i u d -> at_ X j v e ->
  loc_of d = Some l -> loc_of e = Some l ->
  ((exists w, written d = Some (l, w)) \/
   (exists w, written e = Some (l, w))) ->
  i < j -> t42_sw p i < t42_sw p j.
Proof.
  intros Hadj Hsafe Hati Hatj Hdi Hej Hwrite Hij.
  apply t42_sw_order; [exact Hij |].
  intros [-> ->].
  destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [H1 H2].
  destruct (t42_at_unique X p t1 e1 u d H1 Hati) as [_ Hd].
  destruct (t42_at_unique X (S p) t2 e2 v e H2 Hatj) as [_ He].
  apply Hsafe. exists l. subst d e. repeat split; assumption.
Qed.

Lemma t42_cpu_sync_swap_forward X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) ->
  cpu_sync X i j ->
  cpu_sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j).
Proof.
  intros Hadj Hdiff Hnos Hcpu. inversion Hcpu; subst.
  - eapply cpu_po.
    + eapply t42_event_order_swap; eauto.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t e Hadj)); assumption.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t e' Hadj)); assumption.
  - eapply cpu_fence.
    + apply t42_sw_order; [assumption |]. intros [-> ->].
      apply Hnos. apply sync_cpu. eapply cpu_fence; eauto.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t
        (Shared k true a l v) Hadj)); assumption.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t'
        (Shared k' true a' l' v') Hadj)); assumption.
Qed.

Lemma t42_cpu_sync_swap_iff X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  (cpu_sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j) <->
   cpu_sync X i j).
Proof.
  intros Hadj Hdiff Hnos Hnos' . split.
  - intro H.
    pose proof (t42_cpu_sync_swap_forward (t42_swap_run X p) p t2 e2 t1 e1
      (t42_sw p i) (t42_sw p j)
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence) Hnos' H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    repeat rewrite t42_sw_involutive in K. exact K.
  - apply (t42_cpu_sync_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_omp_sync_swap_forward X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) ->
  omp_sync X i j ->
  omp_sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j).
Proof.
  intros Hadj Hdiff Hnos Homp. inversion Homp; subst.
  - eapply omp_sync_barrier.
    + apply t42_sw_order; [assumption |]. intros [-> ->].
      apply Hnos. apply sync_omp. eapply omp_sync_barrier; eauto.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t Barrier Hadj)); assumption.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t' e Hadj)); assumption.
    + rewrite (t42_interval_swap X p t1 e1 t2 e2 i t Barrier Hadj Hdiff ltac:(assumption)).
      rewrite (t42_interval_swap X p t1 e1 t2 e2 j t' e Hadj Hdiff ltac:(assumption)).
      assumption.
  - eapply omp_sync_critical.
    + apply t42_sw_order; [assumption |]. intros [-> ->].
      apply Hnos. apply sync_omp. eapply omp_sync_critical; eauto.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t Exit Hadj)); assumption.
    + apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t' Enter Hadj)); assumption.
Qed.

Lemma t42_omp_sync_swap_iff X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  (omp_sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j) <->
   omp_sync X i j).
Proof.
  intros Hadj Hdiff Hnos Hnos'. split.
  - intro H.
    pose proof (t42_omp_sync_swap_forward (t42_swap_run X p) p t2 e2 t1 e1
      (t42_sw p i) (t42_sw p j)
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence) Hnos' H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    repeat rewrite t42_sw_involutive in K. exact K.
  - apply (t42_omp_sync_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_sync_swap_forward X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) ->
  sync X i j -> sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j).
Proof.
  intros Hadj Hdiff Hnos H. inversion H; subst.
  - apply sync_cpu. eapply t42_cpu_sync_swap_forward; eauto.
  - apply sync_omp. eapply t42_omp_sync_swap_forward; eauto.
Qed.

Lemma t42_sync_swap_iff X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  (sync (t42_swap_run X p) (t42_sw p i) (t42_sw p j) <-> sync X i j).
Proof.
  intros Hadj Hdiff Hnos Hnos'. split.
  - intro H.
    pose proof (t42_sync_swap_forward (t42_swap_run X p) p t2 e2 t1 e1
      (t42_sw p i) (t42_sw p j)
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence) Hnos' H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    repeat rewrite t42_sw_involutive in K. exact K.
  - apply (t42_sync_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_clos_trans_map (R S : nat -> nat -> Prop) (f : nat -> nat) :
  (forall i j, R i j -> S (f i) (f j)) ->
  forall i j, clos_trans nat R i j -> clos_trans nat S (f i) (f j).
Proof.
  intros Hmap i j H. induction H.
  - apply t_step. now apply Hmap.
  - eapply t_trans; eauto.
Qed.

Lemma t42_hb_cpu_swap_forward X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> hb_cpu X i j ->
  hb_cpu (t42_swap_run X p) (t42_sw p i) (t42_sw p j).
Proof.
  intros Hadj Hdiff Hnos H. unfold hb_cpu in *.
  eapply t42_clos_trans_map; [|exact H].
  intros a b Hab. eapply t42_cpu_sync_swap_forward; eauto.
Qed.

Lemma t42_hb_cpu_swap_iff X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  (hb_cpu (t42_swap_run X p) (t42_sw p i) (t42_sw p j) <-> hb_cpu X i j).
Proof.
  intros Hadj Hdiff Hnos Hnos'. split.
  - intro H.
    pose proof (t42_hb_cpu_swap_forward (t42_swap_run X p) p t2 e2 t1 e1
      (t42_sw p i) (t42_sw p j)
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence) Hnos' H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    repeat rewrite t42_sw_involutive in K. exact K.
  - apply (t42_hb_cpu_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_hb_swap_forward X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> hb X i j ->
  hb (t42_swap_run X p) (t42_sw p i) (t42_sw p j).
Proof.
  intros Hadj Hdiff Hnos H. unfold hb in *.
  eapply t42_clos_trans_map; [|exact H].
  intros a b Hab. eapply t42_sync_swap_forward; eauto.
Qed.

Lemma t42_hb_swap_iff X p t1 e1 t2 e2 i j :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  (hb (t42_swap_run X p) (t42_sw p i) (t42_sw p j) <-> hb X i j).
Proof.
  intros Hadj Hdiff Hnos Hnos'. split.
  - intro H.
    pose proof (t42_hb_swap_forward (t42_swap_run X p) p t2 e2 t1 e1
      (t42_sw p i) (t42_sw p j)
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence) Hnos' H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    repeat rewrite t42_sw_involutive in K. exact K.
  - apply (t42_hb_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_writes_swap X p t1 e1 t2 e2 i l v :
  t42_adjacent X p t1 e1 t2 e2 ->
  (writes (t42_swap_run X p) (t42_sw p i) l v <-> writes X i l v).
Proof.
  intro Hadj. unfold writes. split.
  - intros [t [e [Hat Hwrite]]]. exists t, e. split; [|exact Hwrite].
    apply (proj1 (t42_at_swap_iff X p t1 e1 t2 e2 i t e Hadj)). exact Hat.
  - intros [t [e [Hat Hwrite]]]. exists t, e. split; [|exact Hwrite].
    apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 i t e Hadj)). exact Hat.
Qed.

Lemma t42_writes_order_swap X p t1 e1 t2 e2 i j l v w :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  writes X i l v -> writes X j l w -> i < j ->
  t42_sw p i < t42_sw p j.
Proof.
  intros Hadj Hsafe [u [d [Hati Hdi]]] [u' [d' [Hatj Hdj]]] Hij.
  eapply t42_access_order_swap; eauto using t42_written_loc.
Qed.

Lemma t42_write_read_order_swap X p t1 e1 t2 e2 i j l v w t e :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  writes X i l w -> at_ X j t e -> read_value e = Some (l, v) -> i < j ->
  t42_sw p i < t42_sw p j.
Proof.
  intros Hadj Hsafe [u [d [Hati Hdi]]] Hatj Hread Hij.
  eapply t42_access_order_swap; eauto using t42_written_loc, t42_read_value_loc.
Qed.

Lemma t42_swap_rf_apply p rf i :
  t42_swap_rf p rf (t42_sw p i) = option_map (t42_sw p) (rf i).
Proof.
  unfold t42_swap_rf. rewrite t42_sw_involutive. reflexivity.
Qed.

Lemma t42_swap_rf_some p rf i s :
  t42_swap_rf p rf (t42_sw p i) = Some (t42_sw p s) <-> rf i = Some s.
Proof.
  rewrite t42_swap_rf_apply. destruct (rf i) as [q|] eqn:Hq; simpl.
  - split; intro H; [|inversion H; reflexivity].
    inversion H. apply t42_sw_injective in H1. subst q. reflexivity.
  - split; discriminate.
Qed.

Lemma t42_swap_rf_none p rf i :
  t42_swap_rf p rf (t42_sw p i) = None <-> rf i = None.
Proof.
  rewrite t42_swap_rf_apply. destruct (rf i); simpl; split; congruence.
Qed.

Lemma t42_source_ok_read_swap_forward X rf p t1 e1 t2 e2 j t e l v :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  at_ X j t e -> read_value e = Some (l, v) ->
  source_ok X l v (rf j) j ->
  source_ok (t42_swap_run X p) l v
    (t42_swap_rf p rf (t42_sw p j)) (t42_sw p j).
Proof.
  intros Hadj Hsafe Hat Hread Hsource. unfold source_ok in *.
  destruct (rf j) as [s|] eqn:Hs.
  - destruct Hsource as [Hsj Hwrite]. rewrite t42_swap_rf_apply, Hs. simpl.
    split.
    + eapply t42_write_read_order_swap; eauto.
    + apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 s l v Hadj)). exact Hwrite.
  - rewrite t42_swap_rf_apply, Hs. simpl. exact Hsource.
Qed.

Lemma t42_source_ok_length_swap_forward X rf p t1 e1 t2 e2 l v j :
  t42_adjacent X p t1 e1 t2 e2 ->
  source_ok X l v (rf j) (length X) ->
  source_ok (t42_swap_run X p) l v
    (t42_swap_rf p rf (t42_sw p j)) (length (t42_swap_run X p)).
Proof.
  intros Hadj Hsource. unfold source_ok in *.
  destruct (rf j) as [s|] eqn:Hs.
  - destruct Hsource as [Hslen Hwrite]. rewrite t42_swap_rf_apply, Hs. simpl.
    split.
    + rewrite t42_swap_run_length. eapply t42_sw_lt_length; eauto.
      eapply t42_adjacent_bound; eauto.
    + apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 s l v Hadj)). exact Hwrite.
  - rewrite t42_swap_rf_apply, Hs. simpl. exact Hsource.
Qed.

Definition t42_rf_valid (X : run) (rf : rf_map) : Prop :=
  forall j t e l v s, at_ X j t e -> read_value e = Some (l, v) ->
    rf j = Some s -> exists w, writes X s l w.

Lemma t42_rf_valid_swap_forward X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t42_rf_valid X rf ->
  t42_rf_valid (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hvalid j t e l v s Hat Hread Hrf.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t e Hadj) Hat) as HatX.
  unfold t42_swap_rf in Hrf.
  destruct (rf (t42_sw p j)) as [q|] eqn:Hq; simpl in Hrf; [|discriminate].
  inversion Hrf. subst s.
  destruct (Hvalid (t42_sw p j) t e l v q HatX Hread Hq) as [w Hwrite].
  exists w. apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 q l w Hadj)). exact Hwrite.
Qed.

Lemma t42_latest_swap_forward X p t1 e1 t2 e2 j t e l v s :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  at_ X j t e -> read_value e = Some (l, v) ->
  (match s with None => True | Some q => exists w, writes X q l w end) ->
  latest X l j s ->
  latest (t42_swap_run X p) l (t42_sw p j) (option_map (t42_sw p) s).
Proof.
  intros Hadj Hdiff Hsafe Hat Hread Hsource Hlatest.
  destruct s as [s|].
  - simpl in Hsource, Hlatest |- *. destruct Hsource as [w Hwrites].
    destruct Hlatest as [Hsj Hnew]. split.
    + eapply t42_write_read_order_swap; eauto.
    + intros q w' Hbetween Hwriteq.
      apply (Hnew (t42_sw p q) w').
      * split.
        -- rewrite <- (t42_sw_involutive p s).
           apply (t42_writes_order_swap (t42_swap_run X p) p t2 e2 t1 e1
             (t42_sw p s) q l w w').
           ++ apply t42_adjacent_swap. exact Hadj.
           ++ intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
           ++ apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 s l w Hadj)). exact Hwrites.
           ++ exact Hwriteq.
           ++ exact (proj1 Hbetween).
        -- rewrite <- (t42_sw_involutive p j).
           apply (t42_write_read_order_swap (t42_swap_run X p) p t2 e2 t1 e1
             q (t42_sw p j) l v w' t e).
           ++ apply t42_adjacent_swap. exact Hadj.
           ++ intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
           ++ exact Hwriteq.
           ++ apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t e Hadj)). exact Hat.
           ++ exact Hread.
           ++ exact (proj2 Hbetween).
      * apply (proj1 (t42_writes_swap X p t1 e1 t2 e2 (t42_sw p q) l w' Hadj)).
        rewrite t42_sw_involutive. exact Hwriteq.
  - simpl in Hlatest |- *. intros q w Hq Hwriteq.
    apply (Hlatest (t42_sw p q) w).
    + rewrite <- (t42_sw_involutive p j).
      apply (t42_write_read_order_swap (t42_swap_run X p) p t2 e2 t1 e1
        q (t42_sw p j) l v w t e).
      * apply t42_adjacent_swap. exact Hadj.
      * intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
      * exact Hwriteq.
      * apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 j t e Hadj)). exact Hat.
      * exact Hread.
      * exact Hq.
    + apply (proj1 (t42_writes_swap X p t1 e1 t2 e2 (t42_sw p q) l w Hadj)).
      rewrite t42_sw_involutive. exact Hwriteq.
Qed.

Lemma t42_source_latest_swap_forward X rf p t1 e1 t2 e2 j t e l v :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  at_ X j t e -> read_value e = Some (l, v) ->
  source_ok X l v (rf j) j /\ latest X l j (rf j) ->
  source_ok (t42_swap_run X p) l v
      (t42_swap_rf p rf (t42_sw p j)) (t42_sw p j) /\
    latest (t42_swap_run X p) l (t42_sw p j)
      (t42_swap_rf p rf (t42_sw p j)).
Proof.
  intros Hadj Hdiff Hsafe Hat Hread [Hsource Hlatest]. split.
  - eapply t42_source_ok_read_swap_forward; eauto.
  - rewrite t42_swap_rf_apply.
    eapply t42_latest_swap_forward; eauto.
    unfold source_ok in Hsource. destruct (rf j); simpl in *; intuition eauto.
Qed.

Lemma t42_not_older_swap_forward X rf p t1 e1 t2 e2 j i l v :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  (match rf j with None => True | Some s => exists w, writes X s l w end) ->
  writes X i l v -> not_older (rf j) i ->
  not_older (t42_swap_rf p rf (t42_sw p j)) (t42_sw p i).
Proof.
  intros Hadj Hsafe Hsource Hwrite Holder.
  unfold not_older in *. destruct (rf j) as [s|] eqn:Hs; [|contradiction].
  simpl in Hsource, Holder |- *. rewrite t42_swap_rf_apply, Hs. simpl.
  destruct Hsource as [w Hwrites]. destruct (Nat.eq_dec i s) as [-> | Hneq].
  - lia.
  - assert (i < s) by lia. eapply Nat.lt_le_incl.
    eapply t42_writes_order_swap; eauto.
Qed.

Lemma t42_source_ok_some_write X l v s bound :
  source_ok X l v (Some s) bound -> exists w, writes X s l w.
Proof.
  unfold source_ok. intros [_ Hwrite]. exists v. exact Hwrite.
Qed.

Lemma t42_model_rf_valid X rf :
  memory_ok X rf -> device_ok X rf -> t42_rf_valid X rf.
Proof.
  intros [Hcpu Hshared] Hdevice j t e l v s Hat Hread Hrf.
  destruct e as
    [l0 v0 | l0 v0 | l0 v0 | k f a l0 old | c l0 v0 | c l0 v0 |
     c | l0 | | | w | w n |]; simpl in Hread; try discriminate.
  - inversion Hread. subst l0 v0. destruct (Hcpu j t l v (or_introl Hat)) as [Hsource _].
    rewrite Hrf in Hsource. eapply t42_source_ok_some_write; eauto.
  - inversion Hread. subst l0 v0. destruct (Hcpu j t l v (or_intror Hat)) as [Hsource _].
    rewrite Hrf in Hsource. eapply t42_source_ok_some_write; eauto.
  - inversion Hread. subst l0 old. destruct (Hshared j t k f a l v Hat) as [Hsource _].
    rewrite Hrf in Hsource. eapply t42_source_ok_some_write; eauto.
  - inversion Hread. subst l0 v0. destruct (Hdevice j t c l v Hat) as [[Hsource _] _].
    rewrite Hrf in Hsource. eapply t42_source_ok_some_write; eauto.
Qed.

Lemma t42_seen_swap_backward
    (H H' : nat -> nat -> Prop) X rf p t1 e1 t2 e2 j l k :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  (forall a b, H' a b -> H (t42_sw p a) (t42_sw p b)) ->
  t42_rf_valid (t42_swap_run X p) (t42_swap_rf p rf) ->
  seen H' (t42_swap_run X p) (t42_swap_rf p rf) (t42_sw p j) l k ->
  seen H X rf j l (t42_sw p k).
Proof.
  intros Hadj Hdiff Hsafe Hrel Hvalid Hseen.
  destruct Hseen as [[wk Hwritek] Hreason]. split.
  - exists wk. apply (proj1 (t42_writes_swap X p t1 e1 t2 e2
      (t42_sw p k) l wk Hadj)). rewrite t42_sw_involutive. exact Hwritek.
  - destruct Hreason as [Hedge | Hprior].
    + left. specialize (Hrel k (t42_sw p j) Hedge).
    rewrite t42_sw_involutive in Hrel. exact Hrel.
    + right. destruct Hprior as
      [r [u [d [d' [vr [s [Hrj [Hatr [Hatj [Hread [Hrfs Hks]]]]]]]]]]].
      pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 r u d Hadj) Hatr) as HatrX.
      pose proof (proj1 (t42_at_swap_iff X p t1 e1 t2 e2 j u d' Hadj) Hatj) as HatjX.
      pose proof (t42_event_order_swap (t42_swap_run X p) p t2 e2 t1 e1
        r (t42_sw p j) u d d'
        (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence)
        Hatr Hatj Hrj) as HrjX.
      rewrite t42_sw_involutive in HrjX.
      destruct (Hvalid r u d l vr s Hatr Hread Hrfs) as [ws Hwrites].
      unfold t42_swap_rf in Hrfs.
      destruct (rf (t42_sw p r)) as [q|] eqn:Hrfq; simpl in Hrfs; [|discriminate].
      inversion Hrfs. subst s.
      exists (t42_sw p r), u, d, d', vr, q. repeat split; try assumption.
      destruct (Nat.eq_dec k (t42_sw p q)) as [-> | Hneq].
      * rewrite t42_sw_involutive. lia.
      * assert (Hkq : k < t42_sw p q) by lia.
        apply Nat.lt_le_incl.
        rewrite <- (t42_sw_involutive p q).
        apply (t42_writes_order_swap (t42_swap_run X p) p t2 e2 t1 e1
          k (t42_sw p q) l wk ws).
        -- apply t42_adjacent_swap. exact Hadj.
        -- intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
        -- exact Hwritek.
        -- exact Hwrites.
        -- exact Hkq.
Qed.

Lemma t42_seen_not_older_swap_forward
    (H H' : nat -> nat -> Prop) X rf p t1 e1 t2 e2 j t e l v :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  (forall a b, H' a b -> H (t42_sw p a) (t42_sw p b)) ->
  t42_rf_valid X rf -> at_ X j t e -> read_value e = Some (l, v) ->
  (forall i, seen H X rf j l i -> not_older (rf j) i) ->
  forall k, seen H' (t42_swap_run X p) (t42_swap_rf p rf)
      (t42_sw p j) l k ->
    not_older (t42_swap_rf p rf (t42_sw p j)) k.
Proof.
  intros Hadj Hdiff Hsafe Hrel Hvalid Hat Hread Holder k Hseen.
  pose proof (t42_rf_valid_swap_forward X rf p t1 e1 t2 e2 Hadj Hvalid) as Hvalid'.
  pose proof (t42_seen_swap_backward H H' X rf p t1 e1 t2 e2 j l k
    Hadj Hdiff Hsafe Hrel Hvalid' Hseen) as HseenX.
  pose proof (Holder (t42_sw p k) HseenX) as HoldX.
  destruct HseenX as [[wk Hwritek] _].
  assert (Hsource : match rf j with
    | None => True | Some s => exists w, writes X s l w end).
  { destruct (rf j) as [s|] eqn:Hrfj; [|exact I].
    eapply Hvalid; eauto. }
  pose proof (t42_not_older_swap_forward X rf p t1 e1 t2 e2 j
    (t42_sw p k) l wk Hadj Hsafe Hsource Hwritek HoldX) as K.
  rewrite t42_sw_involutive in K. exact K.
Qed.

Lemma t42_read_ok_swap_forward
    (H H' : nat -> nat -> Prop) X rf p t1 e1 t2 e2 j t e l v :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  (forall a b, H' a b -> H (t42_sw p a) (t42_sw p b)) ->
  t42_rf_valid X rf -> at_ X j t e -> read_value e = Some (l, v) ->
  read_ok H X rf j l v j ->
  read_ok H' (t42_swap_run X p) (t42_swap_rf p rf)
    (t42_sw p j) l v (t42_sw p j).
Proof.
  intros Hadj Hdiff Hsafe Hrel Hvalid Hat Hread [Hsource Holder]. split.
  - eapply t42_source_ok_read_swap_forward; eauto.
  - eapply t42_seen_not_older_swap_forward; eauto.
Qed.

Lemma t42_read_ok_length_swap_forward
    (H H' : nat -> nat -> Prop) X rf p t1 e1 t2 e2 j t e l v :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  (forall a b, H' a b -> H (t42_sw p a) (t42_sw p b)) ->
  t42_rf_valid X rf -> at_ X j t e -> read_value e = Some (l, v) ->
  read_ok H X rf j l v (length X) ->
  read_ok H' (t42_swap_run X p) (t42_swap_rf p rf)
    (t42_sw p j) l v (length (t42_swap_run X p)).
Proof.
  intros Hadj Hdiff Hsafe Hrel Hvalid Hat Hread [Hsource Holder]. split.
  - eapply t42_source_ok_length_swap_forward; eauto.
  - eapply t42_seen_not_older_swap_forward; eauto.
Qed.

Lemma t42_hb_cpu_swap_backward X p t1 e1 t2 e2 a b :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  hb_cpu (t42_swap_run X p) a b -> hb_cpu X (t42_sw p a) (t42_sw p b).
Proof.
  intros Hadj Hdiff Hnos Hnos' H.
  pose proof (t42_hb_cpu_swap_iff X p t1 e1 t2 e2
    (t42_sw p a) (t42_sw p b) Hadj Hdiff Hnos Hnos') as K.
  repeat rewrite t42_sw_involutive in K. now apply (proj1 K).
Qed.

Lemma t42_hb_swap_backward X p t1 e1 t2 e2 a b :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  hb (t42_swap_run X p) a b -> hb X (t42_sw p a) (t42_sw p b).
Proof.
  intros Hadj Hdiff Hnos Hnos' H.
  pose proof (t42_hb_swap_iff X p t1 e1 t2 e2
    (t42_sw p a) (t42_sw p b) Hadj Hdiff Hnos Hnos') as K.
  repeat rewrite t42_sw_involutive in K. now apply (proj1 K).
Qed.

Lemma t42_sw_reverse_pair p i j :
  i < j -> ~ t42_sw p i < t42_sw p j -> i = p /\ j = S p.
Proof.
  intros Hij Hrev. destruct (Nat.eq_dec i p) as [-> | Hip].
  - destruct (Nat.eq_dec j (S p)) as [-> | Hj]; [auto |].
    exfalso. apply Hrev. apply t42_sw_order; [exact Hij |].
    intros [_ Heq]. apply Hj. exact Heq.
  - exfalso. apply Hrev. apply t42_sw_order; [exact Hij |].
    intros [Hi _]. apply Hip. exact Hi.
Qed.

Lemma t42_filter_adjacent_length {A : Type} (f : A -> bool) pre a b post :
  length (filter f (pre ++ a :: b :: post)) =
  length (filter f (pre ++ b :: a :: post)).
Proof.
  repeat rewrite filter_app. simpl. destruct (f a), (f b); simpl;
    repeat rewrite app_length; simpl; lia.
Qed.

Lemma t42_count_iter_swap X p t1 e1 t2 e2 w i :
  t42_adjacent X p t1 e1 t2 e2 ->
  count_iter (t42_swap_run X p) w i = count_iter X w i.
Proof.
  intros [A [B [Hlen ->]]]. rewrite t42_swap_run_split by exact Hlen.
  unfold count_iter. symmetry. apply t42_filter_adjacent_length.
Qed.

Lemma t42_memory_ok_swap X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  ~ t42_events_conflict e1 e2 ->
  memory_ok X rf -> device_ok X rf ->
  memory_ok (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hdiff Hnos Hnos' Hsafe Hmemory Hdevice.
  destruct Hmemory as [Hcpu Hshared].
  pose proof (t42_model_rf_valid X rf (conj Hcpu Hshared) Hdevice) as Hvalid.
  split.
  - intros j t l v [Hat | Hat].
    + pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t (Read l v) Hadj) Hat)
        as HatX.
      pose proof (Hcpu (t42_sw p j) t l v (or_introl HatX)) as Hok.
      pose proof (t42_read_ok_swap_forward (hb_cpu X) (hb_cpu (t42_swap_run X p))
        X rf p t1 e1 t2 e2 (t42_sw p j) t (Read l v) l v
        Hadj Hdiff Hsafe
        ltac:(intros a b H; eapply t42_hb_cpu_swap_backward; eauto)
        Hvalid HatX ltac:(reflexivity) Hok) as K.
      rewrite t42_sw_involutive in K. exact K.
    + pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t (HistoryRead l v) Hadj) Hat)
        as HatX.
      pose proof (Hcpu (t42_sw p j) t l v (or_intror HatX)) as Hok.
      pose proof (t42_read_ok_swap_forward (hb_cpu X) (hb_cpu (t42_swap_run X p))
        X rf p t1 e1 t2 e2 (t42_sw p j) t (HistoryRead l v) l v
        Hadj Hdiff Hsafe
        ltac:(intros a b H; eapply t42_hb_cpu_swap_backward; eauto)
        Hvalid HatX ltac:(reflexivity) Hok) as K.
      rewrite t42_sw_involutive in K. exact K.
  - intros j t k f a l old Hat.
    pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t
      (Shared k f a l old) Hadj) Hat) as HatX.
    pose proof (Hshared (t42_sw p j) t k f a l old HatX) as Hok.
    pose proof (t42_source_latest_swap_forward X rf p t1 e1 t2 e2
      (t42_sw p j) t (Shared k f a l old) l old Hadj Hdiff Hsafe
      HatX ltac:(reflexivity) Hok) as K.
    rewrite t42_sw_involutive in K. exact K.
Qed.

Lemma t42_omp_ok_swap X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  ~ t42_events_conflict e1 e2 ->
  memory_ok X rf -> device_ok X rf -> omp_ok X rf ->
  omp_ok (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hdiff Hnos Hnos' Hsafe Hmemory Hdevice Homp.
  destruct Homp as [Hread [Hthreads [Hbarrier [Hcritical [Hiter Hbrackets]]]]].
  pose proof (t42_model_rf_valid X rf Hmemory Hdevice) as Hvalid.
  repeat split.
  - intros j t l v [Hat | Hat] i Hseen.
    + pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t (Read l v) Hadj) Hat)
        as HatX.
      pose proof (Hread (t42_sw p j) t l v (or_introl HatX)) as Holder.
      assert (Hseen' : seen (hb (t42_swap_run X p)) (t42_swap_run X p)
        (t42_swap_rf p rf) (t42_sw p (t42_sw p j)) l i).
      { rewrite t42_sw_involutive. exact Hseen. }
      pose proof (t42_seen_not_older_swap_forward (hb X) (hb (t42_swap_run X p))
        X rf p t1 e1 t2 e2 (t42_sw p j) t (Read l v) l v
        Hadj Hdiff Hsafe
        ltac:(intros a b H; eapply t42_hb_swap_backward; eauto)
        Hvalid HatX ltac:(reflexivity) Holder i Hseen') as K.
      rewrite t42_sw_involutive in K. exact K.
    + pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t (HistoryRead l v) Hadj) Hat)
        as HatX.
      pose proof (Hread (t42_sw p j) t l v (or_intror HatX)) as Holder.
      assert (Hseen' : seen (hb (t42_swap_run X p)) (t42_swap_run X p)
        (t42_swap_rf p rf) (t42_sw p (t42_sw p j)) l i).
      { rewrite t42_sw_involutive. exact Hseen. }
      pose proof (t42_seen_not_older_swap_forward (hb X) (hb (t42_swap_run X p))
        X rf p t1 e1 t2 e2 (t42_sw p j) t (HistoryRead l v) l v
        Hadj Hdiff Hsafe
        ltac:(intros a b H; eapply t42_hb_swap_backward; eauto)
        Hvalid HatX ltac:(reflexivity) Holder i Hseen') as K.
      rewrite t42_sw_involutive in K. exact K.
  - intros i t e Hat. apply (Hthreads (t42_sw p i) t e).
    apply (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 i t e Hadj)). exact Hat.
  - intros j t' e' k t Hat Hk Ht.
    pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t' e' Hadj) Hat) as HatX.
    pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p j) t' e'
      Hadj Hdiff HatX) as Hint.
    rewrite t42_sw_involutive in Hint. rewrite Hint in Hk.
    destruct (Hbarrier (t42_sw p j) t' e' k t HatX Hk Ht) as [x [Hxj [Hatb Hix]]].
    exists (t42_sw p x). split.
    + rewrite <- (t42_sw_involutive p j).
      apply t42_sw_order; [exact Hxj |]. intros [Hxp Hjsp]. subst x.
      rewrite Hjsp in HatX, Hk.
      apply Hnos. apply sync_omp. eapply omp_sync_barrier; eauto. lia.
    + split.
      * apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 x t Barrier Hadj)). exact Hatb.
      * rewrite (t42_interval_swap X p t1 e1 t2 e2 x t Barrier Hadj Hdiff Hatb).
        exact Hix.
  - intros i j t t' Hij Hati Hatj Htt'.
    pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 i t Enter Hadj) Hati) as HatiX.
    pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t' Enter Hadj) Hatj) as HatjX.
    destruct (Nat.lt_ge_cases (t42_sw p i) (t42_sw p j)) as [Hord | Hrev].
    + specialize (Hcritical (t42_sw p i) (t42_sw p j) t t' Hord HatiX HatjX Htt').
      destruct Hcritical as [x [[Hix Hxj] Hatx]].
      exists (t42_sw p x). split.
      * split.
        -- rewrite <- (t42_sw_involutive p i). eapply t42_event_order_swap; eauto.
        -- rewrite <- (t42_sw_involutive p j).
           apply t42_sw_order; [exact Hxj |]. intros [Hxp Hjsp]. subst x.
           rewrite Hjsp in HatjX.
           apply Hnos. apply sync_omp. eapply omp_sync_critical; eauto.
      * apply (proj2 (t42_at_swap_iff X p t1 e1 t2 e2 x t Exit Hadj)). exact Hatx.
    + destruct (t42_sw_reverse_pair p i j Hij ltac:(lia)) as [-> ->].
      rewrite t42_sw_p in HatiX. rewrite t42_sw_Sp in HatjX.
      specialize (Hcritical p (S p) t' t ltac:(lia) HatjX HatiX ltac:(congruence)).
      destruct Hcritical as [x [[Hpx Hxsp] _]]. lia.
  - intros Hdone w Hsplit Hreach i.
    rewrite (t42_count_iter_swap X p t1 e1 t2 e2 w i Hadj).
    apply Hiter.
    + intros t Ht. rewrite <- (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff).
      apply Hdone. exact Ht.
    + exact Hsplit.
    + intros t Ht. rewrite <- (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff).
      apply Hreach. exact Ht.
  - (* t41c, 2026-10-14: well-bracketed critical sections (omp_ok's new last clause) *)
    intro t. rewrite (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff). apply Hbrackets.
Qed.

Definition t42_device_safe (X : run) (rf : rf_map) (p : nat) : Prop :=
  forall j t c l v, at_ X j t (DeviceRead c l v) ->
    rf j = Some p -> j < p -> ~ at_ X (S p) t (DeviceCovered c).

Lemma t42_device_ok_swap X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  ~ t42_events_conflict e1 e2 -> t42_device_safe X rf p ->
  memory_ok X rf -> device_ok X rf ->
  device_ok (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hdiff Hnos Hnos' Hsafe Hdevice_safe Hmemory Hdevice.
  pose proof (t42_model_rf_valid X rf Hmemory Hdevice) as Hvalid.
  intros j t c l v Hat.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t
    (DeviceRead c l v) Hadj) Hat) as HatX.
  destruct (Hdevice (t42_sw p j) t c l v HatX) as [Hok Hfuture]. split.
  - pose proof (t42_read_ok_length_swap_forward (hb X) (hb (t42_swap_run X p))
      X rf p t1 e1 t2 e2 (t42_sw p j) t (DeviceRead c l v) l v
      Hadj Hdiff Hsafe
      ltac:(intros a b H; eapply t42_hb_swap_backward; eauto)
      Hvalid HatX ltac:(reflexivity) Hok) as K.
    rewrite t42_sw_involutive in K. exact K.
  - intros i Hrfji Hji.
    unfold t42_swap_rf in Hrfji.
    destruct (rf (t42_sw p j)) as [q|] eqn:Hrfq; simpl in Hrfji; [|discriminate].
    inversion Hrfji. subst i.
    assert (Hwriteq : writes X q l v).
    { destruct Hok as [Hsource _]. unfold source_ok in Hsource.
      rewrite Hrfq in Hsource. exact (proj2 Hsource). }
    assert (Hwriteq' : writes (t42_swap_run X p) (t42_sw p q) l v).
    { apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 q l v Hadj)). exact Hwriteq. }
    assert (Hjq : t42_sw p j < q).
    { rewrite <- (t42_sw_involutive p q).
      destruct Hwriteq' as [u [d [Hatq Hd]]].
      apply (t42_access_order_swap (t42_swap_run X p) p t2 e2 t1 e1
        j (t42_sw p q) t (DeviceRead c l v) u d l).
      - apply t42_adjacent_swap. exact Hadj.
      - intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
      - exact Hat.
      - exact Hatq.
      - reflexivity.
      - eapply t42_written_loc; eauto.
      - right. exists v. exact Hd.
      - exact Hji. }
    destruct (Hfuture q eq_refl Hjq) as [Hnocover Hother]. split.
    + intros r Hr Hatcov.
      assert (Hrstrict : r < t42_sw p q).
      { destruct (Nat.eq_dec r (t42_sw p q)) as [Heq | Hneq]; [|lia].
        subst r. destruct Hwriteq' as [u [d [Hatq Hd]]].
        destruct (t42_at_unique (t42_swap_run X p) (t42_sw p q)
          u d t (DeviceCovered c) Hatq Hatcov) as [_ He].
        subst d. simpl in Hd. discriminate. }
      pose proof (t42_event_order_swap (t42_swap_run X p) p t2 e2 t1 e1
        j r t (DeviceRead c l v) (DeviceCovered c)
        (t42_adjacent_swap X p t1 e1 t2 e2 Hadj) ltac:(congruence)
        Hat Hatcov ltac:(lia)) as Hlower.
      assert (Hupper : t42_sw p r <= q).
      { destruct (Nat.lt_ge_cases (t42_sw p r) q) as [Hlt | Hge]; [lia |].
        assert (Hnot : ~ t42_sw p r < t42_sw p (t42_sw p q)).
        { rewrite t42_sw_involutive. lia. }
        destruct (t42_sw_reverse_pair p r (t42_sw p q) Hrstrict Hnot) as [HrP HqS].
        assert (HqP : q = p).
        { apply t42_sw_injective with (p := p).
          rewrite HqS. symmetry. apply t42_sw_p. }
        exfalso. apply (Hdevice_safe (t42_sw p j) t c l v HatX).
        - rewrite HqP in Hrfq. exact Hrfq.
        - lia.
        - pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 r t
            (DeviceCovered c) Hadj) Hatcov) as HcovX.
          rewrite HrP, t42_sw_p in HcovX. exact HcovX. }
      apply (Hnocover (t42_sw p r)); [lia |].
      apply (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 r t
        (DeviceCovered c) Hadj)). exact Hatcov.
    + intros [d Hati]. apply Hother. exists d.
      apply (proj1 (t42_at_swap_iff X p t1 e1 t2 e2 q t d Hadj)). exact Hati.
Qed.

Lemma t42_reads_latest_swap X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ t42_events_conflict e1 e2 ->
  reads_latest X rf ->
  reads_latest (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hdiff Hsafe Hlatest j t e l v Hat Hread Hqual.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t e Hadj) Hat) as HatX.
  assert (HqualX : is_shared e = true \/
    (cls (interval X t (t42_sw p j)) (array_of l) <> SharedActionsOnly /\
     ~ exists c, device_cmd e = Some c /\ crosses_sync (proj X t) c)).
  { destruct Hqual as [Hshared | [Hclass Hcross]].
    - now left.
    - right. split.
      + pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p j) t e
          Hadj Hdiff HatX) as Hint.
        rewrite t42_sw_involutive in Hint. rewrite <- Hint. exact Hclass.
      + intros [c [Hcmd HcrossX]]. apply Hcross. exists c. split; [exact Hcmd |].
        rewrite (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff). exact HcrossX. }
  pose proof (Hlatest (t42_sw p j) t e l v HatX Hread HqualX) as Hok.
  pose proof (t42_source_latest_swap_forward X rf p t1 e1 t2 e2
    (t42_sw p j) t e l v Hadj Hdiff Hsafe HatX Hread Hok) as K.
  rewrite t42_sw_involutive in K. exact K.
Qed.

Lemma t42_program_run_swap X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  program_run X -> program_run (t42_swap_run X p).
Proof.
  intros Hadj Hdiff Hprogram t. unfold program_run in Hprogram.
  rewrite (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff). apply Hprogram.
Qed.

Lemma t42_complete_swap X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  complete X -> complete (t42_swap_run X p).
Proof.
  intros Hadj Hdiff Hcomplete t Ht. unfold complete in Hcomplete.
  rewrite (t42_proj_swap X p t1 e1 t2 e2 t Hadj Hdiff). now apply Hcomplete.
Qed.

Lemma t42_all_fit_swap X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  all_fit X -> all_fit (t42_swap_run X p).
Proof.
  intros Hadj Hdiff Hfit t Ht i e l Hat Hloc.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 i t e Hadj) Hat) as HatX.
  specialize (Hfit t Ht (t42_sw p i) e l HatX Hloc).
  pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p i) t e
    Hadj Hdiff HatX) as Hint.
  pose proof (t42_inside_swap X p t1 e1 t2 e2 (t42_sw p i) t e
    Hadj Hdiff HatX) as Hinside.
  rewrite t42_sw_involutive in Hint, Hinside. rewrite Hint, Hinside.
  pose proof (t42_owned_swap X p t1 e1 t2 e2 (t42_sw p i) t e l
    Hadj Hdiff HatX) as Howned.
  rewrite t42_sw_involutive in Howned.
  destruct e; simpl in Hfit |- *; tauto.
Qed.

Lemma t42_intervals_contiguous_swap X p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  interval X t1 p = interval X t2 (S p) ->
  intervals_contiguous X -> intervals_contiguous (t42_swap_run X p).
Proof.
  intros Hadj Hdiff Hsame Hordered i j t t' e e' Hij Hati Hatj.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 i t e Hadj) Hati) as HatiX.
  pose proof (proj1 (t42_at_swap_reverse X p t1 e1 t2 e2 j t' e' Hadj) Hatj) as HatjX.
  pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p i) t e
    Hadj Hdiff HatiX) as HIi.
  pose proof (t42_interval_swap X p t1 e1 t2 e2 (t42_sw p j) t' e'
    Hadj Hdiff HatjX) as HIj.
  rewrite t42_sw_involutive in HIi, HIj. rewrite HIi, HIj.
  destruct (Nat.lt_ge_cases (t42_sw p i) (t42_sw p j)) as [Hord | Hrev].
  - eapply Hordered; eauto.
  - destruct (t42_sw_reverse_pair p i j Hij ltac:(lia)) as [-> ->].
    rewrite t42_sw_p in HatiX. rewrite t42_sw_Sp in HatjX.
    rewrite t42_sw_p, t42_sw_Sp.
    destruct (t42_adjacent_at X p t1 e1 t2 e2 Hadj) as [H1 H2].
    destruct (t42_at_unique X (S p) t2 e2 t e H2 HatiX) as [-> _].
    destruct (t42_at_unique X p t1 e1 t' e' H1 HatjX) as [-> _].
    rewrite Hsame. apply Nat.le_refl.
Qed.

Lemma t42_final_is_swap_forward X p t1 e1 t2 e2 l v :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  final_is X l v -> final_is (t42_swap_run X p) l v.
Proof.
  intros Hadj Hsafe Hfinal. unfold final_is in *. destruct Hfinal as [Hlast | Hinit].
  - left. destruct Hlast as [i [Hwrite Hafter]]. exists (t42_sw p i). split.
    + apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 i l v Hadj)). exact Hwrite.
    + intros q w Hlt Hwriteq. apply (Hafter (t42_sw p q) w).
      * rewrite <- (t42_sw_involutive p i).
        apply (t42_writes_order_swap (t42_swap_run X p) p t2 e2 t1 e1
          (t42_sw p i) q l v w).
        -- apply t42_adjacent_swap. exact Hadj.
        -- intro Hc. apply Hsafe. now apply t42_events_conflict_sym.
        -- apply (proj2 (t42_writes_swap X p t1 e1 t2 e2 i l v Hadj)). exact Hwrite.
        -- exact Hwriteq.
        -- exact Hlt.
      * apply (proj1 (t42_writes_swap X p t1 e1 t2 e2 (t42_sw p q) l w Hadj)).
        rewrite t42_sw_involutive. exact Hwriteq.
  - right. destruct Hinit as [Hv Hnone]. split; [exact Hv |].
    intros q w Hwriteq. apply (Hnone (t42_sw p q) w).
    apply (proj1 (t42_writes_swap X p t1 e1 t2 e2 (t42_sw p q) l w Hadj)).
    rewrite t42_sw_involutive. exact Hwriteq.
Qed.

Lemma t42_final_is_swap_iff X p t1 e1 t2 e2 l v :
  t42_adjacent X p t1 e1 t2 e2 ->
  ~ t42_events_conflict e1 e2 ->
  (final_is (t42_swap_run X p) l v <-> final_is X l v).
Proof.
  intros Hadj Hsafe. split.
  - intro H.
    pose proof (t42_final_is_swap_forward (t42_swap_run X p) p t2 e2 t1 e1 l v
      (t42_adjacent_swap X p t1 e1 t2 e2 Hadj)
      ltac:(intro Hc; apply Hsafe; now apply t42_events_conflict_sym) H) as K.
    rewrite (t42_swap_run_involutive X p (t42_adjacent_bound X p t1 e1 t2 e2 Hadj)) in K.
    exact K.
  - apply (t42_final_is_swap_forward X p t1 e1 t2 e2); assumption.
Qed.

Lemma t42_model_run_swap X rf p t1 e1 t2 e2 :
  t42_adjacent X p t1 e1 t2 e2 -> t1 <> t2 ->
  ~ sync X p (S p) -> ~ sync (t42_swap_run X p) p (S p) ->
  ~ t42_events_conflict e1 e2 -> t42_device_safe X rf p ->
  model_run X rf -> model_run (t42_swap_run X p) (t42_swap_rf p rf).
Proof.
  intros Hadj Hdiff Hnos Hnos' Hsafe Hdevice_safe [Hprogram [Hmemory [Hdevice Homp]]].
  unfold model_run. split.
  - exact (t42_program_run_swap X p t1 e1 t2 e2 Hadj Hdiff Hprogram).
  - split.
    + exact (t42_memory_ok_swap X rf p t1 e1 t2 e2 Hadj Hdiff Hnos Hnos'
        Hsafe Hmemory Hdevice).
    + split.
      * exact (t42_device_ok_swap X rf p t1 e1 t2 e2 Hadj Hdiff Hnos Hnos'
          Hsafe Hdevice_safe Hmemory Hdevice).
      * exact (t42_omp_ok_swap X rf p t1 e1 t2 e2 Hadj Hdiff Hnos Hnos'
          Hsafe Hmemory Hdevice Homp).
Qed.

Lemma t42_indep_model_all_fit_swap X rf p :
  t42_indep X p -> t42_device_safe X rf p ->
  model_run X rf -> all_fit X ->
  model_run (t42_swap_run X p) (t42_swap_rf p rf) /\
  all_fit (t42_swap_run X p).
Proof.
  intros [t1 [e1 [t2 [e2 [Hadj [Hdiff [Hnos [Hnos' Hsafe]]]]]]]]
    Hdevice_safe Hmodel Hfit. split.
  - eapply t42_model_run_swap; eauto.
  - eapply t42_all_fit_swap; eauto.
Qed.

(* END t42 lemmas *)
(** * 8. The parallel composition theorem.  OPEN: proof is ticket 42. *)
Theorem parallel_composition :
  obl_class_fit -> obl_owned_disjoint -> obl_atomic_blocks -> obl_chunk_cover ->
  obl_uniform_control -> obl_team_size -> obl_dx100_quiet ->
  forall (X : run) (rf : rf_map),
    program_run X ->
    memory_ok X rf ->      (* assumption entry: RC11 with fenced __sync (platform choice) *)
    omp_ok X rf ->         (* assumption entry: OpenMP 5.2 runtime (trusted tool) *)
    device_ok X rf ->      (* assumption entry: DX100 proof semantics *)
    complete X ->
    exists (Y : run) (rf' : rf_map), serial_outcome X Y rf'.
Proof.
  (* OPEN — ticket 42 proves this; it must prove exactly this approved text. *)
Admitted.

End Composition.
