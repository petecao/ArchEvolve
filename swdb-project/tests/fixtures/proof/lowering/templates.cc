// Probata PoC 24 fixture, construct group "templates": a function template instantiated at int and
// long, and a class template (a type and an integer parameter) instantiated twice.
// Created: 2026-10-14 ET. Updated: 2026-10-14 ET (straight-line, so its WP contract needs no loop hint).
// Harness: templates_harness.inc. Its contract (tests/test_wp_subset.py): result == 2 * (a + 1) + 4 * b.
template <class T>
T twice(T x) {
  return x + x;
}

template <class T, int N>
struct Ring {
  T items[N];
  int head;
  void put(T v) {
    items[head % N] = v;
    ++head;
  }
  T get(int i) const { return items[i % N]; }
};

int swdb_template_unit(int a, long b) {
  Ring<int, 3> r;
  r.head = 0;
  r.put(twice(a));
  r.put(twice(a + 1));
  Ring<long, 2> q;
  q.head = 0;
  q.put(twice(b));
  return r.get(1) + (int)q.get(0) + (int)twice<long>(b);
}
