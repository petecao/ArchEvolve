# SMASH block-lane consumer coordinate witness

This new compiled integer fixture tests the printed Algorithm 1 expression
`C[rowInd+ctrElmt] += NZA[NZA_ind] * x[colInd+ctrElmt]` against an explicitly
linear, consecutive-element block interpretation. SMASH section 4.2.3 defines
`Index = row_index * matrix_columns + column_index`; section 4.1 identifies
represented NZA blocks, while the CPU owns block-rank/element computation.

For a two-row, four-column matrix, the first two-element block with values
`[1,2]` and vector `[10,20,30,40]` should contribute `[50,0]`. The printed index
expression instead contributes `[10,40]`. Applying it to a two-element block at
row1/col0 also targets a nonexistent output row2. The fixture uses `.at()` to
observe that bound failure without unsafe memory access; the index expressions
are otherwise retained. This is a source-pseudocode counterexample under the
declared layout, not a demonstrated fault in authenticated public SMASH code.

The minimal consumer correction is to derive each lane from the flat block base:

```text
flat = flat_start + lane
row = flat / matrix_columns
column = flat % matrix_columns
C[row] += NZA[block_rank * block_elements + lane] * x[column]
```

It preserves zero-valued lanes and supports a full block crossing a row boundary.
Before writing, check matrix extent multiplication, complete block bounds and
vector length. The executable tests use only tiny integer values whose arithmetic
cannot overflow; this fixture is not a general integer/FP numerical kernel API.
Arbitrary scalar arithmetic, actual NZA ordering/padding and original benchmark
numerics still require their own source/implementation contracts.

Executed compile/run with C++17, `-O1 -Wall -Wextra -Werror`, UBSan and
`-fno-sanitize-recover=all`. Both counterexamples were reproduced; corrected
within-row, second-row, cross-row, zero-lane, incomplete-block and extent-overflow
checks passed. No existing bitmap tests or numerical benchmark was invoked.

Root next action: add this conditional consumer obligation to SMASH's portable
implementation notes. Before an actual implementation experiment, bind the
public consumer code and exact block layout; do not infer it from the printed
pseudocode alone. The existing assist-only catalog capability remains unchanged.
