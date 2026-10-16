"""Pending source-local caller lifetime duties; created 2026-10-16 ET.

The closed AST checker binds declaration/data/return events. These formulas do
not grant origins or assume any global pointer history/ownership invariant.
"""


def prepare(candidate):
    hnew = 'Heap::begin_automatic(h,24,a)'
    fresh = 'Heap::fresh_id(h)'
    clauses = [
      ('local.begin.feasible', ['L1'], 'receiver',
       r'Heap::well_formed(Heap::empty(0)) && Heap::automatic_available(Heap::empty(0),24,8,8) && '
       r'Heap::typed_writes(Heap::begin_automatic(Heap::empty(0),24,8),1,0,24,8) && '
       r'!Heap::freeable(Heap::begin_automatic(Heap::empty(0),24,8),1,0)'),
      ('local.begin.storage', ['L1'], 'receiver',
       r'\forall Heap::heap h; \forall integer a; Heap::well_formed(h) && '
       r'Heap::automatic_available(h,24,8,a) ==> Heap::well_formed(' + hnew + ') && '
       'Heap::typed_writes(' + hnew + ',' + fresh + ',0,24,8) && '
       '!Heap::freeable(' + hnew + ',' + fresh + ',0) && '
       '(\forall integer p; !Heap::initialized_at(' + hnew + ',' + fresh + ',p))'),
      ('local.begin.history', ['L1','B1'], 'receiver',
       r'\forall Heap::heap h; \forall integer b; Heap::well_formed(h) && Heap::issued(h,b) ==> '
       r'b != Heap::fresh_id(h)'),
      ('local.begin.frame', ['L1'], 'receiver',
       r'\forall Heap::heap h; \forall integer a,b,p; Heap::well_formed(h) && Heap::live(h,b) ==> '
       'Heap::same_object(h,' + hnew + ',b) && Heap::contents(h,b,p) == Heap::contents(' + hnew + ',b,p) && '
       '(Heap::initialized_at(h,b,p) <==> Heap::initialized_at(' + hnew + ',b,p))'),
      ('local.begin.dead_aliases', ['L1','L2'], 'receiver',
       r'\forall Heap::heap h; \forall integer a,b,p; Heap::well_formed(h) && Heap::issued(h,b) && '
       '!Heap::live(h,b) ==> !Heap::forms(' + hnew + ',b,p) && !Heap::can_read(' + hnew + ',b,p,4)'),
      ('local.end.aliases', ['L2'], 'dtor',
       r'\forall Heap::heap h; \forall integer r,p; Heap::live(h,r) ==> '
       r'!Heap::forms(Heap::end_automatic(h,r),r,p) && !Heap::can_read(Heap::end_automatic(h,r),r,p,4)'),
      ('local.end.frame', ['L2'], 'dtor',
       r'\forall Heap::heap h; \forall integer r,b,p; b != r ==> '
       r'Heap::same_object(h,Heap::end_automatic(h,r),b) && '
       r'Heap::contents(h,b,p) == Heap::contents(Heap::end_automatic(h,r),b,p) && '
       r'(Heap::initialized_at(h,b,p) <==> Heap::initialized_at(Heap::end_automatic(h,r),b,p))'),
      ('caller.data.read', ['A1'], 'data',
       r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; t25v3_repr(h,r,o,b,bo,s,c) ==> '
       r'Heap::typed_reads(h,r,o,8,8) && Heap::initialized_at(h,r,o) && Heap::pointer_at(h,r,o,b,bo)'),
      ('caller.guard.empty', ['U1','U2'], 'read',
       r'\forall integer n; n == 0 ==> !(n > 0)'),
      ('caller.guard.nonempty', ['U1','U2'], 'read',
       r'\forall Heap::heap h; \forall integer r,o,b,bo,n,c; t25v3_repr(h,r,o,b,bo,n,c) && n > 0 ==> '
       r'Heap::typed_forms(h,b,bo,4) && Heap::int32_at(h,b,bo)'),
    ]
    calls = {row['call']: row['source'] for row in candidate['call_obligations']}
    sources = {**calls, 'receiver':candidate['receiver']['source'],
               'read':candidate['scalar_read_obligation']['source']}
    return {'preparation_only':True, 'caller_premises_added':[], 'incoming_pointer_maps_restricted':False,
            'pointer_history_scope':'only source-created local storage and the explicit data capture; no global map premise',
            'source_binding':'closed declaration/data/guard/return AST and exact lowered cleanup order remain to be checked before proof',
            'obligations':[{'id':name,'source_groups':groups,'source':sources[event],
                            'statement':statement,'status':'pending','dependencies':[]}
                           for name,groups,event,statement in clauses],
            'missing':['exact ordinary contract and model-dependency admission',
                       'source-local embedding/cleanup and target layout independent review',
                       'full constructor/reserve/copy/observation/destructor composition and final incoming frame',
                       'actual type/import/task-closure checks and fresh normal-reader proofs']}
