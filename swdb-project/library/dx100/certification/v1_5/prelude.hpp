// Candidate certification prelude, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// Certify 1.5 keeps 1.4's library seams unchanged (../v1_4/prelude.hpp): the same hooks, the same
// names, the same arguments. What changes is where the seams run: in 1.5 the swdb_seam_* functions
// the prelude calls are defined by client.cc, which sends each call to the trusted evaluator
// process; the seam logic (seams.cc), the strict model and the record writer (record.cc) run there,
// unchanged. The candidate's translation unit is compiled against client/MAA_functional.hpp.
//
// One hook is added: the chunk counter of the execution witness (__dxc_accelerated_chunk) is
// counted by the evaluator. In 1.4 the record object read a counter in the candidate's own memory.
#pragma once
#include "../v1_4/prelude.hpp"

void swdb_seam_accelerated_chunk();
inline void swdb_hooked_accelerated_chunk() { swdb_seam_accelerated_chunk(); }
#define __dxc_accelerated_chunk swdb_hooked_accelerated_chunk
