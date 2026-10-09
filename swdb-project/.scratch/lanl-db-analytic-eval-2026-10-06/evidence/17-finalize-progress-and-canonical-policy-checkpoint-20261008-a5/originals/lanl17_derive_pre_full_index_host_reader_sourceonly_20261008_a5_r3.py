from pathlib import Path
import ast,hashlib,json,os,difflib
r=Path('/private/tmp');p=r/'lanl17_pre_full_index_host_observation_20261008_a5_r2.py';old=p.read_text();assert hashlib.sha256(old.encode()).hexdigest()=='74e15563ebaa850b84db2018fb33ebe21829d006eb6e63c3176ea8f83c54e018';new=old
before="    closed(rows,ROUTE_ROLES,'exact_upcoming_output_route_roles');paths=[];out={}"
after="    need(type(rows) is dict and 1<=len(rows)<=len(ROUTE_ROLES) and set(rows)<=set(ROUTE_ROLES),'closed_explicit_next_stage_output_route_subset');paths=[];out={}"
assert new.count(before)==1;new=new.replace(before,after,1)
helper='''def inactive_owned_identity(p,ps):
    # Empty cmdline alone never proves absence. Only exact stable Z/X state can.
    b=kernel_bytes(p/'stat',8192,UID);v=b.rsplit(b')',1)[1].split()
    need(len(v)>=20 and b.split(b' ',1)[0]==p.name.encode() and v[0] in (b'Z',b'X'),'empty_owned_cmdline_not_proved_inactive')
    start=int(v[19]);need(start>0,'inactive_start_positive')
    b2=kernel_bytes(p/'stat',8192,UID);w=b2.rsplit(b')',1)[1].split()
    need(len(w)>=20 and b2.split(b' ',1)[0]==p.name.encode() and w[0] in (b'Z',b'X') and int(w[19])==start and p.stat().st_uid==UID and p.stat().st_ino==ps.st_ino,'inactive_process_identity_race')
    return {'pid':int(p.name),'uid':UID,'proc_inode':ps.st_ino,'start_ticks':start,'state':w[0].decode('ascii')}

'''
needle='def consumers(transport):';assert new.count(needle)==1;new=new.replace(needle,helper+needle,1)
before="            command=owned_cmdline(p,ps);argv=command[:-1].split(b'\\0') if command else []"
after="            command=owned_cmdline(p,ps)\n            if not command:\n                proof=inactive_owned_identity(p,ps);need(owned_cmdline(p,ps)==b'','inactive_cmdline_byte_continuity');continue\n            argv=command[:-1].split(b'\\0')"
assert new.count(before)==1;new=new.replace(before,after,1)
before="except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,subprocess.SubprocessError) as e:"
after="except (OSError,ValueError,KeyError,TypeError,IndexError,UnicodeError,RecursionError,subprocess.SubprocessError) as e:"
assert new.count(before)==1;new=new.replace(before,after,1);ast.parse(new)
def write(p,b):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b)
o=r/'lanl17_pre_full_index_host_observation_20261008_a5_r3.py';b=new.encode();d=r/'lanl17-pre-full-index-host-observation-r3-complete-r2-derivation-20261008-a5.diff';db=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(p),tofile=str(o))).encode();a=r/'lanl17_finalize_parent_host_readonly_20261008_a5_r2.py';fdiff=r/'lanl17-pre-full-index-host-observation-r3-complete-host-r2-derivation-20261008-a5.diff';fb=''.join(difflib.unified_diff(a.read_text().splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(a),tofile=str(o))).encode()
for q,z in [(o,b),(d,db),(fdiff,fb)]:write(q,z)
print(json.dumps({'source':str(o),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'diff':str(d),'diff_bytes':len(db),'diff_sha256':hashlib.sha256(db).hexdigest(),'full_diff':str(fdiff),'full_diff_bytes':len(fb),'full_diff_sha256':hashlib.sha256(fb).hexdigest()}))
