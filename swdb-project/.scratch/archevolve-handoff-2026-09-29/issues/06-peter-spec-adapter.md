# 06 — Adapter from Peter's intrinsic spec

Created: 2026-09-29
**Type:** slice
**Status:** needs-info
**Blocked by:** Peter's spec format
**Spec:** `../spec.md`

Turn Peter's intrinsic spec plus Josh's hardware candidate into an SWDB rewrite proposal,
and render failed proposals into Josh's `rewrite-feedback` YAML. Do not start before Peter
says what his agent will ask for and in what format.

## Progress

2026-09-29: The existing public SWDB rewrite-proposal and repair interfaces are
available, but Peter's request and intrinsic-spec format has not been received in
ticket 01. Ticket 05 also still needs the exact report/source offset-width binding.
The offline declared-read hardware requests and `docs/peter-intrinsics-handoff.md`
at the ArchEvolve root are discussion sketches with provisional components; they
do not provide confirmed callable symbols, signatures, or executable hardware behavior.

Before the adapter can be implemented, the handoff must identify Peter's input
format, source/build and statement references, the selected Josh/Eric hardware
candidate, operand/address widths, lengths and bounds, result layout, buffer ownership,
completion/wait behavior, and visibility/order requirements. The rewrite must preserve
the pinned parent CAS and queue effects, then pass the declared correctness check.
The root `examples/rewrite-feedback.template.yaml` supplies an unfilled draft feedback
shape, but its intrinsic-spec reference and outcome/evidence fields are placeholders.
The team must bind that feedback shape to the actual accepted request format.

These are known prerequisites from the current source and handoff drafts, not an
invented reply from Peter. The ticket stays `needs-info`; no adapter or failed-proposal
feedback instance has been fabricated.
