2026-10-16 ET.

This packet constructs an existential PRIVATE interpretation component for the
one exact int move caller. For every arbitrary incoming source-memory observation
I, the interpretation is I times P times A: I is unrestricted; P is the finite
receiver/buffer witness constructed here; A contains source-fresh administrative
storage hidden separately. P starts at next=1 with no issued keys. This is a
choice of private logical witness, never an empty incoming C heap or a global
Owners.valid/world caller premise. Fresh actual source/destination/buffer identity
names map injectively to P's table. Their actual numerical pointer addresses are
not equated to logical addresses. Default storage/allocator/library correspondence,
layout and local framing remain explicit TCB; no Typed Mint/Mptr ownership follows.

For n=0 choose source key1 at logical address8/extent24 and destination key2 at
address32/extent24, next3. There is no buffer. For every 1<=n<=2147483647 choose
source key1/address8/extent24, buffer key2/address56/extent4*n, destination key3/
address32/extent24, next4. The source begins before its exact constructor; positive
buffer allocation occurs inside the constructor before destination begins. Source
stores Pointer(buffer,0), Integer(n), Integer(n) at offsets0,8,16. Destination is
writable/aligned/reserved with no initialized header-value premise. Other private
keys have allocated/alive=false. All live ranges are separated for every count:
[8,32), [32,56), and, when positive, [56,56+4*n). Exact affine endpoint checks give
4<=4*n<=8589934588 and 60<=56+4*n<=8589934644. Header field stores have width8,
offsets0/8/16, address alignment8 and end<=24. These are logical address witnesses,
not assertions about physical numeric addresses or the total caller address map.

The private owner map is active exactly at source,destination, backing(source)=
buffer and backing(destination)=0; every other key is inactive/backing0. Ready is
true only for source. Complete Owners.valid follows by the two finite active cases:
all positive receiver/backing keys are below next, the sole positive backing is
not either receiver, and any two owners of the same positive backing are equal.
Heap.well_formed follows by all issued/live cases and every live pair above.
Every active owner has receiver storage. The sole ready existential chooses the
actual initialized source fields n,c=n. A positive source backing is dynamic/live
and hence freeable at offset0; the zero case has no positive backing obligation.
This derives EVERY world conjunct, reserved(destination), active(source),
ready(source), destination!=source and header(source,buffer,n,n). Destination values
are never assumed. The complete original four move antecedents/statements and
constructor35/destructor11/private9 remain exact evidence-required dependencies.
No opaque incoming owner registry or sibling/postcondition theorem is a premise.

The complete checked constructor loop gives an initialized literal7 prefix. Base
k=0 is empty. For 0<=k<n write element k at4*k, width4. Put n=k+t+1 for independent
nonnegative integers k,t: 4*n-(4*k+4)=4*t>=0. Its address is aligned4. For j<k,
4*(k-j)>=4, so all earlier initialized elements survive. Increment k and decrease
n-k; finite exit k=n proves every j<n initialized int7. This is symbolic induction,
not a test over a bounded set of n. The exact nonnegative signed32 count widens
without loss and all count/byte bounds fit the selected 64-bit model. Fresh buffer
initial memory is unobserved; the empty prefix does not assume a caller payload.

Capture source.data() before the move as a borrowed raw alias. Complete move
copies all three source header fields to destination, then resets source to null,
0,0. Owners updates only its two backing entries and both phases become ready;
full world is checked again from complete definitions. The payload remains the
same live allocation. Thus n>0 reads initialized int7 at saved[0]; n=0 selects
literal0 without evaluating a pointer expression. Store this scalar into value
and swdb_return before either destructor. The selected moved-from-empty MODEL
correspondence is explicit library TCB, not a portable C++17 postcondition.

Destination destructor releases its one positive buffer (or null), then destination
scope ends; source destructor actually releases NULL after the reset, then source
scope ends. Registry retirement is checked separately and never substituted for
Heap.release. All private allocations retain issued ghost history/frontier but end
not-live. The result scalar was captured earlier; no raw pointer/payload is read
after release. The original source-rule exact full C inverse and fallback CFG
checks remain embedded, with no source or logical-annotation edit.

For arbitrary incoming identity q, each exact source effect targets a distinct
source-fresh private identity or is null release. A target-local store/release/
scope event preserves q. Pointwise identity composes across the full sequence and
every fill iteration. Administrative parameters, loop counter, pointer/scalar locals
and capture slots have their actual activation/store/scope order checked in the
separate product A; they do not silently consume P's frontier. Incoming live bytes
and allocation metadata and dead-ID ghost histories are preserved under the full
source/allocator/release framing TCB. Reusing a dead physical address does NOT claim
its old physical bytes remain unchanged. There is no restriction on incoming types.

This is a checked conditional private derivation. It grants no source/public record,
Heap/Typed/lifetime/caller/default admission. Complete root-adopted exact mathematical
evidence, full original normal diagnostic ledger and current framework preflight
are separate gates. Launch unconditionally refuses until those gates are bound.
