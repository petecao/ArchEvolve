# Selector actual-gate acceptance guard repair

Created: 2026-10-16 ET. Narrow test-only successor to reviewed source
`fcf6aca533e8a339d825c584833c4012a50bf0a9`.

Independent static review identified that the planned wrong-enum actual check
could accept `vacuous_pass` or a failed smoke alongside an open ordinary ensures.
Two metadata RED controls reproduced both cases. The actual predicate now
requires every smoke status to be `valid`, explicitly rejects `vacuous_pass`,
and requires all ordinary goals valid for a positive result. Its negative still
requires an ordinary open ensures and rejects unrelated failed ordinary goals.

The shared worker-B/8 GiB guard recorded RED2 in 0.495569 seconds and GREEN4
with two actual cases skipped in 0.437692 seconds (peak 68,943,872 bytes). No
compiler or actual formal tool ran. Successful metadata controls also retain a
consistent positive and a nonvacuous ordinary wrong-enum result. The exact test
SHA-256 is `d6f85ea30130e35827ad901eaec94017a481d202e70b06dee5b80c0b1c637967`.
The [compact receipt](t28-selector-actual-guard-controls-20261016.json), SHA-256
`96f194e56af481870367a3f8b3377925b855084c3234d2b908f6dff03ed3d37f`, pins the
raw command/log/JUnit/resource artifacts and verifies the six production module
blobs remain byte-identical to the reviewed parent.

The original 68-pass/2-skip compiler/stand-in receipt and its source/test pins
remain unchanged; these four controls supplement it without relabeling that
historical run. Installed source/checker identities are unchanged by this test
repair. The full frozen Git SHA for a prospective actual run must include this
successor. No actual result or whole-ticket acceptance is claimed.
