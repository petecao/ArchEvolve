"""The ACSL subset of formal halves and logic-library files (formal-verification map 16 item 2).

Created: 2026-10-14 ET (Probata proof of concept ticket 20). Format:
docs/reference/format-v0.4-formal-frame.md.

The checks are syntactic and work on tokens, so they run without Frama-C. Frama-C parses and
type-checks the same text separately (`swdb.framac`); it checks no termination and accepts
constructs this subset refuses, so neither check replaces the other.

A formal half (one clause's `acsl.text`) holds only `requires`, `ensures` and `assigns` clauses:

- quantifiers are first-order over integer types, each variable with a lower and an upper bound
  in the guard (`\\forall integer k; lo <= k < hi ==> ...`, `\\exists integer k; lo <= k < hi && ...`);
- labels: `\\old(e)` and `\\at(e, Pre)` only;
- built-ins: `\\valid`, `\\separated`, `\\result` and the constants `\\true`, `\\false`, `\\null`,
  `\\nothing`; no floating-point built-in, no other memory built-in, no `\\lambda` (so no `\\sum`);
- `assigns` takes `\\nothing`, single locations and bounded index ranges, never `\\everything`;
- logic calls go only to definitions in the logic-library entries the clause lists, and never reach
  an inductive predicate or a name only an axiom defines;
- no logic definition, inductive definition, lemma or axiom inside the formal half.

A logic-library file holds `logic`/`predicate` definitions, `inductive` definitions and `lemma`s.
Definitions are non-recursive or primitive recursive (each recursive call takes `n - 1` of an
integer parameter `n`, under a base case `n <= 0`); mutual recursion is refused; no `axiom` and no
`axiomatic` block; a definition body follows the formal-half expression rules (labels aside).
"""

import re
from dataclasses import dataclass, field

_TOKEN = re.compile(r"""
  (?P<ws>\s+)
| (?P<comment>//[^\n]*|/\*.*?\*/)
| (?P<num>0[xX][0-9a-fA-F]+[uUlL]*|(?:\d+\.(?!\.)\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?[fFdDlLuU]*)
| (?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')
| (?P<id>\\?[A-Za-z_][A-Za-z0-9_]*)
| (?P<op><==>|==>|<-->|-->|\.\.|->|==|!=|<=|>=|&&|\|\||\^\^|<<|>>|[-+*/%<>!~&|^?:;,.()\[\]{}=])
""", re.X | re.S)

OPEN, CLOSE = '([{', ')]}'
BINDERS = {'\\forall', '\\exists', '\\lambda', '\\let'}
ALLOWED_BUILTINS = {'\\forall', '\\exists', '\\old', '\\at', '\\valid', '\\initialized', '\\separated', '\\result',
                    '\\true', '\\false', '\\null', '\\nothing'}
EXTENDED_QUANTIFIERS = {'\\sum', '\\product', '\\numof', '\\max', '\\min'}
MEMORY_BUILTINS = {'\\valid_read', '\\valid_function', '\\object_pointer', '\\base_addr', '\\block_length',
                   '\\offset', '\\allocable', '\\freeable', '\\fresh', '\\dangling',
                   '\\allocation', '\\pointer_comparable', '\\separated_from', '\\union', '\\inter',
                   '\\empty', '\\subset'}
FLOAT_BUILTINS = {'\\round_float', '\\round_double', '\\is_finite', '\\is_infinite', '\\is_plus_infinity',
                  '\\is_minus_infinity', '\\is_NaN', '\\exact', '\\round_error', '\\relative_error',
                  '\\total_error', '\\plus_infinity', '\\minus_infinity', '\\NaN', '\\sign', '\\Positive',
                  '\\Negative', '\\NearestEven', '\\NearestAway', '\\ToZero', '\\Up', '\\Down', '\\model',
                  '\\eq_float', '\\ne_float', '\\le_float', '\\lt_float', '\\ge_float', '\\gt_float',
                  '\\eq_double', '\\ne_double', '\\le_double', '\\lt_double', '\\ge_double', '\\gt_double',
                  '\\is_float', '\\is_double'}
