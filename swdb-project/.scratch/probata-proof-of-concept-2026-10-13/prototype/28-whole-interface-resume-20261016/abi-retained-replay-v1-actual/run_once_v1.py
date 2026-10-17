"""Once-admitted exclusive control staging and exact passive metadata invocation."""
import base64
import hashlib
import json
from pathlib import Path
import selectors
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / "abi-retained-replay-v1"
ADMISSION = HERE.parents[2] / "evidence/t28-ABI-v2-retained-replay-v1-root-once-admission-20261016.json"
ROOT = "/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-abi-retained-replay-v1"
SOURCE = "/data1/yanruj/probata-resume-20261016-2baf722f"
COMMIT = "2baf722fdaa6cba24b859eae3172a6f597417d72"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw))
def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
def bounded_remote(label, argv, payload, seconds):
    started = time.monotonic()
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    writer_errors = []
    def writer():
        try:
            process.stdin.write(payload)
            process.stdin.close()
        except (BrokenPipeError, OSError) as error:
            writer_errors.append(type(error).__name__)
    thread = threading.Thread(target=writer, daemon=True); thread.start()
    selected = selectors.DefaultSelector()
    selected.register(process.stdout, selectors.EVENT_READ, "stdout")
    selected.register(process.stderr, selectors.EVENT_READ, "stderr")
    output = {"stdout": bytearray(), "stderr": bytearray()}; refusal = None
    while selected.get_map():
        if time.monotonic() - started > seconds:
            refusal = "local transport timeout"; process.kill(); break
        for key, _mask in selected.select(0.25):
            chunk = key.fileobj.read1(4096)
            if not chunk:
                selected.unregister(key.fileobj); continue
            name = key.data
            if len(output[name]) + len(chunk) > 65536:
                refusal = name + " extent cap"; process.kill(); break
            output[name].extend(chunk)
        if refusal: break
    selected.close()
    try: code = process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill(); code = process.wait(timeout=10); refusal = refusal or "local settlement timeout"
    thread.join(timeout=1)
    for name, raw in output.items():
        with (HERE / (label + "-" + name + ".json")).open("xb") as stream: stream.write(raw)
    result = dict(argv=argv, stdin_sha256=sha(payload), stdin_bytes=len(payload), returncode=code,
                  local_wall_seconds=time.monotonic()-started, local_refusal=refusal,
                  writer_errors=writer_errors, stdout=pin(HERE/(label+"-stdout.json")),
                  stderr=pin(HERE/(label+"-stderr.json")))
    save(label + "-invocation.json", result)
    if code != 0 or refusal: raise RuntimeError(label + " refused; preserved without retry")
    return json.loads(output["stdout"])

