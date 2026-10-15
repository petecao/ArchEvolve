"""Contextual member array windows through the public C++ lowering seam.

Compiler/prelaunch controls only; ordinary WP validity/init/numeric obligations
remain required, and an arbitrary receiver never receives this certificate.
"""
import pytest
from swdb import c_lowering, wp_pointer_bounds

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')
SOURCE = '''struct Buffer { int *data; int n; int get(int i) const { return data[i]; } };
int unit(int *a,int n) { Buffer b; b.data=a; b.n=n; return b.get(0); }
'''


def lower(tmp_path, source=SOURCE, domains=True):
    path=tmp_path/'unit.cc';path.write_text(source)
    return c_lowering.lower(path,'unit',array_domains={'a':{'extent':'n'}} if domains else None,
                            array_domain_contract='contract.fixture_member' if domains else None)


def test_one_receiver_captures_entry_window_without_assuming_validity_or_initialization(tmp_path):
    lowered=lower(tmp_path)
    report=wp_pointer_bounds.check(lowered)
    context=report['member_windows']
    assert context['entry']=='unit' and context['inline_functions']==['Buffer_get']
    assert context['input_premises_added']==[]
    text,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    assert 'this->data[i]' in text
    assert '\\initialized(&this->data)' in text and '\\initialized(&this->n)' in text
    assert '((integer)this->n)' in text and 'swdb_window_access_' in text
    assert 'requires' not in text


@pytest.mark.parametrize('change', [
    lambda s:s.replace('b.n=n;', 'b.n=n; b.n=100;'),
    lambda s:s.replace('b.data=a;', 'b.data=a; b.data=a+1;'),
    lambda s:s.replace('Buffer b;', 'n=100; Buffer b;'),
    lambda s:s.replace('return b.get(0);', 'Buffer c; c.data=a; c.n=n; return c.get(0);'),
    lambda s:s.replace('return b.get(0);', 'Buffer c=b; return c.get(0);'),
    lambda s:s.replace('int unit(', 'void escape(Buffer &b) {} int unit(').replace('return b.get(0);','escape(b); return b.get(0);'),
    lambda s:s.replace('return data[i];','n=100; return data[i];').replace(' const {',' {'),
    lambda s:s.replace('return data[i];','int *p=data; return p[i];'),
    lambda s:s.replace('return data[i];','return i ? get(i-1) : data[0];'),
])
def test_other_receiver_mutation_alias_escape_and_recursive_context_refuse(tmp_path,change):
    with pytest.raises(wp_pointer_bounds.Refused):
        wp_pointer_bounds.check(lower(tmp_path,change(SOURCE)))


def test_validity_cannot_replace_an_explicit_member_window(tmp_path):
    with pytest.raises(wp_pointer_bounds.Refused,match='certified array-object origin'):
        wp_pointer_bounds.check(lower(tmp_path,domains=False))


def test_an_arbitrary_reference_entry_does_not_gain_a_contextual_window(tmp_path):
    source=SOURCE.replace('int unit(int *a,int n) { Buffer b; b.data=a; b.n=n; return b.get(0); }',
                          'int unit(Buffer &b,int n) { return b.get(0); }')
    path=tmp_path/'unit.cc';path.write_text(source)
    lowered=c_lowering.lower(path,'unit')
    with pytest.raises(wp_pointer_bounds.Refused,match='certified array-object origin'):
        wp_pointer_bounds.check(lowered)


def test_context_cannot_change_entry_or_inline_selection_at_launch(tmp_path):
    from swdb import member_windows
    lowered=lower(tmp_path)
    policy={'certificate':lowered.pointer_bounds['member_windows'], 'entry':'unit', 'inline_functions':['Buffer_get']}
    flags=['-wp-fct=unit','-inline-calls=Buffer_get']
    command=['frama-c','-inline-calls=Buffer_get','input.c','-then',*flags,'-then','-report']
    assert member_windows.check_launch(lowered,policy,flags,command)==policy
    for bad in [[],['-wp-fct=Buffer_get','-inline-calls=Buffer_get'],
                [*flags,'-wp-fct=Buffer_get'],['-wp-fct=unit'],
                [*flags,'-inline-calls=other'],[*flags,'-wp-skip-fct=unit']]:
        with pytest.raises(member_windows.Refused,match='context'):
            member_windows.check_launch(lowered,policy,bad,command)
    for bad in [command[2:],command+['-wp-fct=Buffer_get'],
                ['frama-c','input.c','-then',*flags,'-then','-report']]:
        with pytest.raises(member_windows.Refused,match='context'):
            member_windows.check_launch(lowered,policy,flags,bad)


def public_seed(tmp_path, source=SOURCE):
    import hashlib
    import shutil
    import yaml
    from conftest import FIXTURES,make_records
    from test_formal_frame import frame_contract,write_library
    from test_wp_adapter import method_version
    records=make_records(tmp_path)
    library=tmp_path/'library';methods=library/'methods';methods.mkdir(parents=True)
    shutil.copy(FIXTURES/'proof/methods/contract-fixture-1.yaml',methods)
    method=method_version(c_lowering.identity())
    (methods/'wp-tracer-fixture.yaml').write_text(yaml.safe_dump(method,sort_keys=False))
    entry=frame_contract('contract.fixture_member',role='enabling',
        concurrency_frame=[{'array':'a','shared_actions':[],'history_reads':False}],
        clauses=[{'id':'member','role':'postcondition','statement':'The contextual read retains its original input value.',
          'discharge_mode':'runtime_guard','negative_control':{'id':'member-control','check':'fixture'},
          'acsl':{'text':r'requires 1 <= n <= 4; requires \valid(a+(0..n-1)); requires \initialized(a+(0..n-1)); assigns \nothing; ensures \result == a[0];','uses':[]},
          'proof_placement':{'once':'self'}}])
    entry['proof_unit']={'function':'unit','source':{'root':'library','path':'proof_units/unit.cc',
        'sha256':hashlib.sha256(source.encode()).hexdigest()},'array_domains':{'a':{'extent':'n'}}}
    write_library(library,{'proof_units/unit.cc':source,'rewrite_contracts/member.yaml':entry})
    return records,method


