"""Original acceptance runner transport regression, 2026-10-15 ET; no solver."""
import importlib.util
import json
import subprocess
import sys
from types import SimpleNamespace

from conftest import REPO


def test_original_matrix_prove_forwards_the_explicit_outer_budget(tmp_path, monkeypatch):
    path = REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-original-matrix.py'
    spec = importlib.util.spec_from_file_location('original_matrix_runner',path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    records = tmp_path/'records/proofs'
    records.mkdir(parents=True)
    (records/'proof.fixture.yaml').write_text('id: proof.fixture\nverdict: not_proven\n')
    captured = []
    def public(*args, timeout=600, **kwargs):
        captured.append((args,timeout))
        return subprocess.CompletedProcess(args,0,json.dumps({'path':'proofs/proof.fixture.yaml'}),'')
    monkeypatch.setattr(runner,'run_swdb',public)
    seed = runner.MatrixSeed(tmp_path,{'safe':'original-safe'},1800)
    assert seed.prove('--candidate','original-safe')['id']=='proof.fixture'
    args,budget = captured[0]
    assert budget==1800
    assert args[0]=='prove' and '--adapter' in args and 'wp' in args
    assert '--candidate' in args and 'original-safe' in args


def test_original_matrix_exact_control_filter_skips_completed_pairs(tmp_path, monkeypatch):
    path = REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-original-matrix.py'
    spec = importlib.util.spec_from_file_location('filtered_original_matrix',path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    output = tmp_path/'fresh'
    monkeypatch.setattr(sys,'argv',[str(path),'--expected-commit','frozen','--output',str(output),
        '--groups','new_array,templates','--cases','new_out_of_range,new_after_delete'])
    monkeypatch.setattr(runner,'git',lambda *args:'frozen' if args==('rev-parse','HEAD') else '')
    monkeypatch.setattr(runner.c_lowering,'locate',lambda:SimpleNamespace(missing=()))
    monkeypatch.setattr(runner.framac,'locate',lambda:SimpleNamespace(missing=()))
    monkeypatch.setattr(runner,'build_subset_seed',lambda root:{'safe':'original-safe'})
    calls = []
    class FilterSeed(runner.MatrixSeed):
        def unit(self, group, **kwargs):
            calls.append(group)
            path = self.records/'proofs'/f'{group}.yaml'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(f'id: {group}\n')
            return {'id':group}
        def prove(self, *args, **kwargs):
            raise AssertionError('control-only selection must not prove unrelated dependencies')
    monkeypatch.setattr(runner,'MatrixSeed',FilterSeed)
    monkeypatch.setattr(runner,'audit',lambda *args,**kwargs:{'errors':[]})
    assert runner.main()==0
    assert calls==['new_out_of_range','new_after_delete']
    manifest = json.loads((output/'source-manifest.json').read_text())
    assert manifest['cases']==['new_after_delete','new_out_of_range']
    assert manifest['public_timeout_seconds']==1800
    matrix = json.loads((output/'matrix.json').read_text())
    assert [r['label'] for r in matrix['rows']]==calls


def test_filtered_seeded_caller_still_proves_and_validates_current_dependencies(tmp_path, monkeypatch):
    path = REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/t24-original-matrix.py'
    spec = importlib.util.spec_from_file_location('seeded_original_matrix',path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    output = tmp_path/'fresh'
    monkeypatch.setattr(sys,'argv',[str(path),'--expected-commit','frozen','--output',str(output),
        '--groups','std_models','--cases','std_models:seeded'])
    monkeypatch.setattr(runner,'git',lambda *args:'frozen' if args==('rev-parse','HEAD') else '')
    monkeypatch.setattr(runner.c_lowering,'locate',lambda:SimpleNamespace(missing=()))
    monkeypatch.setattr(runner.framac,'locate',lambda:SimpleNamespace(missing=()))
    monkeypatch.setattr(runner,'build_subset_seed',lambda root:{'bug':'original-seed'})
    models = runner.MODELS['std_models']
    calls = []
    class DependencySeed(runner.MatrixSeed):
        def save(self, name, pins):
            record = {'id':name,'pins':pins}
            path = self.records/'proofs'/f'{name}.yaml'
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(record))
            return record
        def prove(self, *args, **kwargs):
            assert args[0]=='--model'
            name = args[1];calls.append(name)
            return self.save('proof.'+name,{'code':{'sha256':'hash.'+name}})
        def unit(self, group, **kwargs):
            assert kwargs['candidate']=='bug'
            calls.append(group+':seeded')
            return self.save('seeded',{'models':[{'id':name,'sha256':'hash.'+name,
                'proof_record':'wrong-proof'} for name in models]})
    monkeypatch.setattr(runner,'MatrixSeed',DependencySeed)
    monkeypatch.setattr(runner,'audit',lambda record,*args,**kwargs:dict(record,errors=[]))
    assert runner.main()==1
    assert calls==models+['std_models:seeded']
    rows = json.loads((output/'matrix.json').read_text())['rows']
    assert all(not r['errors'] for r in rows[:-1])
    assert rows[-1]['label']=='std_models:seeded' and rows[-1]['errors']
