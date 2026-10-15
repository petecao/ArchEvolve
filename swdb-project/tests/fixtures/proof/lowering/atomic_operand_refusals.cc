// 2026-10-15 ET: original atomic operands must not disappear into a one-thread model.
// Refusal corpus only; the division case is never executed.
int erased_load_order(int *p) {
  int m=0;
  int v=__atomic_load_n(p,m++);
  return 100*m+v;
}
int erased_success_order(int *p,int *e) {
  int m=0;
  bool ok=__atomic_compare_exchange_n(p,e,9,false,m++,0);
  return 100*m+10*ok+*p;
}
int erased_failure_order(int *p,int *e) {
  int m=0;
  bool ok=__atomic_compare_exchange_n(p,e,9,false,5,m++);
  return 100*m+10*ok+*e;
}
int erased_weak_flag(int *p,int *e) {
  int m=0;
  bool ok=__atomic_compare_exchange_n(p,e,9,(m++,false),5,0);
  return 100*m+10*ok+*p;
}
bool weak_spurious(int *p,int *e) {
  return __atomic_compare_exchange_n(p,e,9,true,5,0);
}
int erased_order_rte(int *p,int z) {
  return __atomic_load_n(p,0/z);
}
int erased_thread_fence() {
  int m=0;
  __atomic_thread_fence(m++);
  return m;
}
int erased_signal_fence() {
  int m=0;
  __atomic_signal_fence(m++);
  return m;
}
