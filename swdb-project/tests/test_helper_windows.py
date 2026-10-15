"""Checked contextual helper views; created 2026-10-15 ET (tickets27/36)."""
import copy
from dataclasses import replace
import hashlib
import json

import pytest

from swdb import c_lowering

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason="clang22 certifies both source ASTs")

DECLARATIONS = '''
void maa_const(int, int);
void maa_stream_load(int *, int, int, int, int, int);
void wait_ready(int);
unsigned short get_tile_size(int);
'''
HELPER = '''
void load(int *p, int n, int t) {
  maa_const(0, 0);
  maa_const(n, 1);
  maa_const(1, 2);
  maa_stream_load(p, 0, 1, 2, t, -1);
}
'''
UNIT = '''
int unit(int *q, int n) {
  load(q, n, 0);
  wait_ready(0);
  return get_tile_size(0) == n;
}
'''
IMPORTS = {name: {"id": "semantics.dx100_bfs_0_1", "sha256": "a" * 64}
           for name in ("maa_const", "maa_stream_load", "wait_ready", "get_tile_size")}


def source(tmp_path, helper=HELPER, unit=UNIT):
    path = tmp_path / "source.cc"
    path.write_text(DECLARATIONS + helper + unit)
    return path


def prepare(tmp_path, helper=HELPER, unit=UNIT):
    from swdb import helper_windows
    path = source(tmp_path, helper, unit)
    return path, helper_windows.prepare(path, "unit", imported_calls=IMPORTS, scratch=tmp_path / "scratch")


def test_transparent_clone_keeps_every_state_call_and_has_no_helper_premise(tmp_path):
    from swdb import helper_windows
    path, view = prepare(tmp_path)
    assert view is not None
    assert view.certificate["source_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert view.certificate["context_count"] == 1
    assert view.certificate["model_call_count"] == 4
    assert "requires" not in view.text and "assume" not in view.text
    assert view.assumption["kind"] == "trusted_tool"
    helper_windows.check_view(path, "unit", view, imported_calls=IMPORTS)


def test_every_branch_and_nested_helper_context_is_expanded_without_shared_formals(tmp_path):
    helper = HELPER + '\nvoid wrap(int *p, int n, int t) { load(p,n,t); }\n'
    unit = '''int unit(int *q, int *p, int n, int m) {
      if (n) { wrap(q,n,0); } else { wrap(p,m,1); }
      return 1;
    }'''
    _, view = prepare(tmp_path, helper, unit)
    assert view.certificate["context_count"] == 4
    assert view.certificate["model_call_count"] == 8
    names = [name for context in view.certificate["contexts"] for name in context["formal_names"]]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("change", ["file", "source", "certificate"])
def test_source_view_or_certificate_drift_is_rejected_by_fresh_replay(tmp_path, change):
    from swdb import helper_windows
    path, view = prepare(tmp_path)
    if change == "file":
        view.path.write_text(view.text.replace("::maa_const(0, 0)", "::maa_const(9, 0)"))
    elif change == "source":
        path.write_text(path.read_text().replace("maa_const(0, 0)", "maa_const(9, 0)"))
    else:
        certificate = copy.deepcopy(view.certificate)
        certificate["model_call_count"] = 0
        view = replace(view, certificate=certificate)
    with pytest.raises(helper_windows.Refused):
        helper_windows.check_view(path, "unit", view, imported_calls=IMPORTS)


@pytest.mark.parametrize("helper", [
    HELPER.replace("void load", "/*@ requires n >= 0; */\nvoid load"),
    HELPER.replace("maa_const(0, 0);", "int local = n; maa_const(local,0);"),
    HELPER.replace("maa_const(0, 0);", "p[0] = n;"),
    HELPER.replace("maa_const(0, 0);", "load(p,n,t);"),
    HELPER.replace("maa_const(n, 1)", "maa_const(n + 1, 1)"),
    HELPER.replace("void load", "__attribute__((noinline)) void load"),
    HELPER.replace("maa_const(0, 0);", "return;"),
])
def test_nontransparent_helper_shapes_do_not_gain_a_source_window(tmp_path, helper):
    from swdb import helper_windows
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, helper)


