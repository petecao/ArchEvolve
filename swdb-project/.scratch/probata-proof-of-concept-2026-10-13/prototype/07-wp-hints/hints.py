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
}
# Map 13 item 5's rejected kinds and other escape hatches, as whole tokens.
BANNED = ["admit", "axiom", "axiomatic", "inductive", "requires", "ensures", "assumes", "behavior",
          "behaviors", "complete", "disjoint", "decreases", "terminates", "exits", "breaks",
          "continues", "returns", "allocates", "frees", "check", "import", "volatile", "global",
          "invariant_type", "type", "\\from", "for", "reads", "writes", "calls", "\\wp::why3",
          "\\wp::proof", "\\wp::nullable_args", "@", "/*", "*/", "//"]
WORD = re.compile(r"\\?[A-Za-z_][A-Za-z_0-9]*(?:::[A-Za-z_][A-Za-z_0-9]*)*|/\*|\*/|//|@")


def anchors(text):
    return {m.group(1) for ln in text.splitlines() if (m := ANCHOR_RE.match(ln))}


def _block(kind_group, hs):
    if kind_group == "loop":
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
        tokens = WORD.findall(text)
        hits = sorted({t for t in tokens if t in BANNED and not (kind == "loop_invariant" and t == "invariant")})
        if hits:
            rej(h, "banned_token", ",".join(hits))
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
