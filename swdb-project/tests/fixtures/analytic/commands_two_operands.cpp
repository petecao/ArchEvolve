// Counted command fixture whose target-role backend reads a second heap operand.
// Created: 2026-10-09 ET (code review). Logical fixture only; no hardware evidence.
#include <cstdlib>
#include <cstdint>
#include <cstring>
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
unsigned char *second_operand=nullptr;
extern "C" __attribute__((noinline)) void fixture_backend(unsigned char *base,int n){
  volatile uint32_t checksum=0;
  for(int i=0;i<n;++i){uint32_t a,b;std::memcpy(&a,base+i*64,4);std::memcpy(&b,second_operand+i*64,4);checksum+=a+b;}
}
extern "C" __attribute__((noinline)) void fixture_check(unsigned char *base,int n){
  volatile uint32_t checksum=0;
  for(int i=0;i<n;++i){uint32_t value;std::memcpy(&value,base+i*64,sizeof(value));checksum+=value;}
}
extern "C" __attribute__((noinline)) void fixture_read(unsigned char *base,int n){fixture_backend(base,n);fixture_check(base,n);}
int main(){
  unsigned char *data=static_cast<unsigned char *>(std::calloc(512,1));
  second_operand=static_cast<unsigned char *>(std::calloc(512,1));
  if(!data || !second_operand)return 2;
  __swdb_begin();fixture_read(data,6);__swdb_end();
  std::free(data);std::free(second_operand);
}
