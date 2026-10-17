import resource
import sys
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
def readonly(event,args):
    if event=='open':
        path,mode,flags=args
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(1|2|64|512|1024):raise PermissionError('preflight is read-only')
    if event in {'os.system','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.mkdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime','os.chdir','os.putenv','os.unsetenv','ctypes.dlopen','resource.setrlimit'} or event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')):
        raise PermissionError('preflight child/network/mutation refused')
sys.addaudithook(readonly)
import base64,hashlib,json,os,shutil,stat,time,_imp,importlib.util,zlib
from pathlib import Path
POLICY=json.loads(base64.b64decode('__POLICY__'))
RAW=Path(POLICY['original_raw']);OUT=Path(POLICY['output_root']);POST=__POST__
START=time.monotonic()
def need(ok,message):
    if not ok:raise ValueError(message)
def stable(value):return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
def pin(path):
    path=Path(path);before=path.lstat();need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'physical preflight input required')
    with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
    need(stable(before)==stable(path.lstat()),'preflight input changed');return {'bytes':before.st_size,'sha256':value}
pins={}
for path,expected in POLICY['physical_inputs'].items():
    pins[path]=pin(path);need(pins[path]==expected,'selected input differs: '+path)
old_result=json.loads((RAW/'component/result.json').read_bytes())
need(old_result['accepted'] is False and old_result['error']=={'type':'Refused','message':'duplicate compiler JSON key'} and old_result['after_input_errors']==[],'original refusal differs')
need(OUT.parent.resolve(strict=True)==OUT.parent and stat.S_ISDIR(OUT.parent.lstat().st_mode),'physical new-output parent required')
if not POST:need(not os.path.lexists(OUT),'new output namespace already exists')
need(shutil.disk_usage(OUT.parent).free>=53687091200+(0 if POST else 268435456),'selected disk floor/allowance refused')
need(_imp.is_builtin('zlib')==1 and importlib.util.find_spec('zlib').origin=='built-in' and zlib.ZLIB_RUNTIME_VERSION=='1.3','selected builtin zlib differs')
need(sys.executable=='/data1/yanruj/venvs/swdb-test/bin/python','selected Python command differs')
ancestry=[];ancestors=set();pid=os.getpid()
for _ in range(64):
    if pid<=1:break
    ancestors.add(pid);text=Path('/proc/'+str(pid)+'/stat').read_text();fields=text.rsplit(') ',1)[1].split()
    ancestry.append({'pid':pid,'comm':text.split('(',1)[1].rsplit(') ',1)[0],'uid':Path('/proc/'+str(pid)).stat().st_uid,'ppid':int(fields[1]),'start_ticks':int(fields[19])})
    pid=int(fields[1])
need(pid<=1,'finite ancestry required')
matched=[];races=[];permitted=[];denied=[];scanned=0
for item in sorted(Path('/proc').iterdir()):
    if not item.name.isdigit():continue
    scanned+=1;need(scanned<=20000 and time.monotonic()-START<20,'finite process census bound')
    try:
        cmd=(item/'cmdline').read_bytes()
        if str(RAW).encode() in cmd or str(OUT).encode() in cmd:
            text=(item/'stat').read_text();fields=text.rsplit(') ',1)[1].split()
            matched.append({'pid':int(item.name),'uid':item.stat().st_uid,'ppid':int(fields[1]),'start_ticks':int(fields[19]),
                'self_ancestry':int(item.name) in ancestors,'argv0':cmd.split(b'\x00',1)[0].decode(errors='replace')[:256],'argv_sha256':hashlib.sha256(cmd).hexdigest()})
    except FileNotFoundError:races.append(int(item.name))
    except PermissionError:
        row=next((row for row in ancestry if row['pid']==int(item.name)),None)
        if row and row['uid']==0 and row['comm'] in ('sshd','sshd-session','sshd-auth','systemd','(sd-pam)'):
            permitted.append(dict(row,argv_read='denied',scope='exact inherited current SSH/OS/PAM ancestor TCB'))
        else:denied.append(int(item.name))
need(len(matched)<=32 and len(races)<=128 and not denied,'unrelated unreadable/process census refused')
need(all(row['self_ancestry'] for row in matched),'another selected original/output reader is active')
value={'schema':'passive-transform-preflight-2','postflight':POST,'raw':str(RAW),'output':str(OUT),'pins':pins,'original_refusal':old_result['error'],
    'scanned':scanned,'selected_processes':matched,'ancestry':ancestry,'permitted_inherited_unreadables':permitted,'unrelated_unreadables':denied,'exit_races':races,
    'all_host_empty_required':False,'remote_artifact_writes':False,'decoder_origin':'built-in','wall_seconds':time.monotonic()-START}
if POST:
    result_path=OUT/'result.json';need(result_path.stat().st_size<=1048576,'bounded result metadata required')
    result=json.loads(result_path.read_bytes());need(result['normalization_complete'] is True and result['completion_requires_controller_zero_exit_and_settled_publication'] is True
        and result['original_capture_accepted'] is False and result['selected_inputs_unchanged'] is True,'complete settled transform result required')
    output_pins={}
    for row in result['outputs']:
        actual=pin(row['path']);need(actual=={k:row[k] for k in ('bytes','sha256')},'settled output differs');output_pins[row['path']]=actual
    output_pins[str(result_path)]=pin(result_path)
    files=list(OUT.rglob('*'));actual_files=[path for path in files if path.is_file()]
    need(not any(path.is_symlink() for path in files) and {str(path) for path in actual_files}==set(output_pins)
        and sum(row['bytes'] for row in output_pins.values())<=268435456 and all(row['bytes']<=134217728 for row in output_pins.values()),'settled output topology/quota differs')
    transport=json.loads((OUT/'component/transport.json').read_bytes());inverse=json.loads((OUT/'component/inverse.json').read_bytes())
    value.update(output_pins=output_pins,result_selected={key:result[key] for key in ('schema','normalization_complete','completion_requires_controller_zero_exit_and_settled_publication',
        'original_capture_accepted','source_call_ABI_public_or_full28_admission','wall_seconds')},
        normalized_gzip_codec=transport['normalized_gzip_codec'],normalization_selected={key:transport['normalization'][key] for key in
            ('normalized_bytes','normalized_sha256','original_minified_token_bytes','original_minified_token_sha256','inverse_manifest_rows','inverse_manifest_bytes','inverse_manifest_sha256','plain_normalized_file_cap_fit')},inverse=inverse)
print(json.dumps(value,sort_keys=True,separators=(',',':')))
