#include <assert.h>
#include <stddef.h>

struct csr { int *row_ptr; int *col_ptr; float *val; int size; };
typedef struct csr csr;
struct smash { int compression_ratio0; };
typedef struct smash smash;
static unsigned constructor_calls;
static void construct_bitmap0_nza(smash *format, csr *matrix)
{
    (void)format;
    (void)matrix;
    ++constructor_calls;
}
#include "construct_csr_admitted.h"

int main(void)
{
    int rows[] = {0, 1, 1, 1, 1};
    int col[] = {0};
    float value[] = {1};
    csr matrix = {rows, col, value, 4};
    smash format = {4};
    assert(construct_bitmap0_nza_admitted(NULL, &matrix, 5, 1, 1, 1) ==
           SMASH_CSR_MISSING_STORAGE);
    assert(construct_bitmap0_nza_admitted(&format, NULL, 5, 1, 1, 1) ==
           SMASH_CSR_MISSING_STORAGE);
    matrix.row_ptr = NULL;
    assert(construct_bitmap0_nza_admitted(&format, &matrix, 5, 1, 1, 1) ==
           SMASH_CSR_MISSING_STORAGE);
    matrix.row_ptr = rows; matrix.col_ptr = NULL;
    assert(construct_bitmap0_nza_admitted(&format, &matrix, 5, 1, 1, 1) ==
           SMASH_CSR_MISSING_STORAGE);
    matrix.col_ptr = col; matrix.val = NULL;
    assert(construct_bitmap0_nza_admitted(&format, &matrix, 5, 1, 1, 1) ==
           SMASH_CSR_MISSING_STORAGE);
    matrix.val = value; matrix.size = 0;
    assert(construct_bitmap0_nza_admitted(&format, &matrix, 5, 1, 1, 1) ==
           SMASH_CSR_INVALID_SIZE);
    assert(constructor_calls == 0);
    return 0;
}
