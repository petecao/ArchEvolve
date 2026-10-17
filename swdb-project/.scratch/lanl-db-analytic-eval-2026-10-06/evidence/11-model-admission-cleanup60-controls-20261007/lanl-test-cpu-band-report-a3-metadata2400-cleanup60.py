import ast,copy,json,math,os,shutil,signal,subprocess,sys,tempfile,time
from pathlib import Path
from swdb import artifacts,access

def definitions(path,names):
    tree=ast.parse(Path(path).read_text())
    return ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
runner=Path('/private/tmp/lanl-cpu-band-report-a3-metadata2400-cleanup60-runner.py').read_text()
compile(runner.replace('SOURCE_VALUE',repr('/tmp/source')).replace('RAW_VALUE',repr('/tmp/raw')).replace('COMMIT_VALUE',repr('1'*40)),'report-runner','exec')
for name in ('lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py','lanl-export-cpu-band-report-a3.py'):ast.parse(Path('/private/tmp',name).read_text())
C='1'*40;target='mbit10.cpu.lanl20261006.t1.services.v1'

def seal(d):d['identity_sha256']=artifacts.digest({k:v for k,v in d.items() if k!='identity_sha256'});return d

def fixture(state):
    records={};chars={}
    for k in ('bfs','bc'):
        for g in (16,17):
            rid=k+'.kron-g'+str(g)+'.t1.characterization.objects.a1'
            chars[k,g]={'kind':'workload_characterization','id':rid,'input':'kron-g'+str(g)+'-k16','subject':{'id':'gapbs-'+k+'-baseline'},'source':{'run_arguments':['-g',str(g),'-k','16','-n','5']+(['-i','1'] if k=='bc' else [])},'binding':{'roi':'gapbs.trial_lambda.v1','threads':1}}
            records[rid]=chars[k,g]
    calibration={'kind':'cpu_service_calibration','id':'independent.mock.service','parameter':{'value':1.0}};records[calibration['id']]=calibration
    binding={'calibrations':[{'id':calibration['id'],'sha256':artifacts.digest(calibration)}],'characterization_allowlist':[{'id':r['id'],'sha256':artifacts.digest(r)} for r in chars.values()]}
    td={'kind':'target_description','id':target,'extensions':{'cpu_services_binding':binding}};records[target]=td
    protocols={};requests={};estimates=[]
    for k in ('bfs','bc'):
        settings={'mode':'estimated','estimator_version':'swdb.analytic.v1','target_description':target,'inputs':[chars[k,g]['input'] for g in (16,17)],'input_run_arguments':{chars[k,g]['input']:chars[k,g]['source']['run_arguments'] for g in (16,17)},'sources':[chars[k,16]['subject']['id']],'roi':'gapbs.trial_lambda.v1','threads':1}
        requests[k]={'message_version':'1.0','id':'lanl.cpu.'+k+'.t1.native-model.v1','version':1,'settings':settings}
        p={'kind':'protocol','id':requests[k]['id']+'.original','identity_sha256':'2'*64,'settings':{**settings,'estimator_sha256':'2'*64,'target_description':{'id':target,'sha256':artifacts.digest(td),'snapshot':td}}};records[p['id']]=p;protocols[k]={'id':p['id'],'sha256':artifacts.digest(p)}
        for g in (16,17):
            ch=chars[k,g];e={'kind':'estimate','id':'lanl.cpu.'+k+'.g'+str(g)+'.t1.estimate.v1','protocol':p['id'],'seconds':1.5 if k=='bfs' else 2.5,'regions':[{'region':'r0','bound_seconds':1.0,'missing':[]}],'subject':ch['subject'],'input':ch['input'],'characterization':ch['id'],'characterization_sha256':artifacts.digest(ch),'estimator_sha256':'2'*64,'target_description_sha256':artifacts.digest(td),'threads':1,'target':'mbit10','evidence_kind':'execution','error_band':None,'verdict':'within_error'};records[e['id']]=e;estimates.append({'id':e['id'],'sha256':artifacts.digest(e)})
    bands={}
    for k,width in (('bfs',.4),('bc',.6)):
        dev=seal({'kind':'cpu_error_band','id':'lanl.cpu.'+k+'.t1.development-band.v1','state':'development','evidence_kind':'native','width_log':width})
        records[dev['id']]=dev
        e=records['lanl.cpu.'+k+'.g17.t1.estimate.v1']
        band=seal({'kind':'cpu_error_band','id':'lanl.cpu.'+k+'.t1.heldout-band.v1','state':state,'evidence_kind':'native','width_log':width,'target_description_sha256':artifacts.digest(td),'estimator_sha256':'2'*64,'threads':1,'development_band':dev['id'],'admission':{'validated':state=='validated','missing':[] if state=='validated' else ['empirical_holdout_outside_frozen_width']},'pairs':[{'estimate':e['id'],'estimate_sha256':artifacts.digest(e),'characterization':e['characterization'],'characterization_sha256':e['characterization_sha256'],'input':e['input'],'scope':{'implementation':e['subject']['id']},'missing':[] if state=='validated' else ['empirical_holdout_outside_frozen_width']}]})
        records[band['id']]=band;bands[k]={'id':band['id'],'sha256':artifacts.digest(band),'state':state,'width_log':width}
    model=seal({'phase':'model','source_commit':C,'source_clean':True,'ready_for_development':True,'application_performance_timings_collected':False,'target_sha256':artifacts.digest(td),'calibrations':binding['calibrations'],'characterizations':binding['characterization_allowlist'],'estimates':estimates,'protocols':protocols})
    holdout=seal({'phase':'holdout','source_commit':C,'source_clean':True,'application_performance_timings_collected':True,'frozen_model_acceptance':{'identity_sha256':model['identity_sha256']},'protocols':protocols,'bands':bands})
    return records,model,holdout,requests

