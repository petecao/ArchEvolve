// Created: 2026-10-12 ET. Uninstrumented paired library-call service/driver timer.
// stdout is reopened onto a regular sink file, like the timed application run's redirected
// stdout; std::cout keeps sync_with_stdio(true). The sink is flushed and truncated between
// batches, outside the timed windows, so it stays small. The trial JSON goes to the original
// stdout descriptor.
#include "CpuLibraryCallWork.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <string>
#include <unistd.h>

volatile std::uint64_t library_sink = 0;
int main(int argc, char **argv) {
  if (argc != 6) return 2;
  const int op = std::atoi(argv[1]);
  const auto n = std::strtoull(argv[2], nullptr, 10);
  const auto batches = std::strtoull(argv[3], nullptr, 10);
  const bool first = std::string(argv[4]) == "service_first";
  if (op < 0 || op >= LIBRARY_CALL_SERVICES || !n || n > 4096 || !batches || n * batches > 134217728 ||
      (!first && std::string(argv[4]) != "driver_first")) return 2;
  const int result_fd = dup(1);
  FILE *result = result_fd < 0 ? nullptr : fdopen(result_fd, "w");
  if (!result || !std::freopen(argv[5], "w", stdout)) return 3;
  library_ctype facet;
  auto rewind_sink = [] {
    std::cout.flush();
    std::fflush(stdout);
    if (ftruncate(fileno(stdout), 0) != 0) std::exit(4);
    std::rewind(stdout);
  };
  library_sink ^= service_library_call(op, n, true, &std::cout, &facet);  // untimed warm-up
  rewind_sink();
  double gross = 0., driver = 0.;
  auto one = [&](bool invoke) {
    double elapsed = 0.;
    for (std::uint64_t j = 0; j < batches; ++j) {
      auto start = std::chrono::steady_clock::now();
      const auto value = service_library_call(op, n, invoke, &std::cout, &facet);
      auto stop = std::chrono::steady_clock::now();
      elapsed += std::chrono::duration<double>(stop - start).count();
      library_sink ^= value;
      rewind_sink();
    }
    if (invoke) gross = elapsed; else driver = elapsed;
  };
  one(first);
  one(!first);
  std::fprintf(result,
      "{\"events\":%llu,\"batch_events\":%llu,\"batches\":%llu,\"gross_seconds\":%.17g,"
      "\"driver_seconds\":%.17g,\"order\":\"%s\",\"checksum\":%llu}\n",
      (unsigned long long)(n * batches), (unsigned long long)n, (unsigned long long)batches,
      gross, driver, argv[4], (unsigned long long)library_sink);
  std::fclose(result);
}
