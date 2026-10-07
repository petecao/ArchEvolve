// Created: 2026-10-06 ET. Split allocator/driver elapsed; preparations untimed.
#include "CpuAllocatorWork.h"
#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
volatile std::uint64_t allocator_sink = 0;
int main(int argc, char **argv) {
  if (argc != 6) return 2;
  const auto bytes = std::strtoull(argv[1], nullptr, 10);
  const auto n = std::strtoull(argv[2], nullptr, 10);
  const auto batches = std::strtoull(argv[3], nullptr, 10);
  const auto operation = std::atoi(argv[4]);
  const bool first = std::string(argv[5]) == "service_first";
  if (!bytes || bytes > 1048576 || !n || n > 65536 ||
      n * bytes > 67108864 || !batches || n * batches > 16777216 ||
      operation < 0 || operation > 3 ||
      (!first && std::string(argv[5]) != "driver_first")) return 2;
  std::vector<void *> pointers(n, nullptr);
  char sentinel = 0;
  double gross = 0., driver = 0.;
  auto one = [&](bool invoke) {
    double elapsed = 0.;
    for (std::size_t j = 0; j < batches; ++j) {
      if (operation % 2) allocator_sink ^= service_allocator(
          pointers.data(), n, bytes, operation - 1, true, &sentinel);
      auto start = std::chrono::steady_clock::now();
      const auto value = service_allocator(pointers.data(), n, bytes,
                                           operation, invoke, &sentinel);
      auto stop = std::chrono::steady_clock::now();
      elapsed += std::chrono::duration<double>(stop - start).count();
      allocator_sink ^= value;
      if (!(operation % 2) && invoke) allocator_sink ^= service_allocator(
          pointers.data(), n, bytes, operation + 1, true, &sentinel);
      if (operation % 2 && !invoke) {
        allocator_sink ^= service_allocator(pointers.data(), n, bytes,
                                            operation, true, &sentinel);
      }
    }
    if (invoke) gross = elapsed; else driver = elapsed;
    return elapsed;
  };
  if (one(first) < 0 || one(!first) < 0) return 3;
  std::cout << std::setprecision(17) << "{\"events\":" << n * batches
      << ",\"batch_events\":" << n << ",\"batches\":" << batches
      << ",\"gross_seconds\":" << gross << ",\"driver_seconds\":" << driver
      << ",\"order\":\"" << argv[5] << "\",\"checksum\":" << allocator_sink << "}\n";
}
