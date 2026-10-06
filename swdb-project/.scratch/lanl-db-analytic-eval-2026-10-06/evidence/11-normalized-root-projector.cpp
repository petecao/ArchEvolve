// Read-only normalized-IR source-origin projection. Created: 2026-10-06 ET.
// This diagnostic does not run passes that mutate IR or collect addresses/timings.
#include "llvm/Analysis/AliasAnalysis.h"
#include "llvm/Analysis/MemoryLocation.h"
#include "llvm/Analysis/ValueTracking.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/DebugProgramInstruction.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/Module.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/FormatVariadic.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/SHA256.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/ADT/StringExtras.h"
#include <limits>
#include <map>
#include <set>
using namespace llvm;

static bool fail(StringRef s) { errs()<<"root-projector: "<<s<<'\n';return false; }
static std::string filePath(const DIFile *f) {
  if(!f)return "";SmallString<256> p(f->getFilename());
  if(!sys::path::is_absolute(p)){SmallString<256>b(f->getDirectory());sys::path::append(b,p);p=b;}
  sys::path::remove_dots(p,true);return p.str().str();
}
static json::Object location(const Instruction *I) {
  const DILocation *d=I?I->getDebugLoc().get():nullptr;
  return json::Object{{"path",d?filePath(d->getFile()):""},{"line",int64_t(d?d->getLine():0)},
    {"column",int64_t(d?d->getColumn():0)},{"llvm_function",I?I->getFunction()->getName().str():""}};
}
static json::Value integer(uint64_t n) {
  if(n>uint64_t(INT64_MAX))return nullptr;return int64_t(n);
}
static json::Value fixedSize(Type *t,const DataLayout &dl) {
  if(!t || !t->isSized())return nullptr;auto n=dl.getTypeAllocSize(t);
  return n.isScalable()?json::Value(nullptr):integer(n.getFixedValue());
}
static std::string typeName(Type *t) { std::string s;raw_string_ostream o(s);t->print(o);return s; }
static std::string hashFile(StringRef p) {
  auto b=MemoryBuffer::getFile(p);if(!b)return "";
  auto s=(*b)->getBuffer();auto h=SHA256::hash(ArrayRef<uint8_t>(reinterpret_cast<const uint8_t*>(s.data()),s.size()));
  return toHex(ArrayRef<uint8_t>(h),true);
}
static bool ids(StringRef text,std::set<unsigned>&out) {
  SmallVector<StringRef> parts;text.split(parts,',',-1,false);
  for(auto p:parts){unsigned n;if(p.getAsInteger(10,n))return fail("invalid site list");out.insert(n);}return true;
}

