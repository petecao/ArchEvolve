// Public observer callback protocol fixture; no native dereferences of retired views.
// Updated: 2026-10-06 ET. This is hand-built contract evidence, never application evidence.
#include <cstdint>
#include <cstring>
#include <cstdio>
extern "C" uint64_t __swdb_object_scope_enter();
extern "C" void __swdb_object_scope_alloc(uint64_t,uint64_t,uint64_t,uint32_t);
extern "C" uint64_t __swdb_object_scope_storage(uint64_t);
extern "C" void __swdb_object_scope_alloc_at(uint64_t,uint64_t,uint64_t,uint32_t,uint64_t);
extern "C" void __swdb_object_scope_view(uint64_t,uint64_t,uint64_t);
extern "C" void __swdb_object_scope_retire(uint64_t,uint64_t);
extern "C" uint64_t __swdb_object_scope_mark(uint64_t);
extern "C" void __swdb_object_scope_restore(uint64_t,uint64_t);
extern "C" void __swdb_object_scope_leave(uint64_t);
extern "C" void __swdb_object_scope_unwind(uint64_t);
extern "C" void __swdb_object_scope_abandon();
extern "C" void __swdb_access_v2(uint32_t,uint32_t,uint64_t,uint64_t,uint64_t,uint32_t);
extern "C" void __swdb_begin();
extern "C" void __swdb_end();
bool shutdown_probe=false;
struct LateProbe {~LateProbe(){if(shutdown_probe)std::fprintf(stderr,"closed=%d\n",__swdb_object_scope_enter()==0);}} late_probe;
void read(uint64_t pointer,uint64_t n=1,uint64_t width=4){__swdb_access_v2(0,0,pointer,n,width,0);}
int main(int argc,char **argv) {
  char a[256]={},b[256]={};uint64_t p=reinterpret_cast<uint64_t>(a),q=reinterpret_cast<uint64_t>(b);
  auto parent=__swdb_object_scope_enter();
  if(argc>1 && std::strcmp(argv[1],"shutdown")==0)shutdown_probe=true;
  if(argc>1 && std::strcmp(argv[1],"aliases")==0){
    __swdb_object_scope_view(parent,p,4);__swdb_object_scope_view(parent,p,4);
    __swdb_begin();read(p);__swdb_end();
    __swdb_object_scope_leave(parent);
    __swdb_begin();read(p);__swdb_end();
  } else if(argc>1 && std::strcmp(argv[1],"overlap")==0){
    __swdb_object_scope_view(parent,p,4);auto child=__swdb_object_scope_enter();
    __swdb_object_scope_view(child,p+2,4);
    __swdb_begin();read(p);__swdb_end();
    __swdb_object_scope_leave(child);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"full-alias")==0){
    __swdb_object_scope_alloc(parent,p,129,1);auto child=__swdb_object_scope_enter();
    __swdb_object_scope_view(child,p+8,4);__swdb_object_scope_leave(child);
    __swdb_begin();read(p+8);__swdb_end();
    __swdb_object_scope_retire(parent,p);
    __swdb_begin();read(p+8);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"late-life")==0){
    auto storage=__swdb_object_scope_storage(parent);auto mark=__swdb_object_scope_mark(parent);
    __swdb_object_scope_alloc_at(parent,p,129,1,storage);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_restore(parent,mark);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"repeat-start")==0){
    __swdb_object_scope_alloc(parent,p,129,1);
    __swdb_begin();read(p);
    __swdb_object_scope_alloc(parent,p,129,1);read(p);__swdb_end();
    __swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"restore")==0){
    __swdb_object_scope_alloc(parent,p,129,1);auto mark=__swdb_object_scope_mark(parent);
    __swdb_object_scope_alloc(parent,q,129,1);
    __swdb_begin();read(p);read(q);__swdb_end();
    __swdb_object_scope_restore(parent,mark);
    __swdb_begin();read(p);read(q);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"unwind")==0){
    __swdb_object_scope_alloc(parent,p,129,1);auto child=__swdb_object_scope_enter();
    __swdb_object_scope_view(child,q,4);__swdb_object_scope_unwind(parent);
    __swdb_begin();read(p);read(q);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"abandon")==0){
    __swdb_object_scope_alloc(parent,p,129,1);__swdb_object_scope_view(parent,q,4);
    __swdb_object_scope_abandon();
    __swdb_begin();read(p);read(q);__swdb_end();
  } else if(argc>1 && std::strcmp(argv[1],"overflow")==0){
    __swdb_object_scope_alloc(parent,p,UINT64_MAX,1);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"request-overflow")==0){
    __swdb_begin();read(p,UINT64_MAX,1);read(p,1,1);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"unknown-restore")==0){
    __swdb_object_scope_alloc(parent,p,129,1);__swdb_object_scope_restore(parent,0);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_leave(parent);
  } else if(argc>1 && std::strcmp(argv[1],"unknown")==0){
    __swdb_object_scope_alloc(parent,p,129,0);
    __swdb_begin();read(p);__swdb_end();__swdb_object_scope_leave(parent);
  } else {
    __swdb_object_scope_view(parent,p,4);__swdb_object_scope_view(parent,q,4);
    __swdb_begin();read(p);read(q);__swdb_end();__swdb_object_scope_leave(parent);
  }
}
