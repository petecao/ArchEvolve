/* 2026-10-16 ET. Synthetic abstract trace: region_stall_cross_thread_covers_store. */
int swdb_t28_claim(int thread, int tile, int bytes);
int swdb_t28_cpu_write(int thread, int cell, int value);
int swdb_t28_cpu_read(int thread, int cell);
int swdb_t28_cpu_cas(int thread, int cell, int expected, int desired);
int swdb_t28_issue(int thread, int access, int region, int cell, int tile, int bytes, int value);
int swdb_t28_wait(int tile);
int swdb_t28_tile_read(int thread, int tile, int bytes);
int swdb_t28_pending(int command);
int swdb_t28_result(int command);
int swdb_t28_ready(int tile);
int trust_fixture(void) {
  swdb_t28_claim(0, 0, 4);
  swdb_t28_claim(1, 1, 4);
  int first = swdb_t28_issue(0, 2, 0, 0, 0, 4, 9);
  swdb_t28_issue(1, 1, 0, 0, 1, 4, 0);
  int pending = swdb_t28_pending(first);
  int visible = swdb_t28_cpu_read(1, 0);
  swdb_t28_wait(1);
  return pending == 0 && visible == 9;
}
