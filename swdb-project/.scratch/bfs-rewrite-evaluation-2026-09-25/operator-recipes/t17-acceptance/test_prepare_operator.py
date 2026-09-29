"""Synthetic command-binding controls; no host execution. Dated 2026-09-27 ET."""
import importlib.util
import json
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('t17_prepare_operator',HERE/'prepare_operator.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def rows():return json.loads((HERE/'manifest-template.json').read_text())


def bindings(row):
    # Explicit synthetic values only, never an actual T17 resource allocation.
    return dict(python='/fixture/python',runtime='/fixture/runtime',configuration='/fixture/config.json',
        runs_dir='/fixture/raw',records='/fixture/records',lane=1,workload='fixture-workload',
        protocol='fixture-protocol',primary_build=row['primary_build']['id'],diagnostic_build=row['diagnostic_build']['id'],
        total_seconds=600,checkpoint_seconds=60,run_seconds=60,diagnostic_seconds=180,memory_gib=1,
        storage_gib=1,batch_storage_gib=1,verification_ticks=1,
        owned_cleanup_ledger='/fixture/cleanup.json',owned_cleanup_binding='fixture-binding')


def test_actual_template_has_no_dispatch_or_budget():
    p=m.preview(rows());assert p['dispatch_allowed'] is False and p['execution_implemented'] is False
    assert p['aggregate_seconds'] is p['aggregate_retained_bytes'] is p['original_outer_deadline'] is None
    assert len(p['series'])==4


@pytest.mark.parametrize('index',range(4))
def test_each_fixed_series_reuses_both_builds_and_correct_treatment(index):
    row=rows()['series'][index];a=m.series_argv(row,bindings(row))
    assert '--author-binary' not in a and ('--accelerated' in a)==(row['role']=='candidate')
    assert a[a.index('--primary-build')+1]==row['primary_build']['id']
    assert a[a.index('--diagnostic-build')+1]==row['diagnostic_build']['id']
    assert a[a.index('--protocol-role')+1]==row['role']
    assert '--owned-cleanup-ledger' in a and '--owned-cleanup-binding' in a


@pytest.mark.parametrize('key',m.REQUIRED)
def test_missing_binding_never_uses_a_cli_default(key):
    row=rows()['series'][0];b=bindings(row);b[key]=None
    with pytest.raises(ValueError,match='unresolved'):m.series_argv(row,b)


@pytest.mark.parametrize('field,value',[('primary_build','replacement'),('diagnostic_build','replacement'),('lane',True),('total_seconds',43201),('python','relative')])
def test_changed_artifact_or_invalid_bound_is_rejected(field,value):
    row=rows()['series'][0];b=bindings(row);b[field]=value
    with pytest.raises(ValueError):m.series_argv(row,b)


def test_rendered_commands_parse_with_actual_public_series_cli():
    import argparse
    import ast
    root=HERE.parents[3]
    tree=ast.parse((root/'scripts/bfs_simulator_series.py').read_text())
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    parser_nodes=[];started=False
    for node in main.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='parser' for t in node.targets):started=True
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='args' for t in node.targets):break
        if started:parser_nodes.append(node)
    scope={'argparse':argparse,'Path':Path,'ROOT':root,'__doc__':'Read-only CLI contract extraction'}
    exec(compile(ast.Module(body=parser_nodes,type_ignores=[]),'actual_series_parser','exec'),scope)
    for row in rows()['series']:
        argv=m.series_argv(row,bindings(row))
        assert argv[1:3]==['-s','-B'] and argv[3].endswith('/scripts/bfs_simulator_series.py')
        args=scope['parser'].parse_args(argv[4:])
        assert args.primary_build==row['primary_build']['id'] and args.protocol_role==row['role']
        assert not args.author_binary
