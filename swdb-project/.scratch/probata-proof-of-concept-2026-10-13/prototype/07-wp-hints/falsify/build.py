#!/usr/bin/env python3
# PROTOTYPE (Probata PoC ticket 07, method24), throwaway. Created 2026-10-16 ET.
# Builds the bounded hint falsifier's executable: an instrumented copy of the hint-free stand-in that
# records the concrete state at every anchor (stmt anchors where they stand, loop anchors at each
# evaluation of the loop condition), linked with the executable DX100/library models in harness.c.
# The stand-in's own C statements are unchanged; only anchor comments become recorder calls and the
# symbolic build constants become runtime inputs. Hints are never compiled in: falsify.py evaluates them.
import re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANCHOR = re.compile(r"^(\s*)/\* @anchor (\S+) \*/\s*$")
DECL = re.compile(r"^\s*(?:const\s+)?(struct\s+\w+|size_t|unsigned|int|bool|NodeID|dxc_context)\s*(\*?)\s*(\w+)\s*(=|;)")
FOR_DECL = re.compile(r"\bfor\s*\(\s*(?:size_t|unsigned|int)\s+(\w+)\s*=")
PARAMS_DUMPED = ["num_nodes", "num_edges"]


def strip_comments(line):
    line = re.sub(r"/\*.*?\*/", "", line)
    return line.split("//", 1)[0]


def instrument(standin):
    lines = standin.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines) if ln.startswith("void TDStep("))
    out = lines[:start] + ['#include "harness.c"\n']
    depth, scope, pending_loop = 0, [], None   # scope: (name, depth)
    in_body = False
    i = start
    while i < len(lines):
        ln = lines[i]
        m = ANCHOR.match(ln)
        if m and in_body:
            name = m.group(2)
            names = PARAMS_DUMPED + [n for n, _ in scope]
            if name.startswith("loop:"):
                pending_loop = (name, names)
                out.append(ln)
            else:
                out.append(f'{m.group(1)}SWDB_EV("{name}", {" ".join(f"L({n})" for n in names)});\n')
            i += 1
            continue
        if pending_loop and re.search(r"\bfor\s*\(", ln):
            # Collect the whole for header up to its matching ')'.
            text, j = ln, i
            while True:
                k = text.find("for")
                p0 = text.index("(", k)
                lvl, end = 0, None
                for q in range(p0, len(text)):
                    if text[q] == "(":
                        lvl += 1
                    elif text[q] == ")":
                        lvl -= 1
                        if lvl == 0:
                            end = q
                            break
                if end is not None:
                    break
                j += 1
                text += lines[j]
            inner = text[p0 + 1:end]
            parts, lvl, cur = [], 0, ""
            for ch in inner:
                if ch in "([":
                    lvl += 1
                elif ch in ")]":
                    lvl -= 1
                if ch == ";" and lvl == 0:
                    parts.append(cur)
                    cur = ""
                else:
                    cur += ch
            parts.append(cur)
            assert len(parts) == 3, inner
            fd = FOR_DECL.search(text)
            names = pending_loop[1] + ([fd.group(1)] if fd else [])
            rec = f'SWDB_LOOPEV("{pending_loop[0]}", {" ".join(f"L({n})" for n in names)})'
            cond = parts[1].strip() or "1"
            new = text[:p0 + 1] + parts[0] + "; (" + rec + ", (" + cond + "));" + parts[2] + text[end:]
            out.append(new)
            for q in range(i, j + 1):
                code = strip_comments(lines[q])
                d0 = depth
                depth += code.count("{") - code.count("}")
            if fd:
                scope.append((fd.group(1), d0 + 1))
            scope = [(n, d) for n, d in scope if d <= depth]
            pending_loop = None
            i = j + 1
            continue
        code = strip_comments(ln)
        if in_body:
            dm = DECL.match(code)
            if dm:
                scope.append((dm.group(3), depth))
        for ch in code:
            if ch == "{":
                depth += 1
                in_body = True
            elif ch == "}":
                depth -= 1
                scope = [(n, d) for n, d in scope if d <= depth]
        out.append(ln)
        i += 1
    return "".join(out)


def build(standin_dir, out_dir):
    standin_dir, out_dir = Path(standin_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    s = (standin_dir / "dxc_summaries.h").read_text()
    s = s.replace("//@ ghost ", "").replace("extern const unsigned TILE_SIZE;", "extern unsigned TILE_SIZE;")
    (out_dir / "dxc_summaries.h").write_text(s)
    for h in ("gapbs_models.h", "bfs_unit.h"):
        (out_dir / h).write_text((standin_dir / h).read_text())
    c = (standin_dir / "tdstep_standin.c").read_text()
    c = c.replace("extern const int SWDB_FRONTIER_THRESHOLD;", "extern int SWDB_FRONTIER_THRESHOLD;")
    c = c.replace("extern const unsigned SWDB_CHUNK_SIZE;", "extern unsigned SWDB_CHUNK_SIZE;")
    c = instrument(c)
    (out_dir / "fz_unit.c").write_text(c)
    (out_dir / "harness.c").write_text((HERE / "harness.c").read_text())
    exe = out_dir / "fz_unit"
    r = subprocess.run(["clang", "-std=gnu11", "-O1", "-g", "-w", "-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all", "-o", str(exe), str(out_dir / "fz_unit.c")],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("falsifier build failed:\n" + r.stderr[-4000:])
    return exe


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2]))
