"""2026-10-16 ET. Initialized u32 register projection, normal return only."""
from swdb.dx100_register_model import OWNER,ENTRY as REGISTER_ENTRY,STATEMENT as REGISTER_STATEMENT
ENTRY={**REGISTER_ENTRY,'kind':'isolated-initialized-u32-register-core0-v1',
 'host_counter_objects':'REG_count, SPD_count and region_count are disjoint from the configured scalar MMIO range'}
STATEMENT=(REGISTER_STATEMENT+' Software-counter objects are disjoint from the scalar MMIO range. '
 'init_MAA resets only software counters and establishes no RF value or hardware freshness. '
 'Each initialized allocation has an ordinary pre-write signed-domain/capacity obligation, 0 <= REG_count <= 31; it is not an environment assumption. '
 'The exact original store and fence precede the final capacity assertion. The source/model correspondence and disjoint-address premise remain owned TCB duties pending Yan-Ru freeze review (59).')
CALLER=('int trust_fixture() { init_MAA(); int first=get_new_reg<unsigned int>(7U); '
 'int second=get_new_reg<unsigned int>(11U); return (int)(100U*get_reg<unsigned int>(first)+get_reg<unsigned int>(second)); }\n')
STATE='int SPD_count;\nint REG_count;\nsigned char region_count;\nstatic unsigned int __swdb_dx_reg_words[32];\n'
PROTOTYPES={'init_MAA':'void init_MAA(void)',
 'get_new_reg':'int get_new_reg_unsigned_int_args1(unsigned int data)',
 'get_reg':'volatile unsigned int get_reg_unsigned_int(int reg_id)'}
CONTRACTS={'init_MAA':r'assigns SPD_count, REG_count, region_count; ensures SPD_count == 0 && REG_count == 0 && region_count == 6;',
 'get_new_reg':r'requires 0 <= REG_count <= 31; terminates \false; assigns REG_count, __swdb_dx_reg_words[REG_count]; ensures \result == \old(REG_count) && REG_count == \old(REG_count) + 1 && __swdb_dx_reg_words[\result] == data;',
 'get_reg':r'requires 0 <= reg_id < 32; terminates \false; assigns \nothing; ensures \result == __swdb_dx_reg_words[reg_id];'}
MODEL=('void init_MAA(void) { REG_count=0; SPD_count=0; region_count=6; }\n'
 'int get_new_reg_unsigned_int_args1(unsigned int data) { int width=1; DX_ASSERT(width==1 || width==2); int old=REG_count; REG_count+=width; __swdb_dx_reg_words[old]=data; DX_ASSERT(REG_count<=32); return old; }\n'
 'volatile unsigned int get_reg_unsigned_int(int reg_id) { DX_ASSERT(0<=reg_id && reg_id<32); return __swdb_dx_reg_words[reg_id]; }\n')
