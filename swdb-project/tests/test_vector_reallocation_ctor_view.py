"""Constructor35 public workflow regression; created 2026-10-16 ET.

Explicit external Python stand-in only. No mathematical proof acceptance.
The coordinator owns execution of the existing native OCaml setup boundary.
"""
from pathlib import Path

from test_heap_model_view import _heap_public_seed


def test_complete_synthetic_constructor_success_persists_all_thirty_five_targets(tmp_path):
    _library,prove,_marker=_heap_public_seed(tmp_path)
    frama=tmp_path/'frama.py'
    prefix=frama.read_text().split('if "-wp" in sys.argv:')[0]
    frama.write_text(prefix+'''if "-wp" in sys.argv:
 import json,os,re
 text=Path("wp_input.c").read_text()
 lemma=re.search(r"check lemma (\\w+)",text)
 function=None if lemma else "t25v3_ctor_numeric"
 assert lemma or "size_t t25v3_ctor_numeric(" in text
 specs=[("check_lemma_"+lemma.group(1),"lemma",False)] if lemma else [
  ("synthetic_numeric_"+str(i),"assertion",False)for i in range(10)]+[("synthetic_numeric_smoke","assertion",True)]
 rows=[];goals=[];properties=[]
 for prop,kind,smoke in specs:
  name="typed_"+prop
  rows.append({"goal":name,"property":prop,"function":function,"line":34,"smoke":smoke,
   "passed":True,"verdict":"unknown"if smoke else"valid","proved":1,
   "provers":[{"prover":"CVC5:1.2.1","time":0,"success":1}]})
  goals.append({"goal":name,"property":prop,"function":function,"line":34,"smoke":smoke,
   "passed":True,"targets":[],"results":["unknown"if smoke else"valid"]})
  properties.append({"property":prop,"function":function,"kind":kind,"line":34,
   "extern":False,"dependencies":[],"origin":None,"generated_smoke_failure":False,
   "description":"synthetic constructor workflow only"})
 Path("SYNTHETIC-ONLY.txt").write_text("Explicit stand-in; no actual Frama-C or solver")
 Path("wp-goals.json").write_text(json.dumps(rows))
 Path("wp-normalized.c").write_text(text)
 Path("wp-properties.csv").write_text("directory\\tfile\\tline\\tfunction\\tproperty kind\\tstatus\\tproperty\\n")
 Path(os.environ["SWDB_PROOF_REPORT_OUT"]).write_text(json.dumps({"version":"1","complete":True,
  "goals":goals,"properties":properties}))
 sys.exit(0)
''')
    record=prove('--model','std_vector_int_realloc_v3_ctor_count_value')
    assert record['verdict']=='proven'  # Explicitly synthetic workflow assertion.
    assert set(record['verdict_reading'])=={'check','verdict'}
    assert len(record['settings']['heap_model_runs'])==len(record['proof_setup_check']['runs'])==35
    assert len(record['goals'])==45 and sum(bool(goal.get('smoke'))for goal in record['goals'])==1
    assert all((Path(run['cwd'])/'SYNTHETIC-ONLY.txt').is_file()for run in record['settings']['heap_model_runs'])
