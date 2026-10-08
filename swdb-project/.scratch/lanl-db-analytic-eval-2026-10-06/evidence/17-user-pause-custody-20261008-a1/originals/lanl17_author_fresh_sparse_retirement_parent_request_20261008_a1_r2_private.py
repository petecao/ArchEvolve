"""2026-10-08 ET. SOURCE ONLY / NOT RUN.

Author one UNSEALED builder request from the exact accepted default request.
No operational imports, seals, remote reads, Git, source actions or admission.
Genuine accepted default and fresh capacity originals are required inputs.
"""
import argparse
import copy
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

TMP = Path('/private/tmp')
BASE = '/data1/yanruj'
PRIMARY = '5e12a9796432654d88def24ecea617d16ca605b2'
UID = 114316761
GUARD_SHA = 'd75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
WRAPPER_SHA = 'e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec'
PUBLISHER_SHA = '5e667fa8ca26ece4825631e5d51feca490f3e154688a38399518bf9c237df2d9'
SERVICE_SHA = 'fcf92eee1c4b8bdfaed979dc8bedab004c6c4b7e2b1410c7614bc92d60349f4a'
CONTROL = BASE+'/lanl17-detached-sparse-default-a3'
DECODED = TMP/'lanl17-detached-sparse-default-a3-originals-20261008'
SOURCE_DIRECTORY = BASE+'/lanl17-sparse-retirement-source-20261008-a2'
DEFAULT_PLAN_ID = '4d3e5845e0a844d5181d0c6025f49c955ccbdcdc64b03491b78b01519765cd58'
DEFAULT_REVIEW_ID = 'b51b17027c5f971df06b29eb04cf37f5521ac7296949cd4f0cea30495ea063a1'
FIXED = {
    'request': ('lanl17-actual-sparse-default-parent-request-20261008-a3.json', 535589,
                '6d8cf50990054c0568d6b2fbb981bb4f47091207fc72fddb1678cf9919b3da09'),
    'plan': ('lanl17-actual-sparse-default-parent-plan-20261008-a3.json', 740733,
             'e2fb42a2bde17b3d9aab4c0d2121903a22dd3d7f29d7caab85acf22638677c02'),
    'review': ('lanl17-actual-sparse-default-parent-review-20261008-a3.json', 3997,
               'c3720a14075597ff55ca5a16644b74bc81c778ae8bd542c46279f9d039b2bd62'),
}
FILES = {'status.json':16384, 'configuration.json':16384, 'tmux.conf':16384,
         'launch-status.json':16384, 'launch.stdout':16384, 'launch.stderr':16384,
         'guard.stdout':262144, 'guard.stderr':262144, 'guard-receipt/receipt.json':262144}
LIMITS = {'seconds':3600, 'git_seconds':120, 'git_output':33554432,
          'plan_bytes':2097152, 'inventory_bytes':33554432, 'one_file':536870912,
          'total_file_bytes':17179869184, 'walk_entries':400000, 'tracked_entries':20000,
          'stat_checks':2000000, 'processes':10000, 'process_fds':200000,
          'one_proc_bytes':16777216, 'receipt_bytes':262144}
