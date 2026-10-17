"""Shared public CPU service fixture builders, 2026-10-06 ET."""
import hashlib
import json
import subprocess
import sys
import yaml
from conftest import run_swdb
from testkit.analytic import digest, fixture_characterization, target_description, freeze_protocol

def fact(value):
    return {'value': value, 'basis': 'reported' if value is not None else 'unknown', 'scope': 'per_call'}


def clock_case(records, tmp_path, *, cost=.1, events=4, body_counted=False, extra_selector=None, shaped=False, shaped_name="_Znam", setup=None):
    records.add_stub()
    data = fixture_characterization(records.path, subject_id='stub-impl', input_id='tiny-sym')
    data['regions'] = [{'id': 'fixture.region', 'source_location': {'function': 'fixture', 'line': 1},
        'mapped': True, 'kind': 'serial_remainder', 'access_patterns': [],
        'operation_counts': {k: fact(0 if k != 'floating_point' else 32) for k in ('integer','floating_point','branch','atomic')},
        'dynamic_counts': {'loop_iterations': fact(0)}, 'footprint_bytes': {'value': 0, 'basis': 'reported'},
        'active_workers': {'value': 1, 'basis': 'reported'}, 'worker_context': {'team_sizes': [1], 'measurement': 'Hand fixture.'},
        'accelerator_calls': [], 'address_stream_counts': {}}]
    data['unmodeled_calls'] = [{'site': 29, 'region': 'fixture.region', 'name': 'fixture.clock.abi',
        'body_counted': body_counted, 'cost_accounting': 'counted_body' if body_counted else 'opaque_callee',
        'execution_count': fact(events)}]
    if shaped:
        data['unmodeled_calls'][0]['name']=shaped_name
        data['regions'][0]['call_shape_counts']={'format':'swdb.call-shape-counts.v1','scope':'per_run','calls':[{
            'site':29,'name':shaped_name,'event':'allocation','execution_count':fact(events),
            'body_counted':False,'known_length_bins':[{'bytes':8,'execution_count':fact(1)},
                {'bytes':16,'execution_count':fact(2)}], 'allocation_lifetime_size_bins':[],
            'unknown_lengths':fact(0),'unknown_free_lifetimes':fact(0),'scope':'per_run','missing':[]}]}
    if shaped:
        data['unmodeled_calls'][0]['execution_count']['scope']='per_run'
        for call in data['regions'][0]['call_shape_counts']['calls']:
            for field in ('execution_count','unknown_lengths','unknown_free_lifetimes'):
                call[field]['scope']='per_run'
            for field in ('known_length_bins','allocation_lifetime_size_bins'):
                for item in call[field]:item['execution_count']['scope']='per_run'
    path = target_description(tmp_path)
    target = yaml.safe_load(path.read_text()); target['target'] = 'testhost'; target['mechanisms'] = target['mechanisms'][:1]
    target['mechanisms'].append({'model': 'native_service_costs', 'accounting': 'additive_overhead',
        'selector': {'domain': 'host', 'worker_scope': 'serial_T1', 'calls': [
            {'name': 'fixture.clock.abi', 'parameter': 'clock_s', 'unit': 'seconds/call'}], **(extra_selector or {})},
        'parameters': {'clock_s': {'value': cost, 'basis': 'unknown' if cost is None else 'reported',
            'source': 'Independent hand fixture only.', 'unit': 'seconds/call'}}})
    if shaped:
        service=target['mechanisms'][-1]
        service['selector']['calls']=[{'name':shaped_name,'unit':'seconds/call',
            'bin_kind':'known_length_bins','bins':[{'bytes':8,'parameter':'small_s'}, {'bytes':16,'parameter':'large_s'}],
            'scope_assumption':{'regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred'}}]
        service['parameters']={'small_s':{'value':.1,'basis':'reported','unit':'seconds/call','source':'Hand fixture8B.'},
            'large_s':{'value':.2,'basis':'reported','unit':'seconds/call','source':'Hand fixture16B.'}}
    if setup is not None:setup(data,target)
    data.pop('identity_sha256'); data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.counts.yaml',data)
    path.write_text(yaml.safe_dump(target, sort_keys=False))
    protocol = freeze_protocol(records.path, tmp_path, path, roi='fixture.stream.v1', input_id='tiny-sym')
    result = run_swdb('estimate', '--records', records.path, '--characterization', 'fixture.counts',
        '--target-description', path, '--protocol', protocol, '--id', 'fixture.cpu.estimate', '--format', 'json')
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


