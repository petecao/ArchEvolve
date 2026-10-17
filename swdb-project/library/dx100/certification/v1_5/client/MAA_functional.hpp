// Strict DX100 functional interface, candidate side, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// Certify 1.5 compiles the candidate's translation unit against this header instead of
// ../../../strict/MAA_functional.hpp. It declares the same interface (types, macros and calls), but
// holds no model state: every call is a request to the trusted evaluator process (client.cc sends
// it; evaluator.cc runs the unchanged strict layer). Tile pointers point into the shared arena's
// tile windows, which the evaluator keeps equal to the model's CPU-visible tile contents.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
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

// ---- requests (client.cc) ----
void swdb_client_check_fail(const char *name);
void swdb_client_strict_session_begin();
uint64_t swdb_client_operation_count();
void swdb_client_alloc_MAA();
void swdb_client_init_MAA();
void swdb_client_clear_mem_region();
void swdb_client_add_mem_region(void *start, void *end);
int swdb_client_new_tile();
int swdb_client_new_reg();
void swdb_client_const(int32_t value, int id);
int32_t swdb_client_get_reg(int id);
void *swdb_client_tile_pointer(int id);
uint16_t swdb_client_tile_size(int id);
uint16_t swdb_client_tile_ready(int id);
void swdb_client_wait_ready(int id);
void swdb_client_set_tile_size(int id, uint16_t size);
void swdb_client_set_tile_ready(int id, uint16_t ready);
void swdb_client_stream_load(void *base, int lo, int hi, int stride, int dst, int cond);
void swdb_client_indirect_load(void *base, int index, int dst, int cond);
void swdb_client_range_loop(int last_i, int last_j, int minimum, int maximum, int stride, int rows, int columns, int cond);
void swdb_client_alu_scalar(int src, int scalar, int dst, Operation_t op, int cond);
void swdb_client_indirect_store(void *base, int index, int src, int cond, int dst);

namespace swdb_strict {
inline void check(bool value, const char *name) { if (!value) swdb_client_check_fail(name); }
inline int thread() { return omp_in_parallel() ? omp_get_thread_num() : 0; }
inline void session_begin() { swdb_client_strict_session_begin(); }
inline uint64_t operation_count() { return swdb_client_operation_count(); }
}
inline void alloc_MAA() { swdb_client_alloc_MAA(); }
inline void init_MAA() { swdb_client_init_MAA(); }
inline void clear_mem_region() { swdb_client_clear_mem_region(); }
inline void add_mem_region(void *start, void *end) { swdb_client_add_mem_region(start, end); }
inline void m5_add_mem_region(void *start, void *end, int) { add_mem_region(start, end); }
template<class T> inline int get_new_tile() { static_assert(sizeof(T) == 4, "i32 tile"); return swdb_client_new_tile(); }
template<class T> inline int get_new_reg() { static_assert(sizeof(T) == 4, "i32 register"); return swdb_client_new_reg(); }
template<class T> inline void maa_const(T value, int id) { swdb_client_const(int32_t(value), id); }
template<class T> inline int get_new_reg(T value) { int id = get_new_reg<T>(); maa_const(value, id); return id; }
template<class T> inline void set_reg(int id, T value) { maa_const(value, id); }
template<class T> inline T get_reg(int id) { const int32_t v = swdb_client_get_reg(id); T out; static_assert(sizeof(T) == 4, "i32"); __builtin_memcpy(&out, &v, 4); return out; }
template<class T> inline T *get_cacheable_tile_pointer(int id) { return reinterpret_cast<T *>(swdb_client_tile_pointer(id)); }
template<class T> inline volatile T *get_noncacheable_tile_pointer(int id) { return get_cacheable_tile_pointer<T>(id); }
inline uint16_t get_tile_size(int id) { return swdb_client_tile_size(id); }
inline uint16_t get_tile_ready(int id) { return swdb_client_tile_ready(id); }
inline void wait_ready(int id) { swdb_client_wait_ready(id); }
inline void set_tile_size(int id, uint16_t size) { swdb_client_set_tile_size(id, size); }
inline void set_tile_ready(int id, uint16_t ready) { swdb_client_set_tile_ready(id, ready); }
template<class T> inline void maa_stream_load(T *base, int lo, int hi, int stride, int dst, int cond = -1) {
 static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32");
 swdb_client_stream_load((void *)base, lo, hi, stride, dst, cond); }
template<class T> inline void maa_indirect_load(T *base, int index, int dst, int cond = -1) {
 static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32");
 swdb_client_indirect_load((void *)base, index, dst, cond); }
template<class T> inline void maa_range_loop(int last_i, int last_j, int minimum, int maximum, int stride, int rows, int columns, int cond = -1) {
 static_assert(sizeof(T) == 4, "i32"); swdb_client_range_loop(last_i, last_j, minimum, maximum, stride, rows, columns, cond); }
template<class T> inline void maa_alu_scalar(int src, int scalar, int dst, Operation_t op, int cond = -1) {
 static_assert(sizeof(T) == 4, "i32"); swdb_client_alu_scalar(src, scalar, dst, op, cond); }
template<class T> inline void maa_indirect_store_vector(T *base, int index, int src, int cond = -1, int dst = -1) {
 static_assert(sizeof(T) == 4, "strict layer's current operation corpus uses i32");
 swdb_client_indirect_store((void *)base, index, src, cond, dst); }
