# Independent METHOD23 resource-policy review — 2026-10-15 ET

**PASS for the narrow resource-policy change.** This is not full METHOD23 protocol approval, a source freeze, or admission for an actual experiment. No outstanding material finding remains within these three reviewed files.

Reviewed working tree: `/private/tmp/probata-resume-t07-method23`, base `94c77ec1e76d8a7611aaa4cbfdb4a48cf3f86a7a`. The modified guard, new public controls and prospective METHOD23 document are snapshotted and individually pinned in the companion manifest. No repository file was changed by this reviewer.

The original candidate passed 35 independent controls, but an additional real-CLI regression exposed a retry-admission defect: an injected OS sleep overshoot allowed a new environment read at 261.209 ms, beyond the proposed 200 ms window, and accepted recovery. The retained initial RED and snapshots remain immutable. The repair checks retry admission at loop entry and again after identity validation, immediately before the requested observation. The previously observed denial retains its operation, identity and timestamp; a separate expiry event records a later decision without inventing a new denial or live observation.

The repaired exact bytes passed **37 controls in 14.04 s**: 27 existing runner controls, eight new repository controls, the independent escaped-descendant cleanup control and the independent scheduler-overshoot control. The permanent expiry case also checks the exact original denial and separate expiry timestamps, failure result and cleanup/lease result. All controls use small private Python processes and injected psutil/OS boundaries; no actual solver, verifier workload or provider was launched.

Static review confirmed the longer policy applies only to requested environment inspection (200 ms and 21 attempts); other operations retain three attempts. Snapshot and fresh PID/birth checks remain before and after each admitted observation. Confirmed gone/reused identities are distinct from persistent live/unknown denial. A denied marker is never treated as absent; uncertain cleanup still quarantines the private lease. Exact-marker discovery may independently renew a nonroot identity, while root replacement remains refused. No foreign environment values are logged.

Inspection pauses remain counted. Sampled RSS and elapsed-time checks still follow inspection and can refuse a job after recovery. This extends possible sampling/stop latency; already admitted OS calls or scheduling may finish later, and source-level admission is not atomic with kernel start time. This is neither a hard latency/memory bound nor hostile-process containment. The change does not identify the run25 denied process, explain its cause, or establish that it would have recovered.

The real-format task reader and baseline-subset compatibility remain separate outstanding work. A future actual experiment still needs full source/protocol review, clean published pins, preflight and coordinator admission, with the original positive-plus-negative acceptance gate intact.

Exact independent command (cwd: `/private/tmp/probata-resume-t07-method23/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints`; process-inspection escalation used):

```sh
PYTHONDONTWRITEBYTECODE=1 PROBATA_REVIEW_HERE=/private/tmp/probata-resume-t07-method23/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints /Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3 -m pytest -q -p no:cacheprovider test_counted_verifier.py test_inspection_retry.py /private/tmp/test_probata_method20_cleanup_cli.py /private/tmp/test_probata_method23_deadline_independent.py --junitxml=/private/tmp/probata-t07-method23-final-independent-tests.xml > /private/tmp/probata-t07-method23-final-independent-tests.txt 2>&1
```

`git diff --check` passed. No repository source, shared experiment process or shared experiment lease was modified by this review; controlled tests managed only their private fixtures. No actual experiment was performed. Created 2026-10-15T21:09:39.906148-04:00.
