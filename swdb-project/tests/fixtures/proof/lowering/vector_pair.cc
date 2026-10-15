// Probata PoC 25: std::vector<T> and std::pair through their C models (no BC, PR or SSSP code).
// Created: 2026-10-14 ET. Every modeled vector member appears at least once; the harness
// (vector_pair_harness.inc) runs the C++ and its C lowering on one bounded domain.
#include <cstddef>
#include <utility>
#include <vector>

int swdb_vector_unit(const int *a, int n, int x) {
  std::vector<int> v;                          // default construction
  for (int i = 0; i < n; ++i) v.push_back(a[i]);
  std::pair<int, int> best(0, 0);              // (found, value)
  for (int e : v) {                            // range-for
    if (best.first == 0 || e > best.second) {
      best.first = 1;
      best.second = e;
    }
  }
  std::pair<int, int> copy = best;             // pair copy
  copy = best;                                 // pair assignment
  int checked = 0;
  for (std::size_t i = 0; i < v.size(); ++i)   // size, operator[]
    if (v[i] <= copy.second) ++checked;
  std::vector<int> w((std::size_t)(n > 0 ? n : 0), x);   // count and value
  std::vector<int> z((std::size_t)2);                    // count (value-initialized)
  std::vector<int> c = v;                                // copy
  std::vector<int> m = std::move(c);                     // move
  int total = 0;
  for (std::vector<int>::iterator it = m.begin(); it != m.end(); ++it) total += *it;   // begin, end
  for (const int &e : z) total += e;                     // range-for by reference
  m.reserve(8);
  m.resize(3);
  w.swap(m);
  int *d = w.data();
  d[0] += 1;
  int head = w.empty() ? -1 : w.at(0);
  z.clear();
  if (!v.empty()) {
    int &r = v[0];
    r += 2;
    total += v[0];
  }
  return checked * 1000 + best.second * 100 + total * 10 + head + (int)z.size() + (int)m.size() + z.empty();
}
