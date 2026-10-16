"""2026-10-16 ET. Public lower/native initialized stream-input prerequisite."""
import json,subprocess
from pathlib import Path
import pytest
from conftest import run_swdb
from swdb import c_lowering,stdlib_provenance

@pytest.mark.parametrize('prefix,expected',[('7',700),('7,2',720)],ids=['one-prefix','two-prefix'])
def test_lower_native_preserves_explicit_array_prefix_and_implicit_zero_remainder(tmp_path,prefix,expected):
    tool=c_lowering.locate()
    if tool.missing:pytest.skip(tool.missing)
    source=tmp_path/'input.cc'
    source.write_text('alignas(64) unsigned int stream_input[16]={'+prefix+'};\n'
        'int observe_input() { return stream_input[0]*100+stream_input[1]*10+stream_input[15]; }\n')
    dump_command=[*tool.command,'-x','c++','-std=c++17','-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter=stream_input',str(source)]
    dumped=subprocess.run(dump_command,capture_output=True,text=True)
    (tmp_path/'source-array-ast.json').write_text(dumped.stdout)
    (tmp_path/'source-array-ast-command.json').write_text(json.dumps(dump_command,indent=2)+'\n')
    assert dumped.returncode==0,dumped.stderr
    out=tmp_path/'lowered'
    result=run_swdb('lower','--source',source,'--function','observe_input','--out',out,'--format','json')
    (tmp_path/'lower.stdout').write_text(result.stdout);(tmp_path/'lower.stderr').write_text(result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    (tmp_path/'runtime.json').write_text(json.dumps(stdlib_provenance.runtime_identity(tool),indent=2)+'\n')
    commands=[];outputs=[]
    for language,original in [('c++',source),('c',out/'observe_input.c')]:
        path=tmp_path/('run.cc' if language=='c++' else 'run.c');exe=tmp_path/('run-cxx' if language=='c++' else 'run-c')
        path.write_text(original.read_text()+'\n#include <stdio.h>\nint main(void) { printf("%d\\n",observe_input()); return 0; }\n')
        command=[*tool.command,'-x',language,'-std='+('c++17' if language=='c++' else 'c11'),'-fsanitize=address,undefined','-fno-sanitize-recover=all','-MD','-MF',str(tmp_path/(language+'.d')),str(path),'-o',str(exe)]
        commands.append(command)
        compiled=subprocess.run(command,capture_output=True,text=True)
        (tmp_path/(language+'.compile.stderr')).write_text(compiled.stderr)
        assert compiled.returncode==0,compiled.stdout+compiled.stderr
        run=subprocess.run([str(exe)],capture_output=True,text=True)
        (tmp_path/(language+'.stdout')).write_text(run.stdout);(tmp_path/(language+'.stderr')).write_text(run.stderr)
        assert run.returncode==0,run.stdout+run.stderr
        outputs.append(run.stdout)
    (tmp_path/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    assert outputs==[str(expected)+'\n']*2


@pytest.mark.parametrize('declaration',[
    'unsigned int stream_input[16]={[0]=7};',
    'unsigned int stream_input[2][4]={{7}};',
],ids=['designated','nested-filler'])
def test_lower_refuses_array_filler_shapes_outside_checked_scalar_prefix(tmp_path,declaration):
    source=tmp_path/'input.cc'
    access='stream_input[0][0]' if '[2][4]' in declaration else 'stream_input[0]'
    source.write_text(declaration+'\nint observe_input() { return '+access+'; }\n')
    result=run_swdb('lower','--source',source,'--function','observe_input','--out',tmp_path/'out','--format','json')
    (tmp_path/'lower.stdout').write_text(result.stdout);(tmp_path/'lower.stderr').write_text(result.stderr)
    assert result.returncode!=0,result.stdout+result.stderr
    assert 'array_filler' in result.stdout+result.stderr
    assert not (tmp_path/'out/observe_input.c').exists()
