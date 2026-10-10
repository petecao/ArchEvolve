# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/legality_testing/contract_check.py (ContractPredicate,
#         family_of, the deterministic predicate emitter, _negctl_mutation, emit_predicate,
#         emit_contract_probe, splice_probe(s), contract_record_from_verdict) and
#         AgenticRefiner/refiner/legality_testing/dsl_contract.py (runtime_checkable_predicates).
"""Runtime-probe contract checks: a contract's predicates compiled into C++ probes.

Kept from Extensa (decision D1): predicates are parsed by the ported grammar
(`swdb.predicate_grammar`); each becomes a deterministic C++ check with one negative
control per conjunct that mutates a clone of the real buffer; verdict lines
(`PROP <region>::contract.<pid> PASS|FAIL|SKIP`) are read back into a record.

SWDB changes (2026-10-03 ET):

* Predicates come from a library entry's clauses whose formal half is an
  `extensa_predicate` (not from MemAcc's transformation registry).
* Sites are the call sites the certification build names (a rewrite contract's
  application or a differential driver), not a region scan.
* Binding strength: a symbol bound from the rewrite contract's operands is
  `call_bound`; any provider-supplied binding is `model_bound` and never makes a
  candidate certified. The runtime extent upgrade, CUDA device support and
  MemAcc's call-signature evidence are not ported.
* Probes are compiled only into certification builds (`probe_build_flags`); timed
  builds never see them (`assert_probe_free`).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Sequence, Tuple

# --- named reasons -----------------------------------------------------------
# Every path on which a changed region is NOT contract-checked records one of
# these. CLOSED set: a new reason is a visible code change.
REASON_NO_LIBRARY_CALL = "no_library_call"                  # freeform region; not a fallback
REASON_NO_CITATION = "no_cited_entry"                        # calls an executor, cites nothing
REASON_CLASS_CITATION_MISMATCH = "class_citation_mismatch"   # cited class is not the one called
REASON_NO_RUNTIME_PREDICATES = "no_runtime_predicates"       # entry has no runtime-checkable predicate
REASON_TRANSLATION_FAILED = "translation_failed"             # unparseable / unsupported / unbound
REASON_TOOTHLESS = "toothless_negative_control"              # a predicate's negative control did not fire
REASON_DEVICE_REGION = "device_region_not_checkable"         # edit only inside a GPU kernel
REASON_DROPPED_ON_REGEN = "check_dropped_on_regeneration"    # a regenerated oracle lost the check
REASON_NOT_EXERCISED = "contract_probe_not_exercised"        # probe never ran (call site not reached)
REASON_PREDICATE_FAILED = "contract_predicate_failed"        # a predicate was violated (region fails)
REASON_FROZEN_SPEC_UNLABELED = "frozen_spec_without_predicate_ids"
REASON_HAND_TRANSLATED = "hand_translated_frozen_spec"      # labeled, never counted
REASON_ERROR = "contract_check_error"                        # swallowed error, now named
# Added 2026-09-27 (code review, section A; orchestrator items 3-8):
REASON_CALL_FORM_UNRESOLVED = "call_form_unresolved"         # a registry method on an untyped receiver
REASON_NO_KERNEL_METHOD = "entry_names_no_kernel_method"     # no kernel-role symbol to probe before
REASON_NO_KERNEL_CALL = "no_kernel_call_in_region"           # only setup calls of the class
REASON_MODEL_BOUND = "model_bound_binding"                   # checked, but a length came from the model
REASON_MODEL_BOUND_FAILED = "model_bound_predicate_failed"   # FAIL under an unvalidated binding (not a refusal)
REASON_PROBE_BUILD_FAILED = "contract_probe_build_failed"    # the probe broke the build; rebuilt without it
REASON_PROBE_RUN_FAILED = "contract_probe_run_failed"        # the probed run failed; rerun without it
REASON_REGION_NOT_EXERCISED = "library_region_not_exercised"  # row level: a library region was skipped

NAMED_REASONS = (
    REASON_NO_LIBRARY_CALL, REASON_NO_CITATION, REASON_CLASS_CITATION_MISMATCH,
    REASON_NO_RUNTIME_PREDICATES, REASON_TRANSLATION_FAILED, REASON_TOOTHLESS,
    REASON_DEVICE_REGION, REASON_DROPPED_ON_REGEN, REASON_NOT_EXERCISED,
    REASON_PREDICATE_FAILED, REASON_FROZEN_SPEC_UNLABELED, REASON_HAND_TRANSLATED,
    REASON_ERROR, REASON_CALL_FORM_UNRESOLVED, REASON_NO_KERNEL_METHOD,
    REASON_NO_KERNEL_CALL, REASON_MODEL_BOUND, REASON_MODEL_BOUND_FAILED,
    REASON_PROBE_BUILD_FAILED, REASON_PROBE_RUN_FAILED, REASON_REGION_NOT_EXERCISED,
)

#: Verdict property prefixes the probe writes (after the `<rid>::` tag).
PROP_CONTRACT = "contract."
PROP_CONTRACT_NEGCTL = "contract_negctl."
#: Runtime extent verification of a model-sourced length (2026-09-27):
#: `contract_len.<pid>|<symbol>|src=..|cap=..|need=.. PASS|MISMATCH|INEXACT|SKIP`.
#: MISMATCH (never FAIL) so an extent result can never refuse a candidate.
#: INEXACT (2026-09-30 ET, review E1): a rounding allocator reported
#: usable >= need, which cannot tell an exact length from a short one.
PROP_CONTRACT_LEN = "contract_len."
#: Extent sources that report the EXACT allocation size (review E1). Only a
#: PASS from one of these, with cap == need, verifies a model length.
EXACT_EXTENT_SOURCES = ("device_address_range", "asan_allocated_size",
                        "asan_malloc_size")


# --- predicates (ported) ---------------------------------------------------

@dataclass(frozen=True)
class ContractPredicate:
    entry_id: str
    rule_id: str
    body: str
    family: str

    @property
    def pid(self) -> str:
        return f"{self.entry_id}.{self.rule_id}"


_FINITE = re.compile(r"^\s*(?P<expr>.+?)\s+is\s+finite\b", re.S)


def _is_writes_call(node) -> bool:
    from swdb.predicate_grammar import FuncCall, Not
    if isinstance(node, Not):
        node = node.inner
        return isinstance(node, FuncCall) and node.name in ("writes", "writes_to")
    return (isinstance(node, FuncCall) and node.name in ("writes", "writes_to")
            and node.expect is False)


def family_of(ast) -> str:
    """A STRUCTURAL predicate family name (reporting and negative-control
    template choice). Never benchmark-specific. Families (ticket 07):
    index_bounds, alias_disjoint, writes, finite, count_equals_one (claim
    count / single ownership / contribution count), operand_count (|a| == |b|),
    uniqueness (pairwise distinct), elementwise, scalar_relation, conjunction,
    domain_quantified."""
    from swdb.predicate_grammar import (
        And, Card, ChainedCmp, FuncCall, IndexExpr, IntLit, Quantified)
    node = ast
    if isinstance(node, Quantified):
        body = node.body
        if _is_writes_call(body):
            return "writes"
        if isinstance(body, FuncCall) and body.name in ("alias", "aliasing", "disjoint"):
            return "alias_disjoint"
        if node.domain_in is not None:
            return "domain_quantified"
        if node.neq:
            if isinstance(body, ChainedCmp) and all(isinstance(t, Card) for t in body.terms):
                return "operand_count"
            return "uniqueness"
        if isinstance(body, ChainedCmp):
            terms = body.terms
            if (len(terms) == 2 and body.ops == ("==",)
                    and any(isinstance(t, IntLit) and t.value == 1 for t in terms)
                    and any(isinstance(t, IndexExpr) for t in terms)):
                return "count_equals_one"
            if all(o in ("<", "<=") for o in body.ops):
                return "index_bounds"
            return "elementwise"
        return "quantified_other"
    if _is_writes_call(node):
        return "writes"
    if isinstance(node, FuncCall):
        if node.name in ("alias", "aliasing", "disjoint"):
            return "alias_disjoint"
        return "func_other"
    if isinstance(node, ChainedCmp):
        if all(isinstance(t, Card) for t in node.terms):
            return "operand_count"
        return "scalar_relation"
    if isinstance(node, And):
        return "conjunction"
    return "other"


def site_reach_tag(site: "ContractSite") -> str:
    """The per-site identity of a probed call (code review, 2026-09-30 ET):
    the site key's location (`L<line>`, or `L<a>-L<b>` for a writes span),
    plus the receiver variable when known. Characters outside
    [0-9A-Za-z_.:@-] become `_` (the tag lands in a C string and a PROP name)."""
    loc = site.key.split("@", 1)[1] if "@" in (site.key or "") else f"L{site.call_line}"
    tag = f"{loc}:{site.call_var}" if site.call_var else loc
    return re.sub(r"[^0-9A-Za-z_.:@-]", "_", tag)


def site_reach_name(pid: str, site_tag: str) -> str:
    """The PROP name (after `contract.`) of one pid's reach line at one site."""
    return f"{pid}@{site_tag}"


#   2. `_Emit`: the rewritten AST -> a C++ bool expression over host copies
#      (`A_`), address ranges (`Rlo_`/`Rhi_`), cardinalities (`C_`) and
#      scalars (`S_`), evaluated by a generic lambda so the same evaluator runs
#      on the real values and on the mutated copies (`M_`, `MR*_`, `MC_`, `MS_`).
#   3. `_negctl_mutation`: a generic, shape-chosen mutation of the copies that
#      violates the predicate. The negative control fires iff the evaluator
#      refuses the mutated copies.

class EmitError(ValueError):
    """A predicate cannot be emitted (unbound symbol or unsupported shape)."""


@dataclass(frozen=True)
class _MinCards:
    """Synthetic node: min over |X| for the listed symbols (from `min_k`)."""
    names: tuple


@dataclass(frozen=True)
class _WritesNot:
    """Synthetic node: `name` is not written across the executor call."""
    name: str


