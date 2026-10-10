# 47 — Extensa-mode design session

Created: 2026-10-03
Updated: 2026-10-03 ET (resolved)
**Type:** task
**Status:** resolved
**Blocked by:** 03 (resolved)
**Spec:** `../spec.md`

**What to build:** An agent drafts, and Yan-Ru decides, the open Extensa-mode details, then readies the Extensa tickets.

## Acceptance

- [x] The exact port boundary (modules ported and not ported) is decided.
- [x] The native repetition count, the Extensa campaign file format, the summary record shape, each workload class's graph per target, and how candidate artifacts per class and target count against the provider-call budget are decided.
- [x] Tickets 48–58 are revised and moved from needs-triage to ready; send tickets are added for drafts meant for teammates.
- [x] One commit. Yan-Ru delegated the decisions and the commit on 2026-10-03.

## Comments

- 2026-10-03 ET: Yan-Ru delegated this ticket's decisions to the agent ("make a reasonable choice, note it, continue"). Status moved from ready-for-human to claimed, then resolved. Every decision is agent-decided under that delegation and revisable.

## Answer

The decisions are in [extensa-design-2026-10-03.md](../extensa-design-2026-10-03.md) (D1–D12). Each is agent-decided under Yan-Ru's 2026-10-03 delegation and revisable.

- **Port boundary (D1).**
  - Ported from MemAcc `af3d6d7f7a69a72facdc3b95b42e78c952f44a76`:
    - loop accounting (`refiner/a5/search.py`, `leakage.py`);
    - runtime-probe emission (`legality_testing/contract_check.py`, `dsl_contract.py`);
    - the certification-profile data model;
    - CPU synthesis for the pack, regroup, gather and bin-drain families;
    - the base pack, binning, relabel, regroup and gather-staging bodies.
  - Not ported:
    - the agent runtime, timing and speed rule;
    - the A5 study gates (`a5/loop.py`, `selection.py`);
    - Z3/SMT, the K3 and L4 evaluators, the clang `dyncheck` tool and non-CPU targets.
- **One target per campaign (D2).**
- **Native protocol (D3).** 10 paired repetitions, sources `[0, 1234, 7777]`, 1 thread, behind an A/A pilot gate. Spread is range/median, so more repetitions cannot fix it.
- **Graphs (D4).** Native uses Kronecker 22 (new record) and `bfs-20260925-uniform22`. gem5 uses ticket 29's `kronecker18-s0` and `uniform18-s0` with source 0. Every result is labeled "single graph per class".
- **Campaign file (D5).** `swdb.extensa-campaign.v1` YAML under `campaigns/extensa/`.
- **Summary (D6).** A new `campaign_summary` record kind.
- **Provider calls (D7).** One rewrite call yields one patch and one candidate artifact per class through per-class knobs, at no extra cost. Repairs, test generation and synthesis are charged. The cap is 3 per iteration plus 1 setup call, and usage-limit or login failures are not counted.
- **Ticket changes.** Tickets 48–58 are revised and ready-for-agent. Ticket 02 is removed as a blocker under the Q66 assumption, and the go-ahead on 56–58 is recorded as granted on 2026-10-03.
- **Send tickets.** Ticket 59 (ready-for-human) sends Peter the design note and ticket 60 (ready-for-human, blocked by 58) sends the "is the specification enough?" finding. Yan-Ru sends both manually.
- **Effort (D12).** About 59 h of work and about 25 lane-hours.
