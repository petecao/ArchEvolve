"""Each library-operation negative control stays a small edit of its operation's current header.

Created: 2026-10-05 ET (code-review fix F7; agent-decided under Yan-Ru's delegation, revisable).

The controls in ``library/library_operations/controls/`` are whole-header copies of the operation
header (``pack.hh``, ...) with one defect each; both are pinned by the entry. They are kept as copies
(not converted to patches). This test catches drift: when a header is re-pinned without re-deriving
its controls, a control would test an old body. Every control must differ from its header in a few
small hunks (bounds measured 2026-10-05: at most 3 hunks and 8 changed lines; the largest are 3 hunks,
pack aliasing_write +3, and 6 lines, gather_staging aliasing_write -1 +5).
"""
import difflib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'library'
MAX_HUNKS, MAX_CHANGED_LINES = 3, 8


def _pairs():
    rows = []
    for entry_file in sorted((LIBRARY / 'library_operations').glob('*.yaml')):
        entry = yaml.safe_load(entry_file.read_text())
        body = LIBRARY / entry['location']['path']
        for clause in entry.get('clauses') or []:
            control = clause.get('negative_control') or {}
            if 'mutation' in control:
                rows.append(pytest.param(body, LIBRARY / control['mutation']['path'],
                                         id=f"{entry['id']}:{control['id']}"))
    return rows


PAIRS = _pairs()


def test_every_seeded_operation_has_controls():
    assert len(PAIRS) == 15


@pytest.mark.parametrize('body, control', PAIRS)
def test_control_is_a_bounded_edit_of_its_header(body, control):
    diff = list(difflib.unified_diff(body.read_text().splitlines(), control.read_text().splitlines(),
                                     lineterm='', n=0))
    hunks = sum(1 for line in diff if line.startswith('@@'))
    changed = sum(1 for line in diff if line[:1] in '+-' and not line.startswith(('+++', '---')))
    assert 1 <= hunks <= MAX_HUNKS and 1 <= changed <= MAX_CHANGED_LINES, (
        f'{control.name} differs from {body.name} in {hunks} hunks and {changed} lines: re-derive the control '
        'from the current header (one defect, as before) and re-pin it')
