//@ import \wp::why3: heap_reallocation::Heap;
/*@ predicate t25_private_observes(Heap::heap entry, Heap::heap left,
                                     Heap::heap right) =
      (\forall integer b; Heap::live(entry,b) ==>
        Heap::same_object(left,right,b)) &&
      (\forall integer b,p; Heap::live(entry,b) ==>
        Heap::contents(left,b,p) == Heap::contents(right,b,p) &&
        (Heap::initialized_at(left,b,p) <==> Heap::initialized_at(right,b,p)));
    predicate t25_private_frame(Heap::heap entry, Heap::heap now) =
      t25_private_observes(entry,entry,now);
    predicate t25_private_ids(Heap::heap entry, integer r, integer b) =
      !Heap::live(entry,r) && (b == 0 || (!Heap::live(entry,b) && b != r));
    logic Heap::heap t25_private_cleanup(Heap::heap now, integer r, integer b) =
      Heap::end_automatic(Heap::release(now,b),r);
*/
/*@ check lemma t25_private_cleanup_exists_scalar: \forall Heap::heap entry,now; \forall integer r,b,n; t25_private_frame(entry,now) && t25_private_ids(entry,r,b) && Heap::typed_writes(now,r,0,24,8) && !Heap::freeable(now,r,0) && 0 <= n && (n == 0 ? b == 0 : Heap::freeable(now,b,0) && Heap::int32_region(now,b,0,n) && Heap::filled_prefix(now,b,n,7)) ==> \exists Heap::heap final; \exists integer scalar; final == t25_private_cleanup(now,r,b) && scalar == (n > 0 ? Heap::load_int(now,b,0) : 0) && scalar == (n > 0 ? 7 : 0) && t25_private_frame(entry,final) && t25_private_observes(entry,now,final);
*/
