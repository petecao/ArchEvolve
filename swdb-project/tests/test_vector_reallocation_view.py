"""Qualified public model prelaunch controls; created 2026-10-16 ET.

Only deliberately scripted external outcomes, never actual proof acceptance.
"""
from pathlib import Path
import json
import shutil
import pytest

from test_heap_model_view import _heap_public_seed


def test_public_qualified_grow_reaches_exact_checked_packet_with_typed_runtime_binding(tmp_path):
    _library, prove, marker = _heap_public_seed(tmp_path)
    record=prove('--model','std_vector_int_realloc_v3_grow')
    assert record['failure_class']=='parse_error', record
    assert marker.exists(), 'only the scripted parser-error stand-in may launch'
    assert record['proof_setup_check']['verdict']=='passed'
    view=record['settings']['heap_model_view']
    assert view['member']=='std_vector_int_realloc_v3_grow'
    assert view['qualification']['original_contract_proved'] is False
    assert view['qualification']['unary_role']=='reallocation eligibility; not exclusive ownership'
    assert view['generic_caller_composition']=='unsupported'
    assert len(view['obligations'])==61
    runtime=record['settings']['vector_reallocation_typed_runtime']
    assert runtime['integer_model']=='Machine' and runtime['heap_model']=='Typed'
    assert {Path(row['path']).name for row in runtime['sources']}=={'MemTyped.ml','Cint.ml','Factory.ml'}
    assert runtime['source_image_role']=='explicit qualified typed-int domain; caller construction discharge remains required'
    reports={r['name']:r for r in record['evidence']['reports']}
    packet=Path(reports['wp_input']['path']).read_text()
    assert 't25v3_control_grow_premises_feasible' in packet
    assert packet.count('check lemma ')==1
    assert '-wp-prop' not in record['settings']['flags']


def test_complete_synthetic_qualified_success_persists_schema_and_all_current_targets(tmp_path):
    _library,prove,_marker=_heap_public_seed(tmp_path)
    frama=tmp_path/'frama.py'
    prefix=frama.read_text().split('if "-wp" in sys.argv:')[0]
    frama.write_text(prefix+'''if "-wp" in sys.argv:
 import json,os,re
 text=Path("wp_input.c").read_text()
 lemma=re.search(r"check lemma (\\w+)",text)
 function=None if lemma else "t25v3_grow_numeric"
 assert lemma or "size_t t25v3_grow_numeric(" in text
 specs=[("check_lemma_"+lemma.group(1),"lemma",False)] if lemma else [
   ("synthetic_numeric_"+str(i),"assertion",False) for i in range(10)]+[("synthetic_numeric_smoke","assertion",True)]
 rows=[];generated=[];properties=[]
 for prop,kind,smoke in specs:
  goal="typed_"+prop
  rows.append({"goal":goal,"property":prop,"function":function,"line":34,"smoke":smoke,
    "passed":True,"verdict":"unknown" if smoke else "valid","proved":1,
    "provers":[{"prover":"CVC5:1.2.1","time":0,"success":1}]})
  generated.append({"goal":goal,"property":prop,"function":function,"line":34,"smoke":smoke,
    "passed":True,"targets":[],"results":["unknown" if smoke else "valid"]})
  properties.append({"property":prop,"function":function,"kind":kind,"line":34,
    "extern":False,"dependencies":[],"origin":None,"generated_smoke_failure":False,
    "description":"synthetic qualified workflow only"})
 Path("SYNTHETIC-ONLY.txt").write_text("External stand-in; no actual proof or solver execution")
 Path("wp-goals.json").write_text(json.dumps(rows))
 Path("wp-normalized.c").write_text(text)
 Path("wp-properties.csv").write_text("directory\\tfile\\tline\\tfunction\\tproperty kind\\tstatus\\tproperty\\n")
 Path(os.environ["SWDB_PROOF_REPORT_OUT"]).write_text(json.dumps({"version":"1","complete":True,
   "goals":generated,"properties":properties}))
 sys.exit(0)
''')
    record=prove('--model','std_vector_int_realloc_v3_grow')
    assert record['verdict']=='proven'  # labeled synthetic reader/persistence control only
    assert set(record['verdict_reading'])=={'check','verdict'}
    assert len(record['settings']['heap_model_runs'])==61
    assert len(record['proof_setup_check']['runs'])==61
    assert len(record['goals'])==71 and sum(bool(g.get('smoke')) for g in record['goals'])==1
    assert all((Path(r['cwd'])/'SYNTHETIC-ONLY.txt').is_file() for r in record['settings']['heap_model_runs'])
    assert any('does not prove the original v2 raw contract' in a['sentence'] for a in record['assumptions'])


def test_public_qualified_prelaunch_rebuild_refuses_self_consistent_project_axiom(tmp_path):
    action=f'''import hashlib,json
stage,=Path({str(tmp_path/'runs')!r}).rglob("heap-inputs")
manifest=stage/"manifest.json";m=json.loads(manifest.read_text())
p=stage/"theory/heap_reallocation.mlw"
p.write_text(p.read_text().replace("\\nend\\n","\\n axiom desired: false\\nend\\n"))
m["semantics"]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()
manifest.write_text(json.dumps(m))'''
    _library,prove,marker=_heap_public_seed(tmp_path,action)
    done=prove('--model','std_vector_int_realloc_v3_grow',ok=False)
    assert done.returncode!=0 and 'heap_model_view' in done.stderr
    assert not marker.exists()


@pytest.mark.parametrize('attack',['none','source','natural','model_override'])
def test_selected_typed_runtime_cannot_substitute_changed_source_or_integer_model(tmp_path,attack):
    from swdb import vector_reallocation_model as model
    from swdb import vector_reallocation_view as view
    from swdb.heap_model_view import Refused
    # This pure validator control uses the independently pinned source receipt,
    # with no new executable package/tool query. Public adapter controls above
    # separately exercise the engine's existing native reader/setup boundary.
    evidence=Path(__file__).parents[1]/'.scratch/probata-proof-of-concept-2026-10-13/evidence'
    metadata=json.loads((evidence/'t25-int32-embedding-boundary-review-20261016.json').read_text())
    actual=Path(next(row['path'] for row in metadata['source_pins']
                     if Path(row['path']).name=='MemTyped.ml')).parent
    if not all((actual/row['name']).is_file() for row in model.TYPE_IMAGE['required_source_files']):
        pytest.skip('the independently pinned native source fixture is not present on this host')
    core=tmp_path/'core';core.mkdir()
    for row in model.TYPE_IMAGE['required_source_files']:shutil.copyfile(actual/row['name'],core/row['name'])
    flags=['-wp-model','+real']
    if attack=='source':(core/'Cint.ml').write_text('(* unrelated semantics *)\n')
    elif attack=='natural':flags=['-wp-model','NAT+real']
    elif attack=='model_override':flags+=['-wp-model','NAT']
    foundation={'ocaml_package_paths':{'wp_core':str(core)}}
    if attack=='none':assert view.typed_runtime(foundation,flags)['integer_model']=='Machine'
    else:
        with pytest.raises(Refused):view.typed_runtime(foundation,flags)