def save_receipt(tmp_path, data):
    data['identity_sha256'] = hashlib.sha256(json.dumps({k:v for k,v in data.items() if k!='identity_sha256'}, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    path = tmp_path / 'service-receipt.json'
    path.write_text(json.dumps(data))
    return path


def fixture_receipt():
    return {'format': 'swdb.cpu-service-calibration.v1', 'evidence_kind': 'fixture',
        'machine': 'mbit10', 'threads': 1,
        'context': {'compiler_version': 'hand fixture', 'architecture': 'fixture'},
        'settings': {'repetitions': 3},
        'services': [{'id': 'clock.now', 'unit': 'seconds/call',
            'event_definition': 'One system_clock::now call; hand fixture only.',
            'scope': {'worker_scope': 'serial', 'cache_state': 'warm'},
            'denominator': {'level': 'source_normalized_work', 'basis': 'reported',
                'proof': 'Hand-computed fixture, not native count evidence.'},
            'trials': [{'events': 10, 'gross_seconds': seconds, 'driver_seconds': 1.0,
                'order': order} for seconds, order in [(2.0, 'service_first'),
                    (2.2, 'driver_first'), (1.8, 'service_first')]]}]}



def bind(records, *args):
    return subprocess.run([sys.executable, "-m", "swdb.cpu_service_binding", "--records", str(records.path),
        *map(str, args), "--format", "json"], capture_output=True, text=True)


# Allocator v2 (2026-10-12 ET, cpu-description ticket 04): malloc and exact large bins.
def gross_allocator_resource(records,tmp_path,identifier,group,cells,receipt=None):
    """Import an allocator receipt (hand cells (operation, ABI, bytes, s/call) unless a runner receipt is given); derive its gross resource."""
    if receipt is None:receipt=hand_allocator_receipt(tmp_path,group,cells)
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',receipt,
        '--id',identifier+'.source','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    derived=subprocess.run([sys.executable,'-m','swdb.cpu_allocator_resource','--records',str(records.path),
        '--source-calibration',identifier+'.source','--id',identifier,'--fixture','--format','json'],capture_output=True,text=True)
    assert derived.returncode==0,derived.stderr+derived.stdout
    return identifier


def hand_allocator_receipt(tmp_path,group,cells):
    raw=fixture_receipt();raw['machine']='testhost'
    raw['settings'].update(group=group,sizes=sorted({c[2] for c in cells}),min_trial_s=.05,
        cells=[{'operation':op,'size_bytes':size} for op,_,size,_ in cells])
    raw['services']=[{'id':f'allocator.{op}.{size}','unit':'seconds/call','event_definition':f'Hand fixture {abi} event.',
        'scope':{'worker_scope':'serial','operation':op,'event_abi':abi,'size_bytes':size,
            'allocator_regime':'fresh_process_repeated_allocate_free_batches','transfer_basis':'inferred','payload_touch':False},
        'denominator':{'level':'source_normalized_work','basis':'reported','proof':'Hand-computed fixture, not native count evidence.'},
        'trials':[{'events':10,'gross_seconds':10*rate*k,'driver_seconds':.00001,'order':order}
            for k,order in [(1.,'service_first'),(1.1,'driver_first'),(.9,'service_first')]]} for op,abi,size,rate in cells]
    return save_receipt(tmp_path,raw)


def allocator_v2_estimate(records,tmp_path,malloc_bins,receipt=None):
    """Bind v1 + v2 gross allocator resources, then estimate a malloc / 16 MiB new[] / delete[] fixture."""
    def per_run(n):return {**fact(n),'scope':'per_run'}
    def setup(char,target):
        target['mechanisms']=target['mechanisms'][:1]
        rows=[(29,'malloc','known_length_bins',malloc_bins),
              (30,'_Znam','known_length_bins',[(16777216,1),(65536,1)]),
              (31,'_ZdaPv','allocation_lifetime_size_bins',[(16777216,1)])]
        char['unmodeled_calls']=[{'site':site,'region':'fixture.region','name':name,'body_counted':False,
            'cost_accounting':'opaque_callee','execution_count':per_run(sum(n for _,n in bins))} for site,name,_,bins in rows]
        char['regions'][0]['call_shape_counts']={'format':'swdb.call-shape-counts.v1','scope':'per_run','calls':[{
            'site':site,'name':name,'event':'allocation','execution_count':per_run(sum(n for _,n in bins)),'body_counted':False,
            'known_length_bins':[],'allocation_lifetime_size_bins':[],**{field:[{'bytes':b,'execution_count':per_run(n)} for b,n in bins]},
            'unknown_lengths':per_run(0),'unknown_free_lifetimes':per_run(0),'scope':'per_run','missing':[]} for site,name,field,bins in rows]}
    clock_case(records,tmp_path,shaped=True,setup=setup)
    target=yaml.safe_load((tmp_path/'target.yaml').read_text());target['id']='fixture.allocator.base'
    records.write('target_descriptions/fixture.allocator.base.yaml',target)
    v1=gross_allocator_resource(records,tmp_path,'fixture.allocator.v1','allocator_v1',[('new_array','_Znam',65536,.2)])
    v2=gross_allocator_resource(records,tmp_path,'fixture.allocator.v2','allocator_v2',[
        ('malloc','malloc',64,.2),('new_array','_Znam',16777216,.4),('delete_array','_ZdaPv',16777216,.1)],receipt=receipt)
    outcome=bind(records,'--target-description',target['id'],'--characterization','fixture.counts',
        '--calibration',v1,'--calibration',v2,'--id','fixture.allocator.bound','--fixture')
    assert outcome.returncode==0,outcome.stderr+outcome.stdout
    bound=json.loads(outcome.stdout)
    request=tmp_path/'allocator-v2-freeze.yaml'
    request.write_text(yaml.safe_dump({'message_version':'1.0','id':'fixture.allocator.v2.protocol','version':1,
        'settings':{'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':bound['id'],
                    'inputs':['tiny-sym'],'roi':'fixture.stream.v1','threads':1}}))
    frozen=run_swdb('freeze-protocol',request,'--records',records.path,'--format','json')
    assert frozen.returncode==0,frozen.stderr+frozen.stdout
    result=run_swdb('estimate','--records',records.path,'--characterization','fixture.counts','--target-description',
        bound['id'],'--protocol',json.loads(frozen.stdout)['id'],'--id','fixture.allocator.v2.estimate','--format','json')
    assert result.returncode==0,result.stderr+result.stdout
    estimate=json.loads(result.stdout)
    return bound,next(b for b in estimate['regions'][0]['bounds'] if b['model']=='native_service_costs')