INTEGER_TYPES = {'integer', 'int', 'unsigned', 'signed', 'long', 'short', 'char', 'size_t', '_Bool'}
CLAUSES = {'requires', 'ensures', 'assigns'}
OTHER_CLAUSES = {'terminates', 'decreases', 'exits', 'allocates', 'frees', 'assumes', 'complete', 'disjoint',
                 'check', 'admit', 'reads', 'writes', 'loop', 'invariant', 'assert', 'variant', 'ghost'}
GLOBALS = {'logic', 'predicate', 'lemma', 'inductive', 'axiomatic', 'axiom', 'type'}
NOT_CALLS = {'sizeof', 'if', 'while', 'for', 'return'}
COMPARISONS = {'<', '<=', '>', '>='}


class AcslSyntaxError(ValueError):
    pass


@dataclass(frozen=True)
class Tok:
    kind: str
    text: str


def tokens(text):
    found, pos = [], 0
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if not match:
            raise AcslSyntaxError(f'unexpected character {text[pos]!r}')
        pos = match.end()
        if match.lastgroup not in ('ws', 'comment'):
            found.append(Tok(match.lastgroup, match.group()))
    return found


def _texts(toks):
    return [t.text for t in toks]


def _close(toks, i):
    """Index of the bracket closing the one at `i` (or len(toks) when unbalanced)."""
    depth = 0
    for j in range(i, len(toks)):
        if toks[j].text in OPEN:
            depth += 1
        elif toks[j].text in CLOSE:
            depth -= 1
            if depth == 0:
                return j
    return len(toks)


def _statement_end(toks, i, stop=None):
    """Index of the `;` ending the statement that starts at `i`; quantifier and `\\let` binders
    end with their own `;`, which does not end the statement."""
    stop = len(toks) if stop is None else stop
    depth, pending = 0, {}
    for j in range(i, stop):
        text = toks[j].text
        if text in OPEN:
            depth += 1
        elif text in CLOSE:
            pending.pop(depth, None)
            depth -= 1
            if depth < 0:
                return j
        elif text in BINDERS:
            pending[depth] = pending.get(depth, 0) + 1
        elif text == ';':
            if pending.get(depth):
                pending[depth] -= 1
            elif depth == 0:
                return j
    return stop


def _split(toks, separators):
    """Split at top-level separator tokens; returns (parts, separators found)."""
    parts, seps, depth, start = [], [], 0, 0
    for j, tok in enumerate(toks):
        if tok.text in OPEN:
            depth += 1
        elif tok.text in CLOSE:
            depth -= 1
        elif depth == 0 and tok.text in separators:
            parts.append(toks[start:j])
            seps.append(tok.text)
            start = j + 1
    parts.append(toks[start:])
    return parts, seps


def _strip(toks):
    while len(toks) >= 2 and toks[0].text == '(' and _close(toks, 0) == len(toks) - 1:
        toks = toks[1:-1]
    return toks


def _group_end(toks, i, stop):
    """First unmatched closing bracket after `i`, else `stop`."""
    depth = 0
    for j in range(i, stop):
        if toks[j].text in OPEN:
            depth += 1
        elif toks[j].text in CLOSE:
            if depth == 0:
                return j
            depth -= 1
    return stop


def _calls(toks):
    """[(name, [argument token lists])] of every `name(...)` / `name{L}(...)` in `toks`."""
    found = []
    for i, tok in enumerate(toks):
        if tok.kind != 'id' or tok.text.startswith('\\') or tok.text in NOT_CALLS:
            continue
        j = i + 1
        if j < len(toks) and toks[j].text == '{':
            j = _close(toks, j) + 1
        if j < len(toks) and toks[j].text == '(' and not (i > 0 and toks[i - 1].text in ('.', '->')):
            end = _close(toks, j)
            args, _ = _split(toks[j + 1:end], {','})
            found.append((tok.text, [] if end == j + 1 else args))
    return found


