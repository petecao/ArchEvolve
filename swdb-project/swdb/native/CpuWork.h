// Source work shared by the uninstrumented timer and LLVM counting driver.
// Created 2026-10-06 ET. Constructed-work rates are not physical issue throughput.
#pragma once
#include <cstdint>
extern "C" __attribute__((noinline)) uint64_t compute_integer(uint64_t n, uint64_t seed) {
    uint64_t a = seed + 1, b = seed + 3, c = seed + 5, d = seed + 7;
    for (uint64_t i = 0; i < n; ++i) {
        a ^= a << 13; a ^= a >> 7; a ^= a << 17;
        b ^= b << 13; b ^= b >> 7; b ^= b << 17;
        c ^= c << 13; c ^= c >> 7; c ^= c << 17;
        d ^= d << 13; d ^= d >> 7; d ^= d << 17;
    }
    return a ^ b ^ c ^ d;
}
extern "C" __attribute__((noinline)) double compute_floating_point(uint64_t n, uint64_t seed) {
    double a = 1.0 + seed * .001, b = 2.0, c = 3.0, d = 4.0;
    for (uint64_t i = 0; i < n; ++i) {
        a = a * 1.00000001 + .00001; b = b * 1.00000002 + .00002;
        c = c * 1.00000003 + .00003; d = d * 1.00000004 + .00004;
    }
    return a + b + c + d;
}
extern "C" __attribute__((noinline)) uint64_t compute_branch(uint64_t n, uint64_t seed) {
    uint64_t a = seed + 1, b = 17;
    for (uint64_t i = 0; i < n; ++i) {
        a ^= a << 13; a ^= a >> 7; a ^= a << 17;
        if (a & 1) b += a; else b ^= a;
    }
    return a ^ b;
}
extern "C" __attribute__((noinline)) uint64_t compute_atomic(uint64_t n, uint64_t seed) {
    alignas(64) uint64_t a = seed;
    for (uint64_t i = 0; i < n; ++i) __atomic_fetch_add(&a, 1, __ATOMIC_RELAXED);
    return a;
}
