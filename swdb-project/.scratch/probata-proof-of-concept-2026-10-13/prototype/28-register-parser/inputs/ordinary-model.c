#include <stdint.h>
extern void __swdb_parser_assert(int);
#define DX_ASSERT(c) __swdb_parser_assert(c)
static unsigned int __swdb_dx_reg_words[32];
void set_reg_unsigned_int(int reg_id,unsigned int data) { DX_ASSERT(0<=reg_id && reg_id<32); __swdb_dx_reg_words[reg_id]=data; }
volatile unsigned int get_reg_unsigned_int(int reg_id) { DX_ASSERT(0<=reg_id && reg_id<32); return __swdb_dx_reg_words[reg_id]; }
