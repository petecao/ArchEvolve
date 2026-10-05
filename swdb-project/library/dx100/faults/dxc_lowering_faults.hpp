// DX100 certification fault injection. Created: 2026-10-04 ET (ticket 62).
// Updated: 2026-10-04 ET (ticket 67: forged_frontier version 2).
//
// `swdb certify` appends this block to a PRIVATE build copy of the canonical lowering
// header for one rewrite negative control, and selects exactly one fault with
// -DSWDB_DXC_FAULT_<ID>. It is never part of a candidate, a patch or a deliverable.
//
// Each fault acts at a library seam the candidate must call (the DX100 intrinsics, the
// CPU claim primitive compare_and_swap and the queue push, both required by contract
// clause L4). A candidate's spelling therefore never decides whether a control exists.
// Object-like macros at the end rename the seams for the rest of the translation unit,
// so `__dxc_gather<int>(...)` and `::compare_and_swap(...)` are both intercepted.
// A control is rejected only by the evaluator's named runtime checks; a fault that
// never fires leaves the control alive, and certification then fails.
#ifndef SWDB_STRICT
#error "DX100 certification faults require the strict functional layer"
#endif
#if (defined(SWDB_DXC_FAULT_SHARED_CONTEXT) + defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK) + \
     defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION) + defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE) + \
     defined(SWDB_DXC_FAULT_DROPPED_WAIT) + defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT) + \
     defined(SWDB_DXC_FAULT_INDEX_WRAP) + defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)) != 1
#error "select exactly one DX100 certification fault"
#endif
#include <climits>
#include "platform_atomics.h"
#include "sliding_queue.h"
namespace swdb_fault {
inline std::atomic<bool>&context_made(){static std::atomic<bool>v(false);return v;}
inline dxc_context&first_context(){static dxc_context c;return c;}
// Set once per process by forged_frontier v2; session_begin never resets it.
inline std::atomic<bool>&forged_once(){static std::atomic<bool>v(false);return v;}
inline std::atomic<unsigned>&skipped_rechecks(){static std::atomic<unsigned>v(0);return v;}
inline unsigned&range_calls(int thread){static unsigned v[256];return v[thread&255];}
inline bool&gathered(int tile){static bool v[NUM_TILES];return v[tile>=0&&tile<NUM_TILES?tile:0];}
inline void session_begin(){
 __dxc_session_begin();
 context_made()=false;skipped_rechecks()=0;
 for(int t=0;t<256;++t)range_calls(t)=0;
 for(int t=0;t<NUM_TILES;++t)gathered(t)=false;
}
// shared_context: every thread receives the first context allocated in the session,
// so all threads issue on tiles and registers one thread owns.
inline dxc_context thread_context(){
#if defined(SWDB_DXC_FAULT_SHARED_CONTEXT)
 dxc_context c;
#pragma omp critical(swdb_fault_context)
 {if(!context_made()){first_context()=__dxc_thread_context();context_made()=true;}c=first_context();}
 return c;
#else
 return __dxc_thread_context();
#endif
}
// dropped_wait: no wait completes. read_before_wait: waits on gather results are
// skipped, so the consumer reads gathered values before they are ready.
inline void wait(int tile){
#if defined(SWDB_DXC_FAULT_DROPPED_WAIT)
 (void)tile;return;
#else
#if defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT)
 if(gathered(tile))return;
#endif
 __dxc_wait(tile);
#endif
}
template<class T>inline void gather(T*base,int index,int dst){__dxc_gather(base,index,dst);gathered(dst)=true;}
// index_wrap: the stream's start register wraps to INT32_MAX before the load.
// chunk_off_by_one: a stream that fills the tile exactly requests one more element.
template<class T>inline void stream_load(T*base,int minimum,int maximum,int stride,int dst){
 {std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
#if defined(SWDB_DXC_FAULT_INDEX_WRAP)
  swdb_strict::reg(minimum).value=uint32_t(INT32_MAX);
#elif defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE)
  const int64_t lo=swdb_strict::rval(minimum),hi=swdb_strict::rval(maximum),step=swdb_strict::rval(stride);
  if(step>0&&hi>=lo&&(hi-lo+step-1)/step==int64_t(TILE_SIZE))swdb_strict::reg(maximum).value=uint32_t(hi+step);
#endif
  range_calls(swdb_strict::thread())=0;
 }
 __dxc_stream_load(base,minimum,maximum,stride,dst);gathered(dst)=false;
}
// dropped_continuation: after the first range loop of a stream, the loop state is
// forced to its end, so every continuation tile comes back empty.
inline void range_loop(int last_i,int last_j,int lower,int upper,int stride,int rows,int columns){
#if defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION)
 {std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
  if(range_calls(swdb_strict::thread())++>0)swdb_strict::reg(last_i).value=uint32_t(swdb_strict::tile(lower).size);}
#endif
 __dxc_range_loop(last_i,last_j,lower,upper,stride,rows,columns);gathered(rows)=false;gathered(columns)=false;
}
inline void alu_scalar(int src,int reg,int dst,Operation_t op){__dxc_alu_scalar(src,reg,dst,op);gathered(dst)=false;}
}
// skipped_cas_recheck: a claim whose compare fails succeeds anyway (at most eight per
// session, inside the certification graph's spare vertices), as if the CPU skipped the
// recheck of a stale DX100 hint.
template<class T>inline bool swdb_fault_compare_and_swap(T&x,const T&old_val,const T&new_val){
#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)
 if(compare_and_swap(x,old_val,new_val))return true;
 if(swdb_fault::skipped_rechecks().fetch_add(1)<8){__atomic_store_n(&x,new_val,__ATOMIC_SEQ_CST);return true;}
 return false;
#else
 return compare_and_swap(x,old_val,new_val);
#endif
}
// forged_frontier, version 2 (ticket 67): the first CPU queue push of the run is pushed
// twice, whatever the tile size, frontier threshold or chunk timing, so every candidate
// that pushes through the contract's queue seam (clause L4) fires it. The evaluator also
// forges the protected frontier print to the oracle's counts, so only its trusted queue
// inspection (`duplicate_frontier`) can reject this control.
// Version 1 (macro SWDB_DXC_FAULT_FORGED_FRONTIER, certificates written before ticket 67)
// pushed twice only after an accelerated chunk had finished. When a level's only chunk
// finished after all of that level's pushes, it never fired, and a correct candidate was
// rejected (campaign a7: tile 16384, frontier threshold 64).
template<typename T>class swdb_fault_QueueBuffer:public QueueBuffer<T>{
public:
 explicit swdb_fault_QueueBuffer(SlidingQueue<T>&master,size_t given_size=16384):QueueBuffer<T>(master,given_size){}
 void push_back(T to_add){
  QueueBuffer<T>::push_back(to_add);
#if defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)
  if(!swdb_fault::forged_once().exchange(true))QueueBuffer<T>::push_back(to_add);
#endif
 }
};
#define __dxc_session_begin swdb_fault::session_begin
#define __dxc_thread_context swdb_fault::thread_context
#define __dxc_wait swdb_fault::wait
#define __dxc_gather swdb_fault::gather
#define __dxc_stream_load swdb_fault::stream_load
#define __dxc_range_loop swdb_fault::range_loop
#define __dxc_alu_scalar swdb_fault::alu_scalar
#define compare_and_swap swdb_fault_compare_and_swap
#define QueueBuffer swdb_fault_QueueBuffer
