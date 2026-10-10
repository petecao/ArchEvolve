"""Outcome-free parameter scenarios over immutable observations. 2026-10-06 ET.
Unknown references have no numerical rank; structural gaps are never rate-fill tasks.
"""
import copy
import math
import statistics
import re
from swdb import artifacts
from swdb.analytic_count_reuse import policy_sha256


def components(regions):
    values={}
    for region in regions:
        for field in ('bounds','overheads'):
            occurrence={}
            for item in region[field]:
                occurrence[item['model']]=occurrence.get(item['model'],0)+1
                suffix='' if occurrence[item['model']]==1 else '#'+str(occurrence[item['model']])
                values[region['id']+'.'+field+'.'+item['model']+suffix]=item['seconds']
    return values


def compose(characterization,target,count_reuse,characterization_sha256):
    from swdb.analytic import _estimate_regions
    reuse=count_reuse or {'counted_target_description_sha256':artifacts.digest(target)}
    # Numeric scenarios retain the caller's immutable counted-description identity.
    def run(regions,calls):
        return _estimate_regions(regions,calls,target,characterization.get('observation_contract'),
            characterization=characterization,count_reuse=reuse,characterization_sha256=characterization_sha256)
    trials=characterization.get('trials',[])
    if not trials:
        regions,seconds=run(characterization['regions'],characterization['unmodeled_calls'])
        local=components(regions)
        return finite(seconds),{key:finite(value) for key,value in local.items()}
    totals=[];rows=[]
    for trial in trials:
        regions,seconds=run(trial['regions'],trial['unmodeled_calls'])
        totals.append(finite(seconds));rows.append({key:finite(value) for key,value in components(regions).items()})
    summary={}
    for key in sorted({key for row in rows for key in row}):
        sequence=[row.get(key,0.) for row in rows]
        summary[key]=None if any(value is None for value in sequence) else statistics.median(sequence)
    return (None if any(value is None for value in totals) else statistics.median(totals)),summary


