"""Full original-TU provenance for standard-model substitution; created 2026-10-15 ET.

Clang's matching C API visits physical declarations and includes, including headers
omitted by the filtered lowering AST. A clean probe alone is never a certificate.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ID = "swdb-stdlib-provenance-1"
ENV = ("CPATH", "CPLUS_INCLUDE_PATH", "C_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "INCLUDE")
MODELED = {"vector", "pair", "min", "max", "copy", "swap", "allocator", "__wrap_iter"}
ALLOCATORS = {"malloc", "calloc", "realloc", "free", "aligned_alloc", "posix_memalign"}


class Refused(Exception):
    pass


def _sha(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256")
    return digest.hexdigest()


def identity():
    return {"id": ID, "sha256": _sha(__file__)}


class _String(C.Structure):
    _fields_ = [("data", C.c_void_p), ("flags", C.c_uint)]


class _Cursor(C.Structure):
    _fields_ = [("kind", C.c_uint), ("xdata", C.c_int), ("data", C.c_void_p * 3)]


class _Location(C.Structure):
    _fields_ = [("data", C.c_void_p * 2), ("offset", C.c_uint)]


class _Clang:
    """Small binding to the pinned clang-c/Index.h ABI; no optional Python package."""
    def __init__(self, tool):
        root = subprocess.run([*tool.command, "-print-resource-dir"], capture_output=True,
                              text=True, check=True, timeout=30).stdout.strip()
        self.root = Path(root).resolve().parents[2]
        paths = [self.root / "lib" / name for name in ("libclang.dylib", "libclang.so")]
        self.path = next((p.resolve() for p in paths if p.is_file()), None)
        if self.path is None:
            raise Refused("the selected LLVM distribution has no matching libclang")
        self.lib = C.CDLL(str(self.path))
        def bind(name, result, *args):
            fn = getattr(self.lib, name)
            fn.restype, fn.argtypes = result, list(args)
            return fn
        self.string = bind("clang_getCString", C.c_char_p, _String)
        self.dispose_string = bind("clang_disposeString", None, _String)
        self.version = self.text(bind("clang_getClangVersion", _String)())
        if not re.search(r"\b" + re.escape(tool.version) + r"\b", self.version):
            raise Refused("libclang and the selected lowering driver versions differ")
        self.index = bind("clang_createIndex", C.c_void_p, C.c_int, C.c_int)(0, 0)
        self.destroy_index = bind("clang_disposeIndex", None, C.c_void_p)
        self.parse = bind("clang_parseTranslationUnit2FullArgv", C.c_int, C.c_void_p, C.c_char_p,
                          C.POINTER(C.c_char_p), C.c_int, C.c_void_p, C.c_uint, C.c_uint,
                          C.POINTER(C.c_void_p))
        self.destroy_tu = bind("clang_disposeTranslationUnit", None, C.c_void_p)
        self.root_cursor = bind("clang_getTranslationUnitCursor", _Cursor, C.c_void_p)
        self.spelling = bind("clang_getCursorSpelling", _String, _Cursor)
        self.is_declaration = bind("clang_isDeclaration", C.c_uint, C.c_uint)
        self.kind = bind("clang_getCursorKindSpelling", _String, C.c_uint)
        self.location = bind("clang_getCursorLocation", _Location, _Cursor)
        self.file_location = bind("clang_getFileLocation", None, _Location, C.POINTER(C.c_void_p),
                                  C.POINTER(C.c_uint), C.POINTER(C.c_uint), C.POINTER(C.c_uint))
        self.filename = bind("clang_getFileName", _String, C.c_void_p)
        self.definition = bind("clang_isCursorDefinition", C.c_uint, _Cursor)
        self.parent = bind("clang_getCursorSemanticParent", _Cursor, _Cursor)
        self.mangling = bind("clang_Cursor_getMangling", _String, _Cursor)
        self.referenced = bind("clang_getCursorReferenced", _Cursor, _Cursor)
        self.visitor = C.CFUNCTYPE(C.c_uint, _Cursor, _Cursor, C.c_void_p)
        self.visit = bind("clang_visitChildren", C.c_uint, _Cursor, self.visitor, C.c_void_p)
        self.inclusion = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(_Location), C.c_uint, C.c_void_p)
        self.includes = bind("clang_getInclusions", None, C.c_void_p, self.inclusion, C.c_void_p)
        self.diag_count = bind("clang_getNumDiagnostics", C.c_uint, C.c_void_p)
        self.diag = bind("clang_getDiagnostic", C.c_void_p, C.c_void_p, C.c_uint)
        self.severity = bind("clang_getDiagnosticSeverity", C.c_int, C.c_void_p)
        self.diag_text = bind("clang_getDiagnosticSpelling", _String, C.c_void_p)
        self.destroy_diag = bind("clang_disposeDiagnostic", None, C.c_void_p)

    def text(self, value):
        text = self.string(value)
        result = text.decode("utf-8", "replace") if text else ""
        self.dispose_string(value)
        return result

    def physical(self, cursor):
        file, line, column, offset = C.c_void_p(), C.c_uint(), C.c_uint(), C.c_uint()
        self.file_location(self.location(cursor), C.byref(file), C.byref(line), C.byref(column), C.byref(offset))
        return (str(Path(self.text(self.filename(file))).resolve()) if file else "", line.value, offset.value)

    def translation_unit(self, command, source):
        args = (C.c_char_p * len(command))(*(os.fsencode(a) for a in command))
        tu = C.c_void_p()
        error = self.parse(self.index, os.fsencode(source), args, len(args), None, 0, 1, C.byref(tu))
        if error or not tu:
            raise Refused(f"full-TU libclang parse failed ({error})")
        errors = []
        for i in range(self.diag_count(tu)):
            diagnostic = self.diag(tu, i)
            if self.severity(diagnostic) >= 3:
                errors.append(self.text(self.diag_text(diagnostic)))
            self.destroy_diag(diagnostic)
        if errors:
            self.destroy_tu(tu)
            raise Refused("full-TU parser rejected the driver context: " + "; ".join(errors[:3]))
        return tu

    def closure(self, tu):
        files = set()
        @self.inclusion
        def take(file, stack, depth, data):
            files.add(str(Path(self.text(self.filename(file))).resolve()))
        self.includes(tu, take, None)
        return files


def _command(tool, source, includes, defines):
    return [*tool.command, "-x", "c++", "-std=c++17", "-fopenmp", "-fsyntax-only",
            f"-I{Path(source).parent}", *[f"-I{p}" for p in includes],
            *[f"-D{d}" for d in defines], str(source)]


def certify(tool, source, *, includes=(), defines=(), models=()):
    """Return a passed/refused original-TU certificate, never an inferred library premise.

    Call for all modeled std substitutions, including algorithms without std_types.
    Re-run on source replay; the certificate binds every transitive physical file.
    """
    report = {"check": identity(), "verdict": "refused", "reason": ""}
    parser, tu = None, None
    try:
        source = Path(source).resolve()
        parser = _Clang(tool)
        report["parser"] = {"id": "libclang-" + tool.version, "sha256": _sha(parser.path)}
        canonical = parser.root / "include" / "c++" / "v1"
        if not (canonical / "vector").is_file():
            raise Refused("the selected LLVM distribution has no canonical libc++ headers")
        canonical = canonical.resolve()
        # Driver-command header injection is not an audited library selection.
        if any(a.startswith(("-I", "-D", "-U", "-include", "-imacros", "-isystem", "-iquote", "-ivfsoverlay", "-fmodule", "@"))
               for a in tool.command[1:]):
            raise Refused("header-injecting compiler command options are not modeled")
        clean_environment = {k: v for k, v in os.environ.items() if k not in ENV}
        baseline = subprocess.run([*tool.command, "-x", "c++", "-std=c++17", "-fopenmp", "-E", "-H", "-"],
            input="#include <vector>\n#include <utility>\n#include <algorithm>\n#include <new>\n#include <cstdlib>\n",
            capture_output=True, text=True, env=clean_environment, timeout=120)
        if baseline.returncode:
            raise Refused("clean canonical standard-header baseline does not parse")
        baseline_files = {str(Path(m.group(1)).resolve()) for line in baseline.stderr.splitlines()
                          if (m := re.match(r"^\.+ (.+?)(?: \(.*\))?$", line))}
        if str(canonical / "vector") not in baseline_files:
            raise Refused("the selected driver does not use its canonical libc++ vector header")
        report["baseline"] = [{"path": p, "sha256": _sha(p)} for p in sorted(baseline_files)]
        command = _command(tool, source, includes, defines)
        tu = parser.translation_unit(command[:-1], source)
        files = parser.closure(tu)
        macros = subprocess.run([*command[:-1], "-dM", "-E", command[-1]], capture_output=True,
                                text=True, timeout=120)
        if macros.returncode or not re.search(r"^#define _LIBCPP_VERSION 220108$", macros.stdout, re.M):
            raise Refused("the original TU does not select libc++ 22.1.8")
        report["library"] = {"id": "libc++-22.1.8", "version_macro": 220108}
        # Independently compare with the exact driver invocation used by lowering.
        driver = subprocess.run([*command[:-1], "-H", command[-1]], capture_output=True, text=True, timeout=120)
        if driver.returncode:
            raise Refused("the original driver TU does not parse")
        driver_files = {str(Path(m.group(1)).resolve()) for line in driver.stderr.splitlines()
                        if (m := re.match(r"^\.+ (.+?)(?: \(.*\))?$", line))}
        if files - {str(source)} != driver_files:
            raise Refused("libclang and lowering driver see different physical include closures")
        known = {str(p.relative_to(canonical)) for p in canonical.rglob("*") if p.is_file()}
        for file in files:
            path = Path(file)
            if path.is_relative_to(canonical) or file in baseline_files:
                continue
            # Reject top-level and internal standard-header shadowing at any include root.
            if any("/".join(path.parts[-len(Path(name).parts):]) == name for name in known):
                raise Refused(f"noncanonical standard header in original TU: {file}")
        report["headers"] = [{"path": p, "sha256": _sha(p)} for p in sorted(files)]
        report["context"] = {"command": command, "environment": {k: os.environ[k] for k in ENV if k in os.environ}}
        declarations, bindings, problems = [], [], []
        # Candidate macros may otherwise rewrite canonical headers while leaving each
        # resulting declaration physically attributed to the genuine header.
        canonical_words = set()
        for file in files & baseline_files:
            if Path(file).is_relative_to(canonical):
                canonical_words.update(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", Path(file).read_text(errors="replace")))
        def inspect_node(cursor, parent, data):
            kind = parser.text(parser.kind(cursor.kind))
            name = parser.text(parser.spelling(cursor))
            file, line, offset = parser.physical(cursor)
            trusted = bool(file and Path(file).is_relative_to(canonical))
            if cursor.kind == 501 and file and file not in baseline_files:
                if name in canonical_words or name.startswith(("__", "_LIBCPP")):
                    problems.append(f"candidate macro can rewrite canonical standard headers: {file}:{line} ({name})")
            if parser.is_declaration(cursor.kind):
                namespace, ancestor = [], parser.parent(cursor)
                for _ in range(12):
                    if not ancestor.kind or ancestor.kind == 300:  # translation unit
                        break
                    namespace.append(parser.text(parser.spelling(ancestor)))
                    ancestor = parser.parent(ancestor)
                if "std" in namespace and file and not trusted and file not in baseline_files:
                    problems.append(f"project declaration in the modeled std namespace: {file}:{line} ({name})")
                if name in MODELED and "std" in namespace:
                    declarations.append({"name": name, "file": file, "line": line, "offset": offset,
                                         "definition": bool(parser.definition(cursor))})
                    if not trusted:
                        problems.append(f"noncanonical std::{name} declaration: {file}:{line}")
                if kind == "FunctionDecl":
                    mangled = parser.text(parser.mangling(cursor))
                    allocation = (name.startswith(("operator new", "operator delete")) or name in ALLOCATORS or
                                  mangled.lstrip("\x01").startswith(("_Zn", "_Zd")) or
                                  mangled.lstrip("\x01") in ALLOCATORS or
                                  mangled.lstrip("\x01").startswith("_ZSt15set_new_handler"))
                    if allocation and file and not trusted and file not in baseline_files:
                        problems.append(f"source-defined allocation/deallocation hook: {file}:{line} ({name})")
            if kind in {"CallExpr", "CXXNewExpr", "CXXDeleteExpr"} and file and file not in baseline_files:
                callee = parser.referenced(cursor)
                if callee.kind:
                    origin, origin_line, _ = parser.physical(callee)
                    bindings.append({"name": parser.text(parser.spelling(callee)),
                        "mangled": parser.text(parser.mangling(callee)), "file": origin,
                        "line": origin_line, "call_file": file, "call_line": line})
                if (parser.text(parser.spelling(callee)) == "set_new_handler" or
                        parser.text(parser.mangling(callee)).lstrip("\x01").startswith("_ZSt15set_new_handler")):
                    problems.append(f"source-defined allocation handler registration: {file}:{line}")
            # Canonical bodies cannot contain project definitions; declarations still recurse
            # to instantiated templates and members, not to thousands of expression cursors.
            if trusted and kind in {"FunctionDecl", "CXXMethod", "Constructor", "Destructor", "FunctionTemplate"}:
                return 1
            return 2
        @parser.visitor
        def inspect(cursor, parent, data):
            try:
                return inspect_node(cursor, parent, data)
            except Exception as exc:
                problems.append("full-TU declaration traversal failed: " + str(exc))
                return 0
        parser.visit(parser.root_cursor(tu), inspect, None)
        if problems:
            raise Refused(problems[0])
        report["declarations"] = sorted(declarations, key=lambda d: (d["file"], d["offset"], d["name"]))
        report["bindings"] = sorted(bindings, key=lambda d: (d["call_file"], d["call_line"], d["name"]))
        report["models"] = sorted(models)
        report["verdict"] = "passed"
        report["reason"] = "original full TU uses canonical standard declarations without source allocation hooks"
    except (Refused, OSError, ValueError, AttributeError, subprocess.SubprocessError) as exc:
        report["reason"] = str(exc)
    finally:
        if parser:
            if tu:
                parser.destroy_tu(tu)
            parser.destroy_index(parser.index)
    report["sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
    return report


def runtime_identity(tool):
    """Transitive tool identity: checker source and matching native parser binary."""
    parser = None
    try:
        parser = _Clang(tool)
        return {"check": identity(), "parser": {"id": "libclang-" + tool.version, "sha256": _sha(parser.path)}}
    except (Refused, OSError, ValueError, AttributeError, subprocess.SubprocessError) as exc:
        return {"check": identity(), "unavailable": str(exc)}
    finally:
        if parser:
            parser.destroy_index(parser.index)


def needed(models, allocation=False):
    """The shared source admission seam: all standard models and new[] lowering."""
    return allocation or any(name.startswith(("std_", "swdb_alloc_new_array_")) for name in models)


def check(certificate, tool, source, *, includes=(), defines=(), models=()):
    """Rebuild the original full TU immediately before launch; return a refusal or None."""
    fresh = certify(tool, source, includes=includes, defines=defines, models=models)
    if fresh["verdict"] != "passed":
        return fresh["reason"]
    if fresh != certificate:
        return "the original standard declaration/header/parser context changed before launch"
    return None
