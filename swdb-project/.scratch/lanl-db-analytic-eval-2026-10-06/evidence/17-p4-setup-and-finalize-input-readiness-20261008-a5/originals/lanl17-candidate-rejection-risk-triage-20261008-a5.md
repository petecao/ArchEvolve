# Candidate-rejection risk triage — 2026-10-08 20:18 ET

Scope: source-only independent review of frozen R `5e12a9796432654d88def24ecea617d16ca605b2` and retained P1–P3 compact AFTER originals. No SSH, control/target imports or execution, tests, source changes, retrospective repair, or scientific admission.

One concrete prospective defect requires follow-up: infrastructure and administrative certification errors can be converted into ordinary candidate rejection, repair calls, and plateau advancement. The retained compact evidence does not identify the underlying exception for these campaigns, so this finding must not be used to retrospectively classify their actual cause.

| Campaign | Rejected rows | Rows with materialized ID | Final failed certification rows | Comparisons | Stop |
|---|---:|---:|---:|---:|---|
| P1 | 8 | 8 | 4 | 0 | plateau |
| P2 | 8 | 8 | 2 | 0 | plateau |
| P3 | 8 | 2 | 0 | 0 | plateau |

All 24 rows have level rejected and null selection. No candidate comparison exists. Six final certification rows (P1 four; P2 two) have record=null/outcome=failed; their failed-check semantic SHA `233992f6ddb2af642dab6e3c97021f88e6d390c9fe603f1b79f8052477a9afe1` exactly matches canonical compact JSON `["certification_aborted"]`. This is a local digest comparison against a known source taxonomy value, not a recovered exception message. Rejection explanations, feedback reasons and failed-check values were intentionally excluded by the original compact collector (candidate projection lines87–98, iteration100–105). P3 has no certification rows. Actual rejected patches/contracts/knobs and exception text were not inspected.

## Confirmed source finding [P2]

`swdb-project/swdb/campaign_targets.py:564–571` catches all `Failure` and `UsageError` from certification. Except special harness/control-site strings, it converts them into `certification_aborted`, appends no certification record, and continues as a failed candidate certificate. `campaign.py:957–968` may spend repair calls and ultimately rejects it; `campaign.py:899,1197` records NOT_IMPROVED/advances plateau. This intercepts the intended infrastructure failure handling at `campaign.py:1202–1204`.

These exception classes contain distinct cases:

- Infrastructure: unavailable/invalid compiler at `certification.py:127–138`; reconstructed snapshot identity drift at393; trusted certification client/evaluator build/link failures at `certification_process.py:89,102,107` and `certification_isolation.py:98`.
- Candidate-invalid: unsupported authored source changes at `certification.py:958–960`, and evaluator-symbol/harness-scan violations at `certification_isolation.py:314` / `certification_process.py:302`.
- Invalid frozen configuration: invalid typed library at `certification.py:1035–1037`; wrong full matrix at1042–1043; unavailable/misconfigured contract/kernel at1065–1081. These are not evidence that the candidate is wrong.

Consequently the broad catch can label a campaign normal plateau even when its trusted infrastructure failed. Confirmed static behavior, regardless of whether it occurred in P1–P3. No actual missing compiler or actual trusted-build failure is inferred from the six aborted rows.

Suggested narrow prospective fix: introduce an explicit typed candidate-certification refusal for expected candidate scope/header/harness/control-site errors; preserve those public reason codes and candidate rejection behavior. Catch only that category for repair/rejection. Propagate operational/source-integrity failures to the existing infrastructure stop; explicitly translate frozen configuration errors to infrastructure failure rather than allowing a bare UsageError to escape the outer Failure handler. Avoid broad exception-text allowlists or converting every UsageError into an infrastructure failure, since legitimate candidate scope failures currently use it too. Preserve failed persisted certification verdicts as failed candidate outcomes.

Meaningful regression coverage (not run): adapter propagation of missing compiler/trusted evaluator failure; full campaign stops infrastructure_failure with no false completed NOT_IMPROVED iteration or plateau/repair charge; candidate scope/harness rejection still returns the intended failed check; existing failed-verdict-with-no-checks test remains failed. `tests/test_extensa_targets.py:369–381` currently tests failed verdict records, not raised error taxonomy. Repository search found no test asserting certification_aborted mapping.

## Research interpretation and evidence limits

Expected candidate rejections are explicitly supported by `campaign.py:908–926` and the Gem5 contract/session admission guards at `campaign_targets.py:971–980`. A negative search result can be valid research evidence. The compact observations alone cannot establish that all 24 rejections were faithful candidate-invalid outcomes: most rejection causes are absent, and the aborted category is mixed.

No comparisons imply these rows never reached the successful certification→evaluation path (`campaign.py:933–983`). The timing-pair receipts are created only for impending timing requests, so empty pairing is compatible with every proposal being rejected; it does not constitute a verified blind timing history. Public `extensa_agreement.py:257–258` faithfully flags empty pairing/outcome-access history unverified and returns unsupported D30/no switch (312–323). The public report can describe a negative/no-pairs observation while full strict scientific admission remains unavailable. Do not manufacture forecasts/order, retime rejected candidates, or rewrite the frozen R results.

## Pins

- P1 AFTER: `/private/tmp/lanl17-p1-after-capture-20261008-a5/custody.json`, 35637 B, SHA256 `aed96b7d00fed15d9f69a7eb609cc194cafd62964c95c95a401840708963a47a`, canonical True seal `9474bc202e09d8a0e9a7593589a87e295a5906c7ec33b873a68c296a2490621f`.
- P2 AFTER: `/private/tmp/lanl17-p2-after-capture-20261008-a5/custody.json`, 32770 B, SHA256 `975b7ba8242eafd4d52f219626d04eb149e13f2c90620f9fbb6e3bc5d5d73710`, canonical True seal `446dffff826ad6da1bc652d50e15d93ae910e0b59f8e9ce84f0317ae5b61f936`.
- P3 AFTER: `/private/tmp/lanl17-p3-after-capture-20261008-a5/custody.json`, 28810 B, SHA256 `7ad57fbdfd2324fe5feee1ebb1e51321659c128a6127797540273326cb39958d`, canonical True seal `e1bd904486cbe4db154a3d9d217e39cec5eca65c10ccf4a12ec56337e2816785`.
- Frozen `campaign.py`: 79456 B, SHA256 `13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d`.
- Frozen `campaign_targets.py`: 71343 B, SHA256 `727d4399e4bde1996484e3013770e5ab21ef4a30e8fa7313c4697aaa6359211f`.
- Frozen `certification.py`: 77561 B, SHA256 `b7de18069b2bfc0d0e008c0c0e898a613cfcf9297e388d724f271eb9fa5299e7`.
- Frozen `certification_process.py`: 17206 B, SHA256 `d2a24ea28403c92dd00d1ef22848fd67e610a6db7e92905a331acaaaacf7f8ce`.
- Frozen `certification_isolation.py`: 17943 B, SHA256 `9097e28085fdab03e70078c10907eb6061fd1a91ad9f82e005a37f18f6a052eb`.
- Frozen `extensa_agreement.py`: 26057 B, SHA256 `d078cf8a26fbbd65f0d27d0a64dbde56e4f190e1ec4c07b9e4eb311ad3a5174f`.
- Frozen `extensa_pairing.py`: 17550 B, SHA256 `30a62539769c21f5d0ecbc3fb2800bd60c935332f13a6c6c1eba638558a1896a`.
