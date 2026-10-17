"""2026-10-16 ET. Exact retained source9 syntax helpers only; no semantics."""
import hashlib
import json
import re


def need(value, label):
    if not value:
        raise ValueError(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def forms(text):
    """Complete bounded SMT-LIB tokenization, preserving strings/quoted symbols."""
    need(len(text.encode()) <= 1024 * 1024, "SMT input byte cap")
    lexer = re.compile(r'\s+|;[^\n]*(?:\n|$)|"(?:[^"\\]|\\.|"")*"|\|[^|\\]*\||[()]|[^\s();"|]+')
    stack = [[]]
    end = tokens = 0
    for match in lexer.finditer(text):
        need(match.start() == end, "complete SMT token coverage")
        end = match.end()
        token = match[0]
        if token.isspace() or token.startswith(";"):
            continue
        tokens += 1
        need(tokens <= 100000, "SMT token cap")
        if token == "(":
            item = []
            stack[-1].append(item)
            stack.append(item)
            need(len(stack) <= 160, "SMT depth cap")
        elif token == ")":
            need(len(stack) > 1, "SMT balanced close")
            stack.pop()
        else:
            stack[-1].append(token)
    need(end == len(text) and len(stack) == 1, "complete balanced SMT")
    return stack[0]
