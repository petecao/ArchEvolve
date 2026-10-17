"""NOT RUN. Future stdlib-only AST lifts of exact tiny metadata functions.

Synthetic in-memory fixtures; never import a G/O module, call its main or real
helper, inspect /proc/filesystem, use libc/Git/SSH, delete or clear any path.
"""
import ast
import copy
import hashlib
import json
import os
import pathlib
import re
import stat
import types
import unittest

G=pathlib.Path('/private/tmp/lanl_consumed_detached_source_guard_r7_20261008_a1.py')
G_SHA='97219cdb326edf76e6d341aab4a2a8d58a4750e3da8d2e24a5f9e1097f4a69be'
HELPER_SHA='c195eccf8f728f7752dd89e0588af4fe6f0c05f50c7aa6cb47e5bd95f9ecb46b'
UID=114316761
BASE=pathlib.Path('/data1/yanruj')
PRIMARY=BASE/'ArchEvolve'
class Refused(Exception):pass
def require(ok,code):
    if not ok:raise Refused(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def sealed(v):
    v=copy.deepcopy(v);v['identity_sha256']=sha(canonical(v));return v

def lift(name,nested=None,extra=None):
    # This future loader parses one exact bounded source; no module evaluation.
    with G.open('rb') as source:raw=source.read(117232+1)
    require(len(raw)==117232 and sha(raw)==G_SHA,'fixture_source_byte_pin')
    module=ast.parse(raw);node=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name==name)
    if nested is not None:
        node=next(x for x in node.body if isinstance(x,ast.FunctionDef) and x.name==nested)
    source=ast.get_source_segment(raw.decode(),node)
    require(source is not None,'fixture_exact_source_span')
    lifted=ast.Module(body=[copy.deepcopy(node)],type_ignores=[])
    env={'__builtins__':__builtins__,'require':require,'sha':sha,'canonical':canonical,'hashlib':hashlib,
         'json':json,'os':os,'re':re,'stat':stat,'P':pathlib.Path,'PRIMARY':PRIMARY,'UID':UID}
    env.update(extra or {})
    exec(compile(ast.fix_missing_locations(lifted),str(G)+'::isolated::'+node.name,'exec'),env)
    return env[node.name]

def definitions():
    return {f'synthetic-row-{i:02d}':{'path':str(BASE/f'synthetic-row-{i:02d}'),'head':'0'*40,
            'historical_allocated_bytes':0,'receipts':[]} for i in range(18)}
def obj(path,kind=1,children=None,birth=1791329486):
    mode=(stat.S_IFDIR|0o775) if kind==0 else (stat.S_IFLNK|0o777) if kind==2 else (stat.S_IFREG|0o664)
    s=[2097,100+len(path),mode,UID,0,2 if kind==0 else 1,4096 if kind==0 else 8,8,1,1]
    names=sorted(children or [],key=os.fsencode)
    return [path,s,[8191,8191,0,3160180,136,True,birth,0],
            len(names) if kind==0 else None,sha(b'\0'.join(os.fsencode(n) for n in names)) if kind==0 else None,kind]
def finalize_row(row):
    d=hashlib.sha256()
    for o in row['original_objects']:
        b=canonical(o);d.update(len(b).to_bytes(8,'big'));d.update(b)
    n=len(row['original_objects']);row.update(first_objects_observed=n,second_objects_observed=n,
        first_metadata_sha256=d.hexdigest(),second_metadata_sha256=d.hexdigest())
