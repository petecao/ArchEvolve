"""2026-10-16 ET. Shared source/contract seed for the no-growth caller views."""
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'fixtures/proof/vector_reallocation_v3.cc'
CONTRACT = [r'requires 0 <= n;', r'assigns \nothing;',
            r'ensures \result == (n > 0 ? 7 : 0);']


@pytest.fixture(scope='module')
def lowered_no_growth():
    from swdb import c_lowering
    if c_lowering.locate().missing:
        pytest.skip('the selected Clang22 lowerer is unavailable')
    return SOURCE, c_lowering.lower(SOURCE, 'vector_realloc_v3_no_growth')
