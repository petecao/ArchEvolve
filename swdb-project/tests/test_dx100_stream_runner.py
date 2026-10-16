"""2026-10-16 ET. Public runner output isolation with explicit no-tool stand-ins."""
import os,subprocess,sys
from pathlib import Path
import pytest
from conftest import REPO

@pytest.mark.parametrize('shape',['dotdot','symlink','ancestor','disjoint'])
def test_stream_runner_resolves_disjoint_output_before_any_bootstrap_or_write(tmp_path,shape):
    source=tmp_path/'source';(source/'swdb-project').mkdir(parents=True)
    tools=tmp_path/'standins';tools.mkdir()
    git=tools/'git';git.write_text('#!/bin/sh\ncase "$*" in\n"rev-parse HEAD") printf "%s\\n" "$FIXTURE_SHA" ;;\n"status --porcelain") exit 0 ;;\n"rev-parse --show-toplevel") printf "%s\\n" "$FIXTURE_SOURCE" ;;\n*) exit 7 ;;\nesac\n');git.chmod(0o755)
    python=tools/'bootstrap-python'
    python.write_text('#!'+sys.executable+'\nimport os,sys\nfrom pathlib import Path\n'
        'if len(sys.argv)>2 and sys.argv[1]=="-c":\n'
        '    program=sys.argv[2];sys.argv=[sys.argv[0],*sys.argv[3:]]\n'
        '    exec(compile(program,"runner-output-guard","exec"))\n'
        'else:\n    Path(os.environ["FIXTURE_MARKER"]).touch();sys.exit(99)\n')
    # Execute the runner's actual resolver code, never a replacement predicate.
    # Bootstrap, collection and tool work remain an explicit exit99 stand-in.
    python.chmod(0o755);marker=tmp_path/'bootstrap-ran'
    if shape=='dotdot':
        (tmp_path/'detour').mkdir();output=tmp_path/'detour/../source/nested'
    elif shape=='symlink':
        alias=tmp_path/'alias';alias.symlink_to(source,target_is_directory=True);output=alias/'nested'
    elif shape=='ancestor':output=tmp_path
    else:output=tmp_path/'raw'
    runner=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics/run_stream_acceptance.sh'
    command=['bash',str(runner),'a'*40,'positive']
    result=subprocess.run(command,capture_output=True,text=True,env={**os.environ,'PATH':str(tools)+os.pathsep+os.environ['PATH'],
        'FIXTURE_SOURCE':str(source),'FIXTURE_SHA':'a'*40,'PROBATA_OUTPUT':str(output),'PROBATA_PYTHON':str(python),
        'FIXTURE_MARKER':str(marker)})
    (tmp_path/'runner.stdout').write_text(result.stdout);(tmp_path/'runner.stderr').write_text(result.stderr)
    if shape=='disjoint':
        assert result.returncode==99 and marker.exists(),result.stdout+result.stderr
        assert (output/'tmp').is_dir() and (output/'cache').is_dir()
    else:
        assert result.returncode==2,result.stdout+result.stderr
        assert not marker.exists()
        assert not (output/'tmp').exists() and not (output/'cache').exists()
