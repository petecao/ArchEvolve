"""2026-10-08 ET: bounded read-only active-use observation; no Git/host mutation."""
import os, subprocess, json, pathlib, datetime

P = pathlib.Path
root = P('/data1/yanruj/ArchEvolve')
assert os.uname().nodename.split('.')[0] == 'mbit10'
assert root.is_dir()
assert datetime.datetime.now(datetime.timezone.utc) >= datetime.datetime(2026,10,8,14,48,28,tzinfo=datetime.timezone.utc)
names = json.load(__import__('sys').stdin)
assert type(names) is list and len(names) == 41
assert all(type(n) is str and n.startswith('codex/lanl-') for n in names)

connection = {}
for label, argv in (
    ('uptime', ['/usr/bin/uptime']),
    ('disks', ['/usr/bin/df','-h','/data1','/data']),
    ('logged_in_users', ['/usr/bin/who']),
):
    r = subprocess.run(argv,capture_output=True,text=True,timeout=10,check=True)
    assert len(r.stdout.encode()) < 65536
    connection[label] = r.stdout.strip()
connection['leases'] = {}
for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
    p = P('/data1/yanruj/lact-host-lease')/(name+'.meta.json')
    try:
        body = p.read_bytes()
        assert len(body) <= 65536
        v = json.loads(body)
        connection['leases'][name] = {k:v.get(k) for k in ('state','generation','name')}
    except FileNotFoundError:
        connection['leases'][name] = {'state':None,'observation':'file_absent'}

def git(*args):
    r = subprocess.run(['/usr/bin/git','-C',str(root),*args],capture_output=True,text=True,timeout=20,check=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
    assert len(r.stdout.encode()) < 256*1024
    return r.stdout.strip()

worktrees = []
for chunk in git('worktree','list','--porcelain').split('\n\n'):
    f = dict(line.split(' ',1) for line in chunk.splitlines() if ' ' in line)
    if 'worktree' in f:
        worktrees.append({'path':f['worktree'],'head40':f.get('HEAD'),'branch':f.get('branch','').removeprefix('refs/heads/'),'locked': any(line=='locked' or line.startswith('locked ') for line in chunk.splitlines())})
assert worktrees and len(worktrees) < 256
uid = os.getuid()
processes = []
unreadable = []
for p in P('/proc').iterdir():
    if not p.name.isdecimal(): continue
    try:
        if p.stat().st_uid != uid: continue
        cmd = (p/'cmdline').read_bytes()
        if len(cmd) > 128*1024: raise ValueError('cmdline_bound')
        matches = [n for n in names if n.encode() in cmd]
        try: cwd = os.readlink(p/'cwd')
        except FileNotFoundError: continue
        except PermissionError: cwd = None
        tree_matches = [t['path'] for t in worktrees if cwd and (cwd==t['path'] or cwd.startswith(t['path']+'/'))]
        if matches or tree_matches:
            processes.append({'pid':int(p.name),'cwd':cwd,'candidate_branch_literal_matches':matches,'worktree_cwd_matches':tree_matches})
    except FileNotFoundError: continue
    except (PermissionError, OSError, ValueError) as e:
        unreadable.append({'pid':int(p.name),'field':'owned_process_cmdline_or_cwd','error':type(e).__name__})
    assert len(processes) + len(unreadable) < 2048

control = P('/data1/yanruj/lanl17-detached-sparse-retire-a4')
status_path = control/'status.json'
status_body = status_path.read_bytes()
assert len(status_body) <= 16384
s = json.loads(status_body)
status_summary = {k:s.get(k) for k in ('format','state','guard_exit_code','guard_started_utc','guard_finished_utc','guard_attempt','scientific_admission','capacity_admission')}
print(json.dumps({'format':'swdb.remote-branch-active-use-observation.v1','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only':True,'connection_check':connection,'primary_branch':git('rev-parse','--abbrev-ref','HEAD'),'primary_head40':git('rev-parse','HEAD'),'worktrees':worktrees,'owned_process_matches':processes,'unreadable_owned_process_fields':unreadable,'existing_retirement_status':status_summary,'limitations':'Branch/ref and owned process-use observation only. No source sync, fetch/prune, worker control, scientific evaluation or consumer clearance.'},sort_keys=True))
