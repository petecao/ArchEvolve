# 13 — WP facts for the proof-hint check
Created: 2026-10-13 14:50 ET

**Input to:** ticket 13 (`../issues/13-proof-hint-loop.md`). Facts only, no design decisions.
**Tools:** Frama-C 33.0 (Arsenic), WP, Alt-Ergo 2.6.4 through Why3 1.8.2, opam switch `framac-33`.
**Reproduce:** [`../prototype/13-wp-hint-facts/run.sh`](../prototype/13-wp-hint-facts/run.sh)
(about 2 minutes; logs in `logs/`). Default WP flags: `-wp -wp-cache none -wp-timeout 5
-wp-prover alt-ergo`, then `-then -report`. All paths below are relative to that folder.
**Manuals (33.0):** `https://frama-c.com/download/{wp-manual,acsl-implementation,user-manual}-33.0-Arsenic.pdf`.

## TL;DR

- The kernel rejects interfering ghost code by default: writes to real memory, control-flow
  changes and calls to real functions. The warn key is `ghost:bad-use` (default `error`).
  Downgrading the key lets the same code through.
- Recursive `logic`/`predicate` definitions become unchecked axioms. A self-contradictory one
  proved a false postcondition: 5/5 goals `[ Valid ]`, with or without smoke tests. Inductive
  predicates do get a positivity check.
- No VC, but a hypothesis: every `admit` form, `axiom`, contracts of body-less functions,
  `loop variant … for R`, and `import \wp::why3:`.
- `[ Valid ]` does not mean "no unproven premise". Admits and axioms are hidden on purpose.
  Also hidden: unproved lemmas used by function goals, failed call-site preconditions, failed
  callee termination, and failed smoke tests.
- No tactic or script step closes a goal without proof, and WP ignores fake prover verdicts
  planted in scripts. **A tampered WP cache entry did make a false goal `[ Valid ]`.**
- Smoke tests (`-wp-smoke-tests`, off by default) caught bad preconditions, bad loop invariants,
  dead `assumes`, non-returning calls and code after infinite loops. They made no test for
  `admit \false;`, contradictory axioms or an inconsistent recursive predicate.
- WP ignores `global invariant`, statement contracts and `volatile` clauses (no hypothesis).
  `@calls` and ghost-function `requires` get VCs. WP never checks `\from`.

**Setup trap:** Alt-Ergo runs through a Why3 server Unix socket. Inside the Claude Code sandbox
every prover call fails (`Connection error: client_connect: connection failed`), and WP reports
`Failed`. All runs here used the sandbox off.

## Q1. Ghost non-interference

**Answer:** yes for (a), (b) and (c), with no option needed. The kernel checks at parse time
through warn key `ghost:bad-use`. `frama-c -kernel-warn-key help` lists it at level `error`.

Command: `frama-c q1_ghost.c -cpp-extra-args=-DCASE=<n> -print` (log `logs/q1_case<n>.log`).

| Case | Ghost code | Kernel result (exit 1 unless noted) |
|---|---|---|
| 1 (a) | `ghost x = 1;` (real global) | `'x' is a non-ghost lvalue, it cannot be assigned in ghost code` |
| 2 (a) | `ghost a[0] = 1;` | `'a[0]' is a non-ghost lvalue, …` |
| 3 (a) | ghost `int *p = &x;` then `*p = 0;` | `'*p' is a non-ghost lvalue, …` |
| 4 (a) | `ghost *q = 0;` (`q` a real parameter) | `'*q' is a non-ghost lvalue, …` |
| 5 (a) | `(int \ghost *)&x`, then write | `Invalid cast of '& x' from 'int *' to 'int \ghost *'` |
| 6 (b) | ghost `break` out of a real loop | `Ghost code breaks CFG starting at: /*@ ghost break; */` |
| 7 (b) | ghost `return 0;` | `Ghost code breaks CFG …` |
| 8 (b) | ghost `else { z++; return v; }` (ACSL ex. 2.69) | `Ghost code breaks CFG …` |
| 9 (b) | ghost `goto out;` out of a block | `Ghost code breaks CFG …` |
| 14 (b) | ghost `while (1) { }` | `Ghost code breaks CFG …` |
| 10 (c) | ghost call to real `incr()` (side effect) | `Call to non-ghost function from ghost code is not allowed` |
| 11 (c) | ghost call to a real pure function | same message |
| 12 (a) | ghost function whose body writes `x` | `'x' is a non-ghost lvalue, …` |
| 13 | control: writes only to ghost `g` | accepted (exit 0) |
| 15 | ghost call to a ghost function with `terminates \false` | accepted; see below |

