"""Optional index-generalization hypotheses, separate from minimum hardware plans.

A restricted annotation parser identifies explicit integer literals. It never
executes expressions, rewrites source or infers configurable hardware support.
"""
import ast
from copy import deepcopy
import yaml

from archevolve.evolution_store import digest
from tools.render_mermaid import RequestError


ALLOWED = (ast.Expression,ast.Name,ast.Attribute,ast.Subscript,ast.BinOp,ast.Add,ast.Sub,ast.Mult,
           ast.UnaryOp,ast.USub,ast.UAdd,ast.Constant,ast.Load,ast.BoolOp,ast.And)


def parse_annotation(expression):
    if not isinstance(expression,str) or not expression.strip():
        return None,'no_expression'
    if len(expression)>1024: return None,'expression_exceeds_parser_budget'
    try:
        tree=ast.parse(expression,mode='eval')
    except (SyntaxError,ValueError,RecursionError):
        return None,'unsupported_annotation_syntax'
    nodes=list(ast.walk(tree))
    if len(nodes)>128: return None,'expression_exceeds_parser_budget'
    if any(not isinstance(n,ALLOWED) or isinstance(n,ast.Constant) and type(n.value) is not int for n in nodes):
        return None,'unsupported_annotation_syntax'
    if any(isinstance(n,ast.BoolOp) and (n is not tree.body or not all(isinstance(v,ast.Subscript) for v in n.values)) for n in nodes):
        return None,'unsupported_annotation_syntax'
    return tree,None


def literal(node):
    if isinstance(node,ast.Constant) and type(node.value) is int: return node.value
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
        if isinstance(node.operand,ast.Constant) and type(node.operand.value) is int:
            return -node.operand.value if isinstance(node.op,ast.USub) else node.operand.value
    return None


def occurrences(node,path=()):
    if isinstance(node,ast.BinOp):
        for side,other in (('right',node.left),('left',node.right)):
            value=literal(getattr(node,side))
            if value is None or not any(isinstance(n,ast.Name) for n in ast.walk(other)): continue
            if isinstance(node.op,ast.Mult): kind='configurable_index_scale'
            elif isinstance(node.op,ast.Add) or isinstance(node.op,ast.Sub) and side=='right': kind='configurable_index_offset'
            else: continue
            yield path+(side,),value,kind
    for key,value in ast.iter_fields(node):
        if isinstance(value,ast.AST): yield from occurrences(value,path+(key,))
        elif isinstance(value,list):
            for i,child in enumerate(value):
                if isinstance(child,ast.AST): yield from occurrences(child,path+(key,i))


def replace(tree,path,value):
    result=deepcopy(tree);cursor=result
    for key in path[:-1]: cursor=cursor[key] if isinstance(key,int) else getattr(cursor,key)
    if isinstance(path[-1],int): cursor[path[-1]]=value
    else: setattr(cursor,path[-1],value)
    return ast.fix_missing_locations(result)


def observed_sites(plan,block,member):
    """Use member-bound annotations only; do not mine arbitrary surrounding code."""
    sites=[]
    if member.get('address_expression'):
        sites.append({'expression':member['address_expression'],'origin':'reported_index_expression',
                      'statement_ids':deepcopy(member.get('statement_ids',[])),
                      'source_locations':deepcopy(member.get('source_locations',[]))})
    seen=set()
    for group in plan.get('source_context_groups',[]):
        for statement in group.get('context_statements',[]):
            if statement['id'] not in member.get('statement_ids',[]) or statement['id'] in seen: continue
            seen.add(statement['id'])
            if statement.get('access_expression'):
                sites.append({'expression':statement['access_expression'],'origin':'source_context_access_expression',
                              'statement_ids':[statement['id']],'source_locations':[deepcopy(statement['location'])]})
    return sites


