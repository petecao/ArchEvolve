# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/predicate_dsl/grammar.py; grammar only.
"""Lark grammar for the L3 Predicate DSL.

Source of truth: docs/superpowers/specs/2026-05-04-predicate-dsl-design.md §4.2.2 BNF.

Public API:
    parse(src: str) -> Predicate   — parse a DSL string; raises ParseError on failure.
    render(ast) -> str             — render an AST node back to a DSL string.
    ParseError                     — ValueError subclass wrapping lark.LarkError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union
from swdb._vendor import lark
from swdb._vendor.lark import Lark, LarkError, Transformer, Token

# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------
# Production layering encodes precedence (highest → lowest):
#   negation > conjunction > disjunction > implication > biconditional
# Reserved-word terminals carry priority .2 so they never lex as IDENT.
# FOR_EACH is the two-word "for each" synonym for forall; it gets priority .3
# to beat single-IDENT matches.
# FUNC_NAME is a closed alphabet; unknown function names will not match and
# cause a parse error (enforcing §4.2.1 governance).
# CMP_OP lists 2-char operators first to avoid the single-char prefix eating them.

_GRAMMAR = r"""
predicate     : biconditional

biconditional : implication ( BICOND implication )*
BICOND        : "<=>"

implication   : disjunction ( IMPL implication )?
IMPL          : "=>"

disjunction   : conjunction ( OR_LIT conjunction )*
conjunction   : negation ( AND_LIT negation )*
negation      : NOT_LIT negation
              | atom

atom          : quantified
              | membership
              | func_call
              | comparison
              | "(" predicate ")"

// ── Quantifiers ─────────────────────────────────────────────────────────────
quantified    : FORALL_LIT qvars (":" predicate)?
              | FOR_EACH   qvars (":" predicate)?
              | EXISTS_LIT qvars_exists (":" predicate)?

// qvars for forall/for-each: "i" | "i, j" | "k1 != k2" | "stmt in domain_ident"
NEQ_OP        : "!="
qvars         : IDENT IN_LIT IDENT   -> qvars_domain
              | IDENT NEQ_OP IDENT
              | IDENT ("," IDENT)?

// qvars for exists: "i" | "i in {0,1,2}" (bounded set membership form)
qvars_exists  : IDENT IN_LIT "{" set_lit ("," set_lit)* "}"
              | IDENT ("," IDENT)?

// ── Set membership ──────────────────────────────────────────────────────────
membership    : IDENT IN_LIT "{" set_lit ("," set_lit)* "}"
set_lit       : IDENT
              | INT

// ── Function calls ──────────────────────────────────────────────────────────
func_call     : FUNC_NAME "(" arg_list ")" cmp_result?
cmp_result    : EQ_OP (TRUE_LIT | FALSE_LIT)
EQ_OP         : "==" | "!="
arg_list      : arg_expr ("," arg_expr)*
arg_expr      : IDENT "[]"      -> array_arg
              | IDENT           -> scalar_arg

// ── Comparisons ─────────────────────────────────────────────────────────────
comparison    : chained_cmp
chained_cmp   : int_expr (CMP_OP int_expr)+
CMP_OP        : "<=" | ">=" | "==" | "!=" | "<" | ">"

// ── Integer expressions ─────────────────────────────────────────────────────
ARITH_OP      : "+" | "-"
int_expr      : int_term (ARITH_OP int_term)*
int_term      : INT
              | card_expr
              | index_expr
              | MIN_K_LIT "(" card_expr ")"
              | "(" int_expr ")"
              | IDENT

card_expr     : "|" IDENT "|"

// index_expr: IDENT[int_expr] | IDENT[int_expr][int_expr] | IDENT[index_expr]
index_expr    : IDENT "[" index_expr "]"
              | IDENT "[" int_expr "]" "[" int_expr "]"
              | IDENT "[" int_expr "]"

// ── Terminals ────────────────────────────────────────────────────────────────

