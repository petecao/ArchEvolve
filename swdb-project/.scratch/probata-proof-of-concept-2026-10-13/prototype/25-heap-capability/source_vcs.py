"""Closed original int count/value + dtor source VC map. Created: 2026-10-15 ET.

Trusted translation prototype: these definitions describe source transitions and
VCs, not desired postcondition axioms. No proof result is generated here.
"""

PRELUDE = r"""
/*@ logic Heap::heap t25_initial(Heap::heap h, integer r, integer o) =
      Heap::put_integer(Heap::put_integer(Heap::put_pointer(h,r,o,0,0),r,o+8,0),r,o+16,0);
    logic Heap::heap t25_allocated(Heap::heap h, integer r, integer o, integer n, integer a) =
      Heap::put_integer(Heap::put_pointer(Heap::allocate(t25_initial(h,r,o),n,a),
        r,o,Heap::fresh_id(h),0),r,o+16,n);
    logic Heap::heap t25_sample(integer dummy) =
      Heap::put_integer(Heap::put_integer(
        t25_allocated(Heap::allocate(Heap::empty(0),6,8),1,0,1,64),2,0,7),1,8,1);
    predicate t25_fields(Heap::heap h, integer r, integer o,
                        integer b, integer bo, integer s, integer c) =
      Heap::typed_writes(h,r,o,24,8) &&
      Heap::initialized_at(h,r,o) && Heap::pointer_at(h,r,o,b,bo) &&
      Heap::initialized_at(h,r,o+8) && Heap::integer_at(h,r,o+8,s) &&
      Heap::initialized_at(h,r,o+16) && Heap::integer_at(h,r,o+16,c);
    predicate t25_repr(Heap::heap h, integer r, integer o,
                      integer b, integer bo, integer s, integer c) =
      t25_fields(h,r,o,b,bo,s,c) && 0 <= s <= c <= 4611686018427387903 &&
      (c == 0 ? b == 0 && bo == 0 : Heap::typed_writes(h,b,bo,4*c,4)) &&
      (\forall integer j; 0 <= j < s ==> Heap::initialized_at(h,b,bo+4*j));
    predicate t25_inv(Heap::heap h, integer r, integer o, integer b,
                     integer n, integer k, integer v) =
      Heap::well_formed(h) && t25_fields(h,r,o,b,0,0,n) && b != r &&
      0 < n <= 4611686018427387903 && 0 <= k <= n &&
      Heap::typed_writes(h,b,0,4*n,4) && Heap::filled_prefix(h,b,k,v);
    predicate t25_frame(Heap::heap old, Heap::heap now, integer r, integer o) =
      (\forall integer b; Heap::live(old,b) ==>
        Heap::same_object(old,now,b)) &&
      (\forall integer b,p; Heap::live(old,b) && !(b == r && o <= p < o+24) ==>
        Heap::contents(old,b,p) == Heap::contents(now,b,p) &&
        (Heap::initialized_at(old,b,p) <==> Heap::initialized_at(now,b,p)));
*/
"""

NUMERIC = r"""/* 2026-10-15 ET. Original uint64 count/index/allocator arithmetic VC kernel.
   The loop-state relation supplies k<n; it is not an added original caller premise. */
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
struct t25_receiver_layout { int *data; size_t size; size_t capacity; };
_Static_assert(sizeof(int) == 4, "mapped int width");
_Static_assert(_Alignof(int) == 4, "mapped int alignment");
_Static_assert(_Alignof(struct t25_receiver_layout) == 8, "mapped receiver alignment");
_Static_assert(sizeof(size_t) == 8, "mapped size width");
_Static_assert(sizeof(void *) == 8, "mapped receiver layout");
_Static_assert(sizeof(struct t25_receiver_layout) == 24, "mapped receiver extent");
_Static_assert(offsetof(struct t25_receiver_layout, data) == 0, "mapped data field");
_Static_assert(offsetof(struct t25_receiver_layout, size) == 8, "mapped size field");
_Static_assert(offsetof(struct t25_receiver_layout, capacity) == 16, "mapped capacity field");
/*@ requires n <= 4611686018427387903 && k < n;
    assigns \nothing;
    ensures \result == k+1 && \result <= n;
*/
size_t t25_ctor_numeric(size_t n, size_t k) {
  size_t next = k + 1;
  size_t bytes = n * sizeof(int);
  /*@ assert allocation_size_no_wrap: (integer)n * 4 <= 18446744073709551615; */
  /*@ assert allocation_size_exact: bytes == (integer)n * 4; */
  /*@ assert scaled_index_in_range: (integer)k * 4 + 4 <= bytes; */
  /*@ assert variant_nonnegative: 0 <= (integer)n - k; */
  /*@ assert variant_decreases: 0 <= (integer)n - next < (integer)n - k; */
  return next;
}
"""


