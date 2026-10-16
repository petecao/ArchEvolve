"""2026-10-16 ET. Exact original-partial register parser input preparation."""
import hashlib,json,re,subprocess
from conftest import REPO
from swdb import c_lowering,framac

def test_register_four_portable_parser_inputs_keep_partial_order_and_frame(tmp_path):
 folder=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-register-parser/inputs'
 manifest=json.loads((folder/'manifest.json').read_text())
 assert manifest['parser_flags']==list(framac.FLAGS)==['-machdep','x86_64','-kernel-warn-key','annot-error=abort']
 assert {r['name']for r in manifest['inputs']}=={'wp-correct.c','wp-wrong.c','all-contracts.c','ordinary-model.c'}
 for row in manifest['inputs']:
  path=folder/row['name'];text=path.read_text()
  assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']and path.stat().st_size==row['bytes']
  assert not re.search(r'\b(?:__asm__|asm)\s*\(',text)
  for block in re.findall(r'/\*@(.+?)\*/',text,re.S):
   clauses=re.findall(r'\b(requires|terminates|assigns|ensures)\b',block)
   ranks={'requires':0,'terminates':1,'assigns':2,'ensures':3}
   assert [ranks[c]for c in clauses]==sorted(ranks[c]for c in clauses)
  command=[*c_lowering.locate().command,'-x','c','-std=c11','-fsyntax-only',str(path)]
  built=subprocess.run(command,capture_output=True,text=True,timeout=30)
  (tmp_path/(row['name']+'.command.json')).write_text(json.dumps(command,indent=2)+'\n')
  (tmp_path/(row['name']+'.stdout')).write_text(built.stdout);(tmp_path/(row['name']+'.stderr')).write_text(built.stderr)
  assert built.returncode==0,built.stdout+built.stderr
 for name in ('wp-correct.c','wp-wrong.c'):
  text=(folder/name).read_text();compact=''.join(text.split())
  assert text.count(r'terminates \false;')==3
  assert 'assigns__swdb_dx_reg_words[0..1];'in compact
 correct=(folder/'wp-correct.c').read_text();wrong=(folder/'wp-wrong.c').read_text()
 assert correct.replace('== 711 ;','== 1107 ;')==wrong