def _binders(toks):
    """[(name, type tokens)] of a quantifier binder list `T a, b, U c`."""
    found, last = [], []
    for part in _split(toks, {','})[0]:
        if not part:
            continue
        kind = part[:-1] or last
        found.append((part[-1].text, kind))
        last = kind
    return found


def _bounds(guard, names):
    """{name: {'lower', 'upper'}} found in the top-level conjuncts of `guard`."""
    found = {name: set() for name in names}
    for conjunct in _split(guard, {'&&'})[0]:
        conjunct = _strip(conjunct)
        if _split(conjunct, {'||', '==>', '<==>', '^^', '?', '-->', '<-->'})[1] or (conjunct and conjunct[0].text == '!'):
            continue    # only a plain comparison chain bounds a variable
        operands, ops = _split(conjunct, COMPARISONS)
        for left, op, right in zip(operands, ops, operands[1:]):
            lt, rt = _texts(left), _texts(right)
            for name in names:
                if lt == [name] and name not in rt and rt:
                    found[name].add('upper' if op in ('<', '<=') else 'lower')
                elif rt == [name] and name not in lt and lt:
                    found[name].add('lower' if op in ('<', '<=') else 'upper')
    return found


def check_expression(toks, *, formal_half=True):
    """Reasons the term or predicate `toks` breaks the subset's expression rules."""
    reasons, skip = [], set()
    for i, tok in enumerate(toks):
        if i in skip:
            continue
        text = tok.text
        if text in ('\\forall', '\\exists'):
            end = _statement_end(toks, i + 1)
            if end >= len(toks) or toks[end].text != ';':
                reasons.append(f'{text} without a binder list ending in ";"')
                continue
            skip.update(range(i + 1, end + 1))
            binders = _binders(toks[i + 1:end])
            for name, kind in binders:
                words = _texts(kind)
                if not words or any(w not in INTEGER_TYPES and not re.fullmatch(r'u?int\d+_t', w) for w in words):
                    reasons.append(f'quantifier variable {name} has type {" ".join(words) or "?"}, not an integer '
                                   'type; quantifiers range over integers only')
            body = toks[end + 1:_group_end(toks, end + 1, len(toks))]
            if text == '\\forall':
                parts, seps = _split(body, {'==>'})
                guard = parts[0] if seps else []
            else:
                guard = body
            bounds = _bounds(guard, [name for name, _ in binders])
            joint = '==>' if text == '\\forall' else '&&'
            for name, found in bounds.items():
                if found != {'lower', 'upper'}:
                    reasons.append(f'quantifier over {name} has no range guard: write '
                                   f'"lo <= {name} < hi {joint} ..." '
                                   'with integer bounds')
        elif text == '\\lambda' or text in EXTENDED_QUANTIFIERS:
            reasons.append(f'{text} is not allowed: no \\lambda (and so no \\sum or other extended quantifier); '
                           'use a primitive-recursive logic-library definition')
        elif text == '\\at':
            if i + 1 < len(toks) and toks[i + 1].text == '(':
                args, _ = _split(toks[i + 2:_close(toks, i + 1)], {','})
                label = _texts(args[-1]) if len(args) >= 2 else []
                if formal_half and label != ['Pre']:
                    reasons.append(f'\\at with label {" ".join(label) or "?"}: only \\old(e) and \\at(e, Pre) '
                                   'are allowed')
        elif text in FLOAT_BUILTINS or (text.startswith('\\') and re.search(r'float|double|round|NaN|infinit', text)):
            reasons.append(f'floating-point logic built-in {text} is not allowed; use real arithmetic')
        elif text in MEMORY_BUILTINS:
            reasons.append(f'memory built-in {text} is not allowed: only \\valid, \\initialized, \\separated and \\result')
        elif text == '\\everything':
            reasons.append('\\everything is not allowed; name the locations and index ranges')
        elif text == '\\let':
            reasons.append('\\let is not in the allowed ACSL subset')
        elif text.startswith('\\') and text not in ALLOWED_BUILTINS:
            reasons.append(f'built-in {text} is not in the allowed ACSL subset')
        elif text in ('float', 'double'):
            reasons.append(f'floating-point type {text} is not allowed; use real')
        elif (formal_half and tok.kind == 'id' and i + 1 < len(toks) and toks[i + 1].text == '{'
              and not text.startswith('\\')):
            labels = [t.text for t in toks[i + 2:_close(toks, i + 1)] if t.text != ',']
            if labels != ['Pre']:
                reasons.append(f'label application {text}{{{",".join(labels)}}}: only \\old(e) and \\at(e, Pre) '
                               'are allowed')
    return reasons