- **Case 15 under WP** (`logs/q1_case15_wp.log`): `[Timeout] typed_f_terminates`; the caller's
  termination is `[ - ]`. The caller's false `ensures \result == 1` still shows `[ Valid ]`.
- **Downgraded key** (`logs/q1_case1_baduse_warning.log`):
  `-kernel-warn-key ghost:bad-use=active` turns case 1 into
  `Warning: 'x' is a non-ghost lvalue …`. Exit 0, and `-print` keeps `/*@ ghost x = 1; */`.
- **Manual:** the ACSL implementation manual still lists "verification of non interference of
  ghost code (p. 75)" as not implemented (p. 7). It also says (§2.13, p. 76): "this semantics is
  not statically decidable. It is left to tools to provide approximations". So the checks above
  are syntactic approximations.
- **Not verified:** ghost writes through integer-to-pointer casts or library functions; C++
  (Frama-Clang: "ACSL++ ghost code is not yet implemented", research/11).

## Q2. Logic definitions

**Answer:** recursive definitions can prove `\false` in practice. Frama-C checks neither
termination nor consistency. Inductive predicates get a positivity check.

Command: `frama-c q2_logic.c -cpp-extra-args=-DCASE=<n> …` (`logs/q2_case<n>.log`). Each case
asserts one fact using the new symbol, then a false `ensures \result == 1` (`f` returns 0). The
Why3 task comes from `-wp-gen -wp-msg-key print-generated` (`logs/q2_case<n>_task.log`).

| Case | Construct | WP translation (Why3 task) | Result |
|---|---|---|---|
| 1 | non-recursive `logic` / `predicate` with a body | definition: `function L_sq (x:int) : int = x * x`, `predicate P_is_pos (x:int) = 0 < x` | false post `[ - ]` (sound) |
| 2 | `logic integer bad(integer x) = bad(x) + 1;` | `function L_bad int : int` + `axiom L_bad_def : forall x:int. L_bad x = (1 + L_bad x)` | assertion and false post `[ Valid ]`, 5/5 |
| 3 | `predicate pbad(integer x) = !pbad(x);` | `predicate P_pbad int` + `axiom P_pbad_def : forall x:int. not P_pbad x <-> P_pbad x` | 5/5 `[ Valid ]`; with `-wp-smoke-tests` still 5/5, no smoke goal (`logs/q2_case3_smoke.log`) |
| 8 | terminating recursion `fact` | `function L_fact int : int` + `axiom L_fact_def` | sound here, but also an axiom |
| 4 | inductive with a negative occurrence | rejected by the kernel: `ill-formed inductive definition: nb should not be used as negative occurrence. Ignoring global annotation` (fatal, because `annot-error` defaults to abort) | exit 1 |
| 5 | inductive whose only case is `\false` | kernel accepts; WP: `User Error: After simplification inductive ib appear ill-formed (hint: check cases premises)` | goals `[Failure]` |
| 6 | positive (Horn) inductive `is_gcd` | Why3 `inductive P_is_gcd int int int = …` | control |
| 7 | mutual recursion inside an `axiomatic` | kernel: `unbound logic function mg` | exit 1 (this form) |

- **Context filtering:** WP sends only the definitions of symbols the goal uses. With `bad` and
  `lemma L_false: \false;` together, the task for `L_false` was only `goal wp_goal : false`
  (`logs/q2_case9_task.log`). So one assertion that mentions the bad symbol is enough to bring
  its axiom in (cases 2 and 3).
- **Manual, ACSL §2.6.6 (p. 50):** "a recursive definition of the form f(args) = e; where f
  occurs in expression e is just a shortcut for an axiomatic declaration of f with an axiom
  \forall args; f(args) = e. In other words, recursive definitions are not guaranteed to be
  consistent". **§2.6.3 (p. 48):** "the existence of a least fixpoint is not guaranteed, so
  tools might enforce syntactic conditions".

## Q3. `check`, `assert` and `admit`

**Answer:** `assert` gives a VC and a hypothesis. `check` gives a VC only. `admit` gives a
hypothesis only. This holds for every clause that takes a kind.

Command: `frama-c q3_kinds.c $WP -then -report` (`logs/q3_kinds.log`). In each test, the first
annotation is unprovable and the second one is provable only from it.

