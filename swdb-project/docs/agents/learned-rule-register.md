# Register of learned agent rules

Updated: 2026-10-16 22:20 ET. Owner: Yan-Ru Jhou. Origin: the 2026-10-08–09 LANL
analytic-evaluator session and its retrospective; revised after the 2026-10-11–12
LANL-shaped-db, 2026-10-15 Probata and 2026-10-16 Probata ticket 07 retrospectives.

The executable instructions are in
[learned-workflow.md](../../../.claude/rules/learned-workflow.md); audit them using
the [procedure below](#audit-procedure).
This register records why each lesson exists and how it can become unnecessary.
It grants no execution, deletion, scope or scientific-admission permission.

## Lifecycle

- **active:** the reminder still affects behaviour; its instruction is in the rule file.
- **automated:** a required check now covers the incident; replace the instruction
  with a short navigation pointer only if one is needed to discover that check.
- **retired:** the lesson's trigger no longer applies or another authoritative
  rule covers it. Remove its instruction from the active file and keep the reason here.

An enforced check can replace a mechanical reminder. For a judgement call, use
relevant later sessions and the current task definition to assess whether the
instruction adds value. Absence of incidents without comparable opportunities
is insufficient. Retiring these reminders preserves the spec, owner policies,
permissions and scientific thresholds they point to.

## Review register

Initial assessment: 2026-10-09 ET. Latest review: 2026-10-16 ET.
Review after: 2026-10-22 ET; then weekly.
The date prioritizes an audit, not automatic expiry. Update an entry's review
date with a substantive decision; a healthy, unchanged audit needs no date-only
commit. Scheduled audits may remain quiet.

| ID | State | Evidence required to replace or retire the reminder |
|---|---|---|
| LR-01 | active | Tickets close against their own criteria; claims bind exact source and retained evidence, distinguish actual runs from offline checks, and make additional research scope explicit. Spike evidence stays proportionate (verdict, inputs, hashes, run folder) in later comparable sessions. |
| LR-02 | active | A mandatory launch check enforces the applicable pilot/admission requirement and rejects an ineligible pair; cite its regression and where it runs. |
| LR-03 | active | Test selection distinguishes component and real-verifier work; dependency-closed fixtures, relevant tool/watchdog preflight and cheap report-reader checks cover the observed failures. |
| LR-04 | active | Recurring mechanical checks run in the normal workflow; failure diagnosis and selection make broad reruns depend on changed code or unresolved failures. A launcher records one review per method version before launch. |
| LR-05 | active | Status and resume summaries derive from tickets; pause checks release unfinished claims, preserve resume commands and stop the effort's heartbeat. A tracker check fails on a resume section over 30 lines. |
| LR-06 | active | Output lifecycle tooling enforces destination capacity and verified disposable cleanup while preserving every required future reader. |
| LR-07 | active | A committed runner enforces memory-sized workers, shared slots, RSS caps, timeouts and incremental structured results; independently checked long runs post scheduled status tables and report missed intervals. |
| LR-08 | active | Normal integration and closeout checks enforce the remote-branch budget, keep worker branches local and retire eligible idle refs/worktrees under the existing recovery and reader checks. A PreToolUse hook blocks stash/reset/path checkout in the shared primary checkout. |
| LR-09 | active | Proof, optimization and measurement launchers run a target self-check (preconditions satisfiable, postconditions true on concrete known-good runs) and refuse a refuted target; cite the check and where it runs. |
| LR-10 | active | Judgment call. Retire only if later comparable efforts reach a checkpoint report on their own (trend, suspected premise, options) before three attempts pass without a step change. |

Partial improvements justify narrowing an instruction; they do not automatically
retire the entire lesson. New lessons need a concrete observed incident, a trigger,
and a review/retirement criterion. Edit an existing entry when the incident matches
it instead of adding another nearly identical rule.

## Incident evidence

- **LR-01:** [ticket 17's final answer](../../.scratch/lanl-db-analytic-eval-2026-10-06/issues/17-agreement-report.md)
  closes its negative report. [Ticket 24](../../.scratch/lanl-db-analytic-eval-2026-10-06/issues/24-prospective-blind-dx100-pair.md)
  separates the prospective study. Read their current statuses instead of caching them here.
- **LR-02:** [the study spec, D35](../../.scratch/lanl-db-analytic-eval-2026-10-06/spec.md)
  records that campaigns with unknown estimates yielded zero eligible pairs.
  [The retained audit](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-actual-input-assembly-and-refused-strict-audit-20261009-a5/README.md)
  refused missing ordered outcome metadata. Spec text alone is not a wired launch check.
- **LR-03:** commits `3ee74f7b` and `7952578d` replace repeated full-catalog fixture
  copies with [Records.copy_closure](../../tests/conftest.py). The latter commit
  records a 600-second timeout changing to a 39-second pass. This is a partial fix;
  inspect later fixtures and the selected tool environment when auditing.
- **LR-04:** the session retained a refactor NameError in its
  [composition note](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-prospective-count-model-admission-20261009/README.md)
  and a copied configuration hash in the
  [P3 note](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-third-original-full-index-20261009-a5/README.md).
  Initial inspection found no active Git hook or CI workflow. Recheck current
  configuration; this observation does not imply future absence.
- **LR-05:** the session log contained 49 heartbeat prompts totalling about
  778,000 characters and 43 compactions at the retrospective checkpoint.
  Repeated histories in resume, progress and heartbeat prompts obscured current
  state. Preserve original evidence through links rather than repeated bodies.
- **LR-06:** [verified disposable cleanup](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-authorized-disposable-disk-reclaim-20261009-a5/README.md)
  recovered about 6.1 GiB from old fixture trees and caches. Required source,
  validation and custody bodies remained. A hash does not supply those bodies to
  their future readers.

- **2026-10-11–12 LANL-shaped-db session** (map:
  [lanl-shaped-db](../../.scratch/lanl-shaped-db-2026-10-09/map.md), follow-ups:
  [map](../../.scratch/lanl-shaped-db-followups-2026-10-11/map.md)):
  - **LR-01:** tickets closed against their criteria, but three follow-ups were split into
    new tickets that Yan-Ru then asked to finish; Yan-Ru wants in-ticket completion.
  - **LR-03:** pytest-xdist was found missing after a costly run; an mbit10 suite was
    rerun after mass setup errors before their cause (the `mbit10` host guard) was named.
    About 140 full-catalog-copy tests remain.
  - **LR-06:** on mbit10 the suite wrote ~850 MB of source snapshots to
    `/data1/yanruj/EvolveSWDB_sources`, outside its temp folder (2026-10-12, ticket 02).
  - **LR-07 (new):** a full-suite run helped exhaust the Mac's RAM (restart, 2026-10-11
    ~18:30 ET); a `-n 16` mbit10 run hit node-0 OOM kills; an overnight stall went
    unnoticed for ~9 h because the session heartbeat did not fire; one run lost all
    results to a timeout; Yan-Ru had to ask for status repeatedly.

- **2026-10-15 Probata session**:
  - **LR-01/05:** the [closeout review](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/closeout-code-review-20261015.md)
    preserves incomplete acceptance criteria; the [handoff](../../.scratch/probata-proof-of-concept-2026-10-13/HANDOFF.md)
    records the controlled pause and remaining frontier.
  - **LR-03/04:** the [query composition evidence](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/wp-footprint-query-20261015.json)
    records two watchdog sandbox failures and their isolated retries. The
    [member-lifetime evidence](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/t24-member-lifetimes-mac-20261015.json)
    preserves a test-only optional-field error and an offline assertion replay
    against the unchanged proof record.
  - **LR-07:** the [bounded validation receipt](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/closeout-validation-20261015.json)
    records resource-guarded controls. The shared launcher used in the session
    remained under `/tmp`; this rule revision installs no committed launcher,
    test profiles or tracker generator.
  - **LR-08 (new):** the [completion receipt](../../.scratch/probata-proof-of-concept-2026-10-13/evidence/closeout-complete-20261015.json)
    records removal of 30 remote branches, 53 local branches and 33 idle worktrees.
    Yan-Ru requested minimal remote branches. The rule budgets published refs,
    keeps ticket branches local and points to the existing cleanup policy;
    [recovery procedures](../../.scratch/probata-proof-of-concept-2026-10-13/prototype/closeout/README.md)
    retain historical source and required readers.

- **2026-10-16 Probata ticket 07 session** (ticket:
  [07](../../.scratch/probata-proof-of-concept-2026-10-13/issues/07-spike-wp-agent-hints.md), "Final Answer"):
  - **LR-09 (new):** the stand-in's postcondition `pushed_are_new` was false (`\old` read the queue entry
    in the pre-state). Counted runs 1-26 over about 3 days tried to prove it; a bounded falsifier run on
    concrete inputs refuted it in about 10 s.
  - **LR-10 (new):** 23 method versions and 26 counted runs ran without a premise check while the best set
    stayed at 19-29 open goals; standing autonomy instructions pushed toward continuing.
  - **LR-01/04:** before the pause, about 20 hours produced admission packets, observers and reviews of
    reviews with no counted run; after Yan-Ru approved one review per method, four counted runs (27-30)
    fit in one afternoon.
  - **LR-05:** the ticket reached 1,943 lines; each resume began by reading two persisted 140 KB outputs.
  - **LR-08:** a test-comparison command ran `git stash` in the shared primary checkout and dropped
    another effort's settings-recovery stash ref (restored from its object).

