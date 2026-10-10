// Read-only OpenMP ABI projection. Updated: 2026-10-06 ET.
// Site enumeration/cross-check follows the verified normalized-root projector
// (a9dbe11); no passes, addresses, pointee reads, runtime bodies or costs.
#include "llvm/ADT/StringExtras.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/Module.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/FormatVariadic.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/Path.h"
#include "llvm/Support/SHA256.h"
#include "llvm/Support/SourceMgr.h"
#include <set>
using namespace llvm;

static int fail(StringRef reason) { errs()<<"openmp-projector: "<<reason<<'\n';return 2; }
static std::string filePath(const DIFile *file) {
  if(!file)return "";
  SmallString<256> path(file->getFilename());
  if(!sys::path::is_absolute(path)) { SmallString<256> base(file->getDirectory());sys::path::append(base,path);path=base; }
  sys::path::remove_dots(path,true);return path.str().str();
}
static std::string hashFile(StringRef path) {
  auto buffer=MemoryBuffer::getFile(path);if(!buffer)return "";
  auto bytes=(*buffer)->getBuffer();auto hash=SHA256::hash(ArrayRef<uint8_t>(reinterpret_cast<const uint8_t*>(bytes.data()),bytes.size()));
  return toHex(ArrayRef<uint8_t>(hash),true);
}
static json::Object location(const Instruction &inst) {
  auto *debug=inst.getDebugLoc().get();
  return json::Object{{"path",filePath(debug?debug->getFile():inst.getFunction()->getSubprogram()->getFile())},
    {"line",int64_t(debug?debug->getLine():0)},{"column",int64_t(debug?debug->getColumn():0)}};
}
static json::Object operand(Value *value,unsigned index) {
  json::Object row{{"index",int64_t(index)},{"bits",nullptr},{"signed_decimal",nullptr}};
  if(value->getType()->isPointerTy()) { row["kind"]="pointer";row["state"]="redacted";return row; }
  if(auto *type=dyn_cast<IntegerType>(value->getType())) {
    row["kind"]="integer";row["bits"]=int64_t(type->getBitWidth());
    if(auto *literal=dyn_cast<ConstantInt>(value)) {
      SmallString<128> decimal;literal->getValue().toString(decimal,10,true);
      row["state"]="constant";row["signed_decimal"]=decimal.str().str();
    } else row["state"]=isa<PoisonValue>(value)?"poison":isa<UndefValue>(value)?"undef":"dynamic";
  } else { row["kind"]="other";row["state"]="unsupported_type"; }
  return row;
}
static json::Object identFlags(const CallBase &call) {
  json::Object row{{"state","unknown"},{"bits",nullptr},{"signed_decimal",nullptr},
    {"basis","code_reading"},{"scope","immutable direct ident_t initializer only; no runtime pointee read"}};
  if(!call.arg_size() || !call.getArgOperand(0)->getType()->isPointerTy())return row;
  auto *global=dyn_cast<GlobalVariable>(call.getArgOperand(0)->stripPointerCasts());
  if(!global || !global->isConstant() || !global->hasDefinitiveInitializer() || global->isThreadLocal())return row;
  auto *type=dyn_cast<StructType>(global->getValueType());
  if(!type || type->getNumElements()!=5 || !type->getElementType(4)->isPointerTy())return row;
  for(unsigned i=0;i<4;++i)if(!type->getElementType(i)->isIntegerTy(32))return row;
  auto *flag=dyn_cast_or_null<ConstantInt>(global->getInitializer()->getAggregateElement(1u));
  if(!flag || !flag->getType()->isIntegerTy(32))return row;
  SmallString<32> decimal;flag->getValue().toString(decimal,10,true);
  row["state"]="constant";row["bits"]=32;row["signed_decimal"]=decimal.str().str();return row;
}

static std::string owner(Function &function,Module &module) {
  StringRef symbol=function.getName();size_t pos=symbol.find(".omp_outlined");
  if(pos!=StringRef::npos)if(auto *base=module.getFunction(symbol.substr(0,pos)))
    if(auto *debug=base->getSubprogram())return debug->getName().str();
  return function.getSubprogram()?function.getSubprogram()->getName().str():symbol.str();
}

