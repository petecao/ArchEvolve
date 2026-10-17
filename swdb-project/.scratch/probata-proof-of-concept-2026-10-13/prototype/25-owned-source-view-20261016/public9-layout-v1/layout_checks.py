# 2026-10-16 ET. Prospective C layout guards; source/Typed admission stays false.
def layout_dependencies(path, source):
    raw=path.read_bytes()
    if len(raw)>1048576 or b'\0' in raw:
        raise ValueError('bounded layout dependency file required')
    text=raw.decode().replace('\\\n',' ')
    target,separator,body=text.partition(':')
    if separator!=':' or target.strip()!='layout-object':
        raise ValueError('exact layout dependency target required')
    if any(c in body for c in (chr(92),chr(34),chr(39))):
        raise ValueError('unsupported layout dependency escaping')
    names=body.split()
    if not names or len(names)>512 or len(set(names))!=len(names):
        raise ValueError('layout dependency membership absent/duplicate/oversized')
    paths=[]
    for name in names:
        p=Path(name)
        if not p.is_absolute() or any(c in name for c in '\n\r\0$:*?[]'):
            raise ValueError('unsupported layout dependency spelling')
        paths.append(p)
    if source not in paths:
        raise ValueError('actual complete layout source missing from dependencies')
    return paths


def layout_pin(path):
    aliases=[]
    for candidate in reversed((path,*path.parents)):
        st=candidate.lstat()
        if stat.S_ISLNK(st.st_mode):
            aliases.append({'path':str(candidate),'literal_target':os.readlink(candidate)})
    physical=path.resolve(strict=True);before=physical.lstat()
    def stable(s):
        return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if not stat.S_ISREG(before.st_mode) or before.st_size>16*1024*1024:
        raise ValueError('bounded regular layout dependency required')
    fd=os.open(physical,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        if stable(os.fstat(fd))!=stable(before):raise ValueError('layout dependency open identity changed')
        h=hashlib.sha256();size=0
        while True:
            block=os.read(fd,65536)
            if not block:break
            size+=len(block)
            if size>16*1024*1024:raise ValueError('layout dependency grew past cap')
            h.update(block)
        if stable(os.fstat(fd))!=stable(before):raise ValueError('layout dependency changed during read')
    finally:os.close(fd)
    if stable(physical.lstat())!=stable(before) or path.resolve(strict=True)!=physical:
        raise ValueError('layout dependency replaced or redirected')
    if any(os.readlink(row['path'])!=row['literal_target'] for row in aliases):
        raise ValueError('layout dependency alias changed')
    return {'path':str(path),'physical':str(physical),'bytes':size,'sha256':h.hexdigest(),
            'aliases':aliases,'stable':stable(before)}


def layout_checks(inputs,manifest,expected,out,policy,remaining,rss_watchdog):
    selected=expected['layout_policy'];driver=Path(selected['driver']['path'])
    if sha(driver)!=selected['driver']['sha256']:
        raise ValueError('selected C layout driver changed')
    base=out/'layout';base.mkdir();results=[]
    for member in manifest['source_members']:
        source=inputs/member['view_path']
        if sha(source)!=member['view_sha256']:
            raise ValueError('complete original C/layout source differs')
        root=base/member['function'];root.mkdir()
        common=[str(driver),'--target='+selected['target'],'-resource-dir='+selected['resource_dir'],
                '-std=c11','-x','c','-MT','layout-object']
        phases=[];snapshots=None;dependencies=None
        for phase in ('dependencies','syntax'):
            directory=root/phase;directory.mkdir();(directory/'tmp').mkdir()
            depfile=directory/'headers.d'
            flags=['-M'] if phase=='dependencies' else ['-fsyntax-only','-MD']
            argv=[*common,*flags,'-MF',str(depfile),str(source)]
            timeout=min(selected['phase_seconds'],remaining())
            bounded_json(directory/'command.json',{'argv':argv,'cwd':str(directory),'input':pin(source),
                'phase':phase,'timeout_seconds':timeout,'compiler_only':True,'executes_generated_program':False},out,policy)
            env={**os.environ,'TMPDIR':str(directory/'tmp')}
            result=guarded_generation(argv,directory,env,policy,timeout,rss_watchdog,out)
            bounded_json(directory/'resources.json',result,out,policy);raw_bytes(out)
            if (result['exit_code']!=0 or result['timed_out'] or result['out_of_memory'] or result['output_limit']):
                raise ValueError('actual complete original C layout phase failed: '+member['function']+'/'+phase)
            current=layout_dependencies(depfile,source)
            if phase=='dependencies':
                dependencies=current;snapshots=[layout_pin(path) for path in dependencies]
                if sum(r['bytes'] for r in snapshots)>128*1024*1024:
                    raise ValueError('layout dependency aggregate cap exceeded')
            elif current!=dependencies or [layout_pin(path) for path in current]!=snapshots:
                raise ValueError('actual C syntax dependencies differ before/after use')
            phases.append({'phase':phase,'command':pin(directory/'command.json'),'resources':result,'dependency_file':pin(depfile)})
        if sha(driver)!=selected['driver']['sha256'] or sha(source)!=member['view_sha256']:
            raise ValueError('layout driver or complete source changed')
        row={'function':member['function'],'original':member['original_sha256'],'view':member['view_sha256'],
            'C_layout_assertions_passed':True,'source_contract_or_body_proven':False,'native_Cpp_ABI_claim':False,
            'phases':phases,'physical_dependencies':snapshots}
        bounded_json(root/'result.json',row,out,policy);results.append(row)
    if len(results)!=8:raise ValueError('all eight actual C layout source guards required')
    bounded_json(base/'result.json',{'checks':results,'compiler_only':True,'executes_generated_program':False,
        'scope':'Selected C model layout only; original ACSL comments are not proved by syntax acceptance. Actual source/Typed/padding/ownership/caller derivation remains pending. Declared physical dependencies checked immediately before/after syntax use; compiler/loader/between-check TCB retained.'},out,policy)
    return {'units':8,'result':pin(base/'result.json'),'C_layout_assertions_passed':True,'source_or_Typed_or_caller_admission':False}
