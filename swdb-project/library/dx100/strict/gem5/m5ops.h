// Certification-only gem5 calls. Updated: 2026-10-03 ET.
#pragma once
#include <cstdint>
inline void m5_checkpoint(uint64_t,uint64_t){}
inline void m5_work_begin(uint64_t,uint64_t){}
inline void m5_work_end(uint64_t,uint64_t){}
inline void m5_reset_stats(uint64_t,uint64_t){}
inline void m5_dump_stats(uint64_t,uint64_t){}
inline void m5_exit(uint64_t){}