class Roots {
  Module &M;const DataLayout &DL;
  std::map<const Value*,std::string> tokens;
public:
  std::map<std::string,json::Object> rows;
  explicit Roots(Module&m):M(m),DL(m.getDataLayout()){}
  std::string token(const Value *v) {
    if(auto *g=dyn_cast<GlobalValue>(v))return "global:"+g->getName().str();
    if(auto *a=dyn_cast<Argument>(v))return a->getParent()->getName().str()+":argument:"+std::to_string(a->getArgNo());
    if(auto *i=dyn_cast<Instruction>(v)){unsigned n=0;for(const auto &x:instructions(i->getFunction())){if(&x==i)break;++n;}
      return i->getFunction()->getName().str()+":instruction:"+std::to_string(n);}
    return "unsupported-constant"; // Never export numeric pointer constants or raw IR.
  }
  std::string describe(Value *ptr,unsigned depth=0) {
    Value *v=getUnderlyingObject(ptr,32);auto existing=tokens.find(v);if(existing!=tokens.end())return existing->second;
    std::string id=token(v);tokens[v]=id;rows[id]=json::Object{{"root_class","pending"}};
    json::Object o{{"id",id},{"full_allocation_identity_proven",false}};
    if(depth>=12){o["root_class"]="depth_limit";rows[id]=std::move(o);return id;}
    if(auto *a=dyn_cast<AllocaInst>(v)) {
      o["root_class"]="alloca";o["producer"]=a->getFunction()->getName().str();o["source_location"]=location(a);
      o["allocated_type"]=typeName(a->getAllocatedType());o["element_alloc_bytes"]=fixedSize(a->getAllocatedType(),DL);
      json::Array vars;
      for(auto &i:instructions(a->getFunction()))for(DbgRecord &dr:i.getDbgRecordRange())
        if(auto *d=dyn_cast<DbgVariableRecord>(&dr);d && d->isDbgDeclare())
          for(Value *x:d->location_ops())if(x && x->getType()->isPointerTy() && getUnderlyingObject(x,32)==a){
            auto *v=d->getVariable();vars.push_back(json::Object{{"name",v->getName().str()},
              {"path",filePath(v->getFile())},{"line",int64_t(v->getLine())},
              {"scope","debug variable annotation; allocation bounds come from target DataLayout"}});break;}
      o["source_variables"]=std::move(vars);
      o["alignment_bytes"]=integer(a->getAlign().value());o["constant_extent_bytes"]=nullptr;
      o["array_count_constant"]=nullptr;o["extent_status"]="dynamic_or_scalable";
      if(auto *n=dyn_cast<ConstantInt>(a->getArraySize());n && n->getValue().getActiveBits()<=64 && a->getAllocatedType()->isSized()){
        auto sz=DL.getTypeAllocSize(a->getAllocatedType());uint64_t count=n->getZExtValue();
        o["array_count_constant"]=integer(count);
        if(!sz.isScalable() && (!count || sz.getFixedValue()<=UINT64_MAX/count)){
          auto total=sz.getFixedValue()*count;o["constant_extent_bytes"]=integer(total);
          o["extent_status"]=total<=uint64_t(INT64_MAX)?"fixed_target_data_layout":"json_integer_range_exceeded";
        }
      }
      unsigned starts=0,ends=0,returns=0,resumes=0,restores=0;
      for(auto &i:instructions(a->getFunction())){
        returns+=isa<ReturnInst>(i);resumes+=isa<ResumeInst>(i);
        if(auto *cb=dyn_cast<IntrinsicInst>(&i)){
          if(cb->getIntrinsicID()==Intrinsic::stackrestore)++restores;
          if(isa<LifetimeIntrinsic>(cb) && cb->arg_size() && getUnderlyingObject(cb->getArgOperand(cb->arg_size()-1),32)==a){
            starts+=cb->getIntrinsicID()==Intrinsic::lifetime_start;ends+=cb->getIntrinsicID()==Intrinsic::lifetime_end;
          }
        }
      }
      o["lifetime_markers"]=json::Object{{"start_sites",int64_t(starts)},{"end_sites",int64_t(ends)},
        {"function_return_sites",int64_t(returns)},{"function_resume_sites",int64_t(resumes)},{"function_stackrestore_sites",int64_t(restores)}};
      o["lifetime_status"]="static_markers_and_frame_exits_only; runtime_registration_not_present";
    } else if(auto *g=dyn_cast<GlobalVariable>(v)) {
      o["root_class"]=g->isDeclaration()?"global_declaration":"global_definition";
      o["declared_type"]=typeName(g->getValueType());o["declared_type_bytes"]=fixedSize(g->getValueType(),DL);
      o["constant_extent_bytes"]=g->isDeclaration()?json::Value(nullptr):fixedSize(g->getValueType(),DL);
      o["thread_local"]=g->isThreadLocal();o["constant"]=g->isConstant();o["unnamed_address"]=g->hasGlobalUnnamedAddr();
      o["lifetime_status"]=g->isThreadLocal()?"thread_storage; no observer registration":"static_storage; no observer registration";
    } else if(auto *a=dyn_cast<Argument>(v)) {
      o["root_class"]="argument";o["producer"]=a->getParent()->getName().str();o["argument_index"]=int64_t(a->getArgNo());
      json::Array producers;bool omp=false;
      for(Function &f:M)for(auto &i:instructions(f))if(auto *cb=dyn_cast<CallBase>(&i)){
        auto *callee=cb->getCalledFunction();if(!callee)continue;
        int arg=-1;std::string binding;
        if(callee==a->getParent() && a->getArgNo()<cb->arg_size()){arg=a->getArgNo();binding="direct_call_argument";}
        if(callee->getName()=="__kmpc_fork_call" && cb->arg_size()>=3 && cb->getArgOperand(2)->stripPointerCasts()==a->getParent()){
          omp=true;
          if(a->getArgNo()>=2 && a->getArgNo()+1<cb->arg_size()){arg=a->getArgNo()+1;binding="kmpc_micro_shared_argument";}
        }
        if(arg>=0){json::Object p{{"binding",binding},{"caller",f.getName().str()},{"source_location",location(cb)},
          {"call_argument_index",int64_t(arg)}};auto *value=cb->getArgOperand(arg);
          if(value->getType()->isPointerTy())p["root_id"]=describe(value,depth+1);else p["root_id"]=nullptr;
          producers.push_back(std::move(p));}
      }
      o["caller_producers"]=std::move(producers);
      if(omp && a->getArgNo()<2){o["abi_role"]=a->getArgNo()?"kmpc_micro_bound_tid":"kmpc_micro_global_tid";
        o["abi_typed_referent_bytes"]=4;o["abi_view_scope"]="microtask_execution_only; not full libomp allocation";}
      o["lifetime_status"]="depends_on_caller_or_explicit_abi_view; not inferred from pointer width";
    } else if(auto *l=dyn_cast<LoadInst>(v)) {
      o["root_class"]="loaded_pointer";o["producer"]=l->getFunction()->getName().str();o["source_location"]=location(l);
      o["pointer_field_storage_root_id"]=describe(l->getPointerOperand(),depth+1);
      o["pointee_extent_status"]="unknown; container extent does not bound loaded pointee";
    } else if(auto *cb=dyn_cast<CallBase>(v)) {
      o["root_class"]="call_result";o["producer"]=cb->getFunction()->getName().str();o["source_location"]=location(cb);
      o["callee"]=cb->getCalledFunction()?cb->getCalledFunction()->getName().str():"indirect";
      o["extent_status"]="call_result_extent_not_assumed";
    } else if(auto *p=dyn_cast<PHINode>(v)) {
      o["root_class"]="phi_pointer";json::Array incoming;
      for(Value *x:p->incoming_values())incoming.push_back(describe(x,depth+1));o["incoming_roots"]=std::move(incoming);
    } else if(auto *s=dyn_cast<SelectInst>(v)) {
      o["root_class"]="selected_pointer";o["true_root"]=describe(s->getTrueValue(),depth+1);o["false_root"]=describe(s->getFalseValue(),depth+1);
    } else o["root_class"]="unsupported_pointer_producer";
    rows[id]=std::move(o);return id;
  }
};

