"""Spelling-independent rewrite negative controls (2026-10-04 ET, ticket 62).

Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

Before ticket 62 every rewrite control was an exact-text mutation of ticket 20's
spelling, so a semantically equal rewrite written differently could not be certified.
Controls now attach to the library side:

* Library faults. Each shared control is one fault in
  ``library/dx100/faults/dxc_lowering_faults.hpp``. Certification appends that block to
  a private build copy of the candidate's canonical lowering header (whose bytes it has
  already checked) and selects the fault with one ``-DSWDB_DXC_FAULT_<ID>`` macro. The
  fault acts where the candidate calls the DX100 intrinsics, the CPU claim primitive or
  the queue push, so the candidate's text is never searched.
* Protected-line edits. ``forged_frontier`` also forges the evaluator-protected frontier
  print, whose exact text certification already requires.
* Token-matched sites. A kernel control with no library seam (BC-L1 ``stale_depth_hint``)
  matches a C++ token sequence, insensitive to whitespace, line breaks and comments.

The pass rule and the control set are unchanged; only how a control reaches its site is.
"""
from __future__ import annotations

import re
from pathlib import Path

from swdb.cli import Failure

FAULT_FILE = 'dx100/faults/dxc_lowering_faults.hpp'  # relative to the library root
LIBRARY_FAULTS = {
    'shared_context': 'SWDB_DXC_FAULT_SHARED_CONTEXT',
    'skipped_cas_recheck': 'SWDB_DXC_FAULT_SKIPPED_CAS_RECHECK',
    'dropped_continuation': 'SWDB_DXC_FAULT_DROPPED_CONTINUATION',
    'chunk_off_by_one': 'SWDB_DXC_FAULT_CHUNK_OFF_BY_ONE',
    'dropped_wait': 'SWDB_DXC_FAULT_DROPPED_WAIT',
    'read_before_wait': 'SWDB_DXC_FAULT_READ_BEFORE_WAIT',
    'index_wrap': 'SWDB_DXC_FAULT_INDEX_WRAP',
    'forged_frontier': 'SWDB_DXC_FAULT_FORGED_FRONTIER',
}
FRONTIER_PRINT = '<< queue.size() << " elements"'
FORGED_COUNTS = 'static unsigned swdb_forged_level=0; static const unsigned swdb_forged_counts[]={1,4200,17000};\n'


def fault_header(canonical, library_root):
    """The private control-build header: canonical bytes, then the fault block."""
    block = (Path(library_root) / FAULT_FILE).read_bytes()
    marker = b'\n// ---- swdb certification fault block (private build copy only) ----\n'
    return canonical + (b'' if canonical.endswith(b'\n') else b'\n') + marker + block


def forge_frontier_print(source):
    """Print the oracle's counts on the protected frontier line instead of the queue size."""
    if source.count(FRONTIER_PRINT) != 1:
        raise Failure('protected frontier print is missing or ambiguous')
    return FORGED_COUNTS + source.replace(FRONTIER_PRINT, '<< swdb_forged_counts[swdb_forged_level++] << " elements"', 1)


def library_control(source, name):
    """A control that acts at the library seam: the source (forged print only) and its fault macro."""
    if name not in LIBRARY_FAULTS:
        raise Failure('unknown rewrite control')
    mutated = forge_frontier_print(source) if name == 'forged_frontier' else source
    return {'source': mutated, 'fault': LIBRARY_FAULTS[name], 'site': 'library_fault'}


# --- token-level site matching ------------------------------------------------
_TOKEN = re.compile(r'''
    (?P<skip>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<token>[A-Za-z_]\w*|\d[\w.]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'
       |::|->|\+\+|--|<<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^]=|.)
''', re.VERBOSE | re.DOTALL)


def tokens(text):
    """[(token, start, end)] of C++ text; whitespace and comments separate tokens only."""
    found = []
    for match in _TOKEN.finditer(text):
        if match.lastgroup == 'token':
            found.append((match.group(), match.start(), match.end()))
    return found


def replace_tokens(source, before, after, name):
    """Replace the unique token-sequence occurrence of ``before`` with ``after``."""
    pattern = [t for t, _, _ in tokens(before)]
    stream = tokens(source)
    words = [t for t, _, _ in stream]
    width = len(pattern)
    hits = [i for i in range(len(words) - width + 1) if words[i:i + width] == pattern]
    if len(hits) != 1:
        raise Failure('candidate source lacks a unique negative-control mutation site: ' + name)
    start, end = stream[hits[0]][1], stream[hits[0] + width - 1][2]
    return source[:start] + after + source[end:]
