//@ import \wp::why3: heap_reallocation::Heap;

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

/*@ predicate t25v3_repr(Heap::heap h, integer r, integer o, integer b, integer bo,
                         integer s, integer c) =
      t25_repr(h,r,o,b,bo,s,c) && Heap::int32_region(h,b,bo,s);
    predicate t25v3_ctor_inv(Heap::heap h, integer r, integer o, integer b,
                            integer n, integer k, integer v) =
      t25_inv(h,r,o,b,n,k,v) && Heap::freeable(h,b,0) &&
      -2147483648 <= v <= 2147483647;
    predicate t25v3_eligible(Heap::heap h, integer r, integer o, integer b, integer bo,
                             integer s, integer c) =
      t25v3_repr(h,r,o,b,bo,s,c) &&
      (c == 0 || (Heap::freeable(h,b,bo) && r != b));
    predicate t25v3_copy_frame(Heap::heap entry, Heap::heap h, integer fresh) =
      Heap::fresh_id(h) == Heap::fresh_id(entry)+1 &&
      (\forall integer x; x != fresh ==> Heap::same_object(entry,h,x)) &&
      (\forall integer x,p; x != fresh ==>
        Heap::contents(entry,x,p) == Heap::contents(h,x,p) &&
        (Heap::initialized_at(entry,x,p) <==> Heap::initialized_at(h,x,p)));
    predicate t25v3_copy_inv(Heap::heap entry, Heap::heap h,
                           integer r, integer o, integer b, integer bo,
                           integer s, integer c, integer f, integer cap, integer k) =
      Heap::well_formed(entry) && Heap::well_formed(h) &&
      t25v3_eligible(entry,r,o,b,bo,s,c) && t25v3_eligible(h,r,o,b,bo,s,c) &&
      0 <= k <= s <= c < cap <= 4611686018427387903 &&
      f == Heap::fresh_id(entry) && !Heap::issued(entry,f) && f != r && f != b &&
      Heap::typed_writes(h,f,0,4*cap,4) && Heap::freeable(h,f,0) && Heap::bytes(h,f) == 4*cap &&
      t25v3_copy_frame(entry,h,f) && Heap::copied_prefix(entry,h,b,bo,f,k) &&
      (\forall integer j; k <= j < cap ==> !Heap::initialized_at(h,f,4*j));
    logic Heap::heap t25v3_grown(Heap::heap h, integer r, integer o,
                               integer old, integer fresh, integer cap) =
      Heap::put_integer(Heap::put_pointer(Heap::release(h,old),r,o,fresh,0),r,o+16,cap);
    predicate t25v3_grow_frame(Heap::heap entry, Heap::heap now,
                             integer r, integer o, integer old) =
      (\forall integer x; Heap::live(entry,x) && x != old ==>
        Heap::same_object(entry,now,x)) &&
      (\forall integer x,p; Heap::live(entry,x) && x != old &&
        !(x == r && o <= p < o+24) ==>
        Heap::contents(entry,x,p) == Heap::contents(now,x,p) &&
        (Heap::initialized_at(entry,x,p) <==> Heap::initialized_at(now,x,p)));
*/
/*@ check lemma t25v3_grow_copy_establish_destination_extent: \forall Heap::heap entry; \forall integer r,o,b,bo,s,c,cap,a; Heap::well_formed(entry) && t25v3_eligible(entry,r,o,b,bo,s,c) && c < cap <= 4611686018427387903 && Heap::available(entry,cap,a) ==> Heap::bytes(Heap::allocate(entry,cap,a),Heap::fresh_id(entry)) == 4*cap;
*/
