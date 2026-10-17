// Created: 2026-10-06 ET. Count the shared service body; never time it.
#include "CpuServiceWork.h"
#include <cstdlib>
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  const auto n = std::strtoull(argv[1], nullptr, 10);
  if (!n || n > 96) return 2;
  volatile auto result = service_clock(n, std::atoi(argv[2]) != 0);
  (void)result;
}