def test_public_wp_reaches_execution_with_exact_context_and_preserved_source_guards(tmp_path):
    import json
    import yaml
    from conftest import run_swdb
    from test_wp_adapter import fake
    records,method=public_seed(tmp_path)
    done=run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
          '--runs-dir',tmp_path/'runs','--summary','contract.fixture_member','--format','json',env=fake('unknown'))
    assert done.returncode==0,done.stdout+done.stderr
    row=yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['failure_class']=='unknown',row
    assert row['settings']['member_windows']['inline_functions']==['Buffer_get']
    assert row['proof_setup_check']['verdict']=='passed'
    assert '-wp-fct=unit' in row['settings']['flags']
    assert '-wp-no-filter-init' in row['settings']['flags']


def test_reference_helper_cannot_rebind_an_entry_window_behind_a_checked_call(tmp_path):
    source=SOURCE.replace('int unit(', 'void redirect(int *&p,int *other) { p=other; }\nint unit(')
    source=source.replace('int *a,int n)', 'int *a,int n,int *other)')
    source=source.replace('return b.get(0);','redirect(a,other); int value=b.get(0); return a[1]+value;')
    lowered=lower(tmp_path,source)
    with pytest.raises(wp_pointer_bounds.Refused,match='nonreceiver|pointer call|stable primitive'):
        wp_pointer_bounds.check(lowered)


def test_standalone_model_keeps_its_existing_nonmember_launch_path(tmp_path):
    import json
    import yaml
    from conftest import run_swdb
    from test_wp_adapter import fake
    records,method=public_seed(tmp_path)
    done=run_swdb('prove','--records',records.path,'--adapter','wp','--method-version',method['id'],
          '--runs-dir',tmp_path/'runs','--model','std_min_int','--format','json',env=fake('unknown'))
    assert done.returncode==0,done.stdout+done.stderr
    row=yaml.safe_load((records.path/json.loads(done.stdout)['path']).read_text())
    assert row['failure_class']=='unknown',row
    assert 'member_windows' not in row['settings']
    assert row['proof_setup_check']['verdict']=='passed'


def test_two_level_direct_receiver_chain_preserves_exact_context(tmp_path):
    source=SOURCE.replace('int get(int i) const { return data[i]; }',
        'int helper(int i) const { return data[i]; } int get(int i) const { return helper(i); }')
    row=wp_pointer_bounds.check(lower(tmp_path,source))
    assert row['member_windows']['inline_functions']==['Buffer_get','Buffer_helper']


def test_deeper_than_independently_demonstrated_inline_depth_refuses(tmp_path):
    source=SOURCE.replace('int get(int i) const { return data[i]; }',
        'int leaf(int i) const { return data[i]; } int helper(int i) const { return leaf(i); } int get(int i) const { return helper(i); }')
    with pytest.raises(wp_pointer_bounds.Refused,match='depth'):
        wp_pointer_bounds.check(lower(tmp_path,source))


@pytest.mark.parametrize('tamper',['entry','inline','source','certificate','policy_file','policy_settings'])
def test_public_prelaunch_refuses_changed_receiver_source_context_or_inlining(tmp_path,tamper):
    import os
    import subprocess
    import sys
    from conftest import REPO
    from test_wp_adapter import fake
    records,method=public_seed(tmp_path)
    script='''from pathlib import Path
from swdb import proof,wp_adapter,proof_setup
from swdb.cli import main
original=wp_adapter.WpAdapter._wp
def fault(self,job,path,context):
    if TARGET=='entry':
        context['extra_flags']=['-wp-fct=Buffer_get','-inline-calls=Buffer_get']
    elif TARGET=='inline':
        context['extra_flags']=['-wp-fct=unit']
    elif TARGET=='source':
        source=Path(context['pointer_source_plan']['source'])
        source.write_text(source.read_text().replace('b.n=n;','b.n=n+1;'))
    elif TARGET=='certificate':
        context['lowering'].pointer_bounds['member_windows']['entry']='other'
    return original(self,job,path,context)
wp_adapter.WpAdapter._wp=fault
checked=proof_setup.check_generated
def changed(job,adapter,context,inputs,flags,**kwargs):
    if TARGET=='policy_file':
        for path,_ in inputs:
            if Path(path).name=='member-window-context.json':Path(path).write_text('{}\\n')
    elif TARGET=='policy_settings':
        context['settings']['member_windows']['entry']='other'
    return checked(job,adapter,context,inputs,flags,**kwargs)
proof_setup.check_generated=changed
raise SystemExit(main())
'''.replace('TARGET',repr(tamper))
    done=subprocess.run([sys.executable,'-c',script,'prove','--records',str(records.path),
        '--adapter','wp','--method-version',method['id'],'--runs-dir',str(tmp_path/'runs'),
        '--summary','contract.fixture_member','--format','json'],cwd=REPO,
        env={**os.environ,**fake('unknown')},text=True,capture_output=True,timeout=600)
    assert done.returncode==1,done.stdout+done.stderr
    assert 'proof setup check' in done.stderr,done.stderr
    if tamper in {'entry','inline','policy_settings'}:
        assert '[member_windows]' in done.stderr,done.stderr
    assert not list(records.path.glob('proofs/*.yaml'))