def birth_document(admin=False):
    defs=definitions();rows=[]
    # A complete small tree preserves the production's two exact symlink names.
    paths=[('.',0,['swdb-project']),('swdb-project',0,['weeklogs']),
      ('swdb-project/weeklogs',0,['2026-09-24','2026-09-30']),
      ('swdb-project/weeklogs/2026-09-24',0,['.build']),
      ('swdb-project/weeklogs/2026-09-24/.build',0,['node_modules']),
      ('swdb-project/weeklogs/2026-09-24/.build/node_modules',2,None),
      ('swdb-project/weeklogs/2026-09-30',0,['.build']),
      ('swdb-project/weeklogs/2026-09-30/.build',0,['node_modules']),
      ('swdb-project/weeklogs/2026-09-30/.build/node_modules',2,None)]
    for name,definition in defs.items():
        root=str(PRIMARY/'.git/worktrees'/name) if admin else definition['path']
        objects=[obj('.',0,['HEAD']),obj('HEAD')] if admin else [obj(p,k,c) for p,k,c in paths]
        row={'row':name,'path':root,'g5_definition':copy.deepcopy(definition),'original_objects':objects,
             'first_pass_completed':True,'second_pass_completed':True,'metadata_equal_between_passes':True}
        if admin:row['original_pointer_route']=root
        else:row['git_indirection']={'original_pointer_route':str(PRIMARY/'.git/worktrees'/name)}
        finalize_row(row);rows.append(row)
    doc={'format':'swdb.exact-portal-helper-worktree-administration-inode-birth-query.v1' if admin else
          'swdb.exact-portal-helper-checkout-inode-birth-query.v1','sealed':False,
         'cleanup_capacity_or_scientific_admission':False,'boot_clock_interval_equal':True,
         'clock_before':{'boot_epoch_seconds':1785498067,'clock_ticks_per_second':100},
         'clock_after':{'boot_epoch_seconds':1785498067,'clock_ticks_per_second':100},
         'all_eighteen_walks_completed_and_metadata_stable':True,
         'g5_source_sha256':'a84dc9ca7ccd20e6485cc8e9a2007b3b982fad9c5ae19dacbb1f164d664748cb',
         'symlink_targets_and_shared_git_admin_not_traversed':True,
         'administration_anchor_metadata_interval_equal':True,'public_identity_interval_equal':True,
         'genuine_prior_checkout_birth_original_pin':{'bytes':14762700,'sha256':'e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7'},
         'object_encoding':{'format':'ordered-array.v1','original_stat_fields':
           ['dev','ino','mode','uid','gid','nlink','size','blocks','mtime_ns','ctime_ns'],
           'original_statx_fields':['returned_mask','requested_mask','attributes','attributes_mask',
                'mount_id_or_null','birth_supported','birth_seconds','birth_nanoseconds'],
           'object_fields':['relative_path','original_stat','original_statx','directory_names_count_or_null',
                'directory_names_digest_or_null','type_code']},'rows':rows}
    return doc,defs

def review():
    keys=('trusted_host_clock_and_inode_birth_history','installed_native_image_matches_running_child',
       'installed_packages_correspond_to_reviewed_exact_source',
       'libfuse_3_14_wait_loop_has_only_control_socket_and_fixed_mount_target',
       'all_potentially_removed_checkout_and_git_admin_inodes_postdate_helper',
       'node_modules_symlink_targets_are_not_followed_or_removed',
       'ordinary_portal_parent_and_other_consumers_still_checked',
       'existing_git_shared_objects_refs_and_alias_gates_remain_mandatory')
    return sealed({'format':'swdb.exact-portal-autounmount-semantic-parent-review.v1','canonical_ensure_ascii':True,
        'accepted_exact_role_only':True,'shared_helper_sha256':HELPER_SHA,'pid':1654291,'start_ticks':559081545,
        'parent_pid':1654279,'parent_start_ticks':559081538,'explicit_assumptions':dict.fromkeys(keys,True),
        'inherited_file_descriptors_not_generically_closed':True,'protected_child_fields':dict.fromkeys(
            ('fd','cwd','root','exe','maps','syscall','wait_channel'),'UNOBSERVED'),
        'global_reference_free_or_cleanup_capacity_or_scientific_admission':False,
        'other_consumers_parent_or_descendants_exempted':False,
        'admin_birth_producer_pin':{'bytes':52031,'sha256':'b2b08374ea997679df9e08894fc14d139cce9f9c90ab3dabd324db36d6f661a3'},
        'lifecycle_research_pin':{'bytes':13046,'sha256':'9c83f802ed7d467c8411c3253be9bac330827ba01a935a11bb7a6ed9eb248840'}})

def public_fixture(pid=1654291,start=559081545,ppid=1654279):
    caps={'CapInh':'0000000000000000','CapPrm':'000001ffffffffff','CapEff':'000001ffffffffff',
          'CapBnd':'000001ffffffffff','CapAmb':'0000000000000000'}
    values=['S',str(ppid)]+['0']*17+[str(start)]+['0']*3
    rs=(str(pid)+' (fusermount3) '+' '.join(values)).encode()
    fields={'Name':'fusermount3','Pid':str(pid),'PPid':str(ppid),'Uid':f'{UID} 0 0 0',
            'Gid':' '.join([str(UID)]*4),'State':'S sleeping','Threads':'1','TracerPid':'0',**caps}
    return rs,('\n'.join(k+': '+v for k,v in fields.items())+'\n').encode(),caps

