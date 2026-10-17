// DX100 intrinsic lowerings, hardware interface 1.0-e4fc4af. Updated: 2026-10-03 ET.
#pragma once
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <omp.h>
#if defined(FUNC)
#include <MAA_functional.hpp>
#else
#include <MAA_gem5.hpp>
#endif
static_assert(TILE_SIZE > 0 && TILE_SIZE <= 65535, "DX100 uint16 tile-size field");
struct dxc_context { int tile[8], reg[8]; };
namespace swdb_dxc {
inline bool &session(){static bool value=false;return value;}
inline std::atomic<uint64_t>&chunks(){static std::atomic<uint64_t>v(0);return v;}
inline std::atomic<uint64_t>&races(){static std::atomic<uint64_t>v(0);return v;}
inline std::atomic<uint64_t>&violations(){static std::atomic<uint64_t>v(0);return v;}
}
inline void __dxc_session_begin(){
#ifdef SWDB_STRICT
 swdb_strict::session_begin();
#endif
 swdb_dxc::session()=true;swdb_dxc::chunks()=0;swdb_dxc::races()=0;swdb_dxc::violations()=0;
}
inline dxc_context __dxc_thread_context(){
#ifdef SWDB_STRICT
 swdb_strict::check(swdb_dxc::session(),"session_required");
 swdb_strict::check(omp_get_num_threads()<=NUM_CORES,"thread_count");
#else
 assert(swdb_dxc::session()&&omp_get_num_threads()<=NUM_CORES);
#endif
 dxc_context c;
#pragma omp critical(swdb_dxc_allocate)
 {for(int i=0;i<8;++i)c.tile[i]=get_new_tile<int>();for(int i=0;i<8;++i)c.reg[i]=get_new_reg<int>();}
 return c;
}
inline void __dxc_const_i32(int32_t value,int reg){maa_const<int>(value,reg);}
inline void __dxc_wait(int tile){wait_ready(tile);std::atomic_thread_fence(std::memory_order_seq_cst);asm volatile("" ::: "memory");}
template<class T>inline void __dxc_gather(T*base,int index,int dst){maa_indirect_load<T>(base,index,dst);}
template<class T>inline void __dxc_stream_load(T*base,int minimum,int maximum,int stride,int dst){maa_stream_load<T>(base,minimum,maximum,stride,dst);}
inline void __dxc_range_loop(int last_i,int last_j,int lower,int upper,int stride,int rows,int columns){maa_range_loop<int>(last_i,last_j,lower,upper,stride,rows,columns);}
inline uint16_t __dxc_tile_size(int tile){return get_tile_size(tile);}
template<class T>inline T*__dxc_tile_pointer(int tile){
#ifdef SWDB_STRICT
 swdb_strict::check(get_tile_ready(tile)!=0,"read_before_wait");
#endif
 return get_cacheable_tile_pointer<T>(tile);
}
inline void __dxc_alu_scalar(int src,int reg,int dst,Operation_t op){maa_alu_scalar<int>(src,reg,dst,op);}
inline void __dxc_accelerated_chunk(){++swdb_dxc::chunks();}
inline void __dxc_cas_probe(int vertex,int hint,bool success,int initial,int fresh,int vertex_count=INT32_MAX){
#ifdef SWDB_DXC_DIAGNOSTIC
 if(!success&&hint<0)++swdb_dxc::races();
 if((hint<0&&hint!=initial&&hint!=-1)||(hint>=0&&(hint>=vertex_count||fresh<0)))++swdb_dxc::violations();
#else
 (void)vertex;(void)hint;(void)success;(void)initial;(void)fresh;(void)vertex_count;
#endif
}
inline void __dxc_report(){std::printf("SWDB accelerated_chunks=%llu\n",(unsigned long long)swdb_dxc::chunks().load());
#ifdef SWDB_DXC_DIAGNOSTIC
 std::printf("SWDB cas_fail_negative_hint=%llu l3_violations=%llu\n",(unsigned long long)swdb_dxc::races().load(),(unsigned long long)swdb_dxc::violations().load());
#endif
}
