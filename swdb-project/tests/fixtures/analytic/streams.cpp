// Streams the address classifier must not mistake for indirect accesses.
// Created: 2026-10-09 ET (code review F1/F2). Hand-counted fixture, not application evidence.
#include <cstring>
struct Vec { int *data; int n; };
struct Bounds { int lo, hi; };
// OpenMP reloads the captured x/y pointers every iteration and starts each chunk at a loaded bound.
extern "C" __attribute__((noinline)) void omp_stream(int *y, const int *x, int n) {
  #pragma omp parallel for
  for (int i = 0; i < n; ++i) y[i] = x[i] + 1;
}
// A C++ member pointer and bound reloaded every iteration (as pvector::operator[] does).
extern "C" __attribute__((noinline)) long member_stream(const Vec *v) {
  long sum = 0;
  for (int i = 0; i < v->n; ++i) sum += v->data[i];
  return sum;
}
// Bounds read once from scalar fields are not an index array (not ranged_indirect).
extern "C" __attribute__((noinline)) long field_bounds(const Bounds *b, const int *a) {
  long sum = 0;
  for (int i = b->lo; i < b->hi; ++i) sum += a[i];
  return sum;
}
// The same accumulator element every iteration: a stride-0 stream.
extern "C" __attribute__((noinline)) void accumulate(long *out, const int *a, int n) {
  for (int i = 0; i < n; ++i) *out += a[i];
}
int main(int argc, char **argv) {
  int a[8] = {1, 2, 3, 4, 5, 6, 7, 8}, y[8] = {0};
  Vec v{a, 8}; Bounds b{1, 7}; long out = 0;
  if (argc < 2) return 2;
  if (std::strcmp(argv[1], "omp") == 0) { omp_stream(y, a, 8); return y[7] == 9 ? 0 : 3; }
  if (std::strcmp(argv[1], "member") == 0) return member_stream(&v) == 36 ? 0 : 3;
  if (std::strcmp(argv[1], "bounds") == 0) return field_bounds(&b, a) == 27 ? 0 : 3;
  accumulate(&out, a, 8);
  return out == 36 ? 0 : 3;
}
