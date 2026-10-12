// PROTOTYPE (ticket 08): SV-COMP intrinsics on top of crux-llvm's crucible.h.
#include <crucible.h>
int __VERIFIER_nondet_int_impl(void) { return crucible_int32_t("nondet"); }
void __VERIFIER_assume(int c) { crucible_assume(c != 0, __FILE__, __LINE__); }