int main(int argc,char **argv) {
  if(argc!=6 && argc!=7)return fail("usage: openmp-projector normalized.bc source.json output.json call-sites expected-ir-sha256 [exact-function]");
  StringRef selected=argc==7?argv[6]:"";
  const std::string irHash=hashFile(argv[1]),mapHash=hashFile(argv[2]);
  if(irHash.empty() || irHash!=argv[5])return fail("source_ir_sha256 mismatch");
  LLVMContext context;SMDiagnostic diagnostic;auto module=parseIRFile(argv[1],diagnostic,context);
  if(!module){diagnostic.print(argv[0],errs());return 2;}
  auto buffer=MemoryBuffer::getFile(argv[2]);if(!buffer)return fail("cannot read source.json");
  auto parsed=json::parse((*buffer)->getBuffer());if(!parsed)return fail("malformed source.json");
  auto *object=parsed->getAsObject();auto *accesses=object?object->getArray("accesses"):nullptr;
  auto *calls=object?object->getArray("unmodeled_calls"):nullptr;
  if(!accesses || !calls)return fail("source.json needs accesses and unmodeled_calls");
  std::set<unsigned> requested;SmallVector<StringRef> pieces;StringRef(argv[4]).split(pieces,',',-1,false);
  for(StringRef piece:pieces) { unsigned site;if(piece.getAsInteger(10,site) || !requested.insert(site).second)return fail("invalid or duplicate requested call site"); }
  unsigned site=0,callSite=0;json::Array projected;
  const auto &layout=module->getDataLayout();
  for(Function &function:*module) {
    if(function.isDeclaration() || function.getName().starts_with("__swdb_") || !function.getSubprogram())continue;
    if(!selected.empty() && selected!=owner(function,*module) && selected!=function.getName())continue;
    for(Instruction &inst:instructions(function)) {
      if(inst.getMetadata("swdb.observer") || isa<DbgInfoIntrinsic>(inst) || isa<PHINode>(inst) || isa<AllocaInst>(inst))continue;
      Value *pointer=nullptr;Type *type=nullptr;StringRef update="read";
      if(auto *load=dyn_cast<LoadInst>(&inst)){pointer=load->getPointerOperand();type=load->getType();}
      if(auto *store=dyn_cast<StoreInst>(&inst)){pointer=store->getPointerOperand();type=store->getValueOperand()->getType();update="write";}
      if(auto *atomic=dyn_cast<AtomicRMWInst>(&inst)) {
        pointer=atomic->getPointerOperand();type=atomic->getValOperand()->getType();update="arbitrary";
        switch(atomic->getOperation()) {
          case AtomicRMWInst::Add:case AtomicRMWInst::Sub:case AtomicRMWInst::FAdd:case AtomicRMWInst::FSub:update="add-update";break;
          case AtomicRMWInst::Max:case AtomicRMWInst::Min:case AtomicRMWInst::UMax:case AtomicRMWInst::UMin:case AtomicRMWInst::FMax:case AtomicRMWInst::FMin:update="min-max-update";break;
          case AtomicRMWInst::Xchg:update="write";break;
          default:break;
        }
      }
      if(auto *atomic=dyn_cast<AtomicCmpXchgInst>(&inst)){pointer=atomic->getPointerOperand();type=atomic->getCompareOperand()->getType();update="compare-and-swap";}
      if(pointer) {
        if(site>=accesses->size())return fail("too many enumerated access sites");
        auto *row=(*accesses)[site].getAsObject();
        unsigned lanes=isa<FixedVectorType>(type)?cast<FixedVectorType>(type)->getNumElements():1;
        auto width=layout.getTypeStoreSize(type);if(width.isScalable())return fail("unsupported scalable access");
        auto source=location(inst);
        if(!row || row->getInteger("site")!=int64_t(site) || row->getString("llvm_function")!=function.getName() ||
           row->getInteger("line")!=source.getInteger("line") || row->getInteger("column")!=source.getInteger("column") ||
           row->getString("path")!=source.getString("path") || row->getInteger("element_bytes")!=int64_t(width.getFixedValue()/lanes) ||
           row->getInteger("ir_lanes")!=int64_t(lanes) || row->getString("update_kind")!=update) {
          errs()<<"openmp-projector: access map mismatch at "<<site<<'\n';return 2;
        }
        ++site;
      }
      auto *call=dyn_cast<CallBase>(&inst);if(!call)continue;
      auto *callee=call->getCalledFunction();StringRef name=callee?callee->getName():"indirect-call";
      if(callee && (name.starts_with("llvm.fmuladd") || name.starts_with("llvm.fma") || name.starts_with("__swdb_") ||
         name.starts_with("llvm.lifetime.") || name.starts_with("llvm.dbg.") || name=="llvm.assume"))continue;
      if(callSite>=calls->size())return fail("too many enumerated call sites");
      auto *row=(*calls)[callSite].getAsObject();unsigned line=callee && inst.getDebugLoc()?inst.getDebugLoc().getLine():0;
      if(!row || row->getInteger("site")!=int64_t(callSite) || row->getString("name")!=name || row->getInteger("line")!=int64_t(line)) {
        errs()<<"openmp-projector: call map mismatch at "<<callSite<<'\n';return 2;
      }
      if(requested.erase(callSite)) {
        if(!callee || !name.starts_with("__kmpc_"))return fail("requested call is not a direct __kmpc_ site");
        json::Array operands;for(unsigned i=0;i<call->arg_size();++i)operands.push_back(operand(call->getArgOperand(i),i));
        projected.push_back(json::Object{{"site",int64_t(callSite)},{"name",name.str()},
          {"region",row->getString("region")?row->getString("region")->str():""},
          {"llvm_function",function.getName().str()},{"source_location",location(inst)},
          {"argument_count",int64_t(call->arg_size())},{"callee_parameter_count",int64_t(callee->arg_size())},
          {"callee_variadic",callee->isVarArg()},{"operands",std::move(operands)},{"ident_flags",identFlags(*call)}});
      }
      ++callSite;
    }
  }
  if(site!=accesses->size() || callSite!=calls->size() || !requested.empty())return fail("count or requested-site mismatch");
  if(irHash!=hashFile(argv[1]) || mapHash!=hashFile(argv[2]))return fail("projection input changed during reading");
  json::Object output{{"source_ir_sha256",irHash},{"source_json_sha256",mapHash},
    {"enumerated_access_sites",int64_t(site)},{"enumerated_call_sites",int64_t(callSite)},
    {"all_source_json_sites_cross_checked",true},{"calls",std::move(projected)}};
  std::error_code error;raw_fd_ostream stream(argv[3],error);if(error)return fail("cannot write projection");
  stream<<formatv("{0:2}",json::Value(std::move(output)))<<'\n';return 0;
}
