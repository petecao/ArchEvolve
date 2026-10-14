// Probata PoC 21 fixture proof units in the core C++ subset (functions, arrays, loops).
// Created: 2026-10-14 ET. Tests insert this text into a candidate artifact's src/bfs.cc and pin it
// as the fixture contract's baseline proof unit (proof_unit.source).
// - swdb_fixture_fill: the safe fixture; its seeded bug stops one element early (i < n - 1).
// - count_up: map 07's Frama-C/WP smoke program with its ACSL moved out: the requires, assigns
//   and ensures go in the smoke fixture contract, the loop annotations and the assertion are
//   fixture hints at anchors (the seeded bug's assertion says i == n + 1).
void swdb_fixture_fill(int *a, int n, int v) {
  for (int i = 0; i < n; ++i) {
    a[i] = v;
  }
}

int count_up(int n) {
  int i = 0;
  while (i < n) i++;
  return i;
}
