"""Exact consumed14 E checkout only; no force, refs/raw/source remain. Default inspect."""
import argparse,datetime,hashlib,json,os,pathlib,re,socket,stat,subprocess,time
P=pathlib.Path
UID=114316761;BASE=P('/data1/yanruj');PRIMARY=BASE/'ArchEvolve'
E=BASE/'ArchEvolve-lanl-generality-final-export-20261007-a1'
R=BASE/'ArchEvolve-lanl-generality-final-20261007-a1'
C=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
RAW=P('/data/yanruj/EvolveSWDB_runs');B='codex/lanl-generality-estimate-evidence-20261007-a1'
ERAW=RAW/'lanl-generality-final-20261007-a1'
EC='43256ee0300a59a03919833075fbb13fb3ba9ab3';RC='c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
EV=P('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
RECEIPT=EV/'14-generality-final-final-20261007-a1-export.json'
AD=RAW/'lanl14-export-reader-administration-20261007-a1/lanl14-export-reader-control-reader-a1/stdout'
LIMITS = {'one_proc_bytes': 16*1024*1024}
ACCOUNT_SERVICE_HELPER_SHA256='f6c4076013eaa487c0e810ba4329512657bef9b1b74a0c074a7231bcc0466883'
ACCOUNT_SERVICE_IDENTIFICATION_PIN={'path':str(BASE/'lanl-account-pam-service-identification-20261008-a1/identification.json'),'bytes':3818,'sha256':'ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa'}
RAW_TOP_LANE_SIDECAR_PIN={'path': '/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261006-a1.lane.json', 'bytes': 988, 'sha256': '83ba263a56756047716a2e550c3acc7a9d73eadefbbc9e245cdb697092369c1c', 'stat': {'ctime_ns': 1791344103814358923, 'dev': 2065, 'gid': 114316761, 'ino': 9345428, 'mode': 33204, 'mtime_ns': 1791344103814358923, 'nlink': 1, 'size': 988, 'uid': 114316761}}
deadline=time.monotonic()+600
def require(v,s):
 if not v:raise ValueError(s)
def tick():require(time.monotonic()<deadline,'bounded administration deadline')
def inside(x):return x==str(E) or x.startswith(str(E)+'/')
class Refused(Exception):
    pass

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()

def strict_json(raw):
    def pairs(rows):
        d = {}
        for k, v in rows:
            require(k not in d, 'duplicate_json_key')
            d[k] = v
        return d
    def bad(value):
        raise Refused('nonfinite_json')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def stamp(s):
    return {k: getattr(s, 'st_'+k) for k in
            ('dev', 'ino', 'mode', 'uid', 'gid', 'nlink', 'size', 'mtime_ns', 'ctime_ns')}


def exact_account_pam_service_identification(identification_pin, parent_review_identity_sha256,
                                             check_deadline, charge_bytes):
    """Exact reviewed OS-role exclusion; protected references remain UNOBSERVED.

    Callers must bind the ordinary original file pin in their actual reviewed
    configuration. This helper checks current public identity, not reference
    freedom. Budget callbacks belong to that caller's finite metadata inspection.
    No service descendants, parent, or other unreadable consumer are exempted.
    """
    require(re.fullmatch('[0-9a-f]{64}', parent_review_identity_sha256),
            'account_service_parent_review_identity_missing')
    require(identification_pin['path'] == str(BASE/'lanl-account-pam-service-identification-20261008-a1/identification.json')
            and identification_pin['bytes'] == 3818
            and identification_pin['sha256'] == 'ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa',
            'account_service_original_identification_pin_changed')

    def read_fd(fd, cap):
        pieces, count = [], 0
        while True:
            check_deadline()
            part = os.read(fd, min(1024*1024, cap-count+1))
            if not part:
                break
            count += len(part)
            charge_bytes(len(part))
            require(count <= cap, 'account_service_read_limit')
            pieces.append(part)
        return b''.join(pieces)

    def regular_file(path, size, digest, owner, mode=None, original_stat=None):
        check_deadline()
        path = P(path)
        require(path.is_absolute() and path.resolve(strict=True) == path
                and not any(q.is_symlink() for q in (path, *path.parents)),
                'account_service_file_route_changed')
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner
                and before.st_nlink == 1 and before.st_size == size
                and not before.st_mode & 0o7000, 'account_service_file_identity_changed')
        if mode is not None:
            require(stat.S_IMODE(before.st_mode) == mode, 'account_service_native_mode_changed')
        if original_stat is not None:
            require(stamp(before) == original_stat, 'account_service_original_file_stat_changed')
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            require(stamp(os.fstat(fd)) == stamp(before), 'account_service_file_open_changed')
            raw = read_fd(fd, size)
            require(len(raw) == size and sha(raw) == digest
                    and stamp(os.fstat(fd)) == stamp(before)
                    and stamp(path.lstat()) == stamp(before), 'account_service_file_bytes_or_stat_changed')
        finally:
            os.close(fd)
        return raw, stamp(before)

    # The original document remains UNSEALED; its exact returned bytes are checked.
    base_stat = BASE.lstat()
    require(not any(q.is_symlink() for q in (BASE, *BASE.parents))
            and BASE.resolve(strict=True) == BASE and stat.S_ISDIR(base_stat.st_mode)
            and base_stat.st_uid == UID and stat.S_IMODE(base_stat.st_mode) == 0o700,
            'account_service_original_private_ancestor_changed')
    original, original_stat = regular_file(identification_pin['path'], 3818,
        identification_pin['sha256'], UID, original_stat=identification_pin.get('stat'))
    document = strict_json(original)
    require(document['format'] == 'swdb.exact-account-pam-service-original-identification.v1'
            and document['sealed'] is False and 'identity_sha256' not in document
            and document['stable_exact_process_identities_and_public_metadata'] is True
            and document['semantic_service_classification_and_fresh_creation_chronology_require_parent_review'] is True
            and document['reference_free_or_global_visibility_or_cleanup_clearance_claimed'] is False,
            'account_service_original_identification_policy_changed')

    def proc_bytes(path):
        check_deadline()
        fd = os.open(path, os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            return read_fd(fd, LIMITS['one_proc_bytes'])
        finally:
            os.close(fd)

    def current_process(pid, start, ppid, name, cmd_size, cmd_sha, child):
        proc = P('/proc')/str(pid)
        raw_stat = proc_bytes(proc/'stat')
        values = raw_stat[raw_stat.rfind(b')')+2:].split()
        require(int(values[19]) == start and int(values[1]) == ppid,
                'account_service_current_PID_or_parent_changed')
        fields = {}
        for line in proc_bytes(proc/'status').decode().splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                require(key not in fields, 'account_service_duplicate_status_field')
                fields[key] = value.strip()
        uids = [int(value) for value in fields['Uid'].split()]
        gids = [int(value) for value in fields['Gid'].split()]
        require(fields['Name'] == name and int(fields['PPid']) == ppid
                and uids == [UID]*4 and gids == [UID]*4,
                'account_service_current_name_UID_GID_or_parent_changed')
        require(all(int(fields[key], 16) == 0 for key in ('CapInh','CapPrm','CapEff','CapAmb'))
                and int(fields['CapBnd'], 16) == 0x000001ffffffffff,
                'account_service_capability_predicate_changed')
        if child:
            require(values[0] == b'S' and fields['State'].split()[0] == 'S'
                    and int(fields['Threads']) == 1 and int(fields['TracerPid']) == 0
                    and all(int(fields[key], 16) == 0 for key in ('SigPnd','ShdPnd')),
                    'account_service_child_state_thread_tracer_or_pending_changed')
        cmd = proc_bytes(proc/'cmdline')
        cgroup = proc_bytes(proc/'cgroup')
        require(len(cmd) == cmd_size and sha(cmd) == cmd_sha
                and len(cgroup) == 70
                and sha(cgroup) == 'f6b0978005408a4cbf4759816cf4703b0e097284eabe55f01f1cea870640e455',
                'account_service_current_command_or_cgroup_changed')
        # SigBlk is observed, never required zero/nonzero: wait may temporarily unblock.
        return {'pid':pid, 'start_ticks':start, 'ppid':ppid, 'name':name,
                'uids':uids, 'gids':gids, 'state':values[0].decode(),
                'capability_bound':fields['CapBnd'], 'signal_blocked_observed':fields['SigBlk'],
                'cmdline_pin':{'bytes':len(cmd), 'sha256':sha(cmd)},
                'cgroup_pin':{'bytes':len(cgroup), 'sha256':sha(cgroup)}}

    def boot_identity():
        rows = [line for line in proc_bytes(P('/proc/stat')).splitlines() if line.startswith(b'btime ')]
        require(len(rows) == 1 and int(rows[0].split()[1]) == 1785498067
                and os.sysconf('SC_CLK_TCK') == 100, 'account_service_boot_or_clock_changed')
        return {'boot_epoch':1785498067, 'clock_ticks':100}

    def current_pair():
        return [current_process(359656, 40749693, 359655, '(sd-pam)', 9,
                    '971490059d839d27af3ded30a476216b92689d837b0236a700723fb13640e370', True),
                current_process(359655, 40749691, 1, 'systemd', 49,
                    'a4eb13854c1664d48464c575a8c86538e8a379ecd5e1e40ab6c56b61b9b9ffb5', False)]

    boot_before = boot_identity()
    before = current_pair()
    require(os.readlink(P('/proc/359655/exe')) == '/usr/lib/systemd/systemd',
            'account_service_parent_executable_changed')
    native_constants = [('/usr/lib/systemd/systemd', 100816,
        'b472aadf808bef87c0eb203056a77cb64bd268b71b756306013a53de68a94173'),
        ('/usr/lib/systemd/systemd-executor', 137792,
        'b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044')]
    require([(pin['path'], pin['bytes'], pin['sha256']) for pin in document['native_files']]
            == native_constants, 'account_service_original_native_pins_changed')
    native_pins = []
    for path, size, digest in native_constants:
        original_native = next(pin for pin in document['native_files'] if pin['path'] == path)
        raw_native, native_stat = regular_file(path, size, digest, 0, 0o755,
                                              original_native['stat'])
        if path.endswith('/systemd-executor'):
            require(b'(sd-pam)' in raw_native, 'account_service_executor_role_literal_missing')
        native_pins.append({'path':path, 'bytes':size, 'sha256':digest, 'stat':native_stat})
    after = current_pair()
    require([{key:value for key,value in item.items() if key != 'signal_blocked_observed'} for item in before]
            == [{key:value for key,value in item.items() if key != 'signal_blocked_observed'} for item in after]
            and os.readlink(P('/proc/359655/exe')) == '/usr/lib/systemd/systemd'
            and boot_identity() == boot_before, 'account_service_identity_changed_during_check')
    for pin in native_pins:
        require(stamp(P(pin['path']).lstat()) == pin['stat'], 'account_service_native_changed_after_check')
    regular_file(identification_pin['path'], 3818, identification_pin['sha256'], UID,
                 original_stat=original_stat)
    # Close the identity interval after all final public and original-file reads.
    for pid, start, ppid in ((359656,40749693,359655), (359655,40749691,1)):
        final_stat = proc_bytes(P('/proc')/str(pid)/'stat')
        final_values = final_stat[final_stat.rfind(b')')+2:].split()
        require(int(final_values[19]) == start and int(final_values[1]) == ppid
                and (pid != 359656 or final_values[0] == b'S'),
                'account_service_final_PID_parent_or_child_state_changed')
    require(stamp(BASE.lstat()) == stamp(base_stat), 'account_service_private_ancestor_changed_during_check')
    check_deadline()
    return {'classification':'excluded_exact_system_service', 'pid':359656,
            'start_ticks':40749693, 'parent_pid':359655, 'parent_start_ticks':40749691,
            'original_identification_pin':dict(identification_pin),
            'original_identification_policy':'original_unsealed',
            'parent_review_identity_sha256':parent_review_identity_sha256,
            'before_public_identity':before, 'after_public_identity':after,
            'boot_identity':boot_before, 'native_file_pins':native_pins,
            'classification_basis':'Exact current public identity plus parent-reviewed trusted OS lifecycle and original fresh-creation custodies; not file mtime inference.',
            'trusted_OS_role_and_fresh_creation_chronology_are_parent_semantic_binding':True,
            'child_executable_to_executor_relationship_is_inherited_OS_role_not_observed_exe':True,
            'protected_child_fields':{key:'UNOBSERVED' for key in ('fd','cwd','root','exe','maps','syscall','meaningful_wait_channel')},
            'reference_free_claimed':False, 'global_privileged_visibility_or_clearance_claimed':False,
            'other_consumers_parent_and_descendants_exempted':False,
            'signal_blocked_mask_zero_or_nonzero_is_not_predicated':True}

def exact_original_raw_lane_sidecar(check_deadline, selected_paths):
    """One exact original regular RAW sibling; no generic regular-file waiver."""
    check_deadline()
    pin=RAW_TOP_LANE_SIDECAR_PIN;path=P(pin['path'])
    require(path.parent==RAW and path.name=='lanl17-cleanup-smoke-20261006-a1.lane.json'
            and path.resolve(strict=True)==path
            and not any(p.is_symlink() for p in (path,*path.parents)),
            'exact_original_top_sidecar_route')
    before=path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_uid==UID and before.st_nlink==1
            and stamp(before)==pin['stat'] and before.st_size==988,
            'exact_original_top_sidecar_stat')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd))==stamp(before),'exact_original_top_sidecar_open')
        parts=[];count=0
        while True:
            check_deadline()
            part=os.read(fd,min(988-count+1,988))
            if not part:break
            count+=len(part);require(count<=988,'exact_original_top_sidecar_read_bound');parts.append(part)
        raw=b''.join(parts)
        require(count==988 and sha(raw)==pin['sha256']
                and stamp(os.fstat(fd))==stamp(before)==stamp(path.lstat()),
                'exact_original_top_sidecar_returned_bytes')
    finally:os.close(fd)
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'original_top_sidecar_duplicate_key');result[key]=value
        return result
    def bad(value):raise ValueError('original_top_sidecar_nonfinite_JSON')
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=bad)
    require(type(value) is dict and set(value)=={'socket_lane'},'original_top_sidecar_JSON_shape')
    refs=[]
    def visit(item,location):
        if type(item) is dict:
            for key,child in item.items():visit(child,location+[key])
        elif type(item) is list:
            for index,child in enumerate(item):visit(child,location+[index])
        elif type(item) is str and item.startswith('/'):
            require(not any(item==str(p) or item.startswith(str(p)+'/') for p in selected_paths),
                    'original_top_sidecar_JSON_selected_reference')
            refs.append({'JSON_location':location,'path':item})
    visit(value,[])
    require(not any(str(p).encode() in raw for p in selected_paths),
            'original_top_sidecar_literal_selected_reference')
    return {'path':str(path),'bytes':988,'sha256':pin['sha256'],'stat':stamp(before),
            'original_policy':'original_UNSEALED_socket_lane_metadata_no_reseal',
            'original_absolute_JSON_references':refs,
            'literal_and_original_JSON_selected_reference_checks':True,
            'unchanged_historical_mode0664_beneath_existing_private_RAW_ancestor':True}

