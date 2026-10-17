"""Knob and schedule legality checks for candidate certification (ticket 68).

Created: 2026-10-04 ET. Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

Both promoted DX100 contracts name two checks that no certification run reported before:
clause `frontier_threshold` names `knob_range`, and clause `schedule` names `schedule_range`.
The contract text is unchanged. This module makes both names real, evaluator-owned checks:

* ``knob_range``: every knob the contract declares (``knobs[].range``) is read from the
  candidate's knob assignment, the macro ``SWDB_KNOB_<NAME>`` that Extensa campaigns define (the
  rewrite prompt's knob interface). The value comes from the preprocessor, at the end of the
  candidate's translation unit and at the build's tile size. It must be an integer constant inside
  ``min``/``max`` (and ``upper_bound: build.tile_size``), or one of ``choices``. A knob the
  candidate does not expose keeps the contract default and is recorded as such.
* ``schedule_range``: structural, as clause `schedule`'s discharge mode says. Every OpenMP
  worksharing-loop ``schedule`` clause in the candidate's own translation unit, after
  preprocessing (macros and ``_Pragma`` resolved, inactive code removed), must name a kind from the
  `schedule` knob's choices. Any chunk it gives must be an integer constant inside the
  `schedule_granularity` range. A loop without a schedule clause uses the implementation default
  (static), which is in range.

Both checks are evaluator-owned and run on the preprocessed private build copy before the build.
A control is rejected by the named check, never by a build failure. For example, a candidate's own
``static_assert`` on a knob may also stop the build; the control is still rejected by
``knob_range``, and the build failure is only recorded.

Negative controls (certifier-owned, one per check):

* ``knob_out_of_range``: the knob assignment of the knob whose legality clause names
  ``knob_range`` is set one below its minimum. It goes through the campaign knob block if the source
  has one, otherwise through a new block at the top of the source.
* ``schedule_out_of_range``: every ``#pragma omp ... for`` line of the candidate's source gets
  ``schedule(guided)``. An existing clause is replaced; otherwise the clause is appended. Guided is
  a valid OpenMP schedule, so the run stays correct, and only ``schedule_range`` can reject it.

The contract's own clause controls for these checks (`chunk_off_by_one` -> `knob_range`,
`shared_context` -> `schedule_range`) never change a knob assignment or a schedule clause, so they
cannot exercise these checks. ``swdb.certification.clause_controls`` records those two pairs as not
enforceable (reason ``control_cannot_exercise_check``) and enforces each clause through the
certifier's control above. The pairing in the contract is a wording issue left to Yan-Ru.

Updated: 2026-10-05 ET (code-review fixes C4, C24; rules ``v2``, certify 1.6; agent-decided under
Yan-Ru's delegation, revisable). Rules ``v1`` (certify 1.3-1.5) probed only ``SWDB_KNOB_<NAME>``. The
promoted DX100 patches (ticket 20, ticket 42) spell their knobs ``SWDB_FRONTIER_THRESHOLD`` and
``SWDB_CHUNK_SIZE``, so v1 recorded ``contract_default`` (64) for them whatever the patch assigned: a
threshold of 0 passed. Rules v2:

* every declared spelling of a knob (:func:`knob_spellings`: ``SWDB_KNOB_<NAME>`` and ``SWDB_<NAME>``) is
  probed, and the value comes from the spellings the candidate's code uses (a spelling that appears
  only in its own ``#ifndef``/``#define``/``#undef`` is not used);
* a knob whose spellings the candidate does not use is recorded ``unverified`` (never the contract
  default); for the knob whose clause names ``knob_range`` that fails the check, since nothing else
  discharges the clause;
* used spellings with different values fail the check;
* ``knob_out_of_range`` sets every spelling the candidate uses (the ``SWDB_KNOB_<NAME>`` spelling when
  it uses none), so the control changes the value the candidate actually reads;
* ``schedule_out_of_range`` also mutates ``_Pragma("omp ... for ...")`` operators; a candidate that
  writes its worksharing loops only with ``_Pragma`` no longer aborts the certification.
"""
from __future__ import annotations

