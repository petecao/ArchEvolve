// Independent address-shape fixtures. Updated: 2026-10-06 ET.
#include <cstring>
struct Node { int value; Node *next; };
extern "C" __attribute__((noinline)) int gather(const int *indices, const int *values) {
  int sum=0;
  for(int i=0;i<4;++i) sum+=values[indices[i]];
  return sum;
}
extern "C" __attribute__((noinline)) int ranged(const int *offsets,const int *values) {
  int sum=0;
  for(int row=0;row<2;++row)
    for(int j=offsets[row];j<offsets[row+1];++j) sum+=values[j];
  return sum;
}
extern "C" __attribute__((noinline)) int chase(Node *p) {
  int sum=0;
  while(p) { sum+=p->value; p=p->next; }
  return sum;
}
extern "C" __attribute__((noinline)) int merge(const bool *choose,const int *left,const int *right) {
  int sum=0;
  for(int i=0;i<4;++i) { const int *selected=choose[i]?left:right; sum+=selected[i]; }
  return sum;
}
extern "C" __attribute__((noinline)) int atomic_update(int *value) {
  for(int i=0;i<3;++i) __atomic_fetch_add(value,1,__ATOMIC_RELAXED);
  return *value;
}
extern "C" __attribute__((noinline)) int sparse_workers(int *value) {
  #pragma omp parallel
  {
    #pragma omp single
    for(int i=0;i<3;++i) *value+=1;
  }
  return *value;
}
int main(int argc,char **argv) {
  int indices[]={3,0,3,2},values[]={2,3,5,7,11},offsets[]={0,2,5};
  int left[]={2,3,5,7},right[]={11,13,17,19}; bool choose[]={true,false,true,false};
  Node c{5,nullptr},b{3,&c},a{2,&b};
  if(argc<2)return 2;
  if(std::strcmp(argv[1],"atomic")==0){int count=0;return atomic_update(&count)==3?0:3;}
  if(std::strcmp(argv[1],"sparse")==0){int count=0;return sparse_workers(&count)==3?0:3;}
  int result=std::strcmp(argv[1],"gather")==0?gather(indices,values):
    std::strcmp(argv[1],"ranged")==0?ranged(offsets,values):
    std::strcmp(argv[1],"chase")==0?chase(&a):merge(choose,left,right);
  return result==21||result==28||result==10||result==39?0:3;
}
