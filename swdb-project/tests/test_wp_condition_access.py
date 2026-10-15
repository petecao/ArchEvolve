"""Ordinary window obligations at pure original control conditions (2026-10-15 ET).

Compiler/source-policy seam only unless a test explicitly invokes public prove.
No speculative guard is emitted for a conditionally unevaluated source operand.
"""
from pathlib import Path

import pytest
from swdb import c_lowering,wp_pointer_bounds

pytestmark=pytest.mark.skipif(bool(c_lowering.locate().missing),reason='Clang22.1.8 required')
FIXTURES=Path(__file__).parent/'fixtures/proof/lowering'


def checked(tmp_path,source,function='unit'):
    path=tmp_path/'condition.cc';path.write_text(source)
    lower=c_lowering.lower(path,function,array_domains={'a':{'extent':'n'}},array_domain_contract='contract.fixture_condition')
    return lower,wp_pointer_bounds.check(lower)


def test_original_openmp_fixture_pure_if_reads_have_ordinary_precondition_checks(tmp_path):
    lower,report=checked(tmp_path,(FIXTURES/'omp_atomics.cc').read_text(),'swdb_omp_unit')
    text,_=wp_pointer_bounds.prepare(lower,lower.text)
    # Clang's OpenMP captured AST repeats some source nodes; inventory may
    # retain duplicate ordinary assertions for the same exact four reads.
    assert len({tuple(r['source_statement'].values()) for r in report['sites'] if r.get('kind')=='access'})==4
    assert text.count('swdb_window_access_')>=4
    assert 'if (a[i] > 0)' in text and 'if (a[i] > maxv)' in text
    assert '\\at((integer)n,Pre)' in text
    assert 'requires' not in text


def test_if_body_mutation_occurs_after_the_checked_condition_read(tmp_path):
    source='int unit(int *a,int n,int i){ int result=0; if(a[i]>0){i=n; result=1;} return result; }'
    lower,report=checked(tmp_path,source)
    text,_=wp_pointer_bounds.prepare(lower,lower.text)
    assert text.index('swdb_window_access_') < text.index('if (a[i] > 0)') < text.index('i = n;')
    assert len([r for r in report['sites'] if r.get('kind')=='access'])==1


@pytest.mark.parametrize('source', [
    'int unit(int *a,int n){if(n>0 && a[0]>0)return 1;return 0;}',
    'int change(int &i){return i++;} int unit(int *a,int n,int i){if(a[i]>change(i))return 1;return 0;}',
    'int unit(int *a,int n,volatile int flag){if(a[0]>flag)return 1;return 0;}',
    'int unit(int *a,int n,int i){if(a[i++]>0)return 1;return 0;}',
], ids=['short_circuit','sibling_call','volatile','mutating_index'])
def test_if_condition_still_refuses_unevaluated_or_effectful_accesses(tmp_path,source):
    with pytest.raises(wp_pointer_bounds.Refused,match='side effects/conditional|pure primitive'):
        checked(tmp_path,source)


@pytest.mark.parametrize('condition',['int i=0; a[i]>0','int value=a[0]'])
def test_if_binding_is_not_read_by_a_guard_before_its_declaration(tmp_path,condition):
    source=f'int unit(int *a,int n){{if({condition})return 1;return 0;}}'
    with pytest.raises((wp_pointer_bounds.Refused,c_lowering.Unsupported),match='if|IfStmt|declaration'):
        checked(tmp_path,source)


def test_atomic_builtin_side_effect_is_not_treated_as_a_pure_condition(tmp_path):
    source='int unit(int *a,int n,int i){if(a[i]>__atomic_fetch_add(&i,1,__ATOMIC_SEQ_CST))return 1;return 0;}'
    with pytest.raises(wp_pointer_bounds.Refused,match='side effects/conditional'):
        checked(tmp_path,source)
