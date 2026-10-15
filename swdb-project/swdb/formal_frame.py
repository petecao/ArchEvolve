"""The formal-half frame of typed-library entries (`formal_frame: 1`), checked by `swdb validate`.

Created: 2026-10-14 ET (Probata proof of concept ticket 20). Design: formal-verification map 16
items 2, 4 and 13; 17 item 5; 10 item 4; 15 item 5; 26 item 4; 12 item 1. Format:
docs/reference/format-v0.4-formal-frame.md.

What an entry in the frame carries (on top of the existing entry fields):

- `formal_frame: 1` and `version` (dotted numbers); `once: <entry>@<version>` placements and the
  required-enabling list name entries by ID and this version.
- per clause: a required `proof_placement` (`per_candidate`, `{once: self | <entry>@<version>}`,
  or `{assumed: {kind, rule | owner, evidence}}`), separate from `discharge_mode`; and optionally
  `acsl: {text, uses}` (the formal half and the logic-library entries it calls).
- `proof_unit: {prototype, types?}`: the C declaration the formal halves are type-checked against
  (hand-written until ticket 21's C lowering supplies it).
- rewrite contracts: `concurrency_frame` (per interface array: `shared_actions` from vocabulary
  `shared_action_kinds`, `history_reads` yes/no) and the marker `contract_role`
  (`offload_only` or `enabling`); an offload-only contract lists `required_enabling_contracts`
  in order (`contract`, `versions`); an enabling contract never lists what it enables.
- proof-semantics entries (kind `proof_semantics`): `rules`, each with exactly one of
  `cites: {gem5_commit, path, lines}` and `assumed: {owner}`.

Logic-library files are `library/logic/<name>.acsl`, entry ID `logic.<name>` (rules in
`swdb.acsl_subset`). Entries without `formal_frame` keep validating as before and carry no frame
fields; ticket 36's proof setup check refuses them at proof time.
"""

import re

from swdb import acsl_subset, framac, paths, vocab
from swdb.problems import Problem

FRAME_VERSION = 1
FRAME_FIELDS = ('proof_unit', 'concurrency_frame', 'contract_role', 'required_enabling_contracts', 'rules')
CLAUSE_FIELDS = ('acsl', 'proof_placement')
ROLES = ('offload_only', 'enabling')
VERSION = re.compile(r'\d+(\.\d+)*')
RANGE = re.compile(r'\s*(>=|<=|==|>|<)\s*\d+(\.\d+)*\s*(,\s*(>=|<=|==|>|<)\s*\d+(\.\d+)*\s*)*')
LOGIC_FOLDER = 'logic'


def logic_files(root, library=None):
    """{entry ID: path} of the library's logic-library files (ticket 26: with the library, each entry's own file)."""
    from swdb import logic_library
    return {ident: found.path for ident, found in logic_library.files(root, library).items()}


class Report:
    """The frame's findings: problems (refusals), unchecked formal halves, type-checked count."""

    def __init__(self):
        self.problems = []
        self.unchecked = []
        self.checked = 0
        self.framac_version = ''
        self.logic_checked = 0          # ticket 26: logic files type-checked on their own
        self.logic_unchecked = []


def check(library):
    """Check every entry and logic-library file of `library` (a swdb.library.Library)."""
    report = Report()
    vocabs, _ = vocab.load_all(paths.VOCAB)
    from swdb import logic_library
    files = logic_files(library.root, library)
    logic = acsl_subset.LogicLibrary({entry: path.read_text() for entry, path in files.items()})
    for entry, found in logic.problems.items():
        report.problems += [Problem(str(files[entry]), where, reason) for where, reason in found]
    for entry, path in files.items():                     # ticket 26: every logic file is versioned
        if logic_library.version_of(path.read_text()) is None:
            report.problems.append(Problem(str(path), 'version', f'{entry} has no version line: the first line of a '
                                           'logic-library file is "// version: <dotted numbers>" (for example 1.0)'))
    rules = {f"{eid}#{rule.get('id')}" for eid, data in library.entries.items()
             if data.get('kind') == 'proof_semantics' and isinstance(data.get('rules'), list)
             for rule in data['rules'] if isinstance(rule, dict)}
    pending = []
    for entry_id, data in library.entries.items():
        path = str(library.files[entry_id])

        def error(where, reason, path=path):
            report.problems.append(Problem(path, where, reason))

        _entry(library, entry_id, data, error, vocabs, logic, rules, pending)
        if data.get('kind') == 'proof_semantics' and data.get('formal_frame') == FRAME_VERSION:
            from swdb import proof_semantics       # ticket 27: calls, contracts, inventory, ghost state
            report.unchecked += proof_semantics.check(library, entry_id, data, error)
    _typecheck(library, logic, files, pending, report)
    return report