def _check_assigns(toks):
    reasons = []
    if any(t.text == '\\from' for t in toks):
        return ['\\from is not allowed in assigns']
    for loc in _split(toks, {','})[0]:
        words = _texts(loc)
        if words == ['\\everything']:
            reasons.append('assigns \\everything is not allowed; name the locations and index ranges')
            continue
        if words == ['\\nothing']:
            continue
        head = [w for w in words if w not in ('*', '(')]
        if not head or not re.fullmatch(r'[A-Za-z_]\w*', head[0]) or '{' in words:
            reasons.append(f'assigns location "{" ".join(words)}" is neither a range nor a single location')
            continue
        for j, word in enumerate(words):
            if word == '..' and (j == 0 or words[j - 1] in '([' or j + 1 >= len(words) or words[j + 1] in ')]'):
                reasons.append(f'assigns location "{" ".join(words)}" has an unbounded index range')
                break
        reasons += check_expression(loc)
    return reasons


@dataclass
class Definition:
    name: str
    kind: str            # logic, predicate, inductive, axiomatic (declared inside an axiomatic block), lemma
    entry: str
    params: list = field(default_factory=list)   # [(name, type tokens)]
    calls: set = field(default_factory=set)


def _head(toks):
    """(name, labels, params) of a definition head `T name{L}(params)`."""
    params, labels = [], []
    if toks and toks[-1].text == ')':
        depth = 0
        for j in range(len(toks) - 1, -1, -1):
            depth += toks[j].text == ')'
            depth -= toks[j].text == '('
            if depth == 0:
                break
        params = [(p[-1].text, p[:-1]) for p in _split(toks[j + 1:-1], {','})[0] if p]
        toks = toks[:j]
    opens = [k for k, t in enumerate(toks) if t.text == '{']
    if toks and toks[-1].text == '}' and opens:
        j = opens[-1]
        labels = [t.text for t in toks[j + 1:-1] if t.text != ',']
        toks = toks[:j]
    return (toks[-1].text if toks else '?'), labels, params


def _primitive_recursive(definition, body):
    """True when every recursive call takes `n - 1` of one integer parameter `n` under `n <= 0`."""
    calls = [args for name, args in _calls(body) if name == definition.name]
    for index, (param, kind) in enumerate(definition.params):
        words = _texts(kind)
        if not words or any(w not in INTEGER_TYPES for w in words):
            continue
        if not all(len(args) > index and _texts(args[index]) == [param, '-', '1'] for args in calls):
            continue
        stripped = _strip(body)
        base = None
        parts, seps = _split(stripped, {'?'})
        if seps:
            question = len(parts[0])
            depth, nest, colon = 0, 0, None
            for j in range(question + 1, len(stripped)):
                text = stripped[j].text
                depth += text in OPEN
                depth -= text in CLOSE
                if depth == 0 and text == '?':
                    nest += 1
                elif depth == 0 and text == ':':
                    if nest == 0:
                        colon = j
                        break
                    nest -= 1
            if colon is not None:
                base = (stripped[:question], stripped[question + 1:colon])
        else:
            disjuncts, ors = _split(stripped, {'||'})
            if ors:
                base = (disjuncts[0], [])
        if base is None:
            continue
        cond, then = base
        if _texts(_strip(cond)) not in ([param, '<=', '0'], ['0', '>=', param]):
            continue
        if any(name == definition.name for name, _ in _calls(cond + then)):
            continue
        return True
    return False