NATIVE = {
    '/usr/bin/tmux': (1102608,'034b15c64035f783d43862f2775eb4828f61571ca62c8199796000b97d556ecd'),
    '/usr/bin/python3.12': (8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
    '/usr/bin/timeout': (39880,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52'),
    '/usr/bin/git': (4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
    '/usr/bin/bash': (1446024,'bc5945feb8bd26203ebfafea5ce1878bb2e32cb8fb50ab7ae395cfb1e1aaaef1'),
}
MUTABLE = {'checked_at','selection_reason','allocation_decision','fresh_capacity_and_cost',
           'parent_review_facts','protected_file_pins','additional_protected_paths'}
FIELDS = ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')


class Refused(Exception):
    pass


def need(value, reason):
    if not value:
        raise Refused(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),
                      ensure_ascii=True,allow_nan=False).encode()


def strict(raw):
    def pairs(items):
        d = {}
        for key,value in items:
            need(key not in d,'duplicate_JSON_key'); d[key] = value
        return d
    def nonfinite(value):
        raise Refused('nonfinite_JSON')
    value = json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)
    need(type(value) is dict,'JSON_object_required')
    return value


def timestamp(value):
    need(type(value) is str,'timestamp_required')
    result = datetime.datetime.fromisoformat(value)
    need(result.tzinfo is not None,'aware_timestamp_required')
    return result


def digest(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'SHA256_required')
    return value


def stamp(s):
    return {key:getattr(s,'st_'+key) for key in FIELDS}


class LocalInputs:
    def __init__(self):
        self.started = time.monotonic(); self.total = 0; self.witnesses = {}; self.directories = {}

    def left(self):
        need(time.monotonic()-self.started<=90,'author_deadline')

    def directory(self,p):
        p = Path(p)
        need(p.is_absolute() and p.resolve(strict=True)==p and TMP in (p,*p.parents)
             and not any(q.is_symlink() for q in (p,*p.parents)),'private_tmp_route_required')
        s = p.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid()
             and stat.S_IMODE(s.st_mode)==0o700,'private_directory_required')
        identity = (s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode)
        if str(p) in self.directories:
            need(self.directories[str(p)]==identity,'input_directory_replaced')
        self.directories[str(p)] = identity
        return p,identity

    def read(self,p,cap,expected=None):
        self.left(); p = Path(p)
        need(p.is_absolute() and str(p)==os.fspath(p) and TMP in p.parents
             and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),
             'canonical_local_original_required')
        before = p.lstat()
        need(stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid()
             and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600
             and before.st_size<=cap,'private_original_file_required')
        fd = os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        with os.fdopen(fd,'rb') as f:
            need(stamp(os.fstat(f.fileno()))==stamp(before),'original_open_changed')
            raw = f.read(cap+1); self.total += len(raw)
            need(self.total<=16*1024*1024 and len(raw)==before.st_size<=cap
                 and stamp(before)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),
                 'bounded_stable_original_read')
        pin = {'path':str(p),'bytes':len(raw),'sha256':sha(raw),'stat':stamp(before)}
        if expected is not None:
            need(pin['sha256']==digest(expected),'explicit_original_byte_pin_changed')
        if str(p) in self.witnesses:
            need(self.witnesses[str(p)]==pin,'original_replaced_between_reads')
        self.witnesses[str(p)] = pin
        return raw,pin

    def close(self):
        for path,pin in list(self.witnesses.items()):
            unused,current = self.read(path,pin['bytes'],pin['sha256'])
            need(current==pin,'final_original_changed')
        for path,identity in list(self.directories.items()):
            need(self.directory(path)[1]==identity,'final_input_directory_changed')


def original_seal(document, form):
    need(document['format']==form and document['canonical_ensure_ascii'] is True
         and document['identity_sha256']==sha(canonical({k:v for k,v in document.items()
                                                       if k!='identity_sha256'})),
         'original_True_seal_changed')


def remote_pin(pin,cap):
    need(type(pin) is dict and type(pin['path']) is str and type(pin['bytes']) is int
         and 0<=pin['bytes']<=cap,'original_remote_pin_schema')
    digest(pin['sha256']); st = pin['stat']
    need(set(st)==set(FIELDS) and all(type(x) is int for x in st.values())
         and st['uid']==UID and st['nlink']==1 and stat.S_ISREG(st['mode'])
         and stat.S_IMODE(st['mode'])==0o600 and st['size']==pin['bytes'],
         'original_remote_private_stamp')


