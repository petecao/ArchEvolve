#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, continuation 2 "t07d"), throwaway. Created 2026-10-14 ET.
# Method change (b): deterministic frame seeds. A syntactic write-set pass over the C stand-in
# (clang's JSON AST) plus the callees' ACSL `assigns` clauses generates one `loop assigns` per loop,
# before any provider call. Nothing here is BFS-specific; the rules are:
#   1. A loop's writes are: assignments and ++/-- in its condition, step and body (nested loops
#      included), plus every callee's `assigns` clause with formals replaced by the actual arguments.
#      `*f(args)` with a pure callee (`assigns \nothing; ensures \result == E;`) becomes `*(E)`.
#   2. Locals declared inside the loop body are dropped (block scoped); the loop's own counters and
#      outer locals stay.
#   3. Alias facts: a call outside every loop whose callee ensures `self->f == p` (both plain paths)
#      lets `x.f` be written as the actual of p, when no loop writes x.f.
#   4. A location whose index reads something the loop writes is widened to the enclosing function's
#      own `assigns` location with the same base, with the function frame's indices taken at Pre
#      (`\at(e, Pre)` for each frame scalar used inside an index).
#   5. Every seed is checked by WP like any hint (its frame goals); seeds are method, not hints.
# Usage: frame_seeds.py <standin.c> [function]  -> JSON list of seed records on stdout.
import hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANCHOR_RE = re.compile(r"^\s*/\* @anchor (loop:\S+) \*/\s*$")
CONTRACT_RE = re.compile(r"/\*@((?:(?!\*/).)*)\*/\s*([^;{/@]*?\b([A-Za-z_]\w*)\s*\(([^)]*)\))\s*[;{]", re.S)


def split_top(s, sep=","):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def contracts(texts):
    """name -> {formals, assigns: [terms] | None, result: E | None}."""
    out = {}
    for text in texts:
        for m in CONTRACT_RE.finditer(text):
            body, name, params = m.group(1), m.group(3), m.group(4)
            if "predicate" in body or "lemma" in body or "logic " in body:
                continue
            formals = []
            for p in split_top(params):
                pm = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*$", p)
                if pm and p.strip() != "void":
                    formals.append(pm.group(1))
            body1 = re.sub(r"behavior\s+\w+\s*:.*", "", body, flags=re.S)  # function-level clauses only
            assigns = []
            for am in re.finditer(r"\bassigns\b(.*?);", body1, re.S):
                assigns += [t for t in split_top(" ".join(am.group(1).split())) if t != "\\nothing"]
            # behaviors may repeat assigns; the function-level clause is the union we need
            res = re.search(r"ensures\s+\\result\s*==\s*([^;]*);", body1)
            pure = re.search(r"\bassigns\s+\\nothing\s*;", body1) is not None
            out[name] = {"formals": formals, "assigns": assigns,
                         "result": " ".join(res.group(1).split()) if (res and pure) else None,
                         "ensures": [" ".join(e.split()) for e in re.findall(r"ensures\s+([^;]*);", body1)]}
    return out


def subst(term, formals, actuals):
    for f, a in zip(formals, actuals):
        term = re.sub(r"(?<![\w.>])" + re.escape(f) + r"\b", "(" + a + ")", term)
    return simplify(term)


def simplify(t):
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r"\(&\s*([A-Za-z_][\w.]*(?:->\w+)*)\)->", r"\1.", t)          # (&x)->f  -> x.f
        t = re.sub(r"\(\s*([A-Za-z_][\w.]*(?:->\w+)*)\s*\)(?=\s*(->|\.|\[|[,)\s+\-]|$))", r"\1", t)  # (x) -> x
        t = re.sub(r"\(\((.*)\)\)$", r"(\1)", t)                                     # ((e)) -> (e)
        t = re.sub(r"\(\s*(-?\d+)\s*\)", r"\1", t)                                    # (16384) -> 16384
        t = re.sub(r"\[\s*\(([^\[\]()]*(?:\[[^\]]*\])?)\)\s*\]", r"[\1]", t)         # [(e)] -> [e]
        m = re.fullmatch(r"\*\s*\(+\s*([A-Za-z_][\w.]*(?:->\w+)*)\s*\+\s*(.+?)\s*\)+", t)  # *(a + i) -> a[i]
        if m and m.group(2).count("(") == m.group(2).count(")"):
            t = m.group(1) + "[" + m.group(2) + "]"
    return " ".join(t.split())


