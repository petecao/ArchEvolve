"""Closed caller lowering order, not a heap proof; created 2026-10-16 ET.

Bind the actual scalar-result capture and destructor placement. Never count the
unreachable fallthrough cleanup as a second executed destructor or grant an
allocation origin merely because a declaration appears in the C text.
"""
import hashlib
import re


def certify(text,function,count,receiver,alias,request,observation):
    pattern=r'\bint '+re.escape(function)+r'\(int '+re.escape(count)+r'\) \{'
    matches=list(re.finditer(pattern,text))
    if len(matches)!=1:raise ValueError('the caller needs one exact lowered function body')
    start=matches[0].end();depth=1;end=start
    while end<len(text) and depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    if depth:raise ValueError('the lowered automatic scope is incomplete')
    body=text[start:end-1]
    n,r,s=count,receiver,alias
    declaration=f'std_vector_int {r};'
    ctor=f'std_vector_int_ctor_count_value(&{r}, (unsigned long){n}, 7);'
    data=f'int *{s} = std_vector_int_data(&{r});'
    argument=f'(unsigned long){n}' if request=='count' else f'((unsigned long){n}) + 1'
    reserve=f'std_vector_int_reserve(&{r}, {argument});'
    observed=f'*std_vector_int_operator_index(&{r}, 0)' if observation=='current buffer' else f'*{s}'
    capture=f'int swdb_return = ({n} > 0) ? ({observed}) : 0;'
    dtor=f'std_vector_int_dtor(&{r});'
    returned='return swdb_return;'
    expected=declaration+ctor+data+reserve+'{'+capture+dtor+returned+'}'+dtor
    normalize=lambda t:re.sub(r'\s+','',re.sub(r'/\*.*?\*/','',t,flags=re.S))
    if normalize(body)!=normalize(expected):
        raise ValueError('the actual lowered construction/capture/cleanup order is unsupported')
    def span(begin,stop):
        raw=text[begin:stop].encode()
        return {'begin':len(text[:begin].encode()),'end':len(text[:stop].encode()),
                'sha256':hashlib.sha256(raw).hexdigest()}
    events=[]
    for name,needle in [('automatic declaration',declaration),('constructor',ctor),
                        ('data capture',data),('reserve',reserve),
                        ('guarded scalar capture',capture),('destructor',dtor),
                        ('return scalar',returned)]:
        if body.count(needle)!=(2 if name=='destructor' else 1):
            raise ValueError('a lowered caller event has no unique expected occurrence')
        begin=start+body.index(needle)
        events.append({'event':name,'lowered_source':span(begin,begin+len(needle)),
                       'reachable_on_normal_return':True})
    events.append({'event':'automatic lifetime end','lowered_source':span(end-1,end),
                   'reachable_on_normal_return':True,
                   'role':'source scope-end event to map; no dynamic-free permission or proof granted'})
    fallback=start+body.rindex(dtor)
    events.append({'event':'unreachable fallthrough destructor',
                   'lowered_source':span(fallback,fallback+len(dtor)),
                   'reachable_on_normal_return':False})
    return {'verdict':'checked source order; semantic proof pending',
            'lowered_function':function,'lowered_function_body':span(start,end-1),
            'order':[e['event'] for e in events if e['reachable_on_normal_return']],
            'events':events,'normal_return_cleanup_count':1,'unreachable_fallthrough_cleanup_count':1,
            'return_scalar_before_destruction':True,'raw_alias_rewritten':False,
            'domain_facts_assumed':[],'allocation_origins_granted':[],
            'pending':['source-local storage/image and layout embedding','all caller/model/cleanup obligations',
                       'current dependency eligibility and actual proof/task closure']}