_BIG = "((lact_v)(~0ULL >> 1))"


def _cid(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z_]", "_", name.replace("#", "__"))


def _canon(v: str) -> str:
    return re.sub(r"\d+$", "", v) or v


def _names_in(node, out: set) -> set:
    from swdb import predicate_grammar as G
    if isinstance(node, G.Ident):
        out.add(node.name)
    elif isinstance(node, G.Card):
        out.add(node.name)
    elif isinstance(node, G.IndexExpr):
        out.add(node.base)
        for e in node.indices:
            _names_in(e, out)
    elif isinstance(node, (G.ArrayArg, G.ScalarArg)):
        out.add(node.name)
    elif isinstance(node, (G.Add, G.Sub)):
        _names_in(node.left, out); _names_in(node.right, out)
    elif isinstance(node, G.MinK):
        _names_in(node.inner, out)
    elif isinstance(node, G.ChainedCmp):
        for t in node.terms:
            _names_in(t, out)
    elif isinstance(node, G.FuncCall):
        for a in node.args:
            _names_in(a, out)
    elif isinstance(node, (G.And, G.Or)):
        for p in node.parts:
            _names_in(p, out)
    elif isinstance(node, G.Not):
        _names_in(node.inner, out)
    elif isinstance(node, G.Implication):
        _names_in(node.antecedent, out); _names_in(node.consequent, out)
    elif isinstance(node, G.Quantified):
        _names_in(node.body, out)
    elif isinstance(node, _MinCards):
        out.update(node.names)
    elif isinstance(node, _WritesNot):
        out.add(node.name)
    return out


def _rename(node, m: Mapping[str, str]):
    """Rename symbols (Ident, |X|, X[..], X[] args) through mapping m."""
    import dataclasses as dc
    from swdb import predicate_grammar as G
    r = lambda n: m.get(n, n)
    if isinstance(node, G.Ident):
        return G.Ident(r(node.name))
    if isinstance(node, G.Card):
        return G.Card(r(node.name))
    if isinstance(node, G.IndexExpr):
        return G.IndexExpr(r(node.base), tuple(_rename(e, m) for e in node.indices))
    if isinstance(node, G.ArrayArg):
        return G.ArrayArg(r(node.name))
    if isinstance(node, G.ScalarArg):
        return G.ScalarArg(r(node.name))
    if isinstance(node, (G.Add, G.Sub)):
        return type(node)(_rename(node.left, m), _rename(node.right, m))
    if isinstance(node, G.MinK):
        return G.MinK(_rename(node.inner, m))
    if isinstance(node, G.ChainedCmp):
        return G.ChainedCmp(tuple(_rename(t, m) for t in node.terms), node.ops)
    if isinstance(node, G.FuncCall):
        return G.FuncCall(node.name, tuple(_rename(a, m) for a in node.args), node.expect)
    if isinstance(node, (G.And, G.Or)):
        return type(node)(tuple(_rename(p, m) for p in node.parts))
    if isinstance(node, G.Not):
        return G.Not(_rename(node.inner, m))
    if isinstance(node, G.Implication):
        return G.Implication(_rename(node.antecedent, m), _rename(node.consequent, m))
    if isinstance(node, G.Quantified):
        return dc.replace(node, body=_rename(node.body, m) if node.body is not None else None)
    if isinstance(node, _MinCards):
        return _MinCards(tuple(r(n) for n in node.names))
    if isinstance(node, _WritesNot):
        return _WritesNot(r(node.name))
    return node


def _list_of(binding: Mapping, name: str) -> Optional[list]:
    b = binding.get(name)
    if isinstance(b, Mapping) and isinstance(b.get("list"), list):
        return b["list"]
    if isinstance(b, list):
        return b
    return None


def _expand(node, binding: Mapping):
    """Step 1 (see the section comment). Raises EmitError on a family whose
    list binding is missing."""
    from swdb import predicate_grammar as G
    if isinstance(node, G.Quantified):
        body = node.body
        if body is None:
            raise EmitError("quantifier without a body")
        # forall stmt in R: not writes(stmt, X)  ->  X unchanged across the call
        # forall m in D: not writes(loop, m)     ->  every member of D unchanged
        if node.domain_in is not None and _is_writes_call(body):
            fc = body.inner if isinstance(body, G.Not) else body
            if len(fc.args) != 2:
                raise EmitError("unsupported writes() form")
            if fc.args[0].name in node.vars:
                return _expand(_WritesNot(fc.args[1].name), binding)
            if fc.args[1].name in node.vars:
                inst = _list_of(binding, node.domain_in)
                if inst is None:
                    raise EmitError(f"domain {node.domain_in!r} is not bound as a list")
                parts = [_WritesNot(f"{node.domain_in}#{a}") for a in range(len(inst))]
                return G.And(tuple(parts)) if len(parts) != 1 else parts[0]
            raise EmitError("unsupported writes() form")
        if node.domain_in is not None:
            (v,) = node.vars if len(node.vars) == 1 else (None,)
            if v is None:
                raise EmitError("multi-variable domain quantifier")
            inst = _list_of(binding, node.domain_in)
            if inst is None:
                raise EmitError(f"domain {node.domain_in!r} is not bound as a list")
            names = _names_in(body, set())
            parts = []
            for a in range(len(inst)):
                m = {v: f"{node.domain_in}#{a}"}
                m.update({n: f"{n}#{a}" for n in names if n.endswith("_" + v)})
                parts.append(_expand(_rename(body, m), binding))
            return G.And(tuple(parts)) if len(parts) != 1 else parts[0]
        names = _names_in(body, set())
        fam = [v for v in node.vars if any(n.endswith("_" + v) for n in names)]
        idx = [v for v in node.vars if v not in fam]
        if fam:
            c = _canon(fam[0])
            if any(_canon(v) != c for v in fam):
                raise EmitError("more than one family variable")
            bases = sorted({n[: -len(v)] + c for v in fam for n in names
                            if n.endswith("_" + v)})
            inst = _list_of(binding, bases[0])
            if inst is None:
                raise EmitError(f"family {bases[0]!r} is not bound as a list")
            n_inst = len(inst)
            if node.neq and len(fam) == 2:
                combos = [(a, b) for a in range(n_inst) for b in range(n_inst) if a < b]
            elif len(fam) == 1 and not node.neq:
                combos = [(a,) for a in range(n_inst)]
            else:
                raise EmitError("unsupported family quantifier form")
            parts = []
            for combo in combos:
                m = {}
                for v, a in zip(fam, combo):
                    for n in names:
                        if n.endswith("_" + v):
                            m[n] = f"{n[: -len(v)]}{c}#{a}"
                inner = _rename(body, m)
                if idx:
                    if len(idx) != 1:
                        raise EmitError("more than one index variable")
                    inner = G.Quantified("forall", (idx[0],), False, None, inner)
                parts.append(_expand(inner, binding))
            if not parts:
                return G.ChainedCmp((G.IntLit(0), G.IntLit(0)), ("==",))  # vacuous
            return G.And(tuple(parts)) if len(parts) != 1 else parts[0]
        import dataclasses as dc
        return dc.replace(node, body=_expand(body, binding))
    if isinstance(node, G.And):
        return G.And(tuple(_expand(p, binding) for p in node.parts))
    if isinstance(node, G.Or):
        return G.Or(tuple(_expand(p, binding) for p in node.parts))
    if isinstance(node, G.Not):
        if _is_writes_call(node):
            fc = node.inner
            return _expand(_WritesNot(fc.args[-1].name), binding)
        return G.Not(_expand(node.inner, binding))
    if isinstance(node, G.FuncCall) and _is_writes_call(node):
        return _expand(_WritesNot(node.args[-1].name), binding)
    if isinstance(node, G.Implication):
        return G.Implication(_expand(node.antecedent, binding),
                             _expand(node.consequent, binding))
    if isinstance(node, G.ChainedCmp):
        return G.ChainedCmp(tuple(_min_k(t, binding) for t in node.terms), node.ops)
    if isinstance(node, _WritesNot):
        inst = _list_of(binding, node.name)
        if inst is not None:
            parts = [_WritesNot(f"{node.name}#{a}") for a in range(len(inst))]
            return G.And(tuple(parts)) if len(parts) != 1 else parts[0]
        return node
    return node


def _min_k(term, binding):
    from swdb import predicate_grammar as G
    if isinstance(term, G.MinK):
        inner = term.inner
        if not isinstance(inner, G.Card):
            raise EmitError("min_k over a non-cardinality")
        inst = _list_of(binding, inner.name)
        if inst is None:
            raise EmitError(f"family {inner.name!r} is not bound as a list")
        if not inst:
            raise EmitError(f"family {inner.name!r} is empty")
        return _MinCards(tuple(f"{inner.name}#{a}" for a in range(len(inst))))
    if isinstance(term, (G.Add, G.Sub)):
        return type(term)(_min_k(term.left, binding), _min_k(term.right, binding))
    return term


@dataclass
class _Uses:
    contents: list = field(default_factory=list)   # X[...] / uniqueness: host copy
    ranges: list = field(default_factory=list)     # alias/disjoint args: address range
    writes: list = field(default_factory=list)     # not-written targets: snapshot
    cards: list = field(default_factory=list)
    scalars: list = field(default_factory=list)