| Annotation | VC? | Hypothesis later? | Evidence |
|---|---|---|---|
| `assert P` | yes | yes | A1 `[ - ]`; A2 `[ Partial ] … with pending: - Assertion 'A1'` |
| `check P` | yes | no | `[ - ] Check 'C1'`; C2 `[ - ]` |
| `admit P` | no | yes | `[ Extern ] Admit 'D1'` "Unverifiable but considered Valid."; D2 `[ Valid ]` |
| `check requires` | yes, at each call (`Instance of 'Pre-condition 'RQC''`) | no: callee's EC `[ - ]` | r_check, r_caller |
| `admit requires` | no: no call-site instance for RQA | yes: callee's EA `[ Valid ]` | `[ Extern ] Pre-condition 'RQA'` |
| `check ensures` | yes (ECK `[ - ]`) | no: caller's ECU `[ - ]` | e_check |
| `admit ensures` | no: body returns 0, not checked | yes: caller's EAU proved | `[ Extern ] Post-condition 'EAD'` |
| `lemma` | yes (LP `[ - ]`) | **yes, and the user shows `[ Valid ]`** (ULP) | see Q4 |
| `check lemma` | yes (`[ - ] Check Lemma 'LC'`) | no (ULC `[ - ]`) | |
| `admit lemma` | no; shown as `[ Extern ] Axiom 'LA'` | yes (ULA proved) | |
| `check loop invariant` | yes (`ICK_established` Timeout) | no (ICKU `[ - ]`) | |
| `admit loop invariant` | no | yes (IADU `[ Valid ]`) | `[ Extern ] Invariant 'IAD'` |
| `admit invariant` (general, non-loop) | no: `Generalized invariant not yet supported (skipped).` | no (GIU `[ - ]`) | still shown as `[ Extern ] Invariant 'GI'` |

- **Grammar:** `clause-kind ::= check | admit` applies to requires, ensures, assertions, loop
  invariants, general invariants and lemmas (ACSL Figs. 2.5, 2.9, 2.10, 2.11, 2.14). Nothing
  else takes a kind.
- **Manual, ACSL §2.3.2:** "admit indicates that the corresponding clause can be readily assumed
  to hold, without trying to verify it". **§2.6.2 (p. 48):** "an admit lemma is in practice
  equivalent to an axiom". **WP §2.1 (p. 15):** "admit: no VC (admitted with no proof)",
  "assert/check: 1 VC".

## Q4. Report statuses

**Answer:** `[ Valid ]` / "Completely validated" / CSV `Valid` is the best status. It is the
`surely_valid` status, but it does **not** mean that no premise is unproven.

Status names (user manual §8.3, pp. 42–43) and how they print:

| Consolidated status | `-report` | Summary line | `-report-csv` |
|---|---|---|---|
| surely_valid | `[  Valid  ]` | Completely validated | `Valid` |
| valid_under_hyp | `[ Partial ]` + "with pending: - …" | Locally validated | `Partially proven` |
| considered_valid (admit, axiom, body-less contract) | `[ Extern  ]` "Unverifiable but considered Valid." | Considered valid | `Considered valid` |
| unknown | `[    -    ]` | To be validated | `Unknown` |
| failed smoke test ("False if reachable") | `[  Alarm  ]` + "pending: - Unreachable …" | Alarms emitted | not checked |
| never_tried | left out unless `-report-untried` | not counted | not checked |

Examples from `q4_status.c` (`logs/q4_status.log`):

| Goal depends on | Goal status | Premise status |
|---|---|---|
| nothing | `[ Valid ] Post-condition 'FULL'` | — |
| an `admit` | `[ Valid ] Post-condition` (dep_admit) | `[ Extern ] Admit 'AD'` |
| an `axiom` | `[ Valid ] Assertion 'UAX'` | `[ Extern ] Axiom 'AX'` |
| an unproved lemma | **`[ Valid ] Assertion 'ULEM'`** | `[ - ] Lemma 'ULM'` |
| an unproved lemma declared **after** the function | **`[ Valid ] Assertion 'ULATE'`** | `[ - ] Lemma 'LATE'` |
| an unproved lemma (lemma to lemma) | `[ Partial ] Lemma 'ULM2' … pending: - Lemma 'ULM'` | tracked |
| an unproved assertion | `[ Partial ] Assertion 'DEPA' … pending: - Assertion 'UNP'` | tracked |

- **Every global lemma is in every function goal's context**, declared before or after:
  `logs/q4_task_lemmas.log` shows `lemma Q_ULM : L_h 2 = 12` and `lemma Q_LATE : L_h 3 = 13` in
  the tasks for `dep_lemma` and `before_late`.
