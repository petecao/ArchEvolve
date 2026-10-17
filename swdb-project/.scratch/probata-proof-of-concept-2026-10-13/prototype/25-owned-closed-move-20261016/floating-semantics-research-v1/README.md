2026-10-16 ET.

The earlier claim that a C NaN comparison disproves the original plain ACSL
equality annotation was overstated. ACSL 1.24 distinguishes logical comparison
after real promotion from the explicit IEEE comparison predicates. Promotions of
nonfinite values are unspecified, so the C expression alone does not settle the
annotation. [ACSL 1.24, section 2.2.5, implemented in Frama-C 33.0](https://www.frama-c.com/download/frama-c-acsl-implementation.pdf).

The pinned local parser source corroborates the distinction: arithmetic
comparison selects `Lreal` and inserts casts before WP receives the predicate.
WP's selected `Real` model uses real-valued storage/arithmetic and classifies its
values as finite. Its separate `Float` path uses the Why3 IEEE classifications
and comparisons. Exact physical pins and source locations are in the JSON
observation; no compiler, parser or solver was executed for this research.

Keep the original clauses and historical evidence intact. The remaining work is
an explicit source/store and IEEE class/value correspondence, including NaN and
infinity controls. A bit-exact payload guarantee needs additional representation
and selected implementation evidence. No finite-only caller requires or hidden
assumption follows, and the existing `+real` result is not relabeled as IEEE
evidence.
