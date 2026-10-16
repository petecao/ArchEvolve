"""2026-10-16 ET. Conditional one-u32-stream transition prototype.

No public source admission is granted by this finite C kernel. An explicit
constructor/RF/region/mapping/no-interference certificate must justify entry.
Packet acknowledgement never settles a producer; a wait without a completion
transition remains blocked. No liveness/rank/total returning stub is supplied.
"""


def render_header():
    return r'''
#ifndef SWDB_DX_ONE_STREAM_H
#define SWDB_DX_ONE_STREAM_H
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
enum dxl_result { DXL_OK=0, DXL_BLOCKED=1, DXL_DOMAIN=2, DXL_ORDER=3 };
enum dxl_phase { DXL_BOOT=0, DXL_PART0=1, DXL_PART1=2, DXL_PACKET=3, DXL_DISPATCHED=4, DXL_SERVICE=5, DXL_REQUEST=6, DXL_RESPONSE=7, DXL_FINISHED=8 };
struct dxl_state {
 uint64_t guest_line,physical_line;
 unsigned phase,ack;
 uint8_t tile_status,ready;
 uint16_t size;
 unsigned lane0_finished,other_lanes_finished,payload_initialized;
 uint32_t payload0,input_words[16];
 unsigned input_bound,sent_requests,received_responses;
};
/* This is the declared synthetic constructor projection, not alloc/init and
   not an executable hardware reset. Caller must supply the conditional entry
   certificate; mapping equality/no-interference are separate obligations. */
static enum dxl_result dxl_fresh(struct dxl_state *s,uint64_t guest,uint64_t physical) {
 if(!s || !guest || !physical || guest%64 || physical%64 ||
    guest>UINT64_MAX-64 || physical>UINT64_MAX-64) return DXL_DOMAIN;
 *s=(struct dxl_state){.guest_line=guest,.physical_line=physical,.phase=DXL_BOOT,
    .tile_status=2,.ready=0,.size=0,.lane0_finished=1,.other_lanes_finished=1,
    .payload_initialized=1,.payload0=0};
 return DXL_OK;
}
/* The full input line must be valid and C-initialized before this observation.
   This prototype copies a declared coherent/no-interference source image. The
   ordinary C object to guest/physical mapping still needs a source certificate. */
static enum dxl_result dxl_bind_input(struct dxl_state *s,const uint32_t *words,unsigned count) {
 if(!s || !words || count!=16) return DXL_DOMAIN;
 if(s->phase!=DXL_BOOT) return DXL_ORDER;
 for(unsigned i=0;i<16;++i) s->input_words[i]=words[i];
 s->input_bound=1;return DXL_OK;
}
/* Exact selected header words: STREAM_LD/u32/dst0, no second destination,
   source/condition tiles or register destinations; source RF IDs0/1/2. */
static enum dxl_result dxl_packet(struct dxl_state *s,unsigned slot,uint64_t word) {
 if(!s || slot>2) return DXL_DOMAIN;
 if(s->phase!=slot) return DXL_ORDER;
 uint64_t expected=slot==0 ? UINT64_C(0x00ff00ff) :
                   slot==1 ? UINT64_C(0xffffffff000102ff) : s->guest_line;
 if(word!=expected) return DXL_DOMAIN;
 s->phase=slot+1;
 return DXL_OK;
}
/* MAA::dispatchInstruction on successful IF push: ack after Idle and one
   uint8 decrement. No response, payload write or size update happens here. */
static enum dxl_result dxl_dispatch(struct dxl_state *s) {
 if(!s || s->phase!=DXL_PACKET) return DXL_ORDER;
 if(s->tile_status!=2 || s->ready!=0) return DXL_DOMAIN;
 s->tile_status=0;s->ready=(uint8_t)(s->ready-1);
 s->lane0_finished=0;s->other_lanes_finished=0;
 s->ack=1;s->phase=DXL_DISPATCHED;
 return DXL_OK;
}
/* Only the selected nonempty signed-int0/1/1 RF domain is admitted. Empty or
   reversed ranges encounter a source page-vector bug and are not totalized. */
static enum dxl_result dxl_start(struct dxl_state *s,int min,int max,int stride) {
 if(!s || s->phase!=DXL_DISPATCHED) return DXL_ORDER;
 if(!s->input_bound || min!=0 || max!=1 || stride!=1) return DXL_DOMAIN;
 s->tile_status=1;s->phase=DXL_SERVICE;return DXL_OK;
}
/* StreamAccess hardcodes64-byte lines and4096-byte pages. The selected base is
   aligned, so lane0 is offset0 in the one translated physical line. */
static enum dxl_result dxl_request(struct dxl_state *s,uint64_t line,unsigned bytes,unsigned lane,unsigned offset) {
 if(!s || s->phase!=DXL_SERVICE) return DXL_ORDER;
 if(line!=s->physical_line || bytes!=64 || lane!=0 || offset!=0) return DXL_DOMAIN;
 s->sent_requests=1;s->phase=DXL_REQUEST;return DXL_OK;
}
/* Exact RT/response association plus the separately declared coherent stable
   full-line image. The pending-state byte and initializedness remain distinct
   from lane-finished/global Finished metadata. */
static enum dxl_result dxl_response(struct dxl_state *s,uint64_t line,unsigned bytes,unsigned lane,unsigned offset,uint32_t word) {
 if(!s || s->phase!=DXL_REQUEST) return DXL_ORDER;
 if(line!=s->physical_line || bytes!=64 || lane!=0 || offset!=0 || word!=s->input_words[0]) return DXL_DOMAIN;
 s->payload0=word;s->lane0_finished=1;s->received_responses=1;
 s->phase=DXL_RESPONSE;return DXL_OK;
}
/* Source Response state additionally checks packet sending/timing closure.
   These arguments are event witnesses, not a mechanism that makes progress. */
static enum dxl_result dxl_finish(struct dxl_state *s,unsigned packets_sent,unsigned timing_quiet) {
 if(!s || s->phase!=DXL_RESPONSE) return DXL_ORDER;
 if(packets_sent>1 || timing_quiet>1 || s->ready!=255 || s->tile_status!=1 ||
    s->sent_requests!=1 || s->received_responses!=1) return DXL_DOMAIN;
 if(!packets_sent || !timing_quiet) return DXL_BLOCKED;
 s->size=1;s->tile_status=2;s->ready=(uint8_t)(s->ready+1);
 s->phase=DXL_FINISHED;return DXL_OK;
}
/* BLOCKED here is an admission refusal, not a hardware size wait: the source
   getSize panics unless Finished and provides no cover. */
static enum dxl_result dxl_get_size(const struct dxl_state *s,uint16_t *out) {
 if(!s || !out) return DXL_DOMAIN;
 if(s->tile_status!=2) return DXL_BLOCKED;
 *out=s->size;return DXL_OK;
}
/* Conservative stable-image guard for every CPU/device writer. The region is
   the translated physical64-byte line, never just logical lane0's four bytes.
   Protection begins at the explicit image binding; no cross-core bypass exists. */
static enum dxl_result dxl_memory_write(const struct dxl_state *s,uint64_t address,uint64_t bytes) {
 if(!s || bytes>UINT64_MAX-address) return DXL_DOMAIN;
 if(bytes && s->input_bound && s->phase!=DXL_FINISHED &&
    address<s->physical_line+64 && s->physical_line<address+bytes) return DXL_DOMAIN;
 return DXL_OK;
}
/* A returned core0 ready read supplies literal1 only when ready==0. A blocked
   observation leaves both state and output unchanged; it creates no cover. */
static enum dxl_result dxl_wait_response(const struct dxl_state *s,uint16_t *out) {
 if(!s || !out) return DXL_DOMAIN;
 if(s->ready!=0) return DXL_BLOCKED;
 *out=1;return DXL_OK;
}
#endif
'''
