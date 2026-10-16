# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# A small evaluator of ACSL predicates and terms over recorded concrete states, for the bounded hint
# falsifier. It only ever answers True, False or Unknown for ONE concrete state; it proves nothing.
# Soundness direction: a reported False must be a real counterexample, so every approximation
# (an unbounded quantifier evaluated over a finite window, an unreadable location, an unsupported
# construct) turns a False into Unknown. \initialized is read as true (not recorded), which can only
# hide counterexamples.
import re

TOKEN = re.compile(r"""
  (?P<ws>\s+) | (?P<num>0[xX][0-9a-fA-F]+[uUlL]*|\d+[uUlL]*) |
  (?P<op><==>|==>|\.\.|->|<<|>>|<=|>=|==|!=|&&|\|\||\^\^|[-+*/%<>!~&|^?:;,.(){}\[\]=]) |
  (?P<id>\\?[A-Za-z_][A-Za-z_0-9]*)
""", re.X)


class Unknown(Exception):
    pass


class Ptr:
    __slots__ = ("b", "i")

    def __init__(self, b, i):
        self.b, self.i = b, i

    def __eq__(self, o):
        return isinstance(o, Ptr) and self.b == o.b and self.i == o.i

    def __hash__(self):
        return hash((self.b, self.i))

    def __repr__(self):
        return f"&{self.b}[{self.i}]"


class Base:
    __slots__ = ("b",)

    def __init__(self, b):
        self.b = b

    def __eq__(self, o):
        return isinstance(o, Base) and self.b == o.b

    def __hash__(self):
        return hash(self.b)


class Range:
    __slots__ = ("p", "lo", "hi")

    def __init__(self, p, lo, hi):
        self.p, self.lo, self.hi = p, lo, hi


def tokenize(s):
    out, pos = [], 0
    s = re.sub(r"//[^\n]*", "", s)
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            raise Unknown(f"cannot tokenize at {s[pos:pos + 20]!r}")
        pos = m.end()
        if m.lastgroup != "ws":
            out.append((m.lastgroup, m.group(), m.start()))
    out.append(("eof", "", len(s)))
    return out


TYPE_WORDS = {"integer", "int", "unsigned", "size_t", "long", "char", "short", "bool", "boolean", "NodeID",
              "SGOffset", "int32_t", "uint32_t", "uint16_t", "int64_t", "uint64_t", "real", "const", "struct",
              "signed", "_Bool", "ptrdiff_t", "dxc_context", "Graph"}
BINDERS = {"\\forall", "\\exists", "\\let"}
# precedence climbing levels (low -> high); ternary and binders handled separately
LEVELS = [["<==>"], ["==>"], ["||", "^^"], ["&&"], ["|"], ["^"], ["&"], ["==", "!="],
          ["<", "<=", ">", ">="], ["<<", ">>"], ["+", "-"], ["*", "/", "%"]]
RIGHT = {"==>"}


