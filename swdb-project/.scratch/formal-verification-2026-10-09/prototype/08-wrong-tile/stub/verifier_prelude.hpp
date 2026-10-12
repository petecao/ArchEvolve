// PROTOTYPE (ticket 08): included before MAA_functional.hpp (via -include).
// ESBMC's C++ library model has no std::_Exit. The strict layer calls it only on a failed check,
// so make that a verification failure instead of a process exit.
#pragma once
#include <cstdlib>
#include <cassert>
namespace std { inline void _Exit(int) { assert(0 && "strict-layer check failed"); abort(); } }