def _entry(library, entry_id, data, error, vocabs, logic, rules, pending):
    clauses = data.get('clauses') if isinstance(data.get('clauses'), list) else []
    clauses = [c if isinstance(c, dict) else {} for c in clauses]
    if 'enables' in data:
        error('enables', 'an enabling contract never lists what it enables (map 17 item 5); the offload-only '
                         'contract names its required enabling contracts')
    frame = data.get('formal_frame')
    if frame is None:
        used = [key for key in FRAME_FIELDS if key in data]
        used += [f'clauses[{i}].{key}' for i, c in enumerate(clauses) for key in CLAUSE_FIELDS if key in c]
        if used or data.get('kind') == 'proof_semantics':
            error('formal_frame', f'{", ".join(used) or "a proof-semantics entry"} belongs to the formal-half '
                                  'frame; set formal_frame: 1')
        return
    if frame != FRAME_VERSION:
        error('formal_frame', f'formal_frame must be {FRAME_VERSION}')
        return
    if not isinstance(data.get('version'), str) or not VERSION.fullmatch(data['version']):
        error('version', 'an entry in the frame has a dotted-number version, as a quoted string (for example "1.0")')
    with_acsl = []
    for i, clause in enumerate(clauses):
        where = f'clauses[{i}]'
        cid = clause.get('id')
        if 'proof_placement' not in clause:
            error(f'{where}.proof_placement', f"{entry_id} clause {cid!r} has no proof placement "
                                              '(per_candidate, once or assumed)')
        else:
            for reason in _placement(library, entry_id, clause['proof_placement'], vocabs, rules):
                error(f'{where}.proof_placement', reason)
        if 'acsl' in clause:
            acsl = clause['acsl']
            if (not isinstance(acsl, dict) or set(acsl) - {'text', 'uses'} or not isinstance(acsl.get('text'), str)
                    or not acsl['text'].strip() or not isinstance(acsl.get('uses', []), list)
                    or not all(isinstance(u, str) for u in acsl.get('uses', []))):
                error(f'{where}.acsl', 'acsl takes text (the formal half) and uses (logic-library entry IDs)')
                continue
            reasons = acsl_subset.check_formal_half(acsl['text'], acsl.get('uses', []), logic)
            reasons += [f'uses {u}, which belongs to another entry: an entry\'s own logic file serves only that '
                        'entry (map 16 item 9)' for u in acsl.get('uses', [])
                        if u in logic.files and u.startswith('logic.') and library.get(u[len('logic.'):]) is not None
                        and u != f'logic.{entry_id}']
            for reason in reasons:
                error(f'{where}.acsl', reason)
            if not reasons:
                with_acsl.append((i, acsl))
    unit = data.get('proof_unit')
    if with_acsl or unit is not None:
        if isinstance(unit, dict) and 'prototype' in unit:
            error('proof_unit.prototype', 'a hand-written prototype is replaced by the C lowering of the baseline proof '
                                          'unit (ticket 21): give proof_unit.source (path, sha256) and function')
            unit, with_acsl = None, []
        elif (not isinstance(unit, dict) or set(unit) - {'source', 'function', 'types'}
                or not isinstance(unit.get('function'), str) or not re.fullmatch(r'[A-Za-z_]\w*', unit['function'])):
            error('proof_unit', 'formal halves need proof_unit: {source: {path, sha256}, function}, the baseline proof '
                                'unit whose C lowering they are type-checked against (kept C++ names)')
            unit, with_acsl = None, []
        else:
            for key in ('source', 'types') if 'types' in unit else ('source',):
                try:
                    library._pin(unit[key])
                except (KeyError, TypeError, ValueError, OSError) as exc:
                    error(f'proof_unit.{key}', str(exc))
                    unit, with_acsl = None, []
                    break
    if unit is not None and (with_acsl or data.get('kind') == 'rewrite_contract'):
        pending.append((entry_id, error, unit, with_acsl, data.get('concurrency_frame')))
    kind = data.get('kind')
    if kind == 'rewrite_contract':
        _concurrency(data, error, vocabs)
        _roles(library, data, error)
    elif any(key in data for key in ('concurrency_frame', 'contract_role', 'required_enabling_contracts')):
        error('kind', 'concurrency frames and contract roles belong to rewrite contracts')
    if kind == 'proof_semantics':
        _rules(data, error)
    elif 'rules' in data:
        error('rules', 'proof-semantics rules belong to a proof_semantics entry')