class Parser:
    def __init__(self, text):
        self.text = text
        self.t = tokenize(text)
        self.k = 0

    def peek(self, o=0):
        return self.t[min(self.k + o, len(self.t) - 1)]

    def next(self):
        tok = self.t[self.k]
        self.k += 1
        return tok

    def expect(self, v):
        tok = self.next()
        if tok[1] != v:
            raise Unknown(f"expected {v!r}, got {tok[1]!r}")
        return tok

    def at(self, v):
        return self.peek()[1] == v

    def span(self, a, b):
        return self.text[a:b].strip()

    def parse_type(self):
        words = []
        while self.peek()[0] == "id" and (self.peek()[1] in TYPE_WORDS or (words and words[-1] == "struct")):
            words.append(self.next()[1])
        if not words:
            raise Unknown("expected a type")
        stars = 0
        while self.at("*"):
            self.next()
            stars += 1
        return (" ".join(words), stars)

    def is_cast(self):
        if not self.at("("):
            return False
        tok = self.peek(1)
        return tok[0] == "id" and tok[1] in TYPE_WORDS and tok[1] not in ("const",) or \
            (tok[1] == "const" and self.peek(2)[0] == "id")

    def expr(self):
        start = self.peek()[2]
        tok = self.peek()
        if tok[1] in BINDERS:
            self.next()
            if tok[1] == "\\let":
                name = self.next()[1]
                self.expect("=")
                val = self.expr_noseq()
                self.expect(";")
                body = self.expr()
                return ("let", name, val, body, self.span(start, self.peek()[2]))
            vars_ = []
            while True:
                ty = self.parse_type()
                while True:
                    name = self.next()[1]
                    vars_.append((name, ty))
                    if self.at(","):
                        self.next()
                        if self.peek()[0] == "id" and self.peek()[1] in TYPE_WORDS:
                            break
                        continue
                    break
                if self.at(";"):
                    break
            self.expect(";")
            body = self.expr()
            return ("quant", tok[1], vars_, body, self.span(start, self.peek()[2]))
        return self.expr_noseq()

    def expr_noseq(self):
        start = self.peek()[2]
        # named predicate "name: P"
        if self.peek()[0] == "id" and not self.peek()[1].startswith("\\") and self.peek(1)[1] == ":" \
                and self.peek(2)[1] != ":":
            self.next()
            self.next()
            return self.expr()
        c = self.binary(0)
        if self.at("?"):
            self.next()
            a = self.expr()
            self.expect(":")
            b = self.expr()
            return ("ite", c, a, b, self.span(start, self.peek()[2]))
        return c

    def binary(self, lvl):
        if lvl == len(LEVELS):
            return self.unary()
        start = self.peek()[2]
        left = self.binary(lvl + 1)
        ops = LEVELS[lvl]
        if ops[0] == "<":  # chained relations
            chain = [left]
            rels = []
            while self.peek()[1] in ops and self.peek()[0] == "op":
                rels.append(self.next()[1])
                chain.append(self.binary(lvl + 1))
            if rels:
                return ("chain", rels, chain, self.span(start, self.peek()[2]))
            return left
        while self.peek()[0] == "op" and self.peek()[1] in ops:
            op = self.next()[1]
            if op in RIGHT:
                right = self.expr_noseq_from(lvl)
            else:
                right = self.binary(lvl + 1)
            left = ("bin", op, left, right, self.span(start, self.peek()[2]))
            if op in RIGHT:
                break
        return left

    def expr_noseq_from(self, lvl):
        # right-hand side of ==> may be a binder or a full predicate of the same level
        if self.peek()[1] in BINDERS:
            return self.expr()
        return self.binary(lvl)

    def unary(self):
        start = self.peek()[2]
        tok = self.peek()
        if tok[0] == "op" and tok[1] in ("!", "-", "+", "~", "*", "&"):
            self.next()
            return ("un", tok[1], self.unary(), self.span(start, self.peek()[2]))
        if self.is_cast():
            self.next()
            ty = self.parse_type()
            self.expect(")")
            return ("cast", ty, self.unary(), self.span(start, self.peek()[2]))
        if tok[1] in BINDERS:
            return self.expr()
        return self.postfix()

    def postfix(self):
        start = self.peek()[2]
        e = self.primary()
        while True:
            if self.at("["):
                self.next()
                i = self.expr()
                if self.at(".."):
                    self.next()
                    hi = self.expr()
                    self.expect("]")
                    e = ("slice", e, i, hi, self.span(start, self.peek()[2]))
                    continue
                self.expect("]")
                e = ("idx", e, i, self.span(start, self.peek()[2]))
            elif self.at("."):
                self.next()
                e = ("dot", e, self.next()[1], self.span(start, self.peek()[2]))
            elif self.at("->"):
                self.next()
                e = ("arrow", e, self.next()[1], self.span(start, self.peek()[2]))
            else:
                return e

    def primary(self):
        start = self.peek()[2]
        tok = self.next()
        kind, v = tok[0], tok[1]
        if kind == "num":
            return ("num", int(v.rstrip("uUlL"), 0), v)
        if v == "(":
            e = self.expr()
            if self.at(".."):
                self.next()
                hi = self.expr()
                self.expect(")")
                return ("range", e, hi, self.span(start, self.peek()[2]))
            self.expect(")")
            return e
        if kind == "id":
            if v == "sizeof":
                self.expect("(")
                ty = self.parse_type()
                self.expect(")")
                return ("num", 8 if ty[1] or ty[0] in ("size_t", "long", "uint64_t", "int64_t") else 4, "sizeof")
            labels = None
            if self.at("{"):
                self.next()
                labels = []
                while not self.at("}"):
                    labels.append(self.next()[1])
                    if self.at(","):
                        self.next()
                self.expect("}")
            if self.at("("):
                self.next()
                args = []
                if v == "\\at":
                    args.append(self.expr())
                    self.expect(",")
                    args.append(("label", self.next()[1]))
                else:
                    while not self.at(")"):
                        args.append(self.expr())
                        if self.at(","):
                            self.next()
                self.expect(")")
                return ("call", v, labels, args, self.span(start, self.peek()[2]))
            return ("id", v, labels)
        raise Unknown(f"unexpected token {v!r}")


