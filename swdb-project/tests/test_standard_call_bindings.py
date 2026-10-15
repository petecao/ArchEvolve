"""Original-TU callee identity controls; created 2026-10-15 ET.

A same-name/same-type project extern is not the instantiated standard template.
All calls deliberately share one line, so line matching cannot certify a substitute.
These are compiler and stand-in public controls, never solver success claims.
"""
import pytest
from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang 22.1.8 required')
CASES = {
    'min': ('const int &min(const int &,const int &);', 'int a=1,b=2; std::min(a,b); return project::min(a,b);'),
    'max': ('const int &max(const int &,const int &);', 'int a=1,b=2; std::max(a,b); return project::max(a,b);'),
    'swap': ('using std::__swap_result_t; using std::is_nothrow_move_constructible; using std::is_nothrow_move_assignable; __swap_result_t<int> swap(int &,int &) noexcept(is_nothrow_move_constructible<int>::value && is_nothrow_move_assignable<int>::value);', 'int a=1,b=2; std::swap(a,b); project::swap(a,b); return a;'),
    'copy': ('int *copy(int *,int *,int *);', 'int a[1]={7}; int b[1]={0}; std::copy(a,a+1,b); project::copy(a,a+1,b); return b[0];'),
}


def source(name):
    declaration, body = CASES[name]
    return '#include <algorithm>\nnamespace project { '+declaration+' }\nint unit(int n) { '+body+' }\n'


@pytest.mark.parametrize('name', CASES)
def test_same_line_project_extern_is_not_a_standard_model_binding(tmp_path, name):
    path = tmp_path/'unit.cc'; path.write_text(source(name))
    lowered = c_lowering.lower(path,'unit')
    report = lowered.stdlib_provenance
    assert report['verdict']=='refused', report
    assert 'original callee differs' in report['reason'], report
    pairs = report['substitutions']
    assert len(pairs)==2
    assert pairs[0]['requested']['mangled']==pairs[0]['actual']['mangled']
    assert pairs[1]['requested']['mangled']!=pairs[1]['actual']['mangled']
    assert pairs[0]['call_range']!=pairs[1]['call_range']
    assert all(p['cursor_kind']=='CallExpr' for p in pairs)


@pytest.mark.parametrize('adapter', ['cbmc','crux-llvm-c','crux-llvm-cxx','bounded'])
def test_public_consumers_refuse_misbound_original_callee_before_dependencies_or_launch(tmp_path,monkeypatch,adapter):
    import test_bounded_standard_header_provenance as public
    monkeypatch.setattr(public,'SOURCE',source('copy'))
    record,marker=public._prove(tmp_path,adapter,shadow=False)
    provenance=record['settings']['stdlib_provenance']
    assert provenance['verdict']=='refused' and 'original callee differs' in provenance['reason'], provenance
    assert record['failure_class']=='unsupported_construct' and record['settings']['verifier_launched'] is False
    assert not marker.exists()
    assert not any(r['name'].startswith(('differential_', 'crux_input', 'cbmc_input','wp_log')) for r in record['evidence']['reports'])


@pytest.mark.parametrize('name', CASES)
def test_canonical_same_line_calls_keep_two_distinct_exact_source_bindings(tmp_path,name):
    path=tmp_path/'unit.cc'; path.write_text(source(name).replace('project::'+name,'std::'+name))
    lowered=c_lowering.lower(path,'unit')
    report=lowered.stdlib_provenance
    assert report['verdict']=='passed', report
    pairs=report['substitutions']
    assert len(pairs)==2 and pairs[0]['call_range']!=pairs[1]['call_range']
    assert all(p['requested']==p['actual'] for p in pairs)
    assert list(lowered.stdlib_substitutions)==report['substitution_requests']


def test_a_dropped_printer_call_request_refuses_at_public_admission_seam(tmp_path):
    from dataclasses import replace
    from swdb import stdlib_source_admission
    path=tmp_path/'unit.cc';path.write_text(source('copy').replace('project::copy','std::copy'))
    lowered=c_lowering.lower(path,'unit')
    forged=replace(lowered,stdlib_substitutions=lowered.stdlib_substitutions[:-1])
    reason=stdlib_source_admission.bind({},forged,path)
    assert 'exact call requests' in reason


def test_a_changed_printer_call_request_is_refused_before_fresh_parser_launch(tmp_path):
    from dataclasses import replace
    from swdb import stdlib_source_admission
    path=tmp_path/'unit.cc';path.write_text(source('copy').replace('project::copy','std::copy'))
    lowered=c_lowering.lower(path,'unit')
    context={}
    assert stdlib_source_admission.bind(context,lowered,path) is None
    context['stdlib_sources']['unit']['lowering']=replace(lowered,stdlib_substitutions=())
    with pytest.raises(stdlib_source_admission.Refused,match='requests changed'):
        stdlib_source_admission.recheck(context,lowered)
