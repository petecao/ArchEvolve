"""2026-10-16 ET. ACSL output order; real Frama parser admission is separate."""
import re
import pytest
from swdb.dx100_stream_model import normal_return_model

@pytest.mark.parametrize('call',['maa_stream_load_unsigned_int','wait_ready','get_tile_size'])
def test_public_stream_contract_places_termination_after_requires_before_simple_clauses(call):
 text=normal_return_model()['contracts'][call]
 clauses=re.findall(r'\b(requires|terminates|assigns|ensures)\b',text)
 ranks={'requires':0,'terminates':1,'assigns':2,'ensures':3}
 assert clauses.count('terminates')==1
 assert [ranks[c]for c in clauses]==sorted(ranks[c]for c in clauses),text


def test_exact_public_parser_bundle_is_pinned_portable_c_without_tool_or_solver_flags(tmp_path):
 import hashlib,json,subprocess
 from conftest import REPO
 from swdb import c_lowering,framac
 folder=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-stream-parser/inputs'
 manifest=json.loads((folder/'manifest.json').read_text())
 assert manifest['parser_flags']==list(framac.FLAGS)==['-machdep','x86_64','-kernel-warn-key','annot-error=abort']
 assert {r['name']for r in manifest['inputs']}=={'wp-correct.c','wp-wrong.c','wp-combined.c','all-contracts.c','ordinary-model.c'}
 for row in manifest['inputs']:
  path=folder/row['name'];text=path.read_text()
  assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
  assert path.stat().st_size==row['bytes']
  assert not re.search(r'\b(?:__asm__|asm)\s*\(',text)
  assert re.findall(r'^#include\s+(.+)$',text,re.M)and all(
    s in ('<stdint.h>','<stddef.h>','<stdbool.h>')for s in re.findall(r'^#include\s+(.+)$',text,re.M))
  command=[*c_lowering.locate().command,'-x','c','-std=c11','-fsyntax-only',str(path)]
  done=subprocess.run(command,capture_output=True,text=True)
  (tmp_path/(row['name']+'.command.json')).write_text(json.dumps(command,indent=2)+'\n')
  (tmp_path/(row['name']+'.stdout')).write_text(done.stdout)
  (tmp_path/(row['name']+'.stderr')).write_text(done.stderr)
  assert done.returncode==0,done.stdout+done.stderr
 # These are the full public artifacts, with all helper contracts and the
 # actual source call order; this is not a toy isolated annotation snippet.
 for name in ('wp-correct.c','wp-wrong.c','wp-combined.c'):
  text=(folder/name).read_text();body=text[re.search(r'int trust_fixture\(void\)\s*\{',text).start():]
  assert body.index('maa_stream_load_unsigned_int(')<body.index('wait_ready(')<body.index('get_tile_size(')
  assert text.count(r'terminates \false;')==4
