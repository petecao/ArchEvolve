// Real counted command/alias fixture; no hardware evidence. Created: 2026-10-06 ET.
#include <cstdlib>
#include <cstdint>
#include <cstring>
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
extern "C" __attribute__((noinline)) void fixture_backend(unsigned char *base,int n){
  if(n<0)throw 7;
  volatile uint32_t checksum=0;
  for(int i=0;i<n;++i){uint32_t value;std::memcpy(&value,base+i*64,sizeof(value));checksum+=value;}
}
extern "C" __attribute__((noinline)) void fixture_check(unsigned char *base,int n){
  volatile uint32_t checksum=0;
  for(int i=0;i<n;++i){uint32_t value;std::memcpy(&value,base+i*64,sizeof(value));checksum+=value;}
}
extern "C" __attribute__((noinline)) void fixture_read(unsigned char *base,int n){fixture_backend(base,n);fixture_check(base,n);}
extern "C" __attribute__((noinline)) void fixture_nested(unsigned char *base,int n){
  if(n)fixture_nested(base,n-1);else fixture_read(base,6);
  volatile int prevent_tail=n;(void)prevent_tail;
}
extern "C" __attribute__((noinline)) void fixture_setup(){
  volatile int scratch[8];for(int i=0;i<8;++i)scratch[i]=i*i;
}
int main(int argc,char **argv){
  unsigned char *data=static_cast<unsigned char *>(std::calloc(512,1));
  if(!data)return 2;
  static unsigned char other[512];
  const char *mode=argc>1?argv[1]:"";
  bool straddle=std::strcmp(mode,"straddle")==0,unknown=std::strcmp(mode,"unknown")==0,fail=std::strcmp(mode,"throw")==0,deep=std::strcmp(mode,"deep")==0;
  __swdb_begin();
  try{if(std::strcmp(mode,"setup")==0){fixture_setup();data[0]=9;}else if(deep){fixture_nested(data,160);data[0]=7;}else fixture_read(unknown?other:data+(straddle?62:0),fail?-1:6);}
  catch(int){data[0]=1;}
  __swdb_end();
  std::free(data);
}
