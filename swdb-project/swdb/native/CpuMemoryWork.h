// Created: 2026-10-06 ET. Shared normalized request work; no physical issue claim.
// Updated: 2026-10-12 ET: memory_v2 narrow stores (1/2 bytes) with a size_t ring index.
#pragma once
#include <cstddef>
#include <cstdint>
template<class T> __attribute__((always_inline)) inline std::uint64_t memory_body(
    volatile T *data, std::size_t elements, std::size_t n, int operation, bool invoke) {
  T index=0, result=0;
  for (std::size_t i=0;i<n;++i) {
    if (invoke) {
      if (operation==0) index=data[index];
      else {
        if (operation==1) data[index]=static_cast<T>(i);
        else if (operation==2) result^=__atomic_fetch_add(const_cast<T*>(&data[index]),T(1),__ATOMIC_SEQ_CST);
        else {
          T expected=operation==3 ? T(0) : ~T(0);
          const bool changed=__atomic_compare_exchange_n(const_cast<T*>(&data[index]),&expected,T(1),false,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST);
          result+=changed ? 1 : 0;
        }
        index=(index+1)&static_cast<T>(elements-1);
      }
    } else index=(index+1)&static_cast<T>(elements-1);
    asm volatile("" : "+r"(index), "+r"(result) :: "memory");
  }
  return static_cast<std::uint64_t>(index)^static_cast<std::uint64_t>(result);
}

extern "C" __attribute__((noinline)) std::uint64_t service_memory8(volatile std::uint8_t *data, std::size_t elements, std::size_t n, int operation, bool invoke) {
  (void)operation;
  return memory_body(data,elements,n,0,invoke);
}
extern "C" __attribute__((noinline)) std::uint64_t service_memory32(volatile std::uint32_t *data, std::size_t elements, std::size_t n, int operation, bool invoke) {
  return memory_body(data,elements,n,operation,invoke);
}
extern "C" __attribute__((noinline)) std::uint64_t service_memory64(volatile std::uint64_t *data, std::size_t elements, std::size_t n, int operation, bool invoke) {
  return memory_body(data,elements,n,operation,invoke);
}
// memory_v2: a narrow T cannot index an 8 MiB ring, so the store cursor is size_t.
template<class T> __attribute__((always_inline)) inline std::uint64_t store_body(
    volatile T *data, std::size_t elements, std::size_t n, bool invoke) {
  std::size_t index=0, result=0;
  for (std::size_t i=0;i<n;++i) {
    if (invoke) data[index]=static_cast<T>(i);
    index=(index+1)&(elements-1);
    asm volatile("" : "+r"(index), "+r"(result) :: "memory");
  }
  return static_cast<std::uint64_t>(index)^static_cast<std::uint64_t>(result);
}
extern "C" __attribute__((noinline)) std::uint64_t service_store8(volatile std::uint8_t *data, std::size_t elements, std::size_t n, bool invoke) {
  return store_body(data,elements,n,invoke);
}
extern "C" __attribute__((noinline)) std::uint64_t service_store16(volatile std::uint16_t *data, std::size_t elements, std::size_t n, bool invoke) {
  return store_body(data,elements,n,invoke);
}
template<class T> __attribute__((always_inline)) inline std::uint64_t service_memory(volatile T *data, std::size_t elements, std::size_t n, int operation, bool invoke) {
  return sizeof(T)==1 && operation==1 ? service_store8(reinterpret_cast<volatile std::uint8_t*>(data),elements,n,invoke)
       : sizeof(T)==2 ? service_store16(reinterpret_cast<volatile std::uint16_t*>(data),elements,n,invoke)
       : sizeof(T)==1 ? service_memory8(reinterpret_cast<volatile std::uint8_t*>(data),elements,n,operation,invoke)
       : sizeof(T)==4 ? service_memory32(reinterpret_cast<volatile std::uint32_t*>(data),elements,n,operation,invoke)
                     : service_memory64(reinterpret_cast<volatile std::uint64_t*>(data),elements,n,operation,invoke);
}
