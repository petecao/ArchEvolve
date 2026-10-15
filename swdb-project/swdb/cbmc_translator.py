"""The CBMC translator: formal halves (ACSL) to C, as a bounded-job harness and summary stubs.

Created: 2026-10-14 ET (Probata proof of concept ticket 22, the CBMC adapter; Yan-Ru's 13:19 ET decision made
CBMC 6.11 on ticket 21's C lowering the bounded verifier). Design: formal-verification map 11 items 1-4 and 8,
16 items 1 and 3, 19 items 2 and 8. Reference: prototype/06c-cbmc/ and the shared note cbmc-two-lanes.md.
Format: docs/reference/format-v0.4-cbmc.md.

Deterministic code, never an LLM: the same formal halves, interface and bounds give byte-identical C.

- Harness (the proof unit's check): every input is drawn from one oracle (`swdb_next()`), the size bounds and
  the `requires` clauses are assumed, `\\old` values are snapshotted, the unit is called, and each `ensures`
  clause and each `assigns` clause's frame is one named property. `swdb_reach.end` is a reachability assert
  that must FAIL (else the assumptions are contradictory: a vacuous pass).
- Summary stub (a called library entry's formal halves): each `requires` is one named CHECK (assert, then
  assume), the `assigns` locations are havocked from the oracle, the `ensures` clauses are assumed, and
  `swdb_reach.summary.<function>` must FAIL too. Stubs are the only place a generated `assume` follows a call.
- Model hooks (ticket 25, swdb.std_models): `SWDB_MODEL_REQUIRE` (a model precondition, such as `operator[]`'s
  `n < size()`: a named CHECK under CBMC, nothing natively, where libc++ does not check either) and
  `SWDB_MODEL_FAIL` (what the C++ does by throwing, such as `at` out of range: a failed CHECK; the C++ side's
  harness catches the `std::out_of_range` and prints the same failed check).
- One text compiles three ways: `-DSWDB_CBMC` (CBMC), `-DSWDB_NATIVE -DSWDB_DIFFERENTIAL` (the C-versus-C++
  differential run on the bounded domain) and `-DSWDB_NATIVE -DSWDB_REPLAY` (counterexample replay). Natively
  the oracle is read from stdin, one run per line, so a CBMC counterexample replays as the oracle values its
  trace shows.

ACSL subset translated (a subset of swdb.acsl_subset's formal-half subset; anything else raises
`Untranslatable`, failure class unsupported_construct): `requires`, `ensures`, `assigns`; integer arithmetic
(+ - * / %, evaluated in `long long`), comparisons (chained), `!`, `&&`, `||`, `==>`, `<==>`, array reads,
`\\result`, `\\true`, `\\false`, `\\old(e)` and `\\at(e, Pre)` (harness only; in a stub only over parameters),
`\\valid(p)`, `\\valid(p + i)`, `\\valid(p + (lo .. hi))`, `\\forall`/`\\exists` over one integer variable with
both bounds in the guard. Not yet: logic-library calls (ticket 26), `\\separated`, `\\null`, ternaries,
bitwise operators.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from swdb import acsl_subset, std_models

TOOL_ID = "swdb-cbmc-translator"
TOOL_VERSION = "2"                  # bump on any change to what the translator prints (2: ticket 25's model hooks)
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

@dataclass(frozen=True)
class Interface:
    """One C function as the C lowering gives it."""
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


def element_type(ctype):
    """`const int *` -> `int` (pointer to pointer: refused)."""
    head, _, tail = ctype.partition("*")
    if "*" in tail:
        raise Untranslatable(f"pointer-to-pointer parameter type {ctype}")
    return " ".join(w for w in head.split() if w not in ("const", "volatile"))


# --- expressions ------------------------------------------------------------------------------------------

class _Expr:
    """Recursive descent over ACSL tokens, printing C. Integer leaves are cast to long long."""

    RELATIONS = ("<", "<=", ">", ">=", "==", "!=")

    def __init__(self, toks, ctx):
        self.toks, self.i, self.ctx = toks, 0, ctx

    def parse(self):
        text = self.implies()
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
        parts = [f"({operands[k]} {op} {operands[k + 1]})" for k, op in enumerate(operators)]
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
            inner = self.implies()
            self.take(")")
            return f"({inner})"
        if tok in ("\\forall", "\\exists"):
            return self.quantifier()
        if tok in ("\\old", "\\at"):
            return self.old()
        if tok == "\\valid":
            return self.valid()
        if tok == "\\result":
            self.take()
            if self.ctx.result is None:
                raise Untranslatable("\\result outside an ensures clause of a function that returns a value")
            return f"((long long)({self.ctx.result}))"
        if tok in ("\\true", "\\false"):
            self.take()
            return "1" if tok == "\\true" else "0"
        if tok.startswith("\\"):
            raise Untranslatable(f"built-in {tok} is not translated yet")
        if tok[0].isdigit():
            self.take()
            digits = tok.rstrip("uUlL")
            if not digits.isdigit():
                raise Untranslatable(f"number {tok}")
            return f"{digits}LL"
        if tok[0].isalpha() or tok[0] == "_":
            self.take()
            if self.peek() == "(":
                raise Untranslatable(f"logic call {tok}(...) is not translated yet (logic library, ticket 26)")
            if self.peek() == "[":
                self.take()
                index = self.implies()
                self.take("]")
                return f"((long long)({self.ctx.array(tok)}[{index}]))"
            return f"((long long)({self.ctx.name(tok)}))"
        raise Untranslatable(f"unexpected {tok!r} in {self._show()}")

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
        return _Expr(inner, self.ctx.at_old()).parse()

    def valid(self):
        self.take()
        self.take("(")
        pointer = self.take()
        if not self.ctx.interface_pointer(pointer):
            raise Untranslatable(f"\\valid of {pointer}, which is not a pointer parameter")
        if self.peek() == ")":
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
        self.take(")")
        return self.ctx.valid(pointer, low, high)

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
        rest = self.toks[self.i:]
        self.i = len(self.toks)                          # a binder extends as far right as possible
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
        remaining = []
        for conjunct in conjuncts:
            bounds = _bounds(conjunct, variable, ctx)
            if bounds is None:
                remaining.append(conjunct)
                continue
            low = bounds[0] if bounds[0] is not None else low
            high = bounds[1] if bounds[1] is not None else high
        if low is None or high is None:
            raise Untranslatable(f"{word} {variable} needs both bounds in its guard ({self._show()})")
        if word == "\\forall":
            guard_text = " && ".join(_Expr(c, ctx).parse() for c in remaining) or "1"
            check = _Expr(body, ctx).parse()
        else:
            if not remaining:
                raise Untranslatable(f"\\exists {variable} with no body")
            check = " && ".join(_Expr(c, ctx).parse() for c in remaining)
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
    """What names mean where an expression is translated."""

    def __init__(self, interface, mode, result=None, old=False, bound=(), counter=None, caps=None):
        self.interface, self.mode, self.result, self.is_old = interface, mode, result, old
        self.bound = tuple(bound)
        self.counter = counter if counter is not None else [0]
        self.caps = caps or {}

    def bind(self, variable):
        return Context(self.interface, self.mode, self.result, self.is_old, (*self.bound, variable), self.counter,
                       self.caps)

    def at_old(self):
        return Context(self.interface, self.mode, self.result, True, self.bound, self.counter, self.caps)

    def interface_pointer(self, name):
        return self.interface.pointer(name) is not None

    def name(self, word):
        if word in self.bound or self.interface.scalar(word):
            return word                                  # parameters are passed by value: \old(p) == p
        if self.interface.global_scalar(word):
            if self.is_old:
                if self.mode != "harness":
                    raise Untranslatable(f"\\old({word}) of a global in a summary is not translated yet (ticket 23)")
                return f"swdb_old_{word}"
            return word
        if self.interface.pointer(word):
            raise Untranslatable(f"pointer {word} used as a value (only {word}[i] and \\valid({word} ...))")
        raise Untranslatable(f"name {word} is neither a parameter nor a global of {self.interface.function}")

    def array(self, word):
        if not self.interface.pointer(word):
            raise Untranslatable(f"{word}[...] where {word} is not a pointer parameter of {self.interface.function}")
        if self.is_old:
            if self.mode != "harness":
                raise Untranslatable(f"\\old({word}[...]) in a summary is not translated yet (ticket 23)")
            return f"swdb_old_{word}"
        return word

    def valid(self, pointer, low, high):
        if self.mode == "harness":
            return f"({low} > {high} || (0 <= {low} && {high} < {self.caps[pointer]}LL))"
        return f"SWDB_WRITABLE({pointer}, {low}, {high})"


def expression(text, interface, mode, result=None, caps=None, counter=None):
    """The C of one ACSL predicate or term (mode `harness` or `stub`)."""
    toks = _tokens(text)
    if not toks:
        raise Untranslatable("empty formal half")
    return _Expr(toks, Context(interface, mode, result, counter=counter, caps=caps)).parse()


# --- assigns ---------------------------------------------------------------------------------------------

def locations(text, interface, mode, caps=None, counter=None):
    """[(kind, name, low, high)] of an assigns clause: kind `range` (pointer elements low..high inclusive, in the
    pre-state) or `global`; [] for \\nothing. Parameters named alone are local copies and ignored."""
    toks = _tokens(text)
    if [t.text for t in toks] == ["\\nothing"]:
        return []
    ctx = Context(interface, mode, counter=counter, caps=caps).at_old()
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


PRELUDE = r"""/* Generated by {tool}: the CBMC harness prelude (one text for CBMC, the differential run and replay). */
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#if defined(SWDB_CBMC)
#define SWDB_CHECK(c, name) do {{ int swdb_c_ = (c); __CPROVER_assert(swdb_c_, name); __CPROVER_assume(swdb_c_); }} while (0)
#define SWDB_ASSUME(c) __CPROVER_assume(c)
#define SWDB_PROP(c, name) __CPROVER_assert((c), name)
#define SWDB_REACH(name) __CPROVER_assert(0, name)
#define SWDB_WRITABLE(p, lo, hi) ((lo) > (hi) || __CPROVER_w_ok((p) + (lo), (size_t)((hi) - (lo) + 1) * sizeof(*(p))))
#define SWDB_MODEL_REQUIRE(c, name) SWDB_CHECK((c), name)
#define SWDB_MODEL_FAIL(name) SWDB_CHECK(0, name)
#else
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#if defined(__cplusplus)
#include <stdexcept>
#endif
static jmp_buf swdb_jump;
static void swdb_failed(const char *name) {{ printf(" fail=%s", name); }}
#define SWDB_CHECK(c, name) do {{ if (!(c)) {{ swdb_failed(name); longjmp(swdb_jump, 1); }} }} while (0)
#define SWDB_ASSUME(c) do {{ if (!(c)) longjmp(swdb_jump, 2); }} while (0)
#define SWDB_PROP(c, name) do {{ if (!(c)) swdb_failed(name); }} while (0)
#define SWDB_REACH(name) ((void)0)
#define SWDB_WRITABLE(p, lo, hi) 1
#define SWDB_MODEL_REQUIRE(c, name) ((void)0)
#define SWDB_MODEL_FAIL(name) SWDB_CHECK(0, name)
#endif
static long long *swdb_oracle;
static long long swdb_oracle_n, swdb_oracle_next;
static long long swdb_next(void) {{
  SWDB_CHECK(swdb_oracle_next < swdb_oracle_n, "{capacity}");
  return swdb_oracle[swdb_oracle_next++];
}}
"""


def prelude():
    return PRELUDE.format(tool=f"{TOOL_ID} {TOOL_VERSION}", capacity=ORACLE_CAPACITY)


def harness(interface, rows, *, sizes, cap, knobs=(), setup=(), state=()):
    """(C text of the harness, Plan) for the proof unit `interface` and its clause list `rows` (Clause).

    `sizes`: {parameter: bound} (each an integer parameter of the unit); `cap`: the length of every interface
    array; `knobs`: [(global name, legality condition as C text, (min, max))], drawn from the oracle and assumed
    legal (the range is the differential run's domain). Ticket 27: `setup` are C statements run first (a proof
    semantics' ghost initialization) and `state` the int lvalues of device state drawn next (havoc)."""
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
        lines.append(f"  {ctype} {name} = ({ctype}) swdb_next();")
        draw = {"name": name, "role": "size" if name in sizes else "value", "ctype": ctype}
        if name in sizes:
            draw["bound"] = sizes[name]
        plan.draws.append(draw)
    for name, ctype, pointer in interface.parameters:
        if not pointer:
            continue
        element = element_type(ctype)
        lines.append(f"  {element} swdb_buf_{name}[{max(cap, 1)}];")
        lines.append(f"  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) swdb_buf_{name}[swdb_k] = ({element}) swdb_next();")
        lines.append(f"  {ctype.replace('*', '').strip()} *{name} = swdb_buf_{name};")
        plan.draws += [{"name": f"{name}[{k}]", "role": "element", "ctype": element} for k in range(cap)]
    for name, _condition, legal in knobs:
        ctype = next(g[1] for g in interface.globals if g[0] == name)
        lines.append(f"  {name} = ({ctype}) swdb_next();")
        plan.draws.append({"name": name, "role": "knob", "ctype": ctype, "range": list(legal)})
    lines += [f"  {statement}" for statement in setup]
    for name in state:
        lines.append(f"  {name} = (int) swdb_next();")
        plan.draws.append({"name": name, "role": "state", "ctype": "int"})
    lines.append("#if defined(SWDB_REPLAY)")
    for draw in plan.draws:
        if draw["role"] == "element":
            pointer, index = draw["name"].split("[")
            lines.append(f'  printf(" input {draw["name"]}=%lld", (long long) swdb_buf_{pointer}[{index[:-1]}]);')
        else:
            lines.append(f'  printf(" input {draw["name"]}=%lld", (long long) {draw["name"]});')
    lines.append("#endif")
    for name, bound in sorted(sizes.items()):
        lines.append(f"  SWDB_ASSUME({name} <= {int(bound)}); /* size bound */")
    for name, condition, _legal in knobs:
        lines.append(f"  SWDB_ASSUME({condition}); /* legality of knob {name} */")
    for clause in rows:
        if clause.kind == "requires":
            text = expression(clause.text, interface, "harness", caps=caps, counter=counter)
            lines.append(f"  SWDB_ASSUME({text}); /* {clause.name} */")
    for name, ctype, pointer in interface.parameters:
        if pointer:
            element = element_type(ctype)
            lines.append(f"  {element} swdb_old_{name}[{max(cap, 1)}];")
            lines.append(f"  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) swdb_old_{name}[swdb_k] = swdb_buf_{name}[swdb_k];")
    for name, ctype in interface.globals:
        if ctype:
            lines.append(f"  {ctype} swdb_old_{name} = {name};")
    arguments = ", ".join(p[0] for p in interface.parameters)
    result = None
    if interface.returns != "void":
        result = "swdb_result"
        lines.append(f"  {interface.returns} swdb_result = {interface.function}({arguments});")
    else:
        lines.append(f"  {interface.function}({arguments});")
    for clause in rows:
        if clause.kind == "ensures":
            text = expression(clause.text, interface, "harness", result=result, caps=caps, counter=counter)
            lines.append(f'  SWDB_PROP({text}, "{clause.name}");')
        elif clause.kind == "assigns":
            lines.append(f'  SWDB_PROP({_frame(clause, interface, cap, caps, counter)}, "{clause.name}");')
    lines.append(f'  SWDB_REACH("{REACH_END}");')
    lines.append("#if defined(SWDB_DIFFERENTIAL)")
    if result:
        lines.append('  printf(" result=%lld", (long long) swdb_result);')
    for name, _ctype, pointer in interface.parameters:
        if pointer:
            lines.append(f'  for (int swdb_k = 0; swdb_k < {cap}; ++swdb_k) printf(" {name}[%d]=%lld", swdb_k, '
                         f'(long long) swdb_buf_{name}[swdb_k]);')
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
        "#else",
        "static char swdb_line[1 << 20];",
        f"static long long swdb_values[{plan.capacity}];",
        "int main(void) {",
        "  long long run = 0;",
        "  while (fgets(swdb_line, sizeof swdb_line, stdin)) {",
        "    char *at = swdb_line, *end;",
        "    long long count = 0;",
        f"    while (count < {plan.capacity}) {{ long long value = strtoll(at, &end, 10); if (end == at) break; "
        "swdb_values[count++] = value; at = end; }",
        "    swdb_oracle = swdb_values; swdb_oracle_n = count; swdb_oracle_next = 0;",
        "    printf(\"run %lld:\", run++);",
        "    int code = setjmp(swdb_jump);",
        "#if defined(__cplusplus)",            # ticket 25: the C++ of std::vector::at throws where the model fails a check
        "    if (code == 0) { try { swdb_run(); printf(\" end=done\\n\"); }",
        f"      catch (const std::out_of_range &) {{ swdb_failed(\"{std_models.OUT_OF_RANGE}\"); printf(\" end=check\\n\"); }} }}",
        "#else",
        "    if (code == 0) { swdb_run(); printf(\" end=done\\n\"); }",
        "#endif",
        "    else printf(\" end=%s\\n\", code == 1 ? \"check\" : \"infeasible\");",
        "    fflush(stdout);",
        "  }",
        "  return 0;",
        "}",
        "#endif"]
    return "\n".join(lines) + "\n", plan