def _uses(node, qvars: set, u: _Uses) -> _Uses:
    from swdb import predicate_grammar as G
    add = lambda lst, n: lst.append(n) if n not in lst else None
    if node is None or isinstance(node, G.IntLit):
        return u
    if isinstance(node, G.Ident):
        if node.name not in qvars:
            add(u.scalars, node.name)
    elif isinstance(node, G.Card):
        add(u.cards, node.name)
    elif isinstance(node, _MinCards):
        for n in node.names:
            add(u.cards, n)
    elif isinstance(node, _WritesNot):
        add(u.writes, node.name)
    elif isinstance(node, G.IndexExpr):
        add(u.contents, node.base)
        for e in node.indices:
            _uses(e, qvars, u)
    elif isinstance(node, (G.Add, G.Sub)):
        _uses(node.left, qvars, u); _uses(node.right, qvars, u)
    elif isinstance(node, G.ChainedCmp):
        for t in node.terms:
            _uses(t, qvars, u)
    elif isinstance(node, G.FuncCall):
        if node.name not in ("alias", "aliasing", "disjoint") or len(node.args) != 2 \
                or not all(isinstance(a, G.ArrayArg) for a in node.args):
            raise EmitError(f"unsupported function {node.name}()")
        for a in node.args:
            add(u.ranges, a.name)
    elif isinstance(node, G.Quantified):
        if node.domain_in is not None or node.bounded_in is not None \
                or node.quant not in ("forall", "for each"):
            raise EmitError(f"unsupported quantifier form ({node.quant} {node.vars})")
        if node.neq:
            if not _is_uniqueness(node):
                raise EmitError("unsupported pairwise quantifier")
        elif len(node.vars) != 1:
            raise EmitError("more than one index variable")
        _uses(node.body, qvars | set(node.vars), u)
    elif isinstance(node, (G.And, G.Or)):
        for p in node.parts:
            _uses(p, qvars, u)
    elif isinstance(node, G.Not):
        _uses(node.inner, qvars, u)
    elif isinstance(node, G.Implication):
        _uses(node.antecedent, qvars, u); _uses(node.consequent, qvars, u)
    else:
        raise EmitError(f"unsupported predicate node {type(node).__name__}")
    return u


def _is_uniqueness(node) -> bool:
    """`forall i != j: X[i] != X[j]` (pairwise distinct elements)."""
    from swdb import predicate_grammar as G
    b = node.body
    if not (node.neq and len(node.vars) == 2 and isinstance(b, G.ChainedCmp)
            and b.ops == ("!=",) and len(b.terms) == 2):
        return False
    t0, t1 = b.terms
    return (isinstance(t0, G.IndexExpr) and isinstance(t1, G.IndexExpr)
            and t0.base == t1.base and len(t0.indices) == len(t1.indices) == 1
            and {getattr(t0.indices[0], "name", None),
                 getattr(t1.indices[0], "name", None)} == set(node.vars))


# Kept for the gate's binding request (symbols the model must bind).
@dataclass(frozen=True)
class _Syms:
    arrays: Tuple[str, ...]
    cards: Tuple[str, ...]
    scalars: Tuple[str, ...]
    lists: Tuple[str, ...] = ()


def _parse_body(body: str):
    """Parse a predicate; the `<expr> is finite ...` form becomes
    `0 <= expr < BIG` over the synthetic scalar `__lact_big`."""
    from swdb.predicate_grammar import ParseError, parse
    from swdb import predicate_grammar as G
    try:
        return parse(body), False
    except ParseError as e:
        m = _FINITE.match(body)
        if not m:
            raise EmitError(f"unparseable predicate: {e}") from e
        try:
            cmp_ = parse(f"0 <= {m.group('expr')}")
        except ParseError as e2:
            raise EmitError(f"unparseable finite predicate: {e2}") from e2
        t = cmp_.terms
        return G.ChainedCmp((t[0], t[1], G.Ident("__lact_big")), ("<=", "<")), True


def symbols_of(body: str) -> _Syms:
    """The symbols a model must bind for one predicate (before expansion): plain
    arrays (`expr` + `len`), cardinalities (`len`), scalars (`expr`), and LIST
    symbols (family members and domains: `{"list": [ {expr,len}, ... ]}`)."""
    from swdb import predicate_grammar as G
    ast, _fin = _parse_body(body)
    lists: list = []
    qv: set = set()

    def walk(n, fams: set, qvars: set):
        if isinstance(n, G.Quantified):
            names = _names_in(n.body, set())
            if n.domain_in is not None and _is_writes_call(n.body):
                fc = n.body.inner if isinstance(n.body, G.Not) else n.body
                if len(fc.args) == 2 and fc.args[1].name in n.vars \
                        and n.domain_in not in lists:
                    lists.append(n.domain_in)       # forall m in D: not writes(_, m)
            elif n.domain_in is not None:
                if n.domain_in not in lists:
                    lists.append(n.domain_in)
                fams = fams | {v for v in n.vars}
                for nm in names:
                    if any(nm.endswith("_" + v) for v in n.vars) and nm not in lists:
                        lists.append(nm)
            elif n.domain_in is None:
                for v in n.vars:
                    for nm in names:
                        if nm.endswith("_" + v):
                            base = nm[: -len(v)] + _canon(v)
                            if base not in lists:
                                lists.append(base)
            walk(n.body, fams, qvars | set(n.vars))
        elif isinstance(n, G.MinK) and isinstance(n.inner, G.Card):
            if n.inner.name not in lists:
                lists.append(n.inner.name)
        else:
            for ch in _children(n):
                walk(ch, fams, qvars)
    walk(ast, set(), set())
    arrays, cards, scalars = [], [], []
    add = lambda lst, x: lst.append(x) if x not in lst else None

    def leaf(n, qvars):
        if isinstance(n, G.Quantified):
            for ch in [n.body]:
                leaf(ch, qvars | set(n.vars) | ({"__stmt__"} if n.domain_in else set()))
            return
        if isinstance(n, G.Ident):
            if n.name not in qvars:
                add(scalars, n.name)
        elif isinstance(n, G.Card):
            add(cards, n.name)
        elif isinstance(n, G.IndexExpr):
            add(arrays, n.base)
        elif isinstance(n, (G.ArrayArg,)):
            add(arrays, n.name)
        for ch in _children(n):
            leaf(ch, qvars)
    leaf(ast, set())
    fam_members = lambda x: x in lists or any(
        x.endswith("_" + v) and x[: -len(v)] + _canon(v) in lists
        for v in ("k", "k1", "k2", "m", "m1", "m2", "a"))
    norm = lambda x: next((x[: -len(v)] + _canon(v) for v in ("k1", "k2", "m1", "m2")
                           if x.endswith("_" + v)), x)
    arrays = [norm(a) for a in arrays]
    cards = [norm(c) for c in cards]
    out_lists = list(dict.fromkeys(norm(x) for x in lists))
    # writes targets (`not writes(stmt, X)` / `writes(loop, X) == false`) are arrays
    for n in _walk_all(ast):
        if isinstance(n, G.FuncCall) and n.name in ("writes", "writes_to") and n.args:
            add(arrays, n.args[-1].name)
    stmt_vars = {v for n in _walk_all(ast) if isinstance(n, G.Quantified)
                 and n.domain_in is not None and _is_writes_call(n.body) for v in n.vars}
    if _fin:
        scalars = [x for x in scalars if x != "__lact_big"]
    qvars_all = {v for q in _walk_all(ast) if isinstance(q, G.Quantified) for v in q.vars}
    arrays = [a for a in dict.fromkeys(arrays) if a not in out_lists and a not in stmt_vars
              and a not in qvars_all]
    cards = [c for c in dict.fromkeys(cards) if c not in out_lists and c not in arrays
             and c not in qvars_all]
    scalars = [x for x in dict.fromkeys(scalars) if x not in out_lists and x not in stmt_vars
               and x not in ("loop",)]
    return _Syms(tuple(arrays), tuple(cards), tuple(scalars), tuple(out_lists))


def _children(n):
    from swdb import predicate_grammar as G
    if isinstance(n, (G.Add, G.Sub)):
        return [n.left, n.right]
    if isinstance(n, G.IndexExpr):
        return list(n.indices)
    if isinstance(n, G.MinK):
        return [n.inner]
    if isinstance(n, G.ChainedCmp):
        return list(n.terms)
    if isinstance(n, G.FuncCall):
        return list(n.args)
    if isinstance(n, (G.And, G.Or)):
        return list(n.parts)
    if isinstance(n, G.Not):
        return [n.inner]
    if isinstance(n, G.Implication):
        return [n.antecedent, n.consequent]
    if isinstance(n, G.Quantified):
        return [n.body] if n.body is not None else []
    return []


def _walk_all(n):
    yield n
    for ch in _children(n):
        yield from _walk_all(ch)


def _walk_all_ext(n):
    """Top-level conjunct structure including synthetic nodes."""
    from swdb import predicate_grammar as G
    yield n
    if isinstance(n, G.And):
        for p in n.parts:
            yield from _walk_all_ext(p)


def _is_affine_in(expr, var: str) -> Optional[str]:
    """If expr is `var`, `var + c`, or `var - c` (c an integer literal), return
    the C++ offset form; else None."""
    from swdb import predicate_grammar as G
    if isinstance(expr, G.Ident) and expr.name == var:
        return var
    if isinstance(expr, (G.Add, G.Sub)) and isinstance(expr.left, G.Ident) \
            and expr.left.name == var and isinstance(expr.right, G.IntLit):
        op = "+" if isinstance(expr, G.Add) else "-"
        return f"({var} {op} {expr.right.value}LL)"
    return None


