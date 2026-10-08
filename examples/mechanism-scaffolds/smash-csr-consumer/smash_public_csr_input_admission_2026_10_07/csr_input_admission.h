#ifndef SMASH_CSR_INPUT_ADMISSION_H
#define SMASH_CSR_INPUT_ADMISSION_H

#include <limits.h>
#include <stddef.h>

enum smash_csr_admission_status
{
    SMASH_CSR_STRUCTURE_OK = 0,
    SMASH_CSR_INVALID_SIZE,
    SMASH_CSR_MISSING_STORAGE,
    SMASH_CSR_TRUNCATED_STORAGE,
    SMASH_CSR_INVALID_ROW_ORIGIN,
    SMASH_CSR_INVALID_ROW_ORDER,
    SMASH_CSR_NNZ_MISMATCH,
    SMASH_CSR_INVALID_COLUMN,
    SMASH_CSR_UNSUPPORTED_COLUMN_ORDER,
    SMASH_CSR_UNSUPPORTED_GEOMETRY
};

/* Counts are caller-proven defined prefixes, not inferred allocation lengths.
 * Values are never read here. Capacity is checked; initialization
 * is not proved.
 */
struct smash_csr_input_view
{
    int size;
    const int *rows;
    size_t row_words;
    const int *columns;
    size_t column_words;
    const float *values;
    size_t value_words;
    size_t declared_nnz;
};

static inline enum smash_csr_admission_status
smash_admit_csr_structure(struct smash_csr_input_view view)
{
    if (view.size <= 0 || view.declared_nnz > INT_MAX)
        return SMASH_CSR_INVALID_SIZE;
    if (!view.rows ||
        (view.declared_nnz && (!view.columns || !view.values)))
        return SMASH_CSR_MISSING_STORAGE;
    if (view.row_words < (size_t)view.size + 1 ||
        view.column_words < view.declared_nnz ||
        view.value_words < view.declared_nnz)
        return SMASH_CSR_TRUNCATED_STORAGE;
    if (view.rows[0] != 0)
        return SMASH_CSR_INVALID_ROW_ORIGIN;
    for (int row = 0; row < view.size; ++row) {
        int begin = view.rows[row];
        int end = view.rows[row + 1];
        if (begin < 0 || end < begin || (size_t)end > view.declared_nnz)
            return SMASH_CSR_INVALID_ROW_ORDER;
    }
    if ((size_t)view.rows[view.size] != view.declared_nnz)
        return SMASH_CSR_NNZ_MISMATCH;
    for (int row = 0; row < view.size; ++row) {
        int previous = -1;
        for (int ordinal = view.rows[row]; ordinal < view.rows[row + 1];
             ++ordinal) {
            int column = view.columns[ordinal];
            if (column < 0 || column >= view.size)
                return SMASH_CSR_INVALID_COLUMN;
            /* Unsupported canonicalization, rather than a claim that generic
             * CSR forbids duplicates or unsorted columns.
             */
            if (column <= previous)
                return SMASH_CSR_UNSUPPORTED_COLUMN_ORDER;
            previous = column;
        }
    }
    return SMASH_CSR_STRUCTURE_OK;
}
#endif