@pytest.mark.parametrize("argument", ["n++", "n + 1", "get_tile_size(0)"])
def test_effectful_or_unmodeled_actual_arguments_are_not_duplicated_or_hidden(tmp_path, argument):
    from swdb import helper_windows
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, unit=UNIT.replace("load(q, n, 0)", f"load(q, {argument}, 0)"))


def test_a_caller_local_cannot_capture_the_helpers_global_callee(tmp_path):
    _, view = prepare(tmp_path, unit=UNIT.replace("load(q, n, 0);", "int maa_const = 3; load(q, n, 0);") )
    assert "::maa_const" in view.text


@pytest.mark.parametrize("header,unit,reason", [
    ("int swdb_hw_0_arg_1 = 9;\n#define VALUE swdb_hw_0_arg_1\n",
     UNIT.replace("load(q, n, 0)", "load(q, VALUE, 0)"), "unmapped generated declaration"),
    ("#define swdb_hw_0_arg_0 hidden_capture\n", UNIT, "formal type, name"),
])
def test_header_hidden_names_cannot_change_capture_bindings(tmp_path, header, unit, reason):
    from swdb import helper_windows
    (tmp_path / "hidden.h").write_text(header)
    path = tmp_path / "source.cc"
    path.write_text('#include "hidden.h"\n' + DECLARATIONS + HELPER + unit)
    with pytest.raises(helper_windows.Refused, match=reason):
        helper_windows.prepare(path, "unit", imported_calls=IMPORTS, scratch=tmp_path / "scratch")


def test_an_existing_source_without_a_defined_helper_needs_no_view(tmp_path):
    from swdb import helper_windows
    path = source(tmp_path, helper="", unit=UNIT.replace("load(q, n, 0);", "maa_stream_load(q,0,1,2,0,-1);"))
    assert helper_windows.prepare(path, "unit", imported_calls=IMPORTS, scratch=tmp_path / "scratch") is None

@pytest.mark.parametrize("helper,unit", [
    (HELPER, UNIT.replace('load(q, n, 0);', 'if (n) load(q,n,0);')),
    (HELPER, UNIT.replace('load(q, n, 0);', 'for (load(q,n,0); n; --n) {}')),
    (HELPER, UNIT.replace('load(q, n, 0);', 'auto f = load; f(q,n,0); load(q,n,0);')),
    (HELPER.replace('void load(int *p, int n, int t)', 'void load(int *p, int n, int t) noexcept'), UNIT),
    (HELPER.replace('maa_const(0, 0);', 'volatile int x = n; maa_const(x,0);'), UNIT),
    (HELPER.replace('maa_const(0, 0);', '#define HW_CALL maa_const(0,0)\n HW_CALL;'), UNIT),
    (HELPER, UNIT.replace('load(q, n, 0);', 'int where = __builtin_LINE(); load(q,n,0);')),
])
def test_unchecked_contexts_or_language_semantics_remain_closed(tmp_path, helper, unit):
    from swdb import helper_windows
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, helper, unit)


def test_all_contexts_are_checked_even_when_only_the_second_one_is_invalid(tmp_path):
    from swdb import helper_windows
    unit = UNIT.replace('load(q, n, 0);', 'load(q,n,0); if (n) { load(q,n++,1); }')
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, unit=unit)


def test_declared_import_cannot_be_replaced_with_a_source_definition_or_alias(tmp_path):
    from swdb import helper_windows
    helper = 'void maa_const(int a, int b) {}\n' + HELPER
    # A source body is not the external model simply because its spelling matches.
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, helper)


def test_import_pin_and_header_changes_are_replayed(tmp_path):
    from swdb import helper_windows
    header = tmp_path / 'decls.h'
    header.write_text(DECLARATIONS)
    path = tmp_path / 'input.cc'
    path.write_text('#include "decls.h"\n' + HELPER + UNIT)
    view = helper_windows.prepare(path, 'unit', imported_calls=IMPORTS, scratch=tmp_path/'scratch')
    changed = copy.deepcopy(IMPORTS)
    changed['maa_const']['sha256'] = 'b'*64
    with pytest.raises(helper_windows.Refused):
        helper_windows.check_view(path, 'unit', view, imported_calls=changed)
    header.write_text(DECLARATIONS + '\n// changed dependency bytes\n')
    with pytest.raises(helper_windows.Refused):
        helper_windows.check_view(path, 'unit', view, imported_calls=IMPORTS)