class _Emit:
    """Step 2: the expanded AST -> a C++ bool expression over `lact_v` (long
    double) values, so a floating-point comparison is exact in the declared
    precision and never truncated (code review A4, 2026-09-27). Prefixes
    select the real values or the mutated copies (negative control)."""

    def __init__(self, *, arr="A_", card="C_", scalar="S_", rlo="Rlo_", rhi="Rhi_"):
        self.pa, self.pc, self.ps, self.plo, self.phi = arr, card, scalar, rlo, rhi

    def expr(self, node, env: dict, guards: list) -> str:
        from swdb import predicate_grammar as G
        if isinstance(node, G.IntLit):
            return f"((lact_v){node.value}LL)"
        if isinstance(node, G.Ident):
            if node.name in env:
                return env[node.name]
            return f"{self.ps}{_cid(node.name)}"
        if isinstance(node, G.Card):
            return f"{self.pc}{_cid(node.name)}"
        if isinstance(node, _MinCards):
            return "std::min({" + ", ".join(f"{self.pc}{_cid(n)}" for n in node.names) + "})"
        if isinstance(node, G.Add):
            return f"({self.expr(node.left, env, guards)} + {self.expr(node.right, env, guards)})"
        if isinstance(node, G.Sub):
            return f"({self.expr(node.left, env, guards)} - {self.expr(node.right, env, guards)})"
        if isinstance(node, G.IndexExpr):
            if len(node.indices) != 1:
                raise EmitError("multi-dimensional index is not supported")
            k = self.expr(node.indices[0], env, guards)
            a = f"{self.pa}{_cid(node.base)}"
            # An index outside the array, or not an integer (a NaN included),
            # violates the predicate; the guard runs before the cast.
            guards.append(f"lact_idx_ok(({k}), {a}.size())")
            return f"{a}[(std::size_t)(long long)({k})]"
        raise EmitError(f"unsupported expression node {type(node).__name__}")

    def pred(self, node, env: dict) -> str:
        from swdb import predicate_grammar as G
        if isinstance(node, G.ChainedCmp):
            guards: list = []
            terms = [self.expr(t, env, guards) for t in node.terms]
            parts = [f"({terms[k]} {node.ops[k]} {terms[k + 1]})"
                     for k in range(len(node.ops))]
            body = " && ".join(parts)
            if guards:
                return f"(({' && '.join(dict.fromkeys(guards))}) && ({body}))"
            return f"({body})"
        if isinstance(node, G.FuncCall):
            a, b = (_cid(x.name) for x in node.args)
            overlap = (f"({self.plo}{a} < {self.phi}{b} && {self.plo}{b} < {self.phi}{a})")
            disjoint = f"(!{overlap})"
            if node.name == "disjoint":
                return disjoint if node.expect else overlap
            return disjoint if node.expect is False else overlap
        if isinstance(node, _WritesNot):
            raise EmitError("a not-written clause mixed with other clauses")
        if isinstance(node, G.And):
            return "(" + " && ".join(self.pred(p, env) for p in node.parts) + ")"
        if isinstance(node, G.Or):
            return "(" + " || ".join(self.pred(p, env) for p in node.parts) + ")"
        if isinstance(node, G.Not):
            return f"(!{self.pred(node.inner, env)})"
        if isinstance(node, G.Implication):
            return f"(!{self.pred(node.antecedent, env)} || {self.pred(node.consequent, env)})"
        if isinstance(node, G.Quantified):
            if node.neq:                       # uniqueness: sort a copy
                a = f"{self.pa}{_cid(node.body.terms[0].base)}"
                return f"lact_all_distinct({a})"
            v = node.vars[0]
            cv = f"q_{_cid(v)}"
            ranges, edge = [], []
            for base, off in self._affine_uses(node.body, v):
                a = f"{self.pa}{_cid(base)}"
                ranges.append(f"(long long){a}.size()")
                o = off.replace(v, cv)
                edge.append(f"(({o}) >= 0LL && ({o}) < (long long){a}.size())")
            if not ranges:
                raise EmitError(f"quantified variable {v!r} indexes no bound array")
            n = ranges[0] if len(set(ranges)) == 1 else "std::max({" + ", ".join(dict.fromkeys(ranges)) + "})"
            inner = self.pred(node.body, dict(env, **{v: f"((lact_v){cv})"}))
            edge_s = " && ".join(dict.fromkeys(edge))
            return (f"([&]() -> bool {{ for (long long {cv} = 0; {cv} < {n}; ++{cv}) "
                    f"{{ if (!({edge_s})) continue; if (!{inner}) return false; }} "
                    f"return true; }}())")
        raise EmitError(f"unsupported predicate node {type(node).__name__}")

    def _affine_uses(self, node, v):
        from swdb import predicate_grammar as G
        out = []
        for n in _walk_all(node):
            if isinstance(n, G.IndexExpr):
                for e in n.indices:
                    off = _is_affine_in(e, v)
                    if off is not None:
                        out.append((n.base, off))
        return out


_MUT = dict(arr="M_", card="MC_", scalar="MS_", rlo="MRlo_", rhi="MRhi_")

#: Marker for "set element idx of bound array NAME to VALUE in a mutated copy";
#: `emit_predicate` replaces it with a native-type clone of the REAL buffer
#: (`lact_mutclone`), so the negative control runs through the same binding,
#: copy and conversion as the check (orchestrator item 7, 2026-09-27).
_SET = "\x01SET\x02{name}\x02{idx}\x02{val}\x01"
_SET_RE = re.compile("\x01SET\x02(.*?)\x02(.*?)\x02(.*?)\x01", re.S)


def _set(name: str, idx: str, val: str) -> str:
    return _SET.format(name=name, idx=idx, val=val)


def _violate(op: str, r: str, side: str) -> str:
    """A value on the wrong side of `X op r` (side='right') or `r op X`,
    robust to large floating-point magnitudes (`lact_above/below/ne`)."""
    if side == "right":
        return {"<": r, "<=": f"lact_above({r})", ">": r, ">=": f"lact_below({r})",
                "==": f"lact_ne({r})", "!=": r}[op]
    return {"<": r, "<=": f"lact_below({r})", ">": r, ">=": f"lact_above({r})",
            "==": f"lact_ne({r})", "!=": r}[op]


def _negctl_mutation(ast, finite: bool = False) -> str:
    """Step 3: ONE generic negative-control mutation for one (non-conjunction)
    predicate, chosen by SHAPE (a conjunction gets one per conjunct, see
    `emit_predicate`):

    - quantified comparison `... X[v] op R ...`: X[0] := a value on the wrong
      side of the adjacent bound at v = 0 (in X's native type); if no term
      indexes X by v directly, the first array indexed by v is pushed far out.
    - uniqueness: X[1] := X[0].
    - alias/disjoint: make the pair overlap (moving whichever member is a
      non-empty range); an expected overlap is moved apart.
    - unquantified comparison: the first cardinality, scalar, or constant-
      indexed element := the wrong side of its neighbor.
    - finite: every cardinality := the finite bound.
    Raises EmitError when no template fits (`translation_failed`).
    """
    from swdb import predicate_grammar as G
    em = _Emit(**_MUT)
    if finite:
        cards = [n for n in _walk_all(ast) if isinstance(n, (G.Card, _MinCards))]
        names = []
        for c in cards:
            names += list(c.names) if isinstance(c, _MinCards) else [c.name]
        if not names:
            raise EmitError("finite predicate over no cardinality")
        return " ".join(f"MC_{_cid(n)} = {_BIG};" for n in dict.fromkeys(names))
    node = ast
    if isinstance(node, G.Quantified) and node.neq:
        a = f"M_{_cid(node.body.terms[0].base)}"
        return (f"if ({a}.size() >= 2) {{ {_set(node.body.terms[0].base, '1', f'{a}[0]')} }} "
                f"else {{ lact_mut_ok = false; }}")
    if isinstance(node, G.Quantified) and isinstance(node.body, G.ChainedCmp):
        v = node.vars[0]
        cmp_ = node.body
        for k, t in enumerate(cmp_.terms):
            if isinstance(t, G.IndexExpr) and len(t.indices) == 1 \
                    and isinstance(t.indices[0], G.Ident) and t.indices[0].name == v:
                env = {v: "((lact_v)0)"}
                arr = f"M_{_cid(t.base)}"
                if k + 1 < len(cmp_.terms):
                    op, other, side = cmp_.ops[k], cmp_.terms[k + 1], "right"
                else:
                    op, other, side = cmp_.ops[k - 1], cmp_.terms[k - 1], "left"
                g: list = []
                r = em.expr(other, env, g)
                guard = " && ".join(dict.fromkeys(g)) or "true"
                return (f"if (!{arr}.empty() && ({guard})) {{ "
                        f"{_set(t.base, '0', _violate(op, r, side))} }} "
                        f"else {{ lact_mut_ok = false; }}")
        for t in cmp_.terms:
            for n in _walk_all(t):
                if isinstance(n, G.IndexExpr) and len(n.indices) == 1 \
                        and isinstance(n.indices[0], G.Ident) and n.indices[0].name == v:
                    arr = f"M_{_cid(n.base)}"
                    return (f"if (!{arr}.empty()) {{ "
                            f"{_set(n.base, '0', '((lact_v)(1LL << 40))')} }} "
                            f"else {{ lact_mut_ok = false; }}")
        raise EmitError("no quantified array element to mutate")
    if isinstance(node, G.FuncCall):
        a, b = (_cid(x.name) for x in node.args)
        want_disjoint = (node.name == "disjoint" and node.expect) or \
            (node.name != "disjoint" and node.expect is False)
        if want_disjoint:
            return (f"if (MRlo_{a} < MRhi_{a}) {{ MRlo_{b} = MRlo_{a}; MRhi_{b} = MRhi_{a}; }} "
                    f"else if (MRlo_{b} < MRhi_{b}) {{ MRlo_{a} = MRlo_{b}; MRhi_{a} = MRhi_{b}; }} "
                    f"else {{ lact_mut_ok = false; }}")
        return f"MRlo_{b} = MRhi_{a} + 64LL; MRhi_{b} = MRlo_{b} + 64LL;"
    if isinstance(node, G.ChainedCmp) and len(node.terms) >= 2:
        for k, t0 in enumerate(node.terms):
            if k + 1 < len(node.terms):
                op, other, side = node.ops[k], node.terms[k + 1], "right"
            else:
                op, other, side = node.ops[k - 1], node.terms[k - 1], "left"
            g: list = []
            r = em.expr(other, {}, g)
            val = _violate(op, r, side)
            if isinstance(t0, G.Card):
                return f"MC_{_cid(t0.name)} = {val};"
            if isinstance(t0, G.Ident):
                return f"MS_{_cid(t0.name)} = {val};"
            if isinstance(t0, G.IndexExpr) and len(t0.indices) == 1:
                gi: list = []
                kx = em.expr(t0.indices[0], {}, gi)
                arr = f"M_{_cid(t0.base)}"
                return (f"if (lact_idx_ok(({kx}), {arr}.size())) "
                        f"{{ {_set(t0.base, f'(long long)({kx})', val)} }} "
                        f"else {{ lact_mut_ok = false; }}")
    raise EmitError("no generic negative-control template for this predicate shape")


