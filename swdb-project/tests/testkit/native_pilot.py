"""The one-thread pilot's completed-reader fixture and DX100 capacity text builders.
Created 2026-10-05 ET (code review T1), from tests/test_bfs_native_one_thread_pilot.py
and tests/test_dx100_capacity.py. Synthetic, never calibration."""

import copy
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from scripts import bfs_native_one_thread_pilot as client
from swdb import artifacts, yamlio
from swdb.store import Store


def plan():
    return yamlio.load(client.PLAN)


def write_ref(path, value):
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    return client.ref(path)


def build_reader_fixture(tmp_path,monkeypatch):
    # The orchestrator reader is tested independently from raw BFS correctness;
    # pair validation is replaced with an explicitly synthetic failing A/A grid.
    value=plan(); real=Store(client.ROOT/'records'); records={}; checks={}
    class Records:
        def get(self,rid,*args): return records[rid] if rid in records else real.get(rid,*args)
    store=Records(); began=datetime(2026,9,26,14,tzinfo=client.ET); ended=began+timedelta(seconds=10)
    runtime={'python':{'path':sys.executable},'fixture_only':True}
    monkeypatch.setattr(client,'runtime_identity',lambda _:runtime)
    monkeypatch.setattr(client,'prerequisites',lambda *args:{'fixture_only':True})
    monkeypatch.setattr(client,'validate_pair_result',lambda store,first,pair,*args:copy.deepcopy(checks[pair['id']]))
    stages=[]; cells=[]; capacities=[]; machine=store.get('mbit10','machine')
    raw_capacity={'node':node(30*1024**2),'zones':zone(),'global':f'MemAvailable: {40*1024**2} kB','pressure':'fixture'}
    estimate=client.dx100_capacity.capacity(raw_capacity['node'],raw_capacity['zones'],raw_capacity['global'],1,4096)
    for i,cell in enumerate(value['cells']):
        first=store.get(cell['first_evaluation'],'evaluation')
        req=client.pair_request(first,cell,machine,value)
        pair={'id':cell['id'],'request':req,'fixture_only':True,
            'started':(began+timedelta(seconds=2*i+1.02)).isoformat(),
            'prepared_at':(began+timedelta(seconds=2*i+1.04)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+1.08)).isoformat()}; records[pair['id']]=pair
        checks[pair['id']]={'samples':{'fixture_only':True},'control':{'unmet_gates':['synthetic spread failure'],
            'gain_claim':False},'members':{'fixture_only':True}}
        resolved=Path(first['build']['compiler']).resolve(strict=True)
        cells.append({'id':pair['id'],'pair_sha256':artifacts.digest(pair),**checks[pair['id']],
                      'compiler':{'compiler_resolved':str(resolved),'compiler_sha256':artifacts.file_hash(resolved)}})
        request=write_ref(tmp_path/f'request{i}',req); output=write_ref(tmp_path/f'out{i}',pair)
        error=write_ref(tmp_path/f'err{i}','')
        compiler=write_ref(tmp_path/f'compiler{i}','\n'.join(first['build']['compiler_version'])+'\n')
        stages.append({'command':[first['build']['compiler'],'--version'],'output':compiler['path'],
            'stdout_sha256':compiler['sha256'],'stderr':error['path'],'stderr_sha256':error['sha256'],
            'state':'complete','returncode':0,'cleanup':{'state':'all_owned_descendants_absent'},
            'host_wall_s':.1,'ceiling_seconds':60,'phase':'primary',
            'started':(began+timedelta(seconds=2*i+.1)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+.2)).isoformat()})
        stages.append({'command':[sys.executable,'-m','swdb','evaluate-pair',request['path'],'--runs-dir',str(tmp_path),
            '--records',str(client.ROOT/'records'),'--format','json'],'request':request,'output':output['path'],
            'stdout_sha256':output['sha256'],'stderr':error['path'],'stderr_sha256':error['sha256'],
            'state':'complete','returncode':0,'cleanup':{'state':'all_owned_descendants_absent'},
            'host_wall_s':.1,'ceiling_seconds':2460,'phase':'primary',
            'started':(began+timedelta(seconds=2*i+1)).isoformat(),
            'finished':(began+timedelta(seconds=2*i+1.1)).isoformat()})
        capacities.append({'inputs':raw_capacity,'estimate':estimate,'native_eligible':True,
            'required_bytes':{'node':20*1024**3,'global':24*1024**3},'command':stages[-1]['command'],
            'observed_at':(began+timedelta(seconds=2*i+.9)).isoformat()})
    for index,stage in enumerate(stages):
        stage.update(pid=200+index,identity={'pid':200+index,'start_ticks':1000+index,'parent_pid':123})
    row={'sampled_at':(began+timedelta(seconds=1)).isoformat(),'rss_bytes':4096,
        'rss_source':value['rss_source'],'page_size_bytes':4096,'guard_seconds':.001,
        'processes':[{'pid':123,'start_ticks':100,'parent_pid':99,'state':'S','rss_bytes':4096,'rss_pages':1}],
        'total_raw_bytes':100,'phase_raw_bytes':100,'build_bytes':10,'raw_free_bytes':40*1024**3,'build_free_bytes':15*1024**3,
        'lane':{'verified_lane':'mbit10-evaluation-node1 (verified: affinity, bind:1, lease held, generation 1)'}}
    rows=[copy.deepcopy(row),copy.deepcopy(row)]
    rows[-1]['sampled_at']=(ended-timedelta(seconds=1)).isoformat()
    for sample in rows:
        stamp=client.witness.stamp(sample['sampled_at'])
        sample.update(guard_started=stamp.isoformat(),guard_finished=(stamp+timedelta(seconds=.001)).isoformat())
    samples=write_ref(tmp_path/'samples','\n'.join(map(json.dumps,rows))+'\n')
    admission=write_ref(tmp_path/'admission',{'code_commit':'a'*40,'plan_sha256':client.PLAN_SHA,'prepared_at':began.isoformat()})
    receipt={'id':client.RUN_ID,'state':'primary_unqualified','repository_commit':'a'*40,
        'plan_canonical_sha256':client.PLAN_SHA,'bounds':value['bounds'],'native_runtime':value['native_runtime'],
        'python_environment':client.PYTHON_INPUTS,
        'gain_claim':False,'protocol_freeze':False,'provider_calls':False,'runtime':runtime,
        'plan':write_ref(tmp_path/'plan',value),'started':began.isoformat(),'finished':ended.isoformat(),
        'outer_start':began.isoformat(),'outer_end':(began+timedelta(seconds=18240)).isoformat(),'host_wall_s':10,
        'cleanup':{'state':'all_owned_descendants_absent','subreaper':True},'final_accounting':{**row,'observed_at':ended.isoformat()},
        'admission':admission,'rss':{'source':value['rss_source'],'samples':samples,'peak_bytes':4096},
        'driver_pid':123,'stages':stages,'capacity':capacities,'cells':cells,'primary_qualified':False,
        'process_observations':{'driver_identity':{'pid':123,'start_ticks':100,'parent_pid':99},
            'pane_identity':{'pid':99,'start_ticks':90},'ancestry':[{'pid':123,'start_ticks':100,'parent_pid':99},
                {'pid':99,'start_ticks':90,'parent_pid':1}],
            'owned_processes':[{'pid':123,'start_ticks':100}]+[stage['identity'] for stage in stages]},
        'runs_dir':str(tmp_path),'records':str(client.ROOT/'records'),
        'diagnostics':[{'id':c['profile'],'state':'not_dispatched_primary_unqualified'} for c in value['cells']]}
    return receipt,value,store,lambda:write_ref(tmp_path/'receipt',receipt)


@pytest.fixture
def reader_fixture(tmp_path,monkeypatch):
    # The orchestrator reader is tested independently from raw BFS correctness;
    # pair validation is replaced with an explicitly synthetic failing A/A grid.
    return build_reader_fixture(tmp_path, monkeypatch)


def node(free, file=0, slab=0, dirty=0):
    values = {'MemFree': free, 'Active(file)': file, 'Inactive(file)': 0,
              'Dirty': dirty, 'Writeback': 0, 'SReclaimable': slab}
    return '\n'.join(f'Node 1 {key}: {value} kB' for key, value in values.items())


def zone(low=0, high=0, protection=0):
    return f'Node 1, zone Normal\n low {low}\n high {high}\n managed 16511103\n protection: (0, 0, {protection})\n'