def propose_generalizations(plan,max_proposals=32):
    if type(max_proposals) is not int or not 1<=max_proposals<=256:
        raise RequestError('Generalization proposal budget must be an integer from 1 to 256 (engine limit, not a hardware domain).')
    if plan.get('format')!='hardware-plan-v0.1': raise RequestError('Generalization input must be a hardware plan.')
    proposals=[];diagnostics=[];eligible_sites=0
    for block in plan['blocks']:
        if block['required_capabilities']['operations']!=['read']:
            diagnostics.append({'block_id':block['id'],'reason':'side_effect_blocks_not_generalized'})
            continue
        for member in block['members']:
            sites=observed_sites(plan,block,member)
            if not sites: diagnostics.append({'request_id':member['request_id'],'reason':'no_expression'})
            for site in sites:
                tree,error=parse_annotation(site['expression'])
                if error:
                    diagnostics.append({'request_id':member['request_id'],**site,'reason':error});continue
                edits=list(occurrences(tree))
                if not edits:
                    diagnostics.append({'request_id':member['request_id'],**site,'reason':'no_supported_literal_generalization'});continue
                for path,value,kind in edits:
                    eligible_sites+=1
                    if len(proposals)>=max_proposals: continue
                    symbol='ae_offset' if kind=='configurable_index_offset' else 'ae_scale'
                    names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
                    while symbol in names: symbol+='_'  # Never capture an existing variable.
                    changed=replace(tree,path,ast.Name(id=symbol,ctx=ast.Load()))
                    # Restore the exact original AST node, including unary signs. This is
                    # a syntactic check only; C++ widths, overflow and hardware remain unproved.
                    original=tree
                    for part in path: original=original[part] if isinstance(part,int) else getattr(original,part)
                    restored=replace(changed,path,deepcopy(original))
                    if ast.dump(restored)!=ast.dump(tree): raise RequestError('Generalization did not preserve its baseline expression.')
                    identity={'plan_sha256':digest(plan),'minimum_block_id':block['id'],'request_id':member['request_id'],
                              'site':site,'ast_path':list(path),'kind':kind,'symbol':symbol,'observed_value':value}
                    proposal_id='generalization-'+digest(identity)[:20]
                    extension={'expression_language':'restricted_index_annotation_not_compilable_cpp','kind':kind,'observed_expression':site['expression'],'proposed_expression':ast.unparse(changed),
                        'parameter':{'name':symbol,'baseline_setting':value,'legal_values':None,'width_bits':None,
                                     'signedness':None,'configuration_granularity':None},
                        'computation_location':None,
                        'capability_request':'Expose the indicated literal as a configurable input while preserving the original case when set to the observed value.',
                        'scope':'One literal at one expression site only; no joint affine, datatype, atomic, ordering or concurrency expansion.'}
                    proposals.append({'id':proposal_id,'identity':identity,'status':'optional_generalization_pending_support_cost_and_legality',
                        'minimum_request':deepcopy(block),
                        'generalized_request':{'format':'capability-extension-query-v0.1','minimum_block_sha256':digest(block),
                            'base_capability_request':deepcopy(block),'requested_extension':extension},
                        'observation_basis':{'statement_binding_status':member.get('statement_binding_status'),
                            'evidence_refs':deepcopy(member.get('reported_features',{}).get('evidence_refs')),
                            'source_binding':deepcopy(plan.get('source_binding'))},
                        'additional_coverage_hypothesis':'May reuse this access pattern for other constant values, but no additional value or workload is admitted.',
                        'minimum_hardware_hardwiring_established':False,
                        'baseline_restoration':{'status':'annotation_ast_restores_observed_expression','program_equivalence_verified':False},
                        'hardware_support':None,'additional_hardware_requirements':None,'software_changes':None,
                        'additional_cost':{'area_mm2':None,'power_w':None,'latency_ms':None,'cost_model':None},
                        'cheapness_assessed':False,'legality_verified':False,'ready_for_implementation':False,
                        'selected':False,'admitted_parameter_domain':None,
                        'review_questions':[
                            'Is this arithmetic currently on the host, in an index producer, or in the proposed block?',
                            'Can the existing interface already supply this operand, or is new hardware/interface support needed?',
                            'What operand width, signedness, legal values, units, configuration lifetime and overflow/bounds rules apply?',
                            'Does the original setting preserve numeric behavior, dependencies, mutability and completion?',
                            'What is the incremental cost versus the same minimum configuration, on a common implementation/process?',
                            'Which additional workloads would actually benefit, and what evidence supports that claim?']})
    return {'format':'optional-generalizations-v0.1','kernel_id':plan['kernel_id'],'input_sha256':plan.get('input_sha256'),
        'minimum_plan_sha256':digest(plan),'policy':'single_explicit_integer_literal_in_read_index_annotation',
        'budget':{'max_proposals':max_proposals},'eligible_literal_sites':eligible_sites,'truncated':eligible_sites>len(proposals),
        'proposals':proposals,'diagnostics':diagnostics,'minimum_plan_changed':False,'catalog_changed':False,
        'scope':'Optional source-annotation hypotheses; cheapness, hardware support, legal domains and new workload coverage remain unestablished.'}


