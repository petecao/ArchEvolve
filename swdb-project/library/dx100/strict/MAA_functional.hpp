// Strict DX100 functional interface. Updated: 2026-10-04 ET (ticket 70: record channel hook).
// 2026-10-09 ET: with -DSWDB_STRICT_WAIT_RULE_GEM5 (candidate certify 1.7, lowering certify 1.2) the
// wait rule follows the gem5 DX100 device (research 14, .scratch/formal-verification-2026-10-09/
// research/14-dx100-wait-rule.md, sections 1, 4 and 6), including the dispatch stall on tiles
// (IF.cc:193-212). Without the define every line below that the
// old header had compiles exactly as before (each #ifndef branch is the old text, byte for byte).
// Out of scope: DX100 loads and stores still touch main memory at the call (no memory timing).
#pragma once
#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <mutex>
#include <vector>
#include <omp.h>
#ifndef TILE_SIZE
#define TILE_SIZE 16384
#endif
#ifndef NUM_CORES
#define NUM_CORES 4
#endif
#define NUM_TILES_PER_CORE 8
#define NUM_REGS_PER_CORE 8
#define NUM_TILES (NUM_CORES * NUM_TILES_PER_CORE)
#define NUM_SCALAR_REGS (NUM_CORES * NUM_REGS_PER_CORE)
#define NUM_REGIONS 256
#define SWDB_STRICT 1
static_assert(TILE_SIZE > 0 && TILE_SIZE <= 65535, "DX100 tile size exceeds uint16 field");
enum class Operation_t { ADD_OP, SUB_OP, MUL_OP, DIV_OP, MIN_OP, MAX_OP,
 AND_OP, OR_OP, XOR_OP, SHL_OP, SHR_OP, GT_OP, GTE_OP, LT_OP, LTE_OP, EQ_OP, NE_OP, MAX };