@dataclass(frozen=True)
class EmittedPredicate:
    pid: str
    family: str
    pre: str = ""          # C++ block run before the call
    post: str = ""         # C++ block run after the call
    snap: str = ""         # writes: snapshot block (before the first call)
    cmp: str = ""          # writes: comparison block (after the last kernel call)
    globals: Tuple[str, ...] = ()
    strength: str = "model_bound"      # "call_bound" | "extent" | "model_bound"
    provenance: Mapping = field(default_factory=dict)
    extent: Tuple[str, ...] = ()       # symbols whose length is extent-checked at run time


def _bind(binding: Mapping, name: str) -> Mapping:
    if "#" in name:
        base, i = name.rsplit("#", 1)
        inst = _list_of(binding, base)
        if inst is None or int(i) >= len(inst):
            raise EmitError(f"family {base!r} instance {i} is not bound")
        b = inst[int(i)]
    else:
        b = binding.get(name)
    if isinstance(b, str):
        b = {"expr": b, "len": b}
    if not isinstance(b, Mapping):
        raise EmitError(f"symbol {name!r} is not bound")
    return b


def _binding_for(binding: Mapping, name: str, what: str) -> str:
    b = _bind(binding, name)
    v = b.get(what)
    if not isinstance(v, str) or not v.strip():
        raise EmitError(f"symbol {name!r} has no {what!r} in the binding")
    if ";" in v or "{" in v or "}" in v or "\n" in v:
        raise EmitError(f"binding for {name!r} is not a single expression")
    return v.strip()



#: SWDB operand origins (2026-10-03 ET). A binding expression is `call_bound` only
#: when the site's operand-origin map says it came from the rewrite contract's
#: operands (or the differential driver's declared call). Anything else, including
#: every provider-supplied binding, is `model_bound`.
CALL_BOUND_ORIGINS = ("contract_operand", "driver_operand")


def _strength(u: "_Uses", binding: Mapping, evidence: Mapping, ast):
    """Returns (strength, provenance, extent). SWDB has no extent upgrade: extent is
    always empty. `evidence` maps a bound symbol to its origin."""
    from swdb import predicate_grammar as G
    prov: dict = {}
    weak = False
    symbols = list(u.contents) + list(u.ranges) + list(u.writes) + list(u.cards) + \
        [s for s in u.scalars if s != "__lact_big"]
    for sym in dict.fromkeys(symbols):
        base = sym.split("#", 1)[0]
        origin = (evidence or {}).get(sym) or (evidence or {}).get(base) or "model"
        prov[sym] = origin
        if origin not in CALL_BOUND_ORIGINS:
            weak = True
    for n in _walk_all_ext(ast) if isinstance(ast, G.And) else [ast]:
        if isinstance(n, G.ChainedCmp) and all(isinstance(t, G.Card) for t in n.terms):
            exprs = [" ".join(_binding_for(binding, t.name, "len").split()) for t in n.terms]
            if len(set(exprs)) < len(exprs):
                prov["tautological"] = f"{[t.name for t in n.terms]} bound to one expression"
                weak = True
    return ("model_bound" if weak else "call_bound"), prov, []

def emit_predicate(pred: ContractPredicate, binding: Mapping, *, region_id: str,
                   device_tu: bool, timing: str = "pre", key: str = "",
                   evidence: Optional[Mapping] = None,
                   site_tag: str = "") -> EmittedPredicate:
    """One predicate -> C++ for its timing. Raises EmitError.

    `pre`/`post`: the check + one negative control per conjunct, run before /
    after the probed call. `snap`/`cmp` (writes family): a snapshot before the
    first call of the class and the unchanged-comparison after the last kernel
    call; the snapshot lives in a file-scope global.

    `site_tag` (code review, 2026-09-30 ET): when set, the evaluating block
    also writes the per-SITE reach line `contract.<pid>@<site_tag>` (PASS when
    evaluated there, SKIP when not evaluable), so a pid planned at several
    call sites is exercised only if EVERY site ran (`site_reach_name`)."""
    from swdb import predicate_grammar as G
    ast0, finite = _parse_body(pred.body)
    binding = dict(binding or {})
    if finite:
        binding["__lact_big"] = {"expr": _BIG}
    ast = _expand(ast0, binding)
    u = _uses(ast, set(), _Uses())
    strength, prov, extent = _strength(u, binding, evidence or {}, ast)
    tag = _cid(f"{region_id}__{pred.pid}")
    st = f"lact_st_{tag}"
    globs = [f"static unsigned {st} = 0;"]
    reach = ""
    if site_tag and timing != "snap":
        sst = f"lact_sr_{tag}__{_cid(site_tag)}"
        globs.append(f"static unsigned {sst} = 0;")
        reach = f'lact_reach("{site_reach_name(pred.pid, site_tag)}", {sst}, lact_ev);'
    # Runtime extent verification of model lengths (decision (b'), 2026-09-27).
    lenchk = []
    for sym, ptr, ln in extent:
        est = f"lact_lst_{tag}_{_cid(sym)}"
        globs.append(f"static unsigned {est} = 0;")
        lenchk.append(
            f"{{ int lact_src = 0; long long lact_cap = -1; long long lact_need = "
            f"(long long)({ln}) * (long long)sizeof(*({ptr})); int lact_r = "
            f"lact_extent_query((const void*)({ptr}), lact_need, &lact_src, &lact_cap); "
            f'lact_lenemit("{pred.pid}", "{sym}", {est}, lact_r, lact_src, lact_cap, lact_need); }}')
    lenchk_code = " ".join(lenchk)
    parts = list(ast.parts) if isinstance(ast, G.And) else [ast]
    wparts = [p for p in parts if isinstance(p, _WritesNot)]
    if wparts:
        if len(wparts) != len(parts):
            raise EmitError("a not-written clause mixed with other clauses")
        if timing not in ("snap", "cmp"):
            raise EmitError("a not-written predicate needs a snapshot span")
        ktag = _cid(f"{region_id}__{key or pred.pid}__{pred.pid}")
        globs += [f"static bool lact_Wset_{ktag} = false;",
                  f"static bool lact_Wok_{ktag} = true;"]
        snap, cmpb, same, caught = [], [], [], []
        for w in wparts:
            ptr, n = _binding_for(binding, w.name, "expr"), _binding_for(binding, w.name, "len")
            wv = f"lact_W_{ktag}_{_cid(w.name)}"
            globs.append(f"static std::vector<lact_v> {wv};")
            snap.append(f"{wv} = lact_copy(({ptr}), (long long)({n}));")
            same.append(f"lact_same(lact_copy(({ptr}), (long long)({n})), {wv})")
            caught.append(f"(!{wv}.empty() && !lact_same(lact_mutclone(({ptr}), "
                          f"(long long)({n}), 0, lact_ne({wv}[0])), {wv}))")
        snap_code = (f"{{ /* contract {pred.pid} (snapshot) */ lact_copy_ok = true; "
                     + " ".join(snap)
                     + f" lact_Wok_{ktag} = lact_copy_ok; lact_Wset_{ktag} = true; }}")
        cmp_prefix = lenchk_code
        cmp_code = (f"{{ /* contract {pred.pid} (after the last kernel call) */ {cmp_prefix} "
                    f"lact_copy_ok = true; bool lact_ok = {' && '.join(same)}; "
                    f"bool lact_caught = {' && '.join(caught)}; "
                    f"bool lact_ev = lact_Wset_{ktag} && lact_Wok_{ktag} && lact_copy_ok; "
                    f'lact_emit("{pred.pid}", {st}, lact_ok, lact_caught, lact_ev); '
                    f"{reach} }}")
        return EmittedPredicate(pred.pid, pred.family, snap=snap_code, cmp=cmp_code,
                                globals=tuple(globs), strength=strength, provenance=prov,
                                extent=tuple(s_ for s_, _p, _l in extent))
    mat, params, real, mut, reset = [], [], [], [], []
    arr_bind = {}
    for a in u.contents:
        ptr = _binding_for(binding, a, "expr")
        n = _binding_for(binding, a, "len")
        c = _cid(a)
        arr_bind[a] = (ptr, n)
        mat.append(f"std::vector<lact_v> A_{c} = lact_copy(({ptr}), (long long)({n})); "
                   f"std::vector<lact_v> M_{c} = A_{c};")
        params.append(f"const std::vector<lact_v>& A_{c}")
        real.append(f"A_{c}"); mut.append(f"M_{c}"); reset.append(f"M_{c} = A_{c};")
    for a in u.ranges:
        ptr = _binding_for(binding, a, "expr")
        n = _binding_for(binding, a, "len")
        c = _cid(a)
        # A null pointer is no buffer: its range is EMPTY whatever length is
        # bound (ticket 08, 2026-09-27).
        mat.append(f"const void* P_{c} = (const void*)({ptr}); "
                   f"long long Rlo_{c} = (long long)(std::uintptr_t)P_{c}; "
                   f"long long Rhi_{c} = (P_{c} && ({n}) > 0) ? Rlo_{c} + (long long)({n}) "
                   f"* (long long)sizeof(*({ptr})) : Rlo_{c}; "
                   f"long long MRlo_{c} = Rlo_{c}; long long MRhi_{c} = Rhi_{c};")
        params += [f"long long Rlo_{c}", f"long long Rhi_{c}"]
        real += [f"Rlo_{c}", f"Rhi_{c}"]; mut += [f"MRlo_{c}", f"MRhi_{c}"]
        reset.append(f"MRlo_{c} = Rlo_{c}; MRhi_{c} = Rhi_{c};")
    for a in u.cards:
        n = _binding_for(binding, a, "len")
        c = _cid(a)
        mat.append(f"lact_v C_{c} = (lact_v)({n}); lact_v MC_{c} = C_{c};")
        params.append(f"lact_v C_{c}"); real.append(f"C_{c}"); mut.append(f"MC_{c}")
        reset.append(f"MC_{c} = C_{c};")
    for a in u.scalars:
        e = _binding_for(binding, a, "expr")
        c = _cid(a)
        mat.append(f"lact_v S_{c} = (lact_v)({e}); lact_v MS_{c} = S_{c};")
        params.append(f"lact_v S_{c}"); real.append(f"S_{c}"); mut.append(f"MS_{c}")
        reset.append(f"MS_{c} = S_{c};")
    body = _Emit().pred(ast, {})

    def realize(code: str) -> str:
        def sub(m):
            name, idx, val = m.group(1), m.group(2), m.group(3)
            ptr, n = arr_bind[name]
            c = _cid(name)
            return (f"M_{c} = lact_mutclone(({ptr}), (long long)({n}), "
                    f"(long long)({idx}), (lact_v)({val}));")
        return _SET_RE.sub(sub, code)

    conjuncts = parts if (len(parts) > 1 and not finite) else [ast]
    negs = []
    for p in conjuncts:
        negs.append("{ " + " ".join(reset) + " bool lact_mut_ok = true; "
                    + realize(_negctl_mutation(p, finite=finite))
                    + f" lact_caught = lact_caught && lact_mut_ok && !lact_eval({', '.join(mut)}); }}")
    code = (f"{{ /* contract {pred.pid}: {pred.body.replace('*/', '* /')} */ "
            + lenchk_code + " "
            + "lact_copy_ok = true; " + " ".join(mat) + " "
            + f"auto lact_eval = [&]({', '.join(params)}) -> bool {{ return {body}; }}; "
            + f"bool lact_ok = lact_eval({', '.join(real)}); "
            + "bool lact_caught = true; " + " ".join(negs) + " "
            + "bool lact_ev = lact_copy_ok; "
            + f'lact_emit("{pred.pid}", {st}, lact_ok, lact_caught, lact_ev); {reach} }}')
    ext = tuple(s_ for s_, _p, _l in extent)
    if timing == "post":
        return EmittedPredicate(pred.pid, pred.family, post=code, globals=tuple(globs),
                                strength=strength, provenance=prov, extent=ext)
    return EmittedPredicate(pred.pid, pred.family, pre=code, globals=tuple(globs),
                            strength=strength, provenance=prov, extent=ext)


