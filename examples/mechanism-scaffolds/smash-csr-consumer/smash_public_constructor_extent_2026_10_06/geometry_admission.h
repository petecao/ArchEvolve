#ifndef SMASH_CONSTRUCTOR_GEOMETRY_ADMISSION_H
#define SMASH_CONSTRUCTOR_GEOMETRY_ADMISSION_H
#include <limits.h>
#include <stdint.h>

/* New admission policy: original constructor defines only complete blocks. */
static inline int smash_constructor_geometry_supported(int size, int ratio)
{
    if (size <= 0 || ratio <= 0)
        return 0;
    const uint64_t extent = (uint64_t)size * (uint64_t)size;
    if (extent > INT_MAX || extent % (unsigned)ratio)
        return 0;
    const uint64_t blocks = extent / (unsigned)ratio;
    return blocks && blocks <= (unsigned)(INT_MAX - 63);
}
#endif
