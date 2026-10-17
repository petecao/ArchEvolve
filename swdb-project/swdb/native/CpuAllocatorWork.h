// Created: 2026-10-06 ET. Updated: 2026-10-12 ET (allocator_v2: malloc/free).
// Shared exact allocator ABI source; no payload touch.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <new>

// 0=new[], 1=delete[], 2=new, 3=delete, 4=malloc, 5=free. Even allocates; the odd
// operation after it releases the same allocation. Calls escape across a noinline boundary.
extern "C" __attribute__((noinline)) std::uint64_t service_allocator(
    void **pointers, std::size_t n, std::size_t bytes, int operation,
    bool invoke, void *driver_pointer) {
  std::uint64_t checksum = 0;
  for (std::size_t i = 0; i < n; ++i) {
    void *p = operation % 2 ? pointers[i] : driver_pointer;
    if (invoke) {
      if (operation == 0) p = ::operator new[](bytes);
      else if (operation == 2) p = ::operator new(bytes);
      else if (operation == 4) p = std::malloc(bytes);
      else if (operation == 1) ::operator delete[](p);
      else if (operation == 3) ::operator delete(p);
      else std::free(p);
    }
    asm volatile("" : "+r"(p) : : "memory");
    checksum ^= reinterpret_cast<std::uintptr_t>(p);
    if (!(operation % 2) || invoke) pointers[i] = operation % 2 ? nullptr : p;
  }
  return checksum;
}
