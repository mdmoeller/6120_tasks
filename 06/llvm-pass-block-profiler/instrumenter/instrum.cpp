#include <llvm/Pass.h>
#include <llvm/IR/Function.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>
#include <llvm/IR/InstrTypes.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/BasicBlock.h>

#include <vector>
#include <string>

using namespace llvm;

namespace {
    struct InstrumPass : public FunctionPass {
        static char ID;
        InstrumPass() : FunctionPass(ID) {}

        size_t f_idx = 0;

        virtual bool runOnFunction(Function &F) {

            LLVMContext& ctxt = F.getContext();

            auto logFunc = F.getParent()->getOrInsertFunction("log_block", 
                    Type::getVoidTy(ctxt), Type::getInt32Ty(ctxt), Type::getInt32Ty(ctxt));

            size_t i = 0;

            /* Add the logger to every block */
            for (auto& b : F) {
                IRBuilder<> builder(b.getFirstNonPHI());

                auto a1 = ConstantInt::get(Type::getInt32Ty(ctxt), f_idx);
                auto a2 = ConstantInt::get(Type::getInt32Ty(ctxt), i);
                Value *args[2] = {a1, a2};

                builder.CreateCall(logFunc, args);
                i++;
            }

            /* Add setup calls to the entry block of main only */
            if (F.getName() == "main") {
                Module *P = F.getParent();

                auto& entry = F.getEntryBlock();
                auto first = entry.getFirstNonPHI();

                IRBuilder<> builder(first);

                /* Initialize countlib with the count of functions */
                auto initFunc = P->getOrInsertFunction("init_counter", 
                        Type::getVoidTy(ctxt), Type::getInt32Ty(ctxt));

                int num_fun = 0;
                for (auto &f : P->functions()) {
                    if (f.size() > 0)
                        num_fun++;
                }
                Value *args = {ConstantInt::get(Type::getInt32Ty(ctxt), num_fun)};
                builder.CreateCall(initFunc, args);

                /* Add each function based on block size */
                auto addFunc = P->getOrInsertFunction("add_function",
                        Type::getVoidTy(ctxt),
                        Type::getInt8PtrTy(ctxt),
                        Type::getInt32Ty(ctxt));


                int j = 0;
                for (auto& f : P->functions()) {
                    if (f.size()) {
                        auto strPtr = builder.CreateGlobalStringPtr(f.getName());
                        Value *args[2] = {strPtr,
                            ConstantInt::get(Type::getInt32Ty(ctxt), f.size())};
                        builder.CreateCall(addFunc, args);
                    }

                }
            }

            f_idx++;
            return true;
        }
    };
}

char InstrumPass::ID = 1;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerInstrumPass(const PassManagerBuilder &,
        legacy::PassManagerBase &PM) {
    PM.add(new InstrumPass());
}
static RegisterStandardPasses
RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
        registerInstrumPass);
