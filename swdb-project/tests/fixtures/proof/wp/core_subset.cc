// Probata PoC 21: every core-subset construct the C lowering accepts (functions, arrays, loops),
// for the determinism, anchor, compile and C-versus-C++ differential tests. Created: 2026-10-14 ET.
#include <cstddef>
#include <cstdint>

int32_t swdb_core_table[4] = {3, -1, 4, 1};
static int swdb_core_calls;

static int swdb_core_clamp(int x, int lo, int hi) {
  ++swdb_core_calls;
  if (x < lo) {
    return lo;
  } else if (x > hi)
    return hi;
  return x;
}

unsigned swdb_core_mix(unsigned u, long w) {
  return (u << 3) ^ static_cast<unsigned>(w) ^ (unsigned)(w >> 2) ^ 0x9e37U;
}

int swdb_core_kernel(const int *a, int n, int32_t *out, size_t m) {
  int s = 0;
  int local[3] = {1, 2, 3};
  for (int i = 0; i < n; ++i) {
    if (a[i] % 2 == 0)
      s += a[i] * local[i % 3];
    else if (a[i] < 0)
      continue;
    else
      s -= swdb_core_clamp(a[i], -5, 5);
    if (s > 1000) break;
  }
  int j = 0;
  while (j < n && (size_t)j < m) {
    out[j] = a[j] + swdb_core_table[j & 3];
    j++;
  }
  do {
    --j;
  } while (j > 0);
  bool positive = s > 0 && n != 0;
  char c = 'A';
  long long wide = (long long)s * 3LL;
  int *p = &s;
  *p += (int)(wide % 7) + c;
  s = positive ? s + (int)swdb_core_mix(1u, -7L) % 11 : -s;
  for (;;) {
    if (s >= 0) break;
    s += 100;
  }
  return s + swdb_core_calls - swdb_core_calls;
}
