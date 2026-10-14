/* Ticket 50 race fixture (racy). Thread 0 does a plain store to x while every
 * other thread does a CAS on x: an atomic/non-atomic pair on one location with
 * no ordering between them, which is a data race. */
#include <omp.h>
#include <stdio.h>

int x = 0;

int main(void) {
#pragma omp parallel
  {
    if (omp_get_thread_num() == 0) {
      x = 1; /* plain store: races with the CAS below */
    } else {
      int expected = 0;
      __atomic_compare_exchange_n(&x, &expected, 2, 0, __ATOMIC_SEQ_CST,
                                  __ATOMIC_SEQ_CST);
    }
  }
  printf("x=%d\n", x);
  return 0;
}
