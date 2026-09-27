# T16 instrumentation preparation diagnosis

Updated: 2026-09-27 ET.

The T16 seal-recovery attempt failed at `execution_identity`, before simulation,
with `actual simulator instrumentation differs from frozen treatment`. The
retained frozen protocol was `bfs-author-reference-20260925.b4cbd3924b40e7df`.
This is a preparation defect: the repaired runtime was paired with the original
freeze requests. The gate in `swdb/bfs_protocol.py` correctly rejects that pair.
No identity check needs weakening and the old protocol and failed run remain
immutable.

The actual retained driver and parser hashes equal the exact Git blobs in runtime
`923cf33b955104fdf96705b648933e7d486a3810`. The driver changed from
`371657977d56816a37f4885f19923f37175331d2d15b5d7f6e6049d3fa8c1395` to
`476874619644d1256dcc5ca1e853c47b7be2e1dc56f538aaa2dd783842e7ad10`;
the parser changed from
`2d589162b6595fee0abf4f1db54aa5b1a0964dab3f51aa408ac06505b6014091` to
`c9d3e14b70a3689799314556fab2922b1723c00960902109af2922a958cd3498`.
The observer hash and every other instrumentation field are unchanged. This
rejects runtime misidentification and unintended non-runtime treatment changes
as explanations for this specific failure.

`tests/test_bfs_instrumentation_rebinding.py` exercises the public freeze API and
actual simulator-binding validator with explicit simulator-shaped fixtures. It
checks the original binding, separate driver/parser changes, both changes,
then a fresh immutable freeze for both roles while retaining the original.
These are contract checks, not simulator execution or scientific acceptance.

A legitimate prospective continuation must create two new freeze requests and
protocols, one for author artifact comparison and one for matched control. Only
the two verifier-runtime hashes in each baseline/candidate instrumentation may
change. Preserve target/configuration, binary/compiler/model identities, graph
and ordered sources, ROI, sampling, pair controls, confidence policy and all
other settings. Freeze them before any new execution; do not relabel prior
samples or reuse either protocol's samples as the other's.

A new plan must pin both new request-file hashes/settings hashes, retain every
previous plan and failure, charge the closed attempt (1,839 seconds and
11,907,072 bytes), and carry cumulative T16 preparation of 15,013 seconds and
8,243,990,528 bytes. The original hard end remains
2026-09-27 20:16:17.225985 ET. Any additional preparation is charged inside that
same pool; it is not a renewed attempt allowance. Admission must verify both
roles' frozen instrumentation against the exact selected runtime before spending
another execution stage. No new plan, freeze, remote execution or budget was
created by this diagnosis.
