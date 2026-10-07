// Independent exact-length bulk constructions. Created2026-10-06 ET.
#pragma once
#include <cstddef>
#include <cstring>
#include <cstdint>

#if defined(SWDB_BULK_COUNT_INLINE)
#define SWDB_BULK_VISIBILITY __attribute__((always_inline)) inline
#else
#define SWDB_BULK_VISIBILITY __attribute__((noinline))
#endif
#define SWDB_BULK_RETAIN(dst,src,salt) asm volatile("" : "+r"(salt) : "r"(dst), "r"(src) : "memory")
extern "C" SWDB_BULK_VISIBILITY void bulk_copy8(unsigned char *dst,const unsigned char *src,std::size_t bytes,std::uint64_t n,bool invoke) {
  dst=static_cast<unsigned char *>(__builtin_assume_aligned(dst,8));
  src=static_cast<const unsigned char *>(__builtin_assume_aligned(src,8));
  std::uint64_t salt=0;
  for(std::uint64_t i=0;i<n;++i){if(invoke)std::memcpy(dst,src,8);salt=(salt+1)&255;SWDB_BULK_RETAIN(dst,src,salt);}
  (void)bytes;
}
#define SWDB_MOVE_BODY(name) \
extern "C" SWDB_BULK_VISIBILITY void name(unsigned char *dst,const unsigned char *src,std::size_t bytes,std::uint64_t n,bool invoke) { \
  dst=static_cast<unsigned char *>(__builtin_assume_aligned(dst,4)); \
  src=static_cast<const unsigned char *>(__builtin_assume_aligned(src,4)); \
  std::uint64_t salt=0; \
  for(std::uint64_t i=0;i<n;++i){if(invoke)std::memmove(dst,src,bytes);salt=(salt+1)&255;SWDB_BULK_RETAIN(dst,src,salt);} \
}
SWDB_MOVE_BODY(bulk_move_disjoint)
SWDB_MOVE_BODY(bulk_move_forward)
SWDB_MOVE_BODY(bulk_move_backward)
#undef SWDB_MOVE_BODY
#undef SWDB_BULK_RETAIN

#undef SWDB_BULK_VISIBILITY
