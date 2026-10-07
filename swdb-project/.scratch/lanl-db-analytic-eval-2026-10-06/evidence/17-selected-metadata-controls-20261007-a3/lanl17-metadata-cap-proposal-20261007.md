# Ticket17 metadata deadline proposal

2026-10-07 ET. Parent review pending; no cap selected, helper rewritten, CLI/SSH action or17freeze/campaign run. Existing09136/31e, supervisor32a021, all old/actual cleanup receipts and C/F6 remain immutable. AdjacentJSON seals the source sites and arithmetic (`83c0b4f1…`).

The completed modela3 stages provide administrative evidence: BCfreeze1266.086s, four forecasts729.741/773.625/796.940/834.880s, publicvalidation326.655s,672canonical records totaling574,754,793B. Parent verified these actual stages and released the lane; compact Git export is pending when this proposal is written. These are past metadata costs. They do not predict future work, scale by record count/bytes or alter a latency model/application outcome.

| Real helper metadata call | Count on successful path | Existing cap (s) | Proposed finite cap (s) |
|---|---:|---:|---:|
| Prepare validate-before-freeze | 1 | 1,400 | 3,600 |
| Prepare population-freeze | 1 | 1,400 | 6,000 |
| Finalize campaign validation | 4 | 1,400 | 3,600 each |
| Finalize conditional public campaign-export | 0–4 | 900 | 6,000 each |
| Finalize agreement-report | 1 | 1,200 | 14,400 |
| Finalize final-export validation | 1 | 1,400 | 3,600 |

These are conservative administrative choices, not statistical margins or duration upper bounds. Validation gets one finite hour, independent freeze/export gets100minutes, and the cross-store agreement report gets four hours. Report reads/validates all four actual campaign stores plus the full base, then validates the enriched writer and rebuilds its index; it also replays summaries/ledgers during validation. No evidence supports retaining the arbitrary900/1200 remnants after catalogue enrichment. Existing Git/df/ps commands keep their120s caps and official --version keeps10s; changing the global command default would also touch dispatch/campaign behavior and is outside this proposal.

Full explicit helper subprocess cap sums include the nested final Git export, rather than only public run_cli calls. Prepare has19 direct120s commands plus10s version (2capacity +3wrapper +3sourcefetch/ref/worktree +2initialclean +7export +2finalclean). Finalize has13 direct120s commands plus10s version (2loadclean +3wrapper +1receiptstatus +7export). Commands nested inside a public CLI are covered by its outer run_cli cap, not counted again.

| Whole real action | Public CLI cap sum (s) | Other explicit helper caps (s) | Full cap sum (s) | Proposed supervisor wait (s) | Additional direct-work reserve (s) |
|---|---:|---:|---:|---:|---:|
| Prepare | 9,600 | 2,290 | 11,890 | 18,000 | 6,110 |
| Finalize, all four exports | 56,400 | 1,570 | 57,970 | 78,000 | 20,030 |

The existing sums including these direct commands are5,090/13,370s, already beyond the prepared4500/12000s outer envelopes before uncapped work. This is permitted-cap arithmetic, not a claim that every command consumes its cap. The proposed reserves explicitly cover source-derived uncapped full Store/certification/Library work, repeated live SG/model/baseline/source checks, YAML/JSON processing, tree copies/hashes and owned cleanup. Source bounds the final candidate-ID filter to at most16 rows/campaign or64 across four under the unchanged two-class/eight-completed-iteration flow; this does not prove unique artifact content,20eligible pairs or independence. Full Store counts remain5 prepare and22+M+3k finalize (34+M when all four export); validations3 and11+k+q (19 when all four export new records). No multiplication of observed seconds byM/catalogue size was used to choose a runtime prediction.

Proposed nested controls, still unselected: prepare supervisor wait18000, enclosing TERM18120 +KILLafter60, parent envelope18300; finalize wait78000, TERM78120 +KILLafter60, parent envelope78300. Extra120s before externalTERM allows the supervisor's existing stop_group/owned cleanup and sealed receipt path; the60s hardkill remains a finite backstop, not evidence that all filesystem/kernel work is bounded. The actual supervisor Linux fixture already covers returned-leader/timeout/TERM wiring for current091 only. Metadata prepare/finalize retain existing all_free checks and run outside an occupied measurement lease; do not weaken those checks merely to place them inside a socket lease.

On parent selection, prepare a distinct helper by changing only the six exact run_cli cap literals and byte-reversing those six sites to091. A distinct supervisor changes only HELPER_SHA. Preserve current variants and all receipts. The selected helper needs a fresh actual original4d Linux cleanup receipt with its exact helper hash before prepare (helper.cleanup_proof rejects any other helper hash). The unchanged reviseda848 metadata fixture can additionally validate the new supervisor/helper binding and externalTERM wiring. Neither current091 proof nor the new metadata fixture alone may be laundered into helper.cleanup_proof. Final sourceW/F6, completed enriched catalogue and actual stage/cleanup receipts must be pinned before a prospective population freeze.

24h/20GB/eight-iteration/four-plateau/provider-call/two-lane limits, D30 constants/bootstrap/dependency population, official provider/auth boundaries, source/observer/ROI/input/backend bindings and timing-only selection stay unchanged. Future work can still exceed these finite administrative allowances. Preserve partial canonical publication/index/Git chronology and stopped receipts; revise metadata planning through parent review, never rerun application outcomes or add numerical padding because metadata timed out. No standalone export action is invented; only existing prepare/finalize nested exports are covered.
