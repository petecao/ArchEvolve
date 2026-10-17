/*2026-10-16 ET. PRIVATE closed source-call routes. */
#ifndef SWDB_DX_SOURCE_ROUTES_V1_H
#define SWDB_DX_SOURCE_ROUTES_V1_H
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_unsigned_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(0u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(1u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_float(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(2u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_unsigned_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(3u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(4u,SPD_id,0u);}
/* MAA.hpp:57 57049152e4dd0809dabd17be8d4bbba34d17279cac56e85d6607944cf33c6c2c */
static struct dws_pointer dws_get_cacheable_tile_pointer_double(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(5u,SPD_id,0u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_unsigned_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(0u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_int(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(1u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_float(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(2u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_unsigned_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(3u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_long(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(4u,SPD_id,1u);}
/* MAA.hpp:61 cf8f50be918f90fdd7c327c69e0793f8d78e5c50c3a91f9af4c4fd19d42b34cb */
static struct dws_pointer dws_get_noncacheable_tile_pointer_double(unsigned thread,int SPD_id) {(void)thread;return dws_tile_pointer(5u,SPD_id,1u);}
/* MAA_gem5.hpp:56 3781b69d4af7249210a12448f83b9b5cd125b593ad289e9d3160a3ce936b0fff */
static void dws_add_mem_region(unsigned thread,struct dws_pointer start,struct dws_pointer end) {(void)thread;dwi_add_mem_region(dws_guest_address(start),dws_guest_address(end));}
/* MAA_gem5.hpp:60 b310e561e9966a6190eeece3c13274e4123b2967718bc86babf5990df87c73c5 */
static void dws_clear_mem_region(unsigned thread) {(void)thread;dwi_clear_mem_region();}
/* MAA_gem5.hpp:71 2a9e2e96bbeb7f0c7093c6a3501b5e4d67654d8d360767ce83eb17df57df8eac */
static void dws_alloc_MAA(unsigned thread) {(void)thread;dwi_alloc_MAA();}
/* MAA_gem5.hpp:93 cf708b8c3413e2d8ca92a4fc6c8791df674b603b46a452293b4f0992ef4d4af3 */
static void dws_init_MAA(unsigned thread) {(void)thread;dwi_init_MAA();}
/* MAA_gem5.hpp:98 963dad36a357d2f9063c552ebf4080f5a865896021db3519f3c365d36f507ceb */
static void dws_wait_ready(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");dwi_wait_ready((unsigned)SPD_id);}
/* MAA_gem5.hpp:102 4a0fd5811d735b68236c767b371fcd289c874ce0ebb7f6989a38ce3e8df1a0ab */
static uint16_t dws_get_tile_size(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");return dwi_get_tile_size((unsigned)SPD_id);}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static uint32_t dws_get_reg_unsigned_int(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_u32(dwi_get_reg(thread,0u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static int32_t dws_get_reg_int(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_i32(dwi_get_reg(thread,1u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static float dws_get_reg_float(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_f32(dwi_get_reg(thread,2u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static uint64_t dws_get_reg_unsigned_long(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_u64(dwi_get_reg(thread,3u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static int64_t dws_get_reg_long(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_i64(dwi_get_reg(thread,4u,(unsigned)reg_id));}
/* MAA_gem5.hpp:108 b953d1971b8ea30d7c3d236521b7527e9da0db6ddd6a54d2ffb2aaa9425b5793 */
static double dws_get_reg_double(unsigned thread,int reg_id) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");return dws_unpack_f64(dwi_get_reg(thread,5u,(unsigned)reg_id));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_unsigned_int(unsigned thread,int reg_id,uint32_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,0u,(unsigned)reg_id,dws_pack_u32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_int(unsigned thread,int reg_id,int32_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,1u,(unsigned)reg_id,dws_pack_i32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_float(unsigned thread,int reg_id,float data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,2u,(unsigned)reg_id,dws_pack_f32(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_unsigned_long(unsigned thread,int reg_id,uint64_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,3u,(unsigned)reg_id,dws_pack_u64(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_long(unsigned thread,int reg_id,int64_t data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,4u,(unsigned)reg_id,dws_pack_i64(data));}
/* MAA_gem5.hpp:114 5e454c419bd3a48379d00a50915504958c02891cdfeccd8e040f692aa0071618 */
static void dws_set_reg_double(unsigned thread,int reg_id,double data) {(void)thread;DXM_CHECK(reg_id>=0,"source-register-domain");dwi_set_reg(thread,5u,(unsigned)reg_id,dws_pack_f64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_unsigned_int_args1(unsigned thread,uint32_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,0u,dws_pack_u32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_int_args1(unsigned thread,int32_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,1u,dws_pack_i32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_float_args1(unsigned thread,float data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,2u,dws_pack_f32(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_unsigned_long_args1(unsigned thread,uint64_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,3u,dws_pack_u64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_long_args1(unsigned thread,int64_t data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,4u,dws_pack_i64(data));}
/* MAA_gem5.hpp:119 d8af7565f7d7dbe316e1dd24585c7d0b6be133e7c80912ff6bf2b70f66f9a723 */
static int dws_get_new_reg_double_args1(unsigned thread,double data) {(void)thread;return (int)dwi_get_new_reg_initialized(thread,5u,dws_pack_f64(data));}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_unsigned_int_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,0u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_int_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,1u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_float_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,2u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_unsigned_long_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,3u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_long_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,4u);}
/* MAA_gem5.hpp:129 3fba9d7f93225d028c342b0fb4d01f1046fb5fac3dfb2a27494d6d906b43288f */
static int dws_get_new_reg_double_args0(unsigned thread) {(void)thread;return (int)dwi_get_new_reg(thread,5u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_unsigned_int(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,0u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_int(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,1u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_float(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,2u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_unsigned_long(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,3u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_long(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,4u);}
/* MAA_gem5.hpp:138 960dbf4e946408df95babf1b2774cd016eab93260fe388620361700763947854 */
static int dws_get_new_tile_double(unsigned thread) {(void)thread;return (int)dwi_get_new_tile(thread,5u);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_unsigned_int(unsigned thread,uint32_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,0u,dws_pack_u32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_int(unsigned thread,int32_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,1u,dws_pack_i32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_float(unsigned thread,float data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,2u,dws_pack_f32(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_unsigned_long(unsigned thread,uint64_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,3u,dws_pack_u64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_long(unsigned thread,int64_t data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,4u,dws_pack_i64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:147 cbdbe27bfebe676b7ff954cfb4c3e76e3ceb4e6cc3a8a9df41e932ecf84fde9f */
static void dws_maa_const_double(unsigned thread,double data,int dst_reg) {(void)thread;DXM_CHECK(dst_reg>=0,"source-register-domain");dwi_maa_const(thread,5u,dws_pack_f64(data),(unsigned)dst_reg);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_unsigned_int(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,0u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,0u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_int(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,1u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,1u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_float(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,2u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,2u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_unsigned_long(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,3u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,3u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_long(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,4u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,4u),0);}
/* MAA_gem5.hpp:152 4b6b953ee741105a2c4db94c8beb4c1902e738e7d4ef5c1b51fd9b3eed406dc3 */
static void dws_print_tile_double(unsigned thread,int SPD_id) {(void)thread;DXM_CHECK(SPD_id>=0,"source-tile-domain");uint16_t size=dwi_get_tile_size((unsigned)SPD_id);DXM_CHECK(size<=DXP_VALUE_BOUND,"value-prefix-capacity");for(unsigned lane=0;lane<size;++lane)dws_print_record((unsigned)SPD_id,lane,5u,dxp_cpu_read_bits(thread,(unsigned)SPD_id,lane,5u),0);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_unsigned_int(unsigned thread) {(void)thread;return dwi_get_data_type(0u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_int(unsigned thread) {(void)thread;return dwi_get_data_type(1u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_float(unsigned thread) {(void)thread;return dwi_get_data_type(2u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_unsigned_long(unsigned thread) {(void)thread;return dwi_get_data_type(3u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_long(unsigned thread) {(void)thread;return dwi_get_data_type(4u);}
/* MAA_gem5.hpp:165 c792f66c6e665c625cf61da15704ad57fad40d6557367adaddc9d040128860c5 */
static unsigned dws_get_data_type_double(unsigned thread) {(void)thread;return dwi_get_data_type(5u);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_unsigned_int(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,0u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_int(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,1u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_float(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,2u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_unsigned_long(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,3u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_long(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,4u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:175 67c0e5afc67ecbd9257fb7beff1189d197d41009c89d329fb69bafa7b3b181d9 */
static void dws_maa_alu_scalar_double(unsigned thread,int src1_tile,int src2_reg,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_scalar(thread,5u,src1_tile,src2_reg,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_unsigned_int(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,0u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_int(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,1u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_float(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,2u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_unsigned_long(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,3u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_long(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,4u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:194 b6d4c8344077a0e537608da84c935732e2538d7a516fc33c37b0331ce3d9c4e6 */
static void dws_maa_alu_vector_double(unsigned thread,int src1_tile,int src2_tile,int dst_tile,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_vector(thread,5u,src1_tile,src2_tile,dst_tile,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_unsigned_int(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,0u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_int(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,1u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_float(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,2u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_unsigned_long(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,3u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_long(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,4u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:213 582596b95879529fee61e1ce1ccc611986137cff2cdcd5256f8f11150ff2ed3e */
static void dws_maa_alu_reduce_double(unsigned thread,int src1_tile,int dst_reg,int op,int cond_tile) {(void)thread;(void)dws_fixed_maa_alu_reduce(thread,5u,src1_tile,dst_reg,op,cond_tile);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_unsigned_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,0u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,1u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_float(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,2u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_unsigned_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,3u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,4u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:232 e3a9243c3bfa56750b355782879cbf944b5290f76e83ebade2e474c1c6146ef1 */
static void dws_maa_stream_load_double(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_stream_load(thread,5u,dws_guest_address(data),min_reg,max_reg,stride_reg,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_unsigned_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,0u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_int(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,1u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_float(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,2u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_unsigned_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,3u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_long(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,4u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:251 33fa1f356097231df32e67c60699b1b2f292a46c87fbb77fc513c3e2748f047e */
static void dws_maa_stream_store_double(unsigned thread,struct dws_pointer data,int min_reg,int max_reg,int stride_reg,int src_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_stream_store(thread,5u,dws_guest_address(data),min_reg,max_reg,stride_reg,src_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,0u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_int(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,1u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_float(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,2u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,3u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_long(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,4u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:270 6edae64375800e942b42272a20f459a3d8e65095d23227c394ecdd9807900fd8 */
static void dws_maa_indirect_load_double(unsigned thread,struct dws_pointer data,int idx_tile,int dst_tile,int cond_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_load(thread,5u,dws_guest_address(data),idx_tile,dst_tile,cond_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,0u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,1u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,2u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,3u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,4u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:289 42b43b7340c0fd4a2045a744c160502866c4348ef5c4c73044fddc0be6e946b6 */
static void dws_maa_indirect_store_vector_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_vector(thread,5u,dws_guest_address(data),idx_tile,src_tile,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,0u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,1u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,2u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,3u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,4u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:308 cdbf1df1e471fe7b73eca3dd1411dc88c268f627352157f8ac1f36f22f725832 */
static void dws_maa_indirect_store_scalar_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_store_scalar(thread,5u,dws_guest_address(data),idx_tile,src_reg,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,0u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,1u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,2u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,3u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,4u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:327 6398c1caf415fdaee7e9ddb0bec972c4d781f4a84ed456e29b85962f1a16484e */
static void dws_maa_indirect_rmw_vector_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_tile,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_vector(thread,5u,dws_guest_address(data),idx_tile,src_tile,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_unsigned_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,0u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,0u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_int(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,1u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,1u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_float(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,2u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,2u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_unsigned_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,3u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,3u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_long(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,4u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,4u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:346 544a52719043a0adbb130d101607b2a450725b5d17e377072e7e7c4097c295b5 */
static void dws_maa_indirect_rmw_scalar_double(unsigned thread,struct dws_pointer data,int idx_tile,int src_reg,int o_type,int cond_tile,int dst_tile) {(void)thread;struct dwi_footprint footprint;struct dxw_memory mapping;dws_memory_view(data,5u,&footprint,&mapping);(void)dws_fixed_maa_indirect_rmw_scalar(thread,5u,dws_guest_address(data),idx_tile,src_reg,o_type,cond_tile,dst_tile,&footprint,&mapping);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_unsigned_int(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,0u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_int(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,1u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_float(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,2u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_unsigned_long(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,3u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_long(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,4u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
/* MAA_gem5.hpp:366 6c625e3ff40317fedb980bb7ea78449e5ac916e1cc371b6b92a47a3c8d991191 */
static void dws_maa_range_loop_double(unsigned thread,int last_i_reg,int last_j_reg,int min_tile,int max_tile,int stride_reg,int dst_i_tile,int dst_j_tile,int cond_tile) {(void)thread;(void)dws_fixed_maa_range_loop(thread,5u,last_i_reg,last_j_reg,min_tile,max_tile,stride_reg,dst_i_tile,dst_j_tile,cond_tile);}
static unsigned dws_get_data_type_other(unsigned thread) {(void)thread;return dwi_get_data_type(6);}
#endif
