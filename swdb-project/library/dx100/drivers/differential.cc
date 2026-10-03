// Executable differential tests and semantic negative controls. Updated: 2026-10-03 ET.
#include <algorithm>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include "dxc_lowering.hpp"
#include "reference.hpp"
static std::string control;
static bool broken(const char*name){return control==name;}
static void equal(const std::vector<int32_t>&actual,const std::vector<int32_t>&expected){
 if(actual!=expected){std::cerr<<"SWDB_DIFFERENTIAL_MISMATCH:reference_semantics\n";std::exit(87);}}
static void put(int id,const std::vector<int32_t>&v){auto*p=__dxc_tile_pointer<int32_t>(id);std::copy(v.begin(),v.end(),p);set_tile_size(id,v.size());}
int main(int argc,char**argv){
 const std::string operation=argc>1?argv[1]:"gather";control=argc>2?argv[2]:"";
 omp_set_dynamic(0);omp_set_num_threads(4);alloc_MAA();init_MAA();__dxc_session_begin();
 if(broken("second_session_begin"))__dxc_session_begin();
 dxc_context contexts[NUM_CORES];
#pragma omp parallel
 {contexts[omp_get_thread_num()]=__dxc_thread_context();}
 if(broken("shared_context")||broken("other_thread_register")){
#pragma omp parallel
 {if(omp_get_thread_num()==1){if(broken("other_thread_register"))__dxc_const_i32(7,contexts[0].reg[0]);else (void)__dxc_tile_pointer<int>(contexts[0].tile[0]);}}
 }
 // All regular work uses thread zero's context and includes its real setup lowering.
 dxc_context c=contexts[0];std::vector<int32_t>base(TILE_SIZE+17);
 for(size_t i=0;i<base.size();++i)base[i]=int32_t((i*97)%211)-105;
 add_mem_region(base.data(),base.data()+base.size());
 __dxc_const_i32(0,c.reg[0]);__dxc_const_i32(13,c.reg[1]);__dxc_const_i32(1,c.reg[2]);
 if(broken("truncation"))__dxc_const_i32(TILE_SIZE+1,c.reg[1]);
 if(broken("memory_region"))clear_mem_region();
 if(operation=="range_loop"){
  std::vector<int32_t>lo={0,3,TILE_SIZE+11,2},hi={TILE_SIZE+11,3,TILE_SIZE+19,4};
  if(broken("index_wrap"))hi[0]=INT32_MAX;
  put(c.tile[1],lo);put(c.tile[2],hi);__dxc_const_i32(0,c.reg[4]);__dxc_const_i32(-1,c.reg[5]);
  std::vector<std::pair<int32_t,int32_t>>actual;
  for(unsigned iteration=0;iteration<20;++iteration){
   __dxc_range_loop(c.reg[4],c.reg[5],c.tile[1],c.tile[2],c.reg[2],c.tile[6],c.tile[7]);
   if(!broken("dropped_wait"))__dxc_wait(c.tile[7]);
   const unsigned n=__dxc_tile_size(c.tile[7]);
   if(n==65535){std::cerr<<"SWDB_DIFFERENTIAL_MISMATCH:read_before_wait\n";return 87;}if(!n)break;
   auto*rows=__dxc_tile_pointer<int>(c.tile[6]);auto*cols=__dxc_tile_pointer<int>(c.tile[7]);
   for(unsigned k=0;k<n;++k)actual.push_back({rows[k],cols[k]});
   if(broken("dropped_continuation"))break;
  }
  if(actual!=swdb_reference::range_loop(lo,hi)){std::cerr<<"SWDB_DIFFERENTIAL_MISMATCH:range_continuation\n";return 87;}
 }else{
  std::vector<int32_t>indices={12,0,5,3,5,1};if(broken("index_wrap"))indices[0]=INT32_MAX;
  put(c.tile[0],indices);std::vector<int32_t>expected;int result=c.tile[1];
  if(operation=="stream_load"||operation=="const_i32"||operation=="wait"||operation=="session_begin"||operation=="thread_context"){
   __dxc_stream_load(base.data(),c.reg[0],c.reg[1],c.reg[2],result);
   expected=swdb_reference::stream_load(base,0,13,1);
  }else if(operation=="alu_scalar"){
   __dxc_const_i32(0,c.reg[3]);put(c.tile[0],{-2,0,5,-11,9});
   __dxc_alu_scalar(c.tile[0],c.reg[3],result,Operation_t::LT_OP);
   expected=swdb_reference::alu_scalar({-2,0,5,-11,9},0);
  }else if(operation=="store"){
   put(c.tile[2],{33,34,35,36,37,38});
   // Store without a condition returns each prior value, including repeated indices.
   for(size_t k=0;k<indices.size();++k){expected.push_back(base[indices[k]]);base[indices[k]]=33+k;}
   for(size_t i=0;i<base.size();++i)base[i]=int32_t((i*97)%211)-105;
   maa_indirect_store_vector<int>(base.data(),c.tile[0],c.tile[2],-1,result);
   if(broken("wrong_store_wait"))__dxc_wait(c.tile[2]);
  }else{
   __dxc_gather(base.data(),c.tile[0],result);expected=swdb_reference::gather(base,indices);
  }
  if(broken("constant_uncovered"))__dxc_const_i32(8,c.reg[1]);
  if(broken("read_before_wait")){equal({get_cacheable_tile_pointer<int>(result)[0]},{expected[0]});}
  if(!broken("dropped_wait")&&!broken("wrong_store_wait"))__dxc_wait(result);
  const uint16_t n=__dxc_tile_size(result);
  if(n==65535){std::cerr<<"SWDB_DIFFERENTIAL_MISMATCH:read_before_wait\n";return 87;}
  auto*ptr=__dxc_tile_pointer<int>(result);equal(std::vector<int32_t>(ptr,ptr+n),expected);
 }
 std::cout<<"SWDB_DIFFERENTIAL_PASS:"<<operation<<"\n";return 0;
}
