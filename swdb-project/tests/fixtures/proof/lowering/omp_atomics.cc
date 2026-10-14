// Probata PoC 24 fixtures, construct groups "OpenMP" and "atomics", at one thread (a parallel region
// runs as one thread; a CAS is a read, a compare and a write; the symbolic-N program is ticket 45).
// Created: 2026-10-14 ET. Harness: omp_atomics_harness.inc (the C++ side is built without -fopenmp,
// so it runs its pragmas as one thread too).
int swdb_omp_unit(int *a, int n) {
  int sum = 0, hits = 0, maxv = 0;
#pragma omp parallel for reduction(+ : sum) schedule(static)
  for (int i = 0; i < n; ++i) sum += a[i];
#pragma omp parallel
  {
#pragma omp for schedule(dynamic, 1) nowait
    for (int i = 0; i < n; ++i) {
      if (a[i] > 0) {
#pragma omp atomic
        hits += 1;
      }
#pragma omp critical
      {
        if (a[i] > maxv) maxv = a[i];
      }
    }
#pragma omp barrier
  }
  return sum * 100 + hits * 10 + maxv;
}

int swdb_atomics_unit(int *p, int *e, int v) {
  int old = __atomic_load_n(p, __ATOMIC_ACQUIRE);
  __atomic_store_n(p, old + v, __ATOMIC_RELEASE);
  int f = __atomic_fetch_add(p, 1, __ATOMIC_SEQ_CST);
  int x = __atomic_exchange_n(p, f, __ATOMIC_SEQ_CST);
  bool ok = __atomic_compare_exchange_n(p, e, 9, false, __ATOMIC_SEQ_CST, __ATOMIC_SEQ_CST);
  bool ok2 = __sync_bool_compare_and_swap(p, 9, 4);
  int y = __sync_val_compare_and_swap(p, 4, 5);
  int z = __sync_fetch_and_add(p, 2);
  int w = __sync_add_and_fetch(p, 3);
  __sync_synchronize();
  return old + x + ok + ok2 + y + z + w + *p + *e;
}
