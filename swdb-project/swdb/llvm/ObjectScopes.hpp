// Optional source-object observer, inserted after original count-site enumeration.
// Updated: 2026-10-06 ET. Generated scaffolding never contributes source work.
#pragma once
inline void instrumentObjectScopes(Module &M) {
  if(env("SWDB_OBJECT_SCOPES")!="1")return;
  auto &C=M.getContext();auto *u64=Type::getInt64Ty(C),*u32=Type::getInt32Ty(C);
  auto abandon=M.getOrInsertFunction("__swdb_object_scope_abandon",Type::getVoidTy(C));
  auto problem=M.getOrInsertFunction("__swdb_object_scope_problem",Type::getVoidTy(C));
  auto enter=M.getOrInsertFunction("__swdb_object_scope_enter",u64);
  auto storageFn=M.getOrInsertFunction("__swdb_object_scope_storage",u64,u64);
  auto add=M.getOrInsertFunction("__swdb_object_scope_alloc_at",Type::getVoidTy(C),u64,u64,u64,u32,u64);
  auto leave=M.getOrInsertFunction("__swdb_object_scope_leave",Type::getVoidTy(C),u64);
  auto unwind=M.getOrInsertFunction("__swdb_object_scope_unwind",Type::getVoidTy(C),u64);
  auto retire=M.getOrInsertFunction("__swdb_object_scope_retire",Type::getVoidTy(C),u64,u64);
  auto mark=M.getOrInsertFunction("__swdb_object_scope_mark",u64,u64);
  auto restore=M.getOrInsertFunction("__swdb_object_scope_restore",Type::getVoidTy(C),u64,u64);
  auto global=M.getOrInsertFunction("__swdb_object_scope_global",Type::getVoidTy(C),u64,u64,u32);
  auto view=M.getOrInsertFunction("__swdb_object_scope_view",Type::getVoidTy(C),u64,u64,u64);
  std::set<Function *> microtasks;
  for(Function &F:M)for(Instruction &I:instructions(F))if(auto *call=dyn_cast<CallBase>(&I))
    if(auto *callee=call->getCalledFunction();callee && callee->getName()=="__kmpc_fork_call" && call->arg_size()>=3)
      if(auto *task=dyn_cast<Function>(call->getArgOperand(2)->stripPointerCasts()))microtasks.insert(task);
  for(Function &F:M) {
    if(F.isDeclaration() || F.getName().starts_with("__swdb_") || !F.getSubprogram())continue;
    bool unsupported=false;
    for(Instruction &I:instructions(F)){
      if(isa<CatchSwitchInst>(I) || isa<FuncletPadInst>(I) || isa<CallBrInst>(I))unsupported=true;
      if(auto *call=dyn_cast<CallBase>(&I))if(auto *callee=call->getCalledFunction())
        if(callee->getName().starts_with("llvm.coro."))unsupported=true;
    }
    if(unsupported){IRBuilder<> B(&*F.getEntryBlock().getFirstInsertionPt());auto *call=B.CreateCall(problem);call->setMetadata("swdb.observer",MDNode::get(C,{}));continue;}
    SmallVector<CallBase *,8> nonlocal,returnsTwice;
    SmallVector<AllocaInst *,16> allocas;SmallVector<Instruction *,8> exits;SmallVector<LandingPadInst *,8> pads;
    SmallVector<IntrinsicInst *,16> lifetimes,saves,restores;
    std::set<AllocaInst *> explicitLifetimes;std::set<GlobalVariable *> globals;
    SmallVector<Value *,32> operands;SmallPtrSet<Value *,32> seen;
    for(Instruction &I:instructions(F))for(Value *value:I.operands())operands.push_back(value);
    while(!operands.empty()){
      auto *value=operands.pop_back_val();if(!seen.insert(value).second)continue;
      if(auto *G=dyn_cast<GlobalVariable>(value)){if(!G->isDeclaration() && !G->isThreadLocal())globals.insert(G);}
      if(auto *user=dyn_cast<User>(value))for(Value *operand:user->operands())operands.push_back(operand);
    }
    for(Instruction &I:instructions(F)) {
      if(auto *call=dyn_cast<CallBase>(&I)){
        if(call->hasFnAttr(Attribute::ReturnsTwice) && isa<CallInst>(call))returnsTwice.push_back(call);
        if(auto *callee=call->getCalledFunction())for(auto name:{"longjmp","_longjmp","siglongjmp","pthread_exit"})
          if(callee->getName()==name)nonlocal.push_back(call);
      }
      if(auto *A=dyn_cast<AllocaInst>(&I))allocas.push_back(A);
      if(isa<ReturnInst>(I) || isa<ResumeInst>(I))exits.push_back(&I);
      if(auto *pad=dyn_cast<LandingPadInst>(&I))pads.push_back(pad);
      if(auto *intrinsic=dyn_cast<IntrinsicInst>(&I)) {
        auto id=intrinsic->getIntrinsicID();
        if(id==Intrinsic::lifetime_start || id==Intrinsic::lifetime_end) {
          lifetimes.push_back(intrinsic);
          if(auto *A=dyn_cast<AllocaInst>(intrinsic->getArgOperand(intrinsic->arg_size()-1)->stripPointerCasts()))explicitLifetimes.insert(A);
        }
        if(id==Intrinsic::stacksave)saves.push_back(intrinsic);
        if(id==Intrinsic::stackrestore)restores.push_back(intrinsic);
      }
    }
    SmallPtrSet<Instruction *,32> original;for(Instruction &I:instructions(F))original.insert(&I);
    IRBuilder<> entry(&*F.getEntryBlock().getFirstInsertionPt());auto *frame=entry.CreateCall(enter);
    for(auto *G:globals){auto size=M.getDataLayout().getTypeAllocSize(G->getValueType());
      if(!size.isScalable() && !M.getDataLayout().isNonIntegralPointerType(G->getType()))entry.CreateCall(global,{entry.CreatePtrToInt(G,u64),entry.getInt64(size.getFixedValue()),entry.getInt32(1)});
    }
    if(microtasks.count(&F) && F.arg_size()>=2 && F.getArg(0)->getType()->isPointerTy() && F.getArg(1)->getType()->isPointerTy())
      for(unsigned i=0;i<2;++i)entry.CreateCall(view,{frame,entry.CreatePtrToInt(F.getArg(i),u64),entry.getInt64(4)});
    std::map<AllocaInst *,CallInst *> storage;
    for(auto *A:allocas){IRBuilder<> B(A->getNextNode());storage[A]=B.CreateCall(storageFn,{frame});}
    auto registerAlloca=[&](AllocaInst *A,Instruction *at) {
      auto size=M.getDataLayout().getTypeAllocSize(A->getAllocatedType());IRBuilder<> B(at);
      Value *bytes=B.getInt64(0),*known=B.getInt32(0);
      if(!size.isScalable() && !M.getDataLayout().isNonIntegralPointerType(A->getType()) && A->getArraySize()->getType()->getIntegerBitWidth()<=64) {
        auto multiply=M.getOrInsertFunction("llvm.umul.with.overflow.i64",StructType::get(u64,B.getInt1Ty()),u64,u64);
        auto *product=B.CreateCall(multiply,{B.CreateZExtOrTrunc(A->getArraySize(),u64),B.getInt64(size.getFixedValue())});
        bytes=B.CreateExtractValue(product,0);known=B.CreateZExt(B.CreateNot(B.CreateExtractValue(product,1)),u32);
      }
      B.CreateCall(add,{frame,B.CreatePtrToInt(A,u64),bytes,known,storage.at(A)});
    };
    for(auto *A:allocas)if(!explicitLifetimes.count(A))registerAlloca(A,storage.at(A)->getNextNode());
    for(auto *intrinsic:lifetimes)if(auto *A=dyn_cast<AllocaInst>(intrinsic->getArgOperand(intrinsic->arg_size()-1)->stripPointerCasts())) {
      if(intrinsic->getIntrinsicID()==Intrinsic::lifetime_start)registerAlloca(A,intrinsic->getNextNode());
      else {IRBuilder<> B(intrinsic);B.CreateCall(retire,{frame,B.CreatePtrToInt(A,u64)});}
    }
    std::map<Value *,Value *> checkpoints;
    for(auto *save:saves){IRBuilder<> B(save->getNextNode());checkpoints[save]=B.CreateCall(mark,{frame});}
    for(auto *reset:restores){IRBuilder<> B(reset);auto found=checkpoints.find(reset->getArgOperand(0)->stripPointerCasts());
      B.CreateCall(restore,{frame,found==checkpoints.end()?B.getInt64(0):found->second});}
    for(auto *call:nonlocal){IRBuilder<> B(call);B.CreateCall(abandon);}
    for(auto *call:returnsTwice){IRBuilder<> B(call->getNextNode());B.CreateCall(unwind,{frame});}
    for(auto *pad:pads){IRBuilder<> B(&*pad->getParent()->getFirstInsertionPt());B.CreateCall(unwind,{frame});}
    for(auto *I:exits) {
      // A musttail call must remain adjacent to its return.
      if(auto *call=dyn_cast_or_null<CallInst>(I->getPrevNode());call && call->isMustTailCall())I=call;
      IRBuilder<> B(I);B.CreateCall(leave,{frame});
    }
    for(Instruction &I:instructions(F))if(!original.count(&I))I.setMetadata("swdb.observer",MDNode::get(C,{}));
  }
}
