// Probata PoC 22 fixture proof units for the CBMC adapter, in the core C++ subset (functions, arrays, loops).
// Created: 2026-10-14 ET. Tests insert this text into a candidate artifact's src/bfs.cc and pin it as the
// fixture contracts' baseline proof unit (proof_unit.source).
// - swdb_fixture_fill: the safe fixture; its seeded bug stops one element early (i < n - 1).
// - swdb_fixture_fill_knob: a compared knob (swdb_fixture_threshold, legal 1..8, only compared); with
//   SWDB_SEEDED_KNOB_BUG it breaks the postcondition at exactly one legal knob value (3).
// - swdb_fixture_clamp / swdb_fixture_clamp_all: a callee with a library summary and the unit that calls it.
// - smoke_main: map 07's CBMC smoke program (smoke.c) with its assertion returned as a flag; -DBUGGY is
//   the seeded bug (refuted by x = 41).
// - swdb_fixture_twice: a loop that runs 2n times, so the unwinding bound from the sizes is too small.
int swdb_fixture_threshold = 4;

void swdb_fixture_fill(int *a, int n, int v) {
  for (int i = 0; i < n; ++i) {
    a[i] = v;
  }
}

void swdb_fixture_fill_knob(int *a, int n, int v) {
  if (n >= swdb_fixture_threshold) {
    for (int i = 0; i < n; ++i) a[i] = v;
  } else {
    for (int i = n - 1; i >= 0; --i) a[i] = v;
  }
#ifdef SWDB_SEEDED_KNOB_BUG
  if (swdb_fixture_threshold == 3 && n > 0) a[0] = v ^ 1;
#endif
}

int swdb_fixture_clamp(int x, int lo, int hi) {
  return x < lo ? lo : (x > hi ? hi : x);
}

void swdb_fixture_clamp_all(int *a, int n) {
  for (int i = 0; i < n; ++i) {
    a[i] = swdb_fixture_clamp(a[i], 0, 9);
  }
}

int smoke_main(int x) {
  if (x < 0 || x > 100) return 1;
  int y = x + 1;
#ifdef BUGGY
  return y != 42;
#else
  return y > x;
#endif
}

int swdb_fixture_twice(int n) {
  int s = 0;
  for (int i = 0; i < 2 * n; ++i) s += 1;
  return s;
}