def _helpers(device_tu: bool, region_id: str, verdict_path: str) -> str:
    """Lambdas every probe block uses (defined in each probe and each deleter,
    never captured across frames).

    `lact_copy(p, n)`: the n elements at p as `lact_v`, read on the host (in a
    CUDA TU device memory is detected and copied after a synchronization; a
    failed copy makes the predicate NOT EVALUABLE, never a fail).
    `lact_mutclone(p, n, i, v)`: a native-type copy of the real buffer with
    element i set to (T)v, converted like `lact_copy` (the negative control).
    `lact_emit`: writes a PROP line only when the pid's state gains a new
    status (output volume is capped; every execution is still checked)."""
    vp = json.dumps(verdict_path)
    rid = region_id.replace("\\", "\\\\").replace('"', '\\"')
    read_host = ("for (long long k = 0; k < n; ++k) h[(std::size_t)k] = p[k];")
    fetch = read_host + " return true;"
    return (
        "bool lact_copy_ok = true; "
        "auto lact_fetch = [&lact_copy_ok](const auto* p, long long n, auto& h) -> bool { "
        "using T = typename std::remove_cv<typename std::remove_reference<decltype(*p)>::type>::type; "
        "(void)sizeof(T); " + fetch + " }; "
        "auto lact_copy = [&lact_fetch](const auto* p, long long n) -> std::vector<lact_v> { "
        "std::vector<lact_v> v; if (!p || n <= 0) return v; "
        "using T = typename std::remove_cv<typename std::remove_reference<decltype(*p)>::type>::type; "
        "std::vector<T> h((std::size_t)n); if (!lact_fetch(p, n, h)) return v; "
        "v.resize((std::size_t)n); for (long long k = 0; k < n; ++k) "
        "v[(std::size_t)k] = (lact_v)h[(std::size_t)k]; return v; }; "
        "auto lact_mutclone = [&lact_fetch](const auto* p, long long n, long long i, lact_v x) "
        "-> std::vector<lact_v> { std::vector<lact_v> v; if (!p || n <= 0 || i < 0 || i >= n) "
        "return v; using T = typename std::remove_cv<typename std::remove_reference<decltype(*p)>"
        "::type>::type; std::vector<T> h((std::size_t)n); if (!lact_fetch(p, n, h)) return v; "
        "h[(std::size_t)i] = (T)x; v.resize((std::size_t)n); for (long long k = 0; k < n; ++k) "
        "v[(std::size_t)k] = (lact_v)h[(std::size_t)k]; return v; }; "
        "auto lact_same = [](const std::vector<lact_v>& a, const std::vector<lact_v>& b) -> bool { "
        "if (a.size() != b.size()) return false; for (std::size_t k = 0; k < a.size(); ++k) "
        "if (!(a[k] == b[k] || (a[k] != a[k] && b[k] != b[k]))) return false; return true; }; "
        "auto lact_idx_ok = [](lact_v k, std::size_t n) -> bool { return k >= 0 && "
        "k < (lact_v)n && k == (lact_v)(long long)k; }; "
        "auto lact_all_distinct = [](const std::vector<lact_v>& a) -> bool { "
        "for (lact_v x : a) if (x != x) return false; std::vector<lact_v> u(a); "
        "std::sort(u.begin(), u.end()); return std::adjacent_find(u.begin(), u.end()) == u.end(); }; "
        "auto lact_above = [](lact_v r) -> lact_v { return r + 1 + std::fabs(r) * 1e-9L; }; "
        "auto lact_below = [](lact_v r) -> lact_v { return r - 1 - std::fabs(r) * 1e-9L; }; "
        "auto lact_ne = [](lact_v r) -> lact_v { return r + 1 + std::fabs(r); }; "
        "(void)lact_copy; (void)lact_mutclone; (void)lact_same; (void)lact_idx_ok; "
        "(void)lact_all_distinct; (void)lact_above; (void)lact_below; (void)lact_ne; "
        "auto lact_emit = [](const char* pid, unsigned& st, bool ok, bool caught, bool ev) { "
        "unsigned w = !ev ? 1u : (ok ? 2u : 4u); unsigned wn = (caught && ev) ? 8u : 16u; "
        "if ((st & w) && (st & wn)) return; "
        "const char* vp = std::getenv(\"LACT_REGION_VERDICT\"); "
        f"std::FILE* f = std::fopen(vp ? vp : {vp}, \"a\"); if (!f) return; "
        f"if (!(st & w)) std::fprintf(f, \"PROP {rid}::{PROP_CONTRACT}%s %s\\n\", pid, "
        "w == 1u ? \"SKIP\" : (w == 2u ? \"PASS\" : \"FAIL\")); "
        f"if (!(st & wn)) std::fprintf(f, \"PROP {rid}::{PROP_CONTRACT_NEGCTL}%s %s\\n\", pid, "
        "wn == 8u ? \"PASS\" : \"SKIP\"); "
        "st |= w | wn; std::fclose(f); }; (void)lact_emit; "
        # Per-site reach line (code review, 2026-09-30 ET): never FAIL (the
        # pid line carries the verdict); PASS = evaluated at this site.
        "auto lact_reach = [](const char* name, unsigned& st, bool ev) { "
        "unsigned w = ev ? 2u : 1u; if (st & w) return; "
        "const char* vp = std::getenv(\"LACT_REGION_VERDICT\"); "
        f"std::FILE* f = std::fopen(vp ? vp : {vp}, \"a\"); if (!f) return; "
        f"std::fprintf(f, \"PROP {rid}::{PROP_CONTRACT}%s %s\\n\", name, "
        "w == 2u ? \"PASS\" : \"SKIP\"); st |= w; std::fclose(f); }; (void)lact_reach; "
        "auto lact_lenemit = [](const char* pid, const char* sym, unsigned& st, int r, int src, "
        "long long cap, long long need) { "
        "unsigned w = r > 0 ? 2u : (r == 0 ? 4u : (r == -2 ? 8u : 1u)); "
        "if (st & w) return; st |= w; "
        "const char* srcs[5] = {\"unknown\", \"device_address_range\", "
        "\"macos_malloc_size\", \"asan_allocated_size\", \"asan_malloc_size\"}; "
        "const char* vp = std::getenv(\"LACT_REGION_VERDICT\"); "
        f"std::FILE* f = std::fopen(vp ? vp : {vp}, \"a\"); if (!f) return; "
        f"std::fprintf(f, \"PROP {rid}::{PROP_CONTRACT_LEN}%s|%s|src=%s|cap=%lld|need=%lld %s\\n\", "
        "pid, sym, srcs[(src >= 0 && src < 5) ? src : 0], cap, need, "
        "w == 2u ? \"PASS\" : (w == 4u ? \"MISMATCH\" : (w == 8u ? \"INEXACT\" : \"SKIP\"))); "
        "std::fclose(f); }; "
        "(void)lact_lenemit;")


@dataclass
class ContractProbe:
    """The emitted probes of one region: (call_line, method, expression) per
    probed call, file-scope `globals`, and per-pid bookkeeping."""
    probes: List[Tuple[int, str, str]] = field(default_factory=list)
    globals: List[str] = field(default_factory=list)
    required: List[str] = field(default_factory=list)
    bound: List[str] = field(default_factory=list)
    unbound: dict = field(default_factory=dict)   # pid -> reason text
    families: dict = field(default_factory=dict)  # pid -> family
    strength: dict = field(default_factory=dict)  # pid -> call_bound | model_bound
    provenance: dict = field(default_factory=dict)  # pid -> {symbol: source}
    writes_scope: dict = field(default_factory=dict)  # pid -> "L<a>-L<b>"
    extent: dict = field(default_factory=dict)  # pid -> [symbols extent-checked at run time]
    #: pid -> [site tags] where the pid is EVALUATED (code review, 2026-09-30
    #: ET): a pid planned at several sites is exercised only if every one of
    #: them wrote its reach line (`site_reach_name`).
    site_tags: dict = field(default_factory=dict)

    @property
    def code(self) -> str:                        # any probe at all?
        return "".join(p[2] for p in self.probes)

    def to_record(self) -> dict:
        return {"required": list(self.required), "bound": list(self.bound),
                "unbound": dict(self.unbound), "families": dict(self.families),
                "strength": dict(self.strength), "provenance": dict(self.provenance),
                "writes_scope": dict(self.writes_scope), "extent": dict(self.extent),
                "site_tags": {k: list(v) for k, v in self.site_tags.items()},
                "sites": [{"line": p[0], "method": p[1],
                           "var": p[3] if len(p) > 3 else ""} for p in self.probes]}


