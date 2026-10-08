"""2026-10-08 ET: parent source and metadata review; no selected main/archive."""
import ast,datetime,hashlib,json,os,pathlib,stat,subprocess
P=pathlib.Path;T=P('/private/tmp');W=P('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve');HEAD='260a0d8ce9dce63a852d88e8cf2bb8cd484e78f1'
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def read(p,cap=64*1024*1024):
 p=P(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and s.st_size<=cap
 with p.open('rb') as f:
  b=f.read(cap+1);z=os.fstat(f.fileno())
 a=p.lstat();keys=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns');assert len(b)==s.st_size and all(getattr(s,'st_'+k)==getattr(z,'st_'+k)==getattr(a,'st_'+k) for k in keys)
 return b,dict(path=str(p),bytes=len(b),sha256=sha(b))
def write(name,o):
 b=(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=True,allow_nan=False)+'\n').encode();p=T/name
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 print(json.dumps(dict(path=str(p),bytes=len(b),sha256=sha(b))));return dict(path=str(p),bytes=len(b),sha256=sha(b))
def pin_exact(name,size,digest):
 b,p=read(T/name);assert (p['bytes'],p['sha256'])==(size,digest);return b,p
src,sp=pin_exact('lanl_copy_reviewed_portal_role_sources_and_inputs_from_git_20261008_a1_r3.py',19764,'cb760515ca47dcce55080e7856b43ce7d7cde91e490ffe9391654695a45f4457')
diff,dp=pin_exact('lanl17-portal-role-source-input-copy-r3-complete-r2-derivation-20261008.diff',6339,'e6ae7f1050ec7bdf2453ae4d5bba8b9c462dd6360285f7ce2c69c1955a49a855')
hand,hp=pin_exact('lanl17-portal-role-source-input-copy-r3-source-handoff-20261008-a1.md',5509,'e1db617bb3ca16e548f9252d2fae549596c1e14b8326b2121c42da6bd5b92c56')
ind,ip=pin_exact('lanl17-portal-role-source-input-copy-r3-final-independent-source-review-20261008-a1.md',3589,'b11f072e6541ff98fb59c4931d0de4d94b7beb0a1cc2399fa4e559c4dd6c40d6')
role,rp=pin_exact('lanl17-exact-portal-autounmount-parent-semantic-review-20261008-a1.json',4517,'add69481b9eb0c8a5711308b9942479a0ce639797a4e67a816df082b022cb989')
o=json.loads(role);assert o['identity_sha256']==sha(canonical({k:v for k,v in o.items() if k!='identity_sha256'}))=='2bbc0b120aa0eaeded6503c2fb5f417b043b9818dd98e309727b7e57a85b42bb'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
root=write('lanl17-portal-role-source-input-copy-r3-final-parent-source-review-20261008-a1.json',dict(format='swdb.portal-source-input-copy.parent-source-review.v1',sealed=False,reviewed_utc=now,source=sp,complete_diff=dp,handoff=hp,independent_review=ip,actual_role_review=rp,full_source_and_complete_delta_and_handoffs_read=True,static_delta_and_original_assignments_imports_other_functions_checked=True,original_signal_cleanup_finding_corrected_in_source=True,accepted_for_one_exact_finite_copy_after_delivered_Git_bootstrap=True,all_original_limits_thirteen_routes_and_pins_preserved=True,runtime_signal_or_cleanup_UNTESTED=True,own_direct_BASE_source_dynamic_delivered_R_manifest_and_outer_capture_required=True,selected_mains_copy_Git_SSH_or_scientific_admission_performed_by_review=False))
raw,invpin=pin_exact('lanl17-observation-source-custody-known251-explicit-inventory-draft-20261008-a1.json',151670,'e4dd91ebc02bc37169e2ec65953636bfa20401a602fb7eb4f1dbb1c84c552044');inv=json.loads(raw);assert len(inv['rows'])==251
extra=[sp,dp,hp,ip,root]
for pin in extra:
 inv['rows'].append(dict(scope='portal-source-input-copy-r3-final-review',original_path=pin['path'],original_bytes=pin['bytes'],original_sha256=pin['sha256'],stored_relative_path='portal-source-input-copy-r3-final-review/'+P(pin['path']).name,storage_codec='plain',content_class='bounded_metadata_original' if P(pin['path']).suffix=='.json' else 'plain_source_or_document',original_policy=dict(kind='original_unsealed_JSON',original_sealed_field=False) if P(pin['path']).suffix=='.json' else dict(kind='opaque_exact_original_bytes')))
