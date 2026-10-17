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
/*@ check lemma t25_private_integer_store_frame: \forall Heap::heap entry,now; \forall integer b,o,v; t25_private_frame(entry,now) && !Heap::live(entry,b) ==> t25_private_frame(entry,Heap::put_integer(now,b,o,v));
*/