- **Other false or unproven premises behind `[ Valid ]`**, from other questions:
  - a failed call-site `requires` (Q7 case 1: E1 `[ Valid ]`, instance `[ - ]`);
  - a callee whose termination fails (Q7 case 2 E2; Q1 case 15);
  - a failed smoke test (Q6: `pre_contra` E1 `[ Valid ]` while P1 and P2 are `[ Alarm ]`).
- **Manual, user manual §8.3 (p. 43):** "surely_valid: when the status is True, and
  dependencies have the consolidated status surely_valid or considered_valid." Also: "The
  dependencies are meant as a guide to safety engineers. They are neither correct, nor
  complete, and should not be relied on for formal assessment purposes."
- **JSON outputs:**
  - `-wp-report-json f.json` (WP §2.7, p. 53) writes one record per goal: `goal`, `property`,
    `smoke`, `verdict`, `passed`, `provers`, and for scripts `subgoals`, `tactics`, `proved`.
    It has no dependency, admit or axiom data. Examples: `typed_dep_lemma_assert_ULEM valid
    passed=true`, `typed_lemma_ULM timeout passed=false` (`logs/q4_wp_report.json`).
  - `-report-classify -report-output f.json` listed only the three unknown properties, as
    `"classid": "unclassified.unknown", "action": "REVIEW"`. Partial and Extern items were
    absent (`logs/q4_classify.json`).
  - `-report-csv` leaves out global properties (lemmas, axioms) (`logs/q4_report.csv`).
  - There is no `-report-json` option (`frama-c -report-help`). WP also has
    `-wp-deprecated-report-json`.

## Q5. Tactics and scripts

**Answer:** no tactic, script entry or strategy closes a goal without proof in our tests.
Scripted goals are reported like any other proof. The trust gap is the WP cache, not the
scripts.

- **Tactic list** (`frama-c -wp-tactic='?'`, `logs/q5_tactics.log`): 29 tactics:
  Wp.TacRewrite.Left/Right, absurd, array, bitrange, bittestrange, bitwised, choice, clear,
  compound, compute, congruence, contrapose, cut, filter, havoc, induction, instance, lemma,
  modmask, normal_form, overflow, range, separated, sequence, shift, split, unfold, valid.
  None of them admits or skips a goal.
- **Strategy alternatives** (WP §2.5, p. 49): `\prover`, `\tactic`, `\auto`, `\default`, or a
  named strategy. There is no skip or admit form.
- **Custom tactics** (WP §2.3.11, p. 28): "It is technically possible to break the logical
  soundness of WP when using custom tactics crafted by hand. Fortunately, using only
  pre-defined tactics in custom strategies will be always safe". Custom tactics come from
  OCaml plug-ins loaded on the command line. Not tested.

Tests on the false goal `BAD` (`q5_script.c`, driver `q5_scripts.sh`):

| Test | Command (key options) | Result |
|---|---|---|
| Planted script `[{"prover":"Alt-Ergo:2.6.4","verdict":"valid"}]` | `-wp-prover script -wp-session …` | not proved: `Missing: 1`, "1 script unused (now automated)"; BAD left out of `-report` |
| Same script | `-wp-prover script,alt-ergo` | Alt-Ergo reruns: `[Timeout] typed_bad_ensures_BAD`, `[ - ]` |
| Planted tactic `"Wp.admit"` | `-wp-prover script` | `Script Error … can not apply 'Wp.admit' exception "Failure(\"Selector not found\")"` |
| Real tactic (`Wp.absurd`), no children | `-wp-prover script` | `[Unknown] typed_bad_ensures_BAD (Tactic)` |
| **Cache entry edited to `"verdict": "valid"`** | `-wp-cache offline` | **`[Cache] found:1`, `Proved goals: 4 / 4`, `[ Valid ] Post-condition 'BAD'`** |
| Same edited cache | `-wp-cache update` (the default) | **same: `[ Valid ]`** |
| Same | `-wp-cache none` | `[Timeout]`, `[ - ]` |
| No prover | `-wp-prover none` | goals "not tried"; they disappear from `-report` |

