"""Erased atomic operands must have no effects or unchecked RTE, 2026-10-15 ET."""
import hashlib
import json
from pathlib import Path

import pytest

from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing),reason='Clang22.1.8 required')


def test_atomic_load_cannot_erase_a_memory_order_side_effect(tmp_path):
    source = tmp_path/'atomic_order.cc'
    source.write_text('int atomic_order(int *p) {\n'
        '  int order = 0;\n'
        '  int value = __atomic_load_n(p, order++);\n'
        '  return 100 * order + value;\n}\n')
    with pytest.raises(c_lowering.Unsupported,match='atomic memory order.*line 3'):
        c_lowering.lower(source,'atomic_order')


@pytest.mark.parametrize('weak,failure',[('true','0'),('(order++, false)','0'),('false','order++')])
def test_atomic_cas_cannot_erase_weak_or_failure_order_operands(tmp_path,weak,failure):
    source = tmp_path/'atomic_cas.cc'
    source.write_text('int atomic_cas(int *p, int *e) {\n'
        '  int order = 0;\n'
        f'  bool ok = __atomic_compare_exchange_n(p,e,9,{weak},5,{failure});\n'
        '  return 100 * order + 10 * ok + *p;\n}\n')
    with pytest.raises(c_lowering.Unsupported,match=r'atomic (weak|memory order).*line 3'):
        c_lowering.lower(source,'atomic_cas')


@pytest.mark.parametrize('fence',['__atomic_thread_fence','__atomic_signal_fence'])
def test_atomic_fence_cannot_discard_its_order_expression(tmp_path,fence):
    source = tmp_path/'atomic_fence.cc'
    source.write_text('int atomic_fence() {\n  int order = 0;\n'
        f'  {fence}(order++);\n  return order;\n}}\n')
    with pytest.raises(c_lowering.Unsupported,match='atomic memory order.*line 3'):
        c_lowering.lower(source,'atomic_fence')


@pytest.mark.parametrize('expression',[
    'order', 'vorder', 'next_order()', '0 / order', '1 << order', '(order++, 0)',
    '(order = 0)', '6', '-1', '(bool)3',
])
def test_unchecked_or_invalid_memory_order_is_never_silently_erased(tmp_path,expression):
    source = tmp_path/'atomic_closed_order.cc'
    source.write_text('int next_order() { return 0; }\n'
        'int atomic_closed_order(int *p, int order, volatile int vorder) {\n'
        f'  __atomic_store_n(p,1,{expression});\n  return order;\n}}\n')
    with pytest.raises(c_lowering.Unsupported,match='atomic memory order.*line 3'):
        c_lowering.lower(source,'atomic_closed_order')


@pytest.mark.parametrize('success,failure',[
    (0,1),(0,2),(0,5),(1,2),(1,5),(2,3),(2,4),(2,5),
    (3,1),(3,2),(3,3),(3,4),(3,5),(4,3),(4,4),(4,5),(5,3),(5,4),
])
def test_cas_rejects_failure_orders_outside_the_success_order_domain(tmp_path,success,failure):
    source = tmp_path/'atomic_pair.cc'
    source.write_text('bool atomic_pair(int *p, int *e) {\n'
        f'  return __atomic_compare_exchange_n(p,e,9,false,{success},{failure});\n}}\n')
    with pytest.raises(c_lowering.Unsupported,match='atomic memory order.*line 2'):
        c_lowering.lower(source,'atomic_pair')


@pytest.mark.parametrize('success,failure',[
    (0,0),(1,0),(1,1),(2,0),(2,1),(2,2),(3,0),
    (4,0),(4,1),(4,2),(5,0),(5,1),(5,2),(5,5),
])
def test_constant_strong_cas_retains_each_legal_order_pair(tmp_path,success,failure):
    source = tmp_path/'atomic_pair.cc'
    source.write_text('bool atomic_pair(int *p, int *e) {\n'
        f'  return __atomic_compare_exchange_n(p,e,9,false,{success},{failure});\n}}\n')
    result = c_lowering.lower(source,'atomic_pair')
    assert 'swdb_atomic_compare_exchange_n_int(p, e, 9)' in result.text


@pytest.mark.parametrize('order',['__ATOMIC_SEQ_CST','(5)','(int)5','static_cast<int>(5)','order_enum'])
def test_pure_literal_or_enum_order_keeps_the_same_model(tmp_path,order):
    source = tmp_path/'atomic_constant.cc'
    source.write_text('enum Orders { order_enum = 5 };\n'
        f'int atomic_constant(int *p) {{ return __atomic_load_n(p,{order}); }}\n')
    result = c_lowering.lower(source,'atomic_constant')
    assert 'swdb_atomic_load_n_int(p)' in result.text


def test_existing_constant_atomic_fixtures_keep_exact_c_anchors_models_and_names():
    root = Path(__file__).parent/'fixtures/proof/lowering'
    baseline = json.loads((root/'atomic_constant_baseline.json').read_text())
    assert c_lowering.naming_rules()==baseline['naming_rules']
    for row in baseline['lowerings']:
        result = c_lowering.lower(root/'omp_atomics.cc',row['function'])
        assert result.sha256==row['c_sha256']
        assert hashlib.sha256(json.dumps(result.anchors,sort_keys=True).encode()).hexdigest()==row['anchors_sha256']
        assert list(result.models)==row['models']
        for model,expected in row['model_sha256'].items():
            assert hashlib.sha256(c_lowering.model_text(model).encode()).hexdigest()==expected