## Audit procedure

1. Read current rule files, this register, repository instructions and Git status.
   Inspect the relevant implementation/checks and recent comparable session evidence.
   Reach historical evidence only for the lesson being assessed.
2. For every active lesson, choose **keep**, **revise**, **automate** or **retire**.
   Cite evidence, expected benefit, the proposed text change and any remaining gap.
   Check duplication, conflicts, broken pointers and whether the instruction changes behaviour.
3. Keep owner policy separate from session-derived reminders. Scheduled audits
   are read-only: report actionable proposals; do not edit files, commit, push,
   run scientific evaluations, clean disks or restart paused project work.
4. For a user-requested update, apply only supported changes to the learned-rule
   files and this register within the granted scope. Existing human/owner rule files
   require their own applicable authorization. Validate links and active IDs afterward.
5. Keep the rule files compact: one meaning per sentence, no fixed word count. This
   register can retain retired rationale. Record substantive changes with date,
   evidence and why the change preserves the original requirement; unchanged
   audits need neither a report file nor a commit.

On-demand request: **"Audit the learned agent rules using the lesson register."**
For a scheduled run with no actionable finding, stay quiet. An overdue review
date alone is not an actionable defect or permission to remove a rule.

## Changes

- 2026-10-09 ET: introduced six active lessons, their retirement evidence and
  read-only weekly/on-demand audit procedure. Existing owner rules were preserved.
