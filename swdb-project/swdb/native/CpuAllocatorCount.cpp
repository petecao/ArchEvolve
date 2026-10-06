// Created: 2026-10-06 ET. Count only the shared allocator body, not preparations.
#include "CpuAllocatorWork.h"
#include <cstdlib>
int main(int argc, char **argv) {
  if (argc != 5) return 2;
  const auto n = std::strtoull(argv[1], nullptr, 10);
  const auto bytes = std::strtoull(argv[2], nullptr, 10);
  const auto operation = std::atoi(argv[3]);
  const bool invoke = std::atoi(argv[4]) != 0;
  if (!n || n > 5 || !bytes || bytes > 1048576 || operation < 0 || operation > 3) return 2;
  void *pointers[5] = {};
  char sentinel = 0;
  if (operation % 2) for (std::size_t i=0; i<n; ++i) pointers[i] = operation == 1 ? ::operator new[](bytes) : ::operator new(bytes);
  volatile auto result = service_allocator(pointers, n, bytes, operation, invoke, &sentinel);
  (void)result;
  if (!(operation % 2) && invoke) for (std::size_t i=0; i<n; ++i) { if (operation == 0) ::operator delete[](pointers[i]); else ::operator delete(pointers[i]); }
  if (operation % 2 && !invoke) for (std::size_t i=0; i<n; ++i) { if (operation == 1) ::operator delete[](pointers[i]); else ::operator delete(pointers[i]); }
}
