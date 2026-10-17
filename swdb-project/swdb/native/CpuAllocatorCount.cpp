// Created: 2026-10-06 ET. Updated: 2026-10-12 ET (allocator_v2: ops 4/5, sizes <=32MiB).
// Count only the shared allocator body, not preparations.
#include "CpuAllocatorWork.h"
#include <cstdlib>
int main(int argc, char **argv) {
  if (argc != 5) return 2;
  const auto n = std::strtoull(argv[1], nullptr, 10);
  const auto bytes = std::strtoull(argv[2], nullptr, 10);
  const auto operation = std::atoi(argv[3]);
  const bool invoke = std::atoi(argv[4]) != 0;
  if (!n || n > 5 || !bytes || bytes > 33554432 || operation < 0 || operation > 5) return 2;
  void *pointers[5] = {};
  char sentinel = 0;
  auto allocate = [&](int op) { return op == 0 ? ::operator new[](bytes) : op == 2 ? ::operator new(bytes) : std::malloc(bytes); };
  auto release = [&](int op, void *p) { if (op == 1) ::operator delete[](p); else if (op == 3) ::operator delete(p); else std::free(p); };
  if (operation % 2) for (std::size_t i=0; i<n; ++i) pointers[i] = allocate(operation - 1);
  volatile auto result = service_allocator(pointers, n, bytes, operation, invoke, &sentinel);
  (void)result;
  if (!(operation % 2) && invoke) for (std::size_t i=0; i<n; ++i) release(operation + 1, pointers[i]);
  if (operation % 2 && !invoke) for (std::size_t i=0; i<n; ++i) release(operation, pointers[i]);
}
