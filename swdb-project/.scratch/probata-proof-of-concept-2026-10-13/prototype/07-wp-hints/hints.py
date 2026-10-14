# PROTOTYPE (Probata PoC ticket 07), throwaway. Created 2026-10-14 ET.
# Hint records {id, anchor, kind, text}: deterministic merger, erase, the proof hint check
# (map 13 items 4, 5, 7), and the verdict reader (map 13 item 7; design S7).
import re

ANCHOR_RE = re.compile(r"^\s*/\* @anchor (\S+) \*/\s*$")
BEGIN, END = "// >>> hint", "// <<< hint"

# kind -> (anchor class, required leading keyword)
KINDS = {
    "loop_invariant": ("loop", "loop invariant"),
    "loop_assigns": ("loop", "loop assigns"),
    "loop_variant": ("loop", "loop variant"),
    "assert": ("stmt", "assert"),
    "ghost": ("stmt|global", "ghost"),
    "predicate": ("global", "predicate"),
    "logic": ("global", "logic"),
    "lemma": ("global", "lemma"),
    "strategy": ("global", "\\wp::strategy"),
    # t07d method change (c): a strategy acts only through its attachment `\wp::proof S: targets;`.
    # Assumption (not decided in map 13 item 5): the attachment is part of the allowed strategy hint.
    "proof": ("global", "\\wp::proof"),
}
# t07d (c): strategies may only reshape a goal with WP's own tactics (each sound: WP proves every
# subgoal) and the three pinned provers at the run's own timeout. No \auto, no prover time argument.
STRATEGY_TACTICS = {"Wp.filter", "Wp.clear", "Wp.split", "Wp.unfold", "Wp.instance", "Wp.lemma", "Wp.range",
                    "Wp.cut", "Wp.separated", "Wp.array", "Wp.compound"}
STRATEGY_WORDS = {"\\wp::strategy", "\\tactic", "\\param", "\\children", "\\child", "\\pattern", "\\goal",
                  "\\when", "\\ingoal", "\\incontext", "\\select", "\\prover", "\\default", "\\true", "\\false"}
STRATEGY_PROVERS = {"alt-ergo", "z3", "cvc5", "Alt-Ergo", "Z3", "CVC5"}
# Map 13 item 5's rejected kinds and other escape hatches, as whole tokens.
BANNED = ["admit", "axiom", "axiomatic", "inductive", "requires", "ensures", "assumes", "behavior",
          "behaviors", "complete", "disjoint", "decreases", "terminates", "exits", "breaks",
          "continues", "returns", "allocates", "frees", "check", "import", "volatile", "global",
          "invariant_type", "type", "\\from", "for", "reads", "writes", "calls", "\\wp::why3",
          "\\wp::proof", "\\wp::nullable_args", "@", "/*", "*/", "//"]
WORD = re.compile(r"\\?[A-Za-z_][A-Za-z_0-9]*(?:::[A-Za-z_][A-Za-z_0-9]*)*|/\*|\*/|//|@")


def anchors(text):
    return {m.group(1) for ln in text.splitlines() if (m := ANCHOR_RE.match(ln))}


LOOP_ORDER = {"loop_invariant": 0, "loop_assigns": 1, "loop_variant": 2}  # t07d: Frama-C wants variants last


def _block(kind_group, hs):
    if kind_group == "loop":
        hs = sorted(hs, key=lambda h: LOOP_ORDER.get(h.get("kind"), 1))
        body = "\n    ".join(h["text"].strip() for h in hs)
        return ["/*@ " + body + " */"]
    return ["/*@ " + h["text"].strip() + " */" for h in hs]


def merge(standin, hints):
    """Insert hint blocks after their anchor lines, loop hints as one annotation per loop."""
    by_anchor = {}
    for h in hints:
        by_anchor.setdefault(h["anchor"], []).append(h)
    out = []
    for ln in standin.splitlines(keepends=True):
        out.append(ln)
        m = ANCHOR_RE.match(ln)
        if m and m.group(1) in by_anchor:
            hs = by_anchor[m.group(1)]
            indent = ln[: len(ln) - len(ln.lstrip())]
            group = "loop" if m.group(1).startswith("loop:") else "other"
            ids = " ".join(h["id"] for h in hs)
            lines = [f"{BEGIN} {ids}"] + _block(group, hs) + [END]
            out.extend(indent + x.replace("\n", "\n" + indent) + "\n" for x in lines)
    return "".join(out)


def erase(merged):
    out, skip = [], False
    for ln in merged.splitlines(keepends=True):
        s = ln.strip()
        if s.startswith(BEGIN):
            skip = True
            continue
        if skip and s == END:
            skip = False
            continue
        if not skip:
            out.append(ln)
    return "".join(out)


