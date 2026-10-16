"""2026-10-16 ET. Pure warning-reader controls; no entry/tool execution."""
import ast, os, pathlib, re
import pytest


@pytest.mark.parametrize('text,count,unknown', [
    ('Warning, file "/staged/heap_reallocation.mlw", line 25, characters 18-23: unused variable dummy\n',1,0),
    ('Warning:\n unused variable dummy\n',1,0),
    ('Warning, file "/staged/heap_reallocation.mlw", line 30, characters 1-2: suspicious assumption\n',1,1),
    ('Warning: unknown diagnostic\n',1,1),
    ('Warning,\n file "/staged/heap_reallocation.mlw", line 25, characters 18-23:\n unsupported type\n',1,1),
    ('Warning: unused variable dummy\n additional unknown continuation\n',1,1),
    ('Warning: unused variable dummy\nWarning, file "other.mlw", line 25, characters 18-23: unused variable dummy\n',2,1),
    ('warning: unrecognized lower-case format\n',1,1),
    ('',0,0),
])
def test_warning_inventory_never_silently_omits_unknown_format(text,count,unknown):
    entry=pathlib.Path(os.environ['T25_WARNING_CONTROL_ENTRY'])
    tree=ast.parse(entry.read_text())
    fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_warnings'),None)
    if fn is None:
        # Replay the retained v2 parser expression only, never its entry point.
        expression=next(n.value for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='warnings' for t in n.targets))
        records=eval(compile(ast.Expression(expression),str(entry),'eval'),{'re':re,'text':text})
        unexpected=[w for w in records if w.strip()!='Warning: unused variable dummy']
    else:
        env={'re':re}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(entry),'exec'),env)
        records,unexpected=env['parse_warnings'](text,pathlib.Path('/staged/heap_reallocation.mlw'))
    assert len(records)==count
    assert len(unexpected)==unknown
