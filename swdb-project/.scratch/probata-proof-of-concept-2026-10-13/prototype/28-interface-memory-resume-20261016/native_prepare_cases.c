/* 2026-10-16 ET. INERT prospective C11/C++17 preparation-only controls.
 * No native execution has occurred. Root must admit compiler/runtime/guard first.
 * No MMIO call, actual memory effect, history observation or public proof runs.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>

static jmp_buf refusal_jump;
static const char *expected_rule;
static const char *observed_rule;
static unsigned passed;
static void model_check(int condition,const char *rule) {
  if (condition) return;
  observed_rule=rule;
  if (expected_rule) longjmp(refusal_jump,1);
  fprintf(stderr,"unexpected model refusal: %s\n",rule); exit(2);
}
static void require_test(int condition,const char *message) {
  if (!condition) { fprintf(stderr,"harness assertion: %s\n",message); exit(3); }
}
#define DXM_CHECK(condition,rule) model_check(!!(condition),rule)
#define DXM_CHOOSE(bound) 0u
#define DXM_TILES 32
#define DXM_CELLS 4
#define DXM_NODES 128
#define DXM_HISTORY 4
#define DXM_EVENTS 16
#define DXC_COMMANDS 64
#define DXC_REGIONS 256
#include "backend_for_prepare.h"
#include "interface_memory_prepare.h"

static struct dxi_memory_correspondence domain(void) {
  struct dxi_memory_correspondence value={1000,1004,0x1014,0x1018,64};
  return value;
}
static void reset_case(void) {
  expected_rule=NULL; observed_rule=NULL;
  dxc_reset();
  /* Explicit synthetic ownership; no hardware ownership enforcement inferred. */
  for (unsigned i=0;i<DXM_TILES;++i) dxm_claim_tile(0,i,4);
  dxr_add(6,1000,2000);
}
static unsigned prepare_call(unsigned which,unsigned dtype) {
  struct dxi_memory_correspondence span=domain();
  switch (which) {
  case 0:return dxi_prepare_maa_stream_load(0,dtype,1000,6,4,span);
  case 1:return dxi_prepare_maa_stream_store(0,dtype,1000,5,4,span);
  case 2:return dxi_prepare_maa_indirect_load(0,dtype,1000,1,5,3,span);
  case 3:return dxi_prepare_maa_indirect_store_scalar(0,dtype,1000,1,3,5,span);
  case 4:return dxi_prepare_maa_indirect_store_vector(0,dtype,1000,1,5,3,9,span);
  case 5:return dxi_prepare_maa_indirect_rmw_scalar(0,dtype,1000,1,3,5,span);
  case 6:return dxi_prepare_maa_indirect_rmw_vector(0,dtype,1000,1,5,3,9,span);
  default:require_test(0,"invalid literal call case"); return 0;
  }
}
static void all_literal_mappings(void) {
  /* Independent literals: er,ew,pr,pw,ready. No generator-produced expectation. */
  static const uint64_t narrow[7][5]={
    {16,64,16,64,64},{48,0,48,0,32},{10,32,10,32,34},
    {10,32,10,32,34},{42,512,42,512,546},{10,32,10,32,34},
    {42,512,42,512,546}};
  static const uint64_t wide[7][5]={
    {16,64,16,192,192},{48,0,112,0,96},{10,32,10,96,98},
    {10,32,10,96,98},{42,512,106,1536,1634},{10,32,10,96,98},
    {42,512,106,1536,1634}};
  for (unsigned dtype=0;dtype<6;++dtype) for (unsigned which=0;which<7;++which) {
    reset_case();
    unsigned id=prepare_call(which,dtype);
    dxc_bind(id,dxm_constant(0)); /* No intervening source action. */
    const uint64_t *literal=dtype<3?narrow[which]:wide[which];
    struct dxc_command *c=&dxc_commands[id];
    require_test(c->explicit_read==literal[0] && c->explicit_write==literal[1],"explicit role mapping");
    require_test(c->physical_read==literal[2] && c->physical_write==literal[3],"physical role mapping");
    require_test(c->ready_roles==literal[4],"counted role mapping");
    require_test(c->region==6 && c->pending && c->bound,"first-ID command binding");
    require_test(c->access==((which==0 || which==2)?1u:2u),"per-call memory access kind");
    require_test(c->begin==((which==0 || which==2)?0x1014u:0x1000u),"physical hazard beginning");
    require_test(c->end==((which==0 || which==2)?0x1018u:0x1040u),"physical hazard end");
    ++passed;
  }
}
static void wait_roles(void) {
  reset_case();
  unsigned id=dxi_prepare_maa_stream_store(0,3,1000,5,4,domain());
  dxc_bind(id,dxm_constant(0));
  dxc_wait_tile(4);
  require_test(dxc_commands[id].pending,"condition-only wait must not cover"); ++passed;
  dxc_wait_tile(6);
  require_test(!dxc_commands[id].pending,"counted second-half wait must cover"); ++passed;
}
static void first_containing_id(void) {
  reset_case();
  dxr_reset_state();
  dxr_add(7,1000,2000); dxr_add(6,1050,1060);
  struct dxi_memory_correspondence span={1052,1056,0x1014,0x1018,64};
  unsigned id=dxi_prepare_maa_stream_load(0,0,1052,6,-1,span);
  dxc_bind(id,dxm_constant(0));
  require_test(dxc_commands[id].region==6,"base uses first containing ID, not registration order");
  ++passed;
}
static void reject_width_alias(void) {
  (void)dxi_prepare_maa_stream_store(0,3,1000,5,5,domain());
}
static void reject_owner_second_half(void) {
  dxm_tile_owner[6]=1;
  (void)dxi_prepare_maa_stream_store(0,3,1000,5,-1,domain());
}
static void reject_physical_alias(void) {
  (void)dxi_prepare_maa_indirect_store_vector(0,3,1000,1,5,-1,6,domain());
}
static void reject_last_pair(void) {
  (void)dxi_prepare_maa_stream_store(0,3,1000,31,-1,domain());
}
static void reject_f2_shadow(void) {
  dxr_reset_state(); dxr_add(7,1000,2000); dxr_add(6,1050,1060);
  struct dxi_memory_correspondence span={1052,1056,0x1014,0x1018,64};
  (void)dxi_prepare_maa_stream_load(0,0,1000,6,-1,span);
}
static void reject_other_region_same_line(void) {
  dxr_add(7,3000,4000);
  unsigned old=dxi_prepare_maa_stream_store(0,0,1000,5,-1,domain());
  dxc_bind(old,dxm_constant(0));
  struct dxi_memory_correspondence other={3000,3004,0x1030,0x1034,64};
  (void)dxi_prepare_maa_indirect_load(0,0,3000,1,9,-1,other);
}
static void reject_cpu_line_access(void) {
  unsigned id=dxi_prepare_maa_stream_store(0,0,1000,5,-1,domain());
  dxc_bind(id,dxm_constant(0));
  dxc_cpu_memory_access(1,0x1030,0x1034,0);
}
static void reject_empty_footprint(void) {
  struct dxi_memory_correspondence empty={1000,1000,0x1014,0x1014,64};
  (void)dxi_prepare_maa_stream_load(0,0,1000,6,-1,empty);
}
static void refusal(void (*scenario)(void),const char *rule) {
  reset_case(); expected_rule=rule;
  if (setjmp(refusal_jump)==0) {
    scenario(); expected_rule=NULL; require_test(0,"required domain refusal absent");
  } else {
    expected_rule=NULL;
    require_test(observed_rule && strcmp(observed_rule,rule)==0,"wrong refusal classification");
    ++passed;
  }
}
int main(void) {
  all_literal_mappings(); wait_roles(); first_containing_id();
  refusal(reject_width_alias,"source-role-alias-width");
  refusal(reject_owner_second_half,"tile-ownership");
  refusal(reject_physical_alias,"intra-command-physical-alias");
  refusal(reject_last_pair,"source-pair-domain");
  refusal(reject_f2_shadow,"region-footprint-correspondence");
  refusal(reject_other_region_same_line,"device-memory-footprint-conflict");
  refusal(reject_cpu_line_access,"store-footprint-cpu-access");
  refusal(reject_empty_footprint,"logical-footprint-domain");
  require_test(passed==53,"complete prospective case count");
  printf("{\"preparation_controls\":%u,\"memory_effects_checked\":false,\"public_proof\":false}\n",passed);
  return 0;
}
