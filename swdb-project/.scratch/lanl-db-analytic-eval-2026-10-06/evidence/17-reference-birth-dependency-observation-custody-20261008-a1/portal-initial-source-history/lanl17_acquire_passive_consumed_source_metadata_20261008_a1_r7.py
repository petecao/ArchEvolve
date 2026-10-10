"""Prospective passive acquisition only. MAIN NOT RUN during source preparation.

All eighteen R3 rows are inventory coverage, never a removal selection. Original
receipt/body hashes are observed without changing their original seal policies.
No plan, review, classification, capacity admission or removal is produced.
Parent later captures stdout privately; this observer writes no filesystem file.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import pwd
import re
import socket
import stat
import subprocess
import sys
import time
import types

P = pathlib.Path
UID = 114316761
ACCOUNT = 'yanruj'
BASE = P('/data1/yanruj')
PRIMARY = BASE/'ArchEvolve'
RAW = P('/data/yanruj/EvolveSWDB_runs')
EV = PRIMARY/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence'
R3 = BASE/'lanl-storage-admin-selected-source-20261008-a5/lanl_consumed_detached_source_guard_r6_20261008_a1.py'
R3_BYTES = 116443
R3_SHA = '6118592610fbff77a7da3ea8196c772331066d3188ded29627218486c106b326'
GIT = P('/usr/bin/git')
GIT_BYTES = 4019024
GIT_SHA = '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
E_CHECKOUT = BASE/'ArchEvolve-lanl-generality-final-export-20261007-a1'
LIMITS = {'passive_seconds':1000, 'external_outer_proposed_seconds':1200,
          'one_file':512*1024*1024, 'total_file_bytes':16*1024*1024*1024,
          'walk_entries':400000, 'inventory_bytes':32*1024*1024,
          'future_plan_bytes_unchanged':2*1024*1024,
          'one_git_seconds':120, 'processes':10000, 'process_fds':200000,
          'one_proc_bytes':16*1024*1024, 'future_source_bytes':2*1024*1024}
SUFFIXES = {'.json','.yaml','.yml','.md','.py','.sh','.txt'}
DENIED_NAMES = {'auth.json','credentials','credentials.json','id_rsa','id_ed25519'}
DENIED_COMPONENTS = {'.ssh','.aws','.codex','.gnupg'}
SAFE_NAME = re.compile(r'[A-Za-z0-9_.-]{1,200}')
DEADLINE = None

class Refused(Exception): pass

def require(ok, code):
    if not ok: raise Refused(code)

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(v, ascii=True):
    return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=ascii,allow_nan=False).encode()
def stamp(s):
    return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def denied(p):
    return p.name in DENIED_NAMES or any(x in DENIED_COMPONENTS for x in p.parts)
def inside(value, root): return value==str(root) or value.startswith(str(root)+'/')

def bootstrap_read(p, cap, owner):
    """Stable returned bytes only; no helper import or body output from this read."""
    require(DEADLINE is None or time.monotonic()<DEADLINE,'passive_deadline')
    require(p.is_absolute() and '..' not in p.parts and not denied(p),'bootstrap_route')
    require(not any(x.is_symlink() for x in (p,*p.parents)) and p.resolve(strict=True)==p,'bootstrap_redirect')
    s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and s.st_size<=cap,'bootstrap_file')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd))==stamp(s),'bootstrap_open')
        parts=[];count=0
        while True:
            require(DEADLINE is None or time.monotonic()<DEADLINE,'passive_deadline')
            part=os.read(fd,min(1024*1024,cap-count+1))
            if not part:break
            count+=len(part);require(count<=cap,'bootstrap_cap');parts.append(part)
        require(count==s.st_size and stamp(os.fstat(fd))==stamp(s)==stamp(p.lstat()),'bootstrap_changed')
        body=b''.join(parts);return body,{'path':str(p),'bytes':len(body),'sha256':sha(body),'stat':stamp(s)}
    finally:os.close(fd)

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


PORTAL_HELPER_SHA = '36fc3b3fdede68b15fca931c199b649303cda4db559f1226ea13474ab5c0e44c'

def portal_inode_birth_rows(document, row_definitions, admin=False, check_deadline=None):
    """Pure metadata validation. No path reads; symlink targets are not covered."""
    fields = ['dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns']
    encoding = document['object_encoding']
    require(encoding['format']=='ordered-array.v1'
            and encoding['original_stat_fields']==fields
            and encoding['original_statx_fields']==['returned_mask','requested_mask','attributes',
                'attributes_mask','mount_id_or_null','birth_supported','birth_seconds','birth_nanoseconds']
            and encoding['object_fields']==['relative_path','original_stat','original_statx',
                'directory_names_count_or_null','directory_names_digest_or_null','type_code'],
            'portal_birth_array_encoding_changed')
    require(document['sealed'] is False and 'identity_sha256' not in document
            and document['cleanup_capacity_or_scientific_admission'] is False
            and document['boot_clock_interval_equal'] is True
            and document['clock_before']['boot_epoch_seconds']==1785498067
            and document['clock_after']['boot_epoch_seconds']==1785498067
            and document['clock_before']['clock_ticks_per_second']==100
            and document['clock_after']['clock_ticks_per_second']==100,
            'portal_original_birth_policy_or_boot_changed')
    if not admin:
        require(document['format']=='swdb.exact-portal-helper-checkout-inode-birth-query.v1'
                and document['all_eighteen_walks_completed_and_metadata_stable'] is True
                and document['g5_source_sha256']=='a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb'
                and document['symlink_targets_and_shared_git_admin_not_traversed'] is True,
                'portal_checkout_birth_original_changed')
    else:
        require(document['format']=='swdb.exact-portal-helper-worktree-administration-inode-birth-query.v1'
                and document['all_eighteen_walks_completed_and_metadata_stable'] is True
                and document['administration_anchor_metadata_interval_equal'] is True
                and document['public_identity_interval_equal'] is True
                and document['genuine_prior_checkout_birth_original_pin']['bytes']==14762700
                and document['genuine_prior_checkout_birth_original_pin']['sha256']=='e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7',
                'portal_admin_birth_original_incomplete')
    originals = document['rows']
    require(isinstance(originals,list) and len(originals)==len(row_definitions)==18
            and {r['row'] for r in originals}==set(row_definitions), 'portal_birth_rows_incomplete')
    result = {}
    cutoff_numerator = (1785498067+1)*100+559081545+1
    for row in originals:
        if check_deadline is not None:check_deadline()
        name = row['row']
        root = str(PRIMARY/'.git/worktrees'/name) if admin else row_definitions[name]['path']
        require(name not in result and row['path']==root
                and row['first_pass_completed'] is True and row['second_pass_completed'] is True
                and row['metadata_equal_between_passes'] is True,
                'portal_birth_row_route_or_stability_changed')
        if admin:
            require(row['original_pointer_route']==root and row['g5_definition']==row_definitions[name],
                    'portal_admin_pointer_route_changed')
        else:
            require(row['g5_definition']==row_definitions[name]
                    and row['git_indirection']['original_pointer_route']==str(PRIMARY/'.git/worktrees'/name),
                    'portal_checkout_definition_or_git_pointer_changed')
        objects = row['original_objects']; digest=hashlib.sha256(); by_path={}; counts=[0,0,0]
        require(isinstance(objects,list) and 0<len(objects)<=400000, 'portal_original_object_count_limit')
        for obj in objects:
            if check_deadline is not None:check_deadline()
            require(isinstance(obj,list) and len(obj)==6, 'portal_birth_object_shape')
            relative, s, x, names_count, names_digest, kind = obj
            require(isinstance(relative,str) and relative and len(relative.encode())<=4096
                    and (relative=='.' or (not relative.startswith('/')
                         and all(part not in ('','.', '..') for part in relative.split('/'))))
                    and relative not in by_path and isinstance(s,list) and len(s)==10
                    and all(type(v) is int for v in s) and isinstance(x,list) and len(x)==8,
                    'portal_birth_path_or_stat_shape')
            require(s[0]==2097 and s[3]==UID and s[5]>0
                    and kind in (0,1,2) and type(kind) is int
                    and (stat.S_ISDIR(s[2]) if kind==0 else stat.S_ISREG(s[2]) if kind==1 else stat.S_ISLNK(s[2]))
                    and (kind==0 or s[5]==1), 'portal_birth_type_owner_device_or_links_changed')
            require(x[0]==8191 and x[1]==8191 and x[4]==136 and x[5] is True
                    and type(x[6]) is int and type(x[7]) is int
                    and x[6]>0 and 0<=x[7]<1000000000
                    and (x[6]*1000000000+x[7])*100 > cutoff_numerator*1000000000,
                    'portal_birth_unsupported_or_not_strictly_after_helper')
            require((kind==0 and type(names_count) is int and names_count>=0
                     and isinstance(names_digest,str) and re.fullmatch('[0-9a-f]{64}',names_digest))
                    or (kind!=0 and names_count is None and names_digest is None),
                    'portal_birth_directory_names_shape')
            if kind==2:
                require(not admin and relative in (
                    'swdb-project/weeklogs/2026-09-24/.build/node_modules',
                    'swdb-project/weeklogs/2026-09-30/.build/node_modules'),
                    'portal_birth_unreviewed_symlink')
            by_path[relative]=obj; counts[kind]+=1
            encoded=canonical(obj); digest.update(len(encoded).to_bytes(8,'big')); digest.update(encoded)
        require('.' in by_path and by_path['.'][5]==0
                and len(objects)==row['first_objects_observed']==row['second_objects_observed']
                and digest.hexdigest()==row['first_metadata_sha256']==row['second_metadata_sha256'],
                'portal_birth_count_or_complete_digest_changed')
        children_by_parent={relative:[] for relative,obj in by_path.items() if obj[5]==0}
        for relative in by_path:
            if check_deadline is not None:check_deadline()
            if relative!='.':
                parent,slash,leaf=relative.rpartition('/')
                parent=parent or '.'; leaf=leaf if slash else relative
                require(parent in children_by_parent, 'portal_birth_parent_object_missing')
                children_by_parent[parent].append(leaf)
        for relative,obj in by_path.items():
            if check_deadline is not None:check_deadline()
            if obj[5]==0:
                children=sorted(children_by_parent[relative], key=os.fsencode)
                require(len(children)==obj[3] and sha(b'\0'.join(os.fsencode(p) for p in children))==obj[4],
                        'portal_birth_complete_directory_inventory_changed')
        require(counts[2]==(0 if admin else 2), 'portal_birth_symlink_scope_changed')
        result[name]={'root':root,'objects':by_path,'count':len(objects),'counts':counts,
                      'metadata_sha256':digest.hexdigest(),
                      'git_pointer':None if admin else row['git_indirection']}
    return result

def exact_portal_autounmount_identification(review_pin, row_definitions, selected_rows, removed_rows,
                                            enclosing_review_identity, helper_sha256,
                                            check_deadline, charge_bytes, charge_metadata):
    """One exact protected helper under explicit OS-image/clock assumptions.

    Caller ordinary reference, alias, Git retention and selection gates remain
    mandatory. This does not observe protected child fields or clear other tasks.
    """
    private=BASE/'lanl-portal-helper-inode-review-20261008-a1'
    require(review_pin['path']==str(private/'parent-review.json')
            and type(review_pin['bytes']) is int and 0<review_pin['bytes']<=256*1024
            and re.fullmatch('[0-9a-f]{64}',review_pin['sha256'])
            and re.fullmatch('[0-9a-f]{64}',enclosing_review_identity), 'portal_review_pin_missing')

    def stat_fact(s):
        return [getattr(s,'st_'+key) for key in
                ('dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns')]

    def actual_stat(path):
        check_deadline(); charge_metadata(0,1,0)
        return path.lstat()

    def route(path):
        require(path.is_absolute() and '..' not in path.parts, 'portal_noncanonical_path')
        for q in (path,*path.parents):
            require(not stat.S_ISLNK(actual_stat(q).st_mode), 'portal_route_symlink')
        charge_metadata(0,len(path.parts),0)  # Conservative debit for resolution's component stats.
        require(path.resolve(strict=True)==path, 'portal_route_redirect')
        return actual_stat(path)

    def read_file(pin, cap, owner=UID, mode=0o600):
        path=P(pin['path']); before=route(path)
        require(type(pin['bytes']) is int and 0<=pin['bytes']<=cap
                and stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1
                and stat.S_IMODE(before.st_mode)==mode and before.st_size==pin['bytes'],
                'portal_original_or_native_file_identity')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            charge_metadata(0,1,0)
            require(stat_fact(os.fstat(fd))==stat_fact(before), 'portal_file_open_changed')
            parts=[]; count=0
            while True:
                check_deadline(); part=os.read(fd,min(1024*1024,cap-count+1))
                if not part:break
                charge_bytes(len(part)); count+=len(part)
                require(count<=cap, 'portal_read_cap'); parts.append(part)
            raw=b''.join(parts); charge_metadata(0,1,0)
            require(len(raw)==pin['bytes'] and sha(raw)==pin['sha256']
                    and stat_fact(os.fstat(fd))==stat_fact(before)==stat_fact(actual_stat(path)),
                    'portal_original_or_native_bytes_changed')
        finally:os.close(fd)
        return raw, {'path':str(path),'bytes':len(raw),'sha256':sha(raw),'stat':stamp(before)}

    def review_binding(review):
        require(review['format']=='swdb.exact-portal-autounmount-semantic-parent-review.v1'
                and review['canonical_ensure_ascii'] is True
                and sha(canonical({k:v for k,v in review.items() if k!='identity_sha256'}))==review['identity_sha256']
                and review['accepted_exact_role_only'] is True
                and review['shared_helper_sha256']==helper_sha256
                and review['pid']==1654291 and review['start_ticks']==559081545
                and review['parent_pid']==1654279 and review['parent_start_ticks']==559081538,
                'portal_semantic_review_binding_changed')
        required_assumptions=('trusted_host_clock_and_inode_birth_history',
            'installed_native_image_matches_running_child',
            'installed_packages_correspond_to_reviewed_exact_source',
            'libfuse_3_14_wait_loop_has_only_control_socket_and_fixed_mount_target',
            'all_potentially_removed_checkout_and_git_admin_inodes_postdate_helper',
            'node_modules_symlink_targets_are_not_followed_or_removed',
            'ordinary_portal_parent_and_other_consumers_still_checked',
            'existing_git_shared_objects_refs_and_alias_gates_remain_mandatory')
        require(set(review['explicit_assumptions'])==set(required_assumptions)
                and all(review['explicit_assumptions'][k] is True for k in required_assumptions)
                and review['inherited_file_descriptors_not_generically_closed'] is True
                and review['protected_child_fields']=={k:'UNOBSERVED' for k in
                    ('fd','cwd','root','exe','maps','syscall','wait_channel')}
                and review['global_reference_free_or_cleanup_capacity_or_scientific_admission'] is False
                and review['other_consumers_parent_or_descendants_exempted'] is False,
                'portal_semantic_assumption_or_scope_missing')
        require(review['admin_birth_producer_pin']=={'bytes':52031,
                    'sha256':'b2b08374ea997679df9e08894fc14d139cce9f9c90ab3dabd324db36d6f661a3'},
                'portal_admin_birth_producer_review_pin_pending')
        require(review['lifecycle_research_pin']=={'bytes':13046,
                    'sha256':'9c83f802ed7d467c8411c3253be9bac330827ba01a935a11bb7a6ed9eb248840'},
                'portal_exact_lifecycle_research_pin_changed')

    base_before=actual_stat(BASE); private_before=route(private)
    require(stat.S_ISDIR(base_before.st_mode) and base_before.st_uid==UID
            and stat.S_IMODE(base_before.st_mode)==0o700
            and stat.S_ISDIR(private_before.st_mode) and private_before.st_uid==UID
            and stat.S_IMODE(private_before.st_mode)==0o700, 'portal_evidence_private_ancestor')
    raw_review,review_fact=read_file(review_pin,256*1024); review=strict_json(raw_review)
    review_binding(review)
    require(review_pin.get('canonical_ensure_ascii') is True
            and review_pin.get('identity_sha256')==review['identity_sha256'],
            'portal_review_pin_explicit_True_identity_missing')
    fixed_originals={
        'public_identity':('public-identity.json',4103,
            '1ea76b7519827bae6f81902c2bebd6b16e22c303fcada24257bf1bab73174489'),
        'checkout_birth':('checkout-inode-birth.json',14762700,
            'e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7'),
        'git_admin_birth':('git-admin-inode-birth.json',139083,
            'a62b53bd4c9f89c3a212690750905c6cf13203fca8fceee560a9ad9ee25a1dd5')}
    documents={}; original_facts=[]
    for key,(name,size,digest) in fixed_originals.items():
        pin=review['original_pins'][key]
        require(pin['path']==str(private/name) and pin['bytes']==size and pin['sha256']==digest,
                'portal_fixed_original_pin_changed')
        raw,fact=read_file(pin,32*1024*1024); documents[key]=strict_json(raw); original_facts.append(fact)
    original=documents['public_identity']
    require(original['format']=='swdb.portal-fuse-service-public-identity.v1'
            and original['sealed'] is False and 'identity_sha256' not in original
            and original['public_role_identity_stable_at_end'] is True
            and original['parent_semantic_exclusion_cleanup_or_global_reference_free_claimed'] is False,
            'portal_original_identity_policy_changed')
    checkout=portal_inode_birth_rows(documents['checkout_birth'],row_definitions,check_deadline=check_deadline)
    admin=portal_inode_birth_rows(documents['git_admin_birth'],row_definitions,True,check_deadline)
    require(isinstance(selected_rows,list) and len(set(selected_rows))==len(selected_rows)
            and set(selected_rows)<=set(row_definitions)
            and isinstance(removed_rows,list) and len(set(removed_rows))==len(removed_rows)
            and set(removed_rows)<=set(selected_rows), 'portal_removed_journal_scope_changed')
    remaining=sorted(set(selected_rows)-set(removed_rows)); evidence_stats={x['path']:x['stat'] for x in original_facts+[review_fact]}

    def proc_read(path,cap):
        check_deadline(); fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:
            parts=[]; count=0
            while True:
                check_deadline(); part=os.read(fd,min(1024*1024,cap-count+1))
                if not part:break
                charge_bytes(len(part)); count+=len(part)
                require(count<=cap,'portal_proc_read_cap'); parts.append(part)
            return b''.join(parts)
        finally:os.close(fd)

    def process_fields(raw_stat,raw_status,pid,start,ppid,child):
        values=raw_stat[raw_stat.rfind(b')')+2:].split(); fields={}
        for line in raw_status.decode().splitlines():
            if ':' in line:
                key,value=line.split(':',1); require(key not in fields,'portal_duplicate_status'); fields[key]=value.strip()
        require(int(raw_stat.split(b' ',1)[0])==pid and int(values[19])==start
                and int(values[1])==ppid and int(fields['Pid'])==pid and int(fields['PPid'])==ppid
                and fields['Name']==('fusermount3' if child else 'xdg-document-po')
                and [int(v) for v in fields['Uid'].split()]==([UID,0,0,0] if child else [UID]*4)
                and [int(v) for v in fields['Gid'].split()]==[UID]*4
                and values[0]==b'S' and fields['State'].split()[0]=='S'
                and int(fields['TracerPid'])==0
                and (int(fields['Threads'])==1 if child else int(fields['Threads'])>0),
                'portal_current_public_process_identity_changed')
        caps={key:fields[key] for key in ('CapInh','CapPrm','CapEff','CapBnd','CapAmb')}
        require(caps==original['child' if child else 'parent']['capability_hex'], 'portal_current_capabilities_changed')
        return {'pid':pid,'start_ticks':start,'ppid':ppid,'state':'S',
                'uids':[int(v) for v in fields['Uid'].split()], 'threads':int(fields['Threads'])}

    def public_link(path):
        check_deadline(); value=os.readlink(path); charge_metadata(0,1,0); charge_bytes(len(os.fsencode(value)))
        return value

    def current_pair():
        pair=[]
        for pid,start,ppid,child,key in ((1654291,559081545,1654279,True,'child'),
                (1654279,559081538,359655,False,'parent')):
            root=P('/proc')/str(pid)
            item=process_fields(proc_read(root/'stat',16384),proc_read(root/'status',32768),pid,start,ppid,child)
            cmd=proc_read(root/'cmdline',4096); pin=original[key+'_cmdline_pin']
            require(len(cmd)==pin['bytes'] and sha(cmd)==pin['sha256'], 'portal_current_fixed_command_changed')
            item['cmdline_pin']=pin; pair.append(item)
        require(public_link(P('/proc/1654279/exe'))=='/usr/libexec/xdg-document-portal', 'portal_parent_exe_changed')
        return pair

    def boot_and_mount():
        boot=[v for v in proc_read(P('/proc/stat'),1024*1024).splitlines() if v.startswith(b'btime ')]
        require(len(boot)==1 and int(boot[0].split()[1])==1785498067
                and os.sysconf('SC_CLK_TCK')==100, 'portal_current_boot_or_ticks_changed')
        require(public_link(P('/proc/self/ns/mnt'))==public_link(P('/proc/1654279/ns/mnt')),
                'portal_parent_mount_namespace_differs')
        mounts=[]
        for line in proc_read(P('/proc/1654279/mountinfo'),16*1024*1024).decode().splitlines():
            before,after=line.split(' - ',1); left=before.split(); right=after.split()
            if left[4]=='/run/user/114316761/doc':
                mounts.append({'mount_id':left[0],'parent_mount_id':left[1],'device':left[2],
                    'root':left[3],'mount_point':left[4],'mount_options':left[5],
                    'optional_fields':left[6:],'filesystem':right[0],'source':right[1],'super_options':right[2]})
        require(mounts==original['parent_namespace_exact_portal_mount'] and len(mounts)==1
                and mounts[0]['device']=='0:48' and mounts[0]['filesystem']=='fuse.portal'
                and mounts[0]['mount_point']=='/run/user/114316761/doc', 'portal_mount_route_changed')
        return mounts[0]

    def live_scope(scope):
        summaries=[]
        for name in remaining:
            row=scope[name]; root=P(row['root']); route(root); digest=hashlib.sha256(); observed={}
            stack=[(root,'.')]
            while stack:
                path,relative=stack.pop(); charge_metadata(1,0,0); before=actual_stat(path)
                require(relative in row['objects'] and stat_fact(before)==row['objects'][relative][1],
                        'portal_current_inode_or_stat_changed')
                obj=row['objects'][relative]; observed[relative]=stat_fact(before)
                if obj[5]==0:
                    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
                    try:
                        charge_metadata(0,1,0)
                        require(stat_fact(os.fstat(fd))==stat_fact(before),'portal_directory_open_changed')
                        names=[]
                        with os.scandir(fd) as entries:
                            for entry in entries:
                                check_deadline(); value=entry.name
                                require('/' not in value and value not in ('.','..')
                                        and len(names)<obj[3], 'portal_directory_names_invalid_or_added')
                                charge_bytes(len(os.fsencode(value))+1); names.append(value)
                        names.sort(key=os.fsencode)
                        name_bytes=b'\0'.join(os.fsencode(value) for value in names)
                        require(len(names)==obj[3] and sha(name_bytes)==obj[4], 'portal_directory_inventory_changed')
                        charge_metadata(0,1,0)
                        require(stat_fact(os.fstat(fd))==stat_fact(before)==stat_fact(actual_stat(path)),
                                'portal_directory_changed_during_listing')
                    finally:os.close(fd)
                    stack.extend((path/value, value if relative=='.' else relative+'/'+value) for value in reversed(names))
                else:
                    require(stat_fact(actual_stat(path))==stat_fact(before), 'portal_leaf_changed_during_metadata')
                encoded=canonical(obj); digest.update(len(encoded).to_bytes(8,'big')); digest.update(encoded)
            require(set(observed)==set(row['objects']) and digest.hexdigest()==row['metadata_sha256'],
                    'portal_current_full_inode_scope_incomplete')
            summaries.append({'row':name,'path':row['root'],'objects':len(observed),
                              'metadata_sha256':digest.hexdigest()})
        return summaries

    pair_before=current_pair(); mount_before=boot_and_mount(); native_facts=[]
    for name in remaining:
        pointer=checkout[name]['git_pointer']
        pin={'path':str(P(checkout[name]['root'])/'.git'),'bytes':pointer['bytes'],'sha256':pointer['sha256']}
        raw,fact=read_file(pin,4096,UID,stat.S_IMODE(pointer['file_stat']['mode']))
        require(stat_fact(actual_stat(P(pin['path'])))==[pointer['file_stat'][key] for key in
            ('dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns')]
            and raw==('gitdir: '+admin[name]['root']+'\n').encode(), 'portal_live_git_indirection_changed')
    for pin in original['native_file_pins']:
        expected=('/usr/bin/fusermount3',39296,'d278775c1528dd32efc85c2cb322423ee93aa8dcf76aaa595f7022d427910704',0o4755) if pin['path']=='/usr/bin/fusermount3' else (
            '/usr/libexec/xdg-document-portal',195560,'44dd7e1eb2df2a4de1d8c1189a3fee4451539ffab5db6ba4d21718c6d43af3dc',0o755)
        require((pin['path'],pin['bytes'],pin['sha256'])==expected[:3], 'portal_native_original_pin_changed')
        raw,fact=read_file(pin,256*1024,0,expected[3]); require(fact['stat']==pin['stat'],'portal_native_installed_identity_changed')
        native_facts.append(fact)
    first_checkout=live_scope(checkout); first_admin=live_scope(admin)
    second_checkout=live_scope(checkout); second_admin=live_scope(admin)
    require(first_checkout==second_checkout and first_admin==second_admin, 'portal_live_scope_interval_changed')
    pair_after=current_pair(); mount_after=boot_and_mount()
    require(pair_before==pair_after and mount_before==mount_after, 'portal_public_identity_interval_changed')
    for path,expected in evidence_stats.items():
        require(stamp(actual_stat(P(path)))==expected,'portal_original_or_review_stat_changed_at_end')
    for fact in native_facts:
        require(stamp(actual_stat(P(fact['path'])))==fact['stat'],'portal_native_stat_changed_at_end')
    require(stat_fact(actual_stat(BASE))==stat_fact(base_before)
            and stat_fact(actual_stat(private))==stat_fact(private_before), 'portal_private_ancestor_interval_changed')
    for pid,start,ppid in ((1654291,559081545,1654279),(1654279,559081538,359655)):
        raw=proc_read(P('/proc')/str(pid)/'stat',16384); values=raw[raw.rfind(b')')+2:].split()
        require(int(raw.split(b' ',1)[0])==pid and int(values[19])==start and int(values[1])==ppid
                and values[0]==b'S', 'portal_final_public_identity_anchor_changed')
    check_deadline()
    return {'classification':'excluded_exact_portal_autounmount_helper','pid':1654291,
        'start_ticks':559081545,'parent_pid':1654279,'parent_start_ticks':559081538,
        'semantic_review_identity_sha256':review['identity_sha256'],
        'enclosing_parent_review_identity_sha256':enclosing_review_identity,
        'original_file_pins':original_facts,'before_public_identity':pair_before,'after_public_identity':pair_after,
        'portal_mount':mount_before,'native_file_pins':native_facts,
        'remaining_checkout_inode_scopes':second_checkout,'remaining_git_admin_inode_scopes':second_admin,
        'selected_rows_from_unchanged_caller_scope':list(selected_rows),
        'already_removed_rows_only_from_completed_journal':list(removed_rows),
        'strict_helper_birth_upper_bound_rational':{'numerator':179108888346,'denominator':100},
        'protected_child_fields':review['protected_child_fields'],
        'explicit_assumptions':review['explicit_assumptions'],
        'inherited_file_descriptors_not_generically_closed':True,
        'symlink_targets_not_followed_or_removed_and_not_reference_cleared':True,
        'shared_git_objects_refs_and_unselected_administration_not_cleared':True,
        'parent_and_other_consumers_still_require_ordinary_checks':True,
        'global_reference_free_or_cleanup_capacity_or_scientific_admission':False}

RAW_TOP_LANE_SIDECAR_PIN={'path': '/data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261006-a1.lane.json', 'bytes': 988, 'sha256': '83ba263a56756047716a2e550c3acc7a9d73eadefbbc9e245cdb697092369c1c', 'stat': {'ctime_ns': 1791344103814358923, 'dev': 2065, 'gid': 114316761, 'ino': 9345428, 'mode': 33204, 'mtime_ns': 1791344103814358923, 'nlink': 1, 'size': 988, 'uid': 114316761}}

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

class Observer:
    def __init__(self,args,module,guard,own_pin,guard_pin,native_pin):
        self.args=args;self.m=module;self.g=guard
        self.deadline=DEADLINE;self.g.deadline=self.deadline
        self.pins={};self.rows={};self.dir_stamps={};self.links={};self.entries=0;self.fds=0
        self.output={'format':'swdb.consumed-detached-source-passive-observation.v1','sealed':False,
                     'started_utc':now(),'inventory_row_names':sorted(module.ROWS),
                     'all_rows_are_observation_coverage_not_selection':True,
                     'expected_primary':args.expected_primary,'own_source_pin':own_pin,
                     'R3_definition_source_pin':guard_pin,'native_git_pin':native_pin,
                     'limits':LIMITS,'observations':{},'gaps':[],
                     'historical_classification_or_parent_completeness_generated':False,
                     'deletion_subset_plan_review_seal_or_capacity_admission_generated':False,
                     'scientific_provider_native_application_actions':False,
                     'original_bodies_environment_auth_args_maps_serialized':False,
                     'filesystem_writes_or_Git_mutations':False}
        self.own_pin=own_pin;self.guard_pin=guard_pin;self.native_pin=native_pin
        self.output_bytes_upper=1024*1024+len(canonical(self.output))
    def left(self):
        remain=self.deadline-time.monotonic();require(remain>0,'passive_deadline');return remain
    def gap(self,code,scope):
        item={'code':code,'scope':scope};self.charge(item);self.output['gaps'].append(item)
    def charge(self,value):
        # Each newly serialized row is charged once, including duplicated pin views.
        # A one-MiB structural/finalization reserve avoids N-fold full JSON encoding.
        extra=len(canonical(value))+4
        require(self.output_bytes_upper+extra<=LIMITS['inventory_bytes'],'compact_observation_limit')
        self.output_bytes_upper+=extra
    def size_check(self):
        require(self.output_bytes_upper<=LIMITS['inventory_bytes'],'compact_observation_limit')
    def names(self,raw):
        return sorted(name for name,row in self.m.ROWS.items() if str(row['path']).encode() in raw)
    def bounded_read(self,p,cap=None):
        self.left();p=P(p);require(not denied(p),'excluded_auth_route')
        key=str(p)
        if key in self.pins:
            require(stamp(p.lstat())==self.pins[key]['stat'],'cached_observed_file_changed')
            return self.pins[key],None
        raw,s=self.g.read(p,LIMITS['one_file'] if cap is None else cap)
        fact={'path':key,'bytes':len(raw),'sha256':sha(raw),'stat':s,
              'candidate_reference_rows':self.names(raw),'reference_classification':'unclassified_literal_bytes'}
        self.pins[key]=fact
        return fact,raw
    def walk(self,root):
        """Reuse only R3 read/path/privacy/walk; never any action or plan method."""
        root=P(root)
        if root==PRIMARY:
            # R3.walk does not pass allow_primary_mode for the known setgid primary.
            # Allocation needs only passive stats; preserve the exact R3 primary gate.
            self.g.path(root,directory=True,allow_primary_mode=True)
            def primary_entries():
                for folder,dirs,files in os.walk(root,topdown=True,followlinks=False,
                         onerror=lambda e:(_ for _ in ()).throw(Refused('primary_walk_inaccessible'))):
                    for name in sorted(dirs+files):
                        self.left();p=P(folder)/name;s=p.lstat()
                        self.g.walk_entries+=1
                        require(self.g.walk_entries<=LIMITS['walk_entries'] and s.st_uid==UID,'primary_entry_bound_or_owner')
                        yield p,s
            entries=primary_entries()
        else:entries=self.g.walk(root)
        for p,s in entries:
            self.left();require(not denied(p),'excluded_auth_walk_route')
            self.entries+=1;require(self.entries<=LIMITS['walk_entries'],'passive_entry_limit')
            if stat.S_ISDIR(s.st_mode):self.dir_stamps[str(p)]=stamp(s)
            yield p,s
    def git(self,root,*args):
        """Fixed read-only whitelist, not Guard.git or any action method."""
        approved={('rev-parse','HEAD'),('rev-parse','HEAD^{tree}'),('branch','--show-current'),
                  ('rev-parse','--show-toplevel'),('rev-parse','--path-format=absolute','--git-common-dir'),
                  ('diff','--name-only'),('diff','--cached','--name-only'),
                  ('status','--porcelain','--untracked-files=all'),
                  ('ls-files','--others','--ignored','--exclude-standard','-z'),
                  ('worktree','list','--porcelain'),('for-each-ref','--format=%(refname) %(objectname)'),
                  ('ls-tree','-r','-z',C,'--','swdb-project/swdb'),
                  ('ls-tree','-r','-z',self.args.expected_primary,'--','swdb-project/swdb')}
        require(args in approved or (len(args)==2 and args[0]=='rev-parse' and args[1] in
               ('refs/heads/yanrujhou_main','refs/remotes/origin/yanrujhou_main','refs/remotes/origin/codex/lanl-analytic-eval','codex/lanl-ticket11-source-c')),'readonly_Git_argv')
        self.left();require(stamp(GIT.lstat())==self.native_pin['stat'],'native_git_stat_changed')
        env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_NO_LAZY_FETCH':'1',
             'GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0','GIT_PAGER':'cat',
             'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
        r=subprocess.run([str(GIT),'-c','protocol.allow=never','-c','core.fsmonitor=false',
                          '-c','core.hooksPath=/dev/null','-C',str(root),*args],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,
                         timeout=min(LIMITS['one_git_seconds'],self.left()),check=False)
        require(len(r.stdout)+len(r.stderr)<=LIMITS['inventory_bytes'],'readonly_Git_output_cap')
        require(r.returncode==0 and not r.stderr,'readonly_Git_refused')
        require(stamp(GIT.lstat())==self.native_pin['stat'],'native_git_changed')
        return r.stdout
    def refs(self,root):
        self.g.path(root,directory=True,allow_primary_mode=(root==PRIMARY))
        return {name:self.git(root,*args).decode().strip() for name,args in
                {'head':('rev-parse','HEAD'),'tree':('rev-parse','HEAD^{tree}'),
                 'branch':('branch','--show-current'),'common_dir':('rev-parse','--path-format=absolute','--git-common-dir'),
                 'status':('status','--porcelain','--untracked-files=all')}.items()}
    def policy(self,v):
        fact={'identity_field_present':'identity_sha256' in v,'canonical_policy_field_present':'canonical_ensure_ascii' in v,
              'original_policy_changed_or_resealed':False}
        if 'sealed' in v:fact['original_sealed_field']=v['sealed']
        if 'identity_sha256' not in v:fact['seal_observation']='original_no_identity_field';return fact
        explicit='canonical_ensure_ascii' in v;ascii=v.get('canonical_ensure_ascii',True)
        if type(ascii) is not bool:
            fact['seal_observation']='unknown_nonboolean_original_policy';return fact
        body={k:x for k,x in v.items() if k!='identity_sha256'}
        fact.update(original_identity_sha256=v['identity_sha256'],observed_original_ensure_ascii=ascii,
                    policy_source='explicit_original_field' if explicit else 'original_defaultTrue_observed_without_field_invention',
                    whole_minus_identity_digest_matches=(sha(canonical(body,ascii))==v['identity_sha256']))
        return fact
    def raw_refs(self,value,location=()):
        found=[]
        if isinstance(value,dict):
            for key,item in value.items():
                loc=location+(key if isinstance(key,str) and SAFE_NAME.fullmatch(key) else {'key_sha256':sha(str(key).encode())},)
                found+=self.raw_refs(item,loc)
        elif isinstance(value,list):
            for i,item in enumerate(value):found+=self.raw_refs(item,location+(i,))
        elif isinstance(value,str) and value.startswith(str(RAW)+'/'):
            p=P(value)
            if '\n' in value or '\x00' in value or '..' in p.parts or str(p)!=value or not SAFE_NAME.fullmatch(p.relative_to(RAW).parts[0]):
                self.gap('receipt_RAW_string_not_canonical',{'JSON_location':list(location)})
            else:found.append({'JSON_location':list(location),'path':value,'raw_root':str(RAW/p.relative_to(RAW).parts[0])})
        return found
    def receipts(self):
        out={};rawroots=set()
        for key,row in self.m.RECEIPTS.items():
            p=PRIMARY/self.m.EVIDENCE/row['file'];fact,body=self.bounded_read(p,LIMITS['inventory_bytes'])
            require(body is not None,'receipt_first_read_required')
            require(fact['sha256']==row['sha256'],'original_receipt_byte_pin_changed')
            value=self.m.strict_json(body);refs=self.raw_refs(value)
            expected=[str(RAW/name) for name in row['raw_names']]
            rawroots.update(expected);rawroots.update(r['raw_root'] for r in refs)
            item={'file_pin':fact,'original_policy':self.policy(value),'R3_introduced_commit':row['introduced'],
                      'R3_declared_raw_roots':expected,'observed_absolute_RAW_references':refs,
                      'seal_semantics_or_historical_classification_not_generated':True}
            self.charge(item);out[key]=item
            self.output['observations']['receipt_files']=out;self.size_check()
        require(len(out)==22,'exact_R3_receipt_count')
        return rawroots
    def file_inventory(self,root,hash_all,metadata_hits):
        root=P(root);root_stat=stamp(root.lstat());self.dir_stamps[str(root)]=root_stat
        result={'path':str(root),'root_stat':root_stat,'files':[],'directories':[],'symlinks':[],
                'scope_complete_within_observed_limits':False,
                'regular_file_hash_scope':'all_regular_files' if hash_all else 'metadata_suffixes_only',
                'regular_file_logical_bytes_observed':0,
                'allocated_bytes_unique_dev_inode_st_blocks512':root.lstat().st_blocks*512,
                'allocation_is_partial_until_scope_finished':True}
        seen={(root_stat['dev'],root_stat['ino'])}
        if root.parent==RAW:
            self.output['observations']['raw_trees_and_control_sibling_candidates'][str(root)]=result
        elif root==EV:self.output['observations']['PRIMARY_evidence_metadata_inventory']=result
        else:self.output['observations']['PRIMARY_records_metadata_inventory']=result
        for p,s in self.walk(root):
            rel=p.relative_to(root).as_posix()
            identity=(s.st_dev,s.st_ino)
            if identity not in seen:
                seen.add(identity);result['allocated_bytes_unique_dev_inode_st_blocks512']+=s.st_blocks*512
                if stat.S_ISREG(s.st_mode):result['regular_file_logical_bytes_observed']+=s.st_size
            if stat.S_ISDIR(s.st_mode):
                item={'relative_path':rel,'stat':stamp(s)};self.charge(item);result['directories'].append(item)
            elif stat.S_ISLNK(s.st_mode):
                link=os.readlink(p)
                try:resolved=str(p.resolve(strict=True));resolution='resolved'
                except (OSError,RuntimeError):resolved=None;resolution='unresolved';self.gap('unresolved_symlink',{'path':str(p)})
                hits=sorted(name for name,row in self.m.ROWS.items() if resolved and inside(resolved,P(row['path'])))
                item={'path':str(p),'relative_path':rel,'stat':stamp(s),'link_sha256':sha(link.encode()),
                      'resolution':resolution,'resolved_candidate_rows':hits,
                      'resolved_scoped_path':resolved if resolved and (inside(resolved,BASE) or inside(resolved,RAW)) and not denied(P(resolved)) else None,
                      'resolved_foreign_or_private_path_not_serialized':bool(resolved and not (inside(resolved,BASE) or inside(resolved,RAW)))}
                self.charge(item);self.links[str(p)]={'stat':stamp(s),'link':link};result['symlinks'].append(item)
            elif stat.S_ISREG(s.st_mode):
                if hash_all or p.suffix in SUFFIXES:
                    fact,_=self.bounded_read(p);self.charge(fact);result['files'].append(fact)
                    if metadata_hits and p.suffix in SUFFIXES and fact['candidate_reference_rows']:
                        self.charge(fact);self.output['observations'].setdefault('unclassified_candidate_reference_files',[]).append(fact)
            else:self.gap('unsupported_inventory_entry',{'path':str(p)})
            self.size_check()
        result['scope_complete_within_observed_limits']=True
        result['allocation_is_partial_until_scope_finished']=False
        return result
    def allocations(self,root):
        root=P(root);s=root.lstat();seen={(s.st_dev,s.st_ino)}
        logical=0;allocated=s.st_blocks*512;count=1
        for p,st in self.walk(root):
            key=(st.st_dev,st.st_ino)
            if key in seen:continue
            seen.add(key);count+=1;allocated+=st.st_blocks*512
            if stat.S_ISREG(st.st_mode):logical+=st.st_size
        return {'path':str(root),'observed_directory_stat':stamp(s),'entries':count,
                'regular_file_logical_bytes':logical,'allocated_bytes_unique_dev_inode_st_blocks512':allocated,
                'registered_shared_Git_object_storage_not_assigned_to_checkout':True,'recovery_or_capacity_clearance':False}
    def candidate_inventory(self):
        out={}
        for name,row in self.m.ROWS.items():
            p=P(row['path'])
            if not os.path.lexists(p):out[name]={'path':str(p),'present':False};self.gap('candidate_absent',{'row':name});continue
            refs=self.refs(p);ignored=self.git(p,'ls-files','--others','--ignored','--exclude-standard','-z')
            out[name]={'path':str(p),'present':True,'R3_expected_head':row['head'],
                       'observed_refs':refs,'matches_R3_HEAD':refs['head']==row['head'],
                       'detached_observed':refs['branch']=='','tracked_untracked_status_empty':refs['status']=='',
                       'ignored_entries':len([x for x in ignored.split(b'\0') if x]),
                       'ignored_path_list_sha256':sha(ignored),'allocation':self.allocations(p),
                       'R3_receipt_keys':row['receipts'],'eligible_or_selected_for_cleanup':False}
            self.charge(out[name]);self.output['observations']['candidate_checkouts']=out;self.size_check()
        require(len(out)==18,'exact18_inventory_rows')
    def future_sources(self,evidence_inventory):
        found={name:[] for name in self.m.FUTURE_SOURCE_HASHES}
        for pin in evidence_inventory['files']:
            name=P(pin['path']).name
            if name in found:
                expected=self.m.FUTURE_SOURCE_HASHES[name]
                if pin['bytes']<=LIMITS['future_source_bytes'] and pin['bytes']==expected['bytes'] and pin['sha256']==expected['sha256'] and pin['stat']['nlink']==1:
                    self.charge(pin);found[name].append(pin)
        for name,values in found.items():
            if not values:self.gap('future_source_pin_not_observed_in_durable_evidence',{'basename':name})
        return {'exact_R3_expected_pin_sources':found,'choice_or_staged_alias_completeness_not_generated':True,
                'only_PRIMARY_evidence_searched':True,'actual_staged_aliases_are_separate_parent_pending_protected_pins':True}
    def account_service_review(self):
        # Input semantic review is not a plan/clearance generated by this observer.
        path=P(self.args.account_service_review)
        require(path==BASE/'lanl-account-pam-service-identification-20261008-a1/parent-review.json',
                'fixed_account_service_review_route')
        pin,raw=self.bounded_read(path,256*1024)
        require(raw is not None and pin['sha256']==self.args.account_service_review_sha256,
                'account_service_review_original_byte_pin')
        review=self.m.strict_json(raw)
        require(review['format']=='swdb.exact-account-service-semantic-parent-review.v1'
                and review['canonical_ensure_ascii'] is True
                and review['accepted_for_exact_service_role_exclusion'] is True
                and re.fullmatch('[0-9a-f]{64}',review['identity_sha256'])
                and review['identity_sha256']==sha(canonical({k:v for k,v in review.items() if k!='identity_sha256'},True)),
                'account_service_review_original_True_seal_or_role')
        original_pin={'path':str(BASE/'lanl-account-pam-service-identification-20261008-a1/identification.json'),
                      'bytes':3818,'sha256':'ece0155e6a1e61e07cabb8a05e2a13ac9577a9ee1418e8f8eed450ce310ce0fa'}
        require(review['original_identification_pin']==original_pin
                and review['shared_helper_source_sha256']=='f6c4076013eaa487c0e810ba4329512657bef9b1b74a0c074a7231bcc0466883'
                and review['reviewed_guard_source']=={'path':'/private/tmp/lanl_consumed_detached_source_guard_r4_20261008_r1.py',
                    'bytes':81694,'sha256':'d30481a540a40f0c4b4695e105dc25f6febf152e391b5a34861b817d0d6960a6'},
                'account_service_review_original_or_helper_source_changed')
        proofs=[{'path':str(EV/'14-supervised-r5-export-actual-custody-20261008-a1/actual/remote-preregistration.json'),
                 'bytes':39887,'sha256':'70a8a1a4c99a46f92a2e9f7291daabe8305a0aa20927570cc9947adf5fc72987',
                 'original_policy_not_modified':True},
                {'path':str(EV/'14-generality-final-final-20261007-a1-export.json'),
                 'bytes':32840,'sha256':'02b369f0624964fa4293f563a7b51e142dc369101147ac7fe848503c4b50eb5d',
                 'original_policy_not_modified':True}]
        require(review['original_fresh_E_custody_pins']==proofs
                and review['trusted_systemd_lifecycle_source']=='https://github.com/systemd/systemd-stable/blob/v255.4/src/core/exec-invoke.c#L1213-L1291'
                and review['signal_wait_kernel_source']=='https://github.com/torvalds/linux/blob/v6.8/kernel/signal.c#L3629-L3645'
                and type(review['assumption']) is str and bool(review['assumption'])
                and type(review['fresh_E_creation_semantic_basis']) is str and bool(review['fresh_E_creation_semantic_basis'])
                and review['protected_child_fields_unobserved']==['fd','cwd','root','exe','maps','syscall','meaningful_wait_channel']
                and review['service_reference_free_or_global_visibility_claimed'] is False
                and review['selected_source_subset_or_actual_guard_cleanup_admitted'] is False
                and review['scientific_admission'] is False and review['capacity_admission'] is False,
                'account_service_review_semantic_scope_or_original_proofs_changed')
        for proof in proofs:
            proof_pin,_=self.bounded_read(P(proof['path']),256*1024)
            require(proof_pin['bytes']==proof['bytes'] and proof_pin['sha256']==proof['sha256'],
                    'account_service_original_fresh_E_custody_byte_pin_changed')
        # The definition's exact globals use hash-verified R3 pure functions;
        # no Guard table/method mutation or fabricated plan is needed.
        helper_globals={key:getattr(self.m,key) for key in
                       ('P','BASE','UID','LIMITS','require','sha','strict_json','stamp','os','re','stat')}
        helper_globals['__builtins__']=self.m.__dict__['__builtins__']
        helper=types.FunctionType(exact_account_pam_service_identification.__code__,helper_globals,
                                  'exact_account_pam_service_identification')
        item={'original_review_file_pin':pin,'original_review_policy':'explicit_original_True',
              'original_identity_sha256':review['identity_sha256'],
              'accepted_for_exact_service_role_exclusion_input':True,
              'original_identification_pin':original_pin,
              'shared_helper_source_pin':{'bytes':11151,
                  'sha256':'f6c4076013eaa487c0e810ba4329512657bef9b1b74a0c074a7231bcc0466883'},
              'trusted_OS_role_and_fresh_E_creation_are_parent_semantic_binding':True,
              'service_reference_free_or_global_visibility_or_cleanup_clearance_generated':False}
        self.charge(item)
        self.output['observations']['account_service_original_semantic_review_input']=item
        return helper,original_pin,review['identity_sha256']

    def portal_service_review(self):
        path=P(self.args.portal_service_review)
        require(path==BASE/'lanl-portal-helper-inode-review-20261008-a1/parent-review.json',
                'fixed_portal_service_review_route')
        pin,raw=self.bounded_read(path,256*1024)
        require(raw is not None and pin['sha256']==self.args.portal_service_review_sha256,
                'portal_service_review_original_byte_pin')
        review=self.m.strict_json(raw)
        require(review['canonical_ensure_ascii'] is True and re.fullmatch('[0-9a-f]{64}',review['identity_sha256'])
                and sha(canonical({k:v for k,v in review.items() if k!='identity_sha256'}))==review['identity_sha256']
                and review['shared_helper_sha256']==PORTAL_HELPER_SHA==self.m.PORTAL_HELPER_SHA,
                'portal_service_review_original_True_seal_or_shared_source')
        self.output['observations']['portal_service_original_semantic_review_input']={
            'original_file_pin':pin,'original_policy':'explicit_original_True',
            'identity_sha256':review['identity_sha256'],
            'semantic_assumptions_inherited_from_parent_review':True,
            'capacity_plan_cleanup_or_scientific_admission_generated':False}
        pin=dict(pin,identity_sha256=review['identity_sha256'],canonical_ensure_ascii=True)
        return pin,review['identity_sha256']

    def owned_processes(self):
        snapshots={};inaccessible_foreign=0
        procs=sorted((p for p in P('/proc').iterdir() if p.name.isdecimal()),key=lambda p:int(p.name))
        require(len(procs)<=LIMITS['processes'],'process_count_limit')
        for proc in procs:
            self.left();owner=None
            try:
                owner=proc.stat().st_uid;raw=self.g.proc_read(proc/'status',LIMITS['one_proc_bytes'])
                if raw is None:continue
            except FileNotFoundError:
                if not proc.exists():continue
                raise Refused('process_snapshot_field_missing')
            except PermissionError:
                if owner==UID:raise Refused('owned_process_snapshot_inaccessible')
                inaccessible_foreign+=1;continue
            except self.m.Refused:
                if owner==UID:raise
                inaccessible_foreign+=1;continue
            fields=dict(line.split(':',1) for line in raw.decode().splitlines() if ':' in line)
            snapshots[int(proc.name)]={'path':proc,'uids':[int(x) for x in fields['Uid'].split()],
                                       'ppid':int(fields['PPid']),'state':fields['State'].split()[0],
                                       'threads':int(fields['Threads'])}
        owned={pid for pid,row in snapshots.items() if UID in row['uids']}
        relevant=set(owned)
        for pid,row in snapshots.items():
            seen=set();parent=row['ppid']
            while parent in snapshots and parent not in seen:
                seen.add(parent)
                if parent in owned:relevant.add(pid);break
                parent=snapshots[parent]['ppid']
        helper,identification_pin,review_identity=self.account_service_review()
        portal_pin,portal_review_identity=self.portal_service_review()
        def charge_service_bytes(count):
            self.g.read_bytes+=count
            require(self.g.read_bytes<=LIMITS['total_file_bytes'],'cumulative_account_service_read_limit')
        records=[];excluded=[];terminal_zombies=[]
        for pid in sorted(relevant):
            self.left();r=snapshots[pid];proc=r['path']
            before=self.g.proc_read(proc/'stat',LIMITS['one_proc_bytes'])
            if before is None:continue
            start=int(before[before.rfind(b')')+2:].split()[19]);hits=[]
            if pid==1654291:
                # Exact errors are outside the inherited disappearing-process catch.
                def charge_portal_metadata(entries,checks,unused_fds):
                    require(unused_fds==0,'portal_unexpected_process_FD_debit')
                    self.g.walk_entries+=entries;self.g.stat_checks+=checks
                    require(self.g.walk_entries<=LIMITS['walk_entries']
                            and self.g.stat_checks<=self.m.LIMITS['stat_checks'],'portal_metadata_limit')
                    self.left()
                audit=exact_portal_autounmount_identification(portal_pin,self.m.ROWS,sorted(self.m.ROWS),[],
                    portal_review_identity,PORTAL_HELPER_SHA,self.left,charge_service_bytes,charge_portal_metadata)
                require(start==audit['start_ticks'],'portal_snapshot_PID_changed')
                self.charge(audit);excluded.append(audit)
                continue
            if pid==359656:
                # Deliberately outside the inherited disappearing-process catch:
                # missing native/original evidence must fail, never skip the predicate.
                audit=helper(identification_pin,review_identity,self.left,charge_service_bytes)
                require(start==audit['start_ticks'],'account_service_snapshot_PID_changed')
                self.charge(audit);excluded.append(audit)
                continue
            if r['state']=='Z':
                # Linux v6.8 do_exit clears task mm/files/fs before EXIT_ZOMBIE.
                # Require one thread so a dead leader cannot hide live siblings.
                before_values=before[before.rfind(b')')+2:].split()
                require(before_values[0]==b'Z' and int(before_values[1])==r['ppid']
                        and r['threads']==1,'terminal_zombie_initial_public_identity_changed')
                status=self.g.proc_read(proc/'status',LIMITS['one_proc_bytes'])
                require(status is not None,'terminal_zombie_status_disappeared')
                terminal_fields={}
                for line in status.decode().splitlines():
                    if ':' in line:
                        key,value=line.split(':',1)
                        require(key not in terminal_fields,'terminal_zombie_duplicate_status')
                        terminal_fields[key]=value.strip()
                terminal_uids=[int(value) for value in terminal_fields['Uid'].split()]
                require(terminal_fields['State'].split()[:1]==['Z']
                        and int(terminal_fields['Pid'])==pid
                        and int(terminal_fields['PPid'])==r['ppid']
                        and terminal_uids==r['uids'] and int(terminal_fields['Threads'])==1,
                        'terminal_zombie_fresh_public_identity_changed')
                after=self.g.proc_read(proc/'stat',LIMITS['one_proc_bytes'])
                require(after is not None,'terminal_zombie_final_stat_disappeared')
                after_values=after[after.rfind(b')')+2:].split()
                require(after_values[0]==b'Z' and int(after_values[19])==start
                        and int(after_values[1])==r['ppid'],
                        'terminal_zombie_final_state_PID_or_parent_changed')
                audit={'pid':pid,'start_ticks':start,'ppid':r['ppid'],'uids':terminal_uids,
                    'state':'Z','threads':1,'captured_status_and_fresh_before_after_stat_Z':True,
                    'fresh_public_status_pin':{'bytes':len(status),'sha256':sha(status)},
                    'protected_references':{key:'UNOBSERVED' for key in ('fd','cwd','root','exe','maps')},
                    'kernel_terminal_resource_release_basis':
                        'https://github.com/torvalds/linux/blob/v6.8/kernel/exit.c#L858-L891',
                    'kernel_terminal_mm_files_fs_invariant_is_explicit_assumption':True,
                    'other_threads_or_live_consumers_exempted':False,
                    'global_reference_free_or_cleanup_clearance_claimed':False}
                self.charge(audit);terminal_zombies.append(audit)
                continue
            try:
                links=[proc/'cwd',proc/'root',proc/'exe',*sorted((proc/'fd').iterdir())]
                self.fds+=len(links);require(self.fds<=LIMITS['process_fds'],'process_fd_limit')
                for link in links:
                    try:target=os.readlink(link)
                    except FileNotFoundError:continue
                    names=sorted(n for n,row in self.m.ROWS.items() if inside(target.removesuffix(' (deleted)'),P(row['path'])))
                    if names:hits.append({'kind':'fd' if link.parent.name=='fd' else link.name,'candidate_rows':names,'target_sha256':sha(target.encode())})
                for name in ('cmdline','maps'):
                    body=self.g.proc_read(proc/name,LIMITS['one_proc_bytes'])
                    if body is None:continue
                    matched=self.names(body)
                    if matched:hits.append({'kind':name,'candidate_rows':matched})
                after=self.g.proc_read(proc/'stat',LIMITS['one_proc_bytes'])
                if after is None:continue
                require(int(after[after.rfind(b')')+2:].split()[19])==start,'process_PID_reused')
                item={'pid':pid,'uids':r['uids'],'ppid':r['ppid'],'start_ticks':start,
                                'state':r['state'],'candidate_references':hits}
                self.charge(item);records.append(item)
            except FileNotFoundError:
                if proc.exists():raise Refused('relevant_process_field_missing')
        return {'owned_or_owned_descendant_snapshots':records,'process_links_observed':self.fds,
                'excluded_exact_system_services':excluded,
                'stable_single_thread_terminal_zombie_audits':terminal_zombies,
                'excluded_service_protected_references_unobserved_not_reference_free':True,
                'other_owned_or_owned_descendant_inaccessible_references_still_refuse':True,
                'inaccessible_unidentified_process_count':inaccessible_foreign,
                'privileged_identified_consumers_require_separate_parent_original_evidence':True,
                'args_maps_environment_auth_bodies_not_transferred':True,'global_clearance_not_claimed':True,
                'one_finite_snapshot_no_future_or_global_consumers_clearance':True}
    def acquire(self):
        self.output['observations']['initial_private_ancestor_roots']=self.g.privacy_gate()
        require(not os.path.lexists(E_CHECKOUT),'expected_E_checkout_cleanup_not_complete')
        primary=self.refs(PRIMARY)
        require(primary['head']==self.args.expected_primary and primary['branch']=='yanrujhou_main','expected_primary_or_branch')
        require(not self.git(PRIMARY,'diff','--name-only') and not self.git(PRIMARY,'diff','--cached','--name-only'),'primary_tracked_dirty')
        require(primary['status']=='?? swdb-project/records/.retention.lock','primary_untracked_retention_only')
        for ref in ('refs/heads/yanrujhou_main','refs/remotes/origin/yanrujhou_main','refs/remotes/origin/codex/lanl-analytic-eval'):
            require(self.git(PRIMARY,'rev-parse',ref).decode().strip()==self.args.expected_primary,'primary_delivery_ref')
        require(self.git(PRIMARY,'rev-parse','codex/lanl-ticket11-source-c').decode().strip()==C,'retained_C_ref')
        crows=self.git(PRIMARY,'ls-tree','-r','-z',C,'--','swdb-project/swdb')
        rrows=self.git(PRIMARY,'ls-tree','-r','-z',self.args.expected_primary,'--','swdb-project/swdb')
        require(crows==rrows and len([x for x in crows.split(b'\0') if x and x.split(b'\t',1)[1].endswith(b'.py')])==185,'C_namespace_or185_changed')
        lock,_=self.bounded_read(PRIMARY/'swdb-project/records/.retention.lock',1)
        require(lock['bytes']==0 and lock['sha256']==sha(b''),'retention_empty_original')
        self.output['observations']['primary']={'refs':primary,'retention_file_pin':lock,
               'C_source_ref':C,'source_namespace_entries':len([x for x in crows.split(b'\0') if x]),
               'C_source_namespace_exact':True,'Python_modules':185,'inherited_F6':F6,
               'final_R17_identity_or_allocation_choice_not_inferred':True,
               'registered_worktrees':self.git(PRIMARY,'worktree','list','--porcelain').decode(),
               'retained_refs':self.git(PRIMARY,'for-each-ref','--format=%(refname) %(objectname)').decode()}
        self.output['observations']['leases']={}
        for name in self.m.LEASES:
            fact,body=self.bounded_read(BASE/'lact-host-lease'/(name+'.meta.json'),128*1024)
            require(body is not None,'lease_first_read');value=self.m.strict_json(body)
            require(value.get('state')=='released','lease_not_released')
            self.output['observations']['leases'][name]={'file_pin':fact,'observed_state':'released'}
        roots=self.receipts()
        namespace=[]
        for p in sorted(RAW.iterdir()):
            if p.name.startswith(('lanl-','lanl17-')):
                require(SAFE_NAME.fullmatch(p.name),'raw_root_name');namespace.append(p.name)
        self.output['observations']['raw_namespace_names']=namespace
        self.output['observations']['receipt_declared_and_observed_RAW_roots']=sorted(roots)
        self.output['observations']['raw_trees_and_control_sibling_candidates']={}
        sidecar=exact_original_raw_lane_sidecar(self.left,[P(row['path']) for row in self.m.ROWS.values()])
        self.g.read_bytes+=sidecar['bytes']
        require(self.g.read_bytes<=LIMITS['total_file_bytes'],'cumulative_original_top_sidecar_read_limit')
        require(P(sidecar['path']).name in namespace,'original_top_sidecar_namespace_retained')
        require(not any(str(RAW/name)==sidecar['path'] for row in self.m.RECEIPTS.values() for name in row['raw_names']),
                'declared_receipt_roots_remain_directories')
        self.pins[sidecar['path']]={**sidecar,'candidate_reference_rows':[],
                                  'reference_classification':'exact_original_literal_and_JSON_reference_check_no_selected_rows'}
        self.output['observations']['original_top_regular_sidecars']=[sidecar]
        self.charge(sidecar)
        # Every LANL namespace sibling is observed; only the parent classifies controls.
        for name in namespace:
            root=RAW/name
            if root==P(sidecar['path']):
                require(stamp(root.lstat())==sidecar['stat'],'original_top_sidecar_still_exact')
                continue
            require(not root.is_symlink() and root.is_dir(),'raw_namespace_root_redirect')
            inv=self.file_inventory(root,(str(root) in roots),True)
            inv['declared_or_referenced_by_original_receipts']=str(root) in roots
            inv['control_sibling_or_original_raw_classification']='parent_review_required'
            self.output['observations']['raw_trees_and_control_sibling_candidates'][str(root)]=inv
            self.size_check()
        for root in sorted(roots):
            if P(root).name not in namespace:self.gap('receipt_RAW_root_absent_from_observed_namespace',{'root':root})
        evidence=self.file_inventory(EV,False,True)
        records=self.file_inventory(PRIMARY/'swdb-project/records',False,True)
        self.output['observations']['PRIMARY_evidence_metadata_inventory']=evidence
        self.output['observations']['PRIMARY_records_metadata_inventory']=records
        self.output['observations']['future_13_source_pins']=self.future_sources(evidence)
        self.candidate_inventory()
        protected={}
        for root,expected in ((self.m.C_PATH,self.m.C),(self.m.COUNT_PATH,self.m.COUNT),(self.m.R14_PATH,self.m.R14)):
            protected[str(root)]={'observed_refs':self.refs(root),'R3_expected_HEAD':expected,
                                  'allocation':self.allocations(root),'protection_or_cleanup_clearance_not_inferred':True}
            self.charge(protected[str(root)])
        self.output['observations']['protected_execution_checkouts']=protected
        self.output['observations']['primary_allocation']=self.allocations(PRIMARY)
        self.output['observations']['fresh_statvfs_free_bytes']={str(p):os.statvfs(p).f_bavail*os.statvfs(p).f_frsize for p in (P('/data1'),P('/data'))}
        self.output['observations']['owned_process_coverage']=self.owned_processes()
        require(sorted(p.name for p in RAW.iterdir() if p.name.startswith(('lanl-','lanl17-')))==namespace,'raw_namespace_changed')
        require(exact_original_raw_lane_sidecar(self.left,[P(row['path']) for row in self.m.ROWS.values()])==sidecar,
                'original_top_sidecar_final_bytes_stat_and_references')
        self.g.read_bytes+=sidecar['bytes']
        require(self.g.read_bytes<=LIMITS['total_file_bytes'],'final_cumulative_original_top_sidecar_read_limit')
        for path,pin in self.pins.items():require(stamp(P(path).lstat())==pin['stat'],'observed_file_stat_changed')
        for path,s in self.dir_stamps.items():require(stamp(P(path).lstat())==s,'observed_directory_changed')
        for path,row in self.links.items():require(stamp(P(path).lstat())==row['stat'] and os.readlink(path)==row['link'],'observed_symlink_changed')
        require(self.refs(PRIMARY)==primary,'primary_refs_or_status_changed')
        for name,item in self.output['observations']['leases'].items():require(stamp(P(item['file_pin']['path']).lstat())==item['file_pin']['stat'],'lease_snapshot_changed')
        for root,item in self.output['observations']['protected_execution_checkouts'].items():
            require(self.refs(P(root))==item['observed_refs'],'protected_checkout_refs_or_status_changed')
        self.output['observations']['final_private_ancestor_roots']=self.g.privacy_gate()
        self.output['stable_at_end_of_observation']=True
        self.output['source_or_raw_semantic_quiescence_not_proved']=True
    def finish(self):
        # Original byte/source rechecks; no rehash of scientific inventories here.
        for p,cap,owner,pin in ((P(self.own_pin['path']),LIMITS['future_source_bytes'],UID,self.own_pin),
                               (R3,LIMITS['future_source_bytes'],UID,self.guard_pin),
                               (GIT,LIMITS['inventory_bytes'],0,self.native_pin)):
            require(self.g.read_bytes+pin['bytes']<=LIMITS['total_file_bytes'],'end_cumulative_read_limit')
            _,later=bootstrap_read(p,cap,owner);self.g.read_bytes+=later['bytes']
            require(later==pin,'end_source_pin_changed')
        self.output['finished_utc']=now();self.output['bytes_hashed_or_read']=self.g.read_bytes
        self.output['walk_entries_observed']=self.g.walk_entries
        self.output['parent_review_and_source_proof_supplier_required']=True
        self.output['observation_complete_within_finite_scope']=not self.output['gaps'] and 'failure' not in self.output
        require(len(canonical(self.output))<=LIMITS['inventory_bytes'],'final_compact_observation_limit');return self.output

def main():
    global DEADLINE
    DEADLINE=time.monotonic()+LIMITS['passive_seconds']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-primary',required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--account-service-review',required=True)
    parser.add_argument('--account-service-review-sha256',required=True)
    parser.add_argument('--portal-service-review',required=True)
    parser.add_argument('--portal-service-review-sha256',required=True)
    args=parser.parse_args();require(re.fullmatch('[0-9a-f]{40}',args.expected_primary),'exact40_expected_primary')
    require(re.fullmatch('[0-9a-f]{64}',args.account_service_review_sha256),'account_service_review_file_pin_argument')
    require(re.fullmatch('[0-9a-f]{64}',args.portal_service_review_sha256),'portal_service_review_file_pin_argument')
    require(re.fullmatch('[0-9a-f]{64}',args.source_sha256),'own_source_pin_argument')
    require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.uname().machine=='x86_64'
            and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name==ACCOUNT,'host_account')
    own=P(__file__).absolute();require(inside(str(own),BASE) and not inside(str(own),PRIMARY),'private_explicit_parent_source_route')
    own_body,own_pin=bootstrap_read(own,LIMITS['future_source_bytes'],UID)
    require(own_pin['sha256']==args.source_sha256,'own_source_changed')
    guard_body,guard_pin=bootstrap_read(R3,LIMITS['future_source_bytes'],UID)
    require(guard_pin['bytes']==R3_BYTES and guard_pin['sha256']==R3_SHA,'reviewed_R3_source')
    git_body,native_pin=bootstrap_read(GIT,LIMITS['inventory_bytes'],0)
    require(native_pin['bytes']==GIT_BYTES and native_pin['sha256']==GIT_SHA and not native_pin['stat']['mode']&0o7022,'native_git_pin')
    module=types.ModuleType('reviewed_R3_passive_definitions');module.__file__=str(R3)
    exec(compile(guard_body,str(R3),'exec'),module.__dict__)
    require(module.__name__!='__main__','R3_main_unreachable')
    guard=module.Guard(types.SimpleNamespace(select=sorted(module.ROWS),remove=False,expected_primary=args.expected_primary))
    guard.read_bytes=len(own_body)+len(guard_body)+len(git_body)
    require(guard.read_bytes<=LIMITS['total_file_bytes'],'bootstrap_cumulative_read_limit')
    observer=Observer(args,module,guard,own_pin,guard_pin,native_pin)
    code=0
    try:observer.acquire()
    except BaseException as exc:
        code=1;observer.output['failure']={'class':type(exc).__name__,'code':str(exc) if isinstance(exc,(Refused,module.Refused)) else 'original_exception_text_not_transferred'}
        observer.output['stable_at_end_of_observation']=False
    try:result=observer.finish()
    except BaseException as exc:
        code=1;result={'format':'swdb.consumed-detached-source-passive-observation-failure.v1','sealed':False,
                      'failure_class':type(exc).__name__,'code':str(exc) if isinstance(exc,Refused) else 'source_or_output_finalization_failed',
                      'no_plan_review_subset_seal_removal_or_admission_generated':True}
    print(json.dumps(result,sort_keys=True,ensure_ascii=True,allow_nan=False))
    return code

if __name__=='__main__':
    try:exit_code=main()
    except BaseException as exc:
        print(json.dumps({'format':'swdb.consumed-detached-source-passive-bootstrap-failure.v1','sealed':False,
                          'failure_class':type(exc).__name__,
                          'code':str(exc) if isinstance(exc,Refused) else 'exception_text_not_transferred',
                          'no_acquisition_success_or_plan_or_removal_inferred':True},sort_keys=True))
        exit_code=1
    raise SystemExit(exit_code)
