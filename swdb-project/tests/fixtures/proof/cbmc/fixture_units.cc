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
// Added 2026-10-14 ET (Probata PoC 23, the C-stub translator and check mode):
// - swdb_fixture_add_one: a callee whose summary reads \old over memory (a[i] == \old(a[i]) + 1); the three
//   callers are the C-stub meaning controls: swdb_fixture_call_bad breaks its precondition (a[i] = 5000),
//   swdb_fixture_call_keep expects a location inside its assigns (a[0]) to keep its value, and
//   swdb_fixture_call_outside relies on a location outside them (a[1]); swdb_fixture_call_inc relies on the
//   summary's postcondition (the agreement negative control drops it from the C stub only).
// - swdb_fixture_total: a sum checked against a logic-library definition (logic call in a formal half).
// - swdb_fixture_copy: b[k] = a[k] with \separated arrays; SWDB_SEEDED_FRAME_BUG negates a[k] first (a frame
//   violation only an \old snapshot under the quantifier catches).
// - swdb_fixture_half: a real-valued unit (double); SWDB_SEEDED_REAL_ERROR adds 1e-3 to its result. The C lowering
//   refuses floating types until ticket 24, and a library entry's baseline proof unit must have one, so its fixture
//   contract pins the integer stand-in swdb_fixture_half_baseline as the baseline.
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

void swdb_fixture_add_one(int *a, int n, int i) {
  a[i] = a[i] + 1;
}

int swdb_fixture_call_bad(int *a, int n) {
  a[0] = 5000;
  swdb_fixture_add_one(a, n, 0);
  return 0;
}

int swdb_fixture_call_keep(int *a, int n) {
  swdb_fixture_add_one(a, n, 0);
  return a[0];
}

int swdb_fixture_call_outside(int *a, int n) {
  swdb_fixture_add_one(a, n, 0);
  return a[1];
}

int swdb_fixture_call_inc(int *a, int n) {
  swdb_fixture_add_one(a, n, 0);
  return a[0];
}

int swdb_fixture_total(int *a, int n) {
  int s = 0;
  for (int i = 0; i < n; ++i) s += a[i];
  return s;
}

void swdb_fixture_copy(int *b, int *a, int n) {
  for (int k = 0; k < n; ++k) {
#ifdef SWDB_SEEDED_FRAME_BUG
    a[k] = -a[k];
#endif
    b[k] = a[k];
  }
}

double swdb_fixture_half(double x) {
#ifdef SWDB_SEEDED_REAL_ERROR
  return x * 0.5 + 0.001;
#else
  return x * 0.5;
#endif
}

int swdb_fixture_half_baseline(int x) {
  return x / 2;
}