def test_generated_scopes_preserve_other_operations_and_newline_positions(tmp_path):
    from swdb import helper_windows
    unit = UNIT.replace('load(q, n, 0);', 'int swdb_hw_0_arg_0 = 7;\n  load(\n q, n, 0);\n  n += swdb_hw_0_arg_0;')
    path, view = prepare(tmp_path, unit=unit)
    assert path.read_text().count('\n') == view.text.count('\n')
    assert view.certificate['contexts'][0]['formal_names'][0] != 'swdb_hw_0_arg_0'
    assert 'n += swdb_hw_0_arg_0;' in view.text
    helper_windows.check_view(path, 'unit', view, imported_calls=IMPORTS)


def test_independent_ast_check_rejects_a_generator_that_omits_a_model_call(tmp_path, monkeypatch):
    from swdb import helper_windows
    original = helper_windows._Plan.expand
    def broken(self, *args):
        return original(self, *args).replace('::maa_const(0, 0);', '')
    monkeypatch.setattr(helper_windows._Plan, 'expand', broken)
    with pytest.raises(helper_windows.Refused, match='operations'):
        prepare(tmp_path)


def test_macro_only_dependencies_are_pinned_even_without_ast_declarations(tmp_path):
    from swdb import helper_windows
    header = tmp_path / 'policy.h'
    header.write_text('#define UNUSED_POLICY 1\n')
    path = source(tmp_path)
    path.write_text('#include "policy.h"\n' + path.read_text())
    view = helper_windows.prepare(path, 'unit', imported_calls=IMPORTS, scratch=tmp_path/'scratch')
    header.write_text('#define UNUSED_POLICY 2\n')
    with pytest.raises(helper_windows.Refused):
        helper_windows.check_view(path, 'unit', view, imported_calls=IMPORTS)


def test_original_dx_fixture_expands_both_load_contexts_and_keeps_store_and_wait(tmp_path):
    from pathlib import Path
    from swdb import helper_windows
    path = tmp_path / 'fixture.cc'
    path.write_bytes((Path(__file__).parent / 'fixtures/proof/dx100/fixture_units.cc').read_bytes())
    imports = {**IMPORTS, 'maa_indirect_store_vector': IMPORTS['maa_const']}
    view = helper_windows.prepare(path, 'dxf_store_exit', imported_calls=imports, scratch=tmp_path/'scratch')
    assert view.certificate['context_count'] == 2
    assert view.certificate['model_call_count'] == 8
    assert 'maa_indirect_store_vector(p, 0, 3, -1, 5);' in view.text
    assert view.text.count('wait_ready(3);') == path.read_text().count('wait_ready(3);')
    helper_windows.check_view(path, 'dxf_store_exit', view, imported_calls=imports)


def test_native_call_order_and_call_value_captures_match_the_original(tmp_path):
    import subprocess
    from swdb import helper_windows
    path, view = prepare(tmp_path, unit=UNIT.replace('load(q, n, 0);', 'load(q,n,0); n=3; load(q,n,1);'))
    stub = r'''
#include <cstdio>
void maa_const(int a,int b) { std::printf("const %d %d\n",a,b); }
void maa_stream_load(int*p,int a,int b,int c,int t,int d) { std::printf("load %d %d %d %d %d %d\n",*p,a,b,c,t,d); }
void wait_ready(int t) { std::printf("wait %d\n",t); }
unsigned short get_tile_size(int t) { return 3; }
int main() { int q=17; return unit(&q,2) != 1; }
'''
    outputs = []
    for label, text in [('original',path.read_text()), ('view',view.text)]:
        source_path, binary = tmp_path/f'{label}.cc', tmp_path/label
        source_path.write_text(text + stub)
        built = subprocess.run([*c_lowering.locate().command, '-std=c++17', str(source_path), '-o', str(binary)], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        run = subprocess.run([str(binary)], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        outputs.append(run.stdout)
    expected = 'const 0 0\nconst 2 1\nconst 1 2\nload 17 0 1 2 0 -1\nconst 0 0\nconst 3 1\nconst 1 2\nload 17 0 1 2 1 -1\nwait 0\n'
    assert outputs == [expected, expected]
