# Public SMASH consumer row boundary

Executed the exact pinned public consumer inner loop with checked metadata containers and symbolic tokens. No float payload or FP operation is executed: operator* returns an empty symbolic token, and subscripting records/checks indices before any storage access. This isolates the integer cursor/control path, not the whole float kernel.

The original `j > columns` permits `j == columns` to reach the next vector access. A new source-aligned case uses a complete2x2 matrix with ratio4 and flat block start0: original accesses0,1,2 and is caught by the metadata check. The one-character `>=` repair produces0,1,0,1 and rows0,0,1,1. New generic cursor cases also cover exact boundary/end state and unchanged interior behavior; the startcol1/width2 case is generic, not claimed to be an aligned source block.

materialize.py verifies exact public spmv_bitmap.c SHAcd7e6514 and changes only that comparison. Successor b9596a14 is private in /tmp/smash-consumer-row-successor-r1. prepare_fixture.py regenerates original/fixed loop includes and owned metadata drivers in a new directory. New host Werror ASan/UBSan compile/run passed. No indexer, numerical helper, old suite, native benchmark, model or capture was applied.

Input prerequisites remain positive dimensions, valid starting row/column, a complete source-bound block/element extent and adequate source/output storage. The terminal cursor may be one row beyond the matrix only after the final permitted element, without a subsequent access. This patch does not populate NZA, repair the separate assignment-versus-accumulation behavior, validate the indexer/ISA or certify numerical results. Whole source integration must prove those separately.

Next action: Root review one source delta with exact pins and new metadata evidence; compose with existing private source repairs if a future software validation is admitted. No shared source or remote branch was edited.