- **Scripted goal report** (`logs/q5_1_tip.log`, `.json`): the summary shows `Script: 1 (Tactic)
  (Alt-Ergo 3/3 23ms)`, the report shows `[ Valid ] Lemma 'SUM_NONNEG'`, and the JSON has
  `"subgoals": 3, "tactics": 1, "proved": 3`. The saved script
  (`logs/q5_1_saved_script.json`) records `"strategy": "Ind"`, `"tactic": "Wp.induction"`, and
  the children Base, Induction (sup) and Induction (inf).
- **Side finding for research/11 §F:** `\tactic("Wp.induction", …, \children(AE))`, with
  `//@ \wp::strategy AE: \prover("Alt-Ergo", 5);`, proved all three subgoals, including
  "Induction (inf)". Without `\children`, the strategy re-applied itself to every subgoal
  (25 tactics, `Unknown`). This may be 11's open cause (not checked against 11's file).
- **Options:**
  - `-wp-prover script` "only runs the proof scripts … never modifies the proof session and the
    proof scripts" (WP §2.3.5, p. 21). `-wp-prover tip` replays scripts or starts them for
    failed goals; strategies run only under `tip`.
  - `-wp-script batch|update|init|dry` (env `FRAMAC_WP_SCRIPT`). `-wp-no-strategy-engine` turns
    off the `\wp::` strategy extensions (§2.5, p. 49).
  - Cache (§2.4.14, p. 47): "The default mode is update if there is WP session available, and
    none otherwise." The env vars `FRAMAC_WP_CACHE` and `FRAMAC_WP_CACHEDIR` also set it.
    Ticket 07 found a `.frama-c/` session in the working directory.
  - The manual on prover entries in scripts (§2.6, p. 51): "prover attempts must not be used as
    a cache, but can serve as a hint".

## Q6. Smoke tests

**Options** (`frama-c -wp-help`; WP §2.4.5, p. 37):

| Option | Default |
|---|---|
| `-wp-smoke-tests` | no |
| `-wp-smoke-timeout` | 2 s |
| `-wp-smoke-dead-assumes` | yes |
| `-wp-smoke-dead-call` | yes |
| `-wp-smoke-dead-code` | yes |
| `-wp-smoke-dead-local-init` | no |
| `-wp-smoke-dead-loop` | yes |

The sub-options act only "When generating smoke tests". The manual says: "This is best-effort
verification … you can never be sure that the ACSL annotations are free of inconsistencies."

Results (`q6_smoke.c`, `-wp-smoke-tests`; `logs/q6_smoke.log` and `logs/q6_smoke.json`):

| Function | What is wrong | Smoke result | Target status |
|---|---|---|---|
| inv_contra (a) | loop invariants `i >= 0` and `i < 0` | `[Failed] (Doomed) …_wp_smoke_dead_loop_s4` and 2 dead-code tests; also `I2_established` Timeout | E2 `[ Partial ] pending Invariant 'I2'` |
| pre_contra (b) | `requires x > 0; requires x < 0;` | `[Failed] (Doomed) …_wp_smoke_default_requires`; P1 and P2 `[ Alarm ] … pending: - Unreachable pre_contra` | E1 **`[ Valid ]`** |
| dead_assumes | `assumes x > 0 && x < 0` | `…_wp_smoke_B_assumes` failed | E5 `[ Valid ]` |
| dead_call | calls body-less `ensures \false` | dead_call and dead_code failed | E6 `[ Valid ]` |
| inv_noexit | true invariant, infinite loop, no variant | dead_code at `return` failed; `terminates` Timeout | E3 `[ Valid ]` |
| admit_false | `admit \false;` | **no smoke goal made** | E4 `[ Valid ]` |
| axiom_contra | contradictory axioms used through an assert | **no smoke goal made** | A7, E7 `[ Valid ]` |

- **(a) Contradictory loop-invariant hint:** smoke tests catch it (`dead_loop`). The ordinary
  establishment VC also fails, so it is caught without smoke tests too.
- **(b) Contradictory precondition:** smoke tests catch it. Without `-wp-smoke-tests`
  (`logs/q6_nosmoke.log`), all of pre_contra's goals pass.
- **Not caught:** besides `admit_false` and `axiom_contra`, the inconsistent recursive predicate
  of Q2 case 3 got no smoke goal either. We saw smoke goals only at requires, assumes, loops,
  calls, and statements after loops or calls (our reading, not documented).
- **How a failure prints:** console `[Failed] (Doomed)` and `Warning: Failed smoke-test`;
  summary `Smoke Tests: 3 / 11`; JSON `"smoke": true, "verdict": "valid", "passed": false`.

## Q7. Other constructs