import re

from swdb.cli import Failure
from swdb.certification_common import CandidateFailure

KNOB_RANGE = 'knob_range'
SCHEDULE_RANGE = 'schedule_range'
CHECKS = (KNOB_RANGE, SCHEDULE_RANGE)
# Certifier-owned negative control -> the named checks that reject it.
CONTROLS = {'knob_out_of_range': {KNOB_RANGE}, 'schedule_out_of_range': {SCHEDULE_RANGE}}
# Which certifier control exercises each check (used by clause_controls).
CHECK_CONTROL = {KNOB_RANGE: 'knob_out_of_range', SCHEDULE_RANGE: 'schedule_out_of_range'}
KNOB_BLOCK = '// swdb campaign knob values for workload class'
CONTROL_BLOCK = '// swdb certification control knob_out_of_range (evaluator-owned)'
PROBE = 'swdb_knob_probe_begin {name} ( {macro} ) swdb_knob_probe_end'
_PROBE = re.compile(r'swdb_knob_probe_begin (\w+) \((.*?)\) swdb_knob_probe_end', re.DOTALL)
# Rules v2 (certify 1.6): one probe per declared spelling, labeled by its position (never by the
# spelling itself, which the preprocessor would expand).
PROBE_V2 = 'swdb_knob_probe_begin {name} swdb_knob_spelling_{index} ( {macro} ) swdb_knob_probe_end'
_PROBE_V2 = re.compile(r'swdb_knob_probe_begin (\w+) swdb_knob_spelling_(\d+) \((.*?)\) swdb_knob_probe_end',
                       re.DOTALL)
RULES = ('v1', 'v2')
SCHEDULE_KINDS_MODIFIERS = {'monotonic', 'nonmonotonic', 'simd'}
_DIRECTIVE_WORDS = {'parallel', 'for', 'simd', 'distribute', 'teams', 'target', 'taskloop', 'loop'}


def knob_macro(name):
    """The campaign knob interface: `SWDB_KNOB_<NAME IN UPPER CASE>` (swdb.campaign_targets)."""
    return 'SWDB_KNOB_' + re.sub(r'[^A-Za-z0-9_]', '_', str(name)).upper()


def knob_spellings(name):
    """The declared spellings of a contract knob: the campaign interface ``SWDB_KNOB_<NAME>`` and the
    short form ``SWDB_<NAME>`` that the promoted DX100 patches use (Peter v1.1 section 5)."""
    macro = knob_macro(name)
    return (macro, 'SWDB_' + macro[len('SWDB_KNOB_'):])


def used_spellings(source, spellings):
    """The spellings the source's code uses: everywhere except a directive that tests, defines or removes
    that very spelling (``#ifdef``/``#ifndef``/``#undef`` X, the name of ``#define`` X, ``defined(X)``)."""
    wanted = set(spellings)
    text = re.sub(r'//[^\n]*|/\*.*?\*/', ' ', source, flags=re.DOTALL)
    text = re.sub(r'\\\n', ' ', text)
    used = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('swdb_knob_probe_begin') or re.match(r'#\s*(ifdef|ifndef|undef)\b', stripped):
            continue
        definition = re.match(r'#\s*define\s+\w+(.*)', stripped)
        if definition:
            stripped = definition.group(1)
        elif stripped.startswith('#'):
            stripped = re.sub(r'\bdefined\s*\(?\s*\w+\s*\)?', ' ', stripped)
        used |= set(re.findall(r'[A-Za-z_]\w*', stripped)) & wanted
    return used


def applies(entry):
    """True when a contract names knob_range or schedule_range in a clause and declares knobs."""
    checks = {(c.get('negative_control') or {}).get('check') for c in entry.get('clauses') or []}
    return bool(entry.get('knobs')) and bool(checks & set(CHECKS))


def clause_check(entry, clause_id):
    for clause in entry.get('clauses') or []:
        if clause.get('id') == clause_id:
            return (clause.get('negative_control') or {}).get('check')
    return None


