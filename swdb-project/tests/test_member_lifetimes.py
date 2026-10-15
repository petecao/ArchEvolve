"""Closed scalar-reference lifetimes beside an entry-specific array receiver.

2026-10-15 ET. Compiler/source-policy controls; no solver acceptance is implied.
"""
from pathlib import Path

import pytest

from swdb import c_lowering, wp_pointer_bounds

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')
FIXTURE = Path(__file__).parent/'fixtures/proof/lowering/classes.cc'


def lower(tmp_path, source=None):
    path=tmp_path/'classes.cc'
    path.write_text(FIXTURE.read_text() if source is None else source)
    return c_lowering.lower(path,'swdb_class_unit',array_domains={'a':{'extent':'n'}},
                            array_domain_contract='contract.fixture_classes')


def test_original_bag_counter_context_retains_constructor_destructor_and_ordinary_guards(tmp_path):
    lowered=lower(tmp_path)
    report=wp_pointer_bounds.check(lowered)
    context=report['member_windows']
    assert context['entry']=='swdb_class_unit'
    assert set(context['inline_functions'])=={'Bag_operator_index','Bag_size','Bag_scale',
        'Counter_ctor','Counter_dtor','Counter_add','bump','swdb_class_sum'}
    assert context['input_premises_added']==[]
    text,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    assert 'Counter_ctor(&counter, &total);' in text
    assert 'Counter_dtor(&counter);' in text
    assert 'bump(&total, kScale);' in text
    assert text.index('Counter_ctor(&counter, &total);') < text.index('Counter_add(&counter,') < text.index('Counter_dtor(&counter);') < text.index('bump(&total, kScale);')
    lifetime,=context['scalar_lifetimes']
    assert lifetime['object']=='counter' and lifetime['references'][0]['local']=='total'
    assert lifetime['scope'][0] < lifetime['span'][0] < lifetime['scope'][1]
    assert {(c['callee'],c['lifetime_event']) for c in context['calls'] if 'lifetime_event' in c}=={('Counter_ctor','constructor'),('Counter_dtor','destructor')}
    assert '\\initialized(&this->data)' in text and '\\initialized(&this->n)' in text
    assert 'swdb_window_access_' in text
    assert 'requires' not in text


def test_top_level_compound_array_update_keeps_a_pre_statement_window_guard(tmp_path):
    from test_member_windows import SOURCE
    source=SOURCE.replace('return data[i];','data[i] *= 2; return data[i];')
    path=tmp_path/'compound.cc';path.write_text(source)
    lowered=c_lowering.lower(path,'unit',array_domains={'a':{'extent':'n'}},
                            array_domain_contract='contract.fixture_member')
    report=wp_pointer_bounds.check(lowered)
    text,_=wp_pointer_bounds.prepare(lowered,lowered.text)
    assert report['member_windows']['input_premises_added']==[]
    assert text.index('swdb_window_access_') < text.index('this->data[i] *= 2;')


