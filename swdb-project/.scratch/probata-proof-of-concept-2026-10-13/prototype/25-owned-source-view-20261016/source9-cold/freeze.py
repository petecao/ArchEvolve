"""2026-10-16 ET. Stdlib-only local byte freezer; never execute observer main."""
from pathlib import Path
import ast
import hashlib
import json
HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
context=json.loads((HERE/'context.json').read_bytes())
semantic=(HERE/'semantic_terms.py').read_text()
context['semantic_source_sha256']=hashlib.sha256(semantic.encode()).hexdigest()
context_raw=(json.dumps(context,sort_keys=True,indent=2)+'\n').encode()
(HERE/'context.json').write_bytes(context_raw)
source=(HERE/'observer.py').read_text()
entry=('CONTEXT_JSON = '+repr(context_raw.decode())+'\nSEMANTIC_SOURCE = '+repr(semantic)+'\n'+source).encode()
ast.parse(entry)
(HERE/'entry.py').write_bytes(entry)
argv=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10','/usr/bin/timeout','--signal=TERM','--kill-after=5s','190s','/usr/bin/env','-i','HOME=/data1/yanruj','LANG=C','LC_ALL=C','PATH=/usr/bin:/bin','PYTHONDONTWRITEBYTECODE=1','/data1/yanruj/venvs/swdb-test/bin/python','-I','-B','-']
command={'date':'2026-10-16 ET','status':'INERT fresh root admission required','argv':argv,'stdin':pin(HERE/'entry.py'),'local_transport_deadline_seconds':210,'stdout_cap_bytes':2097152,'stderr_cap_bytes':32768,'no_compiler_native_solver_or_project_imports':True,'actual_execution':False,'scientific_source_or_caller_acceptance':False}
(HERE/'command.json').write_text(json.dumps(command,sort_keys=True,indent=2)+'\n')
files=[p for p in HERE.iterdir()if p.is_file()and p.name not in {'source-packet.json'}]
packet={'date':'2026-10-16 ET','classification':'FROZEN_INERT_COMPLETE_ORIGINAL_SOURCE9_COLD_CENSUS','files':[pin(p)for p in sorted(files)],'source_commit':'032e1851eec7b195c7a3737997d5f5ea1d1343a5','raw_root':'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-032e1851-owned-source9-public-v3','profile':'owned-source9-public-v3-profile','settlement':context['settlement'],'all9_original_outcomes':'8Valid+swap.owner_correspondence Timeout','all26_retained_tasks_required':True,'all36_properties_and_all9_ordinary_required':True,'canonical_files':29,'raw_files':188,'raw_bytes':21450336,'semantic_adoption':False,'unknown_types_definitions_or_support_never_accepted':True,'root_once_admission_and_parent_source_review_required':True,'actual_observer_compiler_native_verifier_solver_or_remote_execution':False,'limits':{'AS_bytes':536870912,'alarm_seconds':180,'CPU_limit_set':False,'outer_seconds':190,'local_seconds':210,'stdout_bytes':2097152}}
(HERE/'source-packet.json').write_text(json.dumps(packet,sort_keys=True,indent=2)+'\n')
preparation={'date':'2026-10-16 ET','packet':pin(HERE/'source-packet.json'),'entry':pin(HERE/'entry.py'),'command':pin(HERE/'command.json'),'files':packet['files'],'initial8purecontrols_log':pin(HERE/'pure-controls-initial.log'),'inherited17helpers_AST_exact':True,'corrected7semantic_helpers_AST_exact':True,'source_goals':9,'source_definition_transcriptions':24,'root_actual_once_admission_required':True,'complete_cold_census_only':'Unknown combined type/driver definitions remain unresolved, never theorem or source adoption. Original ordinary timeout remains not_proven.','project_imports_or_compiler_native_verifier_solver_remote_observer_executions':0}
out=POC/'evidence/t25-owned-source9-complete-cold-reader-preparation-v1-20261016.json'
out.write_text(json.dumps(preparation,sort_keys=True,indent=2)+'\n')
print(json.dumps({'packet':pin(HERE/'source-packet.json'),'entry':pin(HERE/'entry.py'),'preparation':pin(out)},sort_keys=True))