#ifdef SWDB_CERT_RECORD
// Candidate certification (certify 1.3, ticket 70, 2026-10-04 ET): a failed check is recorded on
// the evaluator's record channel (library/dx100/certification/record.cc), the only place the
// certifier reads it; the stderr line below is for people only.
void swdb_cert_record_strict(const char *name);
#endif
namespace swdb_strict {
inline void check(bool value, const char *name) {
 if (!value) {
#ifdef SWDB_CERT_RECORD
  swdb_cert_record_strict(name);
#endif
  std::fprintf(stderr,"SWDB_STRICT_ASSERT:%s\n",name); std::fflush(stderr); std::_Exit(86); }
}
struct Tile { std::vector<uint32_t> device, cpu; int owner; size_t writer; uint16_t size;
 Tile(): device(TILE_SIZE), cpu(TILE_SIZE), owner(-1), writer(0), size(0) {} };
struct Reg { uint32_t value; int owner; size_t writer; std::vector<size_t> readers;
 Reg():value(0),owner(-1),writer(0){} };
struct Op { std::vector<size_t> dependencies; std::vector<int> tiles, registers; bool covered;
 Op():covered(false){} };
struct Region { uintptr_t start,end; };
struct State { std::mutex lock; std::vector<Tile> tiles; std::vector<Reg> regs; std::vector<Op> ops;
 std::vector<Region> regions; int tile_count,reg_count; bool session; uint64_t operations;
 State():tiles(NUM_TILES),regs(NUM_SCALAR_REGS),ops(1),tile_count(0),reg_count(0),session(false),operations(0) {ops[0].covered=true;} };
inline State &state(){ static State s; return s; }
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
// gem5 roles of one operation: the tiles it names as src1/src2/dst1/dst2 (never the condition tile),
// how many of its dependencies are tile inputs (they come first), and whether it is a range loop
// that filled its output tile (RangeFuser.cc:166-168, 214-218: it finishes without waiting for the
// producers of its min, max and condition tiles). pending[t]: operations that name tile t (rules 1
// and 3). users[t]: operations that name tile t in any role, the condition included (rule 5 only).
struct Roles { std::vector<int> named; size_t inputs,tile_dependencies; bool filled;
 Roles():inputs(0),tile_dependencies(0),filled(false){} };
struct Gem5 { std::vector<Roles> roles; std::vector<std::vector<size_t>> pending,users;
 Gem5():roles(1),pending(NUM_TILES),users(NUM_TILES){} };
inline Gem5 &gem5(){ static Gem5 g; return g; }
#endif
inline int thread(){return omp_in_parallel()?omp_get_thread_num():0;}
inline Tile &tile(int id){State&s=state();check(id>=0&&id<int(s.tiles.size()),"tile_handle");
 check(s.tiles[id].owner==thread(),"thread_ownership_tile");return s.tiles[id];}
inline Reg &reg(int id){State&s=state();check(id>=0&&id<int(s.regs.size()),"register_handle");
 check(s.regs[id].owner==thread(),"thread_ownership_register");return s.regs[id];}
inline void capacity(uint64_t n){check(n<=TILE_SIZE&&n<=65535,"tile_truncation");}
inline void address(const void *base,int64_t index,size_t bytes){
 check(index>=0&&uint64_t(index)*bytes<UINT64_C(4294967296),"byte_offset_overflow");
 const uintptr_t origin=reinterpret_cast<uintptr_t>(base),offset=uint64_t(index)*bytes;
 check(origin<=UINTPTR_MAX-offset&&origin+offset<=UINTPTR_MAX-bytes,"memory_region");
 const uintptr_t start=origin+offset,end=start+bytes;bool found=false;
 for(const Region&r:state().regions)if(start>=r.start&&end<=r.end){found=true;break;}
 check(found,"memory_region");
}
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
inline size_t issue(const std::vector<int>&inputs,const std::vector<int>&registers,
                    const std::vector<int>&outputs,const std::vector<int>&reg_outputs={}){
 State&s=state();Op op;
 for(int id:inputs)op.dependencies.push_back(tile(id).writer);
 for(int id:registers)op.dependencies.push_back(reg(id).writer);
 op.tiles=outputs;op.registers=reg_outputs;s.ops.push_back(op);const size_t index=s.ops.size()-1;
 for(int id:registers)reg(id).readers.push_back(index);
 for(int id:outputs){Tile&t=tile(id);t.writer=index;std::fill(t.cpu.begin(),t.cpu.end(),UINT32_C(0xa5a5a5a5));}
 for(int id:reg_outputs)reg(id).writer=index;
 ++s.operations;return index;
}
inline void cover(size_t id){State&s=state();if(!id||s.ops[id].covered)return;
 const std::vector<size_t> deps=s.ops[id].dependencies;for(size_t dep:deps)cover(dep);
 s.ops[id].covered=true;for(int t:s.ops[id].tiles)if(s.tiles[t].writer==id)s.tiles[t].cpu=s.tiles[t].device;
}
#else
// Drop covered operations from a pending or users list.
inline void prune_list(std::vector<size_t>&p){State&s=state();
 p.erase(std::remove_if(p.begin(),p.end(),[&s](size_t op){return s.ops[op].covered;}),p.end());}
inline void prune(int t){prune_list(gem5().pending[t]);}
// Cover an operation and, transitively, the producers of its inputs (tile and register), except the
// tile inputs (min, max, condition) of a range loop that filled its output tile.
inline void cover(size_t id){State&s=state();std::vector<size_t> stack(1,id),order;
 while(!stack.empty()){const size_t op=stack.back();stack.pop_back();if(!op||s.ops[op].covered)continue;
  s.ops[op].covered=true;order.push_back(op);const Roles&r=gem5().roles[op];const std::vector<size_t>&deps=s.ops[op].dependencies;
  for(size_t k=r.filled?r.tile_dependencies:0;k<deps.size();++k)stack.push_back(deps[k]);}
 for(size_t op:order)for(int t:s.ops[op].tiles)if(s.tiles[t].writer==op)s.tiles[t].cpu=s.tiles[t].device;
}
// Rule 5, the dispatch stall (IF.cc:193-212): the device accepts a command only when no unfinished
// command names its destination tile as a source, destination or condition, so issuing it covers them.
inline void stall(int t){tile(t);const std::vector<size_t> users=gem5().users[t];for(size_t op:users)cover(op);
 prune_list(gem5().users[t]);}
inline size_t issue(const std::vector<int>&inputs,const std::vector<int>&registers,
                    const std::vector<int>&outputs,const std::vector<int>&reg_outputs={}){
 State&s=state();Op op;Roles roles;
 for(int id:outputs)stall(id);
 for(int id:inputs)op.dependencies.push_back(tile(id).writer);
 roles.tile_dependencies=op.dependencies.size();
 for(int id:registers)op.dependencies.push_back(reg(id).writer);
 op.tiles=outputs;op.registers=reg_outputs;s.ops.push_back(op);const size_t index=s.ops.size()-1;
 roles.named=inputs;roles.inputs=inputs.size();roles.named.insert(roles.named.end(),outputs.begin(),outputs.end());
 gem5().roles.push_back(roles);
 for(int id:roles.named){prune(id);gem5().pending[id].push_back(index);
  prune_list(gem5().users[id]);gem5().users[id].push_back(index);}
 for(int id:registers)reg(id).readers.push_back(index);
 for(int id:outputs){Tile&t=tile(id);t.writer=index;std::fill(t.cpu.begin(),t.cpu.end(),UINT32_C(0xa5a5a5a5));}
 for(int id:reg_outputs)reg(id).writer=index;
 ++s.operations;return index;
}
// The last issued operation's condition tile names no counted role (it stays in users[cond] for rule 5).
// Every call appends it as its last tile input, and calls this under the same lock right after issue,
// so it sits at named[inputs-1].
inline void condition(int cond){if(cond<0)return;const size_t index=state().ops.size()-1;Roles&r=gem5().roles.back();
 r.named.erase(r.named.begin()+(r.inputs-1));--r.inputs;
 std::vector<size_t>&p=gem5().pending[cond];
 for(size_t k=p.size();k>0;--k)if(p[k-1]==index){p.erase(p.begin()+(k-1));break;}}
inline void range_filled(bool filled){gem5().roles.back().filled=filled;}
// A wait on t covers every uncovered operation that names t (src1/src2/dst1/dst2), and t's writer.
inline void wait_gem5(int id){Tile&t=tile(id);const std::vector<size_t> named=gem5().pending[id];
 for(size_t op:named)cover(op);
 cover(t.writer);prune(id);}
#endif
template<class T>inline T read_memory(T*base,int64_t i){address(base,i,sizeof(T));
 static_assert(sizeof(T)==4,"strict layer's current operation corpus uses i32");
 return __atomic_load_n(base+i,__ATOMIC_RELAXED);}
template<class T>inline T *data(int id){return reinterpret_cast<T*>(tile(id).device.data());}
inline int32_t rval(int id){return int32_t(reg(id).value);}
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
inline void reset(){State&s=state();s.tiles.assign(NUM_TILES,Tile());s.regs.assign(NUM_SCALAR_REGS,Reg());
 s.ops.assign(1,Op());s.ops[0].covered=true;s.regions.clear();s.tile_count=s.reg_count=0;s.session=false;s.operations=0;}
#else
inline void reset(){State&s=state();s.tiles.assign(NUM_TILES,Tile());s.regs.assign(NUM_SCALAR_REGS,Reg());
 s.ops.assign(1,Op());s.ops[0].covered=true;s.regions.clear();s.tile_count=s.reg_count=0;s.session=false;s.operations=0;
 gem5()=Gem5();}
#endif
inline void session_begin(){State&s=state();std::lock_guard<std::mutex>guard(s.lock);check(!s.session,"session_begin_twice");s.session=true;}
inline uint64_t operation_count(){return state().operations;}
}
inline void alloc_MAA(){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::reset();}
inline void init_MAA(){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::reset();}
inline void clear_mem_region(){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::state().regions.clear();}
inline void add_mem_region(void*start,void*end){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
 swdb_strict::check(start&&end&&reinterpret_cast<uintptr_t>(end)>=reinterpret_cast<uintptr_t>(start),"memory_region_registration");
 swdb_strict::state().regions.push_back({reinterpret_cast<uintptr_t>(start),reinterpret_cast<uintptr_t>(end)});}
