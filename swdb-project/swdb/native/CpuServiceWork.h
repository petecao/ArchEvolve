// Created: 2026-10-06 ET. Shared service/count source; no application timing input.
#pragma once
#include <chrono>
#include <cstdint>

extern "C" __attribute__((noinline)) std::uint64_t service_clock(
    std::uint64_t n, bool invoke_clock) {
  std::uint64_t checksum = 0;
  for (std::uint64_t i = 0; i < n; ++i) {
    std::uint64_t value = i;
    if (invoke_clock)
      value ^= std::uint64_t(std::chrono::system_clock::now().time_since_epoch().count());
    asm volatile("" : "+r"(value) : : "memory");
    checksum ^= value;
  }
  return checksum;
}
