#!/usr/bin/env python3
"""Verify and publish two parent-authored originals; never author plan facts or seals."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import signal
import socket
import stat
import sys
import time

BASE = Path('/data1/yanruj')
UID = 114316761
PRIMARY = '5e12a9796432654d88def24ecea617d16ca605b2'
GUARD_SHA = 'd75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
PYTHON = Path('/usr/bin/python3.12')
PYTHON_BYTES = 8020928
PYTHON_SHA = 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
BODY_CAP = 2*1024*1024
HEADER_CAP = 16384
BACKLINKS = ('control_siblings_complete_review', 'pending_alias_coverage_review',
             'receipt_source_proofs_complete_review', 'original_raw_files_complete_review')
REQUIRED_PLAN = set(BACKLINKS) | {
    'format', 'canonical_ensure_ascii', 'identity_sha256', 'checked_at',
    'guard_source_sha256', 'expected_primary', 'selected_rows', 'selection_reason',
    'allocation_decision', 'allocation_observation_pin', 'parent_review_pin',
    'native_git_pin', 'account_service_identification_pin', 'portal_service_review_pin',
    'additional_protected_paths', 'common_configuration_pin', 'future_source_pins',
    'historical_reference_files', 'original_raw_file_pins', 'pending_control_files',
    'protected_file_pins', 'raw_control_sibling_paths', 'receipt_source_file_proofs',
    'relevant_privileged_consumers', 'reserved_absent_paths', 'retained_raw_library_aliases',
    'retirement_operation', 'shared_config_and_main_index_must_remain_exact'}
ROWS = {
    'ArchEvolve-lanl-allocator-a2-20261006', 'ArchEvolve-lanl-bulk-services-20261006-a1',
    'ArchEvolve-lanl-bulk-total-services-20261006-a1', 'ArchEvolve-lanl-clock-a2-20261006',
    'ArchEvolve-lanl-estimates-20261006', 'ArchEvolve-lanl-estimation-role-20261006-a1',
    'ArchEvolve-lanl-estimation-role-20261006-a2', 'ArchEvolve-lanl-float-memory-services-20261006-a1',
    'ArchEvolve-lanl-functional-evaluation-20261006-a1', 'ArchEvolve-lanl-functional-object-counts-20261006-a2',
    'ArchEvolve-lanl-functional-strict-20261006', 'ArchEvolve-lanl-independent-services-20261006-a1',
    'ArchEvolve-lanl-memory-a1-20261006', 'ArchEvolve-lanl-native-object-counts-20261006-a1',
    'ArchEvolve-lanl-openmp-projections-20261006-a1', 'ArchEvolve-lanl-prospective-inputs-20261006-a2',
    'ArchEvolve-lanl-root-projection-20261006'}
START = time.monotonic()

class Refused(Exception):
    pass

REASON_CODES = frozenset(('allocation_binding', 'base_identity', 'base_replaced', 'base_route', 'consumer_list_schema', 'descriptor_bound_policy', 'descriptor_digest', 'descriptor_path', 'descriptor_route', 'descriptor_schema', 'distinct_publication_paths', 'duplicate_json_key', 'explicit_allowed_unique_rows', 'file_cap', 'file_identity', 'file_mode', 'file_open_changed', 'file_read_changed', 'file_route_changed', 'final_source_native_base_changed', 'fixed_native_shared_scope', 'framing_header', 'guard_plan_list_schema', 'guard_plan_object_schema', 'guard_plan_required_fields', 'header_cap', 'json_object_required', 'native_host_flags', 'native_python_byte_pin', 'nonfinite_json', 'original_byte_pin', 'original_configuration_review_binding', 'original_policy_or_identity', 'original_review_file_pin', 'original_seal', 'plan_age', 'plan_aware_time', 'publication_identity', 'publication_original_changed', 'publication_path_exists', 'publication_write', 'publisher_deadline', 'publisher_source_byte_pin', 'publisher_source_direct_base', 'selected_guard_primary', 'selected_operation_schema', 'selection_reason_missing', 'source_pin', 'stdin_trailing_bytes', 'stdin_truncated'))

def reason_code(error):
    if type(error) is Refused and len(error.args)==1 and type(error.args[0]) is str:
        code=error.args[0]
        if code in REASON_CODES or code in {
                'publisher_signal_'+str(int(s)) for s in
                (signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT)}:
            return code
        return 'unclassified_refusal'
    return 'non_refused_exception'

def need(ok, reason):
    if not ok:
        raise Refused(reason)

def left():
    need(time.monotonic()-START <= 90, 'publisher_deadline')

def stop(signum, frame):
    raise Refused('publisher_signal_'+str(signum))

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def stamp(s):
    return {k:getattr(s, 'st_'+k) for k in
            ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}

def canonical(d):
    return json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()

def parse(raw):
    def pairs(items):
        d = {}
        for k,v in items:
            need(k not in d, 'duplicate_json_key')
            d[k] = v
        return d
    def bad(value):
        raise Refused('nonfinite_json')
    d = json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
    need(type(d) is dict, 'json_object_required')
    return d

def file_bytes(p, cap, owner, mode=None):
    left()
    need(p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)), 'file_route_changed')
    before = p.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid==owner and before.st_nlink==1
         and before.st_size<=cap and not before.st_mode & 0o7022, 'file_identity')
    if mode is not None:
        need(stat.S_IMODE(before.st_mode)==mode, 'file_mode')
    fd = os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        need(stamp(os.fstat(fd))==stamp(before), 'file_open_changed')
        parts=[]; count=0
        while True:
            left(); part=os.read(fd,min(65536,cap-count+1))
            if not part:
                break
            count+=len(part); need(count<=cap,'file_cap'); parts.append(part)
        need(count==before.st_size and stamp(os.fstat(fd))==stamp(before)==stamp(p.lstat()), 'file_read_changed')
        return b''.join(parts),stamp(before)
    finally:
        os.close(fd)

def base_identity(fd):
    left()
    need(BASE.resolve(strict=True)==BASE and not any(p.is_symlink() for p in (BASE,*BASE.parents)), 'base_route')
    s=BASE.lstat(); f=os.fstat(fd)
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
         and (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)==(f.st_dev,f.st_ino,f.st_uid,f.st_gid,f.st_mode), 'base_identity')
    return {k:stamp(s)[k] for k in ('dev','ino','uid','gid','mode')}

def exact_stdin(count):
    parts=[]; remaining=count
    while remaining:
        left(); b=os.read(0,min(65536,remaining))
        need(b, 'stdin_truncated'); parts.append(b); remaining-=len(b)
    return b''.join(parts)

def descriptor(d, prefix):
    need(type(d) is dict and set(d)=={'path','bytes','sha256','identity_sha256','canonical_ensure_ascii'}, 'descriptor_schema')
    need(type(d['bytes']) is int and 0<d['bytes']<=BODY_CAP and d['canonical_ensure_ascii'] is True, 'descriptor_bound_policy')
    need(all(type(d[k]) is str and re.fullmatch('[0-9a-f]{64}',d[k]) for k in ('sha256','identity_sha256')), 'descriptor_digest')
    need(type(d['path']) is str, 'descriptor_path')
    p=Path(d['path'])
    need(p.parent==BASE and str(p)==d['path'] and re.fullmatch(re.escape(prefix)+r'[A-Za-z0-9][A-Za-z0-9._-]{0,160}\.json',p.name), 'descriptor_route')
    return p

def original(raw, pin, form):
    need(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'], 'original_byte_pin')
    d=parse(raw)
    need(d.get('format')==form and d.get('canonical_ensure_ascii') is True
         and d.get('identity_sha256')==pin['identity_sha256'], 'original_policy_or_identity')
    body=dict(d); body.pop('identity_sha256')
    need(sha(canonical(body))==pin['identity_sha256'], 'original_seal')
    return d

def age(d):
    value=datetime.datetime.fromisoformat(d['checked_at'])
    need(value.tzinfo is not None, 'plan_aware_time')
    elapsed=(datetime.datetime.now(datetime.timezone.utc)-value).total_seconds()
    need(0<=elapsed<=300, 'plan_age')

def binding(plan, review, rp):
    need(REQUIRED_PLAN<=set(plan), 'guard_plan_required_fields')
    for key in ('additional_protected_paths','historical_reference_files','original_raw_file_pins',
                'pending_control_files','protected_file_pins','raw_control_sibling_paths',
                'receipt_source_file_proofs','relevant_privileged_consumers','reserved_absent_paths',
                'retained_raw_library_aliases'):
        need(type(plan[key]) is list, 'guard_plan_list_schema')
    for key in (*BACKLINKS,'allocation_observation_pin','parent_review_pin','native_git_pin',
                'account_service_identification_pin','portal_service_review_pin',
                'common_configuration_pin','future_source_pins','retirement_operation'):
        need(type(plan[key]) is dict, 'guard_plan_object_schema')
    need(sha(canonical(plan['retirement_operation']))==
         '1bd4b85ef2d7578ff62fba567fd709cbc9ea05ec628f910a1d12462890a67e9e', 'selected_operation_schema')
    rows=plan['selected_rows']
    need(type(rows) is list and rows and all(type(x) is str and x in ROWS for x in rows)
         and len(set(rows))==len(rows), 'explicit_allowed_unique_rows')
    need(plan['guard_source_sha256']==GUARD_SHA and plan['expected_primary']==PRIMARY, 'selected_guard_primary')
    need(type(plan['selection_reason']) is str and plan['selection_reason'], 'selection_reason_missing')
    alloc=plan['allocation_decision']
    need(type(alloc) is dict and alloc['final_R17_revision']==PRIMARY and alloc['selected_rows']==rows
         and alloc['minimal_selected_subset'] is True
         and alloc['observation_file_sha256']==plan['allocation_observation_pin']['sha256'], 'allocation_binding')
    need(plan['native_git_pin']['path']=='/usr/bin/git'
         and plan['shared_config_and_main_index_must_remain_exact'] is True, 'fixed_native_shared_scope')
    expect={**rp,'format':'swdb.library-preserving-sparse-retirement-parent-review.v1'}
    need(all(plan['parent_review_pin'].get(k)==v for k,v in expect.items()), 'original_review_file_pin')
    config={k:v for k,v in plan.items() if k not in ('identity_sha256','parent_review_pin')}
    links=[]
    for key in BACKLINKS:
        coverage=dict(config[key]); links.append(coverage.pop('parent_review_identity_sha256')); config[key]=coverage
    need(type(config['relevant_privileged_consumers']) is list, 'consumer_list_schema')
    consumers=[]
    for item in config['relevant_privileged_consumers']:
        copied=dict(item); links.append(copied.pop('parent_review_identity_sha256')); consumers.append(copied)
    config['relevant_privileged_consumers']=consumers
    need(review['accepted_for_exact_subset'] is True and review['accepted_library_preserving_sparse_scope'] is True
         and review['final14_completed_and_released'] is True
         and review['reviewed_configuration_sha256']==sha(canonical(config))
         and all(x==review['identity_sha256'] for x in links), 'original_configuration_review_binding')
    age(plan)

def absent(fd, name):
    try:
        os.stat(name,dir_fd=fd,follow_symlinks=False)
    except FileNotFoundError:
        return
    raise Refused('publication_path_exists')

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source-sha256',required=True)
    args=a.parse_args(); need(re.fullmatch('[0-9a-f]{64}',args.source_sha256), 'source_pin')
    need(sys.platform=='linux' and os.uname().machine=='x86_64'
         and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID
         and pwd.getpwuid(UID).pw_name=='yanruj' and sys.version_info[:3]==(3,12,3)
         and sys.flags.dont_write_bytecode==1 and sys.flags.no_user_site==1 and sys.flags.optimize==0
         and Path(sys.executable)==PYTHON, 'native_host_flags')
    for s in (signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT):
        signal.signal(s,stop)
    signal.setitimer(signal.ITIMER_REAL,90)
    native,ns=file_bytes(PYTHON,PYTHON_BYTES,0)
    need(len(native)==PYTHON_BYTES and sha(native)==PYTHON_SHA,'native_python_byte_pin')
    source=Path(__file__).absolute()
    need(source.parent==BASE, 'publisher_source_direct_base')
    own,ss=file_bytes(source,256*1024,UID)
    need(sha(own)==args.source_sha256,'publisher_source_byte_pin')
    fd=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    created=[]
    try:
        fixed=base_identity(fd)
        line=[]
        for unused in range(HEADER_CAP+1):
            b=exact_stdin(1)
            if b==b'\n': break
            line.append(b)
        else: raise Refused('header_cap')
        header=parse(b''.join(line))
        need(set(header)=={'format','plan','review'} and header['format']=='swdb.parent-sparse-original-publication-input.v1','framing_header')
        pp=descriptor(header['plan'],'lanl-sparse-retirement-parent-plan-')
        rp=descriptor(header['review'],'lanl-sparse-retirement-parent-review-')
        need(pp!=rp,'distinct_publication_paths')
        pr=exact_stdin(header['plan']['bytes']); rr=exact_stdin(header['review']['bytes'])
        need(not os.read(0,1),'stdin_trailing_bytes')
        plan=original(pr,header['plan'],'swdb.library-preserving-sparse-retirement-parent-plan.v1')
        review=original(rr,header['review'],'swdb.library-preserving-sparse-retirement-parent-review.v1')
        binding(plan,review,header['review'])
        need(base_identity(fd)==fixed,'base_replaced'); absent(fd,pp.name); absent(fd,rp.name)
        for path,raw,pin in ((rp,rr,header['review']),(pp,pr,header['plan'])):
            age(plan); need(base_identity(fd)==fixed,'base_replaced'); absent(fd,path.name)
            created.append({'path':str(path),'expected_bytes':pin['bytes'],'expected_sha256':pin['sha256'],'write_completed':False})
            out=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=fd)
            try:
                offset=0
                while offset<len(raw):
                    left(); count=os.write(out,raw[offset:offset+65536]); need(count>0,'publication_write'); offset+=count
                os.fsync(out)
                s=os.fstat(out)
                need(stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600,'publication_identity')
            finally: os.close(out)
            os.fsync(fd); need(base_identity(fd)==fixed,'base_replaced')
            got,gs=file_bytes(path,BODY_CAP,UID,0o600)
            need(got==raw,'publication_original_changed')
            created[-1]={**pin,'stat':gs,'write_completed':True}
        binding(plan,review,header['review'])
        final,fs=file_bytes(source,256*1024,UID)
        need(final==own and fs==ss and stamp(PYTHON.lstat())==ns and base_identity(fd)==fixed,'final_source_native_base_changed')
        print(json.dumps({'format':'swdb.parent-sparse-original-publication-return.v1','sealed':False,
              'originals':created,'publisher_source_sha256':args.source_sha256,'native_python_sha256':PYTHON_SHA,
              'expected_primary_from_parent_documents':PRIMARY,'git_or_selected_control_invoked':False,
              'publisher_generates_seals_acceptance_or_capacity_admission':False},sort_keys=True,separators=(',',':')))
        return 0
    except BaseException as e:
        print(json.dumps({'format':'swdb.parent-sparse-original-publication-return.v1','sealed':False,
              'failed':True,'error_type':type(e).__name__,'reason_code':reason_code(e),'publication_attempts_not_cleaned':created,
              'partial_publication_possible':True,'git_or_selected_control_invoked':False},sort_keys=True,separators=(',',':')))
        return 1
    finally: os.close(fd)

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Refused as e:
        print(json.dumps({'format':'swdb.parent-sparse-original-publication-return.v1','sealed':False,
              'failed':True,'publication_state_unknown':True,'reason_code':reason_code(e)},sort_keys=True,separators=(',',':')))
        raise SystemExit(1)
