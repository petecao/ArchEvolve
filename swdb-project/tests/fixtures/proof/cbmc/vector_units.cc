// Probata PoC 25: proof units over std::vector and std::pair (their C models), inserted into a GAPBS bfs.cc
// candidate artifact. Created: 2026-10-14 ET. No BC, PR or SSSP code.
#include <cstddef>
#include <utility>
#include <vector>

// size, operator[], push_back, range-for and std::pair: the largest element (0 for none).
int swdb_fixture_vec_max(const int *a, int n) {
  std::vector<int> v;
  for (int i = 0; i < n; ++i) v.push_back(a[i]);
  std::pair<int, int> best(0, 0);  // (found, value)
  for (int x : v) {
    if (best.first == 0 || x > best.second) {
      best.first = 1;
      best.second = x;
    }
  }
  int checked = 0;
  for (std::size_t i = 0; i < v.size(); ++i)
    if (v[i] <= best.second) ++checked;
  return checked == n ? best.second : -1000;
}

// Stale pointer: data() kept across a growing push_back, then read.
int swdb_fixture_vec_stale_data(const int *a, int n) {
  std::vector<int> v;
  v.push_back(7);
  int *p = v.data();
  for (int i = 0; i < n; ++i) v.push_back(a[i]);
  return *p;
}

// Stale iterator: begin() kept across a growing push_back, then read.
int swdb_fixture_vec_stale_iterator(const int *a, int n) {
  std::vector<int> v;
  v.push_back(7);
  std::vector<int>::iterator it = v.begin();
  for (int i = 0; i < n; ++i) v.push_back(a[i]);
  return *it;
}

// at with an index that may reach size().
int swdb_fixture_vec_at(int n, int k) {
  std::vector<int> v((std::size_t)n, 5);
  return v.at((std::size_t)k);
}

// The same call behind a bounds check.
int swdb_fixture_vec_at_checked(int n, int k) {
  std::vector<int> v((std::size_t)n, 5);
  if ((std::size_t)k < v.size()) return v.at((std::size_t)k);
  return 5;
}
