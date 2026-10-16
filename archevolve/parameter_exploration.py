"""Finite parameter exploration from explicit reviewed domains; no inferred ranges.

No source edits, model/API calls, executable expressions or hardware evaluation.
"""
from copy import deepcopy
from fractions import Fraction
import math

from archevolve.evolution_store import digest
from archevolve.evolution_policy import finite_number, is_sha, pareto_frontier, validate_cohort
from tools.render_mermaid import RequestError

FORMAT = 'bounded-parameter-space-v0.1'


def require(test, message):
    if not test:
        raise RequestError('Parameter exploration: ' + message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def reviewed(value, evidence):
    if value is None:
        return False
    require(isinstance(value, dict) and set(value) == {'reviewer', 'rationale', 'evidence_refs'}, 'Invalid review fields.')
    require(text(value['reviewer']) and text(value['rationale']), 'Review identity and rationale required.')
    refs = value['evidence_refs']
    require(isinstance(refs, list) and refs and all(text(r) and r in evidence for r in refs), 'Review evidence must resolve.')
    return True


def template(candidate, input_sha256, catalog_sha256, synthetic=False):
    require(text(candidate.get('id')) and candidate.get('catalog_design_id') and isinstance(candidate.get('parameter_contract'), list), 'An accelerator candidate with parameter contracts is required.')
    require(is_sha(input_sha256) and is_sha(catalog_sha256), 'Input/catalog hashes required.')
    require(type(synthetic) is bool, 'Synthetic must be explicit boolean.')
    return {'format': FORMAT, 'synthetic': synthetic, 'candidate_sha256': digest(candidate),
        'bindings': {'input_sha256': input_sha256, 'catalog_sha256': catalog_sha256},
        'budget': {'max_configurations': 64, 'max_combinations_checked': 4096},
        'parameters': [{**{k: deepcopy(p.get(k)) for k in ('id','unit','state','value','domain','claim_refs','notes')},
            'role': 'unresolved', 'legal_domain': None, 'review': None, 'software_impact': None}
            for p in candidate['parameter_contract']],
        'coupled_constraints': None, 'legality_review': None,
        'cost_model': None, 'cost_limits': {'area_mm2': None, 'power_w': None},
        'evidence': {},
        'notice': 'Reference values/domains are context, not selected values. Fill explicit reviewed domains and coupling information before enumeration.'}


def domain_values(domain):
    """Return a finite replayable sequence, never materialize an integer range."""
    require(isinstance(domain, dict), 'Domain must be a mapping or null.')
    kind = domain.get('kind')
    if kind == 'enum':
        require(set(domain) == {'kind','values'}, 'Unexpected enum domain fields.')
        values = domain['values']
        require(isinstance(values,list) and values and all(type(v) in (int,float) and math.isfinite(v) for v in values), 'Enum needs finite numeric values; booleans are not numbers here.')
        require(len(set(values)) == len(values), 'Duplicate numeric domain values.')
        return sorted(values)
    require(kind == 'integer_range' and set(domain) == {'kind','min','max','step'}, 'Use enum or bounded integer_range; no expressions.')
    lo,hi,step = domain['min'],domain['max'],domain['step']
    require(all(type(v) is int for v in (lo,hi,step)) and step > 0 and lo <= hi, 'Integer bounds and positive step required.')
    require((hi-lo)//step+1 <= 2**63-1, 'Range exceeds engine indexing capacity, not a hardware limit.')
    return range(lo,hi+1,step)


def constraint_valid(constraint, names):
    require(isinstance(constraint,dict), 'Constraint must be a mapping.')
    kind = constraint.get('kind')
    keys = {'id','kind','parameters'}
    if kind == 'product_at_most':
        keys.add('limit')
    elif kind == 'allowed_tuples':
        keys.add('values')
    require(kind in {'equal','less_equal','power_of_two','product_at_most','allowed_tuples'} and set(constraint)==keys, 'Unsupported constraint fields/kind; arbitrary code is not executed.')
    require(text(constraint['id']), 'Constraint ID required.')
    ps=constraint['parameters']
    require(isinstance(ps,list) and ps and all(text(p) and p in names for p in ps) and len(set(ps))==len(ps), 'Constraint parameters must name distinct enumerated knobs.')
    require(kind not in {'equal','less_equal'} or len(ps)==2, 'Binary constraint needs two knobs.')
    require(kind!='power_of_two' or len(ps)==1, 'Power-of-two constraint needs one knob.')
    if kind=='product_at_most':
        require(type(constraint['limit']) in (int,float) and math.isfinite(constraint['limit']), 'Product limit must be explicitly finite; otherwise leave coupling unresolved.')
    if kind=='allowed_tuples':
        rows=constraint['values']
        require(isinstance(rows,list) and all(isinstance(r,list) and len(r)==len(ps) and all(type(v) in (int,float) and math.isfinite(v) for v in r) for r in rows), 'Allowed tuples must have finite values for all named knobs.')


def constraint_passes(c, values):
    vs=[values[p] for p in c['parameters']]
    kind=c['kind']
    if kind=='equal': return vs[0]==vs[1]
    if kind=='less_equal': return vs[0]<=vs[1]
    if kind=='power_of_two': return type(vs[0]) is int and vs[0]>0 and vs[0] & (vs[0]-1)==0
    if kind=='allowed_tuples': return vs in c['values']
    # Decimal textual values use exact rational arithmetic, avoiding float-boundary acceptance.
    return math.prod(Fraction(str(v)) for v in vs) <= Fraction(str(c['limit']))


def validate_space(candidate, space):
    expected=template(candidate,space.get('bindings',{}).get('input_sha256'),space.get('bindings',{}).get('catalog_sha256'),space.get('synthetic'))
    require(set(space)==set(expected) and space['format']==FORMAT, 'Unexpected exploration-space fields.')
    require(space['candidate_sha256']==digest(candidate), 'Candidate snapshot changed; rebind the parameter space.')
    require(set(space['bindings'])==set(expected['bindings']), 'Unexpected input/catalog binding fields.')
    require(set(space['budget'])=={'max_configurations','max_combinations_checked'} and all(type(v) is int and v>0 for v in space['budget'].values()), 'Positive finite integer search budgets required.')
    require(isinstance(space['evidence'],dict) and all(text(k) and text(v) for k,v in space['evidence'].items()), 'Evidence registry needs nonempty reference/description pairs.')
    evidence={**candidate.get('source_evidence',{}).get('claims',{}), **space['evidence']}
    parameters=space['parameters']
    require(isinstance(parameters,list), 'Parameters must be a list.')
    require(all(isinstance(p,dict) and text(p.get('id')) for p in parameters), 'Parameter IDs required.')
    require(len({p['id'] for p in parameters})==len(parameters), 'Duplicate parameter IDs.')
    originals={p['id']:p for p in expected['parameters']}
    require(set(originals)=={p['id'] for p in parameters}, 'Do not add/drop catalog parameters silently; explicitly review reference_only roles.')
    unknowns=[]; domains={}
    for p in parameters:
        original=originals[p['id']]
        require(set(p)==set(original), 'Unexpected parameter fields.')
        for key in ('unit','state','value','domain','claim_refs','notes'):
            require(p[key]==original[key], 'Catalog parameter context changed: '+p['id']+'.'+key)
        require(p['role'] in {'unresolved','enumerate','reference_only'}, 'Unknown parameter role.')
        review=reviewed(p['review'],evidence)
        if p['role']=='unresolved':
            unknowns.append(p['id']+': role unresolved')
        if not review:
            unknowns.append(p['id']+': parameter binding/domain review missing')
        if p['role']=='reference_only':
            require(p['legal_domain'] is None and p['software_impact'] is None, 'Reference-only parameters cannot select values or software changes.')
        elif p['legal_domain'] is None:
            unknowns.append(p['id']+': legal domain unresolved')
        else:
            domains[p['id']]=domain_values(p['legal_domain'])
        impact=p['software_impact']
        if impact is not None:
            require(isinstance(impact,dict) and set(impact)=={'status','description','evidence_refs'}, 'Invalid software-impact record.')
            require(impact['status'] in {'requires_adaptation','no_change_reviewed'} and text(impact['description']), 'Software impact must be explicit.')
            require(isinstance(impact['evidence_refs'],list) and impact['evidence_refs'] and all(r in evidence for r in impact['evidence_refs']), 'Software impact needs evidence.')
    constraints=space['coupled_constraints']
    if constraints is None:
        unknowns.append('coupled constraints unresolved (null is not an empty reviewed set)')
    else:
        require(isinstance(constraints,list), 'Coupled constraints must be a list or null.')
        # Roles can be unresolved while reviewers draft constraints; referenced IDs must exist.
        names={p['id'] for p in parameters if p['role']!='reference_only'}
        for c in constraints: constraint_valid(c,names)
        require(len({c['id'] for c in constraints})==len(constraints),'Duplicate constraint IDs.')
    if not reviewed(space['legality_review'],evidence):
        unknowns.append('joint legality review missing')
    model=space['cost_model']
    if model is not None:
        require(isinstance(model,dict) and set(model)=={'sha256','description','evidence_refs'} and is_sha(model['sha256']) and text(model['description']), 'Invalid cost model declaration.')
        require(isinstance(model['evidence_refs'],list) and model['evidence_refs'] and all(r in evidence for r in model['evidence_refs']), 'Cost model needs evidence.')
    require(isinstance(space['cost_limits'],dict) and set(space['cost_limits'])=={'area_mm2','power_w'}, 'Invalid cost limits.')
    require(all(v is None or finite_number(v) for v in space['cost_limits'].values()), 'Cost limits must be nonnegative finite values or null.')
    return unknowns,domains


def enumerate_configurations(candidate,space):
    unknowns,domains=validate_space(candidate,space)
    result={'format':'bounded-parameter-exploration-v0.1','synthetic':space['synthetic'],
        'base_candidate_id':candidate['id'],'base_candidate_sha256':digest(candidate),'space_sha256':digest(space),
        'bindings':deepcopy(space['bindings']),'budget':deepcopy(space['budget']),
        'unknowns':unknowns,'configurations':[],'rejected':[], 'combinations_checked':0,
        'total_combinations':None,'unvisited_combinations':None,'truncated':False,
        'cost_model':deepcopy(space['cost_model']),'cost_limits':deepcopy(space['cost_limits']),
        'status':'blocked_unresolved_legality' if unknowns else 'pending_enumeration',
        'evaluation_performed':False,'selected_winner':None}
    if unknowns: return result
    names=sorted(domains)
    total=math.prod(len(domains[n]) for n in names)
    result['total_combinations']=total
    # itertools.product materializes its pools: iterate integer index tuples lazily instead.
    indexes=[0]*len(names)
    while result['combinations_checked'] < total:
        if result['combinations_checked']>=space['budget']['max_combinations_checked'] or len(result['configurations'])>=space['budget']['max_configurations']:
            break
        values={n:domains[n][indexes[i]] for i,n in enumerate(names)}
        failed=[c['id'] for c in space['coupled_constraints'] if not constraint_passes(c,values)]
        result['combinations_checked']+=1
        if failed:
            result['rejected'].append({'values':values,'failed_constraints':failed})
        else:
            identity={'base_candidate_sha256':digest(candidate),'space_sha256':digest(space),
                      'bindings':deepcopy(space['bindings']),'values':values,'synthetic':space['synthetic']}
            config_hash=digest(identity)
            pending=[p['id'] for p in space['parameters'] if p['role']=='enumerate' and
                     (p['software_impact'] is None or p['software_impact']['status']=='requires_adaptation')]
            result['configurations'].append({'id':'config-'+config_hash[:24],'sha256':config_hash,'identity':identity,
                'status':'requires_software_and_hardware_mapping_review',
                'software_handoff':{'pending_parameters':pending,'parameter_impacts':{p['id']:deepcopy(p['software_impact']) for p in space['parameters'] if p['role']=='enumerate'},
                    'original_candidate_ref':'candidate.snapshot.yaml','source_unchanged':True,
                    'required_followup':'Peter binds configuration-specific intrinsic constraints and kernel changes; Yan-Ru supplies the implementation. Eric confirms the hardware configuration.'},
                'evaluation':{'status':'not_run','latency_ms':None,'area_mm2':None,'power_w':None}})
        for i in range(len(names)-1,-1,-1):
            indexes[i]+=1
            if indexes[i]<len(domains[names[i]]): break
            indexes[i]=0
    result['unvisited_combinations']=total-result['combinations_checked']
    result['truncated']=bool(result['unvisited_combinations'])
    result['status']='bounded_configurations_pending_evaluation' if result['configurations'] else 'no_admissible_configuration_in_checked_prefix'
    if not result['truncated'] and not result['configurations']: result['status']='no_admissible_configuration_in_declared_space'
    return result


def evaluation_template(plan):
    return {'format':'parameter-evaluations-v0.1','synthetic':plan['synthetic'],
        'space_sha256':plan['space_sha256'],'bindings':deepcopy(plan['bindings']),
        'records':[], 'notice':'Supply configuration-bound implementation/build hashes and independent evaluator records; no timings are populated.'}


def evaluated_identity(config,software_sha256,hardware_sha256,build_sha256):
    require(all(is_sha(v) for v in (software_sha256,hardware_sha256,build_sha256)), 'Implementation, mapping and build hashes required.')
    return {'configuration_sha256':config['sha256'],'software_sha256':software_sha256,
            'hardware_sha256':hardware_sha256,'build_sha256':build_sha256}


def compare_evaluations(candidate,space,batch,cohort):
    """Import records only; caller/evaluator owns authenticity, trials and aggregation."""
    plan=enumerate_configurations(candidate,space)
    validate_cohort(cohort)
    expected=evaluation_template(plan)
    require(isinstance(batch,dict) and set(batch)==set(expected),'Unexpected evaluation batch fields.')
    require(type(batch['synthetic']) is bool, 'Evaluation mode must be boolean.')
    for key in ('format','synthetic','space_sha256','bindings'):
        require(batch[key]==expected[key], 'Evaluation batch binding mismatch: '+key)
    require(cohort['catalog_sha256']==space['bindings']['catalog_sha256'],'Evaluation cohort uses a different catalog.')
    if space['cost_model'] is not None:
        require(cohort['cost_model_sha256']==space['cost_model']['sha256'],'Cost model differs from declared model.')
    require(isinstance(batch['records'],list),'Evaluation records must be a list.')
    configs={c['id']:c for c in plan['configurations']}
    rows=[]; excluded={}; seen=set()
    for item in batch['records']:
        require(isinstance(item,dict) and set(item)=={'configuration_id','implementation','evaluation'},'Invalid configuration evaluation envelope.')
        cid=item['configuration_id']
        require(text(cid) and cid not in seen,'Supply one aggregated evaluation per configuration; duplicate IDs rejected.')
        seen.add(cid)
        if cid not in configs:
            excluded[cid]=['configuration_not_enumerated_for_this_space']
            continue
        config=configs[cid]; impl=item['implementation']
        require(isinstance(impl,dict) and set(impl)=={'configuration_sha256','software_sha256','hardware_sha256','build_sha256'},'Invalid implementation binding.')
        bound=evaluated_identity(config,impl['software_sha256'],impl['hardware_sha256'],impl['build_sha256'])
        row=deepcopy(item['evaluation'])
        require(isinstance(row,dict),'Evaluation must be a mapping.')
        if impl!=bound or row.get('candidate_id')!=cid or row.get('candidate_sha256')!=digest(bound):
            excluded[cid]=['configuration_or_implementation_binding_mismatch']; continue
        if row.get('synthetic') is not space['synthetic']:
            excluded[cid]=['synthetic_evidence_mode_mismatch']; continue
        # This framework evaluates accelerator configurations, never a zero-area CPU control.
        if row.get('design_role')!='accelerator_candidate':
            excluded[cid]=['configuration_requires_accelerator_role']; continue
        limit=space['cost_limits']['area_mm2']
        if limit is not None and finite_number(row.get('area_mm2')) and row['area_mm2']>limit:
            excluded[cid]=['area_limit_exceeded']; continue
        power=space['cost_limits']['power_w']
        if power is not None and (not finite_number(row.get('power_w')) or row['power_w']>power):
            excluded[cid]=['power_unknown_or_limit_exceeded']; continue
        rows.append(row)
    frontier=pareto_frontier(rows,cohort)
    frontier['excluded'].update(excluded)
    return {'format':'parameter-comparison-v0.1','synthetic':space['synthetic'],'space_sha256':digest(space),
        'cohort':deepcopy(cohort),'frontier':frontier,
        'exploration_status':plan['status'],'unresolved_legality':plan['unknowns'],
        'pending_configuration_ids':sorted(set(configs)-seen),
        'unresolved_cost_limits':[k for k,v in space['cost_limits'].items() if v is None],
        'forecast_cost_model':deepcopy(space['cost_model']),
        'selected_winner':None,'scope':'Record-level comparison of imported evidence only. No execution, inferred costs, automatic configuration activation or statistical confidence.'}