def _placement(library, entry_id, placement, vocabs, rules):
    if placement == 'per_candidate':
        return []
    if not isinstance(placement, dict) or len(placement) != 1 or set(placement) - {'once', 'assumed'}:
        return ['a proof placement takes exactly one of per_candidate, once: <entry>@<version> | self, '
                'and assumed: {kind, rule or owner, evidence}']
    if 'once' in placement:
        target = placement['once']
        if target == 'self':
            return []
        match = re.fullmatch(r'([a-z0-9][a-z0-9._-]*)@(\d+(?:\.\d+)*)', str(target))
        if not match:
            return [f'once takes self or <entry>@<version>, not {target!r}']
        other = library.get(match.group(1))
        if other is None or str(other.get('version')) != match.group(2):
            have = f' (that entry is at version {other.get("version")})' if other is not None else ''
            return [f'once names {target}, which is not in the library{have}']
        return []
    assumed = placement['assumed']
    if not isinstance(assumed, dict):
        return ['assumed takes {kind, rule or owner, evidence}']
    found = []
    kinds = vocabs.get('proof_assumption_kinds', [])
    if assumed.get('kind') not in kinds:
        found.append(f'{assumed.get("kind")!r} is not an assumption kind (vocabulary proof_assumption_kinds: '
                     f'{", ".join(kinds)})')
    unknown = sorted(set(assumed) - {'kind', 'rule', 'owner', 'evidence'})
    if unknown:
        found.append(f'assumed has unknown keys {", ".join(unknown)}')
    if not any(isinstance(assumed.get(key), str) and assumed[key].strip() for key in ('rule', 'owner')):
        found.append('an assumed placement names its rule or owner')
    elif 'rule' in assumed and assumed['rule'] not in rules:
        found.append(f'assumed names proof-semantics rule {assumed["rule"]}, which the library does not hold '
                     '(<proof_semantics entry>#<rule id>)')
    evidence = assumed.get('evidence')
    if not ((isinstance(evidence, str) and evidence.strip())
            or (isinstance(evidence, list) and evidence and all(isinstance(e, str) and e for e in evidence))):
        found.append('an assumed placement names its evidence')
    return found


def _concurrency(data, error, vocabs):
    frame = data.get('concurrency_frame')
    if not isinstance(frame, list):
        error('concurrency_frame', 'a rewrite contract in the frame needs its concurrency frame: for each array '
                                   'of the proof unit interface, its shared actions and history_reads')
        return
    kinds, seen = vocabs.get('shared_action_kinds', []), set()
    for i, row in enumerate(frame):
        where = f'concurrency_frame[{i}]'
        if not isinstance(row, dict) or set(row) != {'array', 'shared_actions', 'history_reads'}:
            error(where, 'each row has exactly array, shared_actions and history_reads')
            continue
        if not isinstance(row['array'], str) or not re.fullmatch(r'[A-Za-z_]\w*', row['array']) or row['array'] in seen:
            error(f'{where}.array', 'array is a C name of the proof unit interface, listed once')
        seen.add(str(row['array']))
        actions = row['shared_actions']
        if not isinstance(actions, list):
            error(f'{where}.shared_actions', 'shared_actions is a list (empty: no shared action)')
        else:
            for action in actions:
                if action not in kinds:
                    error(f'{where}.shared_actions', f'{action!r} is not a shared-action kind (vocabulary '
                                                     f'shared_action_kinds: {", ".join(kinds)})')
        if not isinstance(row['history_reads'], bool):
            error(f'{where}.history_reads', 'history_reads accepts only yes or no')


