"""Local POSIX shared-memory setup diagnostic. Created2026-10-08 ET; no project/scientific evaluation."""
import ctypes,datetime,json,os,secrets
lib=ctypes.CDLL(None,use_errno=True)
lib.shm_open.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_uint];lib.shm_open.restype=ctypes.c_int
lib.shm_unlink.argtypes=[ctypes.c_char_p];lib.shm_unlink.restype=ctypes.c_int
name=("/swdb15."+str(os.getpid())+"."+secrets.token_hex(4)).encode();assert len(name)<31
fd=lib.shm_open(name,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);error=ctypes.get_errno();created=fd>=0
v={"format":"swdb.local-posix-shm-diagnostic.v1","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"name_bytes":len(name),"created":created,"shm_open_errno":error if not created else None,"scientific_evaluation_or_admission":False}
if created:
 try:os.ftruncate(fd,4096);v["ftruncate_passed"]=True
 finally:
  os.close(fd);v["owned_name_unlinked"]=lib.shm_unlink(name)==0
print(json.dumps(v,sort_keys=True))
