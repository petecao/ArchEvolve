"""Original terminal-allocation overrun reaches its ordinary RTE goals, 2026-10-15 ET."""
from pathlib import Path
import pytest
from swdb import c_lowering, wp_pointer_bounds

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason='Clang22.1.8 required')


@pytest.mark.parametrize('unit,seeded',[('swdb_new_unit',True),('swdb_new_out_of_range',False)])
def test_original_overrun_fill_retains_exact_allocation_origin_and_invalid_write(tmp_path,unit,seeded):
    source = (Path(__file__).parent/'fixtures/proof/lowering/new_array.cc').read_text()
    if seeded:
        source = source.replace('i < n; ++i) buf[i] = k;', 'i <= n; ++i) buf[i] = k;',1)
    path = tmp_path/'new_array.cc'; path.write_text(source)
    lowered = c_lowering.lower(path,unit)
    assert lowered.terminal_release is not None
    assert lowered.terminal_release['initialization_loop_comparison'] == '<='
    wp_pointer_bounds.check(lowered)
    assert 'i <= n' in lowered.text and 'swdb_alloc_delete_array_int(buf);' in lowered.text