def _roles(library, data, error):
    role = data.get('contract_role')
    if role is not None and role not in ROLES:
        error('contract_role', f'contract_role is one of {", ".join(ROLES)}')
    required = data.get('required_enabling_contracts')
    if role != 'offload_only':
        if required is not None:
            error('required_enabling_contracts', 'only an offload-only contract names required enabling contracts')
        return
    if not isinstance(required, list) or not required:
        error('required_enabling_contracts', 'an offload-only contract names its required enabling contracts, in '
                                             'order (contract, versions)')
        return
    seen = set()
    for i, row in enumerate(required):
        where = f'required_enabling_contracts[{i}]'
        if not isinstance(row, dict) or set(row) != {'contract', 'versions'}:
            error(where, 'each required enabling contract has exactly contract and versions')
            continue
        other = library.get(row['contract']) if isinstance(row['contract'], str) else None
        if other is None or other.get('kind') != 'rewrite_contract':
            error(f'{where}.contract', f'required enabling contract {row["contract"]} is unknown')
        elif other.get('contract_role') != 'enabling':
            error(f'{where}.contract', f'{row["contract"]} is not marked contract_role: enabling')
        if str(row['contract']) in seen:
            error(f'{where}.contract', f'{row["contract"]} is listed twice')
        seen.add(str(row['contract']))
        if not isinstance(row['versions'], str) or not RANGE.fullmatch(row['versions']):
            error(f'{where}.versions', f'malformed version range {row["versions"]!r}: comma-separated bounds such '
                                       'as ">=1.0, <2.0"')


def _rules(data, error):
    found, seen = data.get('rules'), set()
    if not isinstance(found, list) or not found:
        error('rules', 'a proof_semantics entry lists its rules')
        return
    for i, rule in enumerate(found):
        where = f'rules[{i}]'
        if not isinstance(rule, dict) or not isinstance(rule.get('id'), str) or rule['id'] in seen \
                or not isinstance(rule.get('statement'), str) or not rule['statement'].strip():
            error(where, 'a rule has a unique id and a statement')
            continue
        seen.add(rule['id'])
        unknown = sorted(set(rule) - {'id', 'statement', 'cites', 'assumed'})
        if unknown:
            error(where, f'unknown keys {", ".join(unknown)} (acsl text of rules comes with tickets 27 and 28)')
        has = [key for key in ('cites', 'assumed') if key in rule]
        if len(has) != 1:
            error(where, 'a proof-semantics rule carries exactly one of cites: {gem5_commit, path, lines} and '
                         'assumed: {owner}')
        elif has == ['cites']:
            cites = rule['cites']
            if (not isinstance(cites, dict) or set(cites) != {'gem5_commit', 'path', 'lines'}
                    or not re.fullmatch(r'[0-9a-f]{7,40}', str(cites.get('gem5_commit')))
                    or not isinstance(cites.get('path'), str) or not cites['path']
                    or not re.fullmatch(r'\d+(-\d+)?(,\s*\d+(-\d+)?)*', str(cites.get('lines')))):
                error(f'{where}.cites', 'cites takes gem5_commit (hex), path and lines ("193-212")')
        else:
            assumed = rule['assumed']
            if not isinstance(assumed, dict) or set(assumed) != {'owner'} or not isinstance(assumed['owner'], str) \
                    or not assumed['owner'].strip():
                error(f'{where}.assumed', 'assumed takes exactly owner')


def _source(unit, logic, clauses, declaration):
    """The check file: the used logic files, then each formal half on the lowered declaration (ticket 21)."""
    uses = []
    for _, acsl in clauses:
        uses += [u for u in acsl.get('uses', []) if u not in uses]
    parts = ['#include "proof_unit_types.h"'] if 'types' in unit else []
    head, prototype = declaration.rstrip('\n').rsplit('\n', 1)
    parts.append(head)
    parts += [f'/*@\n{logic.files[u]}\n*/' for u in uses]
    for _, acsl in clauses:
        parts += [f'/*@\n{acsl["text"]}\n*/', prototype]
    return '\n'.join(parts) + '\n'


