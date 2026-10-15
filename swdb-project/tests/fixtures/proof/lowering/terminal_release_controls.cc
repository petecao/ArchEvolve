// Terminal-release ownership negative controls. Created: 2026-10-15 ET.
// Every buffer is initialized first, so each refusal exercises the stated ownership/effect boundary.
int swdb_terminal_callback(int n) { return n; }

int swdb_new_escape_owner_address(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  int **escaped = &buf;
  (*escaped)[0] = n;
  delete[] buf;
  return n;
}

int swdb_new_alias_write(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  int *alias = buf;
  alias[0] = n;
  delete[] buf;
  return n;
}

int swdb_new_escape_scalar_address(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  int value = n;
  int *escaped = &value;
  buf[0] = *escaped;
  delete[] buf;
  return value;
}

int swdb_new_conditional_delete(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  if (n == 1) delete[] buf;
  delete[] buf;
  return n;
}

int swdb_new_double_delete(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  delete[] buf;
  delete[] buf;
  return n;
}

int swdb_new_later_callback(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  delete[] buf;
  return swdb_terminal_callback(n);
}

int swdb_new_ignored_uninitialized_read(int n) {
  int *buf = new int[n];
  int ignored = buf[0];
  delete[] buf;
  return n;
}

int swdb_new_reassigned_owner(int n) {
  int *buf = new int[n];
  for (int i = 0; i < n; ++i) buf[i] = n;
  buf = new int[n];
  delete[] buf;
  return n;
}
