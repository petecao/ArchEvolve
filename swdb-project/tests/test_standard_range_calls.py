"""Original-source std::copy typed range calls; created 2026-10-15 ET.

Compiler/preparation/replay seams only here; no verifier is launched.
"""
import copy
from dataclasses import replace
from pathlib import Path

import pytest

from swdb import c_lowering, wp_pointer_bounds

pytestmark=pytest.mark.skipif(bool(c_lowering.locate().missing),reason='Clang22.1.8 required')


def lower(tmp_path, body, *, params='int n', domains=None):
    path=tmp_path/'copy.cc'
    path.write_text('#include <algorithm>\nint unit('+params+') { '+body+' }\n')
    return c_lowering.lower(path,'unit',array_domains=domains,
        array_domain_contract={'id':'contract.fixture_copy','sha256':'a'*64} if domains else None)


def calls(lowering):
    return [s for s in lowering.pointer_bounds['sites'] if s.get('kind')=='standard_range_call']


def test_original_standalone_call_keeps_one_dimensional_roots_and_exact_relative_offsets(tmp_path):
    lowered=lower(tmp_path,'int a[4]={1,2,3,4}; int b[4]={0,0,0,0}; std::copy(a+1,a+3,b+1); return b[1];')
    row,=calls(lowered)
    assert row['model']=='std_copy_int' and row['reason']==''
    assert row['first']['root']==row['last']['root'] and row['destination']['root']!=row['first']['root']
    assert row['first']['elements']==row['last']['elements']=='4'
    assert row['destination']['elements']=='4'
    assert row['first']['offset']=='(0 + 1)' and row['last']['offset']=='(0 + 3)'
    assert row['destination']['offset']=='(0 + 1)'
    assert r'\base_addr' not in row['predicate'] and r'\valid' not in row['predicate']
    assert 'PTRDIFF_MAX' in row['predicate']
    generated,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    assert 'assert swdb_window_copy_' in generated
    assert 'std_copy_int(a + 1, a + 3, b + 1);' in generated


def test_explicit_window_extent_is_frozen_but_current_call_count_is_a_checked_obligation(tmp_path):
    lowered=lower(tmp_path,'n=n+1; std::copy(a,a+n,b); return 0;',params='int*a,int*b,int n',
        domains={'a':{'extent':'n'},'b':{'extent':'n'}})
    row,=calls(lowered)
    assert r'\at((integer)n,Pre)' in row['first']['elements']
    assert '((integer)n)' in row['last']['offset']
    assert row['first']['root']==row['last']['root']
    wp_pointer_bounds.prepare(lowered,lowered.text)


@pytest.mark.parametrize('body,reason',[
    ('int a[2]={1,2}; int b[2]={0,0}; std::copy(a,b+1,b); return 0;', 'same typed array'),
    ('int a[2]={1,2}; int b[2]={0,0}; int*p=a; p=b; std::copy(p,p+1,b); return 0;', 'stable'),
    ('int a[4]={1,2,3,4}; int b[4]={0,0,0,0}; int k=1; int*p=a+k; k=0; std::copy(p,p+2,b); return 0;', 'stable'),
    ('int a[2][2]={{1,2},{3,4}}; int b[3]={0,0,0}; std::copy(a[0],a[0]+3,b); return 0;', 'origin'),
    ('int a[2]={1,2}; int b[2]={0,0}; return std::copy(a,a+1,b)-b;', 'standalone'),
    ('int a[2]={1,2}; int b[2]={0,0}; std::copy(a,a+(n++),b); return 0;', 'mutation'),
])
def test_unknown_or_different_roots_and_unsafe_call_placement_are_not_certified(tmp_path,body,reason):
    lowered=lower(tmp_path,body)
    if 'n++' in body:
        assert 'single-evaluation' in calls(lowered)[0]['reason']
    with pytest.raises(wp_pointer_bounds.Refused,match=reason):
        wp_pointer_bounds.prepare(lowered,lowered.text)


