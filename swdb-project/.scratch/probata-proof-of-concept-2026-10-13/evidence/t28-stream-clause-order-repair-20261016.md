# Stream clause-order repair

2026-10-16 ET. Preparation only; real parser admission pending.

The coordinator's e4 stream run stopped before WP. Frama33 refused the three
helper contracts because `terminates` followed simple clauses; wrong-size did
not execute. Its original source and raw directory remain immutable. This
successor moves that same clause between requires and simple clauses, including
the public unit's explicit partial-normal-return policy. No predicate, original
program, model body, entry initialization, assumption or backend flag changes.

The installed Frama33 grammar is the primary syntax basis: `contract -> requires
terminates decreases simple_clauses ...`. The retained JSON pins that read-only
source. Three helper order controls plus the public prepared input first failed
(4 failures). A combined original `requires/assigns/ensures` formal half then
exposed another failure: sorting whole strings cannot place `terminates` inside
one combined text. The stream-only repair now preserves original ACSL tokens
and inserts the marker before the first simple-clause keyword. It does not split
quantifier semicolons or alter predicates.

Final compiler/scripted controls: **15 passed, 3 actual skips**, 82.89 s;
whole guard83.2508 s, peak2,467,971,072 B, no OOM/timeout. An additional four-control
profile checks grammar order and all five exact bundle sources with C11 syntax:
4 passed,0.32 s; guard0.7019 s,84,312,064 B. The first bundle matcher assumed a
line break before the function brace and failed after all five syntax checks;
that test-only whitespace error was corrected and is retained separately.

The tiny portable parser bundle contains exact correct/wrong/combined public
WP inputs, normal all27-contract validation source, and the ordinary model:
5 files,19,949 B. All three helper contracts and actual unit call order are
present. The ordinary model's assertion declaration is explicitly parse-only.
Only standard C headers are needed; no ARM build or inline assembly is included.
Root owns the source-reviewed120 s/8 GiB parser-only admission with normal
`swdb.framac.FLAGS`; the recipe is inert and contains no WP/solver request.

Repair source7f5a2d3d was merged with published integration into the author's
own branch723378ff. The later packet adds exported C, provenance, tests and
instructions. All old0.1/library bytes remain unchanged. The JSON retains exact
source/input/raw/command/resource pins and confirms the model state, entry,
C bodies, termination policy and all nontermination contract tokens are
unchanged. This does not establish source refinement, contract/body agreement,
hardware progress, a healthy actual negative or whole28/current0.2 acceptance.