def specs():
    C = 'std_vector_int_ctor_count_value'
    D = 'std_vector_int_dtor'
    # Source span text, independent C1-C9/D1-D7 review group, and actual VC.
    # Quantified heap/alias variables are arbitrary; only original entry facts
    # and inductively established loop representation facts occur as hypotheses.
    rows = [
        ('control.ctor.premises_feasible', C, 'requires \\valid(this) && n <= ', ['C1','C3'],
         r'Heap::well_formed(Heap::allocate(Heap::empty(0),6,8)) && Heap::typed_writes(Heap::allocate(Heap::empty(0),6,8),1,0,24,8) && Heap::available(Heap::allocate(Heap::empty(0),6,8),1,64)'),
        ('control.dtor.premises_feasible', D, 'swdb_free(this->data);', ['D1','D2'],
         r'Heap::well_formed(t25_sample(0)) && t25_repr(t25_sample(0),1,0,2,0,1,1) && Heap::freeable(t25_sample(0),2,0)'),
        ('ctor.rte.zero_data', C, 'this->data = NULL;', ['C1'],
         r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> Heap::typed_writes(h,r,o,8,8)'),
        ('ctor.rte.zero_size', C, 'this->size = 0;', ['C1'],
         r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> Heap::typed_writes(Heap::put_pointer(h,r,o,0,0),r,o+8,8,8)'),
        ('ctor.rte.zero_capacity', C, 'this->capacity = 0;', ['C1'],
         r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> Heap::typed_writes(Heap::put_integer(Heap::put_pointer(h,r,o,0,0),r,o+8,0),r,o+16,8,8)'),
        ('ctor.fields.initialized', C, 'this->data = NULL; this->size = 0; this->capacity = 0;', ['C1'],
         r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> t25_fields(t25_initial(h,r,o),r,o,0,0,0,0)'),
        ('ctor.zero.post', C, 'if (n == 0) return;', ['C2'],
         r'\forall Heap::heap h; \forall integer r,o; Heap::typed_writes(h,r,o,24,8) ==> t25_repr(t25_initial(h,r,o),r,o,0,0,0,0)'),
        ('ctor.zero.frame', C, 'if (n == 0) return;', ['C2','C9'],
         r'\forall Heap::heap h; \forall integer r,o; t25_frame(h,t25_initial(h,r,o),r,o)'),
        ('ctor.alloc.identity', C, 'this->data = swdb_alloc_int(n);', ['C3'],
         r'\forall Heap::heap h; \forall integer r,o,n,a; Heap::well_formed(h) && Heap::typed_writes(h,r,o,24,8) ==> Heap::fresh_id(h) != r && !Heap::issued(h,Heap::fresh_id(h)) && Heap::live(Heap::allocate(h,n,a),Heap::fresh_id(h))'),
        ('ctor.alloc.well_formed', C, 'this->data = swdb_alloc_int(n);', ['C3','C9'],
         r'\forall Heap::heap h; \forall integer n,a; Heap::well_formed(h) && Heap::available(h,n,a) ==> Heap::well_formed(Heap::allocate(h,n,a))'),
        ('ctor.alloc.separation', C, 'this->data = swdb_alloc_int(n);', ['C3','C9'],
         r'\forall Heap::heap h; \forall integer n,a,b; Heap::well_formed(h) && Heap::available(h,n,a) && Heap::live(h,b) ==> Heap::separated(Heap::allocate(h,n,a),Heap::fresh_id(h),b)'),
        ('ctor.alloc.extent', C, 'this->data = swdb_alloc_int(n);', ['C3','C6'],
         r'\forall Heap::heap h; \forall integer n,a; Heap::well_formed(h) && Heap::available(h,n,a) && 0 < n ==> Heap::typed_writes(Heap::allocate(h,n,a),Heap::fresh_id(h),0,4*n,4) && Heap::bytes(Heap::allocate(h,n,a),Heap::fresh_id(h)) == 4*n'),
        ('ctor.alloc.uninitialized', C, 'this->data = swdb_alloc_int(n);', ['C3','C5'],
         r'\forall Heap::heap h; \forall integer n,a,j; !Heap::initialized_at(Heap::allocate(h,n,a),Heap::fresh_id(h),j)'),
        ('ctor.capacity.entry', C, 'this->capacity = n;', ['C4','C5'],
         r'\forall Heap::heap h; \forall integer r,o,n,a,v; Heap::well_formed(h) && Heap::available(h,n,a) && Heap::typed_writes(h,r,o,24,8) && 0 < n <= 4611686018427387903 ==> t25_inv(t25_allocated(h,r,o,n,a),r,o,Heap::fresh_id(h),n,0,v)'),
        ('ctor.rte.allocated_data', C, 'this->data = swdb_alloc_int(n);', ['C3','C4'],
         r'\forall Heap::heap h; \forall integer r,o,n,a; Heap::well_formed(h) && Heap::typed_writes(h,r,o,24,8) ==> Heap::typed_writes(Heap::allocate(t25_initial(h,r,o),n,a),r,o,8,8)'),
        ('ctor.rte.allocated_capacity', C, 'this->capacity = n;', ['C4'],
         r'\forall Heap::heap h; \forall integer r,o,n,a; Heap::well_formed(h) && Heap::typed_writes(h,r,o,24,8) ==> Heap::typed_writes(Heap::put_pointer(Heap::allocate(t25_initial(h,r,o),n,a),r,o,Heap::fresh_id(h),0),r,o+16,8,8)'),
        ('ctor.prefix.establish', C, 'for (size_t k = 0;', ['C5'],
         r'\forall Heap::heap h; \forall integer b,v; Heap::filled_prefix(h,b,0,v)'),
        ('ctor.store.access', C, 'this->data[k] = value;', ['C6'],
         r'\forall Heap::heap h; \forall integer r,o,b,n,k,v; t25_inv(h,r,o,b,n,k,v) && k < n ==> Heap::typed_forms(h,b,4*k,4) && Heap::typed_writes(h,b,4*k,4,4) && Heap::initialized_at(h,r,o)'),
        ('ctor.prefix.step', C, 'this->data[k] = value;', ['C6','C7'],
         r'\forall Heap::heap h; \forall integer r,o,b,n,k,v; t25_inv(h,r,o,b,n,k,v) && k < n ==> t25_inv(Heap::put_integer(h,b,4*k,v),r,o,b,n,k+1,v)'),
        ('ctor.prefix.exit', C, 'this->size = n;', ['C8'],
         r'\forall Heap::heap h; \forall integer r,o,b,n,k,v; t25_inv(h,r,o,b,n,k,v) && !(k < n) ==> k == n && Heap::filled_prefix(h,b,n,v)'),
        ('ctor.final.post', C, 'this->size = n;', ['C8'],
         r'\forall Heap::heap h; \forall integer r,o,b,n,v; t25_inv(h,r,o,b,n,n,v) ==> t25_repr(Heap::put_integer(h,r,o+8,n),r,o,b,0,n,n) && Heap::filled_prefix(Heap::put_integer(h,r,o+8,n),b,n,v)'),
        ('ctor.rte.final_size', C, 'this->size = n;', ['C8'],
         r'\forall Heap::heap h; \forall integer r,o,b,n,v; t25_inv(h,r,o,b,n,n,v) ==> Heap::typed_writes(h,r,o+8,8,8)'),
        ('ctor.frame.preexisting', C, 'this->data = swdb_alloc_int(n);', ['C3','C9'],
         r'\forall Heap::heap h; \forall integer r,o,n,a; Heap::well_formed(h) ==> t25_frame(h,t25_allocated(h,r,o,n,a),r,o)'),
        ('ctor.frame.loop_step', C, 'loop assigns k, this->data[0 .. n - 1];', ['C6','C7','C9'],
         r'\forall Heap::heap old,h; \forall integer r,o,b,k,v; t25_frame(old,h,r,o) && !Heap::live(old,b) ==> t25_frame(old,Heap::put_integer(h,b,4*k,v),r,o)'),
        ('ctor.frame.final', C, 'this->size = n;', ['C8','C9'],
         r'\forall Heap::heap old,h; \forall integer r,o,n; t25_frame(old,h,r,o) ==> t25_frame(old,Heap::put_integer(h,r,o+8,n),r,o)'),
        ('ctor.numeric', C, 'for (size_t k = 0; k < n; ++k)', ['C3','C6','C7'], None),
        ('dtor.data.read', D, 'swdb_free(this->data);', ['D1'],
         r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; t25_repr(h,r,o,b,bo,s,c) ==> Heap::typed_reads(h,r,o,8,8) && Heap::initialized_at(h,r,o) && Heap::pointer_at(h,r,o,b,bo)'),
        ('dtor.free.argument', D, 'this->capacity == 0 || \\freeable(this->data)', ['D1','D2'],
         r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; t25_repr(h,r,o,b,bo,s,c) && (c == 0 || Heap::freeable(h,b,bo)) ==> (b == 0 && bo == 0) || Heap::freeable(h,b,bo)'),
        ('dtor.null.no_op', D, 'swdb_free(this->data);', ['D2'],
         r'\forall Heap::heap h; Heap::release(h,0) == h'),
        ('dtor.alias.invalidated', D, 'swdb_free(this->data);', ['D3','D7'],
         r'\forall Heap::heap h; \forall integer b,alias_offset; b != 0 ==> !Heap::forms(Heap::release(h,b),b,alias_offset) && !Heap::reads(Heap::release(h,b),b,alias_offset,4)'),
        ('dtor.post.old_invalid', D, 'ensures \\old(this->capacity) > 0 ==> !\\valid(\\old(this->data));', ['D4'],
         r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; Heap::well_formed(h) && t25_repr(h,r,o,b,bo,s,c) && (c == 0 || Heap::freeable(h,b,bo)) && c > 0 ==> !Heap::reads(Heap::release(h,b),b,bo,4)'),
        ('dtor.frame.surviving', D, 'assigns \\nothing;', ['D5'],
         r'\forall Heap::heap h; \forall integer dead,b,o; Heap::live(h,b) && b != dead ==> Heap::contents(Heap::release(h,dead),b,o) == Heap::contents(h,b,o) && (Heap::initialized_at(Heap::release(h,dead),b,o) <==> Heap::initialized_at(h,b,o))'),
        ('dtor.frame.other_live', D, 'frees this->data;', ['D5'],
         r'\forall Heap::heap h; \forall integer dead,b; b != dead ==> Heap::same_object(h,Heap::release(h,dead),b)'),
        ('dtor.receiver.overlap', D, 'swdb_free(this->data);', ['D6'],
         r'\forall Heap::heap h; \forall integer r,o; r != 0 ==> !Heap::reads(Heap::release(h,r),r,o,24)'),
        ('control.zero_size.formation', C, 'if (n == 0) return;', ['C2','D7'],
         r'\forall Heap::heap h; \forall integer a; Heap::well_formed(h) && Heap::available(h,0,a) ==> Heap::well_formed(Heap::allocate(h,0,a)) && Heap::fresh_id(h) != 0 && Heap::typed_forms(Heap::allocate(h,0,a),Heap::fresh_id(h),0,4) && !Heap::reads(Heap::allocate(h,0,a),Heap::fresh_id(h),0,4)'),
        ('control.live_zero_base.not_fresh', C, 'ensures \\fresh(\\result, n * sizeof(int))', ['C3','D7'],
         r'\forall Heap::heap h; \forall integer b,n; Heap::live(h,b) && Heap::bytes(h,b) == 0 ==> !Heap::available(h,n,Heap::numerical_address(h,b))'),
        ('control.reused_address.stale', D, 'swdb_free(this->data);', ['D7'],
         r'\forall Heap::heap h; \forall integer b,n; Heap::well_formed(h) && Heap::freeable(h,b,0) && Heap::aligned(Heap::numerical_address(h,b),4) && 0 < n && 4*n <= Heap::bytes(h,b) ==> Heap::available(Heap::release(h,b),n,Heap::numerical_address(h,b)) && Heap::well_formed(Heap::allocate(Heap::release(h,b),n,Heap::numerical_address(h,b))) && Heap::numerical_address(Heap::allocate(Heap::release(h,b),n,Heap::numerical_address(h,b)),Heap::fresh_id(h)) == Heap::numerical_address(h,b) && !Heap::reads(Heap::allocate(Heap::release(h,b),n,Heap::numerical_address(h,b)),b,0,4)'),
        ('control.before_release.read', D, 'swdb_free(this->data);', ['D7'],
         r'\forall Heap::heap h; \forall integer b,o; Heap::reads(h,b,o,4) && Heap::initialized_at(h,b,o) ==> Heap::live(h,b)'),
        ('control.omitted_store', C, 'this->data[k] = value;', ['C6'],
         r'\forall Heap::heap h; \forall integer n,a,v; 0 < n ==> Heap::filled_prefix(Heap::allocate(h,n,a),Heap::fresh_id(h),1,v)'),
        ('control.wrong_release', D, 'swdb_free(this->data);', ['D3','D4'],
         r'\forall Heap::heap h; \forall integer b; Heap::reads(h,b,0,4) ==> !Heap::reads(Heap::release(h,0),b,0,4)'),
        ('control.stale_read', D, 'swdb_free(this->data);', ['D7'],
         r'\forall Heap::heap h; \forall integer b; b != 0 && Heap::reads(h,b,0,4) ==> Heap::reads(Heap::release(h,b),b,0,4)'),
        ('control.double_release', D, 'swdb_free(this->data);', ['D7'],
         r'\forall Heap::heap h; \forall integer b; b != 0 && Heap::freeable(h,b,0) ==> Heap::freeable(Heap::release(h,b),b,0)'),
    ]
    return rows
