"""Local recipe contract tests, 2026-09-26 ET. No provider/host execution."""
import importlib.util
import json
from pathlib import Path
import ast
import pytest

P=Path(__file__).with_name('bfs-provider-context1-20260926.py')
spec=importlib.util.spec_from_file_location('provider_context_recipe',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_budget_does_not_reset_original_time():
    actual=m.debit(600.125)
    assert actual['cumulative_used_seconds']==m.PREVIOUS_SECONDS+600.125
    assert actual['remaining_provider_seconds']==1136.875
    assert actual['initial_floor_discarded_seconds']==1800-m.PREVIOUS_SECONDS-1737
    assert actual['repairs_used']==0 and actual['maximum_later_repairs']==2


@pytest.mark.parametrize('value',[True,None,-1,float('nan'),float('inf'),1737.1])
def test_invalid_debit_never_implies_new_allowance(value):
    with pytest.raises(ValueError):m.debit(value)


def test_public_preflight_compiles_and_is_historical_import_only():
    compile(m.PREFLIGHT,'public-preflight','exec')
    assert 'Store(Path(sys.argv[2]))' in m.PREFLIGHT
    assert 'rewrite.prompt_for' in m.PREFLIGHT and 'prompt==' in m.PREFLIGHT
    assert "_verified_lane" in m.PREFLIGHT


def test_exact_single_submit_no_repair_or_evaluation():
    tree=ast.parse(P.read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='public']
    operations=[n.args[1].value for n in calls if len(n.args)>1 and isinstance(n.args[1],ast.Constant)]
    assert operations.count('submit')==1 and set(operations)=={'get','submit'}
    assert m.BOUNDS['outer_seconds']==m.BOUNDS['work_seconds']+m.BOUNDS['cleanup_seconds']==750
    assert m.CONFIG=={'kind':'claude','command':['/data1/yanruj/.npm-global/bin/claude'],'timeout_s':600,'max_repairs':2,'total_seconds':1737,'budget_usd':10}


def test_controlled_environment_and_fixed_input_pins():
    assert {'LD_PRELOAD','LD_LIBRARY_PATH','PYTHONPATH','PYTHONHOME','PYTHONOPTIMIZE'}<=set(m.REMOVED)
    assert m.PROMPT_SHA=='6042ab21a40f270ac9f21007de8e0a2d7c55850ab1448253697c446801d07f63'
    assert m.SUP_COMMIT=='8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
    assert m.ORIGIN_COMMIT=='5f1b8028619976b36df5fa24b8aacb91bf488168'
    assert m.PUBLIC==m.SUP and m.PUBLIC_COMMIT==m.SUP_COMMIT


@pytest.fixture
def runtime(tmp_path):
    import subprocess,hashlib
    root=tmp_path/'runtime';root.mkdir()
    paths=['scripts','swdb','schemas','vocab','tools/bfs_native','tests','apps','pyproject.toml']
    for name in paths[:-1]:
        (root/name).mkdir(parents=True);(root/name/'fixture.txt').write_text('contract fixture\n')
    (root/'pyproject.toml').write_text('[project]\nname="fixture"\n')
    (root/'scripts'/'helper.py').write_text('TRACKED = True\n')
    for args in (['init','-q'],['add','.'],['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Fixture']):
        subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
    pin=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    files={str(p.relative_to(root)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
           for name in paths for p in ([root/name] if (root/name).is_file() else (root/name).rglob('*')) if p.is_file()}
    manifest={'commit':pin,'runtime_paths':paths,'root_entries':[p.name for p in root.iterdir() if p.name!='.git'],'files':files}
    return root,pin,manifest


def test_exact_git_runtime_is_accepted_without_imports(runtime):
    import time
    root,pin,manifest=runtime
    result=m.guard_runtime(root,pin,manifest,deadline=time.monotonic()+5)
    assert result['files']==manifest['files'] and result['commit']==pin


@pytest.mark.parametrize('fault',['untracked-init','ignored-root','changed-vocab','changed-test','changed-app','symlink','pycache','wrong-head'])
def test_preimport_runtime_rejects_shadow_or_changed_bytes(runtime,tmp_path,fault):
    import time
    root,pin,manifest=runtime
    if fault=='untracked-init':(root/'scripts/__init__.py').write_text('raise AssertionError("must never import")\n')
    elif fault=='ignored-root':(root/'pytest.py').write_text('SHADOW=True\n')
    elif fault=='changed-vocab':(root/'vocab/fixture.txt').write_text('changed\n')
    elif fault=='changed-test':(root/'tests/fixture.txt').write_text('changed\n')
    elif fault=='changed-app':(root/'apps/fixture.txt').write_text('changed\n')
    elif fault=='symlink':
        (root/'scripts/helper.py').unlink();(root/'scripts/helper.py').symlink_to(tmp_path/'outside.py')
    elif fault=='pycache':(root/'scripts/__pycache__').mkdir()
    elif fault=='wrong-head':pin='0'*40;manifest['commit']=pin
    with pytest.raises(ValueError):m.guard_runtime(root,pin,manifest,deadline=time.monotonic()+5)


def test_preimport_guard_obeys_original_expired_clock(runtime):
    import time
    root,pin,manifest=runtime
    with pytest.raises(ValueError,match='original work clock'):m.guard_runtime(root,pin,manifest,deadline=time.monotonic()-1)


def test_manifest_matches_fixed_git_runtime_and_wrapper_uses_isolation():
    assert m.sha(m.RUNTIME_MANIFEST)==m.RUNTIME_MANIFEST_SHA
    manifest=json.loads(m.RUNTIME_MANIFEST.read_text())
    assert manifest['commit']==m.SUP_COMMIT and manifest['root']==str(m.SUP)
    assert len(manifest['files'])==375 and 'scripts/bfs_owned_rss.py' in manifest['files']
    wrapper=P.with_name('bfs-provider-context1-launch-20260926.sh').read_text()
    assert 'python3.12 -I -B -c' in wrapper and 'wrapper_entry' in wrapper
    tree=ast.parse(P.read_text())
    # All repository imports remain function-local and after main's guard.
    assert not any(isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[0] in {'scripts','swdb'} for n in tree.body)
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    guard=next(n.lineno for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='fixed_runtime_guard')
    assert all(n.lineno>guard for n in ast.walk(main) if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('scripts'))


def test_wrapper_clock_snippets_execute_with_original_argument_positions(tmp_path):
    import subprocess,sys,shlex
    from datetime import datetime
    text=P.with_name('bfs-provider-context1-launch-20260926.sh').read_text()
    snippets=[]
    for piece in text.split("<<'PY'\n")[1:]:snippets.append(piece.split('\nPY\n',1)[0])
    commands=[line.split('/usr/bin/python3.12 ',1)[1].split(" <<'PY'",1)[0] for line in text.splitlines() if "<<'PY'" in line]
    # Only procfs is injected for this Mac contract test. Both literal shell
    # argv templates and the full clock bodies execute in real isolated Python.
    fakeproc='from pathlib import Path\n_original_read=Path.read_text\nPath.read_text=lambda p,*a,**k: ("4321 (fixture) S "+" ".join(["0"]*18+["987654"]+["0"]*4)) if str(p)=="/proc/4321/stat" else _original_read(p,*a,**k)\n'
    assert text.index('PANE_PID=$BASHPID')<text.index('readarray -t CLOCK')
    assert '$BASHPID' not in commands[0] and '$PANE_PID' in commands[0]
    first=[part.replace('$PANE_PID','4321').replace('$DISPATCH',str(tmp_path)) for part in shlex.split(commands[0])]
    result=subprocess.run([sys.executable,*first],input=fakeproc+snippets[0],text=True,capture_output=True,timeout=5)
    assert result.returncode==0,result.stderr
    rows=result.stdout.splitlines();assert len(rows)==4 and rows[2:]==['4321','987654']
    launch=json.loads((tmp_path/'launch.json').read_text())
    assert (datetime.fromisoformat(rows[1])-datetime.fromisoformat(rows[0])).total_seconds()==750
    assert launch['pane_identity']=={'pid':4321,'start_ticks':987654}
    second=[part.replace('${CLOCK[1]}',rows[1]) for part in shlex.split(commands[1])]
    result=subprocess.run([sys.executable,*second],input=snippets[1],text=True,capture_output=True,timeout=5)
    assert result.returncode==0,result.stderr
    assert 715<float(result.stdout.strip()[:-1])<=720



def test_isolated_wrapper_explicitly_disables_bytecode(tmp_path):
    import subprocess,sys,shlex,os
    text=P.with_name('bfs-provider-context1-launch-20260926.sh').read_text()
    line=next(row for row in text.splitlines() if 'python3.12' in row and '-c ' in row)
    flags=shlex.split(line.split('/usr/bin/python3.12 ',1)[1].split(' -c ',1)[0])
    (tmp_path/'bytecode_fixture.py').write_text('VALUE=123\n')
    program='import sys; sys.path.insert(0,sys.argv[1]); import bytecode_fixture; assert bytecode_fixture.VALUE==123; print(int(sys.dont_write_bytecode)); print(sys.flags.isolated)'
    result=subprocess.run([sys.executable,*flags,'-c',program,str(tmp_path)],
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=5)
    assert result.returncode==0 and result.stdout.splitlines()==['1','1']
    assert not (tmp_path/'__pycache__').exists() and not list(tmp_path.rglob('*.pyc'))
