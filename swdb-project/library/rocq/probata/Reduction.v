(* Probata Rocq development: the DX100 reduction lemma (statement only).
   Created 2026-10-14 ET (ticket 41).  Revised 2026-10-14 ET after Codex's adversarial review
   and the main session's decisions (F2, M6).  Revised 2026-10-14 ET by the main session under
   Yan-Ru's delegation (ticket 41, Later changes): the issue-stall and register-write covers
   ticket 27 found missing, and an inclusive pending set.
   Proof: ticket 43.  Review guide: HYPOTHESES.md.
   Map decisions: 12 items 1-5 (and Later changes); research 14 (wait rule, gem5 e4fc4af);
   research 12 (region stall across the cores of one instance).

   Two semantics of the same multi-core program and one DX100 instance:
   - timed (what gem5 allows): commands run and finish at any time the gem5 rules permit;
   - at-issue (the proof semantics): each command runs at its issue; a ghost "pending" set
     says which commands no covering step (a wait, a stalled issue, a CPU register write)
     has covered yet; hazards are checked against it.
   The lemma: if the command contracts are well formed and no at-issue run has a hazard,
   every complete timed run is matched by an at-issue run with the same observations and
   the same final state.  CPU steps are in one global order here (M6; ticket 43 must show
   why this split from the composition theorem's RC11 model is sound). *)
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
Variable regions_of : cmd -> list region.     (* registered regions gem5 assigns the command *)
Variable writes_memory : cmd -> bool.
Variable is_range_loop : cmd -> bool.
Variable in_tile : res -> tile -> Prop.
Variable in_reg : res -> reg -> Prop.
Variable in_region : res -> region -> Prop.   (* a relation: registrations may overlap (F2) *)
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

Definition is_memory (r : res) : Prop := (forall t, ~ in_tile r t) /\ (forall g, ~ in_reg r g).
Definition fp_reads (k : cmd) (rho : res -> val) : list res := fst (footprint k rho).
Definition fp_writes (k : cmd) (rho : res -> val) : list res := map fst (snd (footprint k rho)).

(* Assumption entry, proof semantics: each command contract is well formed.  Its writes
   depend only on the elements it reads; a command writing memory says so (the region
   stall's input); tile and register elements it touches lie in the tiles and registers it
   names. *)
Definition contracts_ok : Prop :=
  forall k rho,
    (forall rho', (forall r, In r (fp_reads k rho) -> rho' r = rho r) ->
       footprint k rho' = footprint k rho) /\
    (forall r, In r (fp_writes k rho) -> is_memory r -> writes_memory k = true) /\
    (forall r t, In r (fp_reads k rho) -> in_tile r t ->
       In t (src_tiles k) \/ In t (cond_tiles k)) /\
    (forall r t, In r (fp_writes k rho) -> in_tile r t -> In t (dst_tiles k)) /\
    (forall r g, (In r (fp_reads k rho) \/ In r (fp_writes k rho)) -> in_reg r g ->
       In g (cmd_regs k)).

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
Definition names_any (k : cmd) (t : tile) : Prop :=
  In t (src_tiles k) \/ In t (dst_tiles k) \/ In t (cond_tiles k).
Definition produces (k' k : cmd) : Prop :=   (* k' writes a tile k reads as source or condition *)
  exists t, In t (dst_tiles k') /\ (In t (src_tiles k) \/ In t (cond_tiles k)).
(* gem5 refuses to dispatch k' while an unfinished earlier k blocks it (IF.cc:193-219) *)
Definition stalls (k k' : cmd) : Prop :=
  (exists t, In t (dst_tiles k') /\ names_any k t) \/
  ((exists g, In g (regions_of k) /\ In g (regions_of k')) /\
   (writes_memory k = true \/ writes_memory k' = true)).

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
     ~ stalls k' k) /\
  (* a CPU register write waits until no unfinished command names the register (IF.cc:233-249) *)
  (forall m c r v g n c' k', nth_error T m = Some (SCpu c (CpuWrite r v) Ack) -> in_reg r g ->
     issued T n c' k' -> unfinished T n m -> ~ In g (cmd_regs k')) /\
  (* out-of-order execution (IF.cc:250-299): a command reads each element at some time while
     it runs, after every earlier command that writes that element has written it
     (element readiness, SPD.cc:140-157) *)
  (forall p n rho c k r, nth_error T p = Some (SRun n rho) -> issued T n c k ->
     In r (fp_reads k rho) ->
     exists m, n < m <= p /\ state_after T m r = rho r /\
       forall n' p' rho' c' k', n' < n -> issued T n' c' k' ->
         nth_error T p' = Some (SRun n' rho') -> In r (fp_writes k' rho') -> p' < m) /\
  (* a command finishes only after the producers of its input tiles finished, except a range
     loop (ALU.cc:199-246, StreamAccess.cc:305-316, IndirectAccess.cc:399-459; exception
     RangeFuser.cc:166-168) *)
  (forall n c k n' c' k' q, issued T n c k -> issued T n' c' k' -> n' < n -> produces k' k ->
     is_range_loop k = false -> nth_error T q = Some (SFinish n) -> finished_by T n' q) /\
  (* wait_ready blocks until no unfinished command names the tile in a counted role
     (SPD.cc:120-139, CpuSidePort.cc:295-315) *)
  (forall m c t n c' k', nth_error T m = Some (SCpu c (WaitReady t) Ack) ->
     issued T n c' k' -> unfinished T n m -> ~ names_counted k' t) /\
  (* get_tile_ready answers that question now; a 0 has an unfinished witness *)
  (forall m c t, nth_error T m = Some (SCpu c (TileReady t) (Answer true)) ->
     forall n c' k', issued T n c' k' -> unfinished T n m -> ~ names_counted k' t) /\
  (forall m c t, nth_error T m = Some (SCpu c (TileReady t) (Answer false)) ->
     exists n c' k', issued T n c' k' /\ unfinished T n m /\ names_counted k' t).

(* every command runs and finishes before the run ends; a command nothing covers may finish
   at any time before that *)
Definition complete_timed (T : run) : Prop :=
  (forall c, prog c (observations T c) = Halt) /\
  (forall n c k, issued T n c k -> exists q, nth_error T q = Some (SFinish n)).

(** * 3. At-issue semantics: the proof semantics (12 items 2-4) *)
Definition waits_at (A : run) (m : nat) (t : tile) : Prop :=
  exists c, nth_error A m = Some (SCpu c (WaitReady t) Ack) \/
            nth_error A m = Some (SCpu c (TileReady t) (Answer true)).
(* What covers command n at covering step m.  Three base covers, each a gem5 rule that holds
   the CPU at step m until the command has finished (each mirrors a clause of timed_run), and
   two closure rules that extend a cover backward to earlier commands:
   - base, a wait on tile t covers every command naming t in a counted role
     (research 14, section 4);
   - closure, the producers of a covered command's inputs are covered, but not through a
     range loop (research 14, section 4);
   - closure, a covered command also covers every earlier command that would have stalled
     its dispatch (IF.cc:193-219): that command finished before it was dispatched (F5;
     implied by cov_issue for pending, kept);
   - base, the issue of a command covers every earlier command that stalls its dispatch; the
     CPU's issuing store is not acknowledged until dispatch (CpuSidePort.cc:235-250,
     MAA.cc:581-583, research 14 section 2)
     (destination tile IF.cc:193-212, region IF.cc:213-219; ticket 27);
   - base, a CPU write of a register covers every earlier command naming the register: gem5 holds
     the write until no unfinished command names it (IF.cc:233-249; ticket 27). *)
Inductive covered (A : run) (n m : nat) : Prop :=
| cov_direct c k t : issued A n c k -> n < m -> waits_at A m t -> names_counted k t ->
    covered A n m
| cov_producer c k n' c' k' : covered A n' m -> issued A n c k -> issued A n' c' k' ->
    n < n' -> is_range_loop k' = false -> produces k k' -> covered A n m
| cov_stall c k n' c' k' : covered A n' m -> issued A n c k -> issued A n' c' k' ->
    n < n' -> stalls k k' -> covered A n m
| cov_issue c k c' k' : issued A n c k -> issued A m c' k' -> n < m -> stalls k k' ->
    covered A n m
| cov_reg_write c k c' r v g : issued A n c k -> n < m ->
    nth_error A m = Some (SCpu c' (CpuWrite r v) Ack) -> in_reg r g -> In g (cmd_regs k) ->
    covered A n m.
(* ghost state: issued at n, not covered by any step up to and including step j.  Inclusive:
   a covering step (a register write, an issue) acts only once gem5 has finished the command,
   the same "finished before step j" boundary as timed_run's unfinished T n j. *)
Definition pending (A : run) (n j : nat) : Prop :=
  (exists c k, issued A n c k) /\ n < j /\ forall m, m <= j -> ~ covered A n m.

Definition at_issue_run (A : run) : Prop :=
  follows_program A /\ cpu_ok A /\
  (* each command runs right at its issue and never needs a finish step *)
  (forall n c k, issued A n c k -> exists rho, nth_error A (S n) = Some (SRun n rho)) /\
  (forall p n rho, nth_error A p = Some (SRun n rho) -> p = S n /\ exists c k, issued A n c k) /\
  (forall q n, nth_error A q <> Some (SFinish n)) /\
  (* each element read has its value at issue, or a value another core's CPU stored there
     while the command was pending (12 item 4, "other thread, DX100 only reads") *)
  (forall n c k rho r, issued A n c k -> nth_error A (S n) = Some (SRun n rho) ->
     In r (fp_reads k rho) ->
     rho r = state_after A (S n) r \/
     exists m c' v, S n < m /\ pending A n m /\ c' <> c /\
       nth_error A m = Some (SCpu c' (CpuWrite r v) Ack) /\ rho r = v) /\
  (* get_tile_ready may answer 0 only while a command naming the tile is pending (12 item 3) *)
  (forall m c t, nth_error A m = Some (SCpu c (TileReady t) (Answer false)) ->
     exists n c' k', issued A n c' k' /\ pending A n m /\ names_counted k' t).

(** * 4. Hazard-free: the proof semantics' own hazard definition (12 items 3-5) *)
Definition reads_of (A : run) (n : nat) (r : res) : Prop :=
  exists c k rho, issued A n c k /\ nth_error A (S n) = Some (SRun n rho) /\ In r (fp_reads k rho).
Definition writes_of (A : run) (n : nat) (r : res) : Prop :=
  exists c k rho, issued A n c k /\ nth_error A (S n) = Some (SRun n rho) /\ In r (fp_writes k rho).
Definition issued_by (A : run) (n : nat) (c : core) : Prop := exists k, issued A n c k.
Definition not_owned (c : core) (r : res) : Prop :=
  (exists t, in_tile r t /\ ~ owns_tile c t) \/ (exists g, in_reg r g /\ ~ owns_reg c g).
(* the command reaches a memory element outside some registered region holding it, or in
   none: gem5's region stall would not see the overlap (F2) *)
Definition unregistered (k : cmd) (rho : res -> val) : Prop :=
  exists r, (In r (fp_reads k rho) \/ In r (fp_writes k rho)) /\ is_memory r /\
    ((forall g, ~ in_region r g) \/ exists g, in_region r g /\ ~ In g (regions_of k)).

(* Hazards core c causes against its own commands, and ownership (one thread, WP). *)
Definition hazard_own (A : run) (c : core) (m : nat) : Prop :=
  (exists i o, nth_error A m = Some (SCpu c i o) /\
   match i with
   | CpuRead r =>                                  (* unready read, 12 item 3 *)
       (exists n, pending A n m /\ issued_by A n c /\ writes_of A n r) \/ not_owned c r
   | CpuWrite r _ =>                               (* same-thread overlap, 12 item 4 *)
       (exists n, pending A n m /\ issued_by A n c /\ (writes_of A n r \/ reads_of A n r))
       \/ not_owned c r
   | Issue k =>                                    (* ownership, 12 item 5 *)
       (exists t, names_any k t /\ ~ owns_tile c t) \/ (exists g, In g (cmd_regs k) /\ ~ owns_reg c g)
   | WaitReady t | TileReady t => ~ owns_tile c t
   | Halt => False
   end) \/
  (exists n k rho, m = S n /\ issued A n c k /\ nth_error A m = Some (SRun n rho) /\
     unregistered k rho) \/
  (* a run of core c's command overlaps, on a register, a pending command where either
     writes: no cited gem5 rule orders device against device on registers (F6) *)
  (exists n n' r g rho, m = S n /\ issued_by A n c /\ nth_error A m = Some (SRun n rho) /\
     n' < n /\ pending A n' m /\ in_reg r g /\
     ((writes_of A n r /\ (reads_of A n' r \/ writes_of A n' r)) \/
      (reads_of A n r /\ writes_of A n' r))).
(* Hazards core c causes against another core's pending commands (two copies, WP). *)
Definition hazard_cross (A : run) (c : core) (m : nat) : Prop :=
  exists i o n c', nth_error A m = Some (SCpu c i o) /\ c' <> c /\ pending A n m /\
    issued_by A n c' /\
    match i with
    | CpuRead r => writes_of A n r                 (* other-thread overlap with a DX100 write *)
    | CpuWrite r _ => writes_of A n r \/ (reads_of A n r /\ exists t, in_tile r t)
    | _ => False
    end.

(* hazard_free_own / hazard_free_cross: per-candidate WP obligations. *)
Definition obl_hazard_free_own : Prop := forall A c m, at_issue_run A -> ~ hazard_own A c m.
Definition obl_hazard_free_cross : Prop := forall A c m, at_issue_run A -> ~ hazard_cross A c m.

(** * 5. The DX100 reduction lemma.  OPEN: proof is ticket 43. *)
Theorem dx100_reduction :
  contracts_ok ->           (* assumption entry: DX100 proof semantics (well-formed contracts) *)
  obl_hazard_free_own -> obl_hazard_free_cross ->
  forall T : run, timed_run T -> complete_timed T ->
    exists A : run, at_issue_run A /\
      (forall c, observations A c = observations T c) /\
      (forall r, final_state A r = final_state T r).
Proof.
  (* OPEN — ticket 43 proves this; it must prove exactly this approved text. *)
Admitted.

End Reduction.