def defaults(inputs,args,request,old_plan,old_review):
    folder,folder_id = inputs.directory(args.default_originals_directory)
    need(folder==DECODED,'exact_decoded_default_route')
    inputs.directory(folder/'guard-receipt')
    raw,custody_pin = inputs.read(folder/'local-custody.json',65536,args.custody_sha256)
    custody = strict(raw)
    need(custody['format']=='swdb.lanl17-detached-library-sparse-original-local-byte-custody.v1'
         and custody['sealed'] is False and custody['missing_original_names']==[]
         and custody['guard_receipt_availability']=='present'
         and custody['original_stream_and_seal_policies_unchanged'] is True
         and custody['semantic_or_success_or_capacity_admission'] is False,'complete_default_custody_required')
    entries = {}; local = {}
    need(type(custody['originals']) is list and len(custody['originals'])==len(FILES),
         'all_nine_decoded_originals_required')
    for entry in custody['originals']:
        p = Path(entry['local_path']); relative = str(p.relative_to(folder))
        need(relative in FILES and relative not in entries,'closed_decoded_original_set')
        body,pin = inputs.read(p,FILES[relative],entry['sha256'])
        need(pin['bytes']==entry['bytes'] and pin['stat']==entry['local_original_stat'],
             'decoded_original_byte_and_stat_changed')
        remote = {'path':entry['remote_original_path'],'bytes':entry['bytes'],
                  'sha256':entry['sha256'],'stat':entry['remote_original_stat']}
        remote_pin(remote,FILES[relative]); entries[relative] = remote; local[relative] = body
        if relative!='guard-receipt/receipt.json':
            need(remote['path']==CONTROL+'/'+relative,'exact_default_original_route')
    need(set(entries)==set(FILES),'complete_default_original_names')
    for relative,wanted in (('status.json',args.status_sha256),('guard.stdout',args.stdout_sha256),
                            ('guard-receipt/receipt.json',args.receipt_sha256)):
        need(entries[relative]['sha256']==digest(wanted),'explicit_default_original_hash_changed')
    status = strict(local['status.json']); config = strict(local['configuration.json'])
    returned = strict(local['guard.stdout']); receipt = strict(local['guard-receipt/receipt.json'])
    rows = request['selected_rows']
    need(status['format']=='swdb.lanl17-detached-library-sparse-administration-status.v1'
         and status['sealed'] is False and status['state']=='guard_completed'
         and type(status['guard_exit_code']) is int and status['guard_exit_code']==0
         and 'error_class' not in status and status['retire_requested'] is False
         and status['scientific_admission'] is False and status['capacity_admission'] is False
         and status['expected_primary']==PRIMARY and status['selected_rows']==rows,
         'successful_original_default_status_required')
    need(status['configuration']==entries['configuration.json']
         and status['guard_stdout']==entries['guard.stdout']
         and status['guard_stderr']==entries['guard.stderr'],'default_wrapper_original_pins_changed')
    need(config['format']=='swdb.lanl17-detached-library-sparse-administration-configuration.v1'
         and config['sealed'] is False and config['control_directory']==CONTROL
         and config['prior_reviewed_inspection'] is None
         and config['guard_timeout_seconds']==3660 and config['guard_KILL_after_seconds']==60
         and config['worker_wait_seconds']==3735 and config['transport_wait_seconds']==60
         and config['scientific_action'] is False,'default_configuration_scope_changed')
    for key in ('inputs','selected_rows','expected_primary','guard_attempt','retire_requested','reviewed_plan'):
        need(config[key]==status[key],'configuration_status_binding_changed')
    for key,size,dig in (('wrapper',24114,WRAPPER_SHA),('guard',180887,GUARD_SHA),
                         ('service_review',3258,SERVICE_SHA)):
        need(status['inputs'][key]['bytes']==size and status['inputs'][key]['sha256']==dig,
             'selected_default_source_changed')
    for role,basename in (('guard','lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py'),
                          ('wrapper','lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py')):
        pin = status['inputs'][role]; remote_pin(pin,262144)
        need(pin['path']==SOURCE_DIRECTORY+'/'+basename
             and any(all(v[k]==pin[k] for k in ('path','bytes','sha256','stat'))
                     for v in old_plan['protected_file_pins'] if 'stat' in v),
             'selected_source_original_plan_full_pin_changed')
    need(set(status['inputs']['native'])==set(NATIVE),'native_pin_set_changed')
    for path,(size,dig) in NATIVE.items():
        pin = status['inputs']['native'][path]
        need(pin['path']==path and pin['bytes']==size and pin['sha256']==dig,
             'native_pin_changed')
    attempt = status['guard_attempt']
    need(attempt=='a3','exact_corrected_default_attempt_required')
    output = BASE+'/lanl-library-preserving-sparse-retirement-20261008-'+attempt
    need(config['guard_output_directory']==output
         and entries['guard-receipt/receipt.json']['path']==output+'/receipt.json',
         'source_derived_default_receipt_route_changed')
    argv = ['/usr/bin/timeout','--signal=TERM','--kill-after=60s','3660s',
            '/usr/bin/python3.12','-B',status['inputs']['guard']['path'],
            '--expected-primary',PRIMARY,'--plan',status['reviewed_plan']['file']['path'],
            '--plan-sha256',status['reviewed_plan']['file']['sha256'],'--attempt',attempt]
    for name in rows:
        argv.extend(['--select',name])
    need(status['guard_argv']==argv and type(status['guard_pid']) is int and status['guard_pid']>0
         and status['transport_original_termination']['basis'] in
             ('original_PID_absent','PID_reused_original_start_absent'),
         'exact_default_argv_transport_and_actual_PID_required')
    need(returned['format']=='swdb.library-preserving-sparse-retirement-return.v1'
         and returned['path']==entries['guard-receipt/receipt.json']['path']
         and returned['bytes']==entries['guard-receipt/receipt.json']['bytes']
         and returned['sha256']==entries['guard-receipt/receipt.json']['sha256']
         and returned['admitted'] is True and returned['retired_count']==0
         and returned['failure'] is None,'successful_default_return_required')
    original_seal(receipt,'swdb.library-preserving-sparse-retirement-guard.v1')
    need(receipt['identity_sha256']==returned['identity_sha256']
         and receipt['admitted'] is True and receipt['failure'] is None
         and receipt['retire_requested'] is False and receipt['retired_rows']==[]
         and receipt['completed_retirements']==[] and receipt['pre_retire_full_byte_checks']=={}
         and receipt['selected_rows']==rows and receipt['expected_primary']==PRIMARY
         and receipt['guard_source_sha256']==GUARD_SHA and receipt['full_raw_byte_passes']==2
         and receipt['scientific_admission'] is False and receipt['capacity_admission'] is False,
         'successful_default_receipt_scope_required')
    need(receipt['inspection_limits']==LIMITS,'unchanged_default_limits_required')
    for key,limit in (('bytes_read','total_file_bytes'),('walk_entries_checked','walk_entries'),
                      ('stable_stat_checks','stat_checks')):
        need(type(receipt[key]) is int and 0<=receipt[key]<=LIMITS[limit],'default_counter_limit')
    initial = receipt['initial_checks']
    need(set(initial['trees'])==set(rows),'all_sixteen_default_tree_checks_required')
    need(initial['processes']=={'performed':False,'initial_reference_clearance_claimed':False,
                                'qualification_deferred_to':'assessment_completion'},
         'default_process_scope_labels_changed')
    for name,tree in initial['trees'].items():
        need(tree['regular_bytes_verified'] is False
             and tree['tracked_mode_blob_source_inventory_sha256'] is None
             and tree['detached_clean_ignored0_untracked0'] is True
             and type(tree['tracked_entries']) is int and 0<tree['tracked_entries']<=LIMITS['tracked_entries'],
             'metadata_first_default_tracked_source_required')
        digest(tree['tracked_stat_inventory_sha256'])
    need(initial['sources']['expected_primary']==PRIMARY
         and initial['sources']['C']=='f893fed400347ed23d92e917d8bde21b75e5375d'
         and initial['sources']['F6']=='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
         and initial['sources']['Python_blob_entries_exact_C']==185
         and initial['raw_tree_count']==len(request['reviewed_full_RAW_roots'])
         and initial['aliases']['historical_files']==len(request['historical_file_reviews'])
         and initial['aliases']['future_control_sources_byte_pinned']==13,'default_source_RAW_alias_counts_changed')
    need(set(initial['leases'])=={'mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'}
         and all(v['state']=='released' for v in initial['leases'].values()),
         'default_released_lease_facts_required')
    old_file = status['reviewed_plan']['file']
    need(old_file['path']==BASE+'/lanl-sparse-retirement-parent-plan-20261008-a3.json'
         and old_file['bytes']==FIXED['plan'][1] and old_file['sha256']==FIXED['plan'][2]
         and status['reviewed_plan']['identity_sha256']==old_plan['identity_sha256']
         and receipt['reviewed_plan_file_sha256']==old_file['sha256']
         and receipt['reviewed_plan_identity_sha256']==old_plan['identity_sha256']
         and receipt['parent_review_identity_sha256']==old_review['identity_sha256'],
         'original_default_plan_review_binding_changed')
    # Prior full-byte custody is authenticated original evidence, not a current read.
    started = timestamp(receipt['started_at']); finished = timestamp(receipt['finished_at'])
    checked = timestamp(old_plan['checked_at']); current = datetime.datetime.now(datetime.timezone.utc)
    need(0<=(started-checked).total_seconds()<=300 and started<=finished<=current,
         'original_default_chronology_changed')
    projection = sorted(old_plan['historical_reference_files'],key=lambda pin:pin['path'])
    need(len(projection)==345 and len({pin['path'] for pin in projection})==345
         and {pin['path'] for pin in projection}==set(request['historical_file_reviews']),
         'complete_original_historical_projection_required')
    history = receipt['historical_byte_custody']
    need(history['format']=='swdb.original-historical-byte-custody.v1'
         and history['all_history_bytes_freshly_read_in_this_operation'] is True
         and type(history['inherited_history_files']) is int and history['inherited_history_files']==0
         and history['historical_projection_sha256']==sha(canonical(projection)),
         'fresh_default_historical_byte_policy_required')
    vectors = history['files']
    need(type(vectors) is list and len(vectors)==345
         and [v['path'] for v in vectors]==[p['path'] for p in projection],
         'complete_ordered_default_historical_vectors_required')
    for pin,witness in zip(projection,vectors):
        need(type(witness) is dict and set(witness)=={'path','bytes','sha256','stat','reference_hits'}
             and all(witness[k]==pin[k] for k in ('path','bytes','sha256','stat'))
             and type(witness['reference_hits']) is bool
             and type(witness['bytes']) is int and 0<=witness['bytes']<=LIMITS['one_file'],
             'original_default_historical_vector_changed')
        digest(witness['sha256']); observed = witness['stat']
        need(set(observed)==set(FIELDS) and all(type(v) is int for v in observed.values())
             and observed['uid']==UID and observed['nlink']==1 and stat.S_ISREG(observed['mode'])
             and observed['size']==witness['bytes'], 'original_historical_full_stat_required')
        reviewed = request['historical_file_reviews'][pin['path']]
        need(all(reviewed[k]==pin[k] for k in ('bytes','sha256','handling','review_basis'))
             and pin['handling']=='historical_only_not_dereferenced'
             and type(pin['review_basis']) is str and pin['review_basis'],
             'original_historical_classification_changed')
    full_roots = request['reviewed_full_RAW_roots']
    eligible = {p['path'] for p in projection
                if p['path'].startswith('/data/yanruj/EvolveSWDB_runs/')
                and not any(p['path']==r or p['path'].startswith(r+'/') for r in full_roots)}
    need(len(full_roots)==30 and len(set(full_roots))==30 and len(eligible)==153,
         'exact_original_inherited_history_scope_changed')
    observations = custody['wrapper_custody_observation']
    need(observations['selected_source_pins_bound'] is True
         and observations['configuration_pin_matches_status'] is True
         and observations['wrapper_stdout_pin_matches_original'] is True,'default_decoder_custody_observation')
    observations = custody['guard_receipt_custody_observation']
    need(observations['receipt_seal_verification']=='verified_original_True_policy'
         and observations['stdout_receipt_byte_identity_binding']=='verified_exact_original_bytes_and_identity',
         'default_decoder_receipt_observation')
    need(inputs.directory(folder)[1]==folder_id,'decoded_directory_changed')
    return {'status':entries['status.json'],'stdout':entries['guard.stdout'],
            'original_guard_receipt':{**entries['guard-receipt/receipt.json'],
                                     'identity_sha256':receipt['identity_sha256'],'canonical_ensure_ascii':True},
            'default_reviewed_plan':status['reviewed_plan'],
            'default_review':old_plan['parent_review_pin'],
            'decoded_local_custody_original':custody_pin,'all_originals':list(entries.values()),
            'same_ordered_rows_source_primary_required':True,
            'retirement_requires_separately_fresh_parent_plan_in_unchanged_guard':True,
            'parent_review_is_inherited_explicit_invocation_authority':True},output


