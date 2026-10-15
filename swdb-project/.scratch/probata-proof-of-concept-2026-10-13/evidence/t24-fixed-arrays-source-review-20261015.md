# Independent ticket24 source-window review

Updated: 2026-10-15 ET. Reviewer: root coordinator, separate from implementer.
Frozen reviewed source: 8a3bf8f5291fb9d758116482cd202a69bb10a78c.

## Findings

1. Acceptance-runner defect: original seeded groups accepted any not_proven,
   including unsupported-construct refusals before actual WP. Require actual launch,
   passed setup, mandatory RTE/initializedness/cache/machdep/smoke policy, nonempty
   ordinary and smoke inventory, attributable ordinary open goal and byte-matching
   record/report evidence. Explicit lifetime/escape refusal controls stay separate.
   Sent to implementer; fix pending at this review checkpoint.
2. No confirmed false-proof defect found in the runtime source-window changes.
   The fixed-array certificate supplies structural subobject identity only and
   restricts receivers to exact automatic trivial objects with closed original-TU
   direct calls. It refuses aliases/copies/escape/lifetime effects and arbitrary
   receiver input. Range, initializedness, validity and RTE remain proof obligations.
   The member_windows certificate requires independent source replay at prelaunch;
   its production setup counterpart is integrated separately in b69aaf92.

## Independent compiler controls

Three additional header-free controls passed through c_lowering.lower and
wp_pointer_bounds.prepare: false branch, nested branches, and an unconditional
neighbor read beside a conditional read. Their guards retain the correct path
implication; the unconditional read remains unconditional. No requires added.
Raw control sources and result.json:
/var/folders/x0/g9dhnccj0jjbxh_gblp35zvr0000gn/T/probata-t24-independent-condition-0tihtf1k

These are compiler/source review controls, not actual WP proofs or ticket acceptance.
Original construct groups and seeded faults still require exact-source actual runs.
