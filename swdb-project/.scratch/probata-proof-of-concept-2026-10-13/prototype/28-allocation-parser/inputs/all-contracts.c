#include <stdint.h>
int SPD_count;
int REG_count;
signed char region_count;

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
requires 0 <= REG_count <= 31; assigns REG_count; ensures \result == \old(REG_count) && REG_count == \old(REG_count) + 1;
*/
int get_new_reg_unsigned_int_args0(void);
/*@
requires 0 <= REG_count <= 30; assigns REG_count; ensures \result == \old(REG_count) && REG_count == \old(REG_count) + 2;
*/
int get_new_reg_unsigned_long_long_args0(void);
/*@
requires \false; assigns \nothing;
*/
int get_new_reg_unsigned_int_args1(unsigned int data);
/*@
requires 0 <= SPD_count <= 31; assigns SPD_count; ensures \result == \old(SPD_count) && SPD_count == \old(SPD_count) + 1;
*/
int get_new_tile_unsigned_int(void);
/*@
requires 0 <= SPD_count <= 30; assigns SPD_count; ensures \result == \old(SPD_count) && SPD_count == \old(SPD_count) + 2;
*/
int get_new_tile_unsigned_long_long(void);
/*@
requires \false; assigns \nothing;
*/
int get_noncacheable_tile_pointer(void);
/*@
requires \false; assigns \nothing;
*/
int get_reg(void);
/*@
requires \false; assigns \nothing;
*/
int get_tile_size(void);
/*@
assigns SPD_count, REG_count, region_count; ensures SPD_count == 0 && REG_count == 0 && region_count == 6;
*/
void init_MAA(void);
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
requires \false; assigns \nothing;
*/
int set_reg(void);
/*@
requires \false; assigns \nothing;
*/
int wait_ready(void);