CALL_RE = re.compile(r"([A-Za-z_]\w*)\s*\(")


def resolve_pure(term, C):
    """Replace pure calls f(args) (ensures \\result == E) by E with actuals."""
    changed = True
    while changed:
        changed = False
        for m in CALL_RE.finditer(term):
            name = m.group(1)
            if name not in C or C[name]["result"] is None:
                continue
            depth, j = 0, m.end() - 1
            for j in range(m.end() - 1, len(term)):
                if term[j] == "(":
                    depth += 1
                elif term[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
            args = split_top(term[m.end():j])
            rep = "(" + subst(C[name]["result"], C[name]["formals"], args) + ")"
            term = term[:m.start()] + rep + term[j + 1:]
            changed = True
            break
    return simplify(term)


def ast_function(path, fn):
    out = subprocess.run(["clang", "-target", "x86_64-linux-gnu", "-fsyntax-only", "-Xclang", "-ast-dump=json",
                          "-Xclang", f"-ast-dump-filter={fn}", str(path), "-o", "/dev/null"],
                         capture_output=True, text=True, check=True).stdout
    dec, i = json.JSONDecoder(), 0
    while i < len(out):
        j = out.find("{", i)
        if j < 0:
            break
        obj, i = dec.raw_decode(out, j)
        if obj.get("kind") == "FunctionDecl" and obj.get("name") == fn and \
                any(c.get("kind") == "CompoundStmt" for c in obj.get("inner", [])):
            return obj
    raise SystemExit(f"no body for {fn}")


def src(text, node):
    r = node["range"]
    b, e = r["begin"], r["end"]
    if "offset" not in b or "offset" not in e:
        b, e = b.get("spellingLoc", b), e.get("spellingLoc", e)
    return text[b["offset"]: e["offset"] + e.get("tokLen", 0)]


def walk(n):
    yield n
    for c in n.get("inner", []) or []:
        yield from walk(c)


def callee_name(call):
    for n in walk(call["inner"][0]):
        if n.get("kind") == "DeclRefExpr":
            return n["referencedDecl"]["name"]
    return None


def writes_of(nodes, text, C):
    """Raw write terms (normalized) and locals declared in these nodes."""
    terms, declared = [], set()
    for root in nodes:
        for n in walk(root):
            k = n.get("kind")
            if k == "VarDecl":
                declared.add(n["name"])
            elif k in ("BinaryOperator", "CompoundAssignOperator") and \
                    (n.get("opcode") == "=" or k == "CompoundAssignOperator"):
                terms.append(resolve_pure(src(text, n["inner"][0]), C))
            elif k == "UnaryOperator" and n.get("opcode") in ("++", "--"):
                terms.append(resolve_pure(src(text, n["inner"][0]), C))
            elif k == "CallExpr":
                name = callee_name(n)
                if name in C:
                    args = [src(text, a) for a in n["inner"][1:]]
                    for t in C[name]["assigns"]:
                        terms.append(resolve_pure(subst(t, C[name]["formals"], args), C))
    return terms, declared


def ident_set(t):
    return set(re.findall(r"(?<![\w\\])[A-Za-z_]\w*(?:(?:\.|->)\w+)*", t))


def base_of(t):
    depth = 0
    for i in range(len(t) - 1, -1, -1):
        ch = t[i]
        if ch == "]":
            depth += 1
        elif ch == "[":
            depth -= 1
            if depth == 0:
                return t[:i].strip(), t[i:]
    return t, ""


def seeds(standin_path, fn="TDStep"):
    standin_path = Path(standin_path)
    text = standin_path.read_text()
    hdr_texts = [p.read_text() for p in sorted(standin_path.parent.glob("*.h"))]
    C = contracts(hdr_texts + [text])
    func = ast_function(standin_path, fn)
    frame = C[fn]["assigns"]
    scal = [t for t in frame if "[" not in t]
    frame_pre = []
    for t in frame:  # rule 4: the function frame's indices are evaluated at Pre
        b, idx = base_of(t)
        for s in scal:
            idx = re.sub(r"(?<![\w.>])" + re.escape(s) + r"(?![\w])", r"\\at(" + s + ", Pre)", idx)
        frame_pre.append(b + idx)
    body = [c for c in func["inner"] if c.get("kind") == "CompoundStmt"][0]
    lines = text.splitlines()
    line_of = lambda off: text.count("\n", 0, off) + 1  # noqa: E731
    loops = [n for n in walk(body) if n.get("kind") in ("ForStmt", "WhileStmt", "DoStmt")]
    in_loop = set()
    for lp in loops:
        for n in walk(lp):
            in_loop.add(id(n))
    # rule 3: alias facts from calls outside every loop
    alias = {}
    for n in walk(body):
        if n.get("kind") == "CallExpr" and id(n) not in in_loop:
            name = callee_name(n)
            if name not in C:
                continue
            args = [src(text, a) for a in n["inner"][1:]]
            for e in C[name]["ensures"]:
                for conj in split_top(e.replace("&&", ","), ","):
                    m = re.fullmatch(r"\s*([A-Za-z_]\w*(?:->\w+)+)\s*==\s*([A-Za-z_]\w*)\s*", conj)
                    if m and m.group(2) in C[name]["formals"]:
                        lhs = subst(m.group(1), C[name]["formals"], args)
                        rhs = subst(m.group(2), C[name]["formals"], args)
                        alias[lhs] = rhs
    out = []
    for lp in loops:
        off = lp["range"]["begin"]["offset"]
        ln = line_of(off)
        am = ANCHOR_RE.match(lines[ln - 2]) if ln >= 2 else None
        if not am:
            raise SystemExit(f"loop at line {ln} has no anchor right above it")
        inner = lp.get("inner", [])
        if lp["kind"] == "ForStmt":  # [init, condVar, cond, inc, body]; init runs before the loop
            init, rest = inner[0] if inner else None, [x for x in inner[1:] if x]
        else:
            init, rest = None, [x for x in inner if x]
        init_decl = set()
        if init:
            init_decl = {n["name"] for n in walk(init) if n.get("kind") == "VarDecl"}
        terms, declared = writes_of(rest, text, C)
        declared -= init_decl
        for a in list(alias):  # rule 3 applies only when no loop writes the aliased path
            if any(t == a or t.startswith(a + "[") for t in terms):
                alias.pop(a)
        norm = []
        for t in terms:
            for a, b in alias.items():
                t = re.sub(r"(?<![\w.>])" + re.escape(a) + r"(?![\w])", b, t)
            norm.append(simplify(t))
        written = {t for t in norm if "[" not in t}
        res = []
        for t in norm:
            root = re.match(r"[A-Za-z_]\w*", t)
            if root and root.group(0) in declared and re.fullmatch(r"[A-Za-z_]\w*(?:\.\w+)*", t):
                continue  # a block-scoped local of the loop body (rule 2)
            b, idx = base_of(t)
            varying = idx and any((i in declared or i in written or i.split(".")[0] in declared)
                                  for i in ident_set(idx))
            if varying:
                match = [f for f in frame_pre if base_of(f)[0] == b]
                if not match:
                    raise SystemExit(f"cannot widen {t!r} in {am.group(1)}: no frame location with base {b!r}")
                t = match[0]
            if t not in res:
                res.append(t)
        out.append({"anchor": am.group(1), "kind": "loop_assigns", "text": "loop assigns " + ", ".join(res) + ";"})
    tag = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    for i, s in enumerate(out, 1):
        s["id"] = f"seed{i}"
        s["provenance"] = f"seed: frame_seeds.py {tag} (mechanical, rule 1-4)"
    return out


if __name__ == "__main__":
    print(json.dumps(seeds(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "TDStep"), indent=1))