def blame(merged, frama_c_log, unit="tdstep_standin.c"):
    """Map Frama-C error locations in the merged unit to the hint block they fall in."""
    lines = merged.splitlines()
    out = []
    for m in re.finditer(re.escape(unit) + r":(\d+):", frama_c_log):
        n = int(m.group(1))
        ids = []
        for k in range(min(n, len(lines)) - 1, -1, -1):
            s = lines[k].strip()
            if s == END and k != n - 1 and not (k == n - 2 and lines[n - 1].strip().startswith(("for", "while", "do"))):
                break
            if s.startswith(BEGIN):
                ids = s[len(BEGIN):].split()
                break
        out.append({"line_no": n, "line": lines[n - 1] if 0 < n <= len(lines) else "", "ids": ids})
    return out


def _defined_name(kind, text):
    m = re.match(r"(?:predicate|logic\s+[^(=]*?)\s*([A-Za-z_][A-Za-z_0-9]*)\s*[({=]", text.strip())
    if kind == "predicate":
        m = re.match(r"predicate\s+([A-Za-z_][A-Za-z_0-9]*)", text.strip())
    elif kind == "logic":
        m = re.match(r"logic\s+.*?([A-Za-z_][A-Za-z_0-9]*)\s*(?:\{[^}]*\})?\s*\(", text.strip(), re.S)
    return m.group(1) if m else None


def strategy_problems(kind, text, hints):
    """t07d (c): the narrow strategy vocabulary. Returns [(rule, detail)]."""
    t = " ".join(text.split())
    out = []
    if kind == "strategy":
        m = re.fullmatch(r"\\wp::strategy\s+([A-Za-z_]\w*)\s*:\s*(.+?)\s*;", t)
        if not m:
            return [("strategy_form", "expected `\\wp::strategy Name: alternatives;`")]
        body = m.group(2)
        for w in set(re.findall(r"\\[A-Za-z_]\w*", body)):
            if w not in STRATEGY_WORDS:
                out.append(("strategy_word", w))
        for tac in re.findall(r"\\tactic\s*\(\s*\"([^\"]*)\"", body):
            if tac not in STRATEGY_TACTICS:
                out.append(("strategy_tactic", tac))
        for pv in re.findall(r"\\prover\s*\(([^)]*)\)", body):
            args = [a.strip() for a in pv.split(",") if a.strip()]
            if any(not re.fullmatch(r"\"[^\"]*\"", a) for a in args):
                out.append(("strategy_prover_timeout", pv))  # no time argument: the run's timeout holds
            if any(a.strip('"') not in STRATEGY_PROVERS for a in args):
                out.append(("strategy_prover", pv))
    else:
        m = re.fullmatch(r"\\wp::proof\s+([A-Za-z_]\w*)\s*:\s*(.+?)\s*;", t)
        if not m:
            return [("proof_form", "expected `\\wp::proof StrategyName: target, ...;`")]
        defined = {mm.group(1) for h in hints if h.get("kind") == "strategy"
                   for mm in [re.match(r"\s*\\wp::strategy\s+([A-Za-z_]\w*)", str(h.get("text", "")))] if mm}
        if m.group(1) not in defined:
            out.append(("proof_unknown_strategy", m.group(1)))
        targets = re.findall(r"\"([^\"]*)\"|([A-Za-z_]\w*)", m.group(2))
        names = [x for a, b in targets for x in ((a.split(",") if a else [b]))]
        if any(n.strip().lstrip("+-") == "smoke" for n in names):
            out.append(("proof_smoke", "strategies may not target smoke tests"))
    return out


def check(standin, hints):
    """Return one {id, rule, detail} per violation; an empty list accepts the hint set."""
    known = anchors(standin)
    bad = []

    def rej(h, rule, detail=""):
        bad.append({"id": h.get("id"), "rule": rule, "detail": detail})

    for h in hints:
        kind, anchor, text = h.get("kind"), h.get("anchor"), str(h.get("text", ""))
        if anchor not in known:
            rej(h, "unknown_anchor", anchor)
            continue
        if kind not in KINDS:
            rej(h, "kind_not_allowed", kind)
            continue
        where, lead = KINDS[kind]
        cls = "global" if anchor == "global" else anchor.split(":")[0]
        if cls not in where.split("|"):
            rej(h, "anchor_kind_mismatch", f"{kind} at {anchor}")
        if not text.strip().startswith(lead):
            rej(h, "kind_text_mismatch", f"{kind} must start with '{lead}'")
        tokens = WORD.findall(re.sub(r'"[^"]*"', '""', text) if kind in ("strategy", "proof") else text)
        hits = sorted({t for t in tokens if t in BANNED and not (kind == "loop_invariant" and t == "invariant")
                       and not (kind == "proof" and t == "\\wp::proof")})
        if hits:
            rej(h, "banned_token", ",".join(hits))
        if kind in ("strategy", "proof"):
            for rule, detail in strategy_problems(kind, text, hints):
                rej(h, rule, detail)
        if kind in ("predicate", "logic"):
            name = _defined_name(kind, text)
            body = text.split("=", 1)[1] if "=" in text else text
            if name and re.search(r"\b" + re.escape(name) + r"\b", body):
                rej(h, "recursive_definition", name)
        if kind == "ghost" and re.match(r"ghost\s+[^;=]*\b[A-Za-z_]\w*\s*\([^;]*\)\s*\{", text.strip(), re.S):
            rej(h, "ghost_function", text[:60])
    return bad


