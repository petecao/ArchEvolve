// Ticket 07 smoke check (C++ front end): one assertion over a nondeterministic input.
// Build with -DBUGGY to get a version whose assertion must fail.
#include <cassert>
#include <vector>
extern "C" int __VERIFIER_nondet_int();

template <typename T> T bump(T v) { return v + 1; }

int main() {
  int x = __VERIFIER_nondet_int();
  if (x < 0 || x > 100) return 0;
  std::vector<int> frontier{x};
  int y = bump(frontier[0]);
#ifdef BUGGY
  assert(y != 42);  // refuted by x = 41
#else
  assert(y > x);    // holds for all x in [0, 100]
#endif
  return 0;
}