def parse(text):
    p = Parser(text)
    e = p.expr()
    if p.peek()[0] != "eof" and not p.at(";"):
        raise Unknown(f"trailing text {p.text[p.peek()[2]:p.peek()[2] + 30]!r}")
    return e


def parse_definition(text):
    """predicate name{L..}(params) = body;  |  logic T name{L..}(params) = body;"""
    p = Parser(text)
    kw = p.next()[1]
    if kw == "logic":
        p.parse_type()
    name = p.next()[1]
    labels = []
    if p.at("{"):
        p.next()
        while not p.at("}"):
            labels.append(p.next()[1])
            if p.at(","):
                p.next()
        p.expect("}")
    params = []
    if p.at("("):
        p.next()
        while not p.at(")"):
            ty = p.parse_type()
            params.append((p.next()[1], ty))
            if p.at(","):
                p.next()
        p.expect(")")
    p.expect("=")
    body = p.expr()
    return name, {"labels": labels, "params": params, "body": body, "kind": kw}


def header_definitions(text):
    """All predicate/logic definitions inside /*@ ... */ blocks of a header (not contracts)."""
    defs = {}
    for block in re.findall(r"/\*@(.*?)\*/", text, re.S):
        body = re.sub(r"//[^\n]*", "", block)
        for piece in re.split(r";\s*(?=predicate\b|logic\b|$)", body.strip()):
            piece = piece.strip().rstrip(";")
            if piece.startswith(("predicate", "logic")):
                try:
                    name, d = parse_definition(piece + ";")
                    defs[name] = d
                except Unknown:
                    pass
    return defs


CONSTS = {"DXC_NUM_TILES": 8, "DXC_NUM_REGS": 8, "SWDB_LQUEUE_CAPACITY": 16384, "PTRDIFF_MAX": 2**63 - 1,
          "SIZE_MAX": 2**64 - 1, "INT_MAX": 2**31 - 1, "INT_MIN": -2**31, "UINT_MAX": 2**32 - 1,
          "true": 1, "false": 0, "__ATOMIC_RELAXED": 0}
PARAM_PTRS = {"g": ("G", 0), "VertexOffsets": ("VO", 0), "parent": ("PV", 0), "queue": ("Q", 0)}
WINDOW = range(-4, 41)


UNSIGNED_BITS = {"unsigned": 32, "unsigned int": 32, "uint32_t": 32, "size_t": 64, "unsigned long": 64,
                 "uint64_t": 64, "unsigned long long": 64, "uint16_t": 16, "unsigned short": 16,
                 "unsigned char": 8}
SIGNED_BITS = {"int": 32, "int32_t": 32, "NodeID": 32, "SGOffset": 32, "signed": 32, "long": 64, "int64_t": 64,
               "long long": 64, "ptrdiff_t": 64, "short": 16, "char": 8}


def ctype(ty):
    """('u', bits) / ('s', bits) / ('bool',) / None (integer, pointer, struct) for a parsed type."""
    name, stars = ty
    if stars:
        return None
    name = name.replace("const ", "").strip()
    if name in UNSIGNED_BITS:
        return ("u", UNSIGNED_BITS[name])
    if name in SIGNED_BITS:
        return ("s", SIGNED_BITS[name])
    if name in ("bool", "_Bool"):
        return ("bool",)
    return None


def convert(ty, v):
    """C conversion of an integer value to type ty (modular for unsigned, wrap for signed: the x86_64 rule)."""
    t = ctype(ty)
    if t is None or not isinstance(v, (int, bool)) or isinstance(v, Ptr):
        return v
    v = int(v)
    if t[0] == "bool":
        return 1 if v else 0
    m = 1 << t[1]
    if t[0] == "u":
        return v % m
    v %= m
    return v - m if v >= m // 2 else v