// Closed function-name alphabet (§4.2.1 + §4.8.2 migration funcs).
// Must be declared BEFORE IDENT so the lexer prefers the longer keyword match.
FUNC_NAME.2   : "alias" | "aliasing" | "disjoint" | "dependence"
              | "writes_to" | "range" | "associative" | "commutative"
              | "exact" | "raw_dependence" | "writes"

// Reserved words — priority .2 so they never lex as IDENT.
FORALL_LIT.2  : "forall"
EXISTS_LIT.2  : "exists"
NOT_LIT.2     : "not"
AND_LIT.2     : "and"
OR_LIT.2      : "or"
IN_LIT.2      : "in"
TRUE_LIT.2    : "true"
FALSE_LIT.2   : "false"
MIN_K_LIT.2   : "min_k"

// "for each" as one atomic terminal (priority .3 beats single-IDENT, .2 words).
FOR_EACH.3    : "for each"

// Base terminals.
IDENT         : /[a-zA-Z_][a-zA-Z0-9_]*/
INT           : /0|[1-9][0-9]*/

%ignore /[ \t\r\n]+/
"""

_PARSER = Lark(_GRAMMAR, parser="earley", start="predicate")


# ---------------------------------------------------------------------------
# Public exceptions
# ---------------------------------------------------------------------------

class ParseError(ValueError):
    """Raised when a predicate DSL string fails to parse.

    Wraps ``lark.LarkError`` (and its subclasses ``UnexpectedInput``,
    ``UnexpectedToken``, etc.) as a plain ``ValueError`` so callers do not
    need to import lark themselves.
    """


# ---------------------------------------------------------------------------
# AST node definitions (§4.2.3)
# ---------------------------------------------------------------------------
# Type aliases for readability.
# Expr is the union of all expression-level nodes.
# Predicate is the union of all predicate-level nodes.

@dataclass(frozen=True)
class IntLit:
    """Integer literal — e.g. ``0``, ``1``."""
    value: int


@dataclass(frozen=True)
class Ident:
    """Bare identifier — e.g. ``n_distinct``, ``j``."""
    name: str


@dataclass(frozen=True)
class Card:
    """Cardinality expression — ``|name|``."""
    name: str


@dataclass(frozen=True)
class MinK:
    """``min_k(card)`` built-in."""
    inner: "Expr"


@dataclass(frozen=True)
class Add:
    """Addition — ``left + right``."""
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class Sub:
    """Subtraction — ``left - right``."""
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True)
class IndexExpr:
    """Array indexing — ``base[indices[0]][indices[1]]..."""
    base: str
    indices: tuple  # tuple[Expr, ...]


@dataclass(frozen=True)
class ArrayArg:
    """Array-typed function argument — ``name[]``."""
    name: str


@dataclass(frozen=True)
class ScalarArg:
    """Scalar-typed function argument — ``name``."""
    name: str


# Union alias for expression-level nodes.
Expr = Union[IntLit, Ident, Card, MinK, Add, Sub, IndexExpr]
# Union alias for argument nodes.
Arg = Union[ArrayArg, ScalarArg]


@dataclass(frozen=True)
class ChainedCmp:
    """Chained comparison — ``terms[k] ops[k] terms[k+1]...``.

    ``len(ops) == len(terms) - 1``.  Never desugared at parse time (§4.2.2 note 1).
    """
    terms: tuple  # tuple[Expr, ...]
    ops: tuple    # tuple[str, ...]


@dataclass(frozen=True)
class Membership:
    """Set membership — ``name in {members}``."""
    name: str
    members: tuple  # tuple[Expr, ...]


@dataclass(frozen=True)
class FuncCall:
    """Function call — ``name(args)`` or ``name(args) == false``.

    ``expect=False`` iff the source had ``== false``; default ``True``.
    ``== true`` also accepted but kept as ``expect=True``.
    """
    name: str
    args: tuple   # tuple[Arg, ...]
    expect: bool = True


@dataclass(frozen=True)
class Quantified:
    """Quantified formula.

    ``quant``      — one of ``"forall"``, ``"exists"``, ``"for each"``.
    ``vars``       — tuple of variable names.
    ``neq``        — True when the qvars form is ``v1 != v2``.
    ``bounded_in`` — non-None when the qvars form is ``i in {members}``.
    ``domain_in``  — non-None when the qvars form is ``var in domain_ident``
                     (domain-quantified forall/for-each, §4.8.2).
    ``body``       — the body predicate (may be None if no ``:`` was present).
    """
    quant: str  # Literal["forall", "exists", "for each"]
    vars: tuple   # tuple[str, ...]
    neq: bool
    bounded_in: tuple | None  # tuple[Expr, ...] | None
    body: "Predicate | None"
    domain_in: str | None = None  # identifier name of the domain (e.g. "evolve_region")


@dataclass(frozen=True)
class Not:
    """Negation — ``not inner``."""
    inner: "Predicate"


@dataclass(frozen=True)
class And:
    """Conjunction chain — ``parts[0] and parts[1] and ...``."""
    parts: tuple  # tuple[Predicate, ...]


@dataclass(frozen=True)
class Or:
    """Disjunction chain — ``parts[0] or parts[1] or ...``."""
    parts: tuple  # tuple[Predicate, ...]


@dataclass(frozen=True)
class Implication:
    """Implication — ``antecedent => consequent``."""
    antecedent: "Predicate"
    consequent: "Predicate"


@dataclass(frozen=True)
class Biconditional:
    """Biconditional chain — ``left[0] <=> left[1] <=> ...``."""
    left: tuple  # tuple[Predicate, ...]


# Union alias for predicate-level nodes.
Predicate = Union[
    Biconditional, Implication, Or, And, Not,
    Quantified, ChainedCmp, Membership, FuncCall,
]


# ---------------------------------------------------------------------------
# _AstBuilder — Lark Transformer
# ---------------------------------------------------------------------------

class _AstBuilder(Transformer):
    """Transforms a Lark ``Tree`` into AST dataclass nodes.

    Method names match Lark rule names; Lark auto-dispatches.
    Children arrive already transformed (bottom-up).
    """

    # ── Top-level wrapper ────────────────────────────────────────────────────

    def predicate(self, children):
        # predicate : biconditional  — transparent wrapper
        return children[0]

    # ── Connectives ──────────────────────────────────────────────────────────

    def biconditional(self, children):
        # biconditional : implication ( BICOND implication )*
        # Children: implication [BICOND implication ...] — tokens interleaved
        nodes = [c for c in children if not isinstance(c, Token)]
        if len(nodes) == 1:
            return nodes[0]
        return Biconditional(left=tuple(nodes))

    def implication(self, children):
        # implication : disjunction ( IMPL implication )?
        nodes = [c for c in children if not isinstance(c, Token)]
        if len(nodes) == 1:
            return nodes[0]
        return Implication(antecedent=nodes[0], consequent=nodes[1])

    def disjunction(self, children):
        # disjunction : conjunction ( OR_LIT conjunction )*
        nodes = [c for c in children if not isinstance(c, Token)]
        if len(nodes) == 1:
            return nodes[0]
        return Or(parts=tuple(nodes))

    def conjunction(self, children):
        # conjunction : negation ( AND_LIT negation )*
        nodes = [c for c in children if not isinstance(c, Token)]
        if len(nodes) == 1:
            return nodes[0]
        return And(parts=tuple(nodes))

    def negation(self, children):
        # negation : NOT_LIT negation | atom
        if len(children) == 2:
            # NOT_LIT negation
            return Not(inner=children[1])
        return children[0]

    def atom(self, children):
        # atom : quantified | membership | func_call | comparison | "(" predicate ")"
        # parenthesised form strips the parens — round-trip note below.
        return children[0]

    # ── Quantifiers ──────────────────────────────────────────────────────────

    def quantified(self, children):
        # quantified : FORALL_LIT qvars (":" predicate)?
        #            | FOR_EACH   qvars (":" predicate)?
        #            | EXISTS_LIT qvars_exists (":" predicate)?
        # children[0] = keyword Token, children[1] = qvars dict, children[2?] = body
        kw_tok = children[0]
        qvars_result = children[1]  # dict from qvars / qvars_exists
        body = children[2] if len(children) > 2 else None

        kw = str(kw_tok).strip()
        # Normalise "for each" → stored as "for each"; "forall" → "forall"
        quant: str = kw

        return Quantified(
            quant=quant,
            vars=qvars_result["vars"],
            neq=qvars_result.get("neq", False),
            bounded_in=qvars_result.get("bounded_in", None),
            body=body,
            domain_in=qvars_result.get("domain_in", None),
        )

    def qvars_domain(self, children):
        # qvars_domain : IDENT IN_LIT IDENT  (domain-quantified form, §4.8.2)
        # children: [IDENT(var), Token(IN_LIT), IDENT(domain)]
        idents = [str(c) for c in children if isinstance(c, Token) and c.type == "IDENT"]
        # idents[0] = var, idents[1] = domain
        return {"vars": (idents[0],), "neq": False, "bounded_in": None, "domain_in": idents[1]}

    def qvars(self, children):
        # qvars : IDENT IN_LIT IDENT -> qvars_domain | IDENT NEQ_OP IDENT | IDENT ("," IDENT)?
        # Note: qvars_domain is dispatched separately via alias; this handles the other two forms.
        idents = [str(c) for c in children if isinstance(c, Token) and c.type == "IDENT"]
        has_neq = any(isinstance(c, Token) and c.type == "NEQ_OP" for c in children)
        return {"vars": tuple(idents), "neq": has_neq, "bounded_in": None, "domain_in": None}

    def qvars_exists(self, children):
        # qvars_exists : IDENT IN_LIT "{" set_lit ("," set_lit)* "}" | IDENT ("," IDENT)?
        # Check if there's an IN_LIT token → bounded form
        has_in = any(isinstance(c, Token) and c.type == "IN_LIT" for c in children)
        if has_in:
            var = str(children[0])
            members = tuple(c for c in children if not isinstance(c, Token))
            return {"vars": (var,), "neq": False, "bounded_in": members}
        else:
            idents = [str(c) for c in children if isinstance(c, Token) and c.type == "IDENT"]
            return {"vars": tuple(idents), "neq": False, "bounded_in": None}

    # ── Set membership ───────────────────────────────────────────────────────

    def membership(self, children):
        # membership : IDENT IN_LIT "{" set_lit ("," set_lit)* "}"
        name = str(children[0])
        members = tuple(c for c in children[1:] if not isinstance(c, Token))
        return Membership(name=name, members=members)

    def set_lit(self, children):
        # set_lit : IDENT | INT
        tok = children[0]
        if tok.type == "INT":
            return IntLit(int(str(tok)))
        return Ident(str(tok))

    # ── Function calls ───────────────────────────────────────────────────────

    def func_call(self, children):
        # func_call : FUNC_NAME "(" arg_list ")" cmp_result?
        name = str(children[0])
        # children[1] is arg_list result (list of args), children[2?] is cmp_result
        args = children[1]
        expect = True
        if len(children) > 2:
            expect = children[2]  # bool from cmp_result
        return FuncCall(name=name, args=tuple(args), expect=expect)

    def cmp_result(self, children):
        # cmp_result : ("==" | "!=") (TRUE_LIT | FALSE_LIT)
        # children[0] = op token, children[1] = true/false token
        op = str(children[0])
        val_tok = str(children[1])
        literal_true = (val_tok == "true")
        if op == "==":
            return literal_true
        else:  # "!="
            return not literal_true

    def arg_list(self, children):
        # arg_list : arg_expr ("," arg_expr)*
        # Filter out comma tokens (Lark drops string literals automatically in earley)
        return [c for c in children if isinstance(c, (ArrayArg, ScalarArg))]

    def array_arg(self, children):
        # array_arg : IDENT "[]"
        return ArrayArg(name=str(children[0]))

    def scalar_arg(self, children):
        # scalar_arg : IDENT
        return ScalarArg(name=str(children[0]))

    # ── Comparisons ──────────────────────────────────────────────────────────

    def comparison(self, children):
        # comparison : chained_cmp — transparent
        return children[0]

    def chained_cmp(self, children):
        # chained_cmp : int_expr (CMP_OP int_expr)+
        # Children alternate: expr, Token(CMP_OP), expr, Token(CMP_OP), expr ...
        terms = []
        ops = []
        for c in children:
            if isinstance(c, Token) and c.type == "CMP_OP":
                ops.append(str(c))
            else:
                terms.append(c)
        return ChainedCmp(terms=tuple(terms), ops=tuple(ops))

    # ── Integer expressions ──────────────────────────────────────────────────

    def int_expr(self, children):
        # int_expr : int_term (("+" | "-") int_term)*
        # Children: term [op_tok term ...] — operators are anonymous string tokens
        # In Earley with ambiguous grammars, anon terminals may or may not appear.
        # We need to handle both Token and non-Token children.
        if len(children) == 1:
            return children[0]
        # Rebuild left-to-right: term (+|-) term (+|-) term ...
        result = children[0]
        i = 1
        while i < len(children):
            op_tok = children[i]
            rhs = children[i + 1]
            op_str = str(op_tok)
            if op_str == "+":
                result = Add(left=result, right=rhs)
            else:
                result = Sub(left=result, right=rhs)
            i += 2
        return result

    def int_term(self, children):
        # int_term : INT | card_expr | index_expr | MIN_K_LIT "(" card_expr ")" | "(" int_expr ")" | IDENT
        if len(children) == 1:
            c = children[0]
            if isinstance(c, Token):
                if c.type == "INT":
                    return IntLit(int(str(c)))
                # IDENT (bare variable)
                return Ident(str(c))
            # card_expr or index_expr already transformed
            return c
        # MIN_K_LIT "(" card_expr ")" — children: [Token(MIN_K_LIT), card_expr_result]
        # or "(" int_expr ")" — children: [int_expr_result]  (parens stripped by lark?)
        # When MIN_K_LIT is present:
        if any(isinstance(c, Token) and c.type == "MIN_K_LIT" for c in children):
            card = next(c for c in children if not isinstance(c, Token))
            return MinK(inner=card)
        # Parenthesised int_expr: just unwrap
        return children[0]

    def card_expr(self, children):
        # card_expr : "|" IDENT "|"
        return Card(name=str(children[0]))

    def index_expr(self, children):
        # index_expr : IDENT "[" index_expr "]"
        #            | IDENT "[" int_expr "]" "[" int_expr "]"
        #            | IDENT "[" int_expr "]"
        # children[0] is always the IDENT Token
        base = str(children[0])
        # Remaining non-Token children are the index expressions
        indices = tuple(c for c in children[1:] if not isinstance(c, Token))
        return IndexExpr(base=base, indices=indices)


# ---------------------------------------------------------------------------
# render — single-dispatch over AST node types
# ---------------------------------------------------------------------------

def render(ast) -> str:  # noqa: ANN001
    """Render *ast* back to a DSL string.

    Round-trip property (§4.6.1 + G6):
        `` " ".join(render(parse(s)).split()) == " ".join(s.split()) ``
    """
    return _render(ast, compact=False)


def _render(node, compact: bool = False) -> str:  # noqa: ANN001
    """Internal render with a *compact* flag.

    ``compact=True`` suppresses spaces around ``+`` / ``-`` (used inside
    index brackets to match corpus style ``a[b[i]+1]`` vs ``|a| - 1``).
    """
    if isinstance(node, Biconditional):
        return " <=> ".join(_render(p) for p in node.left)

    if isinstance(node, Implication):
        return f"{_render(node.antecedent)} => {_render(node.consequent)}"

    if isinstance(node, Or):
        return " or ".join(_render(p) for p in node.parts)

    if isinstance(node, And):
        return " and ".join(_render(p) for p in node.parts)

    if isinstance(node, Not):
        return f"not {_render(node.inner)}"

    if isinstance(node, Quantified):
        return _render_quantified(node)

    if isinstance(node, ChainedCmp):
        # Terms in a chained comparison are not inside index brackets → not compact.
        parts = [_render(node.terms[0])]
        for op, term in zip(node.ops, node.terms[1:]):
            parts.append(op)
            parts.append(_render(term))
        return " ".join(parts)

    if isinstance(node, Membership):
        members_str = ", ".join(_render(m) for m in node.members)
        return f"{node.name} in {{{members_str}}}"

    if isinstance(node, FuncCall):
        args_str = ", ".join(_render_arg(a) for a in node.args)
        base = f"{node.name}({args_str})"
        if not node.expect:
            return f"{base} == false"
        return base

    if isinstance(node, IndexExpr):
        result = node.base
        for idx in node.indices:
            # Switch to compact mode inside brackets: b[i]+1 not b[i] + 1
            result += f"[{_render(idx, compact=True)}]"
        return result

    if isinstance(node, Card):
        return f"|{node.name}|"

    if isinstance(node, MinK):
        return f"min_k({_render(node.inner)})"

    if isinstance(node, Add):
        sep = "+" if compact else " + "
        return f"{_render(node.left, compact)}{sep}{_render(node.right, compact)}"

    if isinstance(node, Sub):
        sep = "-" if compact else " - "
        return f"{_render(node.left, compact)}{sep}{_render(node.right, compact)}"

    if isinstance(node, IntLit):
        return str(node.value)

    if isinstance(node, Ident):
        return node.name

    raise TypeError(f"render: unknown AST node type {type(node).__name__!r}")


def _render_quantified(node: Quantified) -> str:
    """Render a Quantified node."""
    quant = node.quant  # "forall", "exists", or "for each"

    # Build the variable/qvars portion.
    if node.domain_in is not None:
        # forall stmt in evolve_region: body  (domain-quantified form, §4.8.2)
        var = node.vars[0]
        qvars_str = f"{var} in {node.domain_in}"
    elif node.bounded_in is not None:
        # exists i in {0, 1, 2}: body
        var = node.vars[0]
        members_str = ", ".join(_render(m) for m in node.bounded_in)
        qvars_str = f"{var} in {{{members_str}}}"
    elif node.neq:
        # forall k1 != k2: body
        qvars_str = f"{node.vars[0]} != {node.vars[1]}"
    else:
        # forall i | forall i,j | forall i,m — no space after comma (corpus convention)
        qvars_str = ",".join(node.vars)

    head = f"{quant} {qvars_str}"

    if node.body is not None:
        return f"{head}: {_render(node.body)}"
    return head


def _render_arg(arg: Arg) -> str:
    if isinstance(arg, ArrayArg):
        return f"{arg.name}[]"
    if isinstance(arg, ScalarArg):
        return arg.name
    raise TypeError(f"_render_arg: unknown arg type {type(arg).__name__!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(src: str) -> Predicate:
    """Parse *src* as a predicate DSL expression.

    Returns:
        An AST node (dataclass instance).

    Raises:
        ParseError: if *src* is syntactically invalid or contains an unknown
            function name.
    """
    try:
        tree = _PARSER.parse(src)
    except LarkError as exc:
        raise ParseError(str(exc)) from exc
    return _AstBuilder().transform(tree)
