// Probata PoC 24 fixture, construct group "new[] and delete[]". Created: 2026-10-14 ET.
// swdb_new_unit is in range (n >= 1); swdb_new_out_of_range writes one past the end and
// swdb_new_after_delete reads after delete[] (seeded bugs: a proof must not prove them; never run).
// Harness: new_array_harness.inc (the safe unit only).
int swdb_new_unit(int n, int k) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = k;
  int s = 0;
  for (int i = 0; i < n; ++i) s += buf[i];
  delete[] buf;
  return s;
}

int swdb_new_out_of_range(int n) {
  int *buf = new int[n];
  for (int i = 0; i <= n; ++i) buf[i] = i;
  int s = buf[0];
  delete[] buf;
  return s;
}

int swdb_new_after_delete(int n) {
  int *buf = new int[n];
  buf[0] = n;
  delete[] buf;
  return buf[0];
}