inline void m5_add_mem_region(void*start,void*end,int){add_mem_region(start,end);}
template<class T>inline int get_new_tile(){static_assert(sizeof(T)==4,"i32 tile");auto&s=swdb_strict::state();
 swdb_strict::check(s.tile_count<NUM_TILES,"tile_budget");int id=s.tile_count++;s.tiles[id].owner=swdb_strict::thread();return id;}
template<class T>inline int get_new_reg(){static_assert(sizeof(T)==4,"i32 register");auto&s=swdb_strict::state();
 swdb_strict::check(s.reg_count<NUM_SCALAR_REGS,"register_budget");int id=s.reg_count++;s.regs[id].owner=swdb_strict::thread();return id;}
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
template<class T>inline void maa_const(T value,int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&r=swdb_strict::reg(id);
 for(size_t reader:r.readers)swdb_strict::check(swdb_strict::state().ops[reader].covered,"constant_uncovered_register");
 r.readers.clear();r.value=uint32_t(value);r.writer=0;}
#else
// gem5 holds a CPU register write until no unfinished command names the register (IF.cc:233-249,
// MAA.cc:510-538, CpuSidePort.cc:145-149): the readers are covered instead of failing.
template<class T>inline void maa_const(T value,int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&r=swdb_strict::reg(id);
 const std::vector<size_t> readers=r.readers;for(size_t reader:readers)swdb_strict::cover(reader);
 r.readers.clear();r.value=uint32_t(value);r.writer=0;}
