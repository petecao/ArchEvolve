// Ticket 07 smoke check for crux-llvm (C++ through clang bitcode): one assertion.
// Build with -DBUGGY to get a version whose assertion must fail.
#include <crucible.h>

template <typename T> T bump(T v) { return v + 1; }

int main() {
  int x = crucible_int32_t("x");
  assuming(x >= 0 && x <= 100);
  int y = bump(x);
#ifdef BUGGY
  check(y != 42);  // refuted by x = 41
#else
  check(y > x);    // holds for all x in [0, 100]
#endif
  return 0;
}