# --- integer constant expressions ------------------------------------------------------------
_INT = re.compile(r'(0[xX][0-9A-Fa-f]+|0[bB][01]+|0[0-7]*|[1-9][0-9]*)(?:[uU](?:ll|LL|l|L)?|(?:ll|LL|l|L)[uU]?)?')
_OPS = ['<<', '>>', '<=', '>=', '==', '!=', '&&', '||', '+', '-', '*', '/', '%', '(', ')', '<', '>',
        '&', '|', '^', '~', '!']


def _tokens(text):
    out, i = [], 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        match = _INT.match(text, i)
        if match and (match.end() == len(text) or not (text[match.end()].isalnum() or text[match.end()] == '_')):
            literal = match.group(1)
            base = 16 if literal[:2].lower() == '0x' else 2 if literal[:2].lower() == '0b' else 8 if len(literal) > 1 and literal[0] == '0' else 10
            digits = literal[2:] if base in (16, 2) else literal
            out.append(int(digits, base) if digits else 0)
            i = match.end()
            continue
        for op in _OPS:
            if text.startswith(op, i):
                out.append(op)
                i += len(op)
                break
        else:
            raise ValueError('not an integer constant expression: ' + text.strip()[:80])
    return out


def evaluate(text):
    """The value of a preprocessed C integer constant expression (literals and operators only)."""
    tokens = _tokens(text)
    position = [0]

    def peek():
        return tokens[position[0]] if position[0] < len(tokens) else None

    def take():
        token = peek()
        position[0] += 1
        return token

    def primary():
        token = take()
        if isinstance(token, int):
            return token
        if token == '(':
            value = binary(0)
            if take() != ')':
                raise ValueError('unbalanced parentheses')
            return value
        if token in ('+', '-', '~', '!'):
            value = primary()
            return {'+': value, '-': -value, '~': ~value, '!': int(not value)}[token]
        raise ValueError('not an integer constant expression: ' + text.strip()[:80])

    levels = [['||'], ['&&'], ['|'], ['^'], ['&'], ['==', '!='], ['<', '>', '<=', '>='], ['<<', '>>'],
              ['+', '-'], ['*', '/', '%']]

    def binary(level):
        if level == len(levels):
            return primary()
        value = binary(level + 1)
        while peek() in levels[level]:
            op = take()
            right = binary(level + 1)
            if op in ('/', '%') and right == 0:
                raise ValueError('division by zero')
            if op == '/':
                value = abs(value) // abs(right) * (1 if (value >= 0) == (right >= 0) else -1)
            elif op == '%':
                value = value - right * (abs(value) // abs(right) * (1 if (value >= 0) == (right >= 0) else -1))
            else:
                value = {'||': lambda a, b: int(bool(a or b)), '&&': lambda a, b: int(bool(a and b)),
                         '|': lambda a, b: a | b, '^': lambda a, b: a ^ b, '&': lambda a, b: a & b,
                         '==': lambda a, b: int(a == b), '!=': lambda a, b: int(a != b),
                         '<': lambda a, b: int(a < b), '>': lambda a, b: int(a > b),
                         '<=': lambda a, b: int(a <= b), '>=': lambda a, b: int(a >= b),
                         '<<': lambda a, b: a << b, '>>': lambda a, b: a >> b,
                         '+': lambda a, b: a + b, '-': lambda a, b: a - b, '*': lambda a, b: a * b}[op](value, right)
        return value

    if not tokens:
        raise ValueError('empty expression')
    value = binary(0)
    if position[0] != len(tokens):
        raise ValueError('not an integer constant expression: ' + text.strip()[:80])
    return value


# --- the checks ------------------------------------------------------------------------------
def probe_source(source, entry, rules='v1'):
    """The source with probe lines appended (preprocessed, never compiled): one per declared knob (v1),
    or one per declared spelling of each knob (v2)."""
    if rules == 'v1':
        lines = [PROBE.format(name=knob['name'], macro=knob_macro(knob['name'])) for knob in entry.get('knobs') or []]
    else:
        lines = [PROBE_V2.format(name=knob['name'], index=index, macro=macro)
                 for knob in entry.get('knobs') or [] for index, macro in enumerate(knob_spellings(knob['name']))]
    return source + ('' if source.endswith('\n') else '\n') + '\n'.join(lines) + '\n'


def _bounds(knob, tile_size):
    bounds = dict(knob.get('range') or {})
    if bounds.get('upper_bound') == 'build.tile_size':
        bounds['upper_bound'] = tile_size
    return bounds


def _in_range(value, bounds):
    if 'choices' in bounds:
        return value in bounds['choices']
    if type(value) is not int:
        return False
    upper = [b for b in (bounds.get('max'), bounds.get('upper_bound')) if type(b) is int]
    return (bounds.get('min') is None or value >= bounds['min']) and all(value <= b for b in upper)


def _default(knob, tile_size):
    default = knob.get('default')
    return tile_size if default == 'build.tile_size' else default


def main_file_lines(preprocessed, main):
    """[(line number, text)] of the preprocessed lines that come from the main source file."""
    out, current, number = [], None, 0
    for line in preprocessed.splitlines():
        marker = re.match(r'#\s*(\d+)\s+"((?:\\.|[^"\\])*)"', line)
        if marker:
            number, current = int(marker.group(1)), marker.group(2)
            continue
        if current == main:
            out.append((number, line))
        number += 1
    return out


def _clause(text, name):
    """Content of the first `name(...)` clause in a pragma line (balanced parentheses), or None."""
    match = re.search(r'\b' + name + r'\s*\(', text)
    if not match:
        return None
    depth, start = 1, match.end()
    for i in range(start, len(text)):
        depth += {'(': 1, ')': -1}.get(text[i], 0)
        if depth == 0:
            return text[start:i]
    return text[start:]


def _worksharing(pragma):
    words = re.match(r'\s*#\s*pragma\s+omp\s+((?:[A-Za-z_]+\s*)+)', pragma)
    directive = []
    for word in (words.group(1).split() if words else []):
        if word not in _DIRECTIVE_WORDS:
            break
        directive.append(word)
    return 'for' in directive


def knob_check(preprocessed, entry, tile_size, rules='v1', source=None):
    """(passed, problems, knobs) for knob_range on one preprocessed probe source.

    Rules v2 (certify 1.6) also need the candidate's own text (``source``) to tell which spellings
    its code uses."""
    if rules != 'v1':
        return _knob_check_v2(preprocessed, entry, tile_size, source or '')
    found = {m.group(1): m.group(2).strip() for m in _PROBE.finditer(preprocessed)}
    problems, knobs = [], []
    for knob in entry.get('knobs') or []:
        name, macro = knob['name'], knob_macro(knob['name'])
        bounds = _bounds(knob, tile_size)
        expansion = found.get(name)
        if expansion is None:
            problems.append(f'{name}: knob probe missing from the preprocessed source')
            continue
        if expansion == macro:
            knobs.append({'name': name, 'macro': macro, 'value': _default(knob, tile_size), 'source': 'contract_default'})
            continue
        if 'choices' in bounds:
            value = expansion if re.fullmatch(r'[A-Za-z_]\w*', expansion) else None
        else:
            try:
                value = evaluate(expansion)
            except ValueError as exc:
                problems.append(f'{name}: {macro} = {expansion[:60]!r} is {exc}')
                knobs.append({'name': name, 'macro': macro, 'value': None, 'source': 'assignment'})
                continue
        knobs.append({'name': name, 'macro': macro, 'value': value, 'source': 'assignment'})
        if not _in_range(value, bounds):
            problems.append(f'{name}: {macro} = {expansion[:60]!r} is outside {bounds}')
    return not problems, problems, knobs


def _value(expansion, bounds):
    """(value, error) of one knob expansion: an identifier for a choices knob, else an integer constant."""
    if 'choices' in bounds:
        return (expansion if re.fullmatch(r'[A-Za-z_]\w*', expansion) else None), None
    try:
        return evaluate(expansion), None
    except ValueError as exc:
        return None, exc


def _knob_check_v2(preprocessed, entry, tile_size, source):
    found = {(m.group(1), int(m.group(2))): m.group(3).strip() for m in _PROBE_V2.finditer(preprocessed)}
    problems, knobs = [], []
    for knob in entry.get('knobs') or []:
        name, spellings = knob['name'], knob_spellings(knob['name'])
        bounds = _bounds(knob, tile_size)
        enforced = clause_check(entry, knob.get('legality_clause')) == KNOB_RANGE
        expansions = [found.get((name, index)) for index in range(len(spellings))]
        if any(expansion is None for expansion in expansions):
            problems.append(f'{name}: knob probe missing from the preprocessed source')
            continue
        used = [macro for macro in spellings if macro in used_spellings(source, spellings)]
        defined = {macro: expansion for macro, expansion in zip(spellings, expansions)
                   if macro in used and expansion != macro}
        row = {'name': name, 'macro': None, 'spellings': list(spellings), 'used': used, 'value': None,
               'source': 'unverified'}
        knobs.append(row)
        if not used or len(defined) != len(used):
            if enforced:
                problems.append(f'{name}: no assignment of {" or ".join(spellings)} is used by the candidate'
                                if not used else
                                f'{name}: {", ".join(m for m in used if m not in defined)} is used but not defined '
                                'at the end of the translation unit')
            continue
        values = {}
        for macro, expansion in defined.items():
            value, error = _value(expansion, bounds)
            if error is not None:
                problems.append(f'{name}: {macro} = {expansion[:60]!r} is {error}')
            values[macro] = value
        if len(set(map(repr, values.values()))) > 1:
            problems.append(f'{name}: the used spellings disagree ({values})')
            continue
        macro = used[0]
        row.update(macro=macro, value=values[macro], source='assignment')
        if values[macro] is None:
            continue
        if not _in_range(values[macro], bounds):
            problems.append(f'{name}: {macro} = {defined[macro][:60]!r} is outside {bounds}')
    return not problems, problems, knobs


def schedule_check(preprocessed, entry, tile_size, main):
    """(passed, problems, schedules) for schedule_range on one preprocessed source."""
    knobs = [k for k in entry.get('knobs') or [] if clause_check(entry, k.get('legality_clause')) == SCHEDULE_RANGE]
    kinds = next((k['range']['choices'] for k in knobs if 'choices' in (k.get('range') or {})), None)
    granularity = next((_bounds(k, tile_size) for k in knobs if 'choices' not in (k.get('range') or {})), {})
    problems, schedules = [], []
    if kinds is None:
        return False, ['the contract declares no schedule kinds for schedule_range'], schedules
    for number, line in main_file_lines(preprocessed, main):
        if not re.match(r'\s*#\s*pragma\s+omp\b', line) or not _worksharing(line):
            continue
        clause = _clause(line, 'schedule')
        row = {'line': number, 'pragma': line.strip()[:160], 'kind': None, 'chunk': None}
        schedules.append(row)
        if clause is None:
            row['kind'] = 'default'
            continue
        head, _, chunk = clause.partition(',')
        modifiers, _, kind = head.rpartition(':')
        kind = kind.strip()
        row['kind'] = kind
        bad_modifiers = {m.strip() for m in modifiers.split(',') if m.strip()} - SCHEDULE_KINDS_MODIFIERS
        if kind not in kinds or bad_modifiers:
            problems.append(f'line {number}: schedule({clause.strip()}) kind is outside {kinds}')
            continue
        if chunk.strip():
            try:
                value = evaluate(chunk)
            except ValueError as exc:
                problems.append(f'line {number}: schedule chunk {chunk.strip()[:60]!r} is {exc}')
                continue
            row['chunk'] = value
            if not _in_range(value, granularity):
                problems.append(f'line {number}: schedule chunk {value} is outside {granularity}')
    return not problems, problems, schedules


# --- negative controls -----------------------------------------------------------------------
def knob_control(source, entry, rules='v1'):
    """The source with the knob_range knob's assignment set one below its minimum.

    Rules v1 set ``SWDB_KNOB_<NAME>``; rules v2 set every declared spelling the candidate uses (that
    spelling when it uses none)."""
    knob = next((k for k in entry.get('knobs') or []
                 if clause_check(entry, k.get('legality_clause')) == KNOB_RANGE
                 and type((k.get('range') or {}).get('min')) is int), None)
    if knob is None:
        raise Failure('candidate source lacks a unique negative-control mutation site: knob_out_of_range')
    value = knob['range']['min'] - 1
    macros = [knob_macro(knob['name'])]
    if rules != 'v1':
        spellings = knob_spellings(knob['name'])
        macros = [m for m in spellings if m in used_spellings(source, spellings)] or macros
    lines_out = [f'#define {macro} {value}' for macro in macros]
    lines = source.split('\n')
    if lines and lines[0].startswith(KNOB_BLOCK):
        prefix = '#define SWDB_KNOB_' if rules == 'v1' else '#define SWDB_'
        end = 1
        while end < len(lines) and lines[end].startswith(prefix):
            end += 1
        block = [l for l in lines[1:end] if not any(re.match(r'#define ' + macro + r'\b', l) for macro in macros)]
        return '\n'.join([lines[0], *block, *lines_out, *lines[end:]])
    return CONTROL_BLOCK + '\n' + '\n'.join(lines_out) + '\n' + source


_PRAGMA_LINE = re.compile(r'^([ \t]*#[ \t]*pragma[ \t]+omp\b[^\n]*)$', re.MULTILINE)
_PRAGMA_OPERATOR = re.compile(r'_Pragma\s*\(\s*"((?:\\.|[^"\\])*)"\s*\)')


def _guided(line):
    """One `#pragma omp ... for` line with its schedule clause replaced by, or extended with, schedule(guided)."""
    clause = _clause(line, 'schedule')
    if clause is None:
        comment = line.find('//')
        head, tail = (line, '') if comment < 0 else (line[:comment], line[comment:])
        return head.rstrip() + ' schedule(guided)' + (' ' + tail if tail else '')
    start = re.search(r'\bschedule\s*\(', line).start()
    end = line.index(clause, start) + len(clause) + 1
    return line[:start] + 'schedule(guided)' + line[end:]


def schedule_control(source, rules='v1'):
    """The source with schedule(guided) on every `#pragma omp ... for` line and, from rules v2 (C24),
    in every `_Pragma("omp ... for ...")` operator."""
    count = [0]

    def mutate(match):
        line = match.group(1)
        if not _worksharing(line) or line.rstrip().endswith('\\'):
            return line
        count[0] += 1
        return _guided(line)

    def operator(match):
        content = match.group(1)
        line = '#pragma ' + content
        if not re.match(r'\s*#\s*pragma\s+omp\b', line) or not _worksharing(line):
            return match.group(0)
        count[0] += 1
        return '_Pragma("' + _guided(line)[len('#pragma '):] + '")'

    mutated = _PRAGMA_LINE.sub(mutate, source)
    if rules != 'v1':
        mutated = _PRAGMA_OPERATOR.sub(operator, mutated)
    if not count[0]:
        raise CandidateFailure('candidate source lacks a unique negative-control mutation site: schedule_out_of_range',
                               check='negative_control_site:schedule_out_of_range')
    return mutated


def control(source, name, entry, rules='v1'):
    """A certifier-owned control: the mutated candidate source (before instrumentation)."""
    if name == 'knob_out_of_range':
        return {'source': knob_control(source, entry, rules), 'fault': None, 'site': 'knob_assignment'}
    if name == 'schedule_out_of_range':
        return {'source': schedule_control(source, rules), 'fault': None, 'site': 'schedule_clause'}
    raise Failure('unknown rewrite control')
