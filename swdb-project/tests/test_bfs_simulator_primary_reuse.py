"""Retained primary identity and no-recompile contract. Updated: 2026-09-26 ET."""
import copy
from pathlib import Path

import pytest

from scripts import bfs_simulator_series as client
from swdb import artifacts


@pytest.fixture
def retained(tmp_path):
    source = tmp_path/'source'; source.mkdir()
    (source/'bfs.cc').write_text('int bfs() { return 0; }\n')
    artifact = artifacts.identify(source)
    files = {}
    for name in ('bfs', 'compiler', 'driver', 'm5ops'):
        p = tmp_path/name; p.write_text(name); p.chmod(0o755)
        files[name] = {'path':str(p), 'sha256':artifacts.file_hash(p)}
    candidate = {'id':'candidate', 'artifact':artifact}
    implementation = {'function':'DOBFS'}
    model = {'id':'model', 'context':{'model_root':'/model','target':'target'}}
    compiled = {'binary':files['bfs']['path'], 'binary_sha256':files['bfs']['sha256'],
        'compiler':files['compiler']['path'], 'compiler_sha256':files['compiler']['sha256'],
        'driver':files['driver'], 'm5ops':files['m5ops'], 'source_artifact':artifact,
        'flags':['-O3', '-DMAA'], 'adapter':'dx100.complete_call.v2'}
    build = {'id':'retained-build', 'candidate':'candidate', 'evidence_kind':'execution',
        'outcome':{'state':'complete','stage':'candidate_build'},
        'request':{'diagnostic_regions':False}, 'build':compiled,
        'context':{'candidate_sha256':artifact['sha256'], 'function':'DOBFS', 'model_build':'model',
            'model_root':'/model', 'target':'target', 'roi':'bfs.complete_call.v1', 'accelerated_requested':True}}
    frozen = {'settings':{'roi':'bfs.complete_call.v1','builds':{'candidate':
        {k:compiled[k] for k in ('compiler','flags','adapter')}}}}
    return build,candidate,implementation,model,True,frozen,'candidate','dx100.bfs.verifier.v2'


def test_reopen_exact_retained_primary_without_compiler_execution(retained, monkeypatch):
    monkeypatch.setattr(client.subprocess, 'Popen', lambda *a, **kw: pytest.fail('must not execute compiler'))
    client.validate_primary_build(*retained)


@pytest.mark.parametrize('location,key,value', [
    ('outcome','state','failed'), ('outcome','stage','simulation'),
    ('request','diagnostic_regions',True), ('request','fixture',True),
    ('context','candidate_sha256','0'*64), ('context','function','DOBFSMAA'),
    ('context','model_build','other'), ('context','model_root','/other'),
    ('context','target','other'), ('context','roi','bfs.dx100.traversal.v1'),
    ('context','accelerated_requested',False), ('context','diagnostic',{'regions':[]}),
    ('build','adapter','dx100.complete_call.v1'), ('build','flags',['-O0']),
])
def test_reused_primary_rejects_incompatible_receipt(retained,location,key,value):
    changed=copy.deepcopy(retained);changed[0][location][key]=value
    with pytest.raises(ValueError,match='retained primary'):
        client.validate_primary_build(*changed)


@pytest.mark.parametrize('field', ['binary','compiler','driver','m5ops','source'])
def test_reused_primary_reopens_actual_artifacts(retained,field):
    build=retained[0]['build']
    path = (Path(build['source_artifact']['path'])/'bfs.cc' if field=='source'
            else Path(build[field] if field in {'binary','compiler'} else build[field]['path']))
    path.write_text('changed')
    with pytest.raises((ValueError, artifacts.Failure)):
        client.validate_primary_build(*retained)


def test_reused_primary_requires_executable_binary(retained):
    Path(retained[0]['build']['binary']).chmod(0o644)
    with pytest.raises(ValueError,match='not executable'):
        client.validate_primary_build(*retained)


@pytest.mark.parametrize('extra', [[], ['--protocol','frozen','--protocol-role','candidate','--author-binary']])
def test_primary_reuse_rejects_unfrozen_or_author_paths_before_output(tmp_path,monkeypatch,capsys,extra):
    import sys
    monkeypatch.setattr(client.socket,'gethostname',lambda:'mbit10')
    monkeypatch.setattr(sys,'argv',['series','--id','reuse','--candidate','candidate','--workload','graph',
        '--build-evaluation','model','--configuration',str(tmp_path/'absent.json'),
        '--runs-dir','/data/yanruj/EvolveSWDB_runs/reuse','--lane','1',
        '--primary-build','retained',*extra])
    with pytest.raises(SystemExit) as stopped:
        client.main()
    assert stopped.value.code==2
    assert 'primary-build requires a frozen complete-call series' in capsys.readouterr().err
    assert not list(tmp_path.iterdir())
