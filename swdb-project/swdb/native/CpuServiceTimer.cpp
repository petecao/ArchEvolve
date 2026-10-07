// Created: 2026-10-06 ET. Uninstrumented paired native service/driver timer.
#include "CpuServiceWork.h"
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

volatile std::uint64_t service_sink = 0;
int main(int argc, char **argv) {
  if (argc != 3) return 2;
  std::uint64_t n = std::strtoull(argv[1], nullptr, 10);
  const bool service_first = std::string(argv[2]) == "service_first";
  if (!n || n > 134217728 || (!service_first && std::string(argv[2]) != "driver_first")) return 2;
  double gross = 0, driver = 0;
  auto one = [&](bool service) {
    auto start = std::chrono::steady_clock::now();
    auto value = service_clock(n, service);
    auto stop = std::chrono::steady_clock::now();
    service_sink ^= value;
    double elapsed = std::chrono::duration<double>(stop - start).count();
    if (service) gross = elapsed; else driver = elapsed;
  };
  one(service_first);
  one(!service_first);
  std::cout << std::setprecision(17)
    << "{\"events\":" << n << ",\"gross_seconds\":" << gross
    << ",\"driver_seconds\":" << driver << ",\"order\":\"" << argv[2]
    << "\",\"checksum\":" << service_sink << "}\n";
}
