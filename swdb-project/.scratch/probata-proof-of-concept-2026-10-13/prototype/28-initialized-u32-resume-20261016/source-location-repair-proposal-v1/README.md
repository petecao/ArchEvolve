The Linux diagnostic retained the original assertion subtree and frozen compiler
inputs on mbit10. The unchanged validator rejected two `SourceLocExpr` leaves in
the file and line arguments of `__assert_fail`; this happened before WP.
The compact local receipt pins the complete remote subtree and token stream.

The proposed repair recognizes only the two direct diagnostic arguments of the
already exact arity-one u32 abort call. It binds their complete leaf metadata,
types, source ranges, order, builtin token spellings and original file/line
mapping in the same frozen translation unit. Other expression positions retain
the old kind restrictions. The old literal diagnostic path remains available.
The original caller, answers 711/1107, predicate guards, body comparison and
source-to-value bindings remain unchanged.

[Clang's primary documentation](https://clang.llvm.org/docs/LanguageExtensions.html#source-location-builtins)
defines these builtins as constant expressions giving the invocation's file and
line. Their interpretation is within the existing selected-compiler trust
boundary. This repair admits the observed diagnostic representation; it does
not supply a new program premise or a proof result.

The production file remains unchanged until independent review and integration.
Local controls use synthetic assertion nodes derived from an existing captured
allocator assertion, with the already required arity-one function diagnostic.
They are explicitly distinct from the complete retained initialized subtree.
The complete retained AST, preprocessed source and LLVM remain on mbit10.
