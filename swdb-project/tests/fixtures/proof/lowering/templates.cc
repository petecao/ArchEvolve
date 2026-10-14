// Probata PoC 24 fixture, construct group "templates": a function template instantiated at int and
// long, and a class template (a type and an integer parameter) instantiated twice.
// Created: 2026-10-14 ET. Harness: templates_harness.inc.
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
  Ring<long, 2> q;
  q.head = 0;
  for (int i = 0; i < 5; ++i) {
    r.put(twice(a + i));
    q.put(twice(b - i));
  }
  return r.get(1) + (int)q.get(0) + (int)twice<long>(b);
}
