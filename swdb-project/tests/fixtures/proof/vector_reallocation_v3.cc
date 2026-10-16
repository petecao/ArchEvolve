// 2026-10-16 ET. Full source for the qualified v3 caller vertical.
// Formal caller contracts and model eligibility are separately pinned; no
// ownership or liveness condition is inserted into this executable source.
#include <vector>
#include <cstddef>

int vector_realloc_v3_safe(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *saved = v.data();
  v.reserve((std::size_t)n + 1);
  return n > 0 ? v[0] : 0;
}

int vector_realloc_v3_stale(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *saved = v.data();
  v.reserve((std::size_t)n + 1);
  return n > 0 ? *saved : 0;
}

int vector_realloc_v3_no_growth(int n) {
  std::vector<int> v((std::size_t)n, 7);
  int *saved = v.data();
  v.reserve((std::size_t)n);
  return n > 0 ? *saved : 0;
}
