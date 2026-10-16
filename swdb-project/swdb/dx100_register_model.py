"""2026-10-16 ET. Closed ordinary u32 register projection; no freshness premise."""
OWNER='Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'
ENTRY={'kind':'isolated-u32-register-core0-v1','core':0,'register_words':32,'guest_address_bits':64,'byte_order':'little',
 'epoch':'configured scalar MMIO mapping with no queued register packets or device commands',
 'interference':'one thread; no other-core CPU or device accesses to the scalar region through return',
 'mapping':'pinned 4-core MMIO setup; aligned fault-free synchronous noncacheable scalar range128bytes',
 'initial_values':'unconstrained; cells0and1 are written before read'}
STATEMENT=('This original partial synthetic unit uses one configured core0 scalar MMIO range of32 four-byte words, '
 'with aligned fault-free synchronous mapping, no queued register packet/device command, and no competing CPU/device access from any core through normal return. '
 'Initial RF values are unconstrained; both observed cells are overwritten. This conditional environment/source-model premise is owned by the Probata proof-semantics maintainer, pending Yan-Ru freeze review (59). '
 'The source casts away volatile on its typed MMIO dereference and mfence has no memory clobber; the certificate binds exact effective source and compiler-emitted effects under recorded flags, not portable MMIO ordering or implementation correctness. '
 'The simulator RF raw-byte storage typed access, object-lifetime and alias validity are scoped runtime/compiler TCB premises, not established by native sanitizers. '
 'Source/model contract-body agreement remains an owned unverified TCB duty. No hardware termination, freshness, general interference or whole-interface claim follows.')
CALLER='int trust_fixture() { set_reg<unsigned int>(0,7U); set_reg<unsigned int>(1,11U); return (int)(100U*get_reg<unsigned int>(0)+get_reg<unsigned int>(1)); }\n'
STATE='static unsigned int __swdb_dx_reg_words[32];\n'
PROTOTYPES={'set_reg':'void set_reg_unsigned_int(int reg_id, unsigned int data)','get_reg':'volatile unsigned int get_reg_unsigned_int(int reg_id)'}
CONTRACTS={'set_reg':r'requires 0 <= reg_id < 32; terminates \false; assigns __swdb_dx_reg_words[reg_id]; ensures __swdb_dx_reg_words[reg_id] == data;',
 'get_reg':r'requires 0 <= reg_id < 32; terminates \false; assigns \nothing; ensures \result == __swdb_dx_reg_words[reg_id];'}
MODEL='void set_reg_unsigned_int(int reg_id,unsigned int data) { DX_ASSERT(0<=reg_id && reg_id<32); __swdb_dx_reg_words[reg_id]=data; }\nvolatile unsigned int get_reg_unsigned_int(int reg_id) { DX_ASSERT(0<=reg_id && reg_id<32); return __swdb_dx_reg_words[reg_id]; }\n'
