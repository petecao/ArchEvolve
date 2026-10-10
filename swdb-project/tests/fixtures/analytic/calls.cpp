// Created: 2026-10-06 ET. Conditional call counts, not application evidence.
extern "C" __attribute__((noinline)) int bump(int x) { return x + 1; }
extern "C" __attribute__((noinline)) int call_scope() {
  int total = 0;
  for (int i = 0; i < 8; ++i)
    if (i % 2 == 0) total += bump(i);
  return total;
}
int main() { return call_scope() == 16 ? 0 : 1; }
