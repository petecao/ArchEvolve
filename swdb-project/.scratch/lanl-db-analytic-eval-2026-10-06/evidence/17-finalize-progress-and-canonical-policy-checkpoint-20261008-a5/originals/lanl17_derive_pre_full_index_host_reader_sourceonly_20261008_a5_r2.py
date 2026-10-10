from pathlib import Path
import ast,hashlib,json,os,difflib
r=Path('/private/tmp');p=r/'lanl17_pre_full_index_host_observation_20261008_a5_r1.py';old=p.read_text();assert hashlib.sha256(old.encode()).hexdigest()=='5f9062fdd83e849d5cc64905e4b340df9070c012bb71e93ac592b06490b6a0a5'
t=ast.parse(old);node=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='consumers');original=ast.get_source_segment(old,node)
replacement='''def owned_cmdline(p,ps):
    # Preserve ancestor's owned-directory scan scope. Strict kernel UID/start
    # guards apply to matching consumers, not every unrelated owned stat file.
    tick();q=p/'cmdline';s=q.lstat();need(stat.S_ISREG(s.st_mode),'owned_cmdline_regular')
    fd=os.open(q,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as f:
        need(stamp(os.fstat(f.fileno()))==stamp(s),'owned_cmdline_open_race');raw=f.read(65537)
        need(len(raw)<=65536 and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(q.lstat()),'owned_cmdline_cap_or_race')
    after=p.stat();need(after.st_uid==UID and after.st_ino==ps.st_ino,'owned_cmdline_directory_race')
    need(not raw or raw.endswith(b'\\0'),'owned_cmdline_terminated');return raw

def consumers(transport):
    matches=[];unknowns=[];seen=0;owned=0;needles=[str(SOURCE).encode(),str(RAW).encode(),str(H).encode()]
    for p in Path('/proc').iterdir():
        tick();seen+=1;need(seen<=32768,'process_inventory_bound')
        if not p.name.isdecimal() or int(p.name) in (transport['self']['pid'],transport['parent']['pid']):continue
        pid=int(p.name);proof=None
        try:
            ps=p.stat()
            if ps.st_uid!=UID:continue
            owned+=1;need(owned<=4096,'owned_process_bound');proof={'pid':pid,'uid':UID,'proc_inode':ps.st_ino}
            command=owned_cmdline(p,ps);argv=command[:-1].split(b'\\0') if command else []
            matched=any(needle in arg for needle in needles for arg in argv)
            if matched:
                identity,current_argv,exe=process_identity(pid)
                need(identity['proc_inode']==ps.st_ino and identity['cmdline_sha256']==digest(command) and current_argv==argv,'matching_consumer_identity_race')
                proof=identity
                raw=kernel_bytes(p/'stat',8192,UID);parts=raw.rsplit(b')',1)[1].split()
                need(len(parts)>=20 and int(parts[19])==identity['start_ticks'] and p.stat().st_uid==UID and p.stat().st_ino==ps.st_ino,'matching_consumer_final_identity_race')
                if parts[0] not in (b'Z',b'X'):
                    need(len(matches)<128,'matching_consumer_bound');matches.append(identity)
            need(owned_cmdline(p,ps)==command,'owned_cmdline_byte_continuity')
        except (OSError,ValueError,IndexError,UnicodeError) as exc:
            if isinstance(exc,(FileNotFoundError,ProcessLookupError)) and proof is None:continue
            need(len(unknowns)<128,'unknown_process_bound');unknowns.append({**(proof or {}),'state':'unknown','error_class':type(exc).__name__,'reason_sha256':digest(str(exc).encode())})
    return {'state':'unknown' if unknowns else 'observed','owned_processes_checked':owned,'matching_live_consumers':matches,'unknown_processes':unknowns,'no_live_owned_source_RAW_consumers':not unknowns and not matches,'partial_inventory_cannot_prove_absence':True,'strict_kernel_identity_checked_for_matching_consumers_only':True,'process_argv_or_other_users_bodies_returned':False}
'''
assert old.count(original)==1;new=old.replace(original,replacement,1)
oldhome="    need(all(not os.environ.get(k) for k in STARTUP),'unsafe_startup_or_POSIX_environment')"
newhome=oldhome+"\n    need('posix' not in os.environ.get('SHELLOPTS','').split(':') and not any(k.startswith('BASH_FUNC_') for k in os.environ),'unsafe_Bash_posix_or_exported_function_startup')"
assert new.count(oldhome)==1;new=new.replace(oldhome,newhome,1);ast.parse(new)
o=r/'lanl17_pre_full_index_host_observation_20261008_a5_r2.py';b=new.encode();d=r/'lanl17-pre-full-index-host-observation-r2-complete-r1-derivation-20261008-a5.diff';db=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(p),tofile=str(o))).encode();ancestor=r/'lanl17_finalize_parent_host_readonly_20261008_a5_r2.py';full=r/'lanl17-pre-full-index-host-observation-r2-complete-host-r2-derivation-20261008-a5.diff';fb=''.join(difflib.unified_diff(ancestor.read_text().splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(ancestor),tofile=str(o))).encode()
def write(p,b):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b)
for path,data in [(o,b),(d,db),(full,fb)]:write(path,data)
print(json.dumps({'source':str(o),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'diff':str(d),'diff_bytes':len(db),'diff_sha256':hashlib.sha256(db).hexdigest(),'full_diff':str(full),'full_diff_bytes':len(fb),'full_diff_sha256':hashlib.sha256(fb).hexdigest()}))