_LOWERED = {}


def lowered(library, unit):
    """The C lowering of a proof_unit's baseline function (cached per source sha256), or the LoweringError."""
    from swdb import c_lowering, proof_semantics
    path = library.resolve(unit['source'])
    covered = proof_semantics.covered_names(library)       # ticket 27: calls a proof semantics defines
    key = (str(path), unit['source'].get('sha256'), unit['function'], c_lowering.locate(), tuple(sorted(covered)))
    if key not in _LOWERED:
        try:
            _LOWERED[key] = c_lowering.lower(path, unit['function'], **proof_semantics.lowering_options(library))
        except c_lowering.LoweringError as exc:
            _LOWERED[key] = exc
    return _LOWERED[key]


def _interface(unit_lowering, frame, error):
    """Ticket 21: the concurrency frame names every interface array (pointer parameter) of the proof unit, and only those."""
    if not isinstance(frame, list):
        return
    arrays = [name for name, _type, pointer in unit_lowering.parameters if pointer]
    named = [row.get('array') for row in frame if isinstance(row, dict)]
    for name in arrays:
        if name not in named:
            error('concurrency_frame', f'the concurrency frame has no row for interface array {name} of '
                                       f'{unit_lowering.function} (every pointer parameter needs one)')
    for name in named:
        if isinstance(name, str) and name not in arrays:
            error('concurrency_frame', f'{name} is not a pointer parameter of {unit_lowering.function}, so it is not an '
                                       'interface array of the proof unit')


def _typecheck(library, logic, files, pending, report):
    _typecheck_logic(logic, files, report)
    if not pending:
        return
    tool = framac.locate()
    report.framac_version = tool.version if not tool.missing else ''
    for entry_id, error, unit, clauses, frame in pending:
        path = str(library.files[entry_id])
        unit_lowering = lowered(library, unit)
        if isinstance(unit_lowering, Exception):
            from swdb import c_lowering
            if isinstance(unit_lowering, (c_lowering.Unsupported, c_lowering.ParseError, c_lowering.NotFound)):
                error('proof_unit', f'the baseline proof unit {unit["function"]} has no C lowering: {unit_lowering}')
                continue
            report.unchecked += [Problem(path, f'clauses[{i}].acsl', f'not type-checked: no C lowering of the proof '
                                         f'unit ({unit_lowering}); this formal half is unchecked, not valid')
                                 for i, _ in clauses]
            continue
        _interface(unit_lowering, frame, error)
        if not clauses:
            continue
        if tool.missing:
            report.unchecked += [Problem(path, f'clauses[{i}].acsl', f'not type-checked: {tool.missing}; '
                                         'this formal half is unchecked, not valid') for i, _ in clauses]
            continue
        includes = [('proof_unit_types.h', library.resolve(unit['types']))] if 'types' in unit else []
        declaration = unit_lowering.declaration
        if framac.typecheck(tool, _source(unit, logic, clauses, declaration), includes) is None:
            report.checked += len(clauses)
            continue
        for i, acsl in clauses:
            message = framac.typecheck(tool, _source(unit, logic, [(i, acsl)], declaration), includes)
            if message is None:
                report.checked += 1
            else:
                error(f'clauses[{i}].acsl', f'Frama-C {tool.version} refuses the formal half: {message}')


def _typecheck_logic(logic, files, report):
    """Ticket 26: Frama-C parses and type-checks every logic file that passes the subset, on its own."""
    clean = [entry for entry in files if not logic.problems.get(entry)]
    if not clean:
        return
    tool = framac.locate()
    report.framac_version = tool.version if not tool.missing else report.framac_version
    for entry in clean:
        path = str(files[entry])
        if tool.missing:
            report.logic_unchecked.append(Problem(path, '-', f'logic file not type-checked: {tool.missing}; it is '
                                                             'unchecked, not valid'))
            continue
        message = framac.typecheck(tool, f'/*@\n{logic.files[entry]}\n*/\n')
        if message is not None:
            report.problems.append(Problem(path, '-', f'Frama-C {tool.version} refuses the logic file: {message}'))
        else:
            report.logic_checked += 1