def _site_binding(binding: Mapping, site, entry_id: str) -> Mapping:
    """A binding keyed per site (`site.key`), or by entry id alone."""
    for k in (site.key, entry_id):
        b = (binding or {}).get(k) if k else None
        if isinstance(b, Mapping):
            return b
    return {}


def emit_contract_probe(plan: ContractPlan, binding: Mapping, *, region_id: str,
                        verdict_path: str, device_tu: bool) -> ContractProbe:
    """Every site of the plan -> one single-line C++ EXPRESSION per probed call,
    spliced as `(EXPR, call)` immediately before it.

    EXPR is an immediately-invoked lambda that runs on EVERY execution of the
    call (serialized by a file-scope mutex; output capped per pid), checks the
    "pre" predicates on the state the call consumes, and returns a
    `std::shared_ptr<void>` temporary whose deleter runs the "post" checks at
    the end of the full expression, i.e. after the call returned. A pid is
    `bound` only if it could be emitted at EVERY site it is planned at."""
    probe = ContractProbe()
    probe.globals.append("static std::mutex lact_contract_mu;")
    helpers = _helpers(device_tu, region_id, verdict_path)
    per_call: dict = {}
    failed_pid: dict = {}
    for p in plan.predicates:
        probe.required.append(p.pid)
        probe.families[p.pid] = p.family
    for site in plan.sites:
        slot = per_call.setdefault((site.call_line, site.call_method, site.call_var),
                                   {"pre": [], "post": []})
        ev = dict(site.origins)
        stag = site_reach_tag(site)
        for p in site.predicates:
            try:
                ep = emit_predicate(p, _site_binding(binding, site, p.entry_id),
                                    region_id=region_id, device_tu=device_tu,
                                    timing=site.timing, key=site.key, evidence=ev,
                                    site_tag=stag)
            except EmitError as e:
                failed_pid.setdefault(p.pid, f"{site.key or site.call_line}: {e}")
                continue
            if site.timing != "snap":
                tags = probe.site_tags.setdefault(p.pid, [])
                if stag not in tags:
                    tags.append(stag)
            prev = probe.strength.get(p.pid)
            both = (prev, ep.strength)
            probe.strength[p.pid] = ("model_bound" if "model_bound" in both else
                                     "extent" if "extent" in both else "call_bound")
            if ep.extent:
                probe.extent.setdefault(p.pid, [])
                probe.extent[p.pid] += [x for x in ep.extent if x not in probe.extent[p.pid]]
            probe.provenance.setdefault(p.pid, {})[site.key or str(site.call_line)] = \
                dict(ep.provenance)
            for g in ep.globals:
                if g not in probe.globals:
                    probe.globals.append(g)
            if site.timing == "snap":
                slot["pre"].append(ep.snap)
                probe.writes_scope[p.pid] = f"L{site.span[0]}-L{site.span[1]}"
            elif site.timing == "cmp":
                slot["post"].append(ep.cmp)
            elif ep.post:
                slot["post"].append(ep.post)
            else:
                slot["pre"].append(ep.pre)
    for pid, why in plan.unprobed:
        if pid not in probe.required:
            probe.required.append(pid)
        failed_pid.setdefault(pid, why)
    for pid in probe.required:
        if pid in failed_pid:
            probe.unbound[pid] = failed_pid[pid]
        elif pid in probe.strength:
            probe.bound.append(pid)
    for (line, method, var), slot in per_call.items():
        if not (slot["pre"] or slot["post"]) or not line:
            continue
        if slot["post"]:
            ret = ("return std::shared_ptr<void>(nullptr, [&](void*) { "
                   "std::lock_guard<std::mutex> lact_g(lact_contract_mu); " + helpers + " "
                   + " ".join(slot["post"]) + " });")
        else:
            ret = "return std::shared_ptr<void>();"
        code = ("[&]() -> std::shared_ptr<void> { /* LACT contract probe (deterministic emitter) */ "
                "{ std::lock_guard<std::mutex> lact_g(lact_contract_mu); " + helpers + " "
                + " ".join(slot["pre"]) + " } " + ret + " }()")
        probe.probes.append((line, method, code, var))
    return probe




#: Prepended to the instrumented file when a probe is spliced in.
PROBE_INCLUDES = ("#include <vector>\n#include <cstdio>\n#include <cstdlib>\n"
                  "#include <cstddef>\n#include <cstdint>\n#include <type_traits>\n"
                  "#include <algorithm>\n#include <memory>\n#include <mutex>\n#include <cmath>\n"
                  "typedef long double lact_v;\n")


@dataclass(frozen=True)
class _Tok:
    kind: str
    text: str
    line: int
    start: int
    end: int


_TOKEN = re.compile(r"""(?P<ws>\s+)|(?P<comment>//[^\n]*|/\*.*?\*/)|(?P<str>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|"""
                    r"""(?P<id>[A-Za-z_]\w*)|(?P<num>\d[\w.']*)|(?P<op>->|::|>>|<<|[^\s\w])""", re.S)


def tokenize(source: str) -> list:
    """A minimal C++ tokenizer (SWDB replacement for refiner.executor_calls.tokenize)."""
    out, line = [], 1
    for m in _TOKEN.finditer(source):
        text = m.group(0)
        kind = m.lastgroup
        if kind not in ("ws", "comment"):
            out.append(_Tok(kind, text, line, m.start(), m.end()))
        line += text.count("\n")
    return out


def _skip_template_args(toks, k: int) -> int:
    if k < len(toks) and toks[k].text == "<":
        depth = 0
        while k < len(toks):
            if toks[k].text == "<":
                depth += 1
            elif toks[k].text in (">", ">>"):
                depth -= 1 if toks[k].text == ">" else 2
                if depth <= 0:
                    return k + 1
            k += 1
    return k

def locate_call(source: str, call_line: int, method: str,
                var: str = "") -> Optional[Tuple[int, int]]:
    """(start, end) character offsets of the whole call expression
    `[obj.|obj->|Qual::]method[<targs>](args)` on `call_line`, or None. With
    `var` (an identifier), the call whose receiver is `var` is chosen, so two
    calls of one method on one line are told apart."""
    toks = tokenize(source)
    idx = None
    want = var if re.fullmatch(r"[A-Za-z_]\w*", var or "") else ""
    for k, t in enumerate(toks):
        if t.line == call_line and t.kind == "id" and t.text == method and k > 0 \
                and toks[k - 1].text in (".", "->", "::", "template"):
            if want:
                r = k - 2 if toks[k - 1].text != "template" else k - 3
                if not (r >= 0 and toks[r].text == want):
                    continue
            idx = k
            break
    if idx is None:
        return None
    j = _skip_template_args(toks, idx + 1)
    if j >= len(toks) or toks[j].text != "(":
        return None
    depth, k = 0, j
    while k < len(toks):
        if toks[k].text == "(":
            depth += 1
        elif toks[k].text == ")":
            depth -= 1
            if depth == 0:
                break
        k += 1
    if k >= len(toks):
        return None
    end = toks[k].end
    s = idx
    while s > 0:
        prev = toks[s - 1].text
        if prev == "template":
            s -= 1
            continue
        if prev in (".", "->", "::"):
            q = s - 2
            if q >= 0 and toks[q].text in (">", ">>"):          # Cls<...>::f
                depth = 0
                while q >= 0:
                    if toks[q].text in (">", ">>"):
                        depth += 1 if toks[q].text == ">" else 2
                    elif toks[q].text == "<":
                        depth -= 1
                        if depth <= 0:
                            break
                    q -= 1
                q -= 1
            if q >= 0 and toks[q].kind == "id":
                s = q
                continue
            if q >= 0 and toks[q].text in (")", "]"):            # f(x).g(), a[i].g()
                s = q + 1
                break
            if prev == "::" and (q < 0 or toks[q].kind != "id"):
                s -= 1
            break
        break
    return toks[s].start, end


def splice_probes(source: str, probes: Iterable[Tuple], globals_: Sequence[str] = ()
                  ) -> Tuple[str, list]:
    """Wrap each located executor call with ALL its probes, last call first so
    earlier offsets stay valid; prepend the includes and the file-scope
    globals once. `probes`: (call_line, method, code[, receiver var]).
    Returns (text, [(call_line, method, spliced_bool)])."""
    located: dict = {}
    report = []
    for pr in probes:
        line, method, code = pr[0], pr[1], pr[2]
        var = pr[3] if len(pr) > 3 else ""
        loc = locate_call(source, line, method, var) if code and "\n" not in code else None
        report.append((line, method, loc is not None))
        if loc is not None:
            located.setdefault(loc, []).append(code)
    starts = sorted(located)
    for a, b in zip(starts, starts[1:]):
        if b[0] < a[1] and not (a[0] <= b[0] and b[1] <= a[1]):
            raise ValueError(f"overlapping probed calls at offsets {a} and {b}")
    text = source
    for (start, end) in sorted(located, key=lambda x: (-x[0], x[1])):
        codes = located[(start, end)]
        text = text[:start] + "(" + ", ".join(codes) + ", " + text[start:end] + ")" + text[end:]
    if located:
        text = PROBE_INCLUDES + "".join(g + "\n" for g in dict.fromkeys(globals_)) + text
    return text, report


def splice_probe(source: str, call_line: int, method: str, code: str) -> Optional[str]:
    text, rep = splice_probes(source, [(call_line, method, code)])  # noqa: F841
    return text if rep and rep[0][2] else None


