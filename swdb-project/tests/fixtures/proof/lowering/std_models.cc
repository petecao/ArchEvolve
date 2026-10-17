// Probata PoC 24 fixture, construct group "std::min, std::max, std::swap, std::copy" (C models).
// Created: 2026-10-14 ET. Harness: std_models_harness.inc.
#include <algorithm>

int swdb_std_unit(int *a, int *b, int n, int x, int y) {
  int lo = std::min(x, y);
  int hi = std::max(x, y);
  std::swap(lo, hi);
  std::copy(a, a + n, b);
  long big = std::max<long>(lo, 7);
  return lo - hi + (int)big + (n > 0 ? b[0] : 0);
}

// Updated: 2026-10-15 ET. A modular integer result initializes its receiving scalar slot.
int swdb_std_min_result(int x, int y) {
  int value = std::min(x, y);
  return value;
}
