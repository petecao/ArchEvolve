// Probata PoC 24 fixture, construct group "classes": a class without inheritance (fields, a member
// function, a const member function, operator[]), a class with a constructor (member initializers, a
// reference member) and a destructor, reference parameters, enum class, constexpr and static_assert.
// Created: 2026-10-14 ET. The unit swdb_class_unit takes only scalars and pointers, so one harness
// (classes_harness.inc) drives the C++ and its C lowering alike. swdb_class_sum is the kept-names
// target: its formal half is written over Bag's field names.
#include <cstddef>

enum class Mode { Sum = 0, Max = 2 };
constexpr int kScale = 3;
static_assert(kScale > 0, "scale is positive");

struct Bag {
  int *data;
  int n;
  int &operator[](int i) { return data[i]; }
  int size() const { return n; }
  void scale(int k) {
    for (int i = 0; i < n; ++i) data[i] *= k;
  }
};

class Counter {
  int count_;
  int &total_;

 public:
  explicit Counter(int &total) : count_(0), total_(total) {}
  ~Counter() { total_ += count_; }
  void add(int v) { count_ += v; }
};

static void bump(int &x, int by) { x += by; }

int swdb_class_sum(const Bag &b) {
  int s = 0;
  for (int i = 0; i < b.n; ++i) s += b.data[i];
  return s;
}

int swdb_class_unit(int *a, int n, int mode) {
  Bag bag;
  bag.data = a;
  bag.n = n;
  int total = 0;
  {
    Counter counter(total);
    for (int i = 0; i < bag.size(); ++i) counter.add(bag[i]);
  }
  bump(total, kScale);
  Mode m = mode == 2 ? Mode::Max : Mode::Sum;
  if (m == Mode::Max) bag.scale(kScale);
  return total + swdb_class_sum(bag) + static_cast<int>(m);
}