class Contracts(unittest.TestCase):
    def test_actual_remaining_scope_and_no_fake_journal(self):
        defs=definitions();names=list(defs);selected=names[:3];removed=[names[0]]
        f=lift('exact_portal_autounmount_identification','continuity_scope',{'row_definitions':defs})
        before=canonical([selected,removed])
        self.assertEqual(f(selected,removed,None),sorted(names[1:3]))
        self.assertEqual(f(selected,removed,[names[2]]),[names[2]])
        self.assertEqual(canonical([selected,removed]),before)
        for continuity in ([names[0]],[names[3]],[names[1],names[1]],[]):
            with self.assertRaisesRegex(Refused,'continuity_scope'):f(selected,removed,continuity)
        for bad_removed in ([names[3]],[names[0],names[0]]):
            with self.assertRaisesRegex(Refused,'journal_scope'):f(selected,bad_removed,None)


    def setUp(self):self.validate=lift('portal_inode_birth_rows')
    def test_complete_both_scopes_and_input_immutability(self):
        for admin in (False,True):
            doc,defs=birth_document(admin);before=canonical(doc);ticks=[];r=self.validate(doc,defs,admin,lambda:ticks.append(1))
            self.assertGreaterEqual(len(ticks),sum(len(row['original_objects']) for row in doc['rows']))
            self.assertEqual(len(r),18);self.assertEqual(canonical(doc),before)
            self.assertEqual(sum(x['counts'][2] for x in r.values()),0 if admin else 36)
    def test_contained_old_inode_refuses_even_with_new_root(self):
        doc,defs=birth_document(True);doc['rows'][0]['original_objects'][1][2][6]=1780000000
        finalize_row(doc['rows'][0])
        with self.assertRaisesRegex(Refused,'not_strictly_after'):self.validate(doc,defs,True)
    def test_exact_conservative_cutoff_refuses(self):
        doc,defs=birth_document(True);x=doc['rows'][0]['original_objects'][1][2];x[6]=1791088883;x[7]=460000000
        finalize_row(doc['rows'][0])
        with self.assertRaisesRegex(Refused,'not_strictly_after'):self.validate(doc,defs,True)
    def test_unsupported_birth_and_portal_device_refuse(self):
        for change in ('unsupported','device'):
            doc,defs=birth_document(True);o=doc['rows'][0]['original_objects'][1]
            if change=='unsupported':o[2][5]=False
            else:o[1][0]=48
            finalize_row(doc['rows'][0])
            with self.assertRaises(Refused):self.validate(doc,defs,True)
    def test_hardlink_and_special_inode_refuse(self):
        for change in ('link','special'):
            doc,defs=birth_document(True);o=doc['rows'][0]['original_objects'][1]
            if change=='link':o[1][5]=2
            else:o[1][2]=stat.S_IFIFO|0o600;o[5]=3
            finalize_row(doc['rows'][0])
            with self.assertRaises(Refused):self.validate(doc,defs,True)
    def test_known_symlink_is_inode_only_and_admin_symlink_refuses(self):
        doc,defs=birth_document(False);r=self.validate(doc,defs)
        self.assertTrue(all(x['counts'][2]==2 for x in r.values()))
        doc,defs=birth_document(True);o=doc['rows'][0]['original_objects'][1];o[5]=2;o[1][2]=stat.S_IFLNK|0o777
        finalize_row(doc['rows'][0])
        with self.assertRaisesRegex(Refused,'unreviewed_symlink'):self.validate(doc,defs,True)
    def test_missing_child_inventory_refuses_with_rebuilt_digest(self):
        doc,defs=birth_document(True);doc['rows'][0]['original_objects'].pop();finalize_row(doc['rows'][0])
        with self.assertRaisesRegex(Refused,'directory_inventory'):self.validate(doc,defs,True)
    def test_wrong_complete_digest_and_row_route_refuse(self):
        for change in ('digest','route'):
            doc,defs=birth_document(True)
            if change=='digest':doc['rows'][0]['first_metadata_sha256']='0'*64
            else:doc['rows'][0]['path']+='/other'
            with self.assertRaises(Refused):self.validate(doc,defs,True)
    def test_admin_scope_cannot_be_replaced_by_checkout_original(self):
        doc,defs=birth_document(False)
        with self.assertRaisesRegex(Refused,'admin_birth'):self.validate(doc,defs,True)
    def test_exact_public_mixed_uid_process_only(self):
        rs,ss,caps=public_fixture();f=lift('exact_portal_autounmount_identification','process_fields',
            {'original':{'child':{'capability_hex':caps}}})
        self.assertEqual(f(rs,ss,1654291,559081545,1654279,True)['uids'],[UID,0,0,0])
        for pid,start,ppid in ((1654292,559081545,1654279),(1654291,559081546,1654279),(1654291,559081545,1)):
            with self.assertRaises(Refused):f(rs,ss,pid,start,ppid,True)
    def test_live_or_multithread_other_uid_refuses(self):
        rs,ss,caps=public_fixture();f=lift('exact_portal_autounmount_identification','process_fields',
            {'original':{'child':{'capability_hex':caps}}})
        for changed in (ss.replace(b'Threads: 1',b'Threads: 2'),ss.replace(f'Uid: {UID} 0 0 0'.encode(),b'Uid: 7 0 0 0'),ss.replace(b'State: S',b'State: R')):
            with self.assertRaises(Refused):f(rs,changed,1654291,559081545,1654279,True)
    def test_non_circular_semantic_review_seal_and_input_preservation(self):
        f=lift('exact_portal_autounmount_identification','review_binding',{'helper_sha256':HELPER_SHA})
        r=review();before=canonical(r);f(r);self.assertEqual(canonical(r),before)
        r['pid']=999
        with self.assertRaises(Refused):f(r)
    def test_resealed_missing_assumption_or_fake_visibility_refuses(self):
        f=lift('exact_portal_autounmount_identification','review_binding',{'helper_sha256':HELPER_SHA})
        for change in ('assumption','FD','visibility'):
            r=review();r.pop('identity_sha256')
            if change=='assumption':r['explicit_assumptions'].pop('installed_native_image_matches_running_child')
            elif change=='FD':r['inherited_file_descriptors_not_generically_closed']=False
            else:r['protected_child_fields']['fd']='CLEAR'
            with self.assertRaises(Refused):f(sealed(r))
    def test_same_inode_live_stat_contract_refuses_replacement(self):
        # Exact live_scope, with a closed in-memory tree and no real OS calls.
        doc,defs=birth_document(True);rows=self.validate(doc,defs,True);name=next(iter(rows));row=rows[name]
        meta={str(pathlib.Path(row['root'])/rel) if rel!='.' else row['root']:copy.deepcopy(o) for rel,o in row['objects'].items()}
        class FakePath:
            def __init__(self,p):self.value=str(p)
            def __truediv__(self,p):return FakePath(self.value+'/'+p)
            def __str__(self):return self.value
        def sf(s):return s.values
        def current(p):return types.SimpleNamespace(values=list(meta[str(p)][1]))
        class Entries:
            def __enter__(self):return iter([types.SimpleNamespace(name='HEAD')])
            def __exit__(self,*unused):pass
        charges=[];fdpath={};counter=[0]
        def opened(p,*unused):counter[0]+=1;fdpath[counter[0]]=str(p);return counter[0]
        fake_os=types.SimpleNamespace(fsencode=os.fsencode,O_RDONLY=0,O_DIRECTORY=0,O_NOFOLLOW=0,O_CLOEXEC=0,
            open=opened,fstat=lambda fd:current(FakePath(fdpath[fd])),close=lambda fd:None,scandir=lambda fd:Entries())
        extra={'P':FakePath,'remaining':[name],'route':lambda p:current(p),'actual_stat':current,'stat_fact':sf,
               'check_deadline':lambda:None,'charge_metadata':lambda *v:charges.append(v),'charge_bytes':lambda n:None,'os':fake_os}
        f=lift('exact_portal_autounmount_identification','live_scope',extra);f(rows)
        before=sum(v[0] for v in charges);self.assertEqual(before,len(row['objects']))
        meta[row['root']+'/HEAD'][1][1]+=1
        with self.assertRaisesRegex(Refused,'inode_or_stat'):f(rows)
    def test_original_counted_inode_replacement_not_new_root_only(self):
        doc,defs=birth_document(True);old=copy.deepcopy(doc);doc['rows'][0]['original_objects'][1][1][1]+=1000
        # A changed retained body cannot be accepted under the original digest.
        with self.assertRaisesRegex(Refused,'complete_digest'):self.validate(doc,defs,True)
        self.assertEqual(old['rows'][0]['original_objects'][0],doc['rows'][0]['original_objects'][0])

if __name__=='__main__':unittest.main()