def main():
    assert sha(ADMISSION.read_bytes()) == "7361b29ba6bc97206db08510ce970815cac86c33de82068c7e32f1cb676abaa3"
    assert sha((PACKET/"source-packet-v1.json").read_bytes()) == "c72dab7efbdef1342c5f89efdb0f0e96dffde3be341d908845ae17432c183b1d"
    command_raw = (PACKET/"command-v1.json").read_bytes()
    assert sha(command_raw) == "c0a10e79571a74b89d82f73ca7baff63252ce80188719a75f024eb0121bc78c6"
    command = json.loads(command_raw)
    manifest = json.loads((PACKET/"staging-manifest-v1.json").read_bytes())
    assert manifest["fresh_root"] == ROOT and len(manifest["files"]) == 8
    payload = []
    for row in manifest["files"]:
        raw = Path(row["source"]["path"]).read_bytes()
        assert len(raw) == row["source"]["bytes"] == row["destination"]["bytes"]
        assert sha(raw) == row["source"]["sha256"] == row["destination"]["sha256"]
        assert Path(row["destination"]["path"]).parent == Path(ROOT)/"control"
        payload.append(dict(pin=row["destination"], data=base64.b64encode(raw).decode()))
    assert sum(row["pin"]["bytes"] for row in payload) == 575171
    stage = """import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(30,35))
import base64,hashlib,json,os,stat,subprocess,time
from pathlib import Path
ROOT=Path(ROOT_LITERAL)
SOURCE=Path(SOURCE_LITERAL)
COMMIT=COMMIT_LITERAL
PAYLOAD=PAYLOAD_LITERAL
def stable(st):return tuple(getattr(st,k)for k in('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
leases={p.name:json.loads(p.read_bytes())for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
assert len(leases)==3 and all(v['state']=='released'for v in leases.values())
git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
assert subprocess.check_output(git+['rev-parse','HEAD'],timeout=10).decode().strip()==COMMIT
assert subprocess.check_output(git+['status','--porcelain','--untracked-files=all'],timeout=10)==b''
assert SOURCE.resolve(strict=True)==SOURCE and stat.S_ISDIR(SOURCE.lstat().st_mode)
assert ROOT.parent.resolve(strict=True)==ROOT.parent and not os.path.lexists(ROOT)
runtime=json.loads(base64.b64decode(next(v['data']for v in PAYLOAD if v['pin']['path'].endswith('/policy.json'))))
selected=Path('/usr/bin/python3.12');assert hashlib.sha256(selected.read_bytes()).hexdigest()==runtime['runtime_hashes'][str(selected)]
ROOT.mkdir();(ROOT/'control').mkdir();rows=[]
for row in PAYLOAD:
 p=Path(row['pin']['path']);raw=base64.b64decode(row['data'],validate=True)
 assert len(raw)==row['pin']['bytes']and hashlib.sha256(raw).hexdigest()==row['pin']['sha256']
 with p.open('xb')as handle:handle.write(raw);handle.flush();os.fsync(handle.fileno())
 before=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(before.st_mode)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==row['pin']['sha256']and stable(p.lstat())==stable(before)
 rows.append(row['pin'])
assert sorted(p.name for p in(ROOT/'control').iterdir())==sorted(Path(v['path']).name for v in rows)
print(json.dumps(dict(schema='exclusive-ABI-replay-staging-1',root=str(ROOT),files=rows,leases=leases,source_commit=COMMIT,source_clean=True,compiler_native_solver_executed=False),sort_keys=True))
"""
    stage = stage.replace("ROOT_LITERAL", repr(ROOT)).replace("SOURCE_LITERAL", repr(SOURCE)).replace("COMMIT_LITERAL", repr(COMMIT)).replace("PAYLOAD_LITERAL", repr(payload))
    stage_path=HERE/"exclusive_staging_v1.py";stage_path.write_text(stage)
    save("local-readback-v1.json", dict(admission=pin(ADMISSION),command=pin(PACKET/"command-v1.json"),
         stdin=pin(PACKET/"replay_entry_v1.py"), staging=pin(stage_path), files=[r["pin"]for r in payload]))
    stage_command="/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/timeout --signal=TERM --kill-after=5s 45s /usr/bin/python3 -I -B -"
    bounded_remote("staging", ["ssh","mbit10",stage_command], stage.encode(),60)
    raw=Path(command["stdin"]["path"]).read_bytes()
    assert len(raw)==command["stdin"]["bytes"]and sha(raw)==command["stdin"]["sha256"]
    result=bounded_remote("replay",command["argv"],raw,command["local_timeout_seconds"])
    assert result["metadata_replay_complete"]is True
    print(json.dumps(dict(returncode=0,metadata_replay_complete=True,replay_stdout=pin(HERE/"replay-stdout.json"),
        replays=[dict(family=row["family"],original=row["original"],derived=row["derived"],
        roots=row["transport"]["root_count"],renames=row["transport"]["role_renames"])for row in result["replays"]],
        outer_postflight_still_required=True),sort_keys=True))

if __name__=="__main__":main()