# --- reading the verdict back ------------------------------------------------

def _prop_status(props, name: str) -> str:
    """Aggregate over repeated PROP lines of one name: fail > skip > pass."""
    sts = [s for n, s in props if n == name]
    if not sts:
        return ""
    if "fail" in sts:
        return "fail"
    if "skip" in sts:
        return "skip"
    return "pass"


def _props_list(properties) -> list:
    props = []
    for p in properties or ():
        if isinstance(p, Mapping):
            name, st = p.get("name"), p.get("status")
        elif isinstance(p, (tuple, list)):
            name, st = p[0], p[1]
        else:
            name, st = getattr(p, "name", None), getattr(p, "status", None)
        props.append((str(name), str(st).lower()))
    return props


# --- SWDB plans, entry predicates and the certification record (2026-10-03 ET) ----

_ALGEBRA = re.compile(r"reduction_op\s+in\s*\{|associative\s*\(|commutative\s*\(|exact\s*\(")


def runtime_checkable_predicates(entry: Mapping) -> List[Tuple[str, str]]:
    """(clause id, predicate) of an entry's runtime-checkable formal halves, in order.

    Ported selection (dsl_contract.runtime_checkable_predicates): operator-algebra
    predicates route to tolerance, never to a runtime check; unparseable predicates
    are kept only with a runtime-family marker."""
    from swdb.predicate_grammar import ParseError, parse
    out = []
    for clause in entry.get("clauses", []) or []:
        formal = clause.get("formal") or {}
        if formal.get("language") != "extensa_predicate":
            continue
        body = (formal.get("predicate") or "").strip()
        if not body or _ALGEBRA.search(body):
            continue
        try:
            parse(body)
        except ParseError:
            if not re.search(r"<\s*\||alias\(|disjoint\(|finite|not\s+writes|writes\(", body):
                continue
        out.append((clause["id"], body))
    return out


def predicates_for_entry(entry: Mapping) -> List[ContractPredicate]:
    from swdb.predicate_grammar import ParseError, parse
    out = []
    for rid, body in runtime_checkable_predicates(entry):
        try:
            fam = family_of(parse(body))
        except ParseError:
            fam = "finite" if _FINITE.match(body) else "unparseable"
        out.append(ContractPredicate(entry["id"], rid, body, fam))
    return out


@dataclass(frozen=True)
class ContractSite:
    """One probed call and the predicates checked there (SWDB: named by the build)."""
    call_line: int
    call_method: str
    call_var: str
    predicates: Tuple[ContractPredicate, ...]
    timing: str = "pre"
    key: str = ""
    span: Tuple[int, int] = (0, 0)
    origins: Mapping = field(default_factory=dict)   # symbol -> operand origin

    def to_record(self) -> dict:
        return {"timing": self.timing, "key": self.key, "span": list(self.span),
                "call": {"line": self.call_line, "method": self.call_method, "var": self.call_var},
                "origins": dict(self.origins),
                "predicates": [dict(asdict(p), pid=p.pid) for p in self.predicates]}


@dataclass(frozen=True)
class ContractPlan:
    sites: Tuple[ContractSite, ...] = ()
    unprobed: Tuple[Tuple[str, str], ...] = ()
    reason: str = ""

    @property
    def predicates(self) -> Tuple[ContractPredicate, ...]:
        seen, out = set(), []
        for s in self.sites:
            for p in s.predicates:
                if p.pid not in seen:
                    seen.add(p.pid)
                    out.append(p)
        return tuple(out)

    @property
    def required_pids(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys([p.pid for p in self.predicates] + [pid for pid, _ in self.unprobed]))

    @property
    def blocking_reason(self) -> str:
        if self.reason:
            return self.reason
        if self.unprobed:
            return self.unprobed[0][1].split(":", 1)[0]
        if not self.sites:
            return REASON_NO_RUNTIME_PREDICATES
        return ""


def plan_for_entry(entry: Mapping, sites: Sequence[Mapping]) -> ContractPlan:
    """Bind an entry's predicates to explicit call sites.

    Each site mapping: {line, method, var?, timing? (pre|post), predicates? (clause ids;
    default every predicate), origins: {symbol: origin}}."""
    preds = predicates_for_entry(entry)
    if not preds:
        return ContractPlan(reason=REASON_NO_RUNTIME_PREDICATES)
    by_id = {p.rule_id: p for p in preds}
    planned, out = set(), []
    for site in sites:
        chosen = tuple(by_id[c] for c in site.get("predicates", list(by_id)) if c in by_id)
        planned.update(p.rule_id for p in chosen)
        out.append(ContractSite(int(site["line"]), site["method"], site.get("var", ""), chosen,
                                site.get("timing", "pre"), site.get("key", ""),
                                tuple(site.get("span", (0, 0))), dict(site.get("origins", {}))))
    # A site that names its predicates scopes the probe: other predicates of the entry are
    # discharged elsewhere (their clause's own mode). Unscoped sites require every predicate.
    scoped = any("predicates" in site for site in sites)
    unprobed = () if scoped else tuple((p.pid, f"{REASON_NOT_EXERCISED}: no site names this predicate")
                                       for p in preds if p.rule_id not in planned)
    return ContractPlan(tuple(out), unprobed)


def read_verdict(path, region_id: str) -> list:
    """(name, status) PROP lines of one region from a verdict file."""
    props = []
    prefix = f"PROP {region_id}::"
    try:
        lines = Path(path).read_text().splitlines()
    except OSError:
        return props
    for line in lines:
        if line.startswith(prefix):
            name, _, status = line[len(prefix):].rpartition(" ")
            props.append((name, status.lower()))
    return props


def contract_record_from_verdict(plan: ContractPlan, probe: Optional[ContractProbe],
                                 properties: Sequence, *, spliced: Optional[bool] = None,
                                 probe_fault: str = "") -> dict:
    """Ported verifier record: required, bound, exercised, caught, passed, binding
    strength, and the named reason. Contract-checked = no blocking reason and every
    required pid bound, exercised, caught, passed and call-bound. A model-bound
    binding gets the separate, uncounted label `contract_checked_model_bound`."""
    props = _props_list(properties)
    required = list(plan.required_pids)
    bound = list(probe.bound) if probe else []
    strength = dict(probe.strength) if probe else {}
    status = {pid: _prop_status(props, PROP_CONTRACT + pid) for pid in bound}
    negst = {pid: _prop_status(props, PROP_CONTRACT_NEGCTL + pid) for pid in bound}
    site_tags = dict(probe.site_tags) if probe else {}
    site_reach = {pid: {tag: _prop_status(props, PROP_CONTRACT + site_reach_name(pid, tag))
                        for tag in site_tags.get(pid, ())}
                  for pid in bound if len(site_tags.get(pid, ())) > 1}
    unreached = {pid: [tag for tag, st in sr.items() if st != "pass"] for pid, sr in site_reach.items()}
    unreached = {pid: tags for pid, tags in unreached.items() if tags}
    evaluated = [pid for pid in bound if status[pid] in ("pass", "fail")]
    exercised = [pid for pid in evaluated if pid not in unreached]
    passed = [pid for pid in exercised if status[pid] == "pass"]
    failed = [pid for pid in evaluated if status[pid] == "fail"]
    caught = [pid for pid in exercised if negst[pid] == "pass"]
    failed_call = [pid for pid in failed if strength.get(pid) == "call_bound"]
    failed_model = [pid for pid in failed if strength.get(pid) != "call_bound"]
    model = [pid for pid in bound if strength.get(pid) != "call_bound"]
    unbound = dict(probe.unbound) if probe else {}
    if failed_call:
        reason = REASON_PREDICATE_FAILED
    elif plan.blocking_reason:
        reason = plan.blocking_reason
    elif probe_fault:
        reason = probe_fault.split(":", 1)[0]
    elif probe is None or unbound or len(bound) < len(required):
        reason = REASON_TRANSLATION_FAILED
    elif failed_model:
        reason = REASON_MODEL_BOUND_FAILED
    elif spliced is False or len(exercised) < len(required):
        reason = REASON_NOT_EXERCISED
    elif len(caught) < len(required):
        reason = REASON_TOOTHLESS
    elif model:
        reason = REASON_MODEL_BOUND
    else:
        reason = ""
    complete = bool(required) and set(passed) == set(required) and set(caught) == set(required)
    checked = not reason and complete
    return {"sites": [s.to_record() for s in plan.sites], "translation": "deterministic_emitter" if probe else "none",
            "required": required, "bound": bound, "unbound": unbound,
            "families": dict(probe.families) if probe else {p.pid: p.family for p in plan.predicates},
            "binding_strength": strength, "binding_provenance": dict(probe.provenance) if probe else {},
            "exercised": exercised, "site_reach": site_reach, "unreached_sites": unreached,
            "caught": caught, "passed": passed, "failed": failed, "failed_call_bound": failed_call,
            "failed_model_bound": failed_model, "probe_fault": probe_fault,
            "contract_checked": bool(checked),
            "contract_checked_model_bound": bool(reason == REASON_MODEL_BOUND and complete),
            "reason": "" if checked else (reason or REASON_ERROR)}


def certification_matrix_cell(record: Mapping, *, cell: str) -> dict:
    """One certification matrix cell from a contract record. A model-bound check never
    passes a cell (it does not count toward certification)."""
    return {"cell": cell, "check": "contract_probe", "status": "passed" if record["contract_checked"] else "failed",
            "reason": record["reason"] or "contract checked", "contract": record}


def probe_build_flags() -> list:
    """Probes compile only into certification builds; they need C++14 generic lambdas."""
    return ["-std=c++17", "-DSWDB_CONTRACT_PROBES=1"]


PROBE_SYMBOL = "lact_contract_mu"


def assert_probe_free(binary: Path) -> None:
    """A timed build must contain no probe symbol."""
    data = Path(binary).read_bytes()
    if PROBE_SYMBOL.encode() in data or b"LACT contract probe" in data or b"contract_negctl." in data:
        raise ValueError(f"timed build {binary} contains contract-probe code")
