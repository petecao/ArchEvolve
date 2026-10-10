# Publication author R1 — strict read-root compatibility

2026-10-07 ET. Distinct source-only revision, NOT RUN. Original source41c152, full handoff71854d and preparation68ce remain byte-exact and retain their original review chronology.

Parent/02 source review identified one concrete interface mismatch: original author `Path.is_relative_to('/data/yanruj')` permits equality with that directory (likewise `/data1/yanruj`), whereas unchanged32bead `main()` requires each supplied read-root string to start with `/data/yanruj/` or `/data1/yanruj/`. Such equality roots could be authored successfully and then refused by the original producer.

R1 changes ONLY the two-line read-root predicate to require strict descendants using those original slash-terminated prefixes on the already canonicalized nonsymlink existing paths. Parent-directory equality is refused before output. All request field sets, original source/input/publication checks, explicit observations/review, UID, bounds, output paths/modes, true/false original seal policies, final guards and scientific/control sources remain exact. No other generic tool or capture support was added.

- Selected prospective R1 source: `/private/tmp/lanl17_author_first_publication_request_r1_20261007.py`, 28,419 B, SHA-256 `791f95b5f53c23740ce8b2bdd72fc8dcd625494a60f5399f30b5ed704347fb1a`.
- Complete two-line diff: `/private/tmp/lanl17-first-publication-request-author-r1-20261007.diff`, 974 B, SHA-256 `aae13099c341702dc90f1bc36728c35924a696d0480d83f7824c97d3997f6708`.
- Original author: `/private/tmp/lanl17_author_first_publication_request_20261007.py`, 28,449 B, SHA-256 `41c152fb30049eba60acd7946598f7eb9f6499eb0981da19332822bd2836bfa7`.
- Original full input/interface handoff: `/private/tmp/lanl17-first-publication-request-author-source-handoff-20261007.md`, SHA-256 `71854d91b30fa54987337e3ee7d997a8e6c8a9f5581f6f8f88711d222efb874c`. Its original source selection remains historical; all interface descriptions apply to R1 with the stricter read-root rule.

Exact reversal of only the new predicate yields every original41c byte. Syntax/AST parse and compilation to a code object only confirm the prospective module is syntactically complete; no module, function, main, fixture, test or real input was run. The separate R1 preparation proof records this source relationship and immutable originals, not an execution or admission result.

Future original specification/CLI/parent review must pin the actually selected R1 author SHA, not original41c. No such actual specification or request has been created now. Producer32bead request format and writer remain unchanged. Parent still must review explicit final R/M2/prepare/freeze/policy/input/observation/review/output pins and exact returned bytes before any author or separate capture action. Actual final R/publication/zero-outcome/live-file observations remain missing future inputs; no values are guessed.

No tracked mutation, original source modification, source staging, Store, Git mutation, SSH, native/provider action, policy freeze or campaign occurred. R1 is pending full parent and independent02 review.
