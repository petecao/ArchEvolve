// DX100 certification seams and faults (certify 1.3). Created: 2026-10-04 ET (ticket 70).
// Replaces library/dx100/faults/dxc_lowering_faults.hpp (tickets 62 and 67), whose fault block
// was appended to the candidate's own translation unit and selected by a macro the candidate
// could test. The fault logic is unchanged; only where it is compiled moved.
//
// `swdb certify` compiles this file into a separate trusted object, once with no fault (positive
// matrix, token and legality controls) and once per library-fault control with exactly one
// -DSWDB_DXC_FAULT_<ID>. That macro reaches only this translation unit. The candidate object,
// built once from the candidate prelude, calls the extern seams below and is linked unchanged
// against each of these objects.
//
// Each fault acts at a library seam the candidate must call (the DX100 intrinsics, the CPU claim
// primitive compare_and_swap and the queue push, both required by contract clause L4). A
// candidate that bypasses a seam leaves its control alive, and certification then fails.
#include <atomic>
#include <climits>
#include <cstdint>
#include <mutex>
#include "dxc_lowering.hpp"
#ifndef SWDB_STRICT
#error "DX100 certification seams require the strict functional layer"
#endif
#if (defined(SWDB_DXC_FAULT_SHARED_CONTEXT) + defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK) + \
     defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION) + defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE) + \
     defined(SWDB_DXC_FAULT_DROPPED_WAIT) + defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT) + \
     defined(SWDB_DXC_FAULT_INDEX_WRAP) + defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)) > 1
#error "select at most one DX100 certification fault"
#endif
namespace swdb_fault {
inline std::atomic<bool>&context_made(){static std::atomic<bool>v(false);return v;}
inline dxc_context&first_context(){static dxc_context c;return c;}
// Set once per process by forged_frontier v2; session_begin never resets it.
inline std::atomic<bool>&forged_once(){static std::atomic<bool>v(false);return v;}
inline std::atomic<unsigned>&skipped_rechecks(){static std::atomic<unsigned>v(0);return v;}
inline unsigned&range_calls(int thread){static unsigned v[256];return v[thread&255];}
inline bool&gathered(int tile){static bool v[NUM_TILES];return v[tile>=0&&tile<NUM_TILES?tile:0];}
}

void swdb_seam_session_begin(){
 __dxc_session_begin();
 swdb_fault::context_made()=false;swdb_fault::skipped_rechecks()=0;
 for(int t=0;t<256;++t)swdb_fault::range_calls(t)=0;
 for(int t=0;t<NUM_TILES;++t)swdb_fault::gathered(t)=false;
}
// shared_context: every thread receives the first context allocated in the session,
// so all threads issue on tiles and registers one thread owns.
dxc_context swdb_seam_thread_context(){
#if defined(SWDB_DXC_FAULT_SHARED_CONTEXT)
 dxc_context c;
#pragma omp critical(swdb_fault_context)
 {if(!swdb_fault::context_made()){swdb_fault::first_context()=__dxc_thread_context();swdb_fault::context_made()=true;}
  c=swdb_fault::first_context();}
 return c;
#else
 return __dxc_thread_context();
#endif
}
// dropped_wait: no wait completes. read_before_wait: waits on gather results are
// skipped, so the consumer reads gathered values before they are ready.
void swdb_seam_wait(int tile){
#if defined(SWDB_DXC_FAULT_DROPPED_WAIT)
 (void)tile;return;
#else
#if defined(SWDB_DXC_FAULT_READ_BEFORE_WAIT)
 if(swdb_fault::gathered(tile))return;
#endif
 __dxc_wait(tile);
#endif
}
void swdb_seam_gather_i32(void*base,int index,int dst){
 __dxc_gather(static_cast<int32_t*>(base),index,dst);swdb_fault::gathered(dst)=true;
}
// index_wrap: the stream's start register wraps to INT32_MAX before the load.
// chunk_off_by_one: a stream that fills the tile exactly requests one more element.
void swdb_seam_stream_load_i32(void*base,int minimum,int maximum,int stride,int dst){
 {std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
#if defined(SWDB_DXC_FAULT_INDEX_WRAP)
  swdb_strict::reg(minimum).value=uint32_t(INT32_MAX);
#elif defined(SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE)
  const int64_t lo=swdb_strict::rval(minimum),hi=swdb_strict::rval(maximum),step=swdb_strict::rval(stride);
  if(step>0&&hi>=lo&&(hi-lo+step-1)/step==int64_t(TILE_SIZE))swdb_strict::reg(maximum).value=uint32_t(hi+step);
#endif
  swdb_fault::range_calls(swdb_strict::thread())=0;
 }
 __dxc_stream_load(static_cast<int32_t*>(base),minimum,maximum,stride,dst);swdb_fault::gathered(dst)=false;
}
// dropped_continuation: after the first range loop of a stream, the loop state is
// forced to its end, so every continuation tile comes back empty.
void swdb_seam_range_loop(int last_i,int last_j,int lower,int upper,int stride,int rows,int columns){
#if defined(SWDB_DXC_FAULT_DROPPED_CONTINUATION)
 {std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
  if(swdb_fault::range_calls(swdb_strict::thread())++>0)swdb_strict::reg(last_i).value=uint32_t(swdb_strict::tile(lower).size);}
#endif
 __dxc_range_loop(last_i,last_j,lower,upper,stride,rows,columns);
 swdb_fault::gathered(rows)=false;swdb_fault::gathered(columns)=false;
}
void swdb_seam_alu_scalar(int src,int reg,int dst,Operation_t op){
 __dxc_alu_scalar(src,reg,dst,op);swdb_fault::gathered(dst)=false;
}
// skipped_cas_recheck: a claim whose compare fails succeeds anyway (at most eight per
// session), as if the CPU skipped the recheck of a stale DX100 hint.
bool swdb_seam_cas_failed(){
#if defined(SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK)
 return swdb_fault::skipped_rechecks().fetch_add(1)<8;
#else
 return false;
#endif
}
// forged_frontier, version 2 (ticket 67): the first CPU queue push of the run is pushed twice,
// whatever the tile size, frontier threshold or chunk timing, so every candidate that pushes
// through the contract's queue seam (clause L4) fires it; only the evaluator's frontier record
// (`duplicate_frontier`, judged out of process) can reject it.
bool swdb_seam_push_twice(){
#if defined(SWDB_DXC_FAULT_FORGED_FRONTIER_V2)
 return !swdb_fault::forged_once().exchange(true);
#else
 return false;
#endif
}
