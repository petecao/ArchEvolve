// Created: 2026-10-16 ET. Local integer/pointer pairs; no pointee dereference.
#include <utility>

int swdb_pair_pointer_values(int x, int y) {
  int left = x, right = y;
  std::pair<int, int *> empty;
  std::pair<int, int *> original(x, &left);
  std::pair<int, int *> copied(original);
  empty = copied;
  original.first = y;
  copied.second = &right;
  return empty.first + 9 - 6 * (empty.second == &left);
}

int swdb_pair_pointer_self_assign(int x, int y) {
  int left = y;
  std::pair<int, int *> value(x, &left);
  value = value;
  return value.first + (value.second == &left ? 1 : 9);
}

int swdb_pair_pointer_default() {
  std::pair<int, int *> value;
  return value.first == 0 && value.second == nullptr;
}

int swdb_pair_pointer_uninitialized() {
  int *missing;
  std::pair<int, int *> value(0, missing);
  return value.first;
}

int swdb_pair_pointer_wrong_identity(int x, int y) {
  int left = x, right = y;
  std::pair<int, int *> empty;
  std::pair<int, int *> original(x, &left);
  std::pair<int, int *> copied(original);
  empty = copied;
  original.first = y;
  copied.second = &right;
  return empty.first + 9 - 6 * (empty.second == &right);
}
