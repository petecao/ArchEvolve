// Probata PoC 24 fixture, construct group "floating point" (float and double types, literals and
// conversions; ticket 26's real-valued units need them). Created: 2026-10-14 ET. Harness: floats_harness.inc.
struct Rank {
  double value;
  float weight;
};

double swdb_float_unit(const double *a, int n, float scale) {
  Rank r;
  r.value = 0.0;
  r.weight = scale * 0.5f;
  for (int i = 0; i < n; ++i) r.value += a[i] * r.weight + 1e-3;
  int whole = (int)r.value;
  bool positive = r.value;
  return r.value / 3.0 + whole + (r.value > 0.25 ? 1.0f : 0.0) + positive;
}
