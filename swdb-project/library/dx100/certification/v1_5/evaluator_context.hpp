// Evaluator-side build context, certify 1.5. Created: 2026-10-05 ET (ticket 78).
// Agent-decided under Yan-Ru's delegation; revisable.
//
// `swdb certify` 1.5 force-includes this header (-include) into every translation unit of the
// evaluator binary: evaluator.cc and the UNCHANGED certify 1.4 sources ../v1_4/record.cc and
// ../v1_4/seams.cc, which include the UNCHANGED strict layer (strict/MAA_functional.hpp). Two names
// are redirected so that the same code runs correctly in the evaluator process:
//
// - The strict layer and the seams name the calling thread with omp_in_parallel(),
//   omp_get_thread_num() and omp_get_num_threads(). In the evaluator a request is served by a
//   server thread, not by the candidate's OpenMP thread, so these three read the identity the
//   request carries (swdb_eval::caller(), set by the server thread for each request).
// - A failed strict check, and a frontier window that repeats a vertex, end the run with
//   std::_Exit(86) and std::_Exit(88). In the evaluator the exit must also end the candidate
//   process, so std::_Exit is redirected to std::swdb_eval_exit (evaluator.cc), which kills the
//   candidate and then exits with the same code.
#pragma once
#include <cstdlib>
#include <omp.h>

namespace swdb_eval {
struct Caller { int thread = 0; int in_parallel = 0; int num_threads = 1; };
Caller &caller();
}
namespace std { [[noreturn]] void swdb_eval_exit(int code) noexcept; }

#define omp_in_parallel() (swdb_eval::caller().in_parallel)
#define omp_get_thread_num() (swdb_eval::caller().thread)
#define omp_get_num_threads() (swdb_eval::caller().num_threads)
#define _Exit swdb_eval_exit