def type_range(ty):
    t = ctype(ty)
    if t is None or t[0] == "bool":
        return None
    if t[0] == "u":
        return 0, (1 << t[1]) - 1
    return -(1 << (t[1] - 1)), (1 << (t[1] - 1)) - 1


def to_val(x):
    if isinstance(x, dict):
        if set(x) == {"b", "i"}:
            return Ptr(x["b"], x["i"])
        if x.get("null"):
            return Ptr(None, 0)
        return {k: to_val(v) for k, v in x.items()}
    if isinstance(x, list):
        return [to_val(v) for v in x]
    return x


class State:
    """One recorded event: memory, locals and ghost scalars."""

    def __init__(self, ev, ghosts=None):
        self.ev = ev
        self.mem = {k: to_val(v) for k, v in ev["mem"].items()}
        self.loc = {k: to_val(v) for k, v in ev["loc"].items()}
        self.ghost = dict(ghosts or {})
        self.count = {k: len(v) for k, v in ev["mem"].items() if isinstance(v, list)}
        self.count["swdb_lqueue_storage"] = 16384
        for k in ("Q", "VO", "PV", "G"):
            self.count[k] = 1
        self.dumped = {k: len(v) for k, v in ev["mem"].items() if isinstance(v, list)}


class Ctx:
    def __init__(self, labels, cur, defs, binds=None):
        self.labels = labels          # label name -> State
        self.cur = cur                # current label name
        self.defs = defs
        self.binds = binds or {}      # logic variables
        self.approx = [False]

    def child(self, binds=None, cur=None, labels=None):
        c = Ctx(labels if labels is not None else self.labels, cur or self.cur, self.defs,
                {**self.binds, **(binds or {})})
        c.approx = self.approx
        return c

    def state(self, label=None):
        lab = label or self.cur
        if lab not in self.labels:
            raise Unknown(f"label {lab} unavailable")
        return self.labels[lab]


