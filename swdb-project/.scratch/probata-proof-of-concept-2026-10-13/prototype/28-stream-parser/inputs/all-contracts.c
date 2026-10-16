#include <stdint.h>
struct __swdb_dx_stream_metadata {
  int phase,ack,status,ready,size,target_size,sent,received;
  int lane0_finished,other_lanes_finished,payload_initialized;
};
static struct __swdb_dx_stream_metadata __swdb_dx_stream_meta;

/*@
requires \false; assigns \nothing;
*/
int add_mem_region(void);
/*@
requires \false; assigns \nothing;
*/
int alloc_MAA(void);
/*@
requires \false; assigns \nothing;
*/
int clear_mem_region(void);
/*@
requires \false; assigns \nothing;
*/
int get_cacheable_tile_pointer(void);
/*@
requires \false; assigns \nothing;
*/
int get_data_type(void);
/*@
requires \false; assigns \nothing;
*/
int swdb_refused_get_new_reg_0(void);
/*@
requires \false; assigns \nothing;
*/
int swdb_refused_get_new_reg_1(void);
/*@
requires \false; assigns \nothing;
*/
int get_new_tile(void);
/*@
requires \false; assigns \nothing;
*/
int get_noncacheable_tile_pointer(void);
/*@
requires \false; assigns \nothing;
*/
int get_reg(void);
/*@
requires SPD_id==0 && __swdb_dx_stream_meta.phase==5 && __swdb_dx_stream_meta.status==2;
terminates \false;
assigns \nothing;
ensures \result==__swdb_dx_stream_meta.size;
*/
volatile unsigned short get_tile_size(int SPD_id);
/*@
requires \false; assigns \nothing;
*/
int init_MAA(void);
/*@
requires \false; assigns \nothing;
*/
int maa_alu_reduce(void);
/*@
requires \false; assigns \nothing;
*/
int maa_alu_scalar(void);
/*@
requires \false; assigns \nothing;
*/
int maa_alu_vector(void);
/*@
requires \false; assigns \nothing;
*/
int maa_const(void);
/*@
requires \false; assigns \nothing;
*/
int maa_indirect_load(void);
/*@
requires \false; assigns \nothing;
*/
int maa_indirect_rmw_scalar(void);
/*@
requires \false; assigns \nothing;
*/
int maa_indirect_rmw_vector(void);
/*@
requires \false; assigns \nothing;
*/
int maa_indirect_store_scalar(void);
/*@
requires \false; assigns \nothing;
*/
int maa_indirect_store_vector(void);
/*@
requires \false; assigns \nothing;
*/
int maa_range_loop(void);
/*@
requires min_reg==0 && max_reg==1 && stride_reg==2 && dst_tile==0 && cond_tile==-1;
requires \valid_read(data+(0..15)) && \initialized(data+(0..15));
requires __swdb_dx_stream_meta.phase==0 && __swdb_dx_stream_meta.ack==0 && __swdb_dx_stream_meta.status==2 && __swdb_dx_stream_meta.ready==0;
requires __swdb_dx_stream_meta.size==0 && __swdb_dx_stream_meta.sent==0 && __swdb_dx_stream_meta.received==0;
requires __swdb_dx_stream_meta.lane0_finished==1 && __swdb_dx_stream_meta.other_lanes_finished==1 && __swdb_dx_stream_meta.payload_initialized==1;
terminates \false;
assigns __swdb_dx_stream_meta;
ensures __swdb_dx_stream_meta.phase==1 && __swdb_dx_stream_meta.ack==1 && __swdb_dx_stream_meta.status==0;
ensures __swdb_dx_stream_meta.ready==255 && __swdb_dx_stream_meta.size==0 && __swdb_dx_stream_meta.target_size==1;
ensures __swdb_dx_stream_meta.lane0_finished==0 && __swdb_dx_stream_meta.other_lanes_finished==0;
ensures __swdb_dx_stream_meta.sent==0 && __swdb_dx_stream_meta.received==0 && __swdb_dx_stream_meta.payload_initialized==1;
*/
void maa_stream_load_unsigned_int(unsigned int *data, int min_reg, int max_reg, int stride_reg, int dst_tile, int cond_tile);
/*@
requires \false; assigns \nothing;
*/
int maa_stream_store(void);
/*@
requires \false; assigns \nothing;
*/
int print_tile(void);
/*@
requires \false; assigns \nothing;
*/
int set_reg(void);
/*@
requires SPD_id==0 && __swdb_dx_stream_meta.phase==1 && __swdb_dx_stream_meta.ack==1 && __swdb_dx_stream_meta.status==0;
requires __swdb_dx_stream_meta.ready==255 && __swdb_dx_stream_meta.size==0 && __swdb_dx_stream_meta.target_size==1;
requires __swdb_dx_stream_meta.sent==0 && __swdb_dx_stream_meta.received==0 && __swdb_dx_stream_meta.payload_initialized==1;
requires __swdb_dx_stream_meta.lane0_finished==0 && __swdb_dx_stream_meta.other_lanes_finished==0;
terminates \false;
assigns __swdb_dx_stream_meta;
ensures __swdb_dx_stream_meta.phase==5 && __swdb_dx_stream_meta.status==2 && __swdb_dx_stream_meta.ready==0;
ensures __swdb_dx_stream_meta.size==1 && __swdb_dx_stream_meta.lane0_finished==1 && __swdb_dx_stream_meta.other_lanes_finished==0;
ensures __swdb_dx_stream_meta.target_size==1 && __swdb_dx_stream_meta.sent==1 && __swdb_dx_stream_meta.received==1 && __swdb_dx_stream_meta.payload_initialized==1;
*/
void wait_ready(int SPD_id);
