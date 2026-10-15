"""The CBMC translator: formal halves (ACSL) to C, as a bounded-job harness and summary stubs.

Created: 2026-10-14 ET (Probata proof of concept ticket 22, the CBMC adapter; Yan-Ru's 13:19 ET decision made
CBMC 6.11 on ticket 21's C lowering the bounded verifier). Design: formal-verification map 11 items 1-4 and 8,
16 items 1 and 3, 19 items 2 and 8. Reference: prototype/06c-cbmc/ and the shared note cbmc-two-lanes.md.
Format: docs/reference/format-v0.4-cbmc.md.
Updated: 2026-10-14 ET (Probata PoC 23, the C-stub translator, fallbacks and check mode): `\\old` over memory
and globals in stubs (snapshotted on entry; under a quantifier, tabulated over its range), logic-library calls
(each definition becomes one C function), `\\separated`, ternaries, real-valued names and literals (`double`), a
crux-llvm build (`-DSWDB_CRUX`) and check mode (`runtime_form`, `-DSWDB_CHECK_MODE`: reals compared within the
kernel's certify tolerance). Format: docs/reference/format-v0.4-stubs-check-mode.md.

Deterministic code, never an LLM: the same formal halves, interface and bounds give byte-identical C.

- Harness (the proof unit's check): every input is drawn from one oracle (`swdb_next()`), the size bounds and
  the `requires` clauses are assumed, `\\old` values are snapshotted, the unit is called, and each `ensures`
  clause and each `assigns` clause's frame is one named property. `swdb_reach.end` is a reachability assert
  that must FAIL (else the assumptions are contradictory: a vacuous pass).
- Summary stub (a called library entry's formal halves): each `requires` is one named CHECK (assert, then
  assume), the `assigns` locations are havocked from the oracle, the `ensures` clauses are assumed, and
  `swdb_reach.summary.<function>` must FAIL too. Stubs are the only place a generated `assume` follows a call.
- One text compiles several ways: `-DSWDB_CBMC` (CBMC), `-DSWDB_CRUX` (crux-llvm), `-DSWDB_NATIVE
  -DSWDB_DIFFERENTIAL` (the C-versus-C++ differential run on the bounded domain), `-DSWDB_NATIVE -DSWDB_REPLAY`
  (counterexample replay) and `-DSWDB_NATIVE -DSWDB_CHECK_MODE` (check mode, C++ only). Natively
  the oracle is read from stdin, one run per line, so a CBMC counterexample replays as the oracle values its
  trace shows.

ACSL subset translated (a subset of swdb.acsl_subset's formal-half subset; anything else raises
`Untranslatable`, failure class unsupported_construct): `requires`, `ensures`, `assigns`; integer arithmetic
(+ - * / %, evaluated in `long long`; a name of floating type or a real literal in `double`), comparisons
(chained), `!`, `&&`, `||`, `==>`, `<==>`, array reads,
`\\result`, `\\true`, `\\false`, `\\old(e)` and `\\at(e, Pre)` (in a stub and in check mode snapshotted on entry),
`\\valid(p)`, `\\valid(p + i)`, `\\valid(p + (lo .. hi))`, `\\separated` of such locations, `c ? a : b`,
logic-library calls (non-recursive or primitive-recursive `logic`/`predicate` definitions, one label at most),
`\\forall`/`\\exists` over one integer variable with both bounds in the guard. Not yet: `\\null`, bitwise operators.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from swdb import acsl_subset

TOOL_ID = "swdb-cbmc-translator"
TOOL_VERSION = "2"                  # bump on any change to what the translator prints (23: 1 -> 2)
REACH_END = "swdb_reach.end"
REACH_SUMMARY = "swdb_reach.summary."
ORACLE_CAPACITY = "swdb.oracle_capacity"
HAVOC_BUDGET = 1024                 # oracle values beyond the inputs, for summary havocs


class Untranslatable(Exception):
    """A formal half outside the translated subset (failure class unsupported_construct)."""


def identity():
    """{id, sha256} of the translator itself (this module's source)."""
    return {"id": f"{TOOL_ID}-{TOOL_VERSION}", "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


# --- clauses -------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Clause:
    kind: str           # requires | ensures | assigns
    text: str           # the ACSL after the keyword, without the final ";"
    name: str           # <entry>#<clause id>, plus .<kind><n> when one formal half holds several statements


def clauses(entry_id, clause_rows):
    """The requires/ensures/assigns statements of the given clause rows, named after their entry and clause."""
    found = []
    for row in clause_rows:
        toks = _tokens(row["acsl"]["text"])
        statements, i = [], 0
        while i < len(toks):
            end = acsl_subset._statement_end(toks, i)
            word = toks[i].text
            if word not in ("requires", "ensures", "assigns"):
                raise Untranslatable(f"clause {row.get('id')}: {word} is not a requires, ensures or assigns clause")
            statements.append((word, " ".join(t.text for t in toks[i + 1:end])))
            i = end + 1
        seen = {}
        for word, text in statements:
            seen[word] = seen.get(word, 0) + 1
            suffix = f".{word}{seen[word]}" if len(statements) > 1 else ""
            found.append(Clause(word, text, f"{entry_id}#{row.get('id')}{suffix}"))
    return found


def _tokens(text):
    try:
        return acsl_subset.tokens(text)
    except acsl_subset.AcslSyntaxError as exc:
        raise Untranslatable(f"not ACSL: {exc}") from None


# --- the interface the translator sees ------------------------------------------------------------------

REAL_WORDS = ("float", "double", "real")


def is_real_type(ctype):
    """Whether a C or ACSL type names a floating or real value (ticket 23: such values are `double`)."""
    return any(word in REAL_WORDS for word in re.split(r"[\s*&]+", ctype or "") if word)


@dataclass(frozen=True)
class Interface:
    """One C function as the C lowering gives it (or, for a real-valued unit, as clang's syntax tree gives it)."""
    function: str
    returns: str                     # C return type ("void" for none)
    parameters: tuple                # (name, C type, is_pointer)
    globals: tuple = ()              # (name, C type of a scalar, or None for an array)

    def pointer(self, name):
        return next((p for p in self.parameters if p[0] == name and p[2]), None)

    def scalar(self, name):
        return any(p[0] == name and not p[2] for p in self.parameters)

    def global_scalar(self, name):
        return any(g[0] == name and g[1] for g in self.globals)

    def ctype(self, name):
        found = next((p[1] for p in self.parameters if p[0] == name), None)
        return found if found is not None else next((g[1] for g in self.globals if g[0] == name), None)

    @property
    def real_valued(self):
        return is_real_type(self.returns) or any(is_real_type(p[1]) for p in self.parameters)


def element_type(ctype):
    """`const int *` -> `int` (pointer to pointer: refused)."""
    head, _, tail = ctype.partition("*")
    if "*" in tail:
        raise Untranslatable(f"pointer-to-pointer parameter type {ctype}")
    return " ".join(w for w in head.split() if w not in ("const", "volatile"))


def _cast(ctype):
    return "double" if is_real_type(ctype) else "long long"


def real_valued(interface, rows):
    """A unit counts as real-valued when its interface or its formal halves use a floating type or `real`."""
    if interface is not None and interface.real_valued:
        return True
    for clause in rows:
        for tok in _tokens(clause.text):
            if tok.text in REAL_WORDS or tok.text == "\\real" or (tok.kind == "num" and re.search(r"[.eE]", tok.text)
                                                                    and not tok.text.lower().startswith("0x")):
                return True
    return False


# --- expressions ------------------------------------------------------------------------------------------

class _Expr:
    """Recursive descent over ACSL tokens, printing C. Integer leaves are cast to long long, real ones to double."""

    RELATIONS = ("<", "<=", ">", ">=", "==", "!=")

    def __init__(self, toks, ctx):
        self.toks, self.i, self.ctx = toks, 0, ctx
        self.real = False

    def sub(self, toks, ctx=None):
        """Translate `toks` in `ctx` (default: this context); a real leaf inside makes this expression real."""
        inner = _Expr(toks, ctx or self.ctx)
        text = inner.parse()
        self.real |= inner.real
        return text

    def parse(self):
        text = self.ternary()
        if self.i != len(self.toks):
            raise Untranslatable(f"unexpected {self.toks[self.i].text!r} in {self._show()}")
        return text

    def _show(self):
        return " ".join(t.text for t in self.toks)

    def peek(self, offset=0):
        at = self.i + offset
        return self.toks[at].text if at < len(self.toks) else None

    def take(self, expected=None):
        if self.i >= len(self.toks):
            raise Untranslatable(f"unexpected end of {self._show()}")
        tok = self.toks[self.i]
        if expected is not None and tok.text != expected:
            raise Untranslatable(f"expected {expected!r}, found {tok.text!r} in {self._show()}")
        self.i += 1
        return tok.text

    def ternary(self):
        condition = self.implies()
        if self.peek() == "?":
            self.take()
            then = self.ternary()
            self.take(":")
            other = self.ternary()
            return f"(({condition}) ? ({then}) : ({other}))"
        return condition

    def implies(self):
        left = self.equiv()
        if self.peek() == "==>":
            self.take()
            return f"(!({left}) || ({self.implies()}))"
        return left

    def equiv(self):
        left = self.disjunction()
        while self.peek() == "<==>":
            self.take()
            left = f"(!({left}) == !({self.disjunction()}))"
        return left

    def disjunction(self):
        left = self.conjunction()
        while self.peek() == "||":
            self.take()
            left = f"({left} || {self.conjunction()})"
        return left

    def conjunction(self):
        left = self.relation()
        while self.peek() == "&&":
            self.take()
            left = f"({left} && {self.relation()})"
        return left

    def relation(self):
        operands, operators = [self.additive()], []
        while self.peek() in self.RELATIONS:
            operators.append(self.take())
            operands.append(self.additive())
        if not operators:
            return operands[0]
        parts = []
        for k, op in enumerate(operators):
            left, right = operands[k], operands[k + 1]
            if self.ctx.mode == "check" and op in ("==", "!="):      # check mode: reals within the tolerance
                parts.append(f"({'' if op == '==' else '!'}SWDB_EQ({left}, {right}))")
            else:
                parts.append(f"({left} {op} {right})")
        return "(" + " && ".join(parts) + ")"

    def additive(self):
        left = self.multiplicative()
        while self.peek() in ("+", "-"):
            op = self.take()
            left = f"({left} {op} {self.multiplicative()})"
        return left

    def multiplicative(self):
        left = self.unary()
        while self.peek() in ("*", "/", "%"):
            op = self.take()
            left = f"({left} {op} {self.unary()})"
        return left

    def unary(self):
        if self.peek() in ("!", "-", "+"):
            op = self.take()
            return f"({op}{self.unary()})"
        if self.peek() in ("~", "&", "*"):
            raise Untranslatable(f"operator {self.peek()} is not translated yet")
        return self.postfix()

    def postfix(self):
        tok = self.peek()
        if tok is None:
            raise Untranslatable(f"unexpected end of {self._show()}")
        if tok == "(":
            self.take()
            inner = self.ternary()
            self.take(")")
            return f"({inner})"
        if tok in ("\\forall", "\\exists"):
            return self.quantifier()
        if tok in ("\\old", "\\at"):
            return self.old()
        if tok == "\\valid":
            return self.valid()
        if tok == "\\separated":
            return self.separated()
        if tok == "\\result":
            self.take()
            if self.ctx.result is None:
                raise Untranslatable("\\result outside an ensures clause of a function that returns a value")
            cast = _cast(self.ctx.result_type)
            self.real |= cast == "double"
            return f"(({cast})({self.ctx.result}))"
        if tok in ("\\true", "\\false"):
            self.take()
            return "1" if tok == "\\true" else "0"
        if tok.startswith("\\"):
            raise Untranslatable(f"built-in {tok} is not translated yet")
        if tok[0].isdigit() or (tok[0] == "." and len(tok) > 1):
            self.take()
            return self.number(tok)
        if tok[0].isalpha() or tok[0] == "_":
            self.take()
            if self.peek() == "{" or self.peek() == "(":
                return self.call(tok)
            if self.peek() == "[":
                self.take()
                index = self.ternary()
                self.take("]")
                base, ctype = self.ctx.array(tok)
                cast = _cast(element_type(ctype) if ctype else "")
                self.real |= cast == "double"
                return f"(({cast})({base}[{index}]))"
            text, ctype = self.ctx.name(tok)
            cast = _cast(ctype)
            self.real |= cast == "double"
            return f"(({cast})({text}))"
        raise Untranslatable(f"unexpected {tok!r} in {self._show()}")

    def number(self, tok):
        if tok.lower().startswith("0x"):
            raise Untranslatable(f"number {tok} (hexadecimal) is not translated yet")
        if re.search(r"[.eE]", tok):
            self.real = True
            digits = tok.rstrip("fFdDlL")
            if not re.fullmatch(r"(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?", digits):
                raise Untranslatable(f"number {tok}")
            return f"((double)({digits}))"
        digits = tok.rstrip("uUlL")
        if not digits.isdigit():
            raise Untranslatable(f"number {tok}")
        return f"{digits}LL"

    def call(self, name):
        """A logic-library call `name(args)` (an optional label `{L}` is read and ignored)."""
        if self.peek() == "{":
            close = acsl_subset._close(self.toks, self.i)
            if close - self.i > 2:
                raise Untranslatable(f"logic call {name} with more than one label")
            self.i = close + 1
        start = self.i
        close = acsl_subset._close(self.toks, start)
        if close >= len(self.toks):
            raise Untranslatable(f"unbalanced call {name}(... in {self._show()}")
        inner = self.toks[start + 1:close]
        self.i = close + 1
        args = acsl_subset._split(inner, {","})[0] if inner else []
        if self.ctx.logic is None:
            raise Untranslatable(f"logic call {name}(...) with no logic library in reach")
        definition = self.ctx.logic.definition(name)
        if len(args) != len(definition.params):
            raise Untranslatable(f"logic call {name} takes {len(definition.params)} arguments, not {len(args)}")
        texts = []
        for arg, (_pname, ptype, pointer) in zip(args, definition.params):
            if pointer:
                words = [t.text for t in arg]
                if len(words) != 1:
                    raise Untranslatable(f"logic call {name}: pointer argument {' '.join(words)} must be a pointer name")
                base, _ctype = self.ctx.array(words[0])
                texts.append(base)
            else:
                texts.append(f"(({ptype})({self.sub(arg)}))")
        cast = definition.returns
        self.real |= cast == "double"
        return f"(({cast}) {self.ctx.logic.use(name)}({', '.join(texts)}))"

    def old(self):
        word = self.take()
        self.take("(")
        start = self.i
        depth = 0
        while self.i < len(self.toks):
            text = self.toks[self.i].text
            if text in "([{":
                depth += 1
            elif text in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif text == "," and depth == 0:
                break
            self.i += 1
        inner = self.toks[start:self.i]
        if word == "\\at":
            self.take(",")
            label = self.take()
            if label != "Pre":
                raise Untranslatable(f"\\at with label {label} (only Pre)")
        self.take(")")
        ctx = self.ctx
        if ctx.mode == "logic":
            raise Untranslatable("\\old or \\at inside a logic definition")
        if ctx.mode == "harness" or ctx.pre is None:
            return self.sub(inner, ctx.at_old())
        return self.hoist(inner)

    def hoist(self, inner):
        """Stub and check mode: snapshot `\\old(inner)` on entry; under a quantifier, tabulate it over its range."""
        ctx = self.ctx
        names = {t.text for t in inner}
        free = [v for v in ctx.bound if v in names]
        before = self.real
        self.real = False
        text = self.sub(inner, ctx.pre_state(free))
        ctype = "double" if self.real else "long long"
        self.real |= before
        ctx.counter[0] += 1
        name = f"swdb_o{ctx.counter[0]}"
        if not free:
            ctx.pre.append(f"  {ctype} {name} = {text}; /* \\old snapshot on entry */")
            return f"({name})"
        dims = []
        for variable in free:
            low, high, bound_toks = ctx.ranges[variable]
            others = {t.text for t in bound_toks} & (set(ctx.bound) - {variable})
            if others:
                raise Untranslatable(f"\\old under quantifier {variable} whose bounds depend on {sorted(others)}: its range "
                                     "cannot be snapshotted on entry")
            if _post_state(bound_toks, ctx):
                raise Untranslatable(f"the bounds of quantifier {variable} depend on the post-state, so the \\old values "
                                     "under it cannot be snapshotted on entry")
            dims.append((variable, low, high))
        lines = []
        for j, (variable, low, high) in enumerate(dims):
            lines.append(f"  long long {name}_lo{j} = {low}, {name}_n{j} = ({high}) - ({low}); "
                         f"if ({name}_n{j} < 0) {name}_n{j} = 0;")
        size = " * ".join(f"{name}_n{j}" for j in range(len(dims)))
        lines.append(f"  {ctype} {name}[({size}) > 0 ? ({size}) : 1]; /* \\old snapshot on entry, tabulated */")
        flat = f"({dims[0][0]} - {name}_lo0)"
        for j, (variable, _low, _high) in enumerate(dims[1:], start=1):
            flat = f"(({flat}) * {name}_n{j} + ({variable} - {name}_lo{j}))"
        loops = "".join(f"for (long long {v} = {name}_lo{j}; {v} < {name}_lo{j} + {name}_n{j}; ++{v}) "
                        for j, (v, _l, _h) in enumerate(dims))
        lines.append(f"  {loops}{name}[{flat}] = {text};")
        ctx.pre.extend(lines)
        return f"({name}[{flat}])"

    def location(self):
        """(pointer, low, high) of `p`, `p + i` or `p + (lo .. hi)` (a pointer parameter)."""
        pointer = self.take()
        if not self.ctx.interface_pointer(pointer):
            raise Untranslatable(f"location {pointer} is not a pointer parameter")
        if self.peek() in (")", ","):
            low = high = "0LL"
        else:
            self.take("+")
            if self.peek() == "(" and self._has_range():
                self.take("(")
                low = self.additive()
                self.take("..")
                high = self.additive()
                self.take(")")
            else:
                low = high = self.additive()
        return pointer, low, high

    def valid(self):
        self.take()
        self.take("(")
        pointer, low, high = self.location()
        self.take(")")
        return self.ctx.valid(pointer, low, high)

    def separated(self):
        self.take()
        self.take("(")
        found = [self.location()]
        while self.peek() == ",":
            self.take()
            found.append(self.location())
        self.take(")")
        if len(found) < 2:
            raise Untranslatable("\\separated needs at least two locations")
        pairs = []
        for k, (p, plo, phi) in enumerate(found):
            for q, qlo, qhi in found[k + 1:]:
                base_p, _ = self.ctx.array(p)
                base_q, _ = self.ctx.array(q)
                pairs.append(f"SWDB_SEPARATED({base_p}, {plo}, {phi}, {base_q}, {qlo}, {qhi})")
        return "(" + " && ".join(pairs) + ")"

    def _has_range(self):
        depth = 0
        for j in range(self.i, len(self.toks)):
            text = self.toks[j].text
            if text == "(":
                depth += 1
            elif text == ")":
                depth -= 1
                if depth == 0:
                    return False
            elif text == ".." and depth == 1:
                return True
        return False

    def quantifier(self):
        word = self.take()
        kind = self.take()
        if kind not in ("integer", "int", "long", "unsigned", "size_t", "char", "short"):
            raise Untranslatable(f"quantifier over {kind} (only integer types)")
        variable = self.take()
        if self.peek() == ",":
            raise Untranslatable("a quantifier binds one variable at a time here")
        self.take(";")
        end = acsl_subset._group_end(self.toks, self.i, len(self.toks))
        rest = self.toks[self.i:end]
        self.i = end                                     # a binder extends as far right as its enclosing group
        ctx = self.ctx.bind(variable)
        if word == "\\forall":
            parts, seps = acsl_subset._split(rest, {"==>"})
            if not seps:
                raise Untranslatable(f"\\forall {variable} without a guard (lo <= {variable} < hi ==> ...)")
            body = rest[len(parts[0]) + 1:]
            conjuncts = acsl_subset._split(acsl_subset._strip(parts[0]), {"&&"})[0]
        else:
            conjuncts, body = acsl_subset._split(acsl_subset._strip(rest), {"&&"})[0], None
        low = high = None
        remaining, bound_toks = [], []
        for conjunct in conjuncts:
            bounds = _bounds(conjunct, variable, ctx)
            if bounds is None:
                remaining.append(conjunct)
                continue
            bound_toks += list(conjunct)
            low = bounds[0] if bounds[0] is not None else low
            high = bounds[1] if bounds[1] is not None else high
        if low is None or high is None:
            raise Untranslatable(f"{word} {variable} needs both bounds in its guard ({self._show()})")
        if self.ctx.mode == "check" and self.ctx.post and _post_state(bound_toks, self.ctx):
            raise Untranslatable(f"check mode refuses quantifier {variable}: its bounds depend on the post-state "
                                 f"({' '.join(t.text for t in bound_toks)})")
        ctx = self.ctx.bind(variable, (low, high, bound_toks))
        if word == "\\forall":
            guard_text = " && ".join(self.sub(c, ctx) for c in remaining) or "1"
            check = self.sub(body, ctx)
        else:
            if not remaining:
                raise Untranslatable(f"\\exists {variable} with no body")
            check = " && ".join(self.sub(c, ctx) for c in remaining)
        self.ctx.counter[0] += 1
        flag = f"swdb_q{self.ctx.counter[0]}"
        if word == "\\forall":
            loop = f"if (({guard_text}) && !({check})) {{ {flag} = 0; break; }}"
            start = 1
        else:
            loop = f"if ({check}) {{ {flag} = 1; break; }}"
            start = 0
        return (f"({{ int {flag} = {start}; for (long long {variable} = {low}; {variable} < {high}; ++{variable}) "
                f"{loop} {flag}; }})")


def _post_state(toks, ctx):
    """Whether these tokens read the post-state outside `\\old`/`\\at`: `\\result`, a global, memory, a logic call
    on memory."""
    i = 0
    while i < len(toks):
        text = toks[i].text
        nxt = toks[i + 1].text if i + 1 < len(toks) else None
        if text in ("\\old", "\\at") and nxt == "(":
            i = acsl_subset._close(toks, i + 1) + 1
            continue
        if text == "\\result":
            return True
        if toks[i].kind == "id" and not text.startswith("\\"):
            if ctx.interface.global_scalar(text) or (nxt == "[" and ctx.interface.pointer(text)) or nxt in ("(", "{"):
                return True
        i += 1
    return False


def _bounds(conjunct, variable, ctx):
    """(low inclusive, high exclusive) C text that this conjunct gives `variable`, or None if it bounds nothing."""
    texts = [t.text for t in conjunct]
    ops = [k for k, t in enumerate(texts) if t in ("<", "<=", ">", ">=")]
    if not ops:
        return None
    pieces, start = [], 0
    for k in ops:
        pieces.append(conjunct[start:k])
        start = k + 1
    pieces.append(conjunct[start:])
    operators = [texts[k] for k in ops]
    low = high = None
    found = False
    for k, op in enumerate(operators):
        left, right = pieces[k], pieces[k + 1]
        if op in (">", ">="):                            # flip to < / <=
            left, right, op = right, left, "<" if op == ">" else "<="
        left_is = [t.text for t in left] == [variable]
        right_is = [t.text for t in right] == [variable]
        if right_is and not left_is:                     # lo < k / lo <= k
            value = _Expr(left, ctx).parse()
            low = value if op == "<=" else f"({value} + 1)"
            found = True
        elif left_is and not right_is:                   # k < hi / k <= hi
            value = _Expr(right, ctx).parse()
            high = value if op == "<" else f"({value} + 1)"
            found = True
        else:
            return None
    return (low, high) if found else None


class Context:
    """What names mean where an expression is translated.

    mode: harness | stub | check | logic. `pre` (stub and check mode, ensures only) collects the snapshots taken on
    entry; `ranges` gives each bound variable's (low, high, bound tokens); `post` is true inside an ensures clause."""

    def __init__(self, interface, mode, result=None, old=False, bound=(), counter=None, caps=None, logic=None,
                 ranges=None, pre=None, post=False, result_type=None):
        self.interface, self.mode, self.result, self.is_old = interface, mode, result, old
        self.bound = tuple(bound)
        self.counter = counter if counter is not None else [0]
        self.caps = caps or {}
        self.logic, self.ranges, self.pre, self.post = logic, dict(ranges or {}), pre, post
        self.result_type = result_type if result_type is not None else interface.returns

    def _copy(self, **changes):
        fields = dict(interface=self.interface, mode=self.mode, result=self.result, old=self.is_old, bound=self.bound,
                      counter=self.counter, caps=self.caps, logic=self.logic, ranges=self.ranges, pre=self.pre,
                      post=self.post, result_type=self.result_type)
        fields.update(changes)
        return Context(**fields)

    def bind(self, variable, rng=None):
        ranges = dict(self.ranges)
        if rng is not None:
            ranges[variable] = rng
        return self._copy(bound=(*self.bound, variable), ranges=ranges)

    def at_old(self):
        return self._copy(old=True)

    def pre_state(self, free):
        """The context of a snapshot taken on entry: the memory read is the pre-state; only `free` stay bound."""
        return self._copy(old=True, bound=tuple(free), ranges={}, pre=None, post=False, result=None)

    def interface_pointer(self, name):
        return self.interface.pointer(name) is not None

    def name(self, word):
        """(C text, C type) of a scalar name."""
        if word in self.bound:
            return word, "long long"
        if self.interface.scalar(word):
            return word, self.interface.ctype(word)          # parameters are passed by value: \old(p) == p
        if self.interface.global_scalar(word):
            ctype = self.interface.ctype(word)
            if self.mode == "logic":
                raise Untranslatable(f"global {word} inside a logic definition")
            if self.is_old and self.mode == "harness":
                return f"swdb_old_{word}", ctype
            return word, ctype
        if self.interface.pointer(word):
            raise Untranslatable(f"pointer {word} used as a value (only {word}[i] and \\valid({word} ...))")
        raise Untranslatable(f"name {word} is neither a parameter nor a global of {self.interface.function}")

    def array(self, word):
        """(C text of the base, pointer C type) of an array name."""
        found = self.interface.pointer(word)
        if not found:
            raise Untranslatable(f"{word}[...] where {word} is not a pointer parameter of {self.interface.function}")
        if self.is_old and self.mode == "harness":
            return f"swdb_old_{word}", found[1]
        return word, found[1]

    def valid(self, pointer, low, high):
        if self.mode == "harness":
            return f"({low} > {high} || (0 <= {low} && {high} < {self.caps[pointer]}LL))"
        return f"SWDB_WRITABLE({pointer}, {low}, {high})"


def expression(text, interface, mode, result=None, caps=None, counter=None, logic=None, pre=None, post=False):
    """The C of one ACSL predicate or term (mode `harness`, `stub` or `check`)."""
    toks = _tokens(text)
    if not toks:
        raise Untranslatable("empty formal half")
    return _Expr(toks, Context(interface, mode, result, counter=counter, caps=caps, logic=logic, pre=pre,
                               post=post)).parse()


# --- logic-library definitions ----------------------------------------------------------------------------

@dataclass
class LogicDefinition:
    name: str
    kind: str                     # logic | predicate
    returns: str                  # C type of the result: long long, double or int
    params: list                  # [(name, C type, is_pointer)]
    body: list                    # tokens


class Logic:
    """The logic-library files a job may call: each used definition becomes one C function `swdb_logic_<name>`.
    Definitions are read lazily: one this translator cannot print fails only the job that calls it."""

    def __init__(self, files):
        self.raw, self.definitions, self.used, self.texts = {}, {}, [], {}
        for entry, text in sorted((files or {}).items()):
            try:
                toks = acsl_subset.tokens(text)
            except acsl_subset.AcslSyntaxError:
                continue
            i = 0
            while i < len(toks):
                end = acsl_subset._statement_end(toks, i)
                word = toks[i].text
                stmt = toks[i + 1:end]
                if word in ("logic", "predicate"):
                    eq = next((j for j, t in enumerate(stmt) if t.text == "="), None)
                    if eq is not None:
                        name = acsl_subset._head(stmt[:eq])[0]
                        self.raw.setdefault(name, (entry, word, stmt[:eq], stmt[eq + 1:]))
                i = end + 1

    def definition(self, name):
        if name in self.definitions:
            return self.definitions[name]
        if name not in self.raw:
            raise Untranslatable(f"logic call {name}(...): no logic-library definition {name}")
        _entry, kind, head, body = self.raw[name]
        _name, labels, params = acsl_subset._head(head)
        if len(labels) > 1:
            raise Untranslatable(f"logic definition {name} has more than one label")
        if kind == "logic":
            at = next((j for j, t in enumerate(head) if t.text == name), 0)
            returns = _logic_type(head[:at], name)[0]
        else:
            returns = "int"
        found = []
        for pname, ptype in params:
            ctype, pointer = _logic_type(ptype, name)
            found.append((pname, ctype, pointer))
        self.definitions[name] = LogicDefinition(name, kind, returns, found, list(body))
        return self.definitions[name]

    def use(self, name):
        """The C name of logic definition `name`, translating it (and what it calls) on first use."""
        if name not in self.texts:
            self.texts[name] = None                    # recursion: the prototype comes first
            definition = self.definition(name)
            params = tuple((p, c, ptr) for p, c, ptr in definition.params)
            interface = Interface(function=f"logic {name}", returns=definition.returns, parameters=params)
            body = _Expr(definition.body, Context(interface, "logic", logic=self)).parse()
            self.texts[name] = (f"static {definition.returns} swdb_logic_{name}({self._params(definition)}) "
                                f"{{ return ({definition.returns})({body}); }}")
            self.used.append(name)
        return f"swdb_logic_{name}"

    @staticmethod
    def _params(definition):
        return ", ".join(f"{ctype} {pname}" for pname, ctype, _ptr in definition.params) or "void"

    def block(self):
        """C text of every used definition: prototypes first (recursion), then the definitions."""
        if not self.used:
            return ""
        lines = [f"/* Generated by {TOOL_ID} {TOOL_VERSION}: logic-library definitions used by the formal halves. */"]
        for name in sorted(self.used):
            lines.append(f"static {self.definitions[name].returns} swdb_logic_{name}"
                         f"({self._params(self.definitions[name])});")
        lines += [self.texts[name] for name in sorted(self.used)]
        return "\n".join(lines) + "\n"


def _logic_type(toks, name):
    """(C type, is_pointer) of an ACSL logic type: integer, int, ..., real, boolean, or `T *` (memory)."""
    words = [t.text for t in toks]
    if not words:
        raise Untranslatable(f"logic definition {name}: a parameter or result without a type")
    pointer = words[-1] == "*"
    base = [w for w in words if w not in ("*", "const")]
    if pointer:
        element = " ".join(base)
        if is_real_type(element):
            return f"const {element} *", True
        return f"const {element} *", True
    if any(w in REAL_WORDS for w in base):
        return "double", False
    if base in (["boolean"], ["_Bool"], ["bool"]):
        return "int", False
    if all(w in acsl_subset.INTEGER_TYPES for w in base):
        return "long long", False
    raise Untranslatable(f"logic definition {name}: type {' '.join(words)} is not translated")


# --- assigns ---------------------------------------------------------------------------------------------

def locations(text, interface, mode, caps=None, counter=None, logic=None):
    """[(kind, name, low, high)] of an assigns clause: kind `range` (pointer elements low..high inclusive, in the
    pre-state) or `global`; [] for \\nothing. Parameters named alone are local copies and ignored."""
    toks = _tokens(text)
    if [t.text for t in toks] == ["\\nothing"]:
        return []
    ctx = Context(interface, mode, counter=counter, caps=caps, logic=logic).at_old()
    found = []
    for part in acsl_subset._split(toks, {","})[0]:
        words = [t.text for t in part]
        if len(words) == 1 and interface.scalar(words[0]):
            continue
        if len(words) == 1 and interface.global_scalar(words[0]):
            found.append(("global", words[0], None, None))
            continue
        if len(words) >= 4 and words[1] == "[" and words[-1] == "]" and interface.pointer(words[0]):
            inner = part[2:-1]
            pieces, seps = acsl_subset._split(inner, {".."})
            if seps:
                if len(pieces) != 2 or not pieces[0] or not pieces[1]:
                    raise Untranslatable(f"assigns range {' '.join(words)} needs both bounds")
                low, high = (_Expr(p, ctx).parse() for p in pieces)
            else:
                low = high = _Expr(inner, ctx).parse()
            found.append(("range", words[0], low, high))
            continue
        raise Untranslatable(f"assigns location {' '.join(words)} is not translated yet")
    return found


# --- the harness ------------------------------------------------------------------------------------------

@dataclass
class Plan:
    """What one generated harness draws from the oracle, in order: [{name, role, ctype, bound?, range?}]."""
    draws: list = field(default_factory=list)
    capacity: int = 0

    @property
    def inputs(self):
        return len(self.draws)


PRELUDE = r"""/* Generated by @TOOL@: the harness prelude (one text for CBMC, crux-llvm, the differential run, replay and
   check mode). */
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#if defined(SWDB_CBMC)
#define SWDB_CHECK(c, name) do { int swdb_c_ = (c); __CPROVER_assert(swdb_c_, name); __CPROVER_assume(swdb_c_); } while (0)
#define SWDB_ASSUME(c) __CPROVER_assume(c)
#define SWDB_PROP(c, name) __CPROVER_assert((c), name)
#define SWDB_REACH(name) __CPROVER_assert(0, name)
#define SWDB_WRITABLE(p, lo, hi) ((lo) > (hi) || __CPROVER_w_ok((p) + (lo), (size_t)((hi) - (lo) + 1) * sizeof(*(p))))
#define SWDB_SAME_OBJECT(p, q) __CPROVER_same_object((p), (q))
#define SWDB_ADDR(p) ((long long) __CPROVER_POINTER_OFFSET(p))
#elif defined(SWDB_CRUX)
#include <crucible.h>
#define SWDB_CHECK(c, name) do { uint8_t swdb_c_ = (c) ? 1 : 0; crucible_assert(swdb_c_, name, __LINE__); crucible_assume(swdb_c_, name, __LINE__); } while (0)
#define SWDB_ASSUME(c) crucible_assume((uint8_t) ((c) ? 1 : 0), "swdb_assume", __LINE__)
#define SWDB_PROP(c, name) crucible_assert((uint8_t) ((c) ? 1 : 0), name, __LINE__)
#define SWDB_REACH(name) crucible_assert(0, name, __LINE__)
#define SWDB_WRITABLE(p, lo, hi) 1
#define SWDB_SAME_OBJECT(p, q) 1
#define SWDB_ADDR(p) ((long long) (uintptr_t) (p))
#else
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
static jmp_buf swdb_jump;
static void swdb_failed(const char *name) { printf(" fail=%s", name); }
#define SWDB_CHECK(c, name) do { if (!(c)) { swdb_failed(name); longjmp(swdb_jump, 1); } } while (0)
#define SWDB_ASSUME(c) do { if (!(c)) longjmp(swdb_jump, 2); } while (0)
#define SWDB_PROP(c, name) do { if (!(c)) swdb_failed(name); } while (0)
#define SWDB_REACH(name) ((void)0)
#define SWDB_WRITABLE(p, lo, hi) 1
#define SWDB_SAME_OBJECT(p, q) 1
#define SWDB_ADDR(p) ((long long) (uintptr_t) (p))
#endif
#define SWDB_SEPARATED(p, plo, phi, q, qlo, qhi) ((plo) > (phi) || (qlo) > (qhi) || !SWDB_SAME_OBJECT(p, q) || \
  SWDB_ADDR(p) + ((phi) + 1) * (long long) sizeof(*(p)) <= SWDB_ADDR(q) + (qlo) * (long long) sizeof(*(q)) || \
  SWDB_ADDR(q) + ((qhi) + 1) * (long long) sizeof(*(q)) <= SWDB_ADDR(p) + (plo) * (long long) sizeof(*(p)))
#if defined(SWDB_CHECK_MODE) && defined(__cplusplus)
#include <cmath>
#ifndef SWDB_TOLERANCE
#define SWDB_TOLERANCE 0.0
#endif
static inline bool swdb_eq(long long a, long long b) { return a == b; }
static inline bool swdb_eq(double a, double b) { return std::fabs(a - b) <= (double) (SWDB_TOLERANCE); }
static inline bool swdb_eq(long long a, double b) { return swdb_eq((double) a, b); }
static inline bool swdb_eq(double a, long long b) { return swdb_eq(a, (double) b); }
#define SWDB_EQ(a, b) swdb_eq((a), (b))
#else
#define SWDB_EQ(a, b) ((a) == (b))
#endif
#if defined(SWDB_CRUX)
static long long swdb_next(void) { return crucible_int64_t("swdb_oracle"); }
static double swdb_next_real(void) { return crucible_double("swdb_oracle_real"); }
#else
static long long *swdb_oracle;
static double *swdb_oracle_real;
static long long swdb_oracle_n, swdb_oracle_next;
static long long swdb_next(void) {
  SWDB_CHECK(swdb_oracle_next < swdb_oracle_n, "@CAPACITY@");
  return swdb_oracle[swdb_oracle_next++];
}
static double swdb_next_real(void) {
  SWDB_CHECK(swdb_oracle_next < swdb_oracle_n, "@CAPACITY@");
  return swdb_oracle_real[swdb_oracle_next++];
}
#endif
"""


def prelude():
    return PRELUDE.replace("@TOOL@", f"{TOOL_ID} {TOOL_VERSION}").replace("@CAPACITY@", ORACLE_CAPACITY)


def _draw(ctype):
    return "swdb_next_real()" if is_real_type(ctype) else "swdb_next()"


def _print(label, ctype, value):
    if is_real_type(ctype):
        return f'printf(" {label}=%.17g", (double) {value})'
    return f'printf(" {label}=%lld", (long long) {value})'


def harness(interface, rows, *, sizes, cap, knobs=(), logic=None, call=None, check=False):
    """(C text of the harness, Plan) for the proof unit `interface` and its clause list `rows` (Clause).

    `sizes`: {parameter: bound} (each an integer parameter of the unit); `cap`: the length of every interface
    array; `knobs`: [(global name, legality condition as C text, (min, max))], drawn from the oracle and assumed
    legal (the range is the differential run's domain). `logic`: the Logic of the job (logic-library calls).
    Check mode's driver (`check=True`) calls `call` (the runtime form) and states no property itself."""
    for name in sizes:
        if not interface.scalar(name):
            raise Untranslatable(f"size bound {name} is not an integer parameter of {interface.function}")
    plan = Plan()
    counter = [0]
    caps = {p[0]: cap for p in interface.parameters if p[2]}
    lines = [f"/* Generated by {TOOL_ID} {TOOL_VERSION}: the bounded-job harness of {interface.function}. */",
             "static void swdb_run(void) {"]
    for name, ctype, pointer in interface.parameters:
        if pointer:
            continue
        lines.append(f"  {ctype} {name} = ({ctype}) {_draw(ctype)};")
        draw = {"name": name, "role": "size" if name in sizes else "value", "ctype": ctype}
        if name in sizes:
            draw["bound"] = sizes[name]
        plan.draws.append(draw)
    for name, ctype, pointer in interface.parameters:
        if not pointer:
            continue
        element = element_type(ctype)
        lines.append(f"  {element} swdb_buf_{name}[{max(cap, 1)}];")
        lines.append(f"  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) swdb_buf_{name}[swdb_k] = ({element}) "
                     f"{_draw(element)};")
        lines.append(f"  {ctype.replace('*', '').strip()} *{name} = swdb_buf_{name};")
        plan.draws += [{"name": f"{name}[{k}]", "role": "element", "ctype": element} for k in range(cap)]
    for name, _condition, legal in knobs:
        ctype = next(g[1] for g in interface.globals if g[0] == name)
        lines.append(f"  {name} = ({ctype}) swdb_next();")
        plan.draws.append({"name": name, "role": "knob", "ctype": ctype, "range": list(legal)})
    lines.append("#if defined(SWDB_REPLAY)")
    for draw in plan.draws:
        if draw["role"] == "element":
            pointer, index = draw["name"].split("[")
            lines.append(f"  {_print('input ' + draw['name'], draw['ctype'], f'swdb_buf_{pointer}[{index[:-1]}]')};")
        else:
            lines.append(f"  {_print('input ' + draw['name'], draw['ctype'], draw['name'])};")
    lines.append("#endif")
    for name, bound in sorted(sizes.items()):
        lines.append(f"  SWDB_ASSUME({name} <= {int(bound)}); /* size bound */")
    for name, condition, _legal in knobs:
        lines.append(f"  SWDB_ASSUME({condition}); /* legality of knob {name} */")
    for clause in rows:
        if clause.kind == "requires":
            text = expression(clause.text, interface, "harness", caps=caps, counter=counter, logic=logic)
            lines.append(f"  SWDB_ASSUME({text}); /* {clause.name} */")
    if not check:
        for name, ctype, pointer in interface.parameters:
            if pointer:
                element = element_type(ctype)
                lines.append(f"  {element} swdb_old_{name}[{max(cap, 1)}];")
                lines.append(f"  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) swdb_old_{name}[swdb_k] = "
                             f"swdb_buf_{name}[swdb_k];")
        for name, ctype in interface.globals:
            if ctype:
                lines.append(f"  {ctype} swdb_old_{name} = {name};")
    arguments = ", ".join(p[0] for p in interface.parameters)
    target = call or interface.function
    result = None
    if interface.returns != "void":
        result = "swdb_result"
        lines.append(f"  {interface.returns} swdb_result = {target}({arguments});")
    else:
        lines.append(f"  {target}({arguments});")
    for clause in [] if check else rows:
        if clause.kind == "ensures":
            text = expression(clause.text, interface, "harness", result=result, caps=caps, counter=counter,
                              logic=logic, post=True)
            lines.append(f'  SWDB_PROP({text}, "{clause.name}");')
        elif clause.kind == "assigns":
            lines.append(f'  SWDB_PROP({_frame(clause, interface, cap, caps, counter, logic)}, "{clause.name}");')
    lines.append(f'  SWDB_REACH("{REACH_END}");')
    lines.append("#if defined(SWDB_DIFFERENTIAL)")
    if result:
        lines.append(f"  {_print('result', interface.returns, 'swdb_result')};")
    for name, ctype, pointer in interface.parameters:
        if pointer:
            element = element_type(ctype)
            lines.append(f'  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) printf(" {name}[%d]=%{".17g" if is_real_type(element) else "lld"}", '
                         f'swdb_k, ({"double" if is_real_type(element) else "long long"}) swdb_buf_{name}[swdb_k]);')
    for name, ctype in interface.globals:
        if ctype:
            lines.append(f'  printf(" {name}=%lld", (long long) {name});')
        else:
            lines.append(f'  for (size_t swdb_k = 0; swdb_k < sizeof({name}) / sizeof({name}[0]); ++swdb_k) '
                         f'printf(" {name}[%zu]=%lld", swdb_k, (long long) {name}[swdb_k]);')
    lines.append("#endif")
    lines.append("}")
    plan.capacity = plan.inputs + HAVOC_BUDGET
    lines += [
        "#if defined(SWDB_CBMC)",
        "int main(void) {",
        f"  long long swdb_values[{plan.capacity}];",
        f"  swdb_oracle = swdb_values; swdb_oracle_n = {plan.capacity}; swdb_oracle_next = 0;",
        "  swdb_run();",
        "  return 0;",
        "}",
        "#elif defined(SWDB_CRUX)",
        "int main(void) {",
        "  swdb_run();",
        "  return 0;",
        "}",
        "#else",
        "static char swdb_line[1 << 20];",
        f"static long long swdb_values[{plan.capacity}];",
        f"static double swdb_reals[{plan.capacity}];",
        "int main(void) {",
        "  long long run = 0;",
        "  while (fgets(swdb_line, sizeof swdb_line, stdin)) {",
        "    char *at = swdb_line, *end;",
        "    long long count = 0;",
        f"    while (count < {plan.capacity}) {{ double real = strtod(at, &end); if (end == at) break; "
        "swdb_values[count] = strtoll(at, NULL, 10); swdb_reals[count++] = real; at = end; }",
        "    swdb_oracle = swdb_values; swdb_oracle_real = swdb_reals; swdb_oracle_n = count; swdb_oracle_next = 0;",
        "    printf(\"run %lld:\", run++);",
        "    int code = setjmp(swdb_jump);",
        "    if (code == 0) { swdb_run(); printf(\" end=done\\n\"); }",
        "    else printf(\" end=%s\\n\", code == 1 ? \"check\" : \"infeasible\");",
        "    fflush(stdout);",
        "  }",
        "  return 0;",
        "}",
        "#endif"]
    return "\n".join(lines) + "\n", plan


def _frame(clause, interface, cap, caps, counter, logic=None):
    """The frame of one assigns clause: every interface array element and scalar global outside it keeps its value."""
    found = locations(clause.text, interface, "harness", caps=caps, counter=counter, logic=logic)
    checks = []
    for name, _ctype, pointer in interface.parameters:
        if not pointer:
            continue
        ranges = [f"(swdb_k >= {low} && swdb_k <= {high})" for kind, target, low, high in found
                  if kind == "range" and target == name]
        inside = " || ".join(ranges) if ranges else "0"
        counter[0] += 1
        flag = f"swdb_f{counter[0]}"
        checks.append(f"({{ int {flag} = 1; for (long long swdb_k = 0; swdb_k < {cap}; ++swdb_k) "
                      f"if (!({inside}) && {name}[swdb_k] != swdb_old_{name}[swdb_k]) {{ {flag} = 0; break; }} {flag}; }})")
    named = {target for kind, target, _l, _h in found if kind == "global"}
    for name, ctype in interface.globals:
        if ctype and name not in named:
            checks.append(f"({name} == swdb_old_{name})")
    return " && ".join(checks) if checks else "1"


# --- summary stubs ------------------------------------------------------------------------------------------

def stub(interface, prototype, rows, entry_id, entry_sha256, logic=None, drop=()):
    """The C stub that replaces a summarized callee: CHECK each requires, snapshot each `\\old` on entry, havoc
    assigns, assume each ensures (tagged with its summary: entry and sha256). `drop`: clause names left out (a
    scripted fault for the agreement negative control: a hand-weakened stub)."""
    lines = [f"/* Generated by {TOOL_ID} {TOOL_VERSION}: summary stub of {interface.function} from library entry "
             f"{entry_id} (sha256 {entry_sha256}). */", f"{prototype} {{"]
    counter, pre = [0], []
    assigns = [c for c in rows if c.kind == "assigns"]
    if not assigns:
        raise Untranslatable(f"summary {entry_id} has no assigns clause (a summary must state what it writes)")
    for clause in rows:
        if clause.kind == "requires":
            text = expression(clause.text, interface, "stub", counter=counter, logic=logic)
            lines.append(f'  SWDB_CHECK({text}, "{clause.name}");')
    result = "swdb_result" if interface.returns != "void" else None
    assumes = []
    for clause in rows:
        if clause.kind == "ensures" and clause.name not in drop:
            text = expression(clause.text, interface, "stub", result=result, counter=counter, logic=logic, pre=pre,
                              post=True)
            assumes.append(f"  SWDB_ASSUME({text}); /* assume from summary {entry_id} sha256 {entry_sha256[:16]}: "
                           f"{clause.name} */")
    lines += pre
    havocs = []
    for clause in assigns:
        havocs += locations(clause.text, interface, "stub", counter=counter, logic=logic)
    for kind, target, low, high in havocs:
        if kind == "global":
            ctype = interface.ctype(target)
            lines.append(f"  {target} = ({ctype}) {_draw(ctype)};")
        else:
            element = element_type(interface.pointer(target)[1])
            lines.append(f"  {{ long long swdb_lo = {low}, swdb_hi = {high};")
            lines.append(f"    for (long long swdb_k = swdb_lo; swdb_k <= swdb_hi; ++swdb_k) {target}[swdb_k] = "
                         f"({element}) {_draw(element)}; }}")
    if result:
        lines.append(f"  {interface.returns} swdb_result = ({interface.returns}) {_draw(interface.returns)};")
    lines += assumes
    lines.append(f'  SWDB_REACH("{REACH_SUMMARY}{interface.function}");')
    if result:
        lines.append("  return swdb_result;")
    lines.append("}")
    return "\n".join(lines) + "\n"


def stub_assumes(rows, drop=()):
    """The names of the `assume`s a stub of these clauses emits (the proof record lists them under the summary)."""
    return [c.name for c in rows if c.kind == "ensures" and c.name not in drop]


# --- check mode: the runtime form of formal halves ------------------------------------------------------------

def runtime_form(interface, rows, logic=None):
    """C++ text of `swdb_check_<f>`, the runtime form of the unit's formal halves: CHECK each requires (the
    caller's duty), snapshot each `\\old` value on entry (under a quantifier, over its range), call the unit, then
    check each ensures (bounded quantifiers as loops; `==` on reals within SWDB_TOLERANCE). An `assigns` clause
    has no runtime form (it names locations, not values). A quantifier bound that reads the post-state is refused."""
    counter, pre = [0], []
    result = "swdb_result" if interface.returns != "void" else None
    params = ", ".join(f"{ctype} {name}" for name, ctype, _pointer in interface.parameters) or "void"
    lines = [f"/* Generated by {TOOL_ID} {TOOL_VERSION}: the runtime form (check mode) of {interface.function}. */",
             f"static {interface.returns} swdb_check_{interface.function}({params}) {{"]
    checks = []
    for clause in rows:
        if clause.kind == "requires":
            lines.append(f'  SWDB_CHECK({expression(clause.text, interface, "check", counter=counter, logic=logic)}, '
                         f'"{clause.name}");')
        elif clause.kind == "ensures":
            text = expression(clause.text, interface, "check", result=result, counter=counter, logic=logic, pre=pre,
                              post=True)
            checks.append(f'  SWDB_PROP({text}, "{clause.name}");')
        else:
            checks.append(f"  /* {clause.name}: assigns has no runtime form */")
    lines += pre
    arguments = ", ".join(p[0] for p in interface.parameters)
    if result:
        lines.append(f"  {interface.returns} swdb_result = {interface.function}({arguments});")
    else:
        lines.append(f"  {interface.function}({arguments});")
    lines += checks
    if result:
        lines.append("  return swdb_result;")
    lines.append("}")
    return "\n".join(lines) + "\n"