#endif
template<class T>inline int get_new_reg(T value){int id=get_new_reg<T>();maa_const(value,id);return id;}
template<class T>inline void set_reg(int id,T value){maa_const(value,id);}
template<class T>inline T get_reg(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&r=swdb_strict::reg(id);
 return swdb_strict::state().ops[r.writer].covered?T(r.value):T(0xa5a5a5a5);}
template<class T>inline T*get_cacheable_tile_pointer(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);
 return reinterpret_cast<T*>(swdb_strict::tile(id).cpu.data());}
template<class T>inline volatile T*get_noncacheable_tile_pointer(int id){return get_cacheable_tile_pointer<T>(id);}
inline uint16_t get_tile_size(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&t=swdb_strict::tile(id);
 return swdb_strict::state().ops[t.writer].covered?t.size:65535;}
#ifndef SWDB_STRICT_WAIT_RULE_GEM5
inline uint16_t get_tile_ready(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&t=swdb_strict::tile(id);
 return swdb_strict::state().ops[t.writer].covered?1:0;}
inline void wait_ready(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::cover(swdb_strict::tile(id).writer);
 std::atomic_thread_fence(std::memory_order_seq_cst);}
#else
// Ready only when no uncovered operation names t and t's writer is covered.
inline uint16_t get_tile_ready(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);auto&t=swdb_strict::tile(id);
 swdb_strict::prune(id);return swdb_strict::gem5().pending[id].empty()&&swdb_strict::state().ops[t.writer].covered?1:0;}
inline void wait_ready(int id){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::wait_gem5(id);
 std::atomic_thread_fence(std::memory_order_seq_cst);}
#endif
inline void set_tile_size(int id,uint16_t size){std::lock_guard<std::mutex>guard(swdb_strict::state().lock);swdb_strict::capacity(size);
 auto&t=swdb_strict::tile(id);t.size=size;std::copy(t.cpu.begin(),t.cpu.end(),t.device.begin());t.writer=0;}
