"""2026-10-16 ET. Plain closed-move source/contract builder."""
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1]/'fixtures/proof/lowering/vector_owned_transfer.cc'
CONTRACT = [r'requires 0 <= n;', r'assigns \nothing;',
            r'ensures \result == (n > 0 ? 7 : 0);']


def build_move(tmp_path):
    from swdb import c_lowering
    if c_lowering.locate().missing:
        pytest.skip('the selected Clang22 lowerer is unavailable')
    source = tmp_path/'vector_owned_transfer.cc'
    source.write_bytes(SOURCE.read_bytes())
    return source, c_lowering.lower(source, 'vector_owned_move_capture')
