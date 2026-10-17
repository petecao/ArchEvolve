// Created: 2026-10-06 ET. Hand-counted fixture, not application evidence.
#include <cstdlib>
extern "C" __attribute__((noinline)) void stream(const float *x, float *y, int n) {
  for (int i = 0; i < n; ++i)
    y[i] = x[i] * 2.0f + 1.0f;
}
int main(int argc, char **argv) {
  int n = argc > 1 ? std::atoi(argv[1]) : 8;
  if (n < 0 || n > 100) return 2;
  float x[100], y[100];
  for (int i = 0; i < n; ++i) x[i] = float(i);
  stream(x, y, n);
  for (int i = 0; i < n; ++i)
    if (y[i] != float(i) * 2.0f + 1.0f) return 1;
  return 0;
}
