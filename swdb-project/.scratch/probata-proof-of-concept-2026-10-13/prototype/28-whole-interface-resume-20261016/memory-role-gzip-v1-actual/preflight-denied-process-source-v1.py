import datetime,hashlib,json,os,pathlib
P=pathlib.Path;rows=[]
for pid in [3261267,3952644]:
 p=P('/proc')/str(pid);row={'pid':pid,'roles':{}}
 for role in ['stat','status','cmdline','environ','cwd','exe','fd']:
  try:
   if role in ['cwd','exe']:value=os.readlink(p/role)
   elif role=='fd':value=[{'fd':x.name,'target':os.readlink(x)} for x in sorted((p/role).iterdir())]
   else:
    raw=(p/role).read_bytes();assert len(raw)<=1048576
    if role=='environ':value={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'selector_matches':[]}
    elif role=='cmdline':value=[x.decode('utf8','replace') for x in raw.split(b'\0') if x]
    elif role=='status':value='\n'.join(x for x in raw.decode().splitlines() if x.startswith(('Name:','State:','Uid:','Gid:','PPid:','TracerPid:','NSpid:')))
    else:value=raw.decode().split()[:24]
   row['roles'][role]={'readable':True,'value':value}
  except Exception as e:row['roles'][role]={'readable':False,'error_type':type(e).__name__}
 rows.append(row)
print(json.dumps({'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'scope':'Two exact permission-denied processes only; no process action or transform'},sort_keys=True))
