// Created: 2026-10-12 ET. Count the shared library-call bodies; never time them.
#include "CpuLibraryCallWork.h"
#include <cstdlib>
#include <iostream>
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const auto n = std::strtoull(argv[1], nullptr, 10);
  if (!n || n > 96) return 2;
  const bool invoke = std::atoi(argv[2]) != 0;
  library_ctype facet;
  std::uint64_t result = 0;
  for (int op = 0; op < LIBRARY_CALL_SERVICES; ++op)
    result ^= service_library_call(op, std::uint64_t(op + 1) * n, invoke, &std::cout, &facet);
  std::cout.flush();
  library_value_sink = result;
}
