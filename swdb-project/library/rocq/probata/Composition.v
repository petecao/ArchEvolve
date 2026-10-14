(* Probata Rocq development: the parallel composition theorem (statement only).
   Created 2026-10-14 ET (ticket 41).  Proof: ticket 42.  Review guide: HYPOTHESES.md.
   Map decisions: 15 items 1-7; 16 item 4 and Later changes; 26 item 4.

   Reading order: 1 parameters, 2 events and runs, 3 memory model (RC11 rendering),
   4 OpenMP rules, 5 DX100 reads, 6 per-candidate obligations, 7 conclusion, 8 theorem. *)
From Stdlib Require Import List Arith Relations.
From Probata Require Import Vocabulary.
Import ListNotations.

Section Composition.

(** * 1. Parameters.  The theorem holds for every choice of them. *)
Variables loc arr val arg : Type.
Variable array_of : loc -> arr.        (* the array a location belongs to *)
Variable init : loc -> val.            (* memory when the parallel region starts *)
Variable sa_new : shared_action_kind -> arg -> val -> val.
  (* a shared action of kind k with argument a turns old value v into sa_new k a v *)
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
| Shared (k : shared_action_kind) (a : arg) (l : loc) (old : val)
                                    (* one shared action: an SC read-modify-write that reads
                                       old and stores sa_new k a old (15 items 3, 5) *)
| DeviceRead (l : loc) (v : val)    (* one element read by this thread's DX100 command, placed
                                       at issue (finish-at-issue; reduction lemma) *)
| DeviceWrite (l : loc) (v : val)   (* one element write by this thread's DX100 command *)
| DeviceQuiet                       (* ghost: no DX100 command of this thread is unfinished *)
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
  | Read l _ | Write l _ | HistoryRead l _ | Shared _ _ l _
  | DeviceRead l _ | DeviceWrite l _ => Some l
  | _ => None
  end.
Definition written (e : event) : option (loc * val) :=
  match e with
  | Write l v | DeviceWrite l v => Some (l, v)
  | Shared k a l old => Some (l, sa_new k a old)
  | _ => None
  end.
Definition read_value (e : event) : option (loc * val) :=
  match e with
  | Read l v | HistoryRead l v | DeviceRead l v => Some (l, v)
  | Shared _ _ l old => Some (l, old)
  | _ => None
  end.
Definition writes (X : run) (i : nat) (l : loc) (v : val) : Prop :=
  exists t e, at_ X i t e /\ written e = Some (l, v).

(** * 3. Memory model: the history read (15 item 3), our rendering of RC11 *)
(* Ordered-before: program order, barrier, critical section, and the SC order of
   shared actions (15 item 3: "writes ordered before it by a barrier, critical or a CAS"). *)
Inductive sync (X : run) (i j : nat) : Prop :=
| sync_po t e e' : i < j -> at_ X i t e -> at_ X j t e' -> sync X i j
| sync_barrier t t' e : i < j -> at_ X i t Barrier -> at_ X j t' e ->
    interval X t i < interval X t' j -> sync X i j
| sync_critical t t' : i < j -> at_ X i t Exit -> at_ X j t' Enter -> sync X i j
| sync_shared t t' k a l v k' a' l' v' : i < j -> at_ X i t (Shared k a l v) ->
    at_ X j t' (Shared k' a' l' v') -> sync X i j.
Definition hb (X : run) : nat -> nat -> Prop := clos_trans nat (sync X).

(* rf j: the position of the write read at position j; None = the initial value. *)
Definition rf_map := nat -> option nat.
Definition source_ok (X : run) (l : loc) (v : val) (s : option nat) (bound : nat) : Prop :=
  match s with None => v = init l | Some i => i < bound /\ writes X i l v end.
Definition not_older (s : option nat) (i : nat) : Prop :=
  match s with None => False | Some i' => i <= i' end.
(* The writes to l that the reader at j has seen: ordered before j, or no newer than what
   the same thread already read from l (its own reads and writes). *)
Definition seen (X : run) (rf : rf_map) (j : nat) (l : loc) (i : nat) : Prop :=
  (exists v, writes X i l v) /\
  (hb X i j \/
   exists r t e e' v s, r < j /\ at_ X r t e /\ at_ X j t e' /\
     read_value e = Some (l, v) /\ rf r = Some s /\ i <= s).
(* History read: a value the location already held (source before bound), never older
   than the newest write the reader has seen. *)
Definition read_ok (X : run) (rf : rf_map) (j : nat) (l : loc) (v : val) (bound : nat) : Prop :=
  source_ok X l v (rf j) bound /\ forall i, seen X rf j l i -> not_older (rf j) i.
Definition latest (X : run) (l : loc) (j : nat) (s : option nat) : Prop :=
  match s with
  | None => forall i v, i < j -> ~ writes X i l v
  | Some i => i < j /\ forall i' v, i < i' < j -> ~ writes X i' l v
  end.

(* Assumption entry, platform choice: the pinned compiler and ISA implement RC11. *)
Definition memory_ok (X : run) (rf : rf_map) : Prop :=
  (forall j t l v, at_ X j t (Read l v) \/ at_ X j t (HistoryRead l v) ->
     read_ok X rf j l v j) /\
  (forall j t k a l old, at_ X j t (Shared k a l old) ->     (* SC read-modify-write *)
     source_ok X l old (rf j) j /\ latest X l j (rf j)).

(** * 4. OpenMP rules (15 item 4).  Assumption entry, trusted tool: OpenMP 5.2 runtime. *)
Definition count_iter (X : run) (w i : nat) : nat :=
  length (filter (fun p => match snd p with
                           | Iter w' i' => andb (Nat.eqb w w') (Nat.eqb i i')
                           | _ => false end) X).
Definition omp_ok (X : run) : Prop :=
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
   forall i, count_iter X w i = if in_dec Nat.eq_dec i (space w) then 1 else 0).