def parent_acceptance(document,request,default):
    need(document['format']=='swdb.sparse-default-original-parent-acceptance-input.v1'
         and document['sealed'] is False and 'identity_sha256' not in document
         and document['accepted_original_default'] is True
         and document['accepted_for_exact_subset'] is True
         and document['accepted_library_preserving_sparse_scope'] is True
         and document['final14_completed_and_released'] is True
         and document['expected_primary']==PRIMARY and document['selected_rows']==request['selected_rows']
         and document['guard_source_sha256']==GUARD_SHA and document['wrapper_source_sha256']==WRAPPER_SHA
         and type(document['review_basis']) is str and document['review_basis'],
         'explicit_parent_default_acceptance_required')
    for field,pin in (('status_sha256',default['status']),('stdout_sha256',default['stdout']),
                      ('receipt_sha256',default['original_guard_receipt'])):
        need(document[field]==pin['sha256'],'parent_default_original_byte_binding')
    need(document['receipt_identity_sha256']==default['original_guard_receipt']['identity_sha256']
         and document['default_plan_sha256']==default['default_reviewed_plan']['file']['sha256']
         and document['default_plan_identity_sha256']==default['default_reviewed_plan']['identity_sha256']
         and document['default_review_sha256']==default['default_review']['sha256']
         and document['default_review_identity_sha256']==default['default_review']['identity_sha256'],
         'parent_default_plan_review_receipt_binding')


