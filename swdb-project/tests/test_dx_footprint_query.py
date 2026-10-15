"""Exact read-only footprint queries retain pointer-formation checks; 2026-10-15 ET."""
import pytest
from swdb import c_lowering, proof_semantics, wp_pointer_bounds
from swdb.library import Library
from conftest import REPO


def lower(tmp_path, source=None, *, library_root=None):
    source = source or '''int swdb_dx_in_footprint(int tile,const int *addr);
int unit(int *base,int n) {int member=swdb_dx_in_footprint(1,base+n);return member;}
'''
    path=tmp_path/'unit.cc';path.write_text(source)
    library=Library(library_root or REPO/'library')
    options=proof_semantics.lowering_options(library)
    options['semantics']['array_origins']=wp_pointer_bounds.semantic_origins(library)
    options['semantics']['array_call_policies']=proof_semantics.array_call_policies(library)
    options['semantics']['audited_imports']=proof_semantics.imported_call_policies(library)
    return c_lowering.lower(path,'unit',array_domains={'base':{'extent':'n'}},
        array_domain_contract='contract.fixture_query',**options)


def test_a_read_only_footprint_query_accepts_a_checked_one_past_address(tmp_path):
    lowered=lower(tmp_path)
    report=wp_pointer_bounds.check(lowered)
    text,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    assert 'swdb_dx_in_footprint' in text
    assert 'swdb_window_' in text
    assert any(row.get('kind')=='query' for row in report['sites'])


@pytest.mark.parametrize('source', [
    'int swdb_dx_in_footprint(int,const int*) { return 1; } int unit(int *base,int n){return swdb_dx_in_footprint(1,base+n);}',
    'int swdb_dx_in_footprint(int,int*); int unit(int *base,int n){return swdb_dx_in_footprint(1,base+n);}',
    'int swdb_dx_in_footprint(int,const int*); int unit(int *base,int n){int v=swdb_dx_in_footprint(n++,base+n);return v;}',
    'int swdb_dx_in_footprint(int,const int*); int unit(int *base,int n){int v=swdb_dx_in_footprint(1,base+n);base=base+1;return base[0]+v;}',
    'void add_mem_region(int,int*,int); int unit(int *base,int n){add_mem_region(1,base,n);return 1;}',
])
def test_query_names_do_not_waive_definitions_signatures_effects_or_other_pointer_calls(tmp_path,source):
    with pytest.raises((wp_pointer_bounds.Refused,c_lowering.LoweringError)):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_const_qualification_preserves_the_exact_source_pointer_formation(tmp_path):
    lowered=lower(tmp_path)
    report=wp_pointer_bounds.check(lowered)
    formed=[row for row in report['sites'] if row.get('expression') and 'base' in row['expression']]
    assert len(formed)==1
    assert '<=' in formed[0]['window_guard']
    assert formed[0]['origin']['parameter']=='base'
    assert formed[0]['origin']['elements']==r'\at((integer)n,Pre)'


def test_a_footprint_query_index_read_is_captured_once_before_address_formation(tmp_path):
    from swdb import nested_entry_reads
    source="""int swdb_dx_in_footprint(int,const int*);
int unit(int *base,int *q,int n) {int member=swdb_dx_in_footprint(1,base+q[0]);return member;}
"""
    path=tmp_path/'query.cc';path.write_text(source)
    from swdb import array_domains
    windows=array_domains.bind({'base':{'extent':'n'},'q':{'extent':'n'}},
        [('base','int *',True),('q','int *',True),('n','int',False)])
    view=nested_entry_reads.prepare(path,'unit',entry_windows=windows,scratch=tmp_path/'view')
    assert view is not None
    nested_entry_reads.check_view(path,'unit',view,entry_windows=windows)
    assert view.text.count('q[0]')==1
    assert view.text.index('= q[0]') < view.text.index('int member=')
    assert 'return member;' in view.text


@pytest.mark.parametrize('replacement',[r'assigns addr[0];',r'assigns \everything;'])
def test_a_changed_query_contract_cannot_borrow_read_only_pointer_trust(tmp_path,replacement):
    import shutil,yaml
    root=tmp_path/'library'
    shutil.copytree(REPO/'library/proof_semantics',root/'proof_semantics')
    path=root/'proof_semantics/dx100_bfs_0_1.yaml'
    data=yaml.safe_load(path.read_text())
    query=next(row for row in data['queries'] if row['query']=='swdb_dx_in_footprint')
    assert r'assigns \nothing;' in query['contract']
    query['contract']=query['contract'].replace(r'assigns \nothing;',replacement)
    path.write_text(yaml.safe_dump(data,sort_keys=False))
    with pytest.raises(wp_pointer_bounds.Refused,match='read-only'):
        wp_pointer_bounds.check(lower(tmp_path,library_root=root))


def test_a_query_capture_cannot_substitute_another_source_read(tmp_path,monkeypatch):
    from swdb import array_domains,nested_entry_reads
    path=tmp_path/'query.cc'
    path.write_text('int swdb_dx_in_footprint(int,const int*); int unit(int *p,int *q,int n) '
        '{int member=swdb_dx_in_footprint(1,p+q[0]);return member;}')
    windows=array_domains.bind({'p':{'extent':'n'},'q':{'extent':'n'}},
        [('p','int *',True),('q','int *',True),('n','int',False)])
    render=nested_entry_reads._render
    monkeypatch.setattr(nested_entry_reads,'_render',lambda raw,edits:render(raw,edits).replace('= q[0]','= p[0]'))
    with pytest.raises(nested_entry_reads.Refused,match='binding|operation'):
        nested_entry_reads.prepare(path,'unit',entry_windows=windows,scratch=tmp_path/'view')