def test_explicit_destructor_cannot_duplicate_the_automatic_lifetime_edge(tmp_path):
    source=FIXTURE.read_text().replace('counter.add(bag[i]);','counter.add(bag[i]);\n    counter.~Counter();')
    with pytest.raises(c_lowering.Unsupported,match='member function ~Counter'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_scalar_reference_helper_cannot_mutate_an_entry_parameter(tmp_path):
    source=FIXTURE.read_text().replace('bump(total, kScale);','bump(mode, kScale);')
    with pytest.raises(wp_pointer_bounds.Refused,match='scalar reference'):
        wp_pointer_bounds.check(lower(tmp_path,source))


@pytest.mark.parametrize('replacement', ['n','bag.n','alias'],ids=['entry_count','receiver_count','reference_alias'])
def test_constructor_reference_cannot_alias_a_captured_extent(tmp_path,replacement):
    source=FIXTURE.read_text().replace('Counter counter(total);',f'Counter counter({replacement});')
    if replacement=='alias':source=source.replace('int total = 0;','int total = 0; int &alias=n;')
    with pytest.raises(wp_pointer_bounds.Refused,match='scalar reference'):
        wp_pointer_bounds.check(lower(tmp_path,source))


@pytest.mark.parametrize('replacement',['n','bag.n','alias'],ids=['entry_count','receiver_count','reference_alias'])
def test_helper_reference_cannot_alias_a_captured_extent(tmp_path,replacement):
    source=FIXTURE.read_text().replace('bump(total, kScale);',f'bump({replacement}, kScale);')
    if replacement=='alias':source=source.replace('int total = 0;','int total = 0; int &alias=bag.n;')
    with pytest.raises(wp_pointer_bounds.Refused,match='scalar reference|reference aliases'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_scalar_receiver_cannot_be_copied(tmp_path):
    source=FIXTURE.read_text().replace('Counter counter(total);','Counter counter(total); Counter copy(counter);')
    with pytest.raises(wp_pointer_bounds.Refused,match='one additional automatic object'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_scalar_receiver_cannot_escape_by_reference(tmp_path):
    source=FIXTURE.read_text().replace('static void bump(', 'static void escape(Counter &) {}\nstatic void bump(')
    source=source.replace('Counter counter(total);','Counter counter(total); escape(counter);')
    with pytest.raises(wp_pointer_bounds.Refused,match='nonreceiver arguments'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_scalar_reference_cannot_be_retained_from_a_short_lived_return(tmp_path):
    source=FIXTURE.read_text().replace('static void bump(', 'static int &expired() { int value=0; return value; }\nstatic void bump(')
    source=source.replace('Counter counter(total);','Counter counter(expired());')
    with pytest.raises(wp_pointer_bounds.Refused,match='scalar reference requires'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_live_scalar_receiver_scope_cannot_have_an_early_return(tmp_path):
    source=FIXTURE.read_text().replace('Counter counter(total);','Counter counter(total); if(mode==9) return 0;')
    with pytest.raises(wp_pointer_bounds.Refused,match='normal scope exit'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_closed_scalar_helpers_cannot_return_reference_aliases(tmp_path):
    source=FIXTURE.read_text().replace('static void bump(', 'static int &leak(int &value) { return value; }\nstatic void bump(')
    source=source.replace('bump(total, kScale);','int value=leak(total); bump(total, value);')
    with pytest.raises(wp_pointer_bounds.Refused,match='cannot return aliases'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_scalar_closure_does_not_waive_pointer_reference_rebinding(tmp_path):
    source=FIXTURE.read_text().replace('static void bump(', 'static void redirect(int *&p,int *other) { p=other; }\nstatic void bump(')
    source=source.replace('int *a, int n, int mode)', 'int *a, int n, int mode,int *other)')
    source=source.replace('bump(total, kScale);','redirect(a,other); bump(total, kScale);')
    with pytest.raises(wp_pointer_bounds.Refused,match='nonreceiver arguments'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_compound_update_with_a_mutating_index_stays_refused(tmp_path):
    from test_member_windows import SOURCE
    source=SOURCE.replace('return data[i];','data[i++] *= 2; return data[0];')
    path=tmp_path/'compound.cc';path.write_text(source)
    lowered=c_lowering.lower(path,'unit',array_domains={'a':{'extent':'n'}},
                            array_domain_contract='contract.fixture_member')
    with pytest.raises(wp_pointer_bounds.Refused,match='side effects/conditional|pure primitive integer'):
        wp_pointer_bounds.check(lowered)


def test_implicit_constructor_and_destructor_edges_contribute_to_complete_depth(tmp_path):
    source=FIXTURE.read_text().replace('class Counter {', 'static int step(int value) { return value+1; }\nclass Counter {')
    source=source.replace('count_(0)', 'count_(step(0))').replace('total_ += count_;','total_ += step(count_);')
    context=wp_pointer_bounds.check(lower(tmp_path,source))['member_windows']
    assert context['maximum_call_depth']==2
    assert 'step' in context['inline_functions']
    assert {(c['caller'],c['callee']) for c in context['calls'] if c['callee']=='step'}=={('Counter_ctor','step'),('Counter_dtor','step')}


def test_implicit_lifetime_edge_cannot_hide_a_deeper_call_chain(tmp_path):
    source=FIXTURE.read_text().replace('class Counter {', 'static int leaf(int value) { return value+1; }\nstatic int step(int value) { return leaf(value); }\nclass Counter {')
    source=source.replace('count_(0)', 'count_(step(0))')
    with pytest.raises(wp_pointer_bounds.Refused,match='depth'):
        wp_pointer_bounds.check(lower(tmp_path,source))


def test_compound_update_does_not_admit_a_nested_scalar_assignment(tmp_path):
    from test_member_windows import SOURCE
    source=SOURCE.replace('return data[i];','data[i] *= (i=0); return data[0];')
    path=tmp_path/'compound.cc';path.write_text(source)
    lowered=c_lowering.lower(path,'unit',array_domains={'a':{'extent':'n'}},array_domain_contract='contract.fixture_member')
    with pytest.raises(wp_pointer_bounds.Refused,match='side effects/conditional'):
        wp_pointer_bounds.check(lowered)


def test_scalar_reference_effects_cannot_change_the_referent_storage_type(tmp_path):
    source=FIXTURE.read_text().replace('total_ += count_;','reinterpret_cast<long &>(total_) += count_;')
    with pytest.raises(c_lowering.Unsupported,match='reinterpret_cast other than between pointer types'):
        wp_pointer_bounds.check(lower(tmp_path,source))
