"""Concrete original fixture-summary negative, created 2026-10-15 ET.

This is native fixture evidence, not a solver refutation or production DX100
semantics. Both language paths execute the unchanged summary_impls.cc body.
"""
from pathlib import Path
import subprocess
import pytest
import yaml

from swdb import c_lowering
from test_wp_subset import SEEDED_BUGS, summary_id

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')
FIXTURES = Path(__file__).parent/'fixtures/proof/lowering'


def test_the_shared_dxc_seed_violates_the_original_postcondition_on_its_native_fixture_body(tmp_path):
    case = yaml.safe_load((FIXTURES.parent/'regression_corpus/fixture-dxc-seed-did-not-violate-post.yaml').read_text())['input']
    source = (FIXTURES/'summaries.cc').read_text()
    implementation = (FIXTURES/'summary_impls.cc').read_text()
    before,after = next(pair for pair in SEEDED_BUGS if '__dxc_tile_size(tile)' in pair[0])
    assert source.count(before) == 1
    assert (before, after) == (case['safe'], case['corrected_seed'])
    assert case['rejected_seed'] == 'return __dxc_tile_size(tile) + 2;'
    assert case['witness_tile'] == 0 and case['original_result_bounds'] == [1, 3]
    harness = '\n#include <stdio.h>\nint main(void) { printf("%d\\n", swdb_dxc_unit(0)); }\n'
    values = {}
    for label,text in [('safe',source),('seeded',source.replace(before,after,1))]:
        path = tmp_path/(label+'.cc'); path.write_text(text+implementation)
        lowered = c_lowering.lower(path,'swdb_dxc_unit',summaries={'__dxc_tile_size':summary_id('dxc_tile_size')})
        c_path = tmp_path/(label+'.c'); c_path.write_text(lowered.text+'\n'+implementation+harness)
        path.write_text(path.read_text()+harness)
        for language,file in [('cxx',path),('c',c_path)]:
            binary = tmp_path/(label+'-'+language)
            tool = list(c_lowering.locate().command)
            tool[0] = tool[0].replace('clang++','clang') if language=='c' else tool[0]
            done = subprocess.run([*tool,'-std=c11' if language=='c' else '-std=c++17',str(file),'-o',str(binary)],
                                  capture_output=True,text=True)
            assert done.returncode == 0,done.stderr
            output = subprocess.run([str(binary)],capture_output=True,text=True,check=True).stdout
            values[label,language] = int(output.strip())
    assert values['safe','c'] == values['safe','cxx'] == 1
    assert values['seeded','c'] == values['seeded','cxx']
    # Original requires 0<=tile<8; tile=0 is in-domain. Original post is 1<=result<=3.
    assert not 1 <= values['seeded','cxx'] <= 3,values
    assert values['seeded','cxx'] == 4
