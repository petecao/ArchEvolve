import datetime,json,os,shutil,subprocess,time
from pathlib import Path
R="5e12a9796432654d88def24ecea617d16ca605b2"
base=Path("/data1/yanruj");raw=Path("/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5")
def run(a):
 p=subprocess.run(a,capture_output=True,timeout=15,env={"PATH":"/usr/bin:/bin","LC_ALL":"C","GIT_OPTIONAL_LOCKS":"0"});assert p.returncode==0 and len(p.stdout)<=65536;return p.stdout.decode()
sources={str(p):{"head":run(["/usr/bin/git","-C",str(p),"rev-parse","HEAD"]).strip(),"status":run(["/usr/bin/git","-C",str(p),"status","--porcelain"])} for p in (base/"ArchEvolve",base/"ArchEvolve-lanl17-source-20261007-a5")}
assert all(x["head"]==R for x in sources.values()) and sources[str(base/"ArchEvolve-lanl17-source-20261007-a5")]["status"]==""
origin=run(["/usr/bin/git","-C",str(base/"ArchEvolve"),"rev-parse","origin/yanrujhou_main"]).strip();assert origin==R
leases={name:json.loads((base/"lact-host-lease"/(name+".meta.json")).read_bytes()) for name in ("mbit10-evaluation-node0","mbit10-evaluation-node1","mbit10-evaluation")};assert all(d["state"]=="released" for d in leases.values())
absent={str(raw/route/"extensa-gem5-bfs-20261006-p2"):not os.path.lexists(raw/route/"extensa-gem5-bfs-20261006-p2") for route in("attempts","campaign-runs/extensa")};assert all(absent.values())
mem={k:int(v.strip().split()[0])*1024 for k,v in (line.split(":",1) for line in Path("/proc/meminfo").read_text().splitlines()) if k=="MemAvailable"}
free={p:shutil.disk_usage(p).free for p in("/data1","/data")};assert mem["MemAvailable"]>=85899345920 and free["/data1"]>=22548578304 and free["/data"]>=25769803776
procs=run(["/usr/bin/ps","-eo","user,pid,ppid,pcpu,pmem,comm","--sort=-pcpu"]).splitlines()[:35]
mpstat=run(["/usr/bin/mpstat","-P","ALL","1","1"]) if Path("/usr/bin/mpstat").exists() else "unavailable"
gpu=run(["/usr/bin/nvidia-smi","--query-gpu=name,utilization.gpu,memory.used,memory.total","--format=csv,noheader"]) if Path("/usr/bin/nvidia-smi").exists() else "unavailable"
assert all(json.loads((base/"lact-host-lease"/(n+".meta.json")).read_bytes())==d for n,d in leases.items())
print(json.dumps({"format":"swdb.lanl17-p2-parent-pre-dispatch-readonly.v1","checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"scientific_admission":False,"source":sources,"primary_origin":origin,"leases":leases,"p2_routes_absent":absent,"mem":mem,"free_bytes":free,"load":os.getloadavg(),"processes_top35_comm_only":procs,"cpu_activity":mpstat,"gpu":gpu},sort_keys=True))
