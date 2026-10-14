/* Ticket 50 race fixture (race-free). racy_store_cas.c with the plain store
 * removed: only CAS operations touch x inside the parallel region. */
#include <omp.h>
#include <stdio.h>

int x = 0;

int main(void) {
#pragma omp parallel
  {
    if (omp_get_thread_num() == 0) {
      /* store removed */
    } else {
      int expected = 0;
      __atomic_compare_exchange_n(&x, &expected, 2, 0, __ATOMIC_SEQ_CST,
                                  __ATOMIC_SEQ_CST);
    }
  }
  printf("x=%d\n", x);
  return 0;
}
