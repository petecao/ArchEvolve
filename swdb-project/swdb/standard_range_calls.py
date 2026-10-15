"""Original-TU primitive std::copy range discharge; created 2026-10-15 ET.

Roots are C++ declarations or explicit entry windows, never allocation addresses.
Numeric bounds are named WP obligations; initialization/separation remain model
requires. Only exact standalone int-copy calls and stable source bindings qualify.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb import standard_range_model


class Refused(ValueError):
    pass


def identity():
    return {'id':'standard-range-calls-1','sha256':hashlib.sha256(
        Path(__file__).read_bytes()+standard_range_model.identity()['sha256'].encode()).hexdigest()}


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def site(node, *, statement, anchor, function, line, model, target):
    from swdb import wp_pointer_bounds as bounds
    row=bounds.call_site(node,statement=statement,anchor=anchor,function=function,line=line)
    row['reason']=row['reason'].replace('DX100 window','std::copy range')
    row['model']=model
    row['binding']={'name':target.get('name'),'signature':(target.get('type') or {}).get('qualType'),
                    'mangled_name':target.get('mangledName'),
                    'file':(target.get('loc') or {}).get('_file',(target.get('loc') or {}).get('file'))}
    return row


def _children(node):
    return [c for c in node.get('inner',[]) if isinstance(c,dict) and c.get('kind')]


def _declaration(origins, node, function):
    ref=node.get('referencedDecl') or {}
    declaration=origins.declarations.get(function,{}).get(ref.get('id'))
    if declaration is None and ref.get('kind')=='VarDecl':
        declaration=origins.globals.get(ref.get('name'))
    if declaration is None:
        raise Refused('std::copy pointer has no stable source declaration origin')
    return declaration


def _origin(node, function, origins, seen=()):
    from swdb import wp_pointer_bounds as bounds
    node=bounds._strip_origin(node)
    children=_children(node)
    if 'volatile' in str((node.get('type') or {}).get('qualType','')):
        raise Refused('std::copy volatile pointer has no stable source origin')
    if node.get('kind')=='BinaryOperator' and node.get('opcode') in {'+','-'}:
        pointers=[c for c in children if bounds._pointer(c)]
        scalars=[c for c in children if not bounds._pointer(c)]
        if len(pointers)!=1 or len(scalars)!=1 or node.get('opcode')=='-' and children[0] is not pointers[0]:
            raise Refused('std::copy endpoint needs one typed pointer and a pure integer offset')
        result=_origin(pointers[0],function,origins,seen)
        try: offset=bounds._scalar_math(scalars[0])
        except bounds.Refused as exc: raise Refused('std::copy offset: '+str(exc)) from None
        return {**result,'offset':f'({result["offset"]} {node["opcode"]} {offset})'}
    if node.get('kind')!='DeclRefExpr':
        raise Refused('std::copy endpoint has no certified one-dimensional source origin')
    declaration=_declaration(origins,node,function)
    key=declaration.get('id')
    if key in seen or (function,key) in origins.unstable:
        raise Refused('std::copy pointer binding is not stable throughout the retained source closure')
    qual=str((declaration.get('type') or {}).get('qualType',''))
    if declaration.get('kind')=='VarDecl' and bounds._pointer(declaration):
        initializers=_children(declaration)
        if declaration.get('storageClass') or len(initializers)!=1:
            raise Refused('std::copy alias lacks one checked stable automatic initializer')
        initializer=bounds._strip_origin(initializers[0])
        if initializer.get('kind')=='BinaryOperator' and any(
                n.get('kind')=='DeclRefExpr' and not bounds._pointer(n) and
                not re.fullmatch(r'(?:const )?int\s*\[\d+\]',str((n.get('type') or {}).get('qualType','')))
                for n in bounds._walk(initializer)):
            raise Refused('std::copy alias offset needs a stable captured scalar value')
        return _origin(initializers[0],function,origins,(*seen,key))
    try: known=origins.get(node,function)
    except bounds.Refused as exc: raise Refused(str(exc)) from None
    if known is None:
        raise Refused('std::copy pointer has no stable certified source origin')
    match=re.fullmatch(r'(?:const )?int\s*\[(\d+)\]',qual)
    if match and int(match[1])>0 and declaration.get('storageClass')!='extern':
        root={'function':function,'name':declaration['name'],'declaration':bounds._span(declaration),
              'kind':'one_dimensional_array','element_type':'int','type':qual}
        return {'root':root,'element_type':'int','elements':match[1],'offset':'0'}
    if declaration.get('kind')=='ParmVarDecl' and known.get('kind')=='entry_window' and known['element_type']=='int':
        root={'function':function,'name':declaration['name'],'declaration':bounds._span(declaration),
              'kind':'entry_window','element_type':'int','declarations_sha256':known['declarations_sha256']}
        return {'root':root,'element_type':'int','elements':known['elements'],'offset':'0'}
    raise Refused('std::copy root is outside the exact int one-dimensional/entry-window origin policy')


def _predicate(first,last,destination):
    f,l,d=(row['offset'] for row in (first,last,destination))
    count=f'(({l}) - ({f}))'
    return (f'0 <= ({f}) <= ({l}) <= ({first["elements"]}) && '
            f'0 <= {count} <= PTRDIFF_MAX && 0 <= ({d}) && '
            f'(({d}) + {count}) <= ({destination["elements"]})')


def certify(sites, definitions, origins):
    """Independently bind printed model calls to every retained original call AST."""
    from swdb import c_lowering, wp_pointer_bounds as bounds
    if not sites:return []
    recorded={(s['function'],s['_ast_id']):s for s in sites}
    rows=[];found=set()
    for function,root in definitions.items():
        for node in bounds._walk(root):
            children=_children(node)
            if node.get('kind')!='CallExpr' or not children:continue
            names=[(n.get('referencedDecl') or {}).get('name') for n in bounds._walk(children[0])]
            if 'copy' not in names:continue
            key=(function,node.get('id'));found.add(key)
            original=recorded.get(key)
            row={k:v for k,v in (original or {}).items() if not k.startswith('_')}
            row.update(kind='standard_range_call',function=function,reason=(original or {}).get('reason',''))
            try:
                if not original:
                    raise Refused('copy-named source call has no exact standard-model binding')
                if row['reason']:raise Refused(row['reason'])
                if row.get('model')!=standard_range_model.NAME or len(children)!=4:
                    raise Refused('only exact std_copy_int calls have a qualified range body proof')
                target=bounds._strip_origin(children[0])
                if target.get('kind')=='ImplicitCastExpr' and target.get('castKind')=='FunctionToPointerDecay':
                    target=_children(target)[0]
                ref=target.get('referencedDecl') or {}
                if (target.get('kind')!='DeclRefExpr' or ref.get('name')!='copy'
                        or ref.get('type',{}).get('qualType')!=row['binding']['signature']
                        or not str(row['binding'].get('mangled_name','')).startswith(('_ZNSt','__ZNSt'))):
                    raise Refused('std::copy original target signature/standard binding changed')
                if bounds._span(node)!=row.get('source_range'):
                    raise Refused('std::copy original call source range changed')
                first,last,destination=(_origin(arg,function,origins) for arg in children[1:])
                if first['root']!=last['root']:
                    raise Refused('std::copy input endpoints must bind the same typed array root/subobject')
                row.update(first=first,last=last,destination=destination,
                    predicate=_predicate(first,last,destination),policy=identity(),
                    model_sha256=hashlib.sha256(c_lowering.model_text(standard_range_model.NAME).encode()).hexdigest(),
                    qualification=standard_range_model.identity())
                row['certificate_sha256']=_digest({k:v for k,v in row.items() if k!='certificate_sha256'})
            except (Refused,bounds.Refused) as exc:
                row['reason']=str(exc)
            rows.append(row)
    for key,original in recorded.items():
        if key not in found:
            rows.append({'kind':'standard_range_call','function':key[0],'source_line':original.get('source_line'),
                         'reason':'printed std::copy call has no original-source AST counterpart'})
    return rows


def check_row(row):
    from swdb import c_lowering
    certificate=dict(row);digest=certificate.pop('certificate_sha256',None)
    if (row.get('policy')!=identity() or row.get('qualification')!=standard_range_model.identity()
            or row.get('model')!=standard_range_model.NAME or digest!=_digest(certificate)
            or row.get('model_sha256')!=hashlib.sha256(c_lowering.model_text(standard_range_model.NAME).encode()).hexdigest()
            or row.get('first',{}).get('root')!=row.get('last',{}).get('root')
            or row.get('predicate')!=_predicate(row['first'],row['last'],row['destination'])):
        raise Refused('std::copy caller range certificate, roots or numerical predicate changed')


def check_caller(lowering):
    from swdb import wp_pointer_bounds
    rows=[row for row in lowering.pointer_bounds.get('sites',[]) if row.get('kind')=='standard_range_call']
    if not rows:raise Refused('std_copy_int requires checked caller typed-range discharge')
    wp_pointer_bounds.check(lowering)
    if getattr(lowering,'stdlib_provenance',{}).get('verdict')!='passed':
        raise Refused('std_copy_int caller typed-range discharge requires passed original-TU standard-library provenance')
    for row in rows:check_row(row)
    return _digest(rows)


def bind_dependency(adapter, record_id, directory):
    """Bind a currently eligible model proof to its fresh qualification and bytes."""
    from swdb import c_lowering, yamlio
    from swdb.store import Store
    store=Store(adapter.records)
    relative=store.path_of(record_id)
    if relative is None:raise Refused('qualified std_copy_int proof record disappeared')
    path=Path(adapter.records)/relative
    data=yamlio.load(path)
    if data!=store.get(record_id,'proof'):
        raise Refused('qualified std_copy_int proof record differs from fresh YAML bytes')
    sha=hashlib.sha256(c_lowering.model_text(standard_range_model.NAME).encode()).hexdigest()
    if adapter._proven('c_model',standard_range_model.NAME,sha)!=record_id:
        raise Refused('std_copy_int qualification no longer has the selected current eligible WP proof')
    view=standard_range_model.wp_view(standard_range_model.NAME,c_lowering.model_text(standard_range_model.NAME),directory)
    pins=data.get('pins') or {}
    if ((data.get('settings') or {}).get('standard_range_model')!=view.certificate
            or any(pins.get(name)!=pin for name,pin in view.pins.items())):
        raise Refused('std_copy_int model proof lacks its exact current typed-range qualification')
    return {'proof_record':record_id,'path':str(path),'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'qualification':view.pins['standard_range_model_certificate'],'check':identity()}


def recheck(adapter, context, lowering, directory):
    """Regenerate the caller source elsewhere; here replay domain and proof binding."""
    if standard_range_model.NAME not in getattr(lowering,'models',()):return None
    plan=context.get('standard_range_calls')
    if not plan or plan.get('caller_sha256')!=check_caller(lowering):
        raise Refused('std_copy_int caller source range plan is missing or changed')
    fresh=bind_dependency(adapter,plan['dependency']['proof_record'],directory)
    if fresh!=plan['dependency']:
        raise Refused('std_copy_int qualified proof bytes or domain changed before launch')
    expected=[pin for pin in context.get('pins',{}).get('models',[]) if pin.get('id')==standard_range_model.NAME]
    if len(expected)!=1 or expected[0].get('proof_record')!=fresh['proof_record']:
        raise Refused('std_copy_int caller dependency differs from its qualified proof binding')
    if context.get('pins',{}).get('standard_range_call_check')!=identity():
        raise Refused('std_copy_int caller policy pin is missing or stale')
    return _digest(plan)