def query_pairs(report,baseline_results):
    """Existing catalog predicates cannot answer the new arithmetic capability.

    Preserve baseline coverage beside an explicit unresolved extension query.
    Never reuse a gather/stream match as evidence for configurable index arithmetic.
    """
    results={r['block_id']:r for r in baseline_results}
    pairs=[]
    for proposal in report['proposals']:
        block_id=proposal['identity']['minimum_block_id']
        if block_id not in results: raise RequestError('Missing baseline query for a generalization.')
        baseline=results[block_id]
        pairs.append({'proposal_id':proposal['id'],'minimum_block_id':block_id,
            'minimum_query':deepcopy(proposal['minimum_request']),
            'minimum_result':{'catalog_identity':deepcopy(baseline.get('catalog_identity')),'status':baseline['status'],'options':deepcopy(baseline['options']),
                              'partial_designs':deepcopy(baseline['partial_designs'])},
            'generalized_query':deepcopy(proposal['generalized_request']),
            'generalized_result':{'status':'unresolved_capability_not_expressed_by_current_catalog_predicates',
                                  'supported':None,'matching_designs':None,'hardware_requirements':None},
            'additional_cost':deepcopy(proposal['additional_cost']),
            'note':'The minimum-result matches are not evidence for the extension. Owner/evaluator response is required.'})
    return {'format':'generalization-query-pairs-v0.1','minimum_plan_sha256':report['minimum_plan_sha256'],
            'pairs':pairs,'cost_comparison_performed':False,'selected_generalization':None}


def generalization_artifacts(plan,baseline_results,max_proposals=32):
    report=propose_generalizations(plan,max_proposals);pairs=query_pairs(report,baseline_results)
    diagram=['flowchart LR','  min["Minimum observed capability request"] --> base["Existing catalog lookup"]',
        '  min --> ext["Optional configurable offset / scale"]',
        '  ext --> query["Separate extension query"]',
        '  query --> unknown["Support, implementation location and legal values unresolved"]',
        '  base --> cost["Compare incremental cost only after evidence exists"]',
        '  unknown --> cost','  cost --> review["No automatic selection or cheapness claim"]']
    lines=['# Optional generalizations for review','',report['scope'],'',
        f"Emitted {len(report['proposals'])} proposals from {report['eligible_literal_sites']} supported literal sites. Truncated: {report['truncated']}.",'',
        '| Source request | Observed annotation | Proposed annotation | Baseline setting |','|---|---|---|---|']
    def md(v): return str(v).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','\\|').replace('`','&#96;').replace('\n',' ')
    for p in report['proposals']:
        ext=p['generalized_request']['requested_extension']
        lines.append('| '+ ' | '.join(md(v) for v in (p['identity']['request_id'],ext['observed_expression'],ext['proposed_expression'],ext['parameter']['baseline_setting']))+' |')
    lines+=['','```mermaid',*diagram,'```','',
        'Annotations are not rewritten C++ or a hardware implementation. The observed setting restores the annotation AST, not a proof of program/hardware equivalence.',
        'The parameter may be supplied by existing host/interface mechanisms; no new adder, multiplier, register or cost is assumed.',
        'All hardware-support answers, additional requirements, legal domains and cost deltas remain null. Minimum catalog matches do not certify extensions.',
        '', '[Proposals](generalization-proposals.yaml) · [Paired database requests](generalization-queries.yaml)','']
    return {'generalization-proposals.yaml':yaml.safe_dump(report,sort_keys=False),
            'generalization-queries.yaml':yaml.safe_dump(pairs,sort_keys=False),
            'generalizations.mmd':'\n'.join(diagram)+'\n','generalizations.md':'\n'.join(lines)}