def capacity(inputs,path,dig,request):
    raw,pin = inputs.read(path,131072,dig); fresh = strict(raw)
    need(fresh['format']=='swdb.sparse-parent-fresh-capacity-original.v1' and fresh['sealed'] is False
         and 'identity_sha256' not in fresh and fresh['script_mains_or_retirement_or_capacity_admission_performed'] is False,
         'fresh_capacity_original_scope_required')
    age = (datetime.datetime.now(datetime.timezone.utc)-timestamp(fresh['checked_at'])).total_seconds()
    need(0<=age<=120,'fresh_capacity_observation_stale')
    need(set(fresh['released_leases'])=={'mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'}
         and all(v=='released' for v in fresh['released_leases'].values())
         and fresh['reserved_paths_still_absent']==request['reserved_absent_paths'],
         'fresh_lease_or_reserved_route_changed')
    copy_rows = fresh['private_control_copies']
    need(type(copy_rows) is list and len(copy_rows)==4, 'four_original_and_selected_source_copies_required')
    copies = {v['path']:v for v in copy_rows}
    expected_copies = {
        BASE+'/lanl17-sparse-retirement-source-20261008-a1/lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py':
            (166145,'4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26'),
        BASE+'/lanl17-sparse-retirement-source-20261008-a1/lanl17_detach_library_preserving_sparse_administration_20261008_a1_r1.py':
            (24115,'1127d1fba8e004153cf086cace7d19ccd901e85902f9ad91924407922c85c6ca'),
        SOURCE_DIRECTORY+'/lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py':(180887,GUARD_SHA),
        SOURCE_DIRECTORY+'/lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py':(24114,WRAPPER_SHA)}
    need(set(copies)==set(expected_copies),'exact_four_distinct_source_copy_routes_required')
    for path,(size,expected) in expected_copies.items():
        pin = copies[path]; remote_pin(pin,262144)
        need(pin['bytes']==size and pin['sha256']==expected,'fresh_four_source_copy_pin_changed')
    for p in request['protected_file_pins']:
        if p['sha256'] in (GUARD_SHA,WRAPPER_SHA):
            need(p['path'] in copies and all(copies[p['path']][k]==p[k] for k in ('bytes','sha256','stat')),
                 'fresh_selected_control_identity_changed')
    need(set(fresh['actual_free_bytes'])=={'/data1','/data'}
         and all(type(v) is int and v>=0 for v in fresh['actual_free_bytes'].values()),
         'fresh_mount_capacity_required')
    alloc = request['allocation_decision']; planned = alloc['per_row_planning']
    rows = request['selected_rows']
    need(len(rows)==16 and rows==sorted(rows) and alloc['eligible_pool']==rows
         and len(planned)==16 and {v['name'] for v in planned}==set(rows),
         'immutable_sixteen_pool_changed')
    t = request['fresh_capacity_and_cost']['reviewed_one_checkout_T_planning_allowance_bytes']
    allowance = request['fresh_capacity_and_cost']['whole_operation_allowance_bytes']
    need(t==1230893056 and allowance==67108864,'planning_allowances_changed')
    q = 21*2**30+2*t+512*2**20; free = fresh['actual_free_bytes']['/data1']
    deficit = max(0,q-free); threshold = deficit+allowance
    choices = []
    for count in range(1,17):
        for subset in itertools.combinations(planned,count):
            inputs.left()
            total = sum(v['discounted_estimate_after_extra_original_admin_allowance_bytes'] for v in subset)
            if total>=threshold:
                choices.append((count,total,tuple(sorted(v['name'] for v in subset))))
        if choices:
            break
    need(choices,'no_conditional_fit_parent_decision_required')
    count,total,names = min(choices)
    if count!=16 or list(names)!=rows:
        raise Refused('minimum_subset_changed_parent_decision_required',
                      {'minimum_cardinality':count,'conditional_minimum_rows':list(names),
                       'required_floor_Q_bytes':q,'deficit_D_bytes':deficit,
                       'administrative_planning_allowance_bytes':allowance,
                       'conditional_estimate_bytes':total,
                       'capacity_or_subset_admission':False})
    return fresh,pin,{'required_floor_Q_bytes':q,'fresh_free_bytes':free,'deficit_D_bytes':deficit,
                     'minimum_cardinality':count,'selected_discounted_estimate_bytes':total,
                     'conditional_margin_after_administrative_allowance_bytes':total-threshold}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('fresh-capacity-original','fresh-capacity-sha256','default-originals-directory',
                'status-sha256','stdout-sha256','receipt-sha256','custody-sha256',
                'parent-acceptance','parent-acceptance-sha256','source-sha256','output'):
        parser.add_argument('--'+key,required=True)
    args = parser.parse_args()
    need(sys.flags.dont_write_bytecode==1 and sys.flags.optimize==0,'native_B_no_optimize_required')
    inputs = LocalInputs()
    def interrupted(signum,frame):
        raise Refused('author_signal_'+str(signum))
    old_handlers = {s:signal.signal(s,interrupted) for s in
                    (signal.SIGALRM,signal.SIGTERM,signal.SIGHUP,signal.SIGINT)}
    signal.setitimer(signal.ITIMER_REAL,90)
    try:
        own = Path(__file__).absolute(); inputs.read(own,65536,args.source_sha256)
        documents = {}
        for key,(name,size,dig) in FIXED.items():
            raw,pin = inputs.read(TMP/name,2097152,dig)
            need(pin['bytes']==size,'fixed_original_size_changed'); documents[key] = strict(raw)
        request = documents['request']; old_plan = documents['plan']; old_review = documents['review']
        need(request['format']=='swdb.sparse-parent-plan-materials-request.v1' and request['sealed'] is False
             and 'identity_sha256' not in request and request['expected_primary']==PRIMARY,
             'immutable_default_request_required')
        original_seal(old_plan,'swdb.library-preserving-sparse-retirement-parent-plan.v1')
        original_seal(old_review,'swdb.library-preserving-sparse-retirement-parent-review.v1')
        need(old_plan['identity_sha256']==DEFAULT_PLAN_ID and old_review['identity_sha256']==DEFAULT_REVIEW_ID
             and old_review['actual_default_only'] is True and old_plan['selected_rows']==request['selected_rows']
             and old_plan['parent_review_pin']['sha256']==FIXED['review'][2]
             and old_plan['parent_review_pin']['identity_sha256']==old_review['identity_sha256'],
             'original_default_only_review_changed')
        need(old_plan['guard_source_sha256']==GUARD_SHA and old_plan['expected_primary']==PRIMARY
             and old_plan['parent_review_pin']['path']==BASE+'/lanl-sparse-retirement-parent-review-20261008-a3.json'
             and old_plan['parent_review_pin']['bytes']==FIXED['review'][1]
             and old_review['accepted_for_exact_subset'] is True
             and old_review['accepted_library_preserving_sparse_scope'] is True
             and old_review['final14_completed_and_released'] is True,
             'original_default_plan_source_and_review_scope_changed')
        configuration = {k:copy.deepcopy(v) for k,v in old_plan.items()
                         if k not in ('identity_sha256','parent_review_pin')}
        backlinks = []
        for key in ('control_siblings_complete_review','pending_alias_coverage_review',
                    'receipt_source_proofs_complete_review','original_raw_files_complete_review'):
            backlinks.append(configuration[key].pop('parent_review_identity_sha256'))
        for consumer in configuration['relevant_privileged_consumers']:
            backlinks.append(consumer.pop('parent_review_identity_sha256'))
        need(all(link==old_review['identity_sha256'] for link in backlinks)
             and sha(canonical(configuration))==old_review['reviewed_configuration_sha256'],
             'whole_original_default_configuration_review_changed')
        default,guard_output = defaults(inputs,args,request,old_plan,old_review)
        body,parent_pin = inputs.read(args.parent_acceptance,65536,args.parent_acceptance_sha256)
        parent = strict(body); parent_acceptance(parent,request,default)
        fresh,fresh_pin,values = capacity(inputs,args.fresh_capacity_original,args.fresh_capacity_sha256,request)
        out = copy.deepcopy(request)
        out['checked_at'] = fresh['checked_at']; out['allocation_decision'].update(values)
        out['selection_reason'] += (
            ' The preceding DEFAULT-only authorization clause describes the preserved a3 request at creation. '
            'This distinct fresh RETIRE request binds only the genuinely parent-accepted a3 DEFAULT originals; '
            'eligible prior historical byte proofs require G5 current full-stat continuity, with two fresh RAW '
            'passes and fresh per-row full regular-byte/Git-source/library checks unchanged. '
            'The unsealed request itself establishes no actual retirement, recovery or scientific admission.')
        out['fresh_capacity_and_cost'].update({
            'checked_at':fresh['checked_at'],'actual_free_data1_bytes':fresh['actual_free_bytes']['/data1'],
            'actual_free_data_bytes':fresh['actual_free_bytes']['/data'],
            'fresh_capacity_original_pin':fresh_pin,'Q_bytes':values['required_floor_Q_bytes'],
            'remaining_cost_terms':
                'The genuinely parent-accepted a3 DEFAULT supplies historical original counters and all345 '
                'full byte witnesses, bound in parent_review_facts.successful_default_original_bindings. '
                'Only153 eligible history hashes may use prior-byte evidence plus G5 current complete-stat '
                'continuity; the author observes no fresh remote history stats. The corrected source core '
                'estimates DEFAULT14381124025B and conditional RETIRE14702545997B remain incomplete source '
                'estimates, not total upper bounds or fit guarantees. Two fresh full RAW passes, every fresh '
                'per-row tracked/Git/source/library byte check and all role/process/admin/plan debits remain. '
                'Default counters do not predict or substitute for actual retirement counter debits. '
                'The 64 MiB administrative allowance and retained '
                'index/witness estimates are conditional planning estimates, not universal caps or '
                'guaranteed recovery. Post-retirement statvfs remains required before scientific '
                'prepare. This unsealed request author gives no recovery, capacity or scientific '
                'admission.'})
        review = out['parent_review_facts']; review['actual_default_only'] = False
        review['successful_default_original_bindings'] = default
        review['parent_default_acceptance_original'] = parent_pin
        review['parent_default_acceptance_review_basis'] = parent['review_basis']
        need(all(review[k] is parent[k] is True for k in ('accepted_for_exact_subset',
                 'accepted_library_preserving_sparse_scope','final14_completed_and_released')),
             'explicit_parent_review_acceptance_changed')
        additions = [{'path':BASE+'/lanl17-publish-sparse-parent-originals-20261008-a3.py',
                      'bytes':16126,'sha256':PUBLISHER_SHA},default['default_reviewed_plan']['file'],
                     default['default_review']]+default['all_originals']
        existing = {v['path']:v for v in out['protected_file_pins']}
        for pin in additions:
            if pin['path'] in existing:
                need(all(existing[pin['path']][k]==pin[k] for k in ('bytes','sha256')),
                     'existing_protected_original_changed')
            else:
                out['protected_file_pins'].append(copy.deepcopy(pin)); existing[pin['path']] = pin
        for directory in (CONTROL,guard_output):
            need(directory!=BASE and Path(directory).parent==Path(BASE),'no_BASE_ancestor_protection')
            if directory not in out['additional_protected_paths']:
                out['additional_protected_paths'].append(directory)
        need(out['selection_reason'].startswith(request['selection_reason'])
             and set(out)==set(request) and all(out[k]==request[k] for k in request if k not in MUTABLE),
             'outside_authorized_request_fields_changed')
        need(out['protected_file_pins'][:len(request['protected_file_pins'])]==request['protected_file_pins']
             and out['additional_protected_paths'][:len(request['additional_protected_paths'])]
                 ==request['additional_protected_paths'],'original_protections_changed')
        inputs.close()
        need(0<=(datetime.datetime.now(datetime.timezone.utc)-timestamp(out['checked_at'])).total_seconds()<=120,
             'fresh_capacity_expired_during_authoring')
        destination = Path(args.output)
        need(destination==TMP/'lanl17-actual-sparse-retirement-parent-request-20261008-a4.json'
             and not os.path.lexists(destination),
             'fresh_direct_tmp_unsealed_request_required')
        raw = canonical(out)+b'\n'; need(len(raw)<=2097152,'bounded_unsealed_request_required')
        inputs.left(); fd = os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        got,pin = inputs.read(destination,2097152,sha(raw)); need(got==raw,'published_request_changed')
        inputs.close()
        need(0<=(datetime.datetime.now(datetime.timezone.utc)-timestamp(out['checked_at'])).total_seconds()<=120,
             'fresh_capacity_expired_after_output')
        print(json.dumps({'format':'swdb.fresh-sparse-retirement-parent-request-author-return.v1','sealed':False,
              'output_original':pin,'checked_at':out['checked_at'],'selected_rows':out['selected_rows'],
              'minimum_cardinality':values['minimum_cardinality'],
              'conditional_margin_bytes':values['conditional_margin_after_administrative_allowance_bytes'],
              'original_default_acceptance_is_parent_semantics':True,'actual_plan_or_review_seal_generated':False,
              'remote_or_Git_or_selected_control_main_invoked':False,'capacity_or_scientific_admission':False},sort_keys=True))
        return 0
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        for s,handler in old_handlers.items():
            signal.signal(s,handler)


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Refused as error:
        print(json.dumps({'format':'swdb.fresh-sparse-retirement-parent-request-author-return.v1',
              'sealed':False,'refused':True,'reason_code':error.args[0],
              'conditional_parent_decision_facts':error.args[1] if len(error.args)==2 else None,
              'partial_unsealed_output_possible':True,'actual_plan_or_review_seal_generated':False},sort_keys=True))
        raise SystemExit(1)