def truth(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v != 0
    if isinstance(v, Ptr):
        return v.b is not None
    raise Unknown("non-scalar truth value")


def read(ctx, p, idx=0):
    if isinstance(p, list):
        i = idx
        if not 0 <= i < len(p):
            raise Unknown("index out of struct array")
        return p[i]
    if not isinstance(p, Ptr) or p.b is None:
        raise Unknown("read through a non-pointer")
    st = ctx.state()
    blk = st.mem.get(p.b)
    i = p.i + idx
    if isinstance(blk, dict):
        if i != 0:
            raise Unknown("struct pointer arithmetic")
        return blk
    if blk is None or not 0 <= i < st.dumped.get(p.b, 0):
        raise Unknown(f"unrecorded location {p.b}[{i}]")
    return blk[i]


def ident(ctx, name):
    if name in ctx.binds:
        return ctx.binds[name]
    st = ctx.state()
    if name in st.ghost:
        return st.ghost[name]
    here = ctx.labels.get("Here")
    for s in (st, here):
        if s is not None and name in s.loc:
            return s.loc[name]
        if s is not None and name in s.ghost:
            return s.ghost[name]
    if name in PARAM_PTRS:
        return Ptr(*PARAM_PTRS[name])
    if name in st.mem.get("scalars", {}):
        return st.mem["scalars"][name]
    if name in st.mem and isinstance(st.mem[name], list):
        return Ptr(name, 0)
    if name in CONSTS:
        return CONSTS[name]
    raise Unknown(f"unknown name {name}")


def arith(op, a, b):
    if isinstance(a, bool):
        a = int(a)
    if isinstance(b, bool):
        b = int(b)
    if isinstance(a, Ptr) or isinstance(b, Ptr):
        if op == "+" and isinstance(a, Ptr) and isinstance(b, int):
            return Ptr(a.b, a.i + b)
        if op == "+" and isinstance(b, Ptr) and isinstance(a, int):
            return Ptr(b.b, b.i + a)
        if op == "-" and isinstance(a, Ptr) and isinstance(b, int):
            return Ptr(a.b, a.i - b)
        if op == "-" and isinstance(a, Ptr) and isinstance(b, Ptr) and a.b == b.b:
            return a.i - b.i
        raise Unknown("pointer arithmetic")
    if not isinstance(a, int) or not isinstance(b, int):
        raise Unknown("non-integer arithmetic")
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op in ("/", "%"):
        if b == 0:
            raise Unknown("division by zero")
        q = abs(a) // abs(b) * (1 if (a >= 0) == (b >= 0) else -1)
        return q if op == "/" else a - q * b
    if op == "<<":
        return a << b
    if op == ">>":
        return a >> b
    if op == "&":
        return a & b
    if op == "|":
        return a | b
    if op == "^":
        return a ^ b
    raise Unknown(op)


def compare(op, a, b):
    if isinstance(a, bool):
        a = int(a)
    if isinstance(b, bool):
        b = int(b)
    if isinstance(a, (Ptr, Base)) or isinstance(b, (Ptr, Base)):
        if op in ("==", "!="):
            eq = a == b
            return eq if op == "==" else not eq
        if isinstance(a, Ptr) and isinstance(b, Ptr) and a.b == b.b:
            a, b = a.i, b.i
        else:
            raise Unknown("pointer order across blocks")
    if not isinstance(a, int) or not isinstance(b, int):
        raise Unknown("comparison of non-scalars")
    return {"==": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def valid(ctx, v, read_only=False):
    if isinstance(v, Range):
        p, lo, hi = v.p, v.lo, v.hi
        if hi < lo:
            return True
    elif isinstance(v, Ptr):
        p, lo, hi = v, 0, 0
    else:
        raise Unknown("\\valid of a non-pointer")
    if p.b is None:
        return False
    n = ctx.state().count.get(p.b)
    if n is None:
        raise Unknown("validity of an unknown block")
    return 0 <= p.i + lo and p.i + hi < n


def mentions(e, names):
    if isinstance(e, tuple):
        if e[0] == "id" and e[1] in names:
            return True
        return any(mentions(x, names) for x in e[1:])
    if isinstance(e, list):
        return any(mentions(x, names) for x in e)
    return False


def conjuncts(e):
    if isinstance(e, tuple) and e[0] == "bin" and e[1] == "&&":
        return conjuncts(e[2]) + conjuncts(e[3])
    return [e]


def bounds_for(var, guard_parts, ctx, others):
    lo = hi = None
    for g in guard_parts:
        if g[0] == "chain":
            items, rels = g[2], g[1]
        elif g[0] == "bin" and g[1] == "==":
            items, rels = [g[2], g[3]], ["=="]
        else:
            continue
        for k, rel in enumerate(rels):
            a, b = items[k], items[k + 1]
            for x, y, flip in ((a, b, False), (b, a, True)):
                if x == ("id", var, None) and not mentions(y, others | {var}):
                    try:
                        val = eval_term(ctx, y)
                    except Unknown:
                        continue
                    if not isinstance(val, int):
                        continue
                    r = rel if not flip else {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "=="}[rel]
                    if r == "<":
                        hi = val - 1 if hi is None else min(hi, val - 1)
                    elif r == "<=":
                        hi = val if hi is None else min(hi, val)
                    elif r == ">":
                        lo = val + 1 if lo is None else max(lo, val + 1)
                    elif r == ">=":
                        lo = val if lo is None else max(lo, val)
                    elif r == "==":
                        lo = val if lo is None else max(lo, val)
                        hi = val if hi is None else min(hi, val)
    return lo, hi


def eval_quant(ctx, kind, vars_, body):
    for _, ty in vars_:
        if ty[1] or ty[0].startswith("struct"):
            raise Unknown("quantifier over pointers or structs")
    names = {n for n, _ in vars_}
    if kind == "\\forall" and body[0] == "bin" and body[1] == "==>":
        guard, rest = conjuncts(body[2]), body[3]
    elif kind == "\\exists":
        guard, rest = conjuncts(body), None
    else:
        guard, rest = [], body
    want = kind == "\\forall"

    def go(i, binds):
        if i == len(vars_):
            c = ctx.child(binds)
            return eval_pred(c, body)
        name = vars_[i][0]
        c = ctx.child(binds)
        lo, hi = bounds_for(name, guard, c, names - set(binds) - {name})
        tr = type_range(vars_[i][1])
        if tr is not None:
            lo = tr[0] if lo is None else max(lo, tr[0])
            hi_t = tr[1]
        else:
            hi_t = None
        if lo is None or hi is None:
            w_lo = WINDOW.start if lo is None else lo
            w_hi = WINDOW.stop - 1 if hi is None else hi
            if hi_t is not None:
                w_hi = min(w_hi, hi_t)
            dom, approx = range(w_lo, max(w_lo, w_hi) + 1), True
        else:
            if hi - lo > 2000:
                raise Unknown("quantifier range too large")
            dom, approx = range(lo, hi + 1), False
        unknown = False
        for x in dom:
            try:
                r = go(i + 1, {**binds, name: x})
            except Unknown:
                unknown = True
                continue
            if r != want:
                return not want
        if unknown:
            raise Unknown("quantifier instance unknown")
        if approx:
            ctx.approx[0] = True
        return want

    return go(0, {})


def call(ctx, name, labels, args):
    if name == "\\at":
        lab = args[1][1]
        if lab == "Old":
            lab = "Pre"
        return eval_term(ctx.child(cur=lab), args[0])
    if name == "\\old":
        return eval_term(ctx.child(cur="Pre"), args[0])
    if name in ("\\valid", "\\valid_read"):
        return valid(ctx, eval_term(ctx, args[0]))
    if name == "\\object_pointer":
        p = eval_term(ctx, args[0])
        if not isinstance(p, Ptr) or p.b is None:
            return False
        n = ctx.state().count.get(p.b)
        if n is None:
            raise Unknown("object of an unknown block")
        return 0 <= p.i <= n
    if name == "\\initialized":
        return True
    if name == "\\base_addr":
        p = eval_term(ctx, args[0])
        if not isinstance(p, Ptr):
            raise Unknown("base of a non-pointer")
        return Base(p.b)
    if name == "\\offset":
        p = eval_term(ctx, args[0])
        if not isinstance(p, Ptr):
            raise Unknown("offset of a non-pointer")
        return p.i * 4
    if name == "\\separated":
        vals = [eval_term(ctx, a) for a in args]
        spans = []
        for v in vals:
            if isinstance(v, Range):
                spans.append((v.p.b, v.p.i + v.lo, v.p.i + v.hi))
            elif isinstance(v, Ptr):
                spans.append((v.b, v.i, v.i))
            else:
                raise Unknown("separated of a non-location")
        for a in range(len(spans)):
            for b in range(a + 1, len(spans)):
                x, y = spans[a], spans[b]
                if x[0] == y[0] and x[1] <= x[2] and y[1] <= y[2] and not (x[2] < y[1] or y[2] < x[1]):
                    return False
        return True
    if name in ("\\abs",):
        return abs(eval_term(ctx, args[0]))
    if name in ("\\max", "\\min"):
        a, b = eval_term(ctx, args[0]), eval_term(ctx, args[1])
        return max(a, b) if name == "\\max" else min(a, b)
    d = ctx.defs.get(name)
    if d is None:
        raise Unknown(f"unknown function {name}")
    if len(args) != len(d["params"]):
        raise Unknown(f"arity of {name}")
    vals = {p: eval_term(ctx, a) for (p, _), a in zip(d["params"], args)}
    labmap = {}
    if d["labels"]:
        given = labels or [ctx.cur] * len(d["labels"])
        if len(given) != len(d["labels"]):
            raise Unknown(f"label arity of {name}")
        for formal, actual in zip(d["labels"], given):
            actual = "Pre" if actual == "Old" else actual
            labmap[formal] = ctx.state(actual)
    new_labels = {**ctx.labels, **labmap}
    cur = d["labels"][0] if d["labels"] else ctx.cur
    c = Ctx(new_labels, cur, ctx.defs, vals)
    c.approx = ctx.approx
    return eval_any(c, d["body"])


def eval_any(ctx, e):
    return eval_term(ctx, e)


def eval_pred(ctx, e):
    return truth(eval_term(ctx, e))


def eval_term(ctx, e):
    k = e[0]
    if k == "num":
        return e[1]
    if k == "id":
        n = e[1]
        if n == "\\true":
            return True
        if n == "\\false":
            return False
        if n == "\\null":
            return Ptr(None, 0)
        d = ctx.defs.get(n)
        if d is not None and not d["params"] and n not in ctx.binds:
            return call(ctx, n, e[2], [])
        return ident(ctx, n)
    if k == "quant":
        return eval_quant(ctx, e[1], e[2], e[3])
    if k == "let":
        return eval_term(ctx.child({e[1]: eval_term(ctx, e[2])}), e[3])
    if k == "ite":
        return eval_term(ctx, e[2]) if eval_pred(ctx, e[1]) else eval_term(ctx, e[3])
    if k == "chain":
        vals = [eval_term(ctx, x) for x in e[2]]
        return all(compare(r, vals[i], vals[i + 1]) for i, r in enumerate(e[1]))
    if k == "bin":
        op = e[1]
        if op in ("&&", "||", "==>", "<==>", "^^"):
            def side(x):
                try:
                    return eval_pred(ctx, x)
                except Unknown:
                    return None
            a = side(e[2])
            if op == "&&" and a is False:
                return False
            if op == "||" and a is True:
                return True
            if op == "==>" and a is False:
                return True
            b = side(e[3])
            if op == "&&":
                if b is False:
                    return False
                if a is None or b is None:
                    raise Unknown("conjunct unknown")
                return True
            if op == "||":
                if b is True:
                    return True
                if a is None or b is None:
                    raise Unknown("disjunct unknown")
                return False
            if op == "==>":
                if b is True:
                    return True
                if a is None or b is None:
                    raise Unknown("implication unknown")
                return not a or b
            if a is None or b is None:
                raise Unknown("equivalence unknown")
            return (a == b) if op == "<==>" else (a != b)
        a, b = eval_term(ctx, e[2]), eval_term(ctx, e[3])
        if op in ("==", "!=", "<", "<=", ">", ">="):
            return compare(op, a, b)
        return arith(op, a, b)
    if k == "un":
        op = e[1]
        if op == "&":
            return address(ctx, e[2])
        v = eval_term(ctx, e[2])
        if op == "!":
            return not truth(v)
        if op == "-":
            return -v
        if op == "+":
            return v
        if op == "~":
            return ~v
        if op == "*":
            return read(ctx, v)
    if k == "cast":
        return convert(e[1], eval_term(ctx, e[2]))
    if k == "idx":
        base = eval_term(ctx, e[1])
        i = eval_term(ctx, e[2])
        if isinstance(i, Range):
            raise Unknown("range index in a term")
        return read(ctx, base, i)
    if k == "dot":
        s = eval_term(ctx, e[1])
        if not isinstance(s, dict) or e[2] not in s:
            raise Unknown(f"field {e[2]}")
        return s[e[2]]
    if k == "arrow":
        s = read(ctx, eval_term(ctx, e[1]))
        if not isinstance(s, dict) or e[2] not in s:
            raise Unknown(f"field {e[2]}")
        return s[e[2]]
    if k == "range":
        return ("rangeval", eval_term(ctx, e[1]), eval_term(ctx, e[2]))
    if k == "call":
        return call(ctx, e[1], e[2], e[3])
    raise Unknown(f"construct {k}")


def address(ctx, e):
    if e[0] == "idx":
        base = eval_term(ctx, e[1])
        i = eval_term(ctx, e[2])
        if isinstance(base, Ptr) and isinstance(i, int):
            return Ptr(base.b, base.i + i)
    raise Unknown("address of this location")


# Range terms such as `p + (lo .. hi)` inside \valid/\separated.
_orig_arith = arith


def arith(op, a, b):  # noqa: F811
    if isinstance(b, tuple) and b and b[0] == "rangeval" and isinstance(a, Ptr) and op == "+":
        return Range(a, b[1], b[2])
    if isinstance(a, tuple) and a and a[0] == "rangeval" and isinstance(b, Ptr) and op == "+":
        return Range(b, a[1], a[2])
    return _orig_arith(op, a, b)


def check(ctx, e):
    """True / False / None (unknown). False only for a real counterexample: some top-level conjunct
    evaluates to false with no window-approximated quantifier involved in that conjunct."""
    result = True
    for part in conjuncts(e):
        ctx.approx[0] = False
        try:
            r = eval_pred(ctx, part)
        except Unknown:
            result = None
            continue
        if not r:
            if not ctx.approx[0]:
                return False
            result = None
    return result
