# Register of learned agent rules

Updated: 2026-10-09 ET. Owner: Yan-Ru Jhou. Origin: the 2026-10-08–09 LANL
analytic-evaluator session and its retrospective.

The executable instructions are in
[learned-workflow.md](../../../.claude/rules/learned-workflow.md); their audit
trigger is in [rule-maintenance.md](../../../.claude/rules/rule-maintenance.md).
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

Initial assessment: 2026-10-09 ET. Review after: 2026-10-16 ET; then weekly.
The date prioritizes an audit, not automatic expiry. Update an entry's review
date with a substantive decision; a healthy, unchanged audit needs no date-only
commit. Scheduled audits may remain quiet.

| ID | State | Evidence required to replace or retire the reminder |
|---|---|---|
| LR-01 | active | Later report tickets consistently close against their own criteria; the ticket/review workflow makes additional research scope explicit. |
| LR-02 | active | A mandatory launch check enforces the applicable pilot/admission requirement and rejects an ineligible pair; cite its regression and where it runs. |
| LR-03 | active | Component fixtures select validated dependency closures by default, and tool preflight/setup diagnostics remove the observed failure mode. |
| LR-04 | active | The recurring checks are wired into the normal commit/CI workflow; required checks and their navigation pointers cover this reminder. |
| LR-05 | active | Current status and resume summaries have one authoritative update path; contradiction/staleness checks prevent older prose overriding current tickets. |
| LR-06 | active | Output lifecycle tooling enforces destination capacity and verified disposable cleanup while preserving every required future reader. |

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
4. For a user-requested update, apply only supported changes to the two learned-rule
   files and this register within the granted scope. Existing human/owner rule files
   require their own applicable authorization. Validate links and active IDs afterward.
5. Keep the combined active rule files near their initial 450-word budget. This
   register can retain retired rationale. Record substantive changes with date,
   evidence and why the change preserves the original requirement; unchanged
   audits need neither a report file nor a commit.

On-demand request: **"Audit the learned agent rules using the lesson register."**
For a scheduled run with no actionable finding, stay quiet. An overdue review
date alone is not an actionable defect or permission to remove a rule.

## Changes

- 2026-10-09 ET: introduced six active lessons, their retirement evidence and
  read-only weekly/on-demand audit procedure. Existing owner rules were preserved.
