# Source-only selected Python bootstrap; no execution during authoring.
import resource
import sys
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(950,950))
OUTPUT_ROOT='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1'
OUTPUT_PATHS=('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/control/controller.py', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/control/normalizer.py', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/control/census.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/control/policy.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/inputs-before.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/inputs-after.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/caller.normalized.json.gz', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/rename-manifest.jsonl', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/transport.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/component/inverse.json', '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1/result.json')
def bootstrap_audit(event,args):
    if event=='open':
        path,mode,flags=args
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(1|2|64|512|1024):
            if type(path) is not str or path not in OUTPUT_PATHS or not flags&64 or not flags&128:
                raise PermissionError('only exclusive fixed new-root output allowed')
    if event=='os.mkdir':
        if args[0] not in (OUTPUT_ROOT,OUTPUT_ROOT+'/control',OUTPUT_ROOT+'/component'):
            raise PermissionError('only fixed new-root directories allowed')
        return
    if event in {'os.system','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate',
        'os.utime','os.chdir','os.putenv','os.unsetenv','ctypes.dlopen','resource.setrlimit'} or event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')):
        raise PermissionError('passive transform mutation/child/network refused: '+event)
sys.addaudithook(bootstrap_audit)
import hashlib
payload=sys.stdin.buffer.read(81926)
if len(payload)!=81925 or hashlib.sha256(payload).hexdigest()!='91db08f4cc17b8af0448b94c72ed074b287283c63b1f5e562c1ed9a487f960e4':
    raise ValueError('exact reviewed transform stdin required')
if len(sys.argv)!=2 or sys.argv[1]!=OUTPUT_ROOT:
    raise ValueError('exact fresh output argument required')
exec(compile(payload,'<reviewed-passive-role-transform-stdin>','exec'),{'__name__':'__main__','SOURCE_BYTES':payload,'__builtins__':__builtins__})
