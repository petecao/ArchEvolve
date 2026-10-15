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
