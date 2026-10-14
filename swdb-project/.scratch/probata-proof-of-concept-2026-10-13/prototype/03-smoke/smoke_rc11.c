/* Ticket 03 weak-memory smoke check for GenMC under RC11 (2026-10-14 ET): message passing.
   Safe: the flag is written with release and read with acquire, so a reader that sees
   flag == 1 also sees data == 42. Build with -DBUGGY to make both flag accesses relaxed:
   RC11 then allows flag == 1 with data == 0, an outcome sequential consistency forbids.
   All accesses are atomic, so the bug is a weak-memory outcome, not a data race. */
#include <assert.h>
#include <pthread.h>
#include <stdatomic.h>

#ifdef BUGGY
#define REL memory_order_relaxed
#define ACQ memory_order_relaxed
#else
#define REL memory_order_release
#define ACQ memory_order_acquire
#endif

atomic_int data, flag;

void *writer(void *arg) {
  (void)arg;
  atomic_store_explicit(&data, 42, memory_order_relaxed);
  atomic_store_explicit(&flag, 1, REL);
  return NULL;
}

void *reader(void *arg) {
  (void)arg;
  if (atomic_load_explicit(&flag, ACQ) == 1)
    assert(atomic_load_explicit(&data, memory_order_relaxed) == 42);
  return NULL;
}

int main(void) {
  pthread_t w, r;
  pthread_create(&w, NULL, writer, NULL);
  pthread_create(&r, NULL, reader, NULL);
  pthread_join(w, NULL);
  pthread_join(r, NULL);
  return 0;
}