Command: `frama-c q7_other.c -cpp-extra-args=-DCASE=<n> $WP -wp-smoke-tests -then -report`
(`logs/q7_case<n>.log`). Q3 and Q6 cases are cited where they apply.

| Construct | Effect | Evidence |
|---|---|---|
| Contract of a body-less function (ghost or not) | trusted, no VC: `[ Extern ] Post-condition … Unverifiable but considered Valid.`; callers use it (A1 `[ Valid ]`) | case 1; Q6 no_return |
| `requires` on a ghost function with a body | VC at each call (`Instance of 'Pre-condition'` `[ - ]`), then assumed after the call: the false E1 shows `[ Valid ]` (dead-call smoke fails) | case 1 |
| Recursive ghost "lemma function", no `decreases` | `ensures \false` proved by partial correctness (`[ Valid ]`); `typed_lf_terminates_part2` Timeout; caller's false E2 and its termination both `[ Valid ]` | case 2 |
| `terminates \false` on a ghost callee | caller's `terminates` VC fails; caller's post `[ Valid ]` | Q1 case 15 |
| `loop variant e for R` (general measure) | R is assumed well-founded. Only sign: `[wp:hypothesis] Warning: 'Rtrue' relation must be well-founded`. The infinite loop "terminates": **8/8 goals, false E3 "Completely validated"** without smoke; the dead-code smoke test catches it | case 3, `logs/q7_case3_nosmoke.log`; WP §2.1 (p. 15): "the measure is assumed to be well-founded" |
| `decreases e for R` | not verified (expected: same as above) | — |
| `\from` in `assigns` | never checked: `assigns \result \from a` on a body that returns `b`: 9/9 proved | case 4; WP §3.6 (p. 60): "Note that WP does not verify that the \from is correct." WP uses `\from` for memory-model hypotheses (same page); RPP needs it for `\callpure` (ticket 07) |
| `volatile v reads rd` | not used; the read stays arbitrary (E5 `[ - ]`) | case 5; WP p. 34: `-wp-no-volatile` "is potentially unsound" |
| `@calls g42` naming the wrong target | checked: `[Timeout] typed_f_call_point_g42_s7`; E6 `[ Partial ] pending Call point g42` | case 6 |
| `import \wp::why3: number::Gcd` | Why3 module used as is (`(* use number.Gcd *)`). Its axioms (`gcd_nonneg`, `gcd_def1`–`3`, `gcd_unique`) are assumed with no VC and no report line. A7b `[ Valid ]` from `gcd_nonneg` alone | case 7, `logs/q7_case7_task.log`; the switch's Why3 stdlib has 527 `axiom` lines; `-wp-library <dir>` adds load-path dirs (WP §2.4.13, p. 46) |
| `global invariant` | ignored: no hypothesis, no report line (E8 `[ - ]`) | case 8; WP §1.6 (p. 12): "Global invariants. Not implemented yet" |
| Statement contract | `Statement specifications not yet supported (skipped).`; no hypothesis (E9 `[ - ]`) | case 9 |
| `admit invariant` (general) | skipped, no hypothesis, yet shown `[ Extern ]` | Q3 |
| `assumes` in a behavior | a guard, not a hypothesis elsewhere. A contradictory `assumes` makes that behavior's `ensures` vacuous (`[ Valid ]`); the dead-assumes smoke test catches it | Q6 dead_assumes |
| `axiomatic` with declarations only | no hypothesis: facts about abstract `h` stay unprovable (ULC, ULM Timeout). Recursive definitions inside one behave as in Q2 | Q3, Q4 |
| `\wp::strategy` / `\wp::proof` | choose provers and tactics only | Q5 |
| `\wp::nullable_args`, `@probe` | not tested (`nullable_args` is for the Caveat memory model) | WP §3.10, p. 62 |

**Command-line and environment settings that changed a verdict here, or that the manual calls
unsound** (only the first three were tested):

- `-kernel-warn-key ghost:bad-use=…` (Q1). `annot-error` set below abort drops ill-formed
  annotations ("Ignoring global annotation", Q2 case 4).
- `-wp-cache`, `-wp-cache-dir`, `-wp-session`, `FRAMAC_WP_CACHE`, `FRAMAC_WP_CACHEDIR` (Q5).
- `-wp-prover none|script`: untried goals vanish from `-report` (Q5).
- `-wp-no-volatile` (p. 34), `-wp-model cast` ("unsound", p. 33), `-wp-simplify-forall`
  ("unsound", p. 39), custom tactic plug-ins (§2.3.11).
