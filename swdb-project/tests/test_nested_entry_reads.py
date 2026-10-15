"""Independent nested-read source relation; created 2026-10-15 ET."""
from dataclasses import replace
import copy

import pytest

from swdb import c_lowering, nested_entry_reads as nested

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason="Clang22 checks source/view ASTs")
WINDOWS = {"windows": {p: {"element_type": "int", "parameter": p} for p in ("q", "base")}, "declarations_sha256": "a" * 64}
SOURCE = 'int unit(int *q,int *base,int n) { return base[q[0]] + base[q[0]]; }'


def make(tmp_path, text=SOURCE):
    source = tmp_path / 'input.cc'
    source.write_text(text)
    return source, nested.prepare(source, 'unit', entry_windows=WINDOWS, scratch=tmp_path / 'view')


def test_each_occurrence_is_captured_once_and_freshly_checked(tmp_path):
    source, view = make(tmp_path)
    assert len(view.certificate['captures']) == 2
    assert view.text.count('= q[0];') == 2
    assert source.read_text() == SOURCE
    nested.check_view(source, 'unit', view, entry_windows=WINDOWS)


def test_utf8_and_source_names_do_not_capture_generated_bindings(tmp_path):
    _, view = make(tmp_path, '// π🍎\nint swdb_nested_read_0;\n' + SOURCE)
    assert [c['name'] for c in view.certificate['captures']] == ['swdb_nested_read_1', 'swdb_nested_read_2']
    assert view.text.startswith('// π🍎\n')


@pytest.mark.parametrize('expression', ['base[q[0]++]', 'base[(int)(long)q[0]]', 'base[q[0]] && n', 'base[q[n++]]', 'base[q[0]] + f()', 'base[q[base[0]]]'])
def test_effects_conversions_conditions_and_deeper_reads_refuse(tmp_path, expression):
    try:
        _, view = make(tmp_path, 'int f(); int unit(int*q,int*base,int n){return ' + expression + ';}')
    except nested.Refused:
        return
    assert view is None  # No normalization; the ordinary gate still refuses it.


def test_volatile_input_does_not_become_an_ordinary_capture(tmp_path):
    with pytest.raises(nested.Refused):
        make(tmp_path, SOURCE.replace('int *q', 'volatile int *q'))


@pytest.mark.parametrize('change', ['source', 'view', 'certificate', 'window'])
def test_fresh_replay_rejects_drift(tmp_path, change):
    source, view = make(tmp_path)
    windows = copy.deepcopy(WINDOWS)
    if change == 'source':
        source.write_text(SOURCE.replace('q[0]', 'q[1]'))
    elif change == 'view':
        view.path.write_text(view.text.replace('= q[0]', '= q[1]'))
    elif change == 'certificate':
        certificate = copy.deepcopy(view.certificate)
        certificate['captures'][0]['name'] = 'other'
        view = replace(view, certificate=certificate)
    else:
        windows['declarations_sha256'] = 'b' * 64
    with pytest.raises(nested.Refused):
        nested.check_view(source, 'unit', view, entry_windows=windows)


@pytest.mark.parametrize('change', ['wrong_read', 'wrong_binding', 'extra_call', 'annotation'])
def test_independent_ast_check_rejects_faulty_renderer_even_with_fresh_hashes(tmp_path, monkeypatch, change):
    original = nested._render
    def broken(raw, edits):
        text = original(raw, edits)
        if change == 'wrong_read':
            return text.replace('= q[0]', '= q[1]', 1)
        if change == 'wrong_binding':
            return text.replace('base[swdb_nested_read_1]', 'base[swdb_nested_read_0]')
        if change == 'extra_call':
            return text.replace('{ int swdb_nested_read_0', '{ f(); int swdb_nested_read_0')
        return text.replace('return base', '/*@ assume \\false; */ return base')
    monkeypatch.setattr(nested, '_render', broken)
    with pytest.raises(nested.Refused):
        make(tmp_path, 'void f();\n' + SOURCE)


@pytest.mark.parametrize('dependency', ['header_body', 'global_data', 'default_argument'])
def test_complete_unit_closure_refuses_untransported_dependencies(tmp_path, dependency):
    (tmp_path / 'here.h').write_text('#define HERE __LINE__\ninline int after(){return HERE;}\n')
    if dependency == 'header_body':
        text = '#include "here.h"\n' + SOURCE.replace('return base', 'after(); return base')
    elif dependency == 'global_data':
        text = '#include "here.h"\nint global=HERE;\n' + SOURCE.replace('return base', 'int local=global; return base')
    else:
        text = 'void imported(int z=1);\n' + SOURCE.replace('return base', 'imported(); return base')
    with pytest.raises(nested.Refused):
        make(tmp_path, text)


def test_independent_relation_rejects_renderer_changes_outside_target_statements(tmp_path, monkeypatch):
    original = nested._render
    monkeypatch.setattr(nested, '_render', lambda raw, edits: original(raw, edits).replace('int unrelated=1', 'int unrelated=2'))
    with pytest.raises(nested.Refused):
        make(tmp_path, 'int unrelated=1;\n' + SOURCE)
