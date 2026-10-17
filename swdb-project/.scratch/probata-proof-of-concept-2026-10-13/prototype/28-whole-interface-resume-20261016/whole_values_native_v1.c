/*2026-10-16 ET. INERT native controls. Authoring did not compile or execute.
 * Explicit private fixtures, never actual C++ source/MMIO admission.
 * Requires the three generated value headers plus frozen whole_adapters.h.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <setjmp.h>
static jmp_buf dxw_rejection;
static unsigned dxw_armed,dxw_choose_last,dxw_controls;
static const char *dxw_failure;
static void dxw_check(unsigned valid,const char *rule) {
  if(valid) return;
  dxw_failure=rule;
  if(dxw_armed) longjmp(dxw_rejection,1);
  fprintf(stderr,"unexpected checked refusal: %s\n",rule);exit(2);
}
#define DXM_CHECK(c,r) dxw_check(!!(c),(r))
#define DXM_CHOOSE(n) (dxw_choose_last ? (n)-1u:0u)
#define DXM_NODES 4096
#include "whole_value_backend_v1.h"
#include "whole_adapters.h"
#include "whole_value_builders_v1.h"
#include "whole_closed_routes_v1.h"

static void demand(unsigned valid,const char *label) {
  if(!valid) {fprintf(stderr,"control failed: %s\n",label);exit(3);}
}
static uint64_t bits(unsigned dtype,int value) {
  if(dtype==2) {float x=(float)value;uint32_t b;memcpy(&b,&x,4);return b;}
  if(dtype==5) {double x=(double)value;uint64_t b;memcpy(&b,&x,8);return b;}
  return dtype<3?(uint32_t)value:(uint64_t)(int64_t)value;
}
static struct dwi_footprint footprint(unsigned dtype) {
  struct dwi_footprint f={4096,4096,4096+2*dxp_width(dtype),8192,8256,64};return f;
}
static struct dxw_memory mapping(void) {
  struct dxw_memory m={10,2,4096,4096};return m;
}
static void seed(unsigned dtype) {
  dxc_reset();dxs_alloc();dxw_choose_last=0;
  struct dx_num_runtime runtime={1,1,1};dxt_set_runtime(runtime);
  /* Explicit entry-state fixture, not inferred from alloc/init. */
  for(unsigned i=0;i<DXM_TILES;++i) {dxm_tile_owner[i]=0;dxg_owner[i]=0;}
  dxp_cpu_write_bits(0,0,0,dtype,bits(dtype,10));
  dxp_cpu_write_bits(0,4,0,dtype,bits(dtype,1));
  dxp_cpu_write_bits(0,10,0,dtype,bits(dtype,100));
  dxp_cpu_write_bits(0,10,1,dtype,bits(dtype,200));
  dxp_cpu_write_bits(0,20,0,0,1);dxp_cpu_write_bits(0,20,1,0,0);
  dxz_sizes[0]=dxm_constant(2);dxz_sizes[4]=dxm_constant(2);dxz_sizes[20]=dxm_constant(2);
  dxg_cpu_write_bits(0,0,dtype,bits(dtype,3));
  dxm_cpu_write(0,10,bits(dtype,1000));dxm_cpu_write(0,11,bits(dtype,2000));
  dxs_add_region(4096,4096+2*dxp_width(dtype));
}
static void completed(unsigned command,unsigned counted_tile) {
  demand(dxc_commands[command].pending,"issue-does-not-complete");
  dwi_wait_ready(counted_tile);demand(!dxc_commands[command].pending,"counted-wait-completes");
}
static void alu(unsigned dtype,unsigned opcode) {
  seed(dtype);unsigned command;
  if(opcode==8) command=dxw_call_maa_alu_scalar(0,dtype,0,0,10,0,20);
  else if(opcode==9) command=dxw_call_maa_alu_vector(0,dtype,0,4,10,0,20);
  else command=dxw_call_maa_alu_reduce(0,dtype,0,12,0,20);
  completed(command,0);
  if(opcode==10) demand(dxg_cpu_read_bits(0,12,dtype)==bits(dtype,10),"masked-reduction");
  else {
    demand(dxp_cpu_read_bits(0,10,0,dtype)==bits(dtype,opcode==8?13:11),"typed-alu");
    demand(dxp_cpu_read_bits(0,10,1,dtype)==bits(dtype,200),"inactive-preserves-bytes");
    demand(dxz_get_size(10)==2,"alu-size");
  }
  ++dxw_controls;
}
static void memory(unsigned dtype,unsigned opcode) {
  seed(dtype);struct dwi_footprint f=footprint(dtype);struct dxw_memory m=mapping();unsigned command;
  if(opcode<=1) {
    dxg_cpu_write_bits(0,0,1,0);dxg_cpu_write_bits(0,4,1,2);dxg_cpu_write_bits(0,8,1,1);
    if(opcode==0) command=dxw_call_maa_stream_load(0,dtype,4096,0,4,8,10,20,&f,&m);
    else command=dxw_call_maa_stream_store(0,dtype,4096,0,4,8,0,20,&f,&m);
  } else {
    dxp_cpu_write_bits(0,0,0,0,0); /* lane1 index/data stay uninitialized and inactive */
    if(opcode==2) command=dxw_call_maa_indirect_load(0,dtype,4096,0,10,20,&f,&m);
    else if(opcode==3) command=dxw_call_maa_indirect_store_scalar(0,dtype,4096,0,0,20,10,&f,&m);
    else if(opcode==4) command=dxw_call_maa_indirect_store_vector(0,dtype,4096,0,4,20,10,&f,&m);
    else if(opcode==5) command=dxw_call_maa_indirect_rmw_scalar(0,dtype,4096,0,0,0,20,10,&f,&m);
    else command=dxw_call_maa_indirect_rmw_vector(0,dtype,4096,0,4,0,20,10,&f,&m);
  }
  completed(command,opcode==0?10:0);
  if(opcode==0 || opcode==2) demand(dxp_cpu_read_bits(0,10,0,dtype)==bits(dtype,1000),"typed-load");
  else {
    int expected=opcode==1?10:opcode==3?3:opcode==4?1:opcode==5?1003:1001;
    demand(dxm_cpu_read(0,10)==bits(dtype,expected),"typed-store-rmw");
    if(opcode>=3) demand(dxp_cpu_read_bits(0,10,0,dtype)==bits(dtype,1000),"old-result");
  }
  demand(dxm_cpu_read(0,11)==bits(dtype,2000),"inactive-memory-preserved");
  if(opcode!=1) demand(dxp_cpu_read_bits(0,10,1,dtype)==bits(dtype,200),"inactive-output-preserved");
  ++dxw_controls;
}
static void range(unsigned dtype) {
  seed(1);
  dxp_cpu_write_bits(0,0,0,0,4);dxp_cpu_write_bits(0,4,0,0,6);
  dxg_cpu_write_bits(0,12,1,0);dxg_cpu_write_bits(0,16,1,UINT32_MAX);dxg_cpu_write_bits(0,0,1,1);
  unsigned command=dxw_call_maa_range_loop(0,dtype,12,16,0,4,0,10,14,20);
  completed(command,14);
  demand(dxp_cpu_read_bits(0,10,0,1)==0 && dxp_cpu_read_bits(0,10,1,1)==0,"range-row-output");
  demand(dxp_cpu_read_bits(0,14,0,1)==4 && dxp_cpu_read_bits(0,14,1,1)==5,"range-value-output");
  demand(dxg_cpu_read_bits(0,12,1)==2 && dxg_cpu_read_bits(0,16,1)==UINT32_MAX,"range-continuation");
  demand(dxz_get_size(10)==2 && dxz_get_size(14)==2,"range-two-sizes");++dxw_controls;
}
static void history(unsigned dtype) {
  seed(dtype);struct dwi_footprint f=footprint(dtype);struct dxw_memory m=mapping();
  dxz_sizes[0]=dxm_constant(1);dxp_cpu_write_bits(0,0,0,0,0);
  unsigned first=dxw_call_maa_indirect_load(0,dtype,4096,0,10,-1,&f,&m);
  unsigned next=dxw_call_maa_alu_scalar(0,dtype,10,0,14,0,-1);
  demand(dxc_commands[first].pending && dxc_commands[next].pending,"immutable-dependent-no-eager-cover");
  dxc_cpu_write(1,10,8192,8192+dxp_width(dtype),bits(dtype,2000));dxw_choose_last=1;
  completed(next,14);
  demand(dxp_cpu_read_bits(0,14,0,dtype)==bits(dtype,2003),"other-thread-history-through-dependent-alu");
  ++dxw_controls;
}
static void subtract_fold(unsigned dtype) {
  seed(dtype);dxp_cpu_write_bits(0,0,1,dtype,bits(dtype,3));dxp_cpu_write_bits(0,20,1,0,1);
  unsigned command=dxw_call_maa_alu_reduce(0,dtype,0,12,1,20);completed(command,0);
  demand(dxg_cpu_read_bits(0,12,dtype)==bits(dtype,-7),"source-minus-accumulator-order");++dxw_controls;
}
static void old_order(unsigned last) {
  seed(0);struct dwi_footprint f=footprint(0);struct dxw_memory m=mapping();
  dxp_cpu_write_bits(0,0,0,0,0);dxp_cpu_write_bits(0,0,1,0,0);
  dxp_cpu_write_bits(0,4,1,0,2);dxp_cpu_write_bits(0,20,1,0,1);
  unsigned command=dxw_call_maa_indirect_store_vector(0,0,4096,0,4,20,10,&f,&m);
  dxw_choose_last=last;completed(command,10);
  demand(dxp_cpu_read_bits(0,10,0,0)==(last?2:1000),"progressive-old-first-lane");
  demand(dxp_cpu_read_bits(0,10,1,0)==(last?1000:1),"progressive-old-second-lane");
  demand(dxm_cpu_read(0,10)==(last?1:2),"permitted-action-order");++dxw_controls;
}
static void rejected(unsigned which) {
  seed(0);struct dwi_footprint f=footprint(0);struct dxw_memory m=mapping();
  unsigned command=0;
  if(which==0) dxz_sizes[20]=dxm_constant(1);
  if(which==1) {dxz_sizes[0]=dxm_constant(3);dxz_sizes[20]=dxm_constant(3);}
  if(which==2) {dxg_cpu_write_bits(0,0,1,0);dxg_cpu_write_bits(0,4,1,2);dxg_cpu_write_bits(0,8,1,0);}
  if(which==3) {dxg_cpu_write_bits(0,0,1,0);dxg_cpu_write_bits(0,4,1,0);dxg_cpu_write_bits(0,8,1,1);}
  if(which<=1) command=dxw_call_maa_alu_scalar(0,0,0,0,10,0,20);
  else if(which<=3) command=dxw_call_maa_stream_load(0,0,4096,0,4,8,10,20,&f,&m);
  else if(which==4) {dxp_cpu_write_bits(0,0,0,0,0);command=dxw_call_maa_indirect_load(0,0,4096,0,10,20,&f,&m);}
  else {dxg_cpu_write_bits(0,0,0,0);command=dxw_call_maa_alu_scalar(0,0,0,0,10,3,20);}
  demand(dxc_commands[command].pending,"checked-domain-is-deferred");
  dxw_armed=1;dxw_failure=0;
  if(setjmp(dxw_rejection)==0) {
    if(which==4) dxc_cpu_write(0,10,8192,8196,7);
    else dwi_wait_ready(10);
    demand(0,"expected-refusal");
  }
  dxw_armed=0;
  const char *expected=which==0?"source-size-agreement":which==1?"value-prefix-capacity":
                       which==2?"stream-positive-stride":which==3?"stream-nonempty-range":
                       which==4?"same-thread-read-footprint-write":"numeric.3.i0";
  demand(dxw_failure && strcmp(dxw_failure,expected)==0,"classified-refusal");++dxw_controls;
}
int main(void) {
  for(unsigned dtype=0;dtype<6;++dtype) {
    for(unsigned opcode=0;opcode<=10;++opcode) {
      if(opcode>=8) alu(dtype,opcode);else if(opcode==7) range(dtype);else memory(dtype,opcode);
    }
    history(dtype);subtract_fold(dtype);
  }
  old_order(0);old_order(1);
  for(unsigned which=0;which<6;++which) rejected(which);
  demand(dxw_controls==86,"exact-control-census");
  printf("{\"controls\":86,\"family_dtype_cases\":66,\"history_cases\":6,\"subtract_fold_cases\":6,\"action_order_cases\":2,\"refusals\":6}\n");
  return 0;
}
