// PROTOTYPE (ticket 08): definitions crux-llvm needs for the strict layer, which libc++ keeps in
// its dylib (not in headers). Single thread only: the mutex is a no-op.
#include <crucible.h>
#include <cstdlib>
#include <mutex>
#include <new>
void std::mutex::lock() {}
void std::mutex::unlock() noexcept {}
std::mutex::~mutex() {}
void *operator new(size_t n) { return malloc(n); }
void operator delete(void *p) noexcept { free(p); }
void operator delete(void *p, size_t) noexcept { free(p); }
[[noreturn]] void std::__libcpp_verbose_abort(const char *, ...) noexcept { crucible_assert(0, __FILE__, __LINE__); abort(); }
// The strict layer calls std::_Exit only on a failed check: make that a verification failure.
extern "C" void _Exit(int) { crucible_assert(0, __FILE__, __LINE__); abort(); }
// Aligned allocation, static-destructor registration and the failure-path printing.
#include <cstdio>
void *operator new(size_t n, std::align_val_t) { return malloc(n); }
void operator delete(void *p, size_t, std::align_val_t) noexcept { free(p); }
extern "C" int __cxa_atexit(void (*)(void *), void *, void *) { return 0; }
extern "C" int fprintf(FILE *, const char *, ...) { return 0; }
extern "C" int fflush(FILE *) { return 0; }