(** * 5. DX100 reads by this thread's commands (15 item 7; 12 item 4).
    Assumption entry, proof semantics: a DX100 read returns a value the location held
    while the command ran (up to the thread's next DeviceQuiet), never older than the
    stores made before issue, and never a later write of the issuing thread itself. *)
Definition before_quiet (X : run) (t j i : nat) : Prop :=
  forall q, j < q <= i -> ~ at_ X q t DeviceQuiet.
Definition device_ok (X : run) (rf : rf_map) : Prop :=
  forall j t l v, at_ X j t (DeviceRead l v) ->
    read_ok X rf j l v (length X) /\
    forall i, rf j = Some i -> j < i -> before_quiet X t j i /\ ~ exists e, at_ X i t e.

Definition model_run (X : run) (rf : rf_map) : Prop :=
  program_run X /\ memory_ok X rf /\ device_ok X rf /\ omp_ok X.

(** * 6. Per-candidate obligations (WP proves each one; HYPOTHESES.md names them) *)
(* Which accesses a sharing class allows (15 items 2, 3, 7).  crit: inside critical;
   own: the thread owns the location in this interval. *)
Definition fits_event (c : sharing_class) (crit own : Prop) (e : event) : Prop :=
  match e with
  | Read _ _ => c = ReadOnly \/ (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
  | HistoryRead _ _ | DeviceRead _ _ =>
      c = ReadOnly \/ (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
      \/ c = SharedActionsOnly
  | Write _ _ | DeviceWrite _ _ => (c = ThreadOwned /\ own) \/ (c = LockProtected /\ crit)
  | Shared _ _ _ _ => c = SharedActionsOnly
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

(* atomic_blocks: each critical section implements one shared action: it reads one location
   l first, writes only l, and leaves sa_new k a old there (or writes nothing). *)
Definition critical_block (tr blk : list event) : Prop :=
  exists pre post, tr = pre ++ Enter :: blk ++ Exit :: post /\ ~ In Enter blk /\ ~ In Exit blk.
Definition implements_shared_action (blk : list event) : Prop :=
  (forall e, In e blk -> written e = None) \/
  exists k a l old,
    (exists pre post, blk = pre ++ Read l old :: post /\
       forall e, In e pre -> loc_of e <> Some l) /\
    (forall e l' v, In e blk -> written e = Some (l', v) -> l' = l) /\
    (exists pre post e, blk = pre ++ e :: post /\ written e = Some (l, sa_new k a old) /\
       forall e', In e' post -> written e' = None).
Definition obl_atomic_blocks : Prop :=
  forall t tr blk, t < N -> program_trace t tr -> critical_block tr blk ->
    implements_shared_action blk.

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

(* dx100_quiet: every DX100 access of thread t is followed by a DeviceQuiet before t's next
   barrier, before t leaves a critical section it was in, and before t's own conflicting
   CPU access to the same location (12 items 3-5, 7). *)
Definition conflicts (d e : event) : Prop :=
  match d, e with
  | DeviceRead l _, (Write l' _ | Shared _ _ l' _) => l = l'
  | DeviceWrite l _, (Read l' _ | Write l' _ | HistoryRead l' _ | Shared _ _ l' _) => l = l'
  | _, _ => False
  end.
Definition is_device (e : event) : Prop :=
  match e with DeviceRead _ _ | DeviceWrite _ _ => True | _ => False end.
Definition quiet_ok (tr : list event) : Prop :=
  forall p d, nth_error tr p = Some d -> is_device d ->
    exists q, p < q /\ nth_error tr q = Some DeviceQuiet /\
      forall m e, p < m < q -> nth_error tr m = Some e ->
        e <> Barrier /\ (in_crit (firstn p tr) false = true -> e <> Exit) /\ ~ conflicts d e.
Definition obl_dx100_quiet : Prop :=
  forall X rf t, model_run X rf -> complete X -> all_fit X -> t < N -> quiet_ok (proj X t).

(** * 7. Conclusion: the run ends as a serial order of its shared actions would *)
Definition intervals_contiguous (Y : run) : Prop :=
  forall i j t t' e e', i < j -> at_ Y i t e -> at_ Y j t' e' -> interval Y t i <= interval Y t' j.
Definition critical_sections_contiguous (Y : run) : Prop :=
  forall i x t, at_ Y i t Enter -> at_ Y x t Exit -> i < x ->
    (forall m, i < m < x -> ~ at_ Y m t Enter /\ ~ at_ Y m t Exit) ->
    forall m, i < m < x -> exists e, at_ Y m t e.
Definition is_shared (e : event) : bool := match e with Shared _ _ _ _ => true | _ => false end.
(* Every shared action, and every read of a location outside SharedActionsOnly, reads the
   latest write before it. *)
Definition reads_latest (Y : run) (rf : rf_map) : Prop :=
  forall j t e l v, at_ Y j t e -> read_value e = Some (l, v) ->
    (is_shared e = true \/ cls (interval Y t j) (array_of l) <> SharedActionsOnly) ->
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
  memory_ok Y rf' /\ device_ok Y rf' /\            (* racing reads stay history reads *)
  (forall l v, final_is X l v <-> final_is Y l v) /\  (* same final memory *)
  iterations_once Y.                               (* every iteration exactly once *)

(** * 8. The parallel composition theorem.  OPEN: proof is ticket 42. *)
Theorem parallel_composition :
  obl_class_fit -> obl_owned_disjoint -> obl_atomic_blocks -> obl_chunk_cover ->
  obl_uniform_control -> obl_team_size -> obl_dx100_quiet ->
  forall (X : run) (rf : rf_map),
    program_run X ->
    memory_ok X rf ->      (* assumption entry: RC11 (platform choice) *)
    omp_ok X ->            (* assumption entry: OpenMP 5.2 runtime (trusted tool) *)
    device_ok X rf ->      (* assumption entry: DX100 proof semantics *)
    complete X ->
    exists (Y : run) (rf' : rf_map), serial_outcome X Y rf'.
Proof.
  (* OPEN — ticket 42 proves this; it must prove exactly this approved text. *)
Admitted.

End Composition.