def _frame(clause, interface, cap, caps, counter):
    """The frame of one assigns clause: every interface array element and scalar global outside it keeps its value."""
    found = locations(clause.text, interface, "harness", caps=caps, counter=counter)
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

def stub(interface, prototype, rows, entry_id, entry_sha256):
    """The C stub that replaces a summarized callee: CHECK each requires, havoc assigns, assume each ensures."""
    lines = [f"/* Generated by {TOOL_ID} {TOOL_VERSION}: summary stub of {interface.function} from library entry "
             f"{entry_id} (sha256 {entry_sha256}). */", f"{prototype} {{"]
    counter = [0]
    assigns = [c for c in rows if c.kind == "assigns"]
    if not assigns:
        raise Untranslatable(f"summary {entry_id} has no assigns clause (a summary must state what it writes)")
    for clause in rows:
        if clause.kind == "requires":
            lines.append(f'  SWDB_CHECK({expression(clause.text, interface, "stub", counter=counter)}, "{clause.name}");')
    havocs = []
    for clause in assigns:
        havocs += locations(clause.text, interface, "stub", counter=counter)
    for position, (kind, target, low, high) in enumerate(havocs):
        if kind == "global":
            ctype = next(g[1] for g in interface.globals if g[0] == target)
            lines.append(f"  {target} = ({ctype}) swdb_next();")
        else:
            element = element_type(interface.pointer(target)[1])
            lines.append(f"  {{ long long swdb_lo = {low}, swdb_hi = {high};")
            lines.append(f"    for (long long swdb_k = swdb_lo; swdb_k <= swdb_hi; ++swdb_k) {target}[swdb_k] = "
                         f"({element}) swdb_next(); }}")
    result = None
    if interface.returns != "void":
        result = "swdb_result"
        lines.append(f"  {interface.returns} swdb_result = ({interface.returns}) swdb_next();")
    for clause in rows:
        if clause.kind == "ensures":
            text = expression(clause.text, interface, "stub", result=result, counter=counter)
            lines.append(f"  SWDB_ASSUME({text}); /* assume from summary {entry_id} sha256 {entry_sha256[:16]}: "
                         f"{clause.name} */")
    lines.append(f'  SWDB_REACH("{REACH_SUMMARY}{interface.function}");')
    if result:
        lines.append("  return swdb_result;")
    lines.append("}")
    return "\n".join(lines) + "\n"