STATUS_RE = re.compile(r"^\[\s*(Valid|Partial|Extern|Alarm|-|Invalid|Unknown|Dead|Never tried|Inconsistent)\s*\]\s+(.*)$")


FUNC_RE = re.compile(r"^--- Properties of Function '([^']+)'")
PROTO_RE = re.compile(r"^[A-Za-z_][\w \t\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*;", re.M)


def bodyless_functions(header):
    """Names of functions declared without a body (summaries)."""
    return set(PROTO_RE.findall(header))


def read_report(report):
    """Parse Frama-C -report text into [{status, property, detail, function}] per property."""
    props, cur, func = [], None, None
    for ln in report.splitlines():
        fm = FUNC_RE.match(ln)
        if fm:
            func, cur = fm.group(1), None
            continue
        if ln.startswith("--- "):
            func, cur = None, None
            continue
        m = STATUS_RE.match(ln)
        if m:
            cur = {"status": m.group(1), "property": m.group(2).strip(), "detail": "", "function": func}
            props.append(cur)
        elif cur is not None and ln.startswith("            "):
            cur["detail"] += ln.strip() + "\n"
        elif ln.startswith("---") or not ln.strip():
            cur = None
    return props


def verdict_problems(props, extern_ok_files, extern_ok_functions=frozenset()):
    """Every property must be Valid; Extern only in summary contracts (S7)."""
    bad = []
    for p in props:
        if p["status"] == "Valid":
            continue
        # t07d bug fix: WP's `\wp::strategy` / `\wp::proof` annotations are listed by -report as
        # properties with status "-", but they are proof directives, not obligations.
        if p["status"] == "-" and re.match(r'(strategy|proof) \("', p["property"]):
            continue
        if p["status"] == "Extern":
            if p.get("function") in extern_ok_functions:
                continue
            m = re.search(r'file ([^,)\s"]+)|"([^"]+)", line', p["property"])
            f = (m.group(1) or m.group(2)) if m else None
            if f and f.split("/")[-1] in extern_ok_files:
                continue
        bad.append(p)
    return bad


def smoke_failures(goals):
    """A smoke goal WP proves Valid signals dead code (S7)."""
    return [g for g in goals if g.get("smoke") and not g.get("passed")]


# ---- t07c method change (c): failing goals with their source positions --------------------------

def hint_block_at(merged_lines, n):
    """Hint ids of the `// >>> hint` block that holds 1-based line n, or of the loop block right
    above the loop head at line n; [] when line n is stand-in code."""
    k = n - 1
    if not (0 <= k < len(merged_lines)):
        return []
    for j in range(k, -1, -1):
        s = merged_lines[j].strip()
        if s == END and j != k:
            if j == k - 1 and merged_lines[k].strip().startswith(("for", "while", "do")):
                continue  # the loop block right above a loop head belongs to that loop's goals
            return []
        if s.startswith(BEGIN):
            return s[len(BEGIN):].split()
    return []


_KINDS = ("loop_invariant", "loop_assigns", "loop_variant", "assigns", "assert", "ensures", "call",
          "terminates", "check", "exits", "lemma")


def goal_kind(goal):
    """A short kind label from WP's goal name (typed_<function>_<kind>...)."""
    for k in _KINDS:
        m = re.search(r"_" + k + r"(?:_|$)", goal)
        if m:
            if k == "loop_invariant":
                tail = "established" if goal.endswith("established") else "preserved" if goal.endswith("preserved") else ""
                return ("loop invariant " + tail).strip()
            if k == "call":
                return "call-site precondition"
            return k.replace("_", " ")
    return goal


def goal_positions(goals, merged, unit="tdstep_standin.c", headers=None):
    """Each non-smoke goal not passed, with kind, file:line, the source line and the hint holding it."""
    lines = merged.splitlines()
    headers = headers or {}
    out = []
    for g in goals:
        if g.get("smoke") or g.get("passed"):
            continue
        f = (g.get("file") or "").split("/")[-1]
        n = int(g.get("line") or 0)
        if f == unit:
            src = lines[n - 1].strip() if 0 < n <= len(lines) else ""
            ids = hint_block_at(lines, n)
        else:
            hl = headers.get(f, "").splitlines()
            src = hl[n - 1].strip() if 0 < n <= len(hl) else ""
            ids = []
        out.append({"goal": g.get("goal"), "kind": goal_kind(g.get("goal", "")), "file": f, "line": n,
                    "source": src[:300], "hint_ids": ids, "failure_class": g.get("verdict"),
                    "function": g.get("function")})
    return out
