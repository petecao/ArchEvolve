# Certification fingerprint redeclaration

Updated: 2026-10-08 21:00 ET.

The prospective classification fix changes certification source bytes. The documented rule in swdb/certification_procedures.py allows a behavior-preserving refactor to redeclare its manifest digest with a dated ticket explanation; behavior changes require a new version. Root and independent Standards and Spec reviewers inspected the unchanged standalone boundary before this redeclaration.

Candidate refusal subclasses retain Failure/UsageError bases, their check predicates, public messages and CLI exit1/exit2. Positive authored instrumentation alone receives typing; trusted generated controls stay operational. Procedure definitions, evaluator entry points, C++/library sources, build/control decisions, correctness matrices and verdict rules are unchanged. Campaign infrastructure Stop/interrupted-row handling changes separately in campaign_targets.py, which is outside these procedure manifests. New certificate command.sources_match_version must match the actual new source; no historical record or source receipt is rewritten or relabeled.

The pure frozen-digest regression before correction returned10failed/1passed/40deselected in0.22s. The focused classification run returned18passed/28deselected in17.88s. The first broader run is retained:61passed/1failed, then parent-interrupted exit2 in587.35s. All10 positive and20 control evaluator runs failed before candidate execution with return95/shm_open failed, while23 build/link commands returned0; environment diagnosis and a fresh appropriate integration rerun remain required. That local failure is not hidden by refreshing manifest declarations. No numerical/scientific admission follows from these local checks.

| Family | Version | Original declared SHA256 | New source SHA256 |
|---|---|---|---|
| candidate | 1.3 | 705e697df88b273ef1223e37d95631661b1ba0ca4e98524b4e1dd6729d0122d3 | 6c75a1b113fbd19957700085e159786d136ebd8f51618a7f1eb07d2d6b7b5eea |
| candidate | 1.4 | b8df5f5cc24e2bb54ee33eb9d609dfdea4009741b00c94de0582b4d71f429515 | 90c7a0bfae71f401e081917821853982610fc4c0202a2f042b5683f9a3247b23 |
| candidate | 1.5 | a25e817ea05e512c5cc6686623ee5d69c80ae527f606c91e75566c00062f988e | 0310109a282af23c03293f7bcb71860b9a542dfa504a9e5d6d18ae5be923bd5e |
| candidate | 1.6 | 309d9cd5140bbb5bf87408ed5f1a4fba40271275704294003be8444829f61311 | 3593fa57119c0b58190f9a119ef5294ae9eea6fc995a675a9a2530982b9f3e76 |
| native | 1.3 | 6c3f478005dc25462f495211e7c5a626803b21f720524b0048e4673e5b0025dd | 5fafe53625d2e7b6c4cf1cccba1cb453c2a7f512f7f7050c163b970d95b81cbc |
| native | 1.4 | a5d54c7eb50169bd6a686e265750f7a10804bec311a399b9af1a1c47b133f78b | b8a4932a2e332db6993c153ef5fee2aa259962a61a453507d526f74e40802a26 |
| native | 1.5 | fe72f415409327e00a78fe41fece2b2d7c8705c708ffc90928286dee2740d0c2 | fc5a7e51fbb1cc6b02e496e2cbfc831884dc8f01e3987757665d7c983bb01b7f |
| library_operation | 1.1 | f0a84509f5a3b3a44de86f479a2627ad6f61f9f786e29cb980789f1c6766c60e | 4cf8263345419fc5442d5aae5fb7f2a358c08b4d4052f90f7a3b2462fc9710b7 |
| library_operation | 1.2 | f3ca83e70284d9aae97296de7ee6013ceea28e3578fdeecd46869d4521254ef7 | a8cb6f19a83cf8ba530f6209b898af7b8985256665633c9e78c8f4ad9821cb91 |
| lowering_calibration | 1.1 | 4ab5d22c2d46d672ae19a87f4426919ebb509fe45497bfd1b51515aa4eb76974 | 1d14a816bea8c3b2a644264bc85ebd6be9dfacbcd01a09376b5e0c4f1623c9e5 |

Only the10 affected source manifests are redeclared; library_operation1.0 is unchanged. Frozen remote R/F6/campaigns and all original policies/catalogs/custody remain unchanged. Full final Standards+Spec review, relevant regression/integration verification and report/index/audit closeout remain pending.
