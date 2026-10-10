// Static diagnostic fixture only. Created: 2026-10-06 ET.
extern "C" void *malloc(unsigned long);
extern "C" void free(void *);
extern "C" void __kmpc_fork_call(void *,int,void (*)(int *,int *,...),...);
struct Wrapper { int *data; int size; };
int global_array[4];
extern int external_word;
thread_local int tls_value;
__attribute__((noinline)) void worker(int *gtid,int *bound_tid,Wrapper *w) {
  volatile int local[3];
  int i=(*gtid)&1;
  local[i]=w->size+external_word;
  volatile int *dynamic=(int *)__builtin_alloca((unsigned long)w->size);dynamic[i]=local[i];
  __builtin_memcpy(w->data,global_array,8);
  w->data[i]=local[i]+*bound_tid+global_array[i]+tls_value;
  char first[24],second[24];
  __builtin_memcpy(first,second,8);
  __builtin_memmove(w->data,first,w->size);
  __builtin_memmove(w->data,w->data+1,16);
}
int main(int n,char **) {
  Wrapper w;w.data=(int *)malloc(32);w.size=n;
  w.data[2]=n;
  int g=1,b=2;
  worker(&g,&b,&w);
  __kmpc_fork_call(nullptr,1,(void (*)(int *,int *,...))worker,&w);
  free(w.data);
  return global_array[0];
}
