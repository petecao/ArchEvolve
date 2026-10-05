"""C++ lexical helpers: comments and literals blanked, function spans by balanced braces.

Created 2026-10-05 ET (code review F12): the one copy of the C++ lexical pattern that the campaign
adapters (session-begin check, protected regions, workspace region lines), the profiling agent and
the rewrite workflow share. `swdb/bfs_native.py` keeps its own literal copy on purpose: its file
hash is the BFS v1 verifier identity.

The helpers are lexical, not a parser: a string, character literal or comment never opens or closes
a brace, and offsets and line numbers are kept so callers can report source lines.
"""
import re

#: A string literal, a character literal, a line comment or a block comment.
LEXICAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')


def code_only(text):
    """`text` with comments and literals blanked (line breaks kept, so offsets and lines stay)."""
    text = re.sub(r"\\\r?\n", "  ", text)
    return LEXICAL.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def body_spans(code, function):
    """Character spans of the bodies of every definition of `function` in lexically blanked `code`."""
    spans = []
    for match in re.finditer(r"\b" + re.escape(function) + r"\s*\(", code):
        depth, i = 0, match.end() - 1
        while i < len(code):                 # the parameter list
            depth += {"(": 1, ")": -1}.get(code[i], 0)
            i += 1
            if depth == 0:
                break
        head = re.match(r"\s*(?:const\s*)?(?:noexcept\s*)?\{", code[i:])
        if not head:
            continue                          # a call or a declaration, not a definition
        start = i + head.end() - 1
        depth, j = 0, start
        while j < len(code):
            depth += {"{": 1, "}": -1}.get(code[j], 0)
            if depth == 0:
                break
            j += 1
        spans.append((start, j))
    return spans


def function_span(text, name):
    """1-based (first, last) lines of the top-level definition of function `name`, or None.

    A definition starts at column 0 (enough for the GAPBS sources) and its body is the first balanced
    brace block after it, counted on the lexically blanked text, so braces inside comments and
    string or character literals are ignored (code review F12, 2026-10-05 ET; before, they counted)."""
    lines = code_only(text).splitlines()
    pattern = re.compile(r"^[A-Za-z_][\w:<>,\s\*&]*\b" + re.escape(name) + r"\s*\(")
    for start, line in enumerate(lines):
        if not pattern.match(line):
            continue
        depth, opened = 0, False
        for end in range(start, len(lines)):
            depth += lines[end].count("{") - lines[end].count("}")
            opened = opened or "{" in lines[end]
            if opened and depth <= 0:
                return start + 1, end + 1
            if not opened and lines[end].rstrip().endswith(";"):
                break                       # a declaration, not a definition
    return None


def enclosing_function(text, line):
    """Name of the top-level function whose definition spans 1-based `line`, or None."""
    for match in re.finditer(r"^[A-Za-z_][\w:<>,\s\*&]*?\b([A-Za-z_]\w*)\s*\(", code_only(text), re.M):
        span = function_span(text, match.group(1))
        if span and span[0] <= line <= span[1]:
            return match.group(1)
    return None
