#include <stdint.h>
static unsigned int __swdb_dx_reg_words[32];

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
requires 0 <= reg_id < 32; terminates \false; assigns \nothing; ensures \result == __swdb_dx_reg_words[reg_id];
*/
volatile unsigned int get_reg_unsigned_int(int reg_id);
/*@
requires \false; assigns \nothing;
*/
int get_tile_size(void);
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
requires \false; assigns \nothing;
*/
int maa_stream_load(void);
/*@
requires \false; assigns \nothing;
*/
int maa_stream_store(void);
/*@
requires \false; assigns \nothing;
*/
int print_tile(void);
/*@
requires 0 <= reg_id < 32; terminates \false; assigns __swdb_dx_reg_words[reg_id]; ensures __swdb_dx_reg_words[reg_id] == data;
*/
void set_reg_unsigned_int(int reg_id, unsigned int data);
/*@
requires \false; assigns \nothing;
*/
int wait_ready(void);
