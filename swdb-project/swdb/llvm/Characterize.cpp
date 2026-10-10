// Source-normalized characterization and instrumentation. Updated: 2026-10-06 ET.
// LLVM 22 new-PM plugin; no timing model and no source-text parsing.
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/ADT/SmallPtrSet.h"
#include "llvm/ADT/StringExtras.h"
#include "llvm/Support/SHA256.h"
#include "llvm/Support/AtomicOrdering.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Plugins/PassPlugin.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/FormatVariadic.h"
#include <cctype>
#include <cstdlib>
#include <map>
#include <set>
using namespace llvm;

namespace {
std::string env(const char *name) { const char *v=std::getenv(name); return v ? v : ""; }
std::string scevText(const SCEV *s) { std::string text; raw_string_ostream os(text); s->print(os); return text; }
// Exact source-normalized primitive facts. Coarse update buckets remain unchanged;
// a store arithmetic producer alone never establishes a read-modify-write.
json::Object memoryPrimitive(Instruction &I, Type *T, const DataLayout &DL) {
  Type *element=T->getScalarType();
  std::string kind=element->isIntegerTy()?"integer":element->isFloatingPointTy()?"floating":
      element->isPointerTy()?"pointer":element->isAggregateType()?"aggregate":"unknown";
  json::Value bits=nullptr;
  if(element->isIntegerTy())bits=int64_t(element->getIntegerBitWidth());
  else if(element->isFloatingPointTy() || element->isPointerTy()) {
    auto width=DL.getTypeSizeInBits(element);
    if(!width.isScalable())bits=int64_t(width.getFixedValue());
  }
  AtomicOrdering ordering=AtomicOrdering::NotAtomic;
  bool vol=false; json::Value failure=nullptr, weak=nullptr, update=nullptr;
  if(auto *load=dyn_cast<LoadInst>(&I)){ordering=load->getOrdering();vol=load->isVolatile();}
  if(auto *store=dyn_cast<StoreInst>(&I)) {
    ordering=store->getOrdering();vol=store->isVolatile();
    if(auto *binary=dyn_cast<BinaryOperator>(store->getValueOperand()))update=binary->getOpcodeName();
  }
  if(auto *rmw=dyn_cast<AtomicRMWInst>(&I)) {
    ordering=rmw->getOrdering();vol=rmw->isVolatile();
    update=AtomicRMWInst::getOperationName(rmw->getOperation()).str();
  }
  if(auto *cas=dyn_cast<AtomicCmpXchgInst>(&I)) {
    ordering=cas->getSuccessOrdering();failure=toIRString(cas->getFailureOrdering());
    vol=cas->isVolatile();weak=cas->isWeak();
  }
  return json::Object{{"format","swdb.source-memory-primitive.v1"},{"opcode",I.getOpcodeName()},
    {"value_kind",kind},{"element_bits",std::move(bits)},{"vector",T->isVectorTy()},
    {"atomic_ordering",toIRString(ordering)},{"failure_ordering",std::move(failure)},
    {"volatile",vol},{"weak",std::move(weak)},{"update_opcode",std::move(update)}};
}

// Follow SSA dependencies, never source spelling. Cycles terminate at the visited set.
bool depends(Value *v, Value *wanted, SmallPtrSetImpl<Value *> &seen) {
  if(v==wanted)return true;
  if(!seen.insert(v).second)return false;
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(depends(op,wanted,seen))return true;
  return false;
}
bool hasLoad(Value *v, SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(isa<LoadInst>(v))return true;
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(hasLoad(op,seen))return true;
  return false;
}
bool hasLoad(Value *v) { SmallPtrSet<Value *,32> seen;return hasLoad(v,seen); }
bool recurrenceLoad(Value *v,Value *phi,SmallPtrSetImpl<Value *> &seen) {
  if(v==phi || !seen.insert(v).second)return false;
  if(auto *load=dyn_cast<LoadInst>(v)) { SmallPtrSet<Value *,32> path;if(depends(load->getPointerOperand(),phi,path))return true; }
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(recurrenceLoad(op,phi,seen))return true;
  return false;
}
bool chase(Value *v, Loop *L, SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(auto *P=dyn_cast<PHINode>(v);P && P->getParent()==L->getHeader()) {
    for(unsigned i=0;i<P->getNumIncomingValues();++i)if(L->contains(P->getIncomingBlock(i))) {
      Value *next=P->getIncomingValue(i);SmallPtrSet<Value *,32> path;
      if(recurrenceLoad(next,P,path))return true;
    }
  }
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(chase(op,L,seen))return true;
  return false;
}
bool merged(Value *v, Loop *L, SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(auto *S=dyn_cast<SelectInst>(v);S && S->getType()->isPointerTy() && hasLoad(S->getCondition()))return true;
  if(auto *P=dyn_cast<PHINode>(v);P && P->getType()->isPointerTy() && P->getParent()!=L->getHeader()
      && P->getNumIncomingValues()>1 && P->getIncomingValue(0)!=P->getIncomingValue(1))return true;
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(merged(op,L,seen))return true;
  return false;
}
bool loadedOuterBoundary(Value *v,Loop *outer,ScalarEvolution &SE,SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(auto *load=dyn_cast<LoadInst>(v);load && outer && !SE.isLoopInvariant(SE.getSCEV(load->getPointerOperand()),outer))return true;
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(loadedOuterBoundary(op,outer,SE,seen))return true;
  return false;
}
bool loadedIndex(Value *v,Loop *L,ScalarEvolution &SE,SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(auto *gep=dyn_cast<GetElementPtrInst>(v))for(Value *index:gep->indices())
    if(hasLoad(index) && !SE.isLoopInvariant(SE.getSCEV(index),L))return true;
  if(auto *load=dyn_cast<LoadInst>(v);load && load->getType()->isPointerTy()
      && !SE.isLoopInvariant(SE.getSCEV(load->getPointerOperand()),L))return true;
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(loadedIndex(op,L,SE,seen))return true;
  return false;
}
bool rangedStart(Value *v, Loop *L, ScalarEvolution &SE, SmallPtrSetImpl<Value *> &seen) {
  if(!seen.insert(v).second)return false;
  if(auto *P=dyn_cast<PHINode>(v);P && P->getParent()==L->getHeader()) {
    for(unsigned i=0;i<P->getNumIncomingValues();++i)if(!L->contains(P->getIncomingBlock(i))) {
      Value *start=P->getIncomingValue(i);SmallPtrSet<Value *,32> path;
      if(P->getType()->isIntegerTy()?hasLoad(start):loadedOuterBoundary(start,L->getParentLoop(),SE,path))return true;
    }
  }
  if(auto *I=dyn_cast<Instruction>(v))for(Value *op:I->operands())if(rangedStart(op,L,SE,seen))return true;
  return false;
}
std::string classify(Value *ptr, Loop *L, ScalarEvolution &SE, json::Value &stride) {
  if(!L)return "unknown";
  SmallPtrSet<Value *,32> seen;
  if(chase(ptr,L,seen))return "pointer_chase";
  seen.clear();if(merged(ptr,L,seen))return "data_dependent_merge";
  const SCEV *S=SE.getSCEV(ptr);
  if(auto *AR=dyn_cast<SCEVAddRecExpr>(S);AR && AR->getLoop()==L && AR->isAffine()) {
    if(auto *step=dyn_cast<SCEVConstant>(AR->getStepRecurrence(SE))) {
      stride=step->getAPInt().getSExtValue();
      seen.clear();return rangedStart(ptr,L,SE,seen)?"ranged_indirect":"stream";
    }
  }
  if(SE.isLoopInvariant(S,L)){stride=0;return "constant";}
  // A varying loaded index is evidence for an indirect address; an opaque call is not.
  seen.clear();if(loadedIndex(ptr,L,SE,seen))return "single_valued_indirect";
  return "unknown";
}
std::string path(const DIFile *file) {
  if(!file)return "";SmallString<256> p(file->getFilename());
  if(!sys::path::is_absolute(p)){SmallString<256> base(file->getDirectory());sys::path::append(base,p);p=base;}
  sys::path::remove_dots(p,true);return p.str().str();
}
std::string qualified(StringRef text) {
  uint64_t hash=1469598103934665603ULL;for(unsigned char c:text){hash^=c;hash*=1099511628211ULL;}
  return std::to_string(hash);
}
std::string owner(Function &F,Module &M) {
  StringRef symbol=F.getName();size_t pos=symbol.find(".omp_outlined");
  if(pos!=StringRef::npos)if(auto *base=M.getFunction(symbol.substr(0,pos)))if(auto *sp=base->getSubprogram())return sp->getName().str();
  return F.getSubprogram()?F.getSubprogram()->getName().str():symbol.str();
}
std::string safe(std::string s){for(char &c:s)if(!std::isalnum(static_cast<unsigned char>(c)) && c!='_' && c!='.' && c!='-' && c!='/')c='_';return s;}
// Exact standard Itanium allocation ABIs. Placement allocation/deallocation does
// not obtain/release backing storage and must not alter its lifetime namespace.
bool heapAllocation(StringRef name) {
  for(auto supported:{"malloc","calloc","realloc","_Znwm","_Znam",
      "_ZnwmRKSt9nothrow_t","_ZnamRKSt9nothrow_t","_ZnwmSt11align_val_t","_ZnamSt11align_val_t",
      "_ZnwmSt11align_val_tRKSt9nothrow_t","_ZnamSt11align_val_tRKSt9nothrow_t"})
    if(name==supported)return true;
  return false;
}
bool heapRelease(StringRef name) {
  for(auto supported:{"free","_ZdlPv","_ZdaPv","_ZdlPvm","_ZdaPvm",
      "_ZdlPvRKSt9nothrow_t","_ZdaPvRKSt9nothrow_t","_ZdlPvSt11align_val_t","_ZdaPvSt11align_val_t",
      "_ZdlPvmSt11align_val_t","_ZdaPvmSt11align_val_t",
      "_ZdlPvSt11align_val_tRKSt9nothrow_t","_ZdaPvSt11align_val_tRKSt9nothrow_t"})
    if(name==supported)return true;
  return false;
}
struct Region { std::string id, function; unsigned line=0; Loop *loop=nullptr; bool mapped=false; std::string file,symbol; bool host_selected=true; };
struct Access { Instruction *inst; Value *ptr; unsigned site, region, bytes, lanes; bool write; unsigned update; };
struct Op { Instruction *inst; unsigned region, category, amount; };
struct Call { Instruction *inst; unsigned site; Value *size=nullptr; bool known=false; unsigned region=0; Value *factor=nullptr,*pointer=nullptr; unsigned action=0; bool semantic_body=false; };

#include "SemanticCommands.hpp"
#include "ObjectScopes.hpp"

class BindROI : public PassInfoMixin<BindROI> {
public:
PreservedAnalyses run(Module &M,ModuleAnalysisManager &) {
  LLVMContext &C=M.getContext();auto *u64=Type::getInt64Ty(C);
  auto begin=M.getOrInsertFunction("__swdb_begin",Type::getVoidTy(C));
  auto end=M.getOrInsertFunction("__swdb_end",Type::getVoidTy(C));
  auto source=M.getOrInsertFunction("__swdb_source",Type::getVoidTy(C),u64);
  unsigned matched=0;std::vector<CallBase *> sites;std::vector<ReturnInst *> picks;
  for(Function &F:M)if(auto *SP=F.getSubprogram()) {
    for(Instruction &I:instructions(F)) {
      if(SP->getName().starts_with("BenchmarkKernel"))if(auto *CB=dyn_cast<CallBase>(&I))
        if(CB->getCalledFunction() && !CB->getCalledFunction()->isIntrinsic() && I.getDebugLoc() && path(I.getDebugLoc()->getScope()->getFile())==env("SWDB_ROI_PATH")
          && I.getDebugLoc().getLine()==unsigned(std::stoul(env("SWDB_ROI_LINE"))))sites.push_back(CB);
      if(SP->getName()=="PickNext")if(auto *R=dyn_cast<ReturnInst>(&I);R && R->getReturnValue())picks.push_back(R);
    }
  }
  for(auto *CB:sites) {
    IRBuilder<> B(CB);B.CreateCall(begin);++matched;
    if(auto *invoke=dyn_cast<InvokeInst>(CB)){IRBuilder<> after(&*invoke->getNormalDest()->getFirstInsertionPt());after.CreateCall(end);}
    else {IRBuilder<> after(CB->getNextNode());after.CreateCall(end);}
  }
  if(matched!=1)report_fatal_error("registered timed kernel call must resolve to exactly one LLVM call site");
  for(auto *R:picks){IRBuilder<> B(R);B.CreateCall(source,{B.CreateSExtOrTrunc(R->getReturnValue(),u64)});}
  return PreservedAnalyses::none();
}
};

class Characterize : public PassInfoMixin<Characterize> {
public:
PreservedAnalyses run(Module &M, ModuleAnalysisManager &MAM) {
  auto &FAM=MAM.getResult<FunctionAnalysisManagerModuleProxy>(M).getManager();
  json::Array mapRows;
  if (!env("SWDB_REGION_MAP").empty()) {
    auto file=MemoryBuffer::getFile(env("SWDB_REGION_MAP"));
    if (!file) report_fatal_error("cannot read region map");
    auto parsed=json::parse((*file)->getBuffer());
    if (!parsed) report_fatal_error("invalid region map JSON");
    auto *obj=parsed->getAsObject();
    if (!obj || !obj->getArray("regions")) report_fatal_error("region map needs regions array");
    mapRows=*obj->getArray("regions");
  }
  std::vector<Region> regions;
  std::vector<Access> accesses;
  std::vector<Op> operations;
  std::vector<Call> calls;
  json::Array accessRows, loopRows, callRows;
  std::vector<std::pair<CallBase *,unsigned>> semanticSites;
  bool semantic=!env("SWDB_FUNCTIONAL_OBSERVATION").empty();
  CommandAccessRoles sourceRoles(semantic);
  std::map<Loop *, unsigned> loopIDs;
  const DataLayout &DL=M.getDataLayout();
  unsigned site=0, callSite=0;
  for (Function &F:M) {
    if (F.isDeclaration() || F.getName().starts_with("__swdb_")) continue;
    auto *SP=F.getSubprogram();
    std::string name=owner(F,M);
    auto selected=env("SWDB_COUNT_FUNCTION");
    bool hostSelected=selected.empty() || selected==name || selected==F.getName();
    if (!hostSelected && !semantic) continue;
    if (!SP) continue; // never silently attribute runtime/compiler helpers
    unsigned serial=regions.size();
    regions.push_back({safe(env("SWDB_SUBJECT"))+"/serial."+qualified(F.getName()),name,SP->getLine(),nullptr,true,path(SP->getFile()),F.getName().str()});
    regions.back().host_selected=hostSelected;
    auto &LI=FAM.getResult<LoopAnalysis>(F);
    auto &SE=FAM.getResult<ScalarEvolutionAnalysis>(F);
    std::vector<Loop *> loops;
    for (Loop *L:LI) { loops.push_back(L); }
    for (size_t i=0;i<loops.size();++i) {
      Loop *L=loops[i]; for (Loop *sub:L->getSubLoops()) loops.push_back(sub);
      unsigned line=L->getStartLoc() ? L->getStartLoc().getLine() : 0;
      std::string loopPath=L->getStartLoc()?path(L->getStartLoc()->getScope()->getFile()):path(SP->getFile());
      std::string id="unmapped."+safe(env("SWDB_SUBJECT"))+"."+safe(name)+"."+std::to_string(line)+"."+std::to_string(i)+"."+qualified(F.getName());
      int64_t bestWidth=INT64_MAX;
      bool mapped=false;
      for (auto &row:mapRows) {
        auto *r=row.getAsObject(); if (!r) report_fatal_error("region entry is not an object");
        auto fn=r->getString("function"); auto lo=r->getInteger("line_start"), hi=r->getInteger("line_end");
        auto mappedPath=r->getString("path");
        std::string locationName=L->getStartLoc()?L->getStartLoc()->getScope()->getSubprogram()->getName().str():name;
        if (fn && (*fn==name || *fn==F.getName() || *fn==locationName) && (!mappedPath || *mappedPath==loopPath) && lo && hi && line>=*lo && line<=*hi) {
          auto width=*hi-*lo;
          if(width>bestWidth)continue;
          if(mapped && width==bestWidth)report_fatal_error("loop maps to ambiguous source regions");
          bestWidth=width;
          if (!r->getString("id")) report_fatal_error("mapped region lacks id");
          id=r->getString("id")->str(); mapped=true;
        }
      }
      unsigned rid=regions.size(); regions.push_back({id,name,line,L,mapped,loopPath,F.getName().str()}); loopIDs[L]=rid;regions.back().host_selected=hostSelected;
      const SCEV *trip=SE.getBackedgeTakenCount(L);
      json::Object row{{"region",id},{"function",name},{"line",int64_t(line)},
        {"path",loopPath},{"llvm_function",F.getName().str()},{"depth",int64_t(L->getLoopDepth())},{"mapped",mapped},
        {"backedge_taken_count",scevText(trip)},
        {"static_header_trip_count",nullptr}};
      if (auto *C=dyn_cast<SCEVConstant>(trip)) row["static_header_trip_count"]=int64_t(C->getAPInt().getZExtValue()+1);
      loopRows.push_back(std::move(row));
    }
    for (Instruction &I:instructions(F)) {
      if(I.getMetadata("swdb.observer")){
        if(auto *CB=dyn_cast<CallBase>(&I))if(CB->getCalledFunction() && CB->getCalledFunction()->getName()=="__swdb_command_enter")semanticSites.emplace_back(CB,LI.getLoopFor(I.getParent())?loopIDs.at(LI.getLoopFor(I.getParent())):serial);
        continue;
      }
      if (isa<DbgInfoIntrinsic>(&I) || isa<PHINode>(&I) || isa<AllocaInst>(&I)) continue;
      unsigned rid=LI.getLoopFor(I.getParent()) ? loopIDs.at(LI.getLoopFor(I.getParent())) : serial;
      Value *ptr=nullptr; Type *T=nullptr; bool write=false;
      if (auto *load=dyn_cast<LoadInst>(&I)) { ptr=load->getPointerOperand(); T=load->getType(); }
      if (auto *store=dyn_cast<StoreInst>(&I)) { ptr=store->getPointerOperand(); T=store->getValueOperand()->getType(); write=true; }
      std::string update=write?"write":"read";bool readWrite=false;
      if(auto *rmw=dyn_cast<AtomicRMWInst>(&I)){ptr=rmw->getPointerOperand();T=rmw->getValOperand()->getType();write=true;readWrite=true;update="arbitrary";
        switch(rmw->getOperation()) {
          case AtomicRMWInst::Add:case AtomicRMWInst::Sub:case AtomicRMWInst::FAdd:case AtomicRMWInst::FSub:update="add-update";break;
          case AtomicRMWInst::Min:case AtomicRMWInst::Max:case AtomicRMWInst::UMin:case AtomicRMWInst::UMax:case AtomicRMWInst::FMin:case AtomicRMWInst::FMax:update="min-max-update";break;
          case AtomicRMWInst::Xchg:update="write";break;
          default:break;
        }}
      if(auto *cas=dyn_cast<AtomicCmpXchgInst>(&I)){ptr=cas->getPointerOperand();T=cas->getCompareOperand()->getType();write=true;readWrite=true;update="compare-and-swap";}
      if (ptr) {
        auto size=DL.getTypeStoreSize(T); unsigned lanes=1;
        if (auto *VT=dyn_cast<FixedVectorType>(T)) lanes=VT->getNumElements();
        if (size.isScalable()) report_fatal_error("scalable accesses need a source multiplicity model");
        unsigned bytes=size.getFixedValue()/lanes;
        const SCEV *S=SE.getSCEV(ptr); std::string shape="unknown"; json::Value stride=nullptr;
        Loop *L=LI.getLoopFor(I.getParent());
        shape=classify(ptr,L,SE,stride);
        unsigned line=I.getDebugLoc() ? I.getDebugLoc().getLine() : 0;
        unsigned col=I.getDebugLoc() ? I.getDebugLoc().getCol() : 0;
        json::Object row{{"site",int64_t(site)},{"region",regions[rid].id},{"region_index",int64_t(rid)},
          {"function",name},{"path",path(I.getDebugLoc()?I.getDebugLoc()->getScope()->getFile():SP->getFile())},{"llvm_function",F.getName().str()},{"line",int64_t(line)},{"column",int64_t(col)},
          {"update_kind",update},{"read_write",readWrite},{"primitive_semantics",memoryPrimitive(I,T,DL)},{"address_shape",shape},
          {"stride_bytes",std::move(stride)},{"element_bytes",int64_t(bytes)},
          {"ir_lanes",int64_t(lanes)},{"address_expression",scevText(S)}};
        accessRows.push_back(std::move(row)); accesses.push_back({&I,ptr,site++,rid,bytes,lanes,write,update=="read"?0u:update=="write" && !readWrite?1u:update=="add-update"?2u:update=="compare-and-swap"?3u:update=="min-max-update"?4u:5u});
      }
      unsigned category=99, amount=1, lanes=1;
      if (auto *VT=dyn_cast<FixedVectorType>(I.getType())) lanes=VT->getNumElements();
      if (I.isBinaryOp() || isa<CmpInst>(&I)) category=I.getType()->isFPOrFPVectorTy() || isa<FCmpInst>(&I) ? 1 : 0;
      if (isa<BranchInst>(&I) || isa<SwitchInst>(&I)) category=2;
      if (isa<AtomicRMWInst>(&I) || isa<AtomicCmpXchgInst>(&I)) category=3;
      if (auto *load=dyn_cast<LoadInst>(&I); load && load->isAtomic()) category=3;
      if (auto *store=dyn_cast<StoreInst>(&I); store && store->isAtomic()) category=3;
      if (auto *CB=dyn_cast<CallBase>(&I)) {
        if (auto *callee=CB->getCalledFunction()) {
          auto called=callee->getName();
          if(called=="__swdb_command_enter")semanticSites.emplace_back(CB,rid);
          if (called.starts_with("llvm.fmuladd") || called.starts_with("llvm.fma")) { category=1; amount=2; }
          else if (!called.starts_with("__swdb_") && !called.starts_with("llvm.lifetime.") && !called.starts_with("llvm.dbg.") && called!="llvm.assume") {
            bool hint=false,checked=false;std::string reference;
            switch(callee->getIntrinsicID()) {
              case Intrinsic::expect:case Intrinsic::expect_with_probability:
                hint=true;reference="https://llvm.org/docs/LangRef.html#llvm-expect-intrinsic";break;
              case Intrinsic::experimental_noalias_scope_decl:
                hint=true;reference="https://llvm.org/docs/LangRef.html#llvm-experimental-noalias-scope-decl-intrinsic";break;
              case Intrinsic::sadd_with_overflow:case Intrinsic::uadd_with_overflow:
              case Intrinsic::ssub_with_overflow:case Intrinsic::usub_with_overflow:
              case Intrinsic::smul_with_overflow:case Intrinsic::umul_with_overflow:
                checked=true;category=0;amount=2; // arithmetic result plus overflow predicate, not two machine instructions
                if(auto *VT=dyn_cast<FixedVectorType>(CB->getArgOperand(0)->getType()))lanes=VT->getNumElements();
                if(isa<ScalableVectorType>(CB->getArgOperand(0)->getType()))report_fatal_error("scalable checked arithmetic needs a source multiplicity model");
                reference="https://llvm.org/docs/LangRef.html#arithmetic-with-overflow-intrinsics";break;
              default:break;
            }
            bool body=!callee->isDeclaration() && callee->getSubprogram() && (selected.empty() || selected==owner(*callee,M) || selected==called);
            Value *size=nullptr;std::string event=hint?"compiler_annotation":checked?"compiler_arithmetic":"external_call";
            if(auto *mem=dyn_cast<MemIntrinsic>(CB)){size=mem->getLength();event="bulk_memory";}
            else if((heapAllocation(called) && called!="calloc" && called!="realloc") && CB->arg_size()){size=CB->getArgOperand(0);event="allocation";}
            else if(called.starts_with("__kmpc_") || called.starts_with("GOMP_"))event="openmp";
            json::Object callRow{{"site",int64_t(callSite)},{"region",regions[rid].id},{"name",called.str()},
              {"line",int64_t(I.getDebugLoc() ? I.getDebugLoc().getLine() : 0)},{"event",event},{"body_counted",body},
              {"cost_accounting",hint?"no_runtime_operation":checked?"source_normalized_operations":body?"counted_body":"opaque_callee"}};
            if(hint || checked) {
              callRow["semantics_reference"]=reference;
              callRow["operations_per_execution"]=int64_t(checked?amount*lanes:0);
              callRow["operation_class"]=checked?json::Value("integer"):json::Value(nullptr);
              callRow["semantics_note"]=hint?"Optimizer hint or alias-scope metadata; no runtime operation is added.":"One logical arithmetic operation and one overflow predicate per lane; machine lowering cost is not inferred.";
            }
            callRows.push_back(std::move(callRow));
            Call observed{&I,callSite++,size,size!=nullptr,rid};
            observed.semantic_body=hint || checked || (!callee->isDeclaration() && callee->getSubprogram());
            if(heapRelease(called)){observed.pointer=CB->getArgOperand(0);observed.action=2;}
            else if(heapAllocation(called)){
              observed.action=called=="realloc"?3:1;
              if(called=="calloc"){observed.size=CB->getArgOperand(0);observed.factor=CB->getArgOperand(1);observed.known=true;}
              if(called=="realloc"){observed.size=CB->getArgOperand(1);observed.pointer=CB->getArgOperand(0);observed.known=true;}
            }
            calls.push_back(observed);
          }
        } else {
          callRows.push_back(json::Object{{"site",int64_t(callSite)},{"region",regions[rid].id},{"name","indirect-call"},{"line",0}});
          calls.push_back({&I,callSite++,nullptr,false,rid});
        }
      }
      if (category!=99) operations.push_back({&I,rid,category,amount*lanes});
    }
  }
  json::Array regionRows;
  for (unsigned i=0;i<regions.size();++i) {
    auto &r=regions[i]; regionRows.push_back(json::Object{{"index",int64_t(i)},{"id",r.id},
      {"function",r.function},{"path",r.file},{"llvm_function",r.symbol},{"line",int64_t(r.line)},{"is_loop",bool(r.loop)},{"mapped",r.mapped}});
  }
  std::map<std::string,unsigned> canonical;
  for(unsigned i=0;i<regions.size();++i)canonical.emplace(regions[i].id,i);
  json::Array semanticRows;std::set<std::pair<unsigned,unsigned>> semanticSeen;
  for(auto entry:semanticSites){auto *call=entry.first;unsigned rid=canonical.at(regions[entry.second].id);
    unsigned site=cast<ConstantInt>(call->getArgOperand(1))->getZExtValue();
    call->setArgOperand(2,ConstantInt::get(Type::getInt32Ty(M.getContext()),rid));
    if(semanticSeen.emplace(site,rid).second)semanticRows.push_back(json::Object{{"site",int64_t(site)},{"region",regions[rid].id},{"region_index",int64_t(rid)},
      {"descriptor",int64_t(cast<ConstantInt>(call->getArgOperand(0))->getZExtValue())}});
  }
  json::Object result{{"semantic_sites",std::move(semanticRows)},{"regions",std::move(regionRows)},{"loops",std::move(loopRows)},
    {"accesses",std::move(accessRows)},{"unmodeled_calls",std::move(callRows)}};
  auto out=env("SWDB_ANALYSIS_OUTPUT"); if (out.empty()) report_fatal_error("SWDB_ANALYSIS_OUTPUT missing");
  std::error_code ec; raw_fd_ostream OS(out,ec); if (ec) report_fatal_error("cannot write static analysis");
  OS<<formatv("{0:2}",json::Value(std::move(result)))<<"\n";
  if (env("SWDB_INSTRUMENT")!="1") return PreservedAnalyses::all();
  LLVMContext &C=M.getContext(); auto *u64=Type::getInt64Ty(C), *u32=Type::getInt32Ty(C);
  auto tripFn=semantic?M.getOrInsertFunction("__swdb_domain_trip",Type::getVoidTy(C),u32,u64,u32):M.getOrInsertFunction("__swdb_trip",Type::getVoidTy(C),u32,u64);
  auto opFn=semantic?M.getOrInsertFunction("__swdb_domain_op",Type::getVoidTy(C),u32,u32,u64,u32):M.getOrInsertFunction("__swdb_op",Type::getVoidTy(C),u32,u32,u64);
  auto callFn=semantic?M.getOrInsertFunction("__swdb_domain_call",Type::getVoidTy(C),u32,u64,u32,u32,u64,u32,u32,u32,u64,u64):M.getOrInsertFunction("__swdb_call_v2",Type::getVoidTy(C),u32,u64,u32,u32,u64,u32);
  auto accessFn=semantic?M.getOrInsertFunction("__swdb_domain_access",Type::getVoidTy(C),u32,u32,u64,u64,u64,u32,u32,u64,u64):M.getOrInsertFunction("__swdb_access_v2",Type::getVoidTy(C),u32,u32,u64,u64,u64,u32);
  instrumentObjectScopes(M);
  for (unsigned i=0;i<regions.size();++i) if (auto *L=regions[i].loop) {
    auto *term=L->getHeader()->getTerminator(); IRBuilder<> B(term); Value *n=B.getInt64(1);
    if (auto *br=dyn_cast<BranchInst>(term); br && br->isConditional()) {
      bool a=L->contains(br->getSuccessor(0)), b=L->contains(br->getSuccessor(1));
      if (a!=b) n=B.CreateZExt(a ? br->getCondition() : B.CreateNot(br->getCondition()),u64);
    }
    SmallVector<Value *,3> values{B.getInt32(i),n};if(semantic)values.push_back(B.getInt32(regions[i].host_selected));B.CreateCall(tripFn,values);
  }
  for (auto &op:operations) { IRBuilder<> B(op.inst); SmallVector<Value *,4> values{B.getInt32(op.region),B.getInt32(op.category),B.getInt64(op.amount)};if(semantic)values.push_back(B.getInt32(regions[op.region].host_selected));B.CreateCall(opFn,values); }
  for(auto &call:calls){
    IRBuilder<> B(call.inst);Value *size=call.size?B.CreateZExtOrTrunc(call.size,u64):B.getInt64(0),*known=B.getInt32(call.known?1:0);
    if(call.factor){
      auto mul=M.getOrInsertFunction("llvm.umul.with.overflow.i64",StructType::get(u64,B.getInt1Ty()),u64,u64);
      auto product=B.CreateCall(mul,{size,B.CreateZExtOrTrunc(call.factor,u64)});
      size=B.CreateExtractValue(product,0);known=B.CreateZExt(B.CreateNot(B.CreateExtractValue(product,1)),u32);
    }
    SmallVector<Value *,8> values{B.getInt32(call.site),size,known,B.getInt32(call.region),
        call.pointer?B.CreatePtrToInt(call.pointer,u64):B.getInt64(0),B.getInt32(call.action)};
    if(semantic){values.push_back(B.getInt32(regions[call.region].host_selected));values.push_back(B.getInt32(call.semantic_body));auto roles=sourceRoles.get(*call.inst);values.push_back(B.getInt64(roles.first));values.push_back(B.getInt64(roles.second));}B.CreateCall(callFn,values);
  }
  for (auto &a:accesses) { IRBuilder<> B(a.inst);SmallVector<Value *,7> values{B.getInt32(a.site),B.getInt32(canonical.at(regions[a.region].id)),B.CreatePtrToInt(a.ptr,u64),B.getInt64(a.lanes),B.getInt64(a.bytes),B.getInt32(a.update)};if(semantic){values.push_back(B.getInt32(regions[a.region].host_selected));auto roles=sourceRoles.get(*a.inst);values.push_back(B.getInt64(roles.first));values.push_back(B.getInt64(roles.second));}B.CreateCall(accessFn,values); }
  // Object metadata is process-wide even when a source function/ROI is selected.
  auto allocFn=M.getOrInsertFunction("__swdb_allocate",Type::getVoidTy(C),u64,u64,u32);
  auto freeFn=M.getOrInsertFunction("__swdb_release",Type::getVoidTy(C),u64);
  auto reallocFn=M.getOrInsertFunction("__swdb_reallocate",Type::getVoidTy(C),u64,u64,u64,u32);
  std::vector<CallBase *> allocationCalls;
  for(Function &F:M)if(!F.isDeclaration() && !F.getName().starts_with("__swdb_"))
    for(Instruction &I:instructions(F))if(auto *call=dyn_cast<CallBase>(&I))if(auto *callee=call->getCalledFunction()) {
      auto name=callee->getName();
      if(heapAllocation(name) || heapRelease(name))allocationCalls.push_back(call);
    }
  for(auto *call:allocationCalls){
    auto name=call->getCalledFunction()->getName();
    if(heapRelease(name)) {
      IRBuilder<> B(call);B.CreateCall(freeFn,{B.CreatePtrToInt(call->getArgOperand(0),u64)});continue;
    }
    if(!call->getType()->isPointerTy() || (isa<CallInst>(call) && cast<CallInst>(call)->isMustTailCall()))continue;
    Instruction *after=nullptr;
    if(auto *invoke=dyn_cast<InvokeInst>(call))after=&*SplitEdge(invoke->getParent(),invoke->getNormalDest())->getFirstInsertionPt();
    else after=call->getNextNode();
    IRBuilder<> B(after);Value *size=nullptr,*known=B.getInt32(1);
    if(name=="calloc") {
      auto mul=M.getOrInsertFunction("llvm.umul.with.overflow.i64",StructType::get(u64,B.getInt1Ty()),u64,u64);
      auto product=B.CreateCall(mul,{B.CreateZExtOrTrunc(call->getArgOperand(0),u64),B.CreateZExtOrTrunc(call->getArgOperand(1),u64)});
      size=B.CreateExtractValue(product,0);known=B.CreateZExt(B.CreateNot(B.CreateExtractValue(product,1)),u32);
    } else size=B.CreateZExtOrTrunc(call->getArgOperand(name=="realloc"?1:0),u64);
    Value *address=B.CreatePtrToInt(call,u64);
    if(name=="realloc")B.CreateCall(reallocFn,{B.CreatePtrToInt(call->getArgOperand(0),u64),address,size,known});
    else B.CreateCall(allocFn,{address,size,known});
  }
  return PreservedAnalyses::none();
}
};
}
extern "C" LLVM_ATTRIBUTE_WEAK PassPluginLibraryInfo llvmGetPassPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION,"SWDBCharacterize","1.0",[](PassBuilder &PB) {
    PB.registerPipelineParsingCallback([](StringRef name, ModulePassManager &MPM, ArrayRef<PassBuilder::PipelineElement>) {
      if(name=="swdb-bind-commands"){MPM.addPass(BindCommands());return true;}
      if(name=="swdb-bind-roi"){MPM.addPass(BindROI());return true;}
      if (name!="swdb-characterize") return false; MPM.addPass(Characterize()); return true;
    });
  }};
}