def test_literal_alias_offsets_are_not_forgotten_and_distinct_shadowed_arrays_remain_distinct(tmp_path):
    lowered=lower(tmp_path,'int a[4]={1,2,3,4}; int b[4]={0,0,0,0}; int*p=a+1; std::copy(p,p+2,b); return 0;')
    row,=calls(lowered)
    assert row['first']['offset']=='(0 + 1)' and row['last']['offset']=='((0 + 1) + 2)'
    wp_pointer_bounds.prepare(lowered,lowered.text)
    shadow=lower(tmp_path,'int a[4]={1,2,3,4}; int*p=a; { int a[4]={5,6,7,8}; std::copy(p,a+1,a+2); } return 0;')
    with pytest.raises(wp_pointer_bounds.Refused,match='same typed array'):
        wp_pointer_bounds.prepare(shadow,shadow.text)


def test_prelaunch_numeric_guard_cannot_be_removed_from_an_otherwise_identical_view(tmp_path):
    lowered=lower(tmp_path,'int a[2]={1,2}; int b[2]={0,0}; std::copy(a,a+1,b); return 0;')
    generated,report=wp_pointer_bounds.prepare(lowered,lowered.text)
    changed=generated.replace('assert swdb_window_copy_', 'assert removed_copy_')
    assert changed!=generated
    with pytest.raises(wp_pointer_bounds.Refused,match='missing or duplicated'):
        wp_pointer_bounds.check_input(lowered,lowered.text,report,changed)


def test_generic_alias_policy_outside_the_exact_copy_operations_is_not_broadened(tmp_path):
    lowered=lower(tmp_path,'int a[4]={1,2,3,4}; int b[4]={0,0,0,0}; int*p=a+1; std::copy(p,p+1,b); return p[0];')
    assert calls(lowered)[0]['reason']==''
    with pytest.raises(wp_pointer_bounds.Refused,match='certified array-object origin'):
        wp_pointer_bounds.prepare(lowered,lowered.text)


def test_source_reparse_rejects_a_self_consistent_forged_destination_extent(tmp_path):
    import hashlib,json
    lowered=lower(tmp_path,'int a[2]={1,2}; int b[2]={0,0}; std::copy(a,a+2,b); return 0;')
    report=copy.deepcopy(lowered.pointer_bounds)
    row=next(r for r in report['sites'] if r.get('kind')=='standard_range_call')
    row['destination']['elements']='200'
    row['predicate']=row['predicate'].rsplit('<= (2)',1)[0]+'<= (200)'
    def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    row.pop('certificate_sha256');row['certificate_sha256']=digest(row)
    report.pop('certificate_sha256');report['certificate_sha256']=digest(report)
    forged=replace(lowered,pointer_bounds=report)
    # Hashes alone are insufficient; the generator-owned source plan is authority.
    with pytest.raises(wp_pointer_bounds.Refused,match='source closure|checked lowering'):
        wp_pointer_bounds.recheck_source(forged,{'source':str(tmp_path/'copy.cc'),'kwargs':{}})


def test_a_global_pointer_cannot_be_admitted_from_a_stale_initializer(tmp_path):
    path=tmp_path/'global.cc'
    path.write_text('#include <algorithm>\nint a[2]={1,2}; int b[2]={0,0}; int*p=a;\n'
                    'int unit(int n){p=b; std::copy(p,p+1,b);return 0;}\n')
    try:lowered=c_lowering.lower(path,'unit')
    except c_lowering.Unsupported:return  # earlier exact-source admission may refuse global pointer initializers
    with pytest.raises(wp_pointer_bounds.Refused,match='global origins|stable|origin'):
        wp_pointer_bounds.prepare(lowered,lowered.text)


def test_local_array_formation_guards_typecheck_without_implicit_acsl_decay(tmp_path):
    from swdb import framac,rss_watchdog,verifier_lock
    tool=framac.locate()
    if tool.missing:pytest.skip(tool.missing)
    lowered=lower(tmp_path,'int a[2]={1,2}; int b[2]={0,0}; std::copy(a,a+2,b); return b[0];')
    generated,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    source=tmp_path/'guard.c';source.write_text(generated)
    log=tmp_path/'parser.log'
    with verifier_lock.hold('t41 local array guard parser control'):
        result=rss_watchdog.run([*tool.command,'-machdep','x86_64',str(source),'-print'],
            log=log,cap_bytes=8589934592,timeout=60)
    assert result.exit_code==0,log.read_text()[-5000:]
