// Created: 2026-10-12 ET. Shared library-call service/count source; no application timing input.
// Each service op invokes exactly one selected call per iteration when `invoke` is set; the
// paired driver runs the same loop without it. SWDB_LIBCALL_EVENT comments mark the
// selected calls for readers; the count proof selects sites by name and coefficient.
// No inline asm in the counted function: the characterizer reports inline asm as
// `indirect-call`, which would pollute the indirect-call service. Volatile globals keep values.
#pragma once
#include <cstdint>
#include <cstring>
#include <locale>
#include <ostream>

// 0 strlen, 1 ostream::put, 2 ostream::flush, 3 __ostream_insert, 4 _M_insert<unsigned long>,
// 5 ctype<char>::_M_widen_init, 6 indirect call (overhead only).
// The count driver runs op k with (k + 1) * n events, so each selected site has a distinct
// coefficient (op 5's virtual dispatch sites stay apart from op 6's indirect call).
constexpr int LIBRARY_CALL_SERVICES = 7;
constexpr std::uint64_t LIBRARY_CALL_TEXT_BYTES = 16;

static inline __attribute__((always_inline)) std::uint64_t library_indirect_body(std::uint64_t v) {
  return v * 3 + 1;
}
extern "C" __attribute__((noinline)) std::uint64_t library_indirect_target(std::uint64_t v) {
  return library_indirect_body(v);
}

const char *volatile library_text_slot = "0123456789abcdef";
std::uint64_t (*volatile library_indirect_slot)(std::uint64_t) = library_indirect_target;
volatile std::uint64_t library_value_sink = 0;

#if defined(__GLIBCXX__)
// libstdc++ caches the widen table after the first _M_widen_init. The application calls it
// once (first call), so each service iteration clears the cache flag to time an uncached call.
// After _M_widen_init, widen(c) makes one virtual do_widen call (an `indirect-call` row). The
// driver makes one virtual do_widen(range) call without _M_widen_init, so the difference keeps
// the dispatch out of this service; the indirect-call service prices it.
struct library_ctype : std::ctype<char> {
  library_ctype() : std::ctype<char>(nullptr, false, 1) {}
  void uncached() const { _M_widen_ok = 0; }
  void table_cached() const { _M_widen_ok = 2; }
};
#else
// Portable fixture analog only: libc++ has no _M_widen_init. One opaque locale call.
struct library_ctype {
  void uncached() const {}
  void table_cached() const {}
};
#endif

extern "C" __attribute__((noinline)) std::uint64_t service_library_call(
    int op, std::uint64_t n, bool invoke, std::ostream *os, const library_ctype *facet) {
  std::uint64_t checksum = 0;
  for (std::uint64_t i = 0; i < n; ++i) {
    std::uint64_t value = i;
    if (op == 0) {
      const char *text = library_text_slot;
      if (invoke)
        value ^= std::strlen(text); // SWDB_LIBCALL_EVENT 0
      else
        value ^= LIBRARY_CALL_TEXT_BYTES + std::uint64_t(text[0] == 0);
    } else if (op == 1) {
      if (invoke)
        os->put('x'); // SWDB_LIBCALL_EVENT 1
    } else if (op == 2) {
      os->put('\n');
      if (invoke)
        os->flush(); // SWDB_LIBCALL_EVENT 2
    } else if (op == 3) {
      const char *text = library_text_slot;
#if defined(__GLIBCXX__)
      if (invoke)
        std::__ostream_insert(*os, text, std::streamsize(LIBRARY_CALL_TEXT_BYTES)); // SWDB_LIBCALL_EVENT 3
#else
      if (invoke)
        os->write(text, std::streamsize(LIBRARY_CALL_TEXT_BYTES)); // SWDB_LIBCALL_EVENT 3
#endif
    } else if (op == 4) {
      if (invoke)
        *os << static_cast<unsigned long>(1000000 + (i & 1023)); // SWDB_LIBCALL_EVENT 4
    } else if (op == 5) {
#if defined(__GLIBCXX__)
      if (invoke) {
        facet->uncached();
        value ^= std::uint64_t(facet->widen('a')); // SWDB_LIBCALL_EVENT 5
      } else {
        char in = 'a', out = 0;
        facet->table_cached();
        facet->widen(&in, &in + 1, &out);
        value ^= std::uint64_t(out);
      }
#else
      if (invoke)
        value ^= std::uint64_t(&std::locale::classic() != nullptr); // SWDB_LIBCALL_EVENT 5
#endif
    } else if (op == 6) {
      auto target = library_indirect_slot;
      if (invoke)
        value = target(value); // SWDB_LIBCALL_EVENT 6
      else
        value = library_indirect_body(value);
    }
    library_value_sink = value;
    checksum ^= value;
  }
  return checksum;
}
