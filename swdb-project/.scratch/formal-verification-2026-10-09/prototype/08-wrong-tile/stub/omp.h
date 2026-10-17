// PROTOTYPE (ticket 08): single-thread OpenMP stub so verifiers can read the strict layer.
#pragma once
inline int omp_in_parallel() { return 0; }
inline int omp_get_thread_num() { return 0; }
inline int omp_get_num_threads() { return 1; }
