import hashlib,json,pathlib,sys,statistics
W=pathlib.Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve')
sys.path.insert(0,str(W/'swdb-project'))
from swdb import access,artifacts
admission_path=pathlib.Path('/private/tmp/lanl-cpu-holdout-a3-local-admission-20261007.json')
a=json.loads(admission_path.read_text())
assert a['identity_sha256']==artifacts.digest({k:v for k,v in a.items() if k!='identity_sha256'})
assert a['admitted'] is True and a['phase']=='holdout'
rows=[]
for actual in a['outcomes']:
    k=actual['kernel'];p=W/'swdb-project/records/estimates'/('lanl.cpu.'+k+'.g17.t1.estimate.v1.yaml')
    estimate=access.read_record(p)
    assert estimate['seconds']==actual['predicted_seconds']
    assert artifacts.digest(estimate['regions'])==actual['estimate_regions_sha256']
    ts=sorted(estimate['trials'],key=lambda t:(t['seconds'],t['position']))
    trial=ts[2]
    assert trial['seconds']==estimate['seconds']
    top=[];model_totals={};request_totals={};region_sum=0.
    for r in trial['regions']:
        assert r['state']=='known' and r['seconds'] is not None
        region_sum+=r['seconds']
        maximum=max((x['seconds'] for x in r['bounds']),default=0.)
        assert r['seconds']==maximum+sum(x['seconds'] for x in r['overheads'])
        limits=[x['model'] for x in r['bounds'] if x['seconds']==maximum]
        chosen=next((x for x in r['bounds'] if x['model']==r['limiting_bound']),None)
        if chosen is not None:model_totals[chosen['model']]=model_totals.get(chosen['model'],0)+chosen['seconds']
        for x in r['overheads']:model_totals['additive:'+x['model']]=model_totals.get('additive:'+x['model'],0)+x['seconds']
        memory=next((x for x in r['bounds'] if x['model']=='memory_service_scenario'),None)
        cells=[]
        if memory:
            for item in memory['inputs']['requests']:
                for profile in item['source_primitive_profiles']:
                    n=profile['requests'];rate=profile['seconds_per_request'];c=profile['construction']
                    key=(item['update_kind'],item['element_bytes'],profile['primitive'],c['footprint_bytes'])
                    agg=request_totals.setdefault(str(key),{'update_kind':key[0],'element_bytes':key[1],'primitive':key[2],'footprint_bytes':key[3],'requests':0,'constructed_seconds':0.,'seconds_per_request':rate})
                    agg['requests']+=n;agg['constructed_seconds']+=n*rate
                    cells.append({'update_kind':key[0],'element_bytes':key[1],'primitive':key[2],'requests':n,'seconds_per_request':rate,'constructed_seconds':n*rate,'footprint_bytes':c['footprint_bytes']})
        top.append({'id':r['id'],'predicted_seconds':r['seconds'],'share_of_selected_trial':r['seconds']/trial['seconds'],'limiting_bound':r['limiting_bound'],'bounds':[{'model':x['model'],'seconds':x['seconds']} for x in r['bounds']],'additive_overheads':[{'model':x['model'],'seconds':x['seconds']} for x in r['overheads']],'memory_cells':sorted(cells,key=lambda c:c['constructed_seconds'],reverse=True)[:5]})
    assert abs(region_sum-trial['seconds'])<1e-12
    rows.append({'kernel':k,'prediction_seconds':estimate['seconds'],'native_median_seconds':actual['native_median_seconds'],'prediction_over_native':estimate['seconds']/actual['native_median_seconds'],'estimate_file_sha256':access.record_hash(p),'estimate_sha256':artifacts.digest(estimate),'selected_median_prediction_trial':trial['position'],'selected_trial_sources':trial['sources'],'region_seconds_sum':region_sum,'limiting_resource_plus_additive_totals':model_totals,'top_predicted_regions':sorted(top,key=lambda r:r['predicted_seconds'],reverse=True)[:7],'source_request_construction_totals':sorted(request_totals.values(),key=lambda r:r['constructed_seconds'],reverse=True),'measured_region_seconds_available':False})
result={'format':'swdb.cpu-holdout-region-diagnostic.v1','source_commit':a['source_commit'],'estimator_sha256':a['estimator_sha256'],'actual_holdout_admission_identity':a['identity_sha256'],'kernels':rows,'scope':'Diagnostic decomposition of already frozen forecasts after accepted held-out admission only; no measured region timing, cost fitting, rate/recipe/band change or additional outcome collection. Per-region values use the actual median forecast trial, so components sum that forecast; display medians across regions are not substituted.','store_or_native_or_provider_or_remote_invocations':0}
result['identity_sha256']=artifacts.digest(result)
out=pathlib.Path('/private/tmp/lanl-cpu-holdout-region-error-diagnostic-20261007.json')
assert not out.exists()
out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'output':str(out),'identity_sha256':result['identity_sha256'],'kernels':[{'kernel':r['kernel'],'median_prediction_trial':r['selected_median_prediction_trial'],'resource_totals':r['limiting_resource_plus_additive_totals'],'top_regions':[{'id':x['id'],'seconds':x['predicted_seconds'],'share':x['share_of_selected_trial'],'limiting':x['limiting_bound']} for x in r['top_predicted_regions']],'construction_cells':r['source_request_construction_totals']} for r in rows]},indent=2))
