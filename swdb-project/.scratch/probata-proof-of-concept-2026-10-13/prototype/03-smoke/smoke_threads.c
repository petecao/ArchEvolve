/* Ticket 03 concurrency smoke check for CIVL and GenMC (2026-10-14 ET), beyond map 07's
   sequential smoke.c: two threads hand over a value under a mutex.
   Build with -DBUGGY to publish `ready` before writing `data`: then the consumer can see
   ready == 1 with data == 0 (assertion fails), and the write of data races with its read. */
#include <assert.h>
#include <pthread.h>

int data = 0, ready = 0;
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;

void *producer(void *arg) {
  (void)arg;
#ifdef BUGGY
  pthread_mutex_lock(&m);
  ready = 1;
  pthread_mutex_unlock(&m);
  data = 42;
#else
  pthread_mutex_lock(&m);
  data = 42;
  ready = 1;
  pthread_mutex_unlock(&m);
#endif
  return NULL;
}

void *consumer(void *arg) {
  (void)arg;
  pthread_mutex_lock(&m);
  if (ready) assert(data == 42);
  pthread_mutex_unlock(&m);
  return NULL;
}

int main(void) {
  pthread_t p, c;
  pthread_create(&p, NULL, producer, NULL);
  pthread_create(&c, NULL, consumer, NULL);
  pthread_join(p, NULL);
  pthread_join(c, NULL);
  return 0;
}