- 2026-10-12 20:10 ET (Yan-Ru approved): revised LR-01 (finish in-ticket; new tickets
  only on request), LR-03 (tool preflight incl. xdist; diagnose mass failures before a
  rerun), LR-06 (count output written outside temp folders); added LR-07 (long-running
  jobs: memory-sized workers, incremental results, 30-minute status tables). LR-02, LR-04
  and LR-05 kept unchanged.
- 2026-10-15 ET (Yan-Ru approved): revised LR-01–07 for evidence boundaries,
  relevant preflight, cheap report-reader checks, selective reruns, explicit pause
  handling and guarded progress reporting; added LR-08 with zero new remote
  branches by default and at most one additional integration branch per active
  effort. Worker branches stay local. Existing owner cleanup policy and scientific
  acceptance requirements remain in force. All lessons remain active; executable
  enforcement is still required before marking them automated. Removed the stale
  pointer to the absent `rule-maintenance.md`; the audit procedure remains here.
- 2026-10-16 22:20 ET (Yan-Ru approved, ticket 07 retrospective): revised LR-01 (evidence sized to the
  ticket type), LR-04 (one review per method version; changes outside the verdict path reviewed in the
  diff), LR-05 (resume section at most 30 lines; history in dated evidence files), LR-08 (ticket work
  in its own worktree; the shared primary checkout keeps other sessions' work and stash entries); added
  LR-09 (check the target first) and LR-10 (convergence checkpoint). Scientific acceptance criteria,
  owner policies and permissions are unchanged; LR-01's evidence requirement still binds every verdict.
- 2026-10-16 22:40 ET (Yan-Ru approved): the audit procedure's 450-word budget (set 2026-10-09 in
  `cf62317e`, no measurement behind it) is replaced by compactness: one meaning per sentence, no fixed
  word count.