int main(int argc,char **argv) {
  if(argc!=6){errs()<<"usage: root-projector normalized.bc source.json output.json access-sites call-sites\n";return 2;}
  LLVMContext ctx;SMDiagnostic err;auto m=parseIRFile(argv[1],err,ctx);if(!m){err.print(argv[0],errs());return 2;}
  auto b=MemoryBuffer::getFile(argv[2]);if(!b){fail("cannot read source.json");return 2;}
  auto parsed=json::parse((*b)->getBuffer());if(!parsed){fail("malformed source.json");return 2;}
  auto *obj=parsed->getAsObject();auto *access=obj?obj->getArray("accesses"):nullptr;auto *calls=obj?obj->getArray("unmodeled_calls"):nullptr;
  if(!access || !calls){fail("source.json needs accesses and unmodeled_calls");return 2;}
  std::set<unsigned> wantA,wantC;if(!ids(argv[4],wantA)||!ids(argv[5],wantC))return 2;
  Roots roots(*m);json::Array outA,outC;unsigned site=0,call=0;
  LoopAnalysisManager lam;FunctionAnalysisManager fam;CGSCCAnalysisManager cgam;ModuleAnalysisManager mam;PassBuilder pb;
  pb.registerModuleAnalyses(mam);pb.registerCGSCCAnalyses(cgam);pb.registerFunctionAnalyses(fam);pb.registerLoopAnalyses(lam);pb.crossRegisterProxies(lam,fam,cgam,mam);
  const auto &dl=m->getDataLayout();
  for(Function &f:*m) {
    if(f.isDeclaration() || f.getName().starts_with("__swdb_") || !f.getSubprogram())continue;
    for(Instruction &i:instructions(f)) {
      if(isa<DbgInfoIntrinsic>(i)||isa<PHINode>(i)||isa<AllocaInst>(i))continue;
      Value *ptr=nullptr;Type *t=nullptr;std::string update="read";
      if(auto *l=dyn_cast<LoadInst>(&i)){ptr=l->getPointerOperand();t=l->getType();}
      if(auto *s=dyn_cast<StoreInst>(&i)){ptr=s->getPointerOperand();t=s->getValueOperand()->getType();update="write";}
      if(auto *a=dyn_cast<AtomicRMWInst>(&i)){ptr=a->getPointerOperand();t=a->getValOperand()->getType();
        update="arbitrary";switch(a->getOperation()){
          case AtomicRMWInst::Add:case AtomicRMWInst::Sub:case AtomicRMWInst::FAdd:case AtomicRMWInst::FSub:update="add-update";break;
          case AtomicRMWInst::Max:case AtomicRMWInst::Min:case AtomicRMWInst::UMax:case AtomicRMWInst::UMin:case AtomicRMWInst::FMax:case AtomicRMWInst::FMin:update="min-max-update";break;
          case AtomicRMWInst::Xchg:update="write";break;default:break;}}
      if(auto *a=dyn_cast<AtomicCmpXchgInst>(&i)){ptr=a->getPointerOperand();t=a->getCompareOperand()->getType();update="compare-and-swap";}
      if(ptr){
        if(site>=access->size()){fail("too many enumerated access sites");return 2;}auto *row=(*access)[site].getAsObject();
        unsigned lanes=isa<FixedVectorType>(t)?cast<FixedVectorType>(t)->getNumElements():1;auto width=dl.getTypeStoreSize(t);
        if(width.isScalable()){fail("scalable access outside this projection contract");return 2;}
        unsigned line=i.getDebugLoc()?i.getDebugLoc().getLine():0,col=i.getDebugLoc()?i.getDebugLoc().getCol():0;
        if(!row || row->getInteger("site")!=int64_t(site) || row->getString("llvm_function")!=f.getName() ||
          row->getInteger("line")!=int64_t(line) || row->getInteger("column")!=int64_t(col) ||
          row->getInteger("element_bytes")!=int64_t(width.getFixedValue()/lanes) || row->getInteger("ir_lanes")!=int64_t(lanes) || row->getString("update_kind")!=update ||
          row->getString("path")!=filePath(i.getDebugLoc()?i.getDebugLoc()->getFile():f.getSubprogram()->getFile())){
          errs()<<"root-projector: access map mismatch at "<<site<<'\n';return 2;}
        if(wantA.erase(site)){json::Object out=*row;out.erase("address_expression");out["root_id"]=roots.describe(ptr);outA.push_back(std::move(out));}++site;
      }
      if(auto *cb=dyn_cast<CallBase>(&i)){
        auto *callee=cb->getCalledFunction();StringRef name=callee?callee->getName():"indirect-call";
        if(callee && (name.starts_with("llvm.fmuladd")||name.starts_with("llvm.fma")||name.starts_with("__swdb_")||
          name.starts_with("llvm.lifetime.")||name.starts_with("llvm.dbg.")||name=="llvm.assume"))continue;
        if(call>=calls->size()){fail("too many enumerated call sites");return 2;}auto *row=(*calls)[call].getAsObject();
        unsigned line=callee && i.getDebugLoc()?i.getDebugLoc().getLine():0;
        if(!row || row->getInteger("site")!=int64_t(call) || row->getString("name")!=name || row->getInteger("line")!=int64_t(line)){
          errs()<<"root-projector: call map mismatch at "<<call<<'\n';return 2;}
        if(wantC.erase(call)){json::Object out=*row;out["source_location"]=location(cb);
          if(auto *mem=dyn_cast<MemTransferInst>(cb)){
            out["source_root_id"]=roots.describe(mem->getSource());out["destination_root_id"]=roots.describe(mem->getDest());
            out["source_alignment_bytes"]=mem->getSourceAlign()?integer(mem->getSourceAlign()->value()):json::Value(nullptr);
            out["destination_alignment_bytes"]=mem->getDestAlign()?integer(mem->getDestAlign()->value()):json::Value(nullptr);
            out["constant_length_bytes"]=nullptr;out["length_kind"]="runtime_value";
            if(auto *n=dyn_cast<ConstantInt>(mem->getLength());n && n->getValue().getActiveBits()<=64){out["constant_length_bytes"]=integer(n->getZExtValue());out["length_kind"]="constant";}
            auto ar=fam.getResult<AAManager>(f).alias(MemoryLocation::getForSource(mem),MemoryLocation::getForDest(mem));
            out["static_alias_result"]=ar==AliasResult::NoAlias?"NoAlias":ar==AliasResult::MustAlias?"MustAlias":ar==AliasResult::PartialAlias?"PartialAlias":"MayAlias";
            out["alias_proof_scope"]="LLVM default AA on normalized IR; not observed runtime address/allocator regime";
          }outC.push_back(std::move(out));}++call;
      }
    }
  }
  if(site!=access->size() || call!=calls->size() || !wantA.empty() || !wantC.empty()){fail("count or requested-site mismatch");return 2;}
  json::Array rootRows;for(auto &[id,row]:roots.rows)rootRows.push_back(std::move(row));
  json::Object out{{"format","swdb.normalized-root-projection.v1"},{"date","2026-10-06 ET"},
    {"scope","read-only static projection; no addresses, runtime counts, timings or cost conclusions"},
    {"normalized_ir_sha256",hashFile(argv[1])},{"source_json_sha256",hashFile(argv[2])},
    {"data_layout",m->getDataLayoutStr()},{"enumerated_access_sites",int64_t(site)},{"enumerated_call_sites",int64_t(call)},
    {"all_source_json_sites_cross_checked",true},{"accesses",std::move(outA)},{"calls",std::move(outC)},{"roots",std::move(rootRows)}};
  std::error_code ec;raw_fd_ostream os(argv[3],ec);if(ec){fail("cannot create output.json");return 2;}os<<formatv("{0:2}",json::Value(std::move(out)))<<'\n';
  outs()<<"cross-checked "<<site<<" access sites and "<<call<<" call sites; projection saved\n";return 0;
}