checks=[];exports=[]
with tempfile.TemporaryDirectory(prefix='lanl-band-report-mock-') as temp:
    root=Path(temp)
    def exercise(state,change=None,output_change=None,expect_refusal=False):
        path=root/str(len(checks));path.mkdir();M=path/'model';M.mkdir();R=path/'raw';R.mkdir();before=path/'before';before.mkdir();(R/'records').mkdir()
        records,model,holdout,requests=fixture(state)
        for k,request in requests.items():(M/(k+'-protocol-request.json')).write_text(json.dumps(request))
        def persisted(d,base):
            p=base/d['kind']/(d['id']+'.yaml');p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(d));return p
        for d in records.values():persisted(d,before)
        shutil.copytree(before,R/'records',dirs_exist_ok=True)
        calls=[]
        class FakeStore:
            def get(self,rid,kind=None):
                value=records[rid];assert kind is None or value['kind']==kind;return value
        def run(args,name,cap=2400):
            args=list(map(str,args));calls.append((name,args,cap))
            assert cap==(3600 if name.startswith('freeze-') else 2400)
            if name.startswith('freeze-'):
                request=json.loads(Path(args[4]).read_text());digest=artifacts.digest(request);k=name.split('-')[1]
                old=records[model['protocols'][k]['id']]
                d={'kind':'protocol','id':request['id']+'.'+digest[:16],'identity_sha256':digest,'settings':{**request['settings'],'estimator_sha256':old['settings']['estimator_sha256'],'target_description':old['settings']['target_description'],'cpu_error_band':{'id':holdout['bands'][k]['id'],'sha256':holdout['bands'][k]['sha256'],'snapshot':records[holdout['bands'][k]['id']]}}}
            elif name.startswith('estimate-'):
                k=name.split('-')[1];d=copy.deepcopy(records['lanl.cpu.'+k+'.g17.t1.estimate.v1']);d.update(id=args[args.index('--id')+1],protocol=args[args.index('--protocol')+1])
                b=records[holdout['bands'][k]['id']];d['error_band']={'id':b['id'],'sha256':artifacts.digest(b),'state':b['state'],'width_log':b['width_log'],'validated':state=='validated','missing':b['admission']['missing']}
                if output_change:output_change(d)
            else:raise AssertionError('unexpected command '+name)
            records[d['id']]=d;persisted(d,R/'records');return json.dumps(d)
        env={'Path':Path,'copy':copy,'json':json,'math':math,'artifacts':artifacts,'access':access,'sha':artifacts.file_hash}
        exec(compile(definitions('/private/tmp/lanl-cpu-band-report-a3-metadata2400-cleanup60-runner.py',{'sealed','check_inputs','perform_report'}),'report-functions','exec'),env)
        if change:change(records,model,holdout,M)
        try:result=env['perform_report'](FakeStore(),model,holdout,C,M,R,run)
        except AssertionError:
            if not expect_refusal:raise
            checks.append({'state':state,'refusal':True,'commands_before_refusal':len(calls)});return
        assert not expect_refusal,'unsupported change accepted'
        assert len(calls)==4 and [c[0] for c in calls]==['freeze-bfs','estimate-bfs','freeze-bc','estimate-bc']
        assert not any('collect' in a for _,args,_ in calls for a in args)
        assert result['protocols']['bfs']['id']!=result['protocols']['bc']['id']
        assert result['bands']['bfs']['width_log']==.4 and result['bands']['bc']['width_log']==.6
        assert all(r['seconds_unchanged'] and r['per_region_costs_unchanged'] and r['error_band']['validated']==(state=='validated') for r in result['reports'])
        proof=seal({'phase':'band_report','source_commit':C,'source_clean':True,'raw_transferred':False,'application_performance_timings_collected':False,'new_phase_records':4,'validation':'OK: mock records valid','frozen_model_acceptance':{'identity_sha256':model['identity_sha256']},'heldout_acceptance':{'identity_sha256':holdout['identity_sha256']},'target_sha256':model['target_sha256'],'calibrations':model['calibrations'],'characterizations':model['characterizations'],'original_estimates':model['estimates'],'prior_record_bytes_preserved':len(list(before.rglob('*.yaml'))),**result})
        exec(compile(definitions('/private/tmp/lanl-export-cpu-band-report-a3.py',{'sealed','check_inputs','inspect_export'}),'export-functions','exec'),env)
        new,preserved=env['inspect_export'](before,R/'records',proof,FakeStore(),model,holdout,C)
        assert len(new)==4 and {r['kind'] for r in new}=={'estimate','protocol'}
        exports.append({'state':state,'new_records':len(new),'prior_records_preserved':preserved})
        extra=R/'records/extra.yaml';extra.write_text(json.dumps({'id':'extra','kind':'estimate'}))
        try:env['inspect_export'](before,R/'records',proof,FakeStore(),model,holdout,C)
        except AssertionError:checks.append({'extra_export_record_refused':True})
        else:raise AssertionError('extra record exported')
        extra.unlink()
        prior_path=next((R/'records').rglob('*.yaml'));old=prior_path.read_bytes();prior_path.write_bytes(old+b'\n')
        try:env['inspect_export'](before,R/'records',proof,FakeStore(),model,holdout,C)
        except AssertionError:checks.append({'prior_bytes_tamper_refused':True})
        else:raise AssertionError('changed prior record accepted')
        prior_path.write_bytes(old)
        checks.append({'state':state,'freeze_commands':2,'estimate_commands':2,'source_argv_preserved':True,'costs_unchanged':True})
    exercise('validated');exercise('failed')
    exercise('validated',change=lambda r,m,h,p:r['independent.mock.service']['parameter'].update(value=2.0),expect_refusal=True)
    exercise('validated',change=lambda r,m,h,p:r['bfs.kron-g17.t1.characterization.objects.a1']['source'].update(run_arguments=['-g','18']),expect_refusal=True)
    exercise('validated',change=lambda r,m,h,p:r['lanl.cpu.bc.g16.t1.estimate.v1'].update(seconds=4.0),expect_refusal=True)
    exercise('validated',change=lambda r,m,h,p:r[m['protocols']['bfs']['id']]['settings'].update(threads=2),expect_refusal=True)
    exercise('validated',change=lambda r,m,h,p:h.update(source_commit='3'*40),expect_refusal=True)
    def change_width(r,m,h,p):
        b=r[h['bands']['bfs']['id']];b['width_log']=.5;seal(b);h['bands']['bfs'].update(sha256=artifacts.digest(b),width_log=.5);seal(h)
    exercise('validated',change=change_width,expect_refusal=True)
    def swapped_request(r,m,h,p):
        q=json.loads((p/'bfs-protocol-request.json').read_text());q['settings']['sources']=['gapbs-bc-baseline'];(p/'bfs-protocol-request.json').write_text(json.dumps(q))
    exercise('validated',change=swapped_request,expect_refusal=True)
    exercise('validated',output_change=lambda e:e.update(seconds=9.0),expect_refusal=True)
    exercise('validated',output_change=lambda e:e['regions'][0].update(bound_seconds=9.0),expect_refusal=True)
    exercise('failed',output_change=lambda e:e['error_band'].update(validated=True),expect_refusal=True)
    exercise('validated',output_change=lambda e:e['error_band'].update(width_log=.5),expect_refusal=True)
    # Exercise the actual session cleanup function with a small Python child, not an application/compiler.
    cleanup=definitions('/private/tmp/lanl-cpu-band-report-a3-metadata2400-cleanup60-runner.py',{'stop','run'});probe=root/'cleanup-probe.py';pidfile=root/'cleanup-child.pid'
    code="from pathlib import Path\nimport os,signal,subprocess,time\nR=W=Path("+repr(str(root))+ ")\nfrom types import SimpleNamespace\nfrom swdb.processes import stop_group\nimport json\ncleanup=SimpleNamespace(cleanup_owned=lambda:{'survivors':{}})\nchild=None;deadline=time.monotonic()+90\n"+ast.unparse(cleanup)+"\nfor sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stop)\nrun(["+repr(sys.executable)+",'-c',"+repr("import os,time;from pathlib import Path;Path("+repr(str(pidfile))+").write_text(str(os.getpid()));time.sleep(60)")+"],'cleanup',30)\n"
    probe.write_text(code);outer=subprocess.Popen([sys.executable,str(probe)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    stop_at=time.monotonic()+5
    while not pidfile.exists() and time.monotonic()<stop_at:time.sleep(.01)
    assert pidfile.exists();child_pid=int(pidfile.read_text());os.kill(outer.pid,signal.SIGTERM);outer.communicate(timeout=15)
    assert outer.returncode!=0
    try:os.kill(child_pid,0)
    except ProcessLookupError:checks.append({'sigterm_child_process_group_cleanup':True})
    else:raise AssertionError('child outlived interrupted report runner')
# Run dispatcher preflight with every external operation mocked; no host/Git/tmux operation executes.
from unittest.mock import patch
from types import SimpleNamespace
with tempfile.TemporaryDirectory(prefix='lanl-band-report-preflight-') as temp:
    base=Path(temp)
    for case in ('ready','hostname','dirty_source','held_lease','disk','wrapper','prior_exit','prior_source','load','raw_exists'):
        root=base/case;root.mkdir();paths={name:root/name for name in ('source','raw','model','heldout','memacc','leases')}
        for name in ('source','model','heldout','memacc','leases'):paths[name].mkdir()
        relative='AgenticRefiner/scripts/host/socket_lane.sh';wrapper=paths['memacc']/relative;wrapper.parent.mkdir(parents=True);wrapper.write_bytes(b'mocked lease wrapper\n')
        for name in ('model','heldout'):
            (paths[name]/'runner-exit-code.txt').write_text('0');(paths[name]/'exit-code.txt').write_text('0');(paths[name]/'acceptance.json').write_text(json.dumps({'source_commit':C}))
        for n in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):(paths['leases']/(n+'.meta.json')).write_text(json.dumps({'state':'held' if case=='held_lease' and n.endswith('node1') else 'released'}))
        if case=='prior_exit':(paths['heldout']/'exit-code.txt').write_text('1')
        if case=='prior_source':(paths['heldout']/'acceptance.json').write_text(json.dumps({'source_commit':'3'*40}))
        if case=='raw_exists':paths['raw'].mkdir()
        mapping={'/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1':str(paths['source']),'/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-band-report-20261006-a3':str(paths['raw']),'/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3':str(paths['model']),'/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-holdout-20261006-a3':str(paths['heldout']),'/data1/yanruj/Memacc-repro-20260925':str(paths['memacc']),'/data1/yanruj/lact-host-lease':str(paths['leases'])}
        class LocalPaths(ast.NodeTransformer):
            def visit_Constant(self,node):
                if isinstance(node.value,str) and node.value in mapping:return ast.copy_location(ast.Constant(mapping[node.value]),node)
                return node
        tree=ast.fix_missing_locations(LocalPaths().visit(ast.parse(Path('/private/tmp/lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py').read_text())))
        calls=[]
        def output(args,**kwargs):
            args=list(map(str,args));calls.append(args)
            if args[0]=='git':
                if 'show' in args:return b'stale wrapper' if case=='wrapper' else wrapper.read_bytes()
                if 'rev-parse' in args:return C+'\n'
                if 'status' in args:return ' M mock-owned-file\n' if case=='dirty_source' else ''
                if 'fetch' in args:return ''
            if args[0] in ('ps','tmux'):return 'mocked'
            raise AssertionError('unexpected external command '+str(args))
        def disk(path):return SimpleNamespace(f_bavail=(1 if case=='disk' else 30)*1024**3,f_frsize=1)
        env={}
        with patch.object(sys,'argv',['mock-report-dispatch',C]),patch('socket.gethostname',return_value='other-host' if case=='hostname' else 'mbit10'),patch('subprocess.check_output',side_effect=output),patch('os.statvfs',side_effect=disk),patch('os.getloadavg',return_value=(33 if case=='load' else 1,1,1)):
            try:exec(compile(tree,'preflight-mock-'+case,'exec'),env)
            except AssertionError:
                assert case!='ready';assert not any(call[0]=='tmux' for call in calls)
                checks.append({'preflight_case':case,'refused_before_mocked_tmux':True})
            else:
                assert case=='ready';assert sum(call[0]=='tmux' for call in calls)==1
                assert env['facts']['limits']=={'runner_s':18000,'outer_s':18300,'public_stage_s':2400,'protocol_freeze_s':3600,'validate_s':2400}
                assert '18300s' in env['parts'] and '9500s' not in env['parts']
                assert '--kill-after=60s' in env['parts'] and '--kill-after=20s' not in env['parts']
                checks.append({'preflight_case':case,'mocked_tmux_calls':1,'real_external_calls':0})

proof={'format':'swdb.cpu-band-report-mocked-proof.v1','scope':'Local syntax/AST and mocked protocol/report/export admission checks plus bounded Python subprocess SIGTERM cleanup. No remote calls, provider inference, compiler or application execution.','dispatcher_sha256':artifacts.file_hash(Path('/private/tmp/lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py')),'exporter_sha256':artifacts.file_hash(Path('/private/tmp/lanl-export-cpu-band-report-a3.py')),'checks':checks,'exports':exports,'controls':{'preflight_guards_mock_tested':True,'live_remote_state_verified':False,'requires_current_wrapper_and_released_owned_leases':True,'requires_other_owned_lane_idle_and_clean_same_source':True,'disk_min_bytes':{'data1':21*1024**3,'data':10*1024**3},'runner_s':18000,'outer_s':18300,'public_stage_s':2400,'protocol_freeze_s':3600,'validate_s':2400},'dispatch_executed':False}
proof['identity_sha256']=artifacts.digest(proof);Path('/private/tmp/lanl-cpu-band-report-a3-metadata2400-cleanup60-mocked-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
