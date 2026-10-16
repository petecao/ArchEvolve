"""2026-10-16 ET. Portable exact public allocator inputs; no actual Frama."""
import hashlib,json,re,subprocess
from conftest import REPO
from swdb import c_lowering,framac

def test_exact_total_allocator_parser_inputs_have_pinned_portable_c_syntax(tmp_path):
 folder=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-allocation-parser/inputs'
 manifest=json.loads((folder/'manifest.json').read_text())
 assert manifest['parser_flags']==list(framac.FLAGS)==['-machdep','x86_64','-kernel-warn-key','annot-error=abort']
 assert {r['name']for r in manifest['inputs']}=={'wp-correct.c','wp-wrong.c','all-contracts.c','ordinary-model.c'}
 for row in manifest['inputs']:
  path=folder/row['name'];text=path.read_text()
  assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']and path.stat().st_size==row['bytes']
  assert r'terminates \false'not in text and not re.search(r'\b(?:__asm__|asm)\s*\(',text)
  command=[*c_lowering.locate().command,'-x','c','-std=c11','-fsyntax-only',str(path)]
  compiled=subprocess.run(command,capture_output=True,text=True)
  (tmp_path/(row['name']+'.command.json')).write_text(json.dumps(command,indent=2)+'\n')
  (tmp_path/(row['name']+'.stdout')).write_text(compiled.stdout)
  (tmp_path/(row['name']+'.stderr')).write_text(compiled.stderr)
  assert compiled.returncode==0,compiled.stdout+compiled.stderr
 for name in ('wp-correct.c','wp-wrong.c'):
  text=(folder/name).read_text();body=text[re.search(r'int trust_fixture\(void\)\s*\{',text).start():]
  calls=['init_MAA(', 'get_new_tile_unsigned_int(', 'get_new_tile_unsigned_long_long(',
         'get_new_reg_unsigned_long_long_args0(', 'get_new_reg_unsigned_int_args0(']
  indices=[body.index(c)for c in calls]
  assert indices==sorted(indices)
