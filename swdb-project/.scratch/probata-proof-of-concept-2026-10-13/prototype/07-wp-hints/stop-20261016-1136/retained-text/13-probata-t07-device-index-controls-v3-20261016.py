"""2026-10-16 ET: public exact-root splitter controls only; no native/compiler/formal."""
from pathlib import Path
import argparse,copy,hashlib,json,os,runpy,sys
P=Path
def forbid(event,args):
 if event in {'subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.posix_spawnp','ctypes.dlopen'} or event.startswith(('os.exec','os.spawn')):raise RuntimeError('pure controls forbid '+event)
sys.addaudithook(forbid)
a=argparse.ArgumentParser();a.add_argument('phase',choices=['red','green']);a.add_argument('output',type=P);args=a.parse_args();out=args.output;out.mkdir()
ROOT=P('/private/tmp/probata-t07-device-index-source');SUB=P('swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints');BASE=ROOT/SUB;SOURCE=BASE/'device_index_worlds.py'
def H(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
if args.phase=='red':
 try:
  api=runpy.run_path(str(SOURCE),run_name='public_generator_not_main');api['build'](BASE,out/'normal')
  passed=(out/'normal/index_safe/site_input.c').is_file() and (out/'normal/missing_index/site_input.c').is_file()
 except Exception as error:passed=False;why=type(error).__name__+': '+str(error)
 (out/'receipt.json').write_text(json.dumps({'date_ET':'2026-10-16','phase':'RED','public_exact_root_split_available':passed,'failure':why if not passed else None,'no_main_or_tool':True},indent=2)+'\n')
 raise SystemExit(0 if passed else 1)
api=runpy.run_path(str(SOURCE),run_name='public_generator_not_main');checks=[]
def check(name,condition):assert condition,name;checks.append(name)
def refused(fn,*argv):
 try:fn(*argv)
 except (RuntimeError,ValueError,FileExistsError,UnicodeDecodeError):return True
 return False
inputs={r['path']:H(BASE/r['path']) for r in api['INPUTS']}
m=api['build'](BASE,out/'normal');normal=(BASE/'checks/device_init/normal.c').read_bytes()
check('both named full-root worlds generated',set(m['generated_worlds'])=={'index_safe','missing_index'})
check('all original six worlds conserved with literal span hashes',len(m['original_worlds'])==6 and {r['root'] for r in m['original_worlds'] if r['source']=='checks/device_init/normal.c'}=={'swdb_device_pipeline_safe','swdb_device_missing_source','swdb_device_wrong_prefix','swdb_device_index_safe','swdb_device_missing_index'})
for tag,root in [('index_safe','swdb_device_index_safe'),('missing_index','swdb_device_missing_index')]:
 raw=(out/'normal'/tag/'site_input.c').read_bytes();span=m['generated_worlds'][tag]['kept_span'];emitted=m['generated_worlds'][tag]['generated_span'];lo,hi=span['start_byte'],span['end_byte']
 check(tag+' full contract/body bytes unchanged',raw[emitted['start_byte']:emitted['end_byte']]==normal[lo:hi])
 check(tag+' retained source lines preserved with explicit byte map',span['first_line']==emitted['first_line'] and span['last_line']==emitted['last_line'])
 check(tag+' canonical blanks have no trailing spaces or extra EOF lines',all(not line.endswith((b' ',b'\t')) for line in raw.splitlines()) and not raw.endswith(b'\n\n'))
 check(tag+' header exactly original physical bytes',(out/'normal'/tag/'dxc_summaries.h').read_bytes()==(BASE/'standin_device_init_canonical/dxc_summaries.h').read_bytes())
 check(tag+' no other source root definition remains',sum(raw.count(('void '+name+'(').encode()) for name in ['swdb_device_pipeline_safe','swdb_device_missing_source','swdb_device_wrong_prefix','swdb_device_index_safe','swdb_device_missing_index'])==1)
check('idempotent deterministic separate render',api['build'](BASE,out/'second')==m and all((out/'normal'/rel).read_bytes()==(out/'second'/rel).read_bytes() for rel in m['outputs']))
check('existing output refused before mutation',refused(api['build'],BASE,out/'normal'))
check('source inputs unchanged',all(H(BASE/rel)==sha for rel,sha in inputs.items()))
for label,rel,mutation in [('CRLF','checks/device_init/normal.c',lambda b:b.replace(b'\n',b'\r\n')),('changed body byte','checks/device_init/normal.c',lambda b:b.replace(b'base[0] = 17',b'base[0] = 18')),('weak source missing store','checks/device_init/omitted-output.c',lambda b:b+b'\n'),('normal header byte','standin_device_init_canonical/dxc_summaries.h',lambda b:b+b'\n'),('weak header byte','checks/device_init/omitted-output-dxc_summaries.h',lambda b:b+b'\n'),('nonUTF8','checks/device_init/normal.c',lambda b:b+b'\xff')]:
 fixture=out/('fixture-'+str(len(checks)));fixture.mkdir()
 for r in api['INPUTS']:
  p=fixture/r['path'];p.parent.mkdir(parents=True,exist_ok=True);b=(BASE/r['path']).read_bytes();p.write_bytes(mutation(b) if r['path']==rel else b)
 target=out/('refused-'+str(len(checks)))
 check(label+' physically refused with no emission',refused(api['build'],fixture,target) and not target.exists())
unknown=out/'unknown-root';check('unknown root cannot add a new desired world',refused(api['build'],BASE,unknown,('unapproved',)) and not unknown.exists())
check('kept local store and negative omission remain distinct',b'dxc_tile_data[0][0] = 0;' in (out/'normal/index_safe/site_input.c').read_bytes() and b'dxc_tile_data[0][0] = 0;' not in (out/'normal/missing_index/site_input.c').read_bytes())
(out/'receipt.json').write_text(json.dumps({'date_ET':'2026-10-16','phase':'GREEN','passed':len(checks),'checks':checks,'source':{'path':str(SOURCE),'sha256':H(SOURCE)},'no_main_or_tool':True,'inputs_unchanged':True},indent=2)+'\n');print(json.dumps({'passed':len(checks)}))
