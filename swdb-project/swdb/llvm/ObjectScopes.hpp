// Optional source-object observer, inserted after original count-site enumeration.
// Updated: 2026-10-06 ET. Generated scaffolding never contributes source work.
#pragma once
inline void instrumentObjectScopes(Module &M) {
  if(env("SWDB_OBJECT_SCOPES")!="1")return;
  auto &C=M.getContext();auto *u64=Type::getInt64Ty(C),*u32=Type::getInt32Ty(C);
  auto enter=M.getOrInsertFunction("__swdb_object_scope_enter",u64);
  auto add=M.getOrInsertFunction("__swdb_object_scope_alloc",Type::getVoidTy(C),u64,u64,u64,u32);
  auto leave=M.getOrInsertFunction("__swdb_object_scope_leave",Type::getVoidTy(C),u64);
  for(Function &F:M) {
    if(F.isDeclaration() || F.getName().starts_with("__swdb_") || !F.getSubprogram())continue;
    SmallVector<AllocaInst *,16> allocas;SmallVector<Instruction *,8> exits;
    for(Instruction &I:instructions(F)) {
      if(auto *A=dyn_cast<AllocaInst>(&I))allocas.push_back(A);
      if(isa<ReturnInst>(I))exits.push_back(&I);
    }
    SmallPtrSet<Instruction *,32> original;for(Instruction &I:instructions(F))original.insert(&I);
    IRBuilder<> entry(&*F.getEntryBlock().getFirstInsertionPt());auto *frame=entry.CreateCall(enter);
    for(auto *A:allocas) {
      auto size=M.getDataLayout().getTypeAllocSize(A->getAllocatedType());
      IRBuilder<> B(A->getNextNode());
      Value *bytes=B.getInt64(0),*known=B.getInt32(0);
      if(!size.isScalable() && isa<ConstantInt>(A->getArraySize())) {
        auto count=cast<ConstantInt>(A->getArraySize())->getValue();
        if(count.getActiveBits()<=64 && (!size.getFixedValue() || count.getZExtValue()<=UINT64_MAX/size.getFixedValue())) {
          bytes=B.getInt64(count.getZExtValue()*size.getFixedValue());known=B.getInt32(1);
        }
      }
      B.CreateCall(add,{frame,B.CreatePtrToInt(A,u64),bytes,known});
    }
    for(auto *I:exits) {
      // A musttail call must remain adjacent to its return.
      if(auto *call=dyn_cast_or_null<CallInst>(I->getPrevNode());call && call->isMustTailCall())I=call;
      IRBuilder<> B(I);B.CreateCall(leave,{frame});
    }
    for(Instruction &I:instructions(F))if(!original.count(&I))I.setMetadata("swdb.observer",MDNode::get(C,{}));
  }
}
