// Source-normalized characterization and instrumentation. Updated: 2026-10-06 ET.
// LLVM 22 new-PM plugin; no timing model and no source-text parsing.
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Analysis/ScalarEvolutionExpressions.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Plugins/PassPlugin.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/raw_ostream.h"
#include <cstdlib>
#include <map>
using namespace llvm;

namespace {
std::string env(const char *name) { const char *v=std::getenv(name); return v ? v : ""; }
std::string scevText(const SCEV *s) { std::string text; raw_string_ostream os(text); s->print(os); return text; }
struct Region { std::string id, function; unsigned line=0; Loop *loop=nullptr; bool mapped=false; };
struct Access { Instruction *inst; Value *ptr; unsigned site, region, bytes, lanes; bool write; };
struct Op { Instruction *inst; unsigned region, category, amount; };
struct Call { Instruction *inst; unsigned site; };

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
  std::map<Loop *, unsigned> loopIDs;
  const DataLayout &DL=M.getDataLayout();
  unsigned site=0, callSite=0;
  for (Function &F:M) {
    if (F.isDeclaration() || F.getName().starts_with("__swdb_")) continue;
    auto *SP=F.getSubprogram();
    std::string name=SP ? SP->getName().str() : F.getName().str();
    auto selected=env("SWDB_COUNT_FUNCTION");
    if (!selected.empty() && selected!=name && selected!=F.getName()) continue;
    if (!SP) continue; // never silently attribute runtime/compiler helpers
    unsigned serial=regions.size();
    regions.push_back({name+".serial",name,SP->getLine(),nullptr,true});
    auto &LI=FAM.getResult<LoopAnalysis>(F);
    auto &SE=FAM.getResult<ScalarEvolutionAnalysis>(F);
    std::vector<Loop *> loops;
    for (Loop *L:LI) { loops.push_back(L); }
    for (size_t i=0;i<loops.size();++i) {
      Loop *L=loops[i]; for (Loop *sub:L->getSubLoops()) loops.push_back(sub);
      unsigned line=L->getStartLoc() ? L->getStartLoc().getLine() : 0;
      std::string id="unmapped."+name+"."+std::to_string(line)+"."+std::to_string(i);
      bool mapped=false;
      for (auto &row:mapRows) {
        auto *r=row.getAsObject(); if (!r) report_fatal_error("region entry is not an object");
        auto fn=r->getString("function"); auto lo=r->getInteger("line_start"), hi=r->getInteger("line_end");
        if (fn && (*fn==name || *fn==F.getName()) && lo && hi && line>=*lo && line<=*hi) {
          if (mapped) report_fatal_error("loop maps to more than one region");
          if (!r->getString("id")) report_fatal_error("mapped region lacks id");
          id=r->getString("id")->str(); mapped=true;
        }
      }
      unsigned rid=regions.size(); regions.push_back({id,name,line,L,mapped}); loopIDs[L]=rid;
      const SCEV *trip=SE.getBackedgeTakenCount(L);
      json::Object row{{"region",id},{"function",name},{"line",int64_t(line)},
        {"depth",int64_t(L->getLoopDepth())},{"mapped",mapped},
        {"backedge_taken_count",scevText(trip)},
        {"static_header_trip_count",nullptr}};
      if (auto *C=dyn_cast<SCEVConstant>(trip)) row["static_header_trip_count"]=int64_t(C->getAPInt().getZExtValue()+1);
      loopRows.push_back(std::move(row));
    }
    for (Instruction &I:instructions(F)) {
      if (isa<DbgInfoIntrinsic>(&I) || isa<PHINode>(&I) || isa<AllocaInst>(&I)) continue;
      unsigned rid=LI.getLoopFor(I.getParent()) ? loopIDs.at(LI.getLoopFor(I.getParent())) : serial;
      Value *ptr=nullptr; Type *T=nullptr; bool write=false;
      if (auto *load=dyn_cast<LoadInst>(&I)) { ptr=load->getPointerOperand(); T=load->getType(); }
      if (auto *store=dyn_cast<StoreInst>(&I)) { ptr=store->getPointerOperand(); T=store->getValueOperand()->getType(); write=true; }
      if (ptr) {
        auto size=DL.getTypeStoreSize(T); unsigned lanes=1;
        if (auto *VT=dyn_cast<FixedVectorType>(T)) lanes=VT->getNumElements();
        if (size.isScalable()) report_fatal_error("scalable accesses need a source multiplicity model");
        unsigned bytes=size.getFixedValue()/lanes;
        const SCEV *S=SE.getSCEV(ptr); std::string shape="unknown"; json::Value stride=nullptr;
        Loop *L=LI.getLoopFor(I.getParent());
        if (L) {
          if (auto *AR=dyn_cast<SCEVAddRecExpr>(S); AR && AR->getLoop()==L && AR->isAffine()) {
            if (auto *step=dyn_cast<SCEVConstant>(AR->getStepRecurrence(SE))) {
              auto s=step->getAPInt().getSExtValue(); stride=s; shape="stream";
            }
          } else if (SE.isLoopInvariant(S,L)) { shape="constant"; stride=0; }
          else { shape="single-valued indirect"; }
        }
        unsigned line=I.getDebugLoc() ? I.getDebugLoc().getLine() : 0;
        unsigned col=I.getDebugLoc() ? I.getDebugLoc().getCol() : 0;
        json::Object row{{"site",int64_t(site)},{"region",regions[rid].id},{"region_index",int64_t(rid)},
          {"function",name},{"line",int64_t(line)},{"column",int64_t(col)},
          {"update_kind",write ? "write" : "read"},{"address_shape",shape},
          {"stride_bytes",std::move(stride)},{"element_bytes",int64_t(bytes)},
          {"ir_lanes",int64_t(lanes)},{"address_expression",scevText(S)}};
        accessRows.push_back(std::move(row)); accesses.push_back({&I,ptr,site++,rid,bytes,lanes,write});
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
          if (called.starts_with("llvm.fmuladd") || called.starts_with("llvm.fma")) { category=1; amount=2; }
          else if (!called.starts_with("llvm.lifetime.") && !called.starts_with("llvm.dbg.") && called!="llvm.assume") {
            callRows.push_back(json::Object{{"site",int64_t(callSite)},{"region",regions[rid].id},{"name",called.str()},
              {"line",int64_t(I.getDebugLoc() ? I.getDebugLoc().getLine() : 0)}});
            calls.push_back({&I,callSite++});
          }
        } else {
          callRows.push_back(json::Object{{"site",int64_t(callSite)},{"region",regions[rid].id},{"name","indirect-call"},{"line",0}});
          calls.push_back({&I,callSite++});
        }
      }
      if (category!=99) operations.push_back({&I,rid,category,amount*lanes});
    }
  }
  json::Array regionRows;
  for (unsigned i=0;i<regions.size();++i) {
    auto &r=regions[i]; regionRows.push_back(json::Object{{"index",int64_t(i)},{"id",r.id},
      {"function",r.function},{"line",int64_t(r.line)},{"is_loop",bool(r.loop)},{"mapped",r.mapped}});
  }
  json::Object result{{"regions",std::move(regionRows)},{"loops",std::move(loopRows)},
    {"accesses",std::move(accessRows)},{"unmodeled_calls",std::move(callRows)}};
  auto out=env("SWDB_ANALYSIS_OUTPUT"); if (out.empty()) report_fatal_error("SWDB_ANALYSIS_OUTPUT missing");
  std::error_code ec; raw_fd_ostream OS(out,ec); if (ec) report_fatal_error("cannot write static analysis");
  OS<<formatv("{0:2}",json::Value(std::move(result)))<<"\n";
  if (env("SWDB_INSTRUMENT")!="1") return PreservedAnalyses::all();
  LLVMContext &C=M.getContext(); auto *u64=Type::getInt64Ty(C), *u32=Type::getInt32Ty(C);
  auto tripFn=M.getOrInsertFunction("__swdb_trip",Type::getVoidTy(C),u32,u64);
  auto opFn=M.getOrInsertFunction("__swdb_op",Type::getVoidTy(C),u32,u32,u64);
  auto callFn=M.getOrInsertFunction("__swdb_call",Type::getVoidTy(C),u32);
  auto accessFn=M.getOrInsertFunction("__swdb_access",Type::getVoidTy(C),u32,u64,u64,u64);
  for (unsigned i=0;i<regions.size();++i) if (auto *L=regions[i].loop) {
    auto *term=L->getHeader()->getTerminator(); IRBuilder<> B(term); Value *n=B.getInt64(1);
    if (auto *br=dyn_cast<BranchInst>(term); br && br->isConditional()) {
      bool a=L->contains(br->getSuccessor(0)), b=L->contains(br->getSuccessor(1));
      if (a!=b) n=B.CreateZExt(a ? br->getCondition() : B.CreateNot(br->getCondition()),u64);
    }
    B.CreateCall(tripFn,{B.getInt32(i),n});
  }
  for (auto &op:operations) { IRBuilder<> B(op.inst); B.CreateCall(opFn,{B.getInt32(op.region),B.getInt32(op.category),B.getInt64(op.amount)}); }
  for (auto &call:calls) { IRBuilder<> B(call.inst); B.CreateCall(callFn,{B.getInt32(call.site)}); }
  for (auto &a:accesses) { IRBuilder<> B(a.inst); B.CreateCall(accessFn,{B.getInt32(a.site),B.CreatePtrToInt(a.ptr,u64),B.getInt64(a.lanes),B.getInt64(a.bytes)}); }
  return PreservedAnalyses::none();
}
};
}
extern "C" LLVM_ATTRIBUTE_WEAK PassPluginLibraryInfo llvmGetPassPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION,"SWDBCharacterize","1.0",[](PassBuilder &PB) {
    PB.registerPipelineParsingCallback([](StringRef name, ModulePassManager &MPM, ArrayRef<PassBuilder::PipelineElement>) {
      if (name!="swdb-characterize") return false; MPM.addPass(Characterize()); return true;
    });
  }};
}