class LogicLibrary:
    """Every logic-library file of a library: {entry ID: text}. `problems[entry]` lists
    (field, reason) for each file; `definitions` maps each defined name to its Definition."""

    def __init__(self, files):
        self.files = dict(files)
        self.problems = {entry: [] for entry in self.files}
        self.definitions = {}
        bodies = {}
        for entry, text in sorted(self.files.items()):
            try:
                toks = tokens(text)
            except AcslSyntaxError as exc:
                self.problems[entry].append(('-', f'not ACSL: {exc}'))
                continue
            self._parse(entry, toks, bodies)
        graph = {name: d.calls & set(self.definitions) for name, d in self.definitions.items()}
        for name, definition in self.definitions.items():
            if definition.kind not in ('logic', 'predicate'):
                continue
            body = bodies.get(name)
            if name in definition.calls and not _primitive_recursive(definition, body):
                self.problems[definition.entry].append((
                    name, f'{name} is recursive but not primitive recursive: each recursive call must take '
                          'n - 1 of an integer parameter n, under a base case n <= 0 (map 16 item 2)'))
            partners = sorted(other for other in self._reach(graph, name) - {name}
                              if name in self._reach(graph, other))
            if partners:
                self.problems[definition.entry].append((
                    name, f'mutual recursion between {name} and {", ".join(partners)} is not allowed: the '
                          'syntactic termination rule sees one definition at a time'))

    @staticmethod
    def _reach(graph, start):
        seen, stack = set(), [start]
        while stack:
            for nxt in graph.get(stack.pop(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def _define(self, definition):
        if definition.name in self.definitions:
            self.problems[definition.entry].append((definition.name, f'{definition.name} is already defined in '
                                                    f'{self.definitions[definition.name].entry}'))
        else:
            self.definitions[definition.name] = definition

    def _parse(self, entry, toks, bodies):
        report = self.problems[entry]
        i = 0
        while i < len(toks):
            word = toks[i].text
            if word in ('inductive', 'axiomatic'):
                brace = next((j for j in range(i, len(toks)) if toks[j].text == '{'), len(toks))
                close = _close(toks, brace)
                name, _, params = _head(toks[i + 1:brace])
                if word == 'inductive':
                    self._define(Definition(name, 'inductive', entry, params,
                                            {n for n, _ in _calls(toks[brace:close])}))
                else:
                    report.append((name, f'axiomatic block {name}: no axiom anywhere; an unproven fact is an '
                                         'assumption-set entry (map 16 item 2)'))
                    inner = toks[brace + 1:close]
                    k = 0
                    while k < len(inner):
                        end = _statement_end(inner, k)
                        if inner[k].text in ('logic', 'predicate'):
                            stmt = inner[k + 1:end]
                            eq = next((j for j, t in enumerate(stmt) if t.text == '='), len(stmt))
                            self._define(Definition(_head(stmt[:eq])[0], 'axiomatic', entry))
                        k = end + 1
                i = close + 1
                continue
            end = _statement_end(toks, i)
            stmt = toks[i + 1:end]
            if word in ('logic', 'predicate'):
                eq = next((j for j, t in enumerate(stmt) if t.text == '=' ), None)
                name, labels, params = _head(stmt[:eq] if eq is not None else stmt)
                if eq is None:
                    report.append((name, f'{name} is declared without a definition; only an axiom could define '
                                         'it, and axioms are not allowed'))
                else:
                    body = stmt[eq + 1:]
                    bodies[name] = body
                    self._define(Definition(name, word, entry, params, {n for n, _ in _calls(body)}))
                    report.extend((name, f'{name}: {reason}') for reason in check_expression(body, formal_half=False))
            elif word == 'lemma':
                colon = next((j for j, t in enumerate(stmt) if t.text == ':'), 0)
                name = _head(stmt[:colon])[0]
                self.definitions.setdefault(f'lemma {name}', Definition(name, 'lemma', entry))
            elif word == 'axiom':
                report.append((_texts(stmt[:1])[0] if stmt else '-', 'axiom is not allowed anywhere; an unproven '
                               'fact is an assumption-set entry (map 16 item 2)'))
            else:
                report.append(('-', f'"{word}" is not allowed in a logic-library file (logic and predicate '
                                    'definitions, inductive definitions and lemmas only)'))
            i = end + 1

    def reach(self, names):
        """Every defined name reachable from `names` through definition bodies (with themselves)."""
        graph = {name: d.calls & set(self.definitions) for name, d in self.definitions.items()}
        found = set()
        for name in names:
            if name in self.definitions:
                found |= {name} | self._reach(graph, name)
        return found


def check_formal_half(text, uses, logic):
    """Reasons one formal half (`acsl.text` with its `acsl.uses` entries) breaks the subset."""
    try:
        toks = tokens(text)
    except AcslSyntaxError as exc:
        return [f'not ACSL: {exc}']
    reasons, calls, local, i = [], set(), set(), 0
    while i < len(toks):
        word = toks[i].text
        if word == 'behavior':
            return reasons + ['a named behavior is not allowed: only requires, ensures and assigns clauses']
        if word in ('inductive', 'axiomatic'):
            brace = next((j for j in range(i, len(toks)) if toks[j].text == '{'), len(toks))
            name = _head(toks[i + 1:brace])[0]
            local.add(name)
            reasons.append(f'inductive definition {name} written in a formal half: inductive definitions belong '
                           'only in logic-library lemmas' if word == 'inductive' else
                           f'axiomatic block {name} with an axiom in a formal half: no axiom anywhere')
            i = _close(toks, brace) + 1
            continue
        end = _statement_end(toks, i)
        body = toks[i + 1:end]
        if word in ('logic', 'predicate', 'lemma', 'type'):
            eq = next((j for j, t in enumerate(body) if t.text in ('=', ':')), len(body))
            name = _head(body[:eq])[0]
            local.add(name)
            reasons.append(f'{word} {name} is defined in the formal half itself: a formal half may call only '
                           'definitions of the logic-library entries it lists')
        elif word == 'axiom':
            reasons.append('axiom in a formal half: no axiom anywhere; an unproven fact is an assumption-set entry')
        elif word in CLAUSES:
            if end >= len(toks):
                reasons.append(f'{word} clause without a closing ";"')
            if word == 'assigns':
                reasons += _check_assigns(body)
            else:
                reasons += check_expression(body)
                calls |= {name for name, _ in _calls(body)}
        elif word in OTHER_CLAUSES:
            reasons.append(f'clause kind {word} is not allowed: only requires, ensures and assigns')
        else:
            reasons.append(f'expected a requires, ensures or assigns clause, found "{word}"')
        i = end + 1
    listed = {}
    for entry in uses:
        if entry not in logic.files:
            reasons.append(f'unknown logic-library entry {entry}')
            continue
        for _, reason in logic.problems[entry]:
            reasons.append(f'uses {entry}, which breaks the logic-library rules: {reason}')
            break
        listed.update({name: d for name, d in logic.definitions.items() if d.entry == entry})
    for name in sorted(calls - local):
        definition = listed.get(name)
        if definition is None:
            reasons.append(f'calls {name}, which no listed logic-library entry defines (acsl.uses)')
            continue
        for reached in sorted(logic.reach([name])):
            kind = logic.definitions[reached].kind
            via = f'calls {name}, which reaches' if reached != name else 'calls'
            if kind == 'inductive':
                reasons.append(f'{via} the inductive predicate {reached} '
                               f'({logic.definitions[reached].entry}): inductive definitions belong only in '
                               'logic-library lemmas, since their executable form can loop')
            elif kind == 'axiomatic':
                reasons.append(f'{via} {reached}, defined only by an axiom '
                               f'({logic.definitions[reached].entry})')
    return reasons
