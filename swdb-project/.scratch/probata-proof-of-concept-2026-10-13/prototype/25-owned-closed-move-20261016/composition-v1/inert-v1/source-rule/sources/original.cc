// Created: 2026-10-16 ET. Closed move ownership; scalar captured before cleanup.
#include <utility>
#include <vector>

int vector_owned_move_capture(int n) {
  std::vector<int> source(n, 7);
  int *saved = source.data();
  std::vector<int> destination(std::move(source));
  int value = n > 0 ? saved[0] : 0;
  return value;
}