assert len(inv['rows'])==256 and len({r['original_path'] for r in inv['rows']})==256 and len({r['stored_relative_path'] for r in inv['rows']})==256
seals=[];tot=0
for row in inv['rows']:
 b,p=read(row['original_path']);assert (len(b),sha(b))==(row['original_bytes'],row['original_sha256']);tot+=len(b)
 old=row['original_policy']
 if old['kind']=='explicit_original_seal':
  row['original_policy_as_prepared']=old.copy();row['original_policy']=dict(kind='original_sealed_JSON',identity_key='identity_sha256',identity_sha256=old['identity_sha256'],canonical_ensure_ascii=old['canonical_ensure_ascii'],flag_originally_present=old['canonical_policy_field_present'])
 pol=row['original_policy']
 if pol['kind']=='original_sealed_JSON':
  o=json.loads(b);flag=pol['canonical_ensure_ascii'];assert ('canonical_ensure_ascii' in o)==pol['flag_originally_present'];assert o.get('canonical_ensure_ascii',True)==flag and flag is True;assert o['identity_sha256']==pol['identity_sha256']==sha(json.dumps({k:v for k,v in o.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=flag,allow_nan=False).encode());seals.append(p)
 elif pol['kind']=='original_unsealed_JSON':
  o=json.loads(b);assert isinstance(o,dict) and 'identity_sha256' not in o and 'canonical_ensure_ascii' not in o
  if 'original_sealed_field' in pol:assert o.get('sealed','ABSENT')==pol['original_sealed_field']
 else:assert pol['kind']=='opaque_exact_original_bytes'
 plain=P(row['original_path']).suffix in {'.py','.md','.diff','.c','.h','.sh','.txt','.dsc'} or P(row['original_path']).name=='tmux.conf';gzip=len(b)>1024*1024 and not plain
 assert row['content_class']==('plain_source_or_document' if plain else 'bounded_metadata_original') and row['storage_codec']==('gzip_mtime0' if gzip else 'plain')
 assert not P(row['stored_relative_path']).is_absolute() and '..' not in P(row['stored_relative_path']).parts
assert len(seals)==2 and tot<512*1024*1024
inv.update(state='parent_reviewed_final_explicit_inventory',pending_explicit_extensions=[],missing_named_originals=[],known_original_count=256,original_bytes_total=tot,remaining_count_slots_before_pending_exact_extensions=0,prior_known251_draft_pin=invpin,parent_copier_R3_acceptance_pin=root,all_256_original_whole_byte_pins_and_policy_descriptions_parent_checked=True,snapshot_boundary='The snapshot includes the original failed/incomplete observer A4, finite original reference/birth/dependency/source-package and native-command metadata, reviewed G7/O8 controls/wrappers and copier/publisher sources, and the one genuine 16-test result. Creation-time NOTRUN packets remain unchanged. Final inventory and final archive execution-review controls are supplied separately to avoid circularity; their exact pins are carried in the resulting manifest. Source staging, hook publication, observer O5, default/removal guards, ticket17 prepare/freeze, four normal campaigns and all scientific completion remain pending at this snapshot.')
inv['original_policy_descriptor_mapping']='Only two prepared explicit_original_seal descriptor names map to archiver original_sealed_JSON; the complete original prepared descriptors remain alongside the runtime descriptors. Original bytes, fields, flags, IDs, seals and codecs are unchanged.'
finalpin=write('lanl17-observation-source-custody-final256-explicit-inventory-20261008-a1.json',inv)
araw,apin=pin_exact('lanl17_archive_reviewed_observation_source_byte_custody_20261008_a1_r3.py',22778,'0219d0689f8833a17e45031bb55f066d0de53602b1941bb7a9f93b43c6ee783d');ast.parse(araw)
aold,_=pin_exact('lanl17_archive_reviewed_observation_source_byte_custody_20261008_a1_r2.py',22778,'5715f1003d8e55c9dda580ecf42ea02cabd7dc72177104f3fb62c7f2a0ed8e7c');assert araw.replace(b'MAX_ROWS = 256\n',b'MAX_ROWS = 192\n',1)==aold
cmd=['git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-C',str(W)]
def git(*args):return subprocess.check_output(cmd+list(args),timeout=60)
assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain','-z','--untracked-files=all');tree=git('ls-tree','-r','-z',HEAD);count=sum(bool(x) for x in tree.split(b'\0'));assert count==4567
assert git('ls-tree','-r','-z',HEAD,'--','swdb-project/swdb')==git('ls-tree','-r','-z','f893fed400347ed23d92e917d8bde21b75e5375d','--','swdb-project/swdb');assert not (W/inv['archive_relative_path']).exists()
review=dict(format='swdb.local-observation-byte-custody-parent-review.v1',canonical_ensure_ascii=True,reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted_for_exact_byte_custody_archive=True,inventory_sha256=finalpin['sha256'],archiver_sha256=apin['sha256'],expected_head=HEAD,prior_tracked_entries=count,prior_tree_bytes_sha256=sha(tree),exact_original_count=256,original_bytes_total=tot,two_original_True_seals_checked=seals,full_archiver_source_read_and_R3_only_MAX_ROWS_change_verified=True,all_original_whole_bytes_stat_pins_and_policy_descriptions_checked=True,finite_five_explicit_additions=extra,capacity_scientific_selected_main_or_Git_mutation_admission=False,final_input_selfcycle_avoided=True)
review['identity_sha256']=sha(canonical(review));write('lanl17-observation-byte-custody-final256-parent-execution-review-20261008-a1.json',review)
