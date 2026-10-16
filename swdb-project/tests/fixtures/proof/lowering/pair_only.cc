// Created: 2026-10-15 ET. Pair-only value, copy and assignment fixture.
#include <utility>

int swdb_pair_values(int x, int y) {
  std::pair<int, int> empty;
  std::pair<int, int> original(x, y);
  std::pair<int, int> copied(original);
  empty = copied;
  original.first = 17;
  copied.second = 19;
  return 3 * empty.first + empty.second;
}

int swdb_pair_self_assign(int x, int y) {
  std::pair<int, int> value(x, y);
  value = value;
  return value.second;
}

int swdb_pair_default() {
  std::pair<int, int> value;
  return value.first + value.second;
}

int swdb_pair_uninitialized() {
  int missing;
  std::pair<int, int> value(0, missing);
  return value.second;
}

int swdb_pair_wrong_field(int x, int y) {
  std::pair<int, int> empty;
  std::pair<int, int> original(x, y);
  std::pair<int, int> copied(original);
  empty = copied;
  original.first = 17;
  copied.second = 19;
  return 3 * empty.second + empty.first;
}
