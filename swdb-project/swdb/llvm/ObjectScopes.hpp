// Optional source-object observer, inserted after original count-site enumeration.
// Updated: 2026-10-06 ET. Generated scaffolding never contributes source work.
#pragma once
inline void instrumentObjectScopes(Module &M) {
  if(env("SWDB_OBJECT_SCOPES")!="1")return;
  auto &C=M.getContext();auto *u64=Type::getInt64Ty(C),*u32=Type::getInt32Ty(C);
  auto enter=M.getOrInsertFunction("__swdb_object_scope_enter",u64);
  auto add=M.getOrInsertFunction("__swdb_object_scope_alloc",Type::getVoidTy(C),u64,u64,u64,u32);
  auto leave=M.getOrInsertFunction("__swdb_object_scope_leave",Type::getVoidTy(C),u64);
  auto retire=M.getOrInsertFunction("__swdb_object_scope_retire",Type::getVoidTy(C),u64,u64);
  auto mark=M.getOrInsertFunction("__swdb_object_scope_mark",u64,u64);
  auto restore=M.getOrInsertFunction("__swdb_object_scope_restore",Type::getVoidTy(C),u64,u64);
  for(Function &F:M) {
    if(F.isDeclaration() || F.getName().starts_with("__swdb_") || !F.getSubprogram())continue;
    SmallVector<AllocaInst *,16> allocas;SmallVector<Instruction *,8> exits;
    SmallVector<IntrinsicInst *,16> lifetimes,saves,restores;
    std::set<AllocaInst *> explicitLifetimes;
    for(Instruction &I:instructions(F)) {
      if(auto *A=dyn_cast<AllocaInst>(&I))allocas.push_back(A);
      if(isa<ReturnInst>(I))exits.push_back(&I);
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
    auto registerAlloca=[&](AllocaInst *A,Instruction *at) {
      auto size=M.getDataLayout().getTypeAllocSize(A->getAllocatedType());IRBuilder<> B(at);
      Value *bytes=B.getInt64(0),*known=B.getInt32(0);
      if(!size.isScalable() && A->getArraySize()->getType()->getIntegerBitWidth()<=64) {
        auto multiply=M.getOrInsertFunction("llvm.umul.with.overflow.i64",StructType::get(u64,B.getInt1Ty()),u64,u64);
        auto *product=B.CreateCall(multiply,{B.CreateZExtOrTrunc(A->getArraySize(),u64),B.getInt64(size.getFixedValue())});
        bytes=B.CreateExtractValue(product,0);known=B.CreateZExt(B.CreateNot(B.CreateExtractValue(product,1)),u32);
      }
      B.CreateCall(add,{frame,B.CreatePtrToInt(A,u64),bytes,known});
    };
    for(auto *A:allocas)if(!explicitLifetimes.count(A))registerAlloca(A,A->getNextNode());
    for(auto *intrinsic:lifetimes)if(auto *A=dyn_cast<AllocaInst>(intrinsic->getArgOperand(intrinsic->arg_size()-1)->stripPointerCasts())) {
      if(intrinsic->getIntrinsicID()==Intrinsic::lifetime_start)registerAlloca(A,intrinsic->getNextNode());
      else {IRBuilder<> B(intrinsic);B.CreateCall(retire,{frame,B.CreatePtrToInt(A,u64)});}
    }
    std::map<Value *,Value *> checkpoints;
    for(auto *save:saves){IRBuilder<> B(save->getNextNode());checkpoints[save]=B.CreateCall(mark,{frame});}
    for(auto *reset:restores){IRBuilder<> B(reset);auto found=checkpoints.find(reset->getArgOperand(0)->stripPointerCasts());
      B.CreateCall(restore,{frame,found==checkpoints.end()?B.getInt64(0):found->second});}
    for(auto *I:exits) {
      // A musttail call must remain adjacent to its return.
      if(auto *call=dyn_cast_or_null<CallInst>(I->getPrevNode());call && call->isMustTailCall())I=call;
      IRBuilder<> B(I);B.CreateCall(leave,{frame});
    }
    for(Instruction &I:instructions(F))if(!original.count(&I))I.setMetadata("swdb.observer",MDNode::get(C,{}));
  }
}
