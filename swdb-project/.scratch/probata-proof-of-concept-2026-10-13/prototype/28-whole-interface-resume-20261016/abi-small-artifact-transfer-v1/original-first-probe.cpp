// 2026-10-16 ET. INERT compiler observation probe; no native execution.
#include "MAA_gem5.hpp"
#include <climits>
#include <cfloat>
#include <cstdint>
using dws_probe_uint32_t = std::uint32_t;
using dws_probe_int32_t = std::int32_t;
using dws_probe_float = float;
using dws_probe_uint64_t = std::uint64_t;
using dws_probe_int64_t = std::int64_t;
using dws_probe_double = double;
enum {
    dws_probe_char_bit = CHAR_BIT,
    dws_probe_int_bits = sizeof(int) * CHAR_BIT,
    dws_probe_pointer_bits = sizeof(void *) * CHAR_BIT,
    dws_probe_little_endian = __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__,
    dws_probe_size_uint32_t = sizeof(dws_probe_uint32_t),
    dws_probe_size_int32_t = sizeof(dws_probe_int32_t),
    dws_probe_size_float = sizeof(dws_probe_float),
    dws_probe_size_uint64_t = sizeof(dws_probe_uint64_t),
    dws_probe_size_int64_t = sizeof(dws_probe_int64_t),
    dws_probe_size_double = sizeof(dws_probe_double),
    dws_probe_align_uint32_t = alignof(dws_probe_uint32_t),
    dws_probe_align_int32_t = alignof(dws_probe_int32_t),
    dws_probe_align_float = alignof(dws_probe_float),
    dws_probe_align_uint64_t = alignof(dws_probe_uint64_t),
    dws_probe_align_int64_t = alignof(dws_probe_int64_t),
    dws_probe_align_double = alignof(dws_probe_double),
    dws_probe_float_radix = FLT_RADIX,
    dws_probe_float_mantissa = FLT_MANT_DIG,
    dws_probe_double_mantissa = DBL_MANT_DIG,
    dws_probe_source_cores = NUM_CORES,
    dws_probe_source_tiles = NUM_TILES,
    dws_probe_source_registers = NUM_SCALAR_REGS,
    dws_probe_source_tile_words = TILE_SIZE
};
