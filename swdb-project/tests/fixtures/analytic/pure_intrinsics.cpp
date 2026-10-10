// Side-effect-free arithmetic intrinsics are counted operations, not opaque calls.
// Created: 2026-10-09 ET (code review 14-F3). Hand-counted fixture, not application evidence.
#include <algorithm>
#include <cmath>
#include <cstdlib>
extern "C" __attribute__((noinline)) double pure_math(double x, double y, int a, int b, unsigned bits) {
  double magnitude = std::fabs(x);         // llvm.fabs: 1 floating-point operation
  double larger = std::fmax(magnitude, y); // llvm.maxnum: 1 floating-point operation
  int top = std::max(a, b);                // inlined std::max: 1 integer comparison
  int distance = std::abs(a - b);          // sub + llvm.abs: 2 integer operations
  int ones = __builtin_popcount(bits);     // llvm.ctpop: 1 integer operation
  return larger + (top + distance + ones); // 2 integer adds, 1 floating-point add
}
int main(int argc, char **) {
  // -2.5, 1.0, 3, 7, 0b1011: fmax(2.5, 1.0) = 2.5; 7 + 4 + 3 = 14; 16.5.
  return pure_math(-2.5, 1.0, 3, 7 + argc - 1, 11u) == 16.5 ? 0 : 1;
}