def read(p,expected=None):
 tick();require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'absolute nonsymlink')
 s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and s.st_size<=256*1024,'owned metadata file')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  with os.fdopen(fd,'rb') as f:
   b=f.read(256*1024+1);require(len(b)==s.st_size and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat()),'stable metadata')
 except:raise
 got=hashlib.sha256(b).hexdigest();require(expected is None or got==expected,'exact byte pin')
 return b,{'path':str(p),'bytes':len(b),'sha256':got}
def git(root,*argv):
 tick();r=subprocess.run(['/usr/bin/git','-C',str(root),*argv],capture_output=True,timeout=min(60,max(.001,deadline-time.monotonic())),env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'})
 require(r.returncode==0 and len(r.stdout)<=4*1024*1024,'bounded Git success');return r.stdout.decode().strip()
def free():s=os.statvfs('/data1');return s.f_bavail*s.f_frsize
def identities(expected):
 require(git(PRIMARY,'rev-parse','HEAD')==git(PRIMARY,'rev-parse','origin/yanrujhou_main')==expected and git(PRIMARY,'branch','--show-current')=='yanrujhou_main','delivered primary')
 require(git(PRIMARY,'status','--porcelain','--untracked-files=all')=='?? swdb-project/records/.retention.lock','preserved primary')
 require(git(R,'rev-parse','HEAD')==RC and not git(R,'status','--porcelain') and git(C,'rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(C,'status','--porcelain'),'execution sources protected')
 require(git(PRIMARY,'rev-parse','refs/heads/'+B)==git(PRIMARY,'rev-parse','origin/'+B)==EC,'export refs retained')
 git(PRIMARY,'merge-base','--is-ancestor',EC,expected)
 for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
  v=json.loads(read(BASE/'lact-host-lease'/f'{n}.meta.json')[0]);require(v['state']=='released','all3 leases released')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--expected-primary',required=True);a.add_argument('--remove',action='store_true');a.add_argument('--account-service-review',required=True);a.add_argument('--account-service-review-sha256',required=True);args=a.parse_args()
 require(re.fullmatch('[a-f0-9]{40}',args.expected_primary) and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID,'exact account and commit')
 nb=P('/usr/bin/git').read_bytes();require(hashlib.sha256(nb).hexdigest()=='06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb' and P('/usr/bin/git').lstat().st_uid==0,'native Git pin')
 review_path=P(args.account_service_review)
 require(re.fullmatch('[0-9a-f]{64}',args.account_service_review_sha256) and review_path.is_absolute() and review_path.is_relative_to(BASE) and review_path.resolve(strict=True)==review_path and not inside(str(review_path)),'exact private service-review route and pin')
 review_raw,review_pin=read(review_path,args.account_service_review_sha256);service_review=strict_json(review_raw)
 require(service_review['format']=='swdb.exact-account-service-semantic-parent-review.v1' and service_review['canonical_ensure_ascii'] is True and service_review['accepted_for_exact_service_role_exclusion'] is True and service_review['shared_helper_source_sha256']==ACCOUNT_SERVICE_HELPER_SHA256 and service_review['original_identification_pin']==ACCOUNT_SERVICE_IDENTIFICATION_PIN and re.fullmatch('[0-9a-f]{64}',service_review['identity_sha256']) and sha(canonical({k:v for k,v in service_review.items() if k!='identity_sha256'}))==service_review['identity_sha256'],'exact sealed parent service-role review')
 identities(args.expected_primary)
 require(E.is_dir() and not E.is_symlink() and E.lstat().st_uid==UID and git(E,'rev-parse','HEAD')==EC and git(E,'branch','--show-current')==B and not git(E,'status','--porcelain') and not git(E,'ls-files','--others','--exclude-standard') and not git(E,'ls-files','--others','--ignored','--exclude-standard'),'clean E no ignored/untracked loss')
 er,ep=read(E/RECEIPT,'02b369f0624964fa4293f563a7b51e142dc369101147ac7fe848503c4b50eb5d');require(read(PRIMARY/RECEIPT,ep['sha256'])[0]==er,'integrated exact receipt')
 ar,ap=read(AD,'bbcbf34ac330da9f2e92173cf7385c9e2d2bc4b4aa7ed982c006bd39937f7bbc')
 ex=json.loads(er);ad=json.loads(ar)
 for v in (ex,ad):require(v['identity_sha256']==hashlib.sha256(json.dumps({k:x for k,x in v.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':')).encode()).hexdigest(),'original default True seal')
 require(ad['format']=='swdb.lanl14-selected-nine-export-admission.v1' and ad['export_commit']==EC and ad['final_source_commit']==RC and ad['new_canonical_records']==18 and ad['full_catalogue_validation']=='OK: 704 record(s) valid' and ad['direct_observations']['cleanup_survivors']=={} and ad['direct_observations']['lane_exit_code']==0,'actual reader acceptance')
 require(ERAW.is_dir() and not ERAW.is_symlink(),'original raw retained')
 process_links=0;raw_links=0;entries=0;helper_read_bytes=0;excluded_exact_system_services=[]
 def charge_helper_bytes(n):
  nonlocal helper_read_bytes
  tick();require(type(n) is int and n>=0,'nonnegative helper byte charge');helper_read_bytes+=n;require(helper_read_bytes<=16*1024*1024*1024,'bounded helper total bytes')
 for proc in P('/proc').iterdir():
  tick()
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  if int(proc.name)==359656:
   excluded_exact_system_services.append(exact_account_pam_service_identification(ACCOUNT_SERVICE_IDENTIFICATION_PIN,service_review['identity_sha256'],tick,charge_helper_bytes));continue
  try:
   if proc.stat().st_uid!=UID:continue
   start=(proc/'stat').read_bytes();fields=start.rsplit(b')',1)[1].split()
   if fields[0]==b'Z':continue
   links=[proc/'cwd',proc/'root',proc/'exe',*list((proc/'fd').iterdir())]
   for link in links:
    try:target=os.readlink(link)
    except FileNotFoundError:continue
    require(not inside(target.removesuffix(' (deleted)')),'owned process physical E reference');process_links+=1
   cmd=(proc/'cmdline').read_bytes();maps=(proc/'maps').read_bytes();require(len(cmd)<=16*1024*1024 and len(maps)<=16*1024*1024 and str(E).encode() not in cmd,'no queued physical E consumer')
   for line in maps.splitlines():
    row=line.split(None,5)
    if len(row)==6:require(not inside(row[5].decode().removesuffix(' (deleted)')),'mapped E reference')
   end=(proc/'stat').read_bytes();require(end.rsplit(b')',1)[1].split()[19]==fields[19],'stable process identity')
  except (FileNotFoundError,ProcessLookupError):continue
  except PermissionError:raise ValueError('inaccessible relevant owned consumer')
 def raw_walk_error(error):raise ValueError('incomplete original raw subtree visibility') from error
 raw_namespace=sorted(p.name for p in RAW.iterdir() if p.name.startswith('lanl'))
 original_top_sidecar=exact_original_raw_lane_sidecar(tick,[E])
 require(P(original_top_sidecar['path']).name in raw_namespace,'original top sidecar namespace retained')
 for name in raw_namespace:
  root=RAW/name
  if root==P(original_top_sidecar['path']):
   require(stamp(root.lstat())==original_top_sidecar['stat'],'original top sidecar still exact');continue
  require(root.is_dir() and not root.is_symlink(),'original raw root')
  for folder,dirs,files in os.walk(root,followlinks=False,onerror=raw_walk_error):
   tick()
   for name in dirs+files:
    entries+=1;require(entries<=400000,'bounded raw links inventory');p=P(folder)/name
    if p.is_symlink():require(not inside(str(p.resolve(strict=True))),'raw dereferenced physical E');raw_links+=1
 require(sorted(p.name for p in RAW.iterdir() if p.name.startswith('lanl'))==raw_namespace
         and exact_original_raw_lane_sidecar(tick,[E])==original_top_sidecar,'original full raw namespace and sidecar continuity')
 before=free();identities(args.expected_primary);require(read(PRIMARY/RECEIPT,ep['sha256'])[0]==er and read(AD,ap['sha256'])[0]==ar and read(review_path,review_pin['sha256'])[0]==review_raw and not git(E,'status','--porcelain'),'immediate final continuity')
 if args.remove:git(PRIMARY,'worktree','remove',str(E));require(not os.path.lexists(E),'only E removed')
 identities(args.expected_primary);require(ERAW.is_dir() and read(PRIMARY/RECEIPT,ep['sha256'])[0]==er and read(AD,ap['sha256'])[0]==ar and read(review_path,review_pin['sha256'])[0]==review_raw,'original raw/receipt/admission retained')
 require(sorted(p.name for p in RAW.iterdir() if p.name.startswith('lanl'))==raw_namespace
         and exact_original_raw_lane_sidecar(tick,[E])==original_top_sidecar,'retained original full raw namespace and sidecar')
 print(json.dumps({'raw_namespace_names':raw_namespace,'original_top_regular_sidecar':original_top_sidecar,'format':'swdb.lanl14-consumed-pure-E-checkout-removal.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_primary':args.expected_primary,'path':str(E),'commit':EC,'branch':B,'removed':args.remove,'process_links_checked':process_links,'excluded_exact_system_services':excluded_exact_system_services,'account_service_review':review_pin,'account_service_parent_review_identity_sha256':service_review['identity_sha256'],'account_service_helper_source_sha256':ACCOUNT_SERVICE_HELPER_SHA256,'account_service_helper_read_bytes':helper_read_bytes,'raw_symlinks_checked':raw_links,'raw_entries_checked':entries,'ignored_and_untracked_files':0,'raw_and_original_controls_and_execution_sources_and_Git_refs_retained':True,'original_receipt':ep,'original_reader':ap,'free_before_bytes':before,'free_after_bytes':free(),'recovered_bytes':free()-before,'scientific_admission':False,'capacity_admission':False},sort_keys=True))
if __name__=='__main__':main()
