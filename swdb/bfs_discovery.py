"""Compiler-derived BFS function/loop inventory, without a symbol catalog.

Updated: 2026-09-25. This is a metadata-only parse; execution retains OpenMP.
"""
import ctypes as C
import hashlib
import json
import re
import sys
from pathlib import Path


class String(C.Structure):
    _fields_ = [("data", C.c_void_p), ("flags", C.c_uint)]


class Cursor(C.Structure):
    _fields_ = [("kind", C.c_uint), ("xdata", C.c_int), ("data", C.c_void_p * 3)]


class Location(C.Structure):
    _fields_ = [("data", C.c_void_p * 2), ("value", C.c_uint)]


class Range(C.Structure):
    _fields_ = [("data", C.c_void_p * 2), ("begin", C.c_uint), ("end", C.c_uint)]


def discover(source, arguments, library):
    """Return only compiler-resolved editable extents, fail on any parse error."""
    source = Path(source).resolve()
    raw = source.read_bytes()
    lib = C.CDLL(str(library))
    visitor = C.CFUNCTYPE(C.c_uint, Cursor, Cursor, C.c_void_p)
    signatures = {
        "clang_createIndex": ([C.c_int, C.c_int], C.c_void_p),
        "clang_disposeIndex": ([C.c_void_p], None),
        "clang_parseTranslationUnit2": ([C.c_void_p, C.c_char_p, C.POINTER(C.c_char_p), C.c_int,
                                         C.c_void_p, C.c_uint, C.c_uint, C.POINTER(C.c_void_p)], C.c_int),
        "clang_disposeTranslationUnit": ([C.c_void_p], None),
        "clang_getTranslationUnitCursor": ([C.c_void_p], Cursor),
        "clang_visitChildren": ([Cursor, visitor, C.c_void_p], C.c_uint),
        "clang_getCursorSpelling": ([Cursor], String),
        "clang_getCursorUSR": ([Cursor], String),
        "clang_getCursorReferenced": ([Cursor], Cursor),
        "clang_getCursorExtent": ([Cursor], Range),
        "clang_getRangeStart": ([Range], Location),
        "clang_getRangeEnd": ([Range], Location),
        "clang_getSpellingLocation": ([Location, C.POINTER(C.c_void_p), C.POINTER(C.c_uint),
                                       C.POINTER(C.c_uint), C.POINTER(C.c_uint)], None),
        "clang_getFileName": ([C.c_void_p], String),
        "clang_getCString": ([String], C.c_char_p),
        "clang_disposeString": ([String], None),
        "clang_getClangVersion": ([], String),
        "clang_getNumDiagnostics": ([C.c_void_p], C.c_uint),
        "clang_getDiagnostic": ([C.c_void_p, C.c_uint], C.c_void_p),
        "clang_getDiagnosticSeverity": ([C.c_void_p], C.c_uint),
        "clang_formatDiagnostic": ([C.c_void_p, C.c_uint], String),
        "clang_disposeDiagnostic": ([C.c_void_p], None),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(lib, name); fn.argtypes = args; fn.restype = result

    def string(value):
        result = lib.clang_getCString(value)
        text = result.decode(errors="replace") if result else ""
        lib.clang_disposeString(value)
        return text

    def location(value):
        file, line, col, offset = C.c_void_p(), C.c_uint(), C.c_uint(), C.c_uint()
        lib.clang_getSpellingLocation(value, C.byref(file), C.byref(line), C.byref(col), C.byref(offset))
        return (string(lib.clang_getFileName(file)) if file.value else "", line.value, offset.value)

    def extent(cursor):
        r = lib.clang_getCursorExtent(cursor)
        return location(lib.clang_getRangeStart(r)), location(lib.clang_getRangeEnd(r))

    def children(cursor):
        found = []
        @visitor
        def visit(child, parent, data):
            found.append(child); return 1
        lib.clang_visitChildren(cursor, visit, None)
        return found

    index = lib.clang_createIndex(0, 0)
    tu = C.c_void_p()
    args = (C.c_char_p * len(arguments))(*(a.encode() for a in arguments))
    result = lib.clang_parseTranslationUnit2(index, str(source).encode(), args, len(arguments), None, 0, 0, C.byref(tu))
    try:
        if result or not tu.value:
            raise ValueError(f"libclang parse failed with code {result}")
        diagnostics = []
        for i in range(lib.clang_getNumDiagnostics(tu)):
            diagnostic = lib.clang_getDiagnostic(tu, i)
            diagnostics.append({"severity": lib.clang_getDiagnosticSeverity(diagnostic),
                                "message": string(lib.clang_formatDiagnostic(diagnostic, 3))})
            lib.clang_disposeDiagnostic(diagnostic)
        if any(d["severity"] >= 3 for d in diagnostics):
            raise ValueError("compiler discovery diagnostics: " + "; ".join(d["message"] for d in diagnostics))
        regions, unresolved, seen = [], [], set()
        loops = {207: "while", 208: "do", 209: "for", 225: "range_for"}

        def walk(cursor, function=None):
            start, end = extent(cursor)
            local = start[0] == str(source) and end[0] == str(source)
            # System/header bodies are intentionally outside this TU-source scope.
            if start[0] and not local:
                return
            name = string(lib.clang_getCursorSpelling(cursor))
            sub = children(cursor)
            if local and cursor.kind == 8:
                body = next((c for c in sub if c.kind == 202), None)
                if body:
                    body_start, body_end = extent(body)
                    fragment = raw[start[2]:end[2]]
                    function = name
                    if re.search(rb"\bconstexpr\b", raw[start[2]:body_start[2]]):
                        unresolved.append({"kind": "function", "name": name, "reason": "constexpr body cannot contain diagnostic scope guards"})
                        return
                    add("function", name, start, end, body_start[2] + 1, end[2], function,
                        string(lib.clang_getCursorUSR(cursor)))
            if local and cursor.kind in loops and function:
                # Statement extents omit the terminating semicolon for expression
                # bodies and do-while. Include it before wrapping the whole loop.
                finish = end[2]
                while finish < len(raw) and raw[finish:finish+1] in b" \t\r\n": finish += 1
                if raw[finish:finish+1] == b";": finish += 1
                else: finish = end[2]
                begin = start[2]
                # OpenMP pragma must remain immediately adjacent to its loop.
                line_start = raw.rfind(b"\n", 0, begin) + 1
                preceding_end = line_start
                preceding_start = raw.rfind(b"\n", 0, max(0, preceding_end-1)) + 1
                previous = raw[preceding_start:preceding_end]
                if re.match(rb"\s*#\s*pragma\s+omp\b", previous):
                    if b"\\" in previous or re.search(rb"\b(?:simd|tile|unroll|collapse)\b", previous):
                        unresolved.append({"kind": "loop", "name": loops[cursor.kind], "line": start[1],
                                           "reason": "transformation-specific or continued OpenMP pragma cannot be safely wrapped"})
                        return
                    else:
                        body_start, body_end = extent(sub[-1])
                        body_finish = body_end[2]
                        while body_finish < len(raw) and raw[body_finish:body_finish+1] in b" \t\r\n": body_finish += 1
                        if raw[body_finish:body_finish+1] == b";": body_finish += 1
                        else: body_finish = body_end[2]
                        add("loop", loops[cursor.kind], start, (end[0], end[1], finish), body_start[2], body_finish, function, None)
                        regions[-1]["invocation_unit"] = "OpenMP loop iteration on the executing worker thread"
                elif raw[start[2]:start[2]+8].lstrip().startswith((b"for", b"while", b"do")):
                    add("loop", loops[cursor.kind], start, (end[0], end[1], finish), begin, finish, function, None)
                else:
                    unresolved.append({"kind": "loop", "line": start[1], "reason": "macro expansion has no editable loop statement"})
            if local and cursor.kind in (43, 45) and function:
                referenced = lib.clang_getCursorReferenced(cursor)
                type_name = string(lib.clang_getCursorSpelling(referenced)) or name
                for region in regions:
                    if region["kind"] == "function" and region["function"] == function and type_name:
                        if type_name not in region["referenced_types"]: region["referenced_types"].append(type_name)
            if local and cursor.kind == 103 and function:
                referenced = lib.clang_getCursorReferenced(cursor)
                helper = string(lib.clang_getCursorSpelling(referenced))
                for r in regions:
                    if r["kind"] == "function" and r["function"] == function and helper:
                        if helper not in r["helpers"]: r["helpers"].append(helper)
            for child in sub:
                walk(child, function)

        def add(kind, name, start, end, begin, finish, function, usr):
            key = (kind, start[2], end[2])
            if key in seen: return
            seen.add(key)
            fragment = raw[start[2]:end[2]]
            sha = hashlib.sha256(fragment).hexdigest()
            regions.append({"id": f"{kind}:{source.name}:{start[2]}:{sha[:16]}", "kind": kind,
                "name": name, "path": str(source), "lines": [start[1], end[1]],
                "byte_range": [start[2], end[2]], "insertion_range": [begin, finish],
                "source_sha256": sha, "text": fragment.decode(errors="replace"),
                "function": function, "usr": usr, "helpers": [], "callers": [], "referenced_types": [], "invocation_unit": "function call" if kind == "function" else "loop entry"})
        walk(lib.clang_getTranslationUnitCursor(tu))
        for region in regions:
            region["callers"] = sorted({r["function"] for r in regions if r["function"] != region["function"]
                                         and region["function"] in r["helpers"]})
        adaptations = (["GNU __restrict__ erased for source inventory only; alias semantics are not inferred; actual builds retain original source and qualifiers"]
                       if "-D__restrict__=" in arguments else [])
        return {"backend": "libclang-cindex", "version": string(lib.clang_getClangVersion()),
                "library": str(library), "arguments": arguments, "diagnostics": diagnostics,
                "parser_adaptations": adaptations,
                "regions": regions, "unresolved": unresolved,
                "scope": "free functions and ordinary loops defined in the BFS translation-unit source file",
                "limitations": ["header-defined, library, virtual/member and compiler-outlined code is not independently attributed",
                    "inlined source scopes remain source scopes, not machine-code symbols",
                    "OpenMP-disabled metadata inventory preserves _OPENMP; actual diagnostic execution retains original OpenMP flags",
                    "metadata parser substitutes Clang builtin/OpenMP declarations in the compiler-private header slot while preserving actual system-library search order; execution uses original compiler headers",
                    "transformation-specific OpenMP pragmas and macro-generated loop extents may remain unresolved"] + adaptations}
    finally:
        if tu.value: lib.clang_disposeTranslationUnit(tu)
        lib.clang_disposeIndex(index)


def instrument(source, regions):
    """Insert nested scope guards; original offsets remain the source identity."""
    raw = Path(source).read_bytes()
    edits = {}
    for index, region in enumerate(regions):
        begin, end = region["insertion_range"]
        opening = f"\n::swdb_profile::Scope swdb_scope_{index}({index});\n".encode()
        if region["kind"] == "loop":
            opening = b"{\n" + opening
            edits.setdefault(end, []).append((0, begin, b"\n}"))
        edits.setdefault(begin, []).append((1, -end, opening))
    for position in sorted(edits, reverse=True):
        raw = raw[:position] + b"".join(edit[2] for edit in sorted(edits[position])) + raw[position:]
    return raw


if __name__ == "__main__":
    request = json.loads(Path(sys.argv[1]).read_text())
    result = discover(request["source"], request["arguments"], request["library"])
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2))
