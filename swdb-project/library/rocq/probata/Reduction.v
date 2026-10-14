(* Probata Rocq development: the DX100 reduction lemma (statement only).
   Created 2026-10-14 ET (ticket 41).  Proof: ticket 43.  Review guide: HYPOTHESES.md.
   Map decisions: 12 items 2-5 (and Later changes); research 14 (wait rule, gem5 e4fc4af);
   research 12 (region stall across the cores of one instance).

   Two semantics of the same multi-core program and one DX100 instance:
   - timed (what gem5 allows): commands run and finish at any time the gem5 rules permit;
   - at-issue (the proof semantics): each command runs at its issue; a ghost "pending" set
     says which commands a wait has not covered yet; hazards are checked against it.
   The lemma: if no at-issue run has a hazard, every timed run is matched by an at-issue run
   with the same observations and the same final state. *)
From Stdlib Require Import List Arith.
Import ListNotations.

Section Reduction.

(** * 1. Parameters *)
Variables res val core tile reg region cmd : Type.
  (* res: one memory element, tile element or register *)
Variable res_eq_dec : forall r r' : res, {r = r'} + {r <> r'}.
Variable core_eq_dec : forall c c' : core, {c = c'} + {c <> c'}.
Variable init : res -> val.
(* Proof-semantics contract of one maa_* command (12 item 1): given the values it reads,
   the elements it reads and the (element, value) pairs it writes.  Indirect footprints
   depend on the values read from the index tile. *)
Variable footprint : cmd -> (res -> val) -> list res * list (res * val).
Variables src_tiles cond_tiles dst_tiles : cmd -> list tile.  (* gem5 roles src1/src2, cond, dst1/dst2 *)
Variable cmd_regs : cmd -> list reg.          (* registers the command names *)
Variable regions_of : cmd -> list region.     (* registered memory regions the command names *)
Variable writes_memory : cmd -> bool.
Variable is_range_loop : cmd -> bool.
Variable in_tile : res -> tile -> Prop.
Variable in_reg : res -> reg -> Prop.
Variable region_of : res -> option region.    (* registered region holding a memory element *)
Variables owns_tile : core -> tile -> Prop.   (* per-thread ownership (12 item 5) *)
Variables owns_reg : core -> reg -> Prop.

Inductive instr : Type :=
| CpuRead (r : res) | CpuWrite (r : res) (v : val)   (* a tile-pointer read, get_reg and
                                                        get_tile_size are CpuReads *)
| Issue (k : cmd) | WaitReady (t : tile) | TileReady (t : tile) | Halt.
Inductive obs : Type := Got (v : val) | Answer (b : bool) | Ack.
(* Each core's program: its next instruction, given what it has observed so far. *)
Variable prog : core -> list obs -> instr.

Inductive step : Type :=
| SCpu (c : core) (i : instr) (o : obs)  (* core c executes its next instruction, observes o *)
| SRun (n : nat) (rho : res -> val)      (* the command issued at step n reads rho, writes *)
| SFinish (n : nat).                     (* the command issued at step n finishes *)
Definition run := list step.

Definition issued (R : run) (n : nat) (c : core) (k : cmd) : Prop :=
  nth_error R n = Some (SCpu c (Issue k) Ack).
Definition step_writes (R : run) (s : step) : list (res * val) :=
  match s with
  | SCpu _ (CpuWrite r v) _ => [(r, v)]
  | SRun n rho => match nth_error R n with
                  | Some (SCpu _ (Issue k) _) => snd (footprint k rho) | _ => [] end
  | _ => []
  end.
Definition upd (s : res -> val) (w : res * val) : res -> val :=
  fun r => if res_eq_dec (fst w) r then snd w else s r.
(* the state after the first m steps *)
Definition state_after (R : run) (m : nat) : res -> val :=
  fold_left (fun s st => fold_left upd (step_writes R st) s) (firstn m R) init.
Definition final_state (R : run) : res -> val := state_after R (length R).

Definition core_steps (R : run) (c : core) : list (instr * obs) :=
  flat_map (fun s => match s with
                     | SCpu c' i o => if core_eq_dec c c' then [(i, o)] else []
                     | _ => [] end) R.
Fixpoint conforms (c : core) (seen : list obs) (tr : list (instr * obs)) : Prop :=
  match tr with
  | [] => True
  | (i, o) :: tr' => i = prog c seen /\ i <> Halt /\ conforms c (seen ++ [o]) tr'
  end.
Definition observations (R : run) (c : core) : list obs := map snd (core_steps R c).
Definition follows_program (R : run) : Prop := forall c, conforms c [] (core_steps R c).
Definition cpu_ok (R : run) : Prop :=           (* a CPU read returns the current value *)
  forall m c i o, nth_error R m = Some (SCpu c i o) ->
    match i with
    | CpuRead r => o = Got (state_after R m r)
    | TileReady _ => exists b, o = Answer b
    | _ => o = Ack
    end.

Definition names_counted (k : cmd) (t : tile) : Prop :=   (* counted roles, MAA.cc:563-580 *)
  In t (src_tiles k) \/ In t (dst_tiles k).
Definition produces (k' k : cmd) : Prop :=   (* k' writes a tile k reads as source or condition *)
  exists t, In t (dst_tiles k') /\ (In t (src_tiles k) \/ In t (cond_tiles k)).

(** * 2. Timed semantics: the gem5 rules (research 14 at e4fc4af) *)
Definition finished_by (R : run) (n m : nat) : Prop :=
  exists q, q < m /\ nth_error R q = Some (SFinish n).
Definition unfinished (R : run) (n m : nat) : Prop :=
  (exists c k, issued R n c k) /\ n < m /\ ~ finished_by R n m.

Definition timed_run (T : run) : Prop :=
  follows_program T /\ cpu_ok T /\
  (* each command runs at most once and finishes at most once, after it runs *)
  (forall p n rho, nth_error T p = Some (SRun n rho) ->
     n < p /\ (exists c k, issued T n c k) /\
     forall p' rho', nth_error T p' = Some (SRun n rho') -> p' = p) /\
  (forall q n, nth_error T q = Some (SFinish n) ->
     (exists p rho, p < q /\ nth_error T p = Some (SRun n rho)) /\
     forall q', nth_error T q' = Some (SFinish n) -> q' = q) /\
  (* dispatch stall: one core's commands dispatch in program order (an Issue is a core step);
     refused while its destination tile is any unfinished command's tile (IF.cc:193-212) or
     it shares a registered region with an unfinished command and either writes memory
     (IF.cc:213-219; across all cores of one instance, research 12) *)
  (forall m c k n c' k', issued T m c k -> issued T n c' k' -> unfinished T n m ->
     (forall t, In t (dst_tiles k) ->
        ~ (In t (src_tiles k') \/ In t (dst_tiles k') \/ In t (cond_tiles k'))) /\
     (forall g, In g (regions_of k) -> In g (regions_of k') ->
        writes_memory k = false /\ writes_memory k' = false)) /\
  (* a CPU register write waits until no unfinished command names the register (IF.cc:233-249) *)
  (forall m c r v g n c' k', nth_error T m = Some (SCpu c (CpuWrite r v) Ack) -> in_reg r g ->
     issued T n c' k' -> unfinished T n m -> ~ In g (cmd_regs k')) /\
  (* out-of-order execution (IF.cc:250-299): a command reads each element at some time while
     it runs, after every earlier command that writes that element has written it
     (element readiness, SPD.cc:140-157) *)
  (forall p n rho c k r, nth_error T p = Some (SRun n rho) -> issued T n c k ->
     In r (fst (footprint k rho)) ->
     exists m, n < m <= p /\ state_after T m r = rho r /\
       forall n' p' rho' c' k', n' < n -> issued T n' c' k' ->
         nth_error T p' = Some (SRun n' rho') -> In r (map fst (snd (footprint k' rho'))) ->
         p' < m) /\
  (* a command finishes only after the producers of its input tiles finished, except a range
     loop (ALU.cc:199-246, StreamAccess.cc:305-316, IndirectAccess.cc:399-459; exception
     RangeFuser.cc:166-168) *)
  (forall n c k n' c' k' q, issued T n c k -> issued T n' c' k' -> n' < n -> produces k' k ->
     is_range_loop k = false -> nth_error T q = Some (SFinish n) -> finished_by T n' q) /\
  (* wait_ready blocks until no unfinished command names the tile in a counted role
     (SPD.cc:120-139, CpuSidePort.cc:295-315); get_tile_ready answers that question now *)
  (forall m c t n c' k', nth_error T m = Some (SCpu c (WaitReady t) Ack) ->
     issued T n c' k' -> unfinished T n m -> ~ names_counted k' t) /\
  (forall m c t b, nth_error T m = Some (SCpu c (TileReady t) (Answer b)) ->
     (b = true <-> forall n c' k', issued T n c' k' -> unfinished T n m -> ~ names_counted k' t)).

Definition complete_timed (T : run) : Prop :=
  (forall c, prog c (observations T c) = Halt) /\
  (forall n c k, issued T n c k -> exists q, nth_error T q = Some (SFinish n)).

(** * 3. At-issue semantics: the proof semantics (12 items 2-4) *)
Definition waits_at (A : run) (m : nat) (t : tile) : Prop :=
  exists c, nth_error A m = Some (SCpu c (WaitReady t) Ack) \/
            nth_error A m = Some (SCpu c (TileReady t) (Answer true)).
(* A wait on tile t covers every command naming t in a counted role and, transitively, the
   producers of their inputs, but not through a range loop (research 14, section 4). *)
Inductive covered (A : run) (n m : nat) : Prop :=
| cov_direct c k t : issued A n c k -> n < m -> waits_at A m t -> names_counted k t ->
    covered A n m
| cov_producer c k n' c' k' : covered A n' m -> issued A n c k -> issued A n' c' k' ->
    n < n' -> is_range_loop k' = false -> produces k k' -> covered A n m.
(* ghost state: issued at n, not covered by any wait before step j *)
Definition pending (A : run) (n j : nat) : Prop :=
  (exists c k, issued A n c k) /\ n < j /\ forall m, m < j -> ~ covered A n m.

Definition at_issue_run (A : run) : Prop :=
  follows_program A /\ cpu_ok A /\
  (* each command runs right at its issue and never needs a finish step *)
  (forall n c k, issued A n c k -> exists rho, nth_error A (S n) = Some (SRun n rho)) /\
  (forall p n rho, nth_error A p = Some (SRun n rho) -> p = S n /\ exists c k, issued A n c k) /\
  (forall q n, nth_error A q <> Some (SFinish n)) /\
  (* each element read has its value at issue, or a value another core's CPU stored there
     while the command was pending (12 item 4, "other thread, DX100 only reads") *)
  (forall n c k rho r, issued A n c k -> nth_error A (S n) = Some (SRun n rho) ->
     In r (fst (footprint k rho)) ->
     rho r = state_after A (S n) r \/
     exists m c' v, S n < m /\ pending A n m /\ c' <> c /\
       nth_error A m = Some (SCpu c' (CpuWrite r v) Ack) /\ rho r = v) /\
  (* get_tile_ready may answer 0 only while a command naming the tile is pending (12 item 3) *)
  (forall m c t, nth_error A m = Some (SCpu c (TileReady t) (Answer false)) ->
     exists n c' k', issued A n c' k' /\ pending A n m /\ names_counted k' t).

(** * 4. Hazard-free: the proof semantics' own hazard definition (12 items 3-5) *)
Definition reads_of (A : run) (n : nat) (r : res) : Prop :=
  exists c k rho, issued A n c k /\ nth_error A (S n) = Some (SRun n rho) /\
    In r (fst (footprint k rho)).
Definition writes_of (A : run) (n : nat) (r : res) : Prop :=
  exists c k rho v, issued A n c k /\ nth_error A (S n) = Some (SRun n rho) /\
    In (r, v) (snd (footprint k rho)).
Definition is_memory (r : res) : Prop := (forall t, ~ in_tile r t) /\ (forall g, ~ in_reg r g).
Definition hazard (A : run) (m : nat) : Prop :=
  (exists c i o, nth_error A m = Some (SCpu c i o) /\
   match i with
   | CpuRead r =>
       (* unready read (12 item 3), and any read overlapping an unfinished DX100 write:
          same thread or other thread (12 item 4) *)
       (exists n, pending A n m /\ writes_of A n r)
       \/ (exists t, in_tile r t /\ ~ owns_tile c t) \/ (exists g, in_reg r g /\ ~ owns_reg c g)
   | CpuWrite r _ =>
       (exists n, pending A n m /\ writes_of A n r)                      (* write over a write *)
       \/ (exists n k, pending A n m /\ issued A n c k /\ reads_of A n r)  (* same thread *)
       \/ (exists n t, pending A n m /\ reads_of A n r /\ in_tile r t)     (* a tile it reads *)
       \/ (exists t, in_tile r t /\ ~ owns_tile c t) \/ (exists g, in_reg r g /\ ~ owns_reg c g)
   | Issue k =>                                                           (* ownership, 12 item 5 *)
       (exists t, (In t (src_tiles k) \/ In t (cond_tiles k) \/ In t (dst_tiles k)) /\
                  ~ owns_tile c t)
       \/ (exists g, In g (cmd_regs k) /\ ~ owns_reg c g)
   | _ => False
   end) \/
  (* a memory element outside the command's registered regions escapes the region stall *)
  (exists n c k rho r, m = S n /\ issued A n c k /\ nth_error A m = Some (SRun n rho) /\
     (In r (fst (footprint k rho)) \/ In r (map fst (snd (footprint k rho)))) /\
     is_memory r /\ forall g, region_of r = Some g -> ~ In g (regions_of k)).

(* hazard_free: per-candidate WP obligation (the proof semantics' hazard assertions). *)
Definition obl_hazard_free : Prop := forall A m, at_issue_run A -> ~ hazard A m.

(** * 5. The DX100 reduction lemma.  OPEN: proof is ticket 43. *)
Theorem dx100_reduction :
  obl_hazard_free ->
  forall T : run, timed_run T -> complete_timed T ->
    exists A : run, at_issue_run A /\
      (forall c, observations A c = observations T c) /\
      (forall r, final_state A r = final_state T r).
Proof.
  (* OPEN — ticket 43 proves this; it must prove exactly this approved text. *)
Admitted.

End Reduction.
