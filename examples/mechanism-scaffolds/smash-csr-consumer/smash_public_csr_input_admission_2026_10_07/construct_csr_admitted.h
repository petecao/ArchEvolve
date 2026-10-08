#ifndef SMASH_CONSTRUCT_CSR_ADMITTED_H
#define SMASH_CONSTRUCT_CSR_ADMITTED_H

#include "csr_input_admission.h"
#include "geometry_admission.h"

/* Include after the source-bound smash/csr types and original constructor.
 * The legacy ABI remains unchanged. Callers opt into this explicit
 * entry point.
 */
static inline enum smash_csr_admission_status
construct_bitmap0_nza_admitted(smash *format, csr *matrix,
                              size_t row_words, size_t column_words,
                              size_t value_words, size_t declared_nnz)
{
    if (!format || !matrix)
        return SMASH_CSR_MISSING_STORAGE;
    struct smash_csr_input_view view =
    {
        matrix->size, matrix->row_ptr, row_words,
        matrix->col_ptr, column_words, matrix->val, value_words, declared_nnz
    };
    enum smash_csr_admission_status status = smash_admit_csr_structure(view);
    if (status != SMASH_CSR_STRUCTURE_OK)
        return status;
    if (!smash_constructor_geometry_supported(matrix->size,
                                             format->compression_ratio0))
        return SMASH_CSR_UNSUPPORTED_GEOMETRY;
    construct_bitmap0_nza(format, matrix);
    return SMASH_CSR_STRUCTURE_OK;
}
#endif