def report(result,target,characterization):
    base_policy=policy_sha256(target)
    base_components=components(result['regions'])
    reuse=result.get('count_reuse') or {'counted_target_description_sha256':result['target_description_sha256']}
    flat=[(region['id'],field,bound) for region in result['regions']
          for field in ('bounds','overheads') for bound in region[field]]
    unknowns=[];sensitivities=[];unknown_names=set()
    for index,mechanism in enumerate(target['mechanisms']):
        for name,fact in sorted(mechanism['parameters'].items()):
            path=f'mechanisms[{index}].parameters.{name}'
            relevant=[(region,field,bound) for region,field,bound in flat if bound['model']==mechanism['model']]
            dependent=sorted({region+'.'+field+'.'+bound['model'] for region,field,bound in relevant})
            required=any(any(missing==name or missing.endswith('.'+name) for missing in bound['missing'])
                for _,_,bound in relevant)
            item={'parameter':path,'model':mechanism['model'],'value':fact['value'],
                'basis':fact['basis'],'source':fact['source'],'unit':fact['unit'],
                'dependent_bounds':dependent,'required_for_total':required,
                'priority_rank':1 if required else 2,'impact_rank':None,'impact_magnitude_seconds':None}
            value=fact['value']
            if value is None:
                unknown_names.add((mechanism['model'],name))
                item['sensitivity_state']='unknown_reference'
                unknowns.append(item);continue
            item['whole_call_seconds']={'half':None,'base':result['seconds'],'double':None}
            item['component_seconds']={'half':{},'base':base_components,'double':{}}
            item['scenario_values']={'half':None,'base':value,'double':None}
            item['scenario_target_description_sha256']={'half':None,'base':result['target_description_sha256'],'double':None}
            if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or value<=0:
                item['sensitivity_state']='invalid_numeric_reference';sensitivities.append(item);continue
            scenarios=[];failure=None
            for label,factor in (('half',.5),('double',2.)):
                changed=copy.deepcopy(target);variant=value*factor
                if not math.isfinite(variant) or variant<=0:
                    scenarios.append((label,None));failure='unsupported_numeric_scenario';continue
                changed['mechanisms'][index]['parameters'][name]['value']=variant
                item['scenario_values'][label]=variant
                if policy_sha256(changed)!=base_policy:
                    scenarios.append((label,None));failure='requires_fresh_observation';continue
                scenarios.append((label,changed))
            if any(changed is None for _,changed in scenarios):
                item['sensitivity_state']=failure
            else:
                for label,changed in scenarios:
                    seconds,local=compose(characterization,changed,reuse,result['characterization_sha256'])
                    item['whole_call_seconds'][label]=seconds
                    item['component_seconds'][label]=local
                    item['scenario_target_description_sha256'][label]=artifacts.digest(changed)
                totals=list(item['whole_call_seconds'].values())
                if all(seconds is not None for seconds in totals):
                    item['impact_magnitude_seconds']=max(abs(seconds-result['seconds']) for seconds in totals)
                    item['sensitivity_state']='whole_call_numeric_scenario'
                else:item['sensitivity_state']='local_components_only'
            sensitivities.append(item)
    magnitudes=sorted({item['impact_magnitude_seconds'] for item in sensitivities
        if item['impact_magnitude_seconds'] is not None},reverse=True)
    for item in sensitivities:
        if item['impact_magnitude_seconds'] is not None:item['impact_rank']=magnitudes.index(item['impact_magnitude_seconds'])+1
    structural={}
    for region,field,bound in flat:
        for missing in bound['missing']:
            if missing=='composition.required_resource_unknown':continue
            if any(model==bound['model'] and (missing==name or missing.endswith('.'+name)) for model,name in unknown_names):continue
            row=structural.setdefault(missing,{'missing':missing,'regions':set(),'models':set(),'formulas':set(),
                'required_for_total':True,'parameter_fill_allowed':False,'impact_rank':None,'impact_magnitude_seconds':None})
            row['regions'].add(region);row['models'].add(bound['model']);row['formulas'].add(bound['formula'])
    structural_rows=[]
    for _,row in sorted(structural.items()):
        structural_rows.append({**row,**{field:sorted(row[field]) for field in ('regions','models','formulas')}})
    return {'format':'swdb.parameter-sensitivity.v1','basis':'estimated',
        'target_description_sha256':result['target_description_sha256'],'observation_policy_sha256':base_policy,
        'unknowns':sorted(unknowns,key=lambda item:(item['priority_rank'],item['parameter'])),
        'sensitivities':sensitivities,'structural_missing':structural_rows,
        'notes':['A null reference has no defensible halve/double magnitude or numerical impact rank; required unknowns share dependency priority.',
            'Numeric scenarios change one positive parameter at a time and recompose each full trial before its median; local component medians are diagnostic.',
            'Only an identical complete observation policy permits count reuse. Structural/layout/window/placement/backend changes require fresh observations.',
            'Scenarios are estimated analytic premises over frozen counts, never timing outcomes or new frozen target versions.',
            'Missing source facts, mechanisms, costs and composition policies are distinct from numeric parameter-fill tasks.']}


def finite(value):
    return value if value is None or math.isfinite(value) else None


def payload_problems(data):
    report=data.get('parameter_report')
    if report is None:return
    target=data['target_description_snapshot']
    if report['target_description_sha256']!=data['target_description_sha256'] or report['observation_policy_sha256']!=policy_sha256(target):
        yield 'parameter_report','report differs from its frozen target/observation policy'
    seen=set()
    for group in ('unknowns','sensitivities'):
        for row in report[group]:
            path=row['parameter'];match=re.fullmatch(r'mechanisms\[([0-9]+)\]\.parameters\.(.+)',path)
            try:
                mechanism=target['mechanisms'][int(match[1])];fact=mechanism['parameters'][match[2]]
                if row['model']!=mechanism['model'] or any(row[key]!=fact[key] for key in ('value','basis','source','unit')):raise ValueError()
            except (IndexError,KeyError,ValueError,TypeError):
                yield 'parameter_report.'+group,'parameter differs from its frozen target fact: '+path
            if path in seen:yield 'parameter_report','duplicate parameter report identity: '+path
            seen.add(path)
            if group=='sensitivities' and row['whole_call_seconds']['base']!=data['seconds']:
                yield 'parameter_report.sensitivities','base scenario differs from frozen whole-call estimate'
    def numbers(value):
        if isinstance(value,dict):
            for child in value.values():yield from numbers(child)
        elif isinstance(value,list):
            for child in value:yield from numbers(child)
        elif isinstance(value,(int,float)) and not isinstance(value,bool):yield value
    if any(not math.isfinite(value) for value in numbers(report)):
        yield 'parameter_report','sensitivity values must be finite or null'