inline void set_tile_ready(int id,uint16_t ready){if(ready)wait_ready(id);}
template<class T>inline void maa_stream_load(T*base,int lo,int hi,int stride,int dst,int cond=-1){
 std::lock_guard<std::mutex>guard(swdb_strict::state().lock);int64_t begin=swdb_strict::rval(lo),end=swdb_strict::rval(hi),step=swdb_strict::rval(stride);
 swdb_strict::check(begin>=0&&end>=begin&&step>0,"stream_bounds");uint64_t n=(end-begin+step-1)/step;swdb_strict::capacity(n);
 std::vector<int>inputs;if(cond>=0)inputs.push_back(cond);std::vector<T>out(n);
 for(uint64_t k=0;k<n;++k)if(cond<0||swdb_strict::data<uint32_t>(cond)[k])out[k]=swdb_strict::read_memory(base,begin+k*step);
 swdb_strict::issue(inputs,{lo,hi,stride},{dst});std::copy(out.begin(),out.end(),swdb_strict::data<T>(dst));swdb_strict::tile(dst).size=n;
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
 swdb_strict::condition(cond);
#endif
}
template<class T>inline void maa_indirect_load(T*base,int index,int dst,int cond=-1){
 std::lock_guard<std::mutex>guard(swdb_strict::state().lock);size_t n=swdb_strict::tile(index).size;swdb_strict::capacity(n);std::vector<T>out(n);
 for(size_t k=0;k<n;++k)if(cond<0||swdb_strict::data<uint32_t>(cond)[k])out[k]=swdb_strict::read_memory(base,swdb_strict::data<int32_t>(index)[k]);
 std::vector<int>inputs={index};if(cond>=0)inputs.push_back(cond);swdb_strict::issue(inputs,{}, {dst});
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
 swdb_strict::condition(cond);
#endif
 std::copy(out.begin(),out.end(),swdb_strict::data<T>(dst));swdb_strict::tile(dst).size=n;
}
template<class T>inline void maa_range_loop(int last_i,int last_j,int minimum,int maximum,int stride,int rows,int columns,int cond=-1){
 std::lock_guard<std::mutex>guard(swdb_strict::state().lock);int64_t i=swdb_strict::rval(last_i),j=swdb_strict::rval(last_j),step=swdb_strict::rval(stride);
 size_t n=swdb_strict::tile(minimum).size;swdb_strict::check(n==swdb_strict::tile(maximum).size&&step>0&&i>=0&&uint64_t(i)<=n,"range_bounds");
 std::vector<int32_t>is,js;
 while(uint64_t(i)<n&&is.size()<TILE_SIZE){int64_t start=swdb_strict::data<T>(minimum)[i],end=swdb_strict::data<T>(maximum)[i];
  swdb_strict::check(start>=0&&end>=start&&uint64_t(end)*4<UINT64_C(4294967296),"byte_offset_overflow");
  int64_t next=j<start?start:j+step;
  if(next>=end){++i;j=-1;continue;}j=next;
  if(cond<0||swdb_strict::data<uint32_t>(cond)[i]){is.push_back(i);js.push_back(j);}
 }
 std::vector<int>inputs={minimum,maximum};if(cond>=0)inputs.push_back(cond);
 swdb_strict::issue(inputs,{last_i,last_j,stride},{rows,columns},{last_i,last_j});
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
 swdb_strict::condition(cond);swdb_strict::range_filled(is.size()==TILE_SIZE);
#endif
 std::copy(is.begin(),is.end(),swdb_strict::data<int32_t>(rows));std::copy(js.begin(),js.end(),swdb_strict::data<int32_t>(columns));
 swdb_strict::tile(rows).size=is.size();swdb_strict::tile(columns).size=js.size();swdb_strict::reg(last_i).value=i;swdb_strict::reg(last_j).value=j;
}
template<class T>inline T swdb_alu(T a,T b,Operation_t op){switch(op){
 case Operation_t::ADD_OP:return a+b;case Operation_t::SUB_OP:return a-b;case Operation_t::MUL_OP:return a*b;
 case Operation_t::DIV_OP:swdb_strict::check(b!=0,"alu_division");return a/b;
 case Operation_t::MIN_OP:return std::min(a,b);case Operation_t::MAX_OP:return std::max(a,b);
 case Operation_t::LT_OP:return a<b;case Operation_t::LTE_OP:return a<=b;case Operation_t::GT_OP:return a>b;
 case Operation_t::GTE_OP:return a>=b;case Operation_t::EQ_OP:return a==b;case Operation_t::NE_OP:return a!=b;
 case Operation_t::AND_OP:return a&b;case Operation_t::OR_OP:return a|b;case Operation_t::XOR_OP:return a^b;
 case Operation_t::SHL_OP:return uint32_t(a)<<b;case Operation_t::SHR_OP:return uint32_t(a)>>b;
 default:swdb_strict::check(false,"alu_opcode");return T();}}
template<class T>inline void maa_alu_scalar(int src,int scalar,int dst,Operation_t op,int cond=-1){
 std::lock_guard<std::mutex>guard(swdb_strict::state().lock);size_t n=swdb_strict::tile(src).size;std::vector<T>out(n);
 for(size_t k=0;k<n;++k)if(cond<0||swdb_strict::data<uint32_t>(cond)[k])out[k]=swdb_alu(swdb_strict::data<T>(src)[k],T(swdb_strict::rval(scalar)),op);
 std::vector<int>inputs={src};if(cond>=0)inputs.push_back(cond);swdb_strict::issue(inputs,{scalar},{dst});
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
 swdb_strict::condition(cond);
#endif
 std::copy(out.begin(),out.end(),swdb_strict::data<T>(dst));swdb_strict::tile(dst).size=n;
}
template<class T>inline void maa_indirect_store_vector(T*base,int index,int src,int cond=-1,int dst=-1){
 std::lock_guard<std::mutex>guard(swdb_strict::state().lock);size_t n=swdb_strict::tile(index).size;
 swdb_strict::check(n==swdb_strict::tile(src).size,"store_size");std::vector<T>old(n);
 for(size_t k=0;k<n;++k)if(cond<0||swdb_strict::data<uint32_t>(cond)[k]){
  const int32_t j=swdb_strict::data<int32_t>(index)[k];old[k]=swdb_strict::read_memory(base,j);
  __atomic_store_n(base+j,swdb_strict::data<T>(src)[k],__ATOMIC_RELAXED);
 }
 std::vector<int>inputs={index,src};if(cond>=0)inputs.push_back(cond);std::vector<int>outputs;if(dst>=0)outputs.push_back(dst);
 swdb_strict::issue(inputs,{},outputs);if(dst>=0){std::copy(old.begin(),old.end(),swdb_strict::data<T>(dst));swdb_strict::tile(dst).size=n;}
#ifdef SWDB_STRICT_WAIT_RULE_GEM5
 swdb_strict::condition(cond);
#endif
}
