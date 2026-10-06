// Description-bound command boundaries before inlining. Created: 2026-10-06 ET.
// Bind instruction source roles after normalization, preserving the original
// inlined subprogram identity rather than attributing every guarded access.
class CommandAccessRoles {
  json::Array commands;
  std::map<const DISubprogram *,std::pair<uint64_t,uint64_t>> cache;
public:
  CommandAccessRoles(bool enabled){if(!enabled)return;
    auto file=MemoryBuffer::getFile(env("SWDB_FUNCTIONAL_OBSERVATION"));if(!file)report_fatal_error("cannot read command roles");
    auto parsed=json::parse((*file)->getBuffer());if(!parsed)report_fatal_error("invalid command roles");
    commands=*parsed->getAsObject()->getObject("functional_observation")->getArray("commands");
    if(commands.size()>64)report_fatal_error("semantic command masks exceed bounded descriptor count");
  }
  std::pair<uint64_t,uint64_t> get(Instruction &I){
    auto *SP=I.getDebugLoc()?I.getDebugLoc()->getScope()->getSubprogram():nullptr;
    if(!SP)return {0,0};auto known=cache.find(SP);if(known!=cache.end())return known->second;
    std::pair<uint64_t,uint64_t> roles{0,0};auto source=MemoryBuffer::getFile(path(SP->getFile()));
    if(source){auto text=(*source)->getBuffer();auto hash=toHex(SHA256::hash(ArrayRef<uint8_t>(reinterpret_cast<const uint8_t *>(text.data()),text.size())),true);
      for(unsigned i=0;i<commands.size();++i){auto *command=commands[i].getAsObject();unsigned role=0;
        for(auto field:{"target_access_sources","bookkeeping_access_sources"}){auto *entries=command->getArray(field);
          if(entries)for(auto &entry:*entries){auto *binding=entry.getAsObject();auto expected=binding->getString("source_sha256");auto symbol=binding->getString("symbol"),debug=binding->getString("debug_name");
            if(expected && *expected==hash && ((symbol && (*symbol==SP->getLinkageName() || (SP->getLinkageName().empty() && *symbol==SP->getName()))) || (debug && *debug==SP->getName())))
              (role?roles.second:roles.first)|=uint64_t(1)<<i;
          }++role;
        }
      }
    }if(roles.first&roles.second)report_fatal_error("ambiguous target/bookkeeping source roles");cache.emplace(SP,roles);return roles;
  }
};
class BindCommands : public PassInfoMixin<BindCommands> {
public:
PreservedAnalyses run(Module &M,ModuleAnalysisManager &){
  auto file=MemoryBuffer::getFile(env("SWDB_FUNCTIONAL_OBSERVATION"));
  if(!file)report_fatal_error("cannot read functional observation contract");
  auto parsed=json::parse((*file)->getBuffer());
  if(!parsed)report_fatal_error("invalid functional observation contract");
  auto *root=parsed->getAsObject();auto *observation=root?root->getObject("functional_observation"):nullptr;
  auto *commands=observation?observation->getArray("commands"):nullptr;
  if(!commands)report_fatal_error("functional observation lacks commands");
  std::set<Instruction *> original,sourceInvokes;for(Function &F:M)for(Instruction &I:instructions(F))original.insert(&I);
  struct Binding {unsigned descriptor,base,active;bool activeKnown,activeSigned,alias,memory;};
  std::map<Function *,Binding> bindings;
  for(Function &F:M){
    auto *SP=F.getSubprogram();if(!SP || F.isDeclaration())continue;
    auto source=MemoryBuffer::getFile(path(SP->getFile()));if(!source)continue;
    auto text=(*source)->getBuffer();auto sourceHash=toHex(SHA256::hash(ArrayRef<uint8_t>(reinterpret_cast<const uint8_t *>(text.data()),text.size())),true);
    for(unsigned i=0;i<commands->size();++i){auto *command=(*commands)[i].getAsObject();auto *aliases=command?command->getArray("aliases"):nullptr;if(!aliases)continue;
      for(auto &entry:*aliases){auto *alias=entry.getAsObject();if(!alias)continue;
        auto symbol=alias->getString("symbol"),debug=alias->getString("debug_name"),hash=alias->getString("source_sha256");
        if(!hash || *hash!=sourceHash || !((symbol && *symbol==F.getName()) || (debug && *debug==SP->getName())))continue;
        auto base=alias->getInteger("memory_base_argument"),active=alias->getInteger("active_elements_argument");
        auto role=alias->getString("role");
        bool memory=command->getString("memory_effect").value_or("read")!="none";
        if((memory && (!base || *base<0)) || !role)report_fatal_error("invalid semantic operand binding");
        if(bindings.count(&F))report_fatal_error("ambiguous semantic function binding");
        bindings.emplace(&F,Binding{i,unsigned(base.value_or(0)),unsigned(active.value_or(0)),bool(active),alias->getBoolean("active_elements_signed").value_or(false),*role=="backend_alias",memory});
      }
    }
  }
  auto &C=M.getContext();auto *u32=Type::getInt32Ty(C),*u64=Type::getInt64Ty(C);auto *voidTy=Type::getVoidTy(C);
  auto enter=M.getOrInsertFunction("__swdb_command_enter",voidTy,u32,u32,u32,u64,u32,u64,u32,u32);
  auto leave=M.getOrInsertFunction("__swdb_command_leave",voidTy,u32,u32);
  std::vector<CallBase *> sites;
  for(Function &F:M)if(!F.isDeclaration() && !F.getName().starts_with("__swdb_"))
    for(Instruction &I:instructions(F))if(auto *call=dyn_cast<CallBase>(&I))if(bindings.count(call->getCalledFunction()))sites.push_back(call);
  unsigned site=0;
  for(auto *call:sites){
    auto binding=bindings.at(call->getCalledFunction());
    if(binding.memory && (binding.base>=call->arg_size() || !call->getArgOperand(binding.base)->getType()->isPointerTy()))report_fatal_error("semantic base operand is not a pointer");
    if(binding.activeKnown && (binding.active>=call->arg_size() || !call->getArgOperand(binding.active)->getType()->isIntegerTy()))report_fatal_error("semantic active count operand is not integer");
    if(auto *ordinary=dyn_cast<CallInst>(call))if(ordinary->isMustTailCall())report_fatal_error("semantic musttail boundary is unsupported");
    IRBuilder<> before(call);before.SetCurrentDebugLocation(call->getDebugLoc());
    Value *active=binding.activeKnown?before.CreateZExtOrTrunc(call->getArgOperand(binding.active),u64):before.getInt64(0);
    Value *activeKnown=before.getInt32(binding.activeKnown || !binding.memory);
    if(binding.activeKnown && binding.activeSigned)activeKnown=before.CreateZExt(before.CreateICmpSGE(call->getArgOperand(binding.active),ConstantInt::get(call->getArgOperand(binding.active)->getType(),0)),u32);
    before.CreateCall(enter,{before.getInt32(binding.descriptor),before.getInt32(site),before.getInt32(0),
      binding.memory?before.CreatePtrToInt(call->getArgOperand(binding.base),u64):before.getInt64(0),before.getInt32(binding.alias),
      active,activeKnown,before.getInt32(binding.memory)});
    if(auto *invoke=dyn_cast<InvokeInst>(call)){
      auto *normal=SplitEdge(invoke->getParent(),invoke->getNormalDest());if(!normal)report_fatal_error("semantic normal edge cannot be split");
      IRBuilder<> after(&*normal->getFirstInsertionPt());after.CreateCall(leave,{after.getInt32(site),after.getInt32(0)});
      auto *unwind=invoke->getUnwindDest();
      if(!isa<LandingPadInst>(&*unwind->getFirstNonPHIIt()))report_fatal_error("semantic unwind requires an Itanium landingpad");
      SmallVector<BasicBlock *,2> split;SplitLandingPadPredecessors(unwind,{invoke->getParent()},".swdb.command",".swdb.other",split);
      IRBuilder<> failed(&*invoke->getUnwindDest()->getFirstInsertionPt());failed.CreateCall(leave,{failed.getInt32(site),failed.getInt32(1)});
    } else if(call->doesNotThrow()){
      IRBuilder<> after(call->getNextNode());after.CreateCall(leave,{after.getInt32(site),after.getInt32(0)});
    } else {
      // A plain potentially throwing call has no visible cleanup edge. Give the
      // guard an explicit cleanup that resumes the same language exception.
      auto *F=call->getFunction();auto *block=call->getParent();
      auto *normal=block->splitBasicBlock(call->getNextNode(),"swdb.command.normal");block->getTerminator()->eraseFromParent();
      auto *cleanup=BasicBlock::Create(C,"swdb.command.unwind",F);
      if(!F->hasPersonalityFn())F->setPersonalityFn(cast<Constant>(M.getOrInsertFunction("__gxx_personality_v0",FunctionType::get(u32,true)).getCallee()));
      SmallVector<Value *,8> arguments(call->args());
      auto *invoke=InvokeInst::Create(call->getFunctionType(),call->getCalledOperand(),normal,cleanup,arguments,"",block);
      sourceInvokes.insert(invoke);invoke->setCallingConv(call->getCallingConv());invoke->setAttributes(call->getAttributes());invoke->setDebugLoc(call->getDebugLoc());call->replaceAllUsesWith(invoke);call->eraseFromParent();
      IRBuilder<> after(&*normal->getFirstInsertionPt());after.CreateCall(leave,{after.getInt32(site),after.getInt32(0)});
      IRBuilder<> failed(cleanup);auto *pad=failed.CreateLandingPad(StructType::get(PointerType::getUnqual(C),u32),0);pad->setCleanup(true);
      failed.CreateCall(leave,{failed.getInt32(site),failed.getInt32(1)});failed.CreateResume(pad);
    }
    ++site;
  }
  if(!site)report_fatal_error("no call matched verified semantic command aliases");
  for(Function &F:M)for(Instruction &I:instructions(F))if(!original.count(&I) && !sourceInvokes.count(&I))I.setMetadata("swdb.observer",MDNode::get(C,{}));
  return PreservedAnalyses::none();
}
};
