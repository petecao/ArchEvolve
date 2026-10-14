"""The C lowering tool: a core-subset C++ proof unit to C with the C++ names kept, plus anchors.

Created: 2026-10-14 ET (Probata proof of concept ticket 21). Design: formal-verification map 16 items 3
and 6 (the C lowering keeps C++ names, so formal halves type-check unchanged), 13 items 4 and 7 (stable
anchors for proof hints), 11 item 3 (the C lowering tool is a trusted tool). Format:
docs/reference/format-v0.4-c-lowering-wp.md.

- Deterministic code, never an LLM. clang 22.1.8 parses the C++ (`-ast-dump=json`, one filtered dump
  per lowered declaration); this module prints C from that syntax tree. The output names no absolute
  path and no time, so the same input gives the same bytes.
- The core subset (ticket 21): free functions with scalar, pointer and array parameters, global and
  local scalars and arrays, `if`, `for`, `while`, `do`, `break`, `continue`, `return`, integer and
  bool arithmetic, explicit casts, calls to functions defined in the same translation unit (lowered
  too). Anything else raises `Unsupported` naming the construct and its line: never a crash and
  never a partial C lowering (ticket 24 widens the subset; floating point comes with real-valued units).
- Anchors: `ghost.globals` (one file-scope slot), and per function `<f>.contract` (right before its
  definition), `<f>.entry`, `<f>.loopN.head` (right before each loop), `<f>.sN.before` and
  `<f>.sN.after` (around every statement, numbered in pre-order). Each is one comment line
  `/* swdb-anchor <id> */` in the C, listed with its line in `<f>.anchors.json`.
- `swdb lower` writes `<function>.c` and `<function>.anchors.json` into a folder.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

TOOL_ID = "swdb-c-lowering"
TOOL_VERSION = "1"                   # bump on any change to what the tool prints (a new method version)
NAMING_RULES = "kept-names.1"        # C++ names unchanged; unnamed parameters become swdb_unnamed_<n>
REQUIRED_CLANG = "22.1.8"
STD = "c++17"
ANCHOR = "/* swdb-anchor {} */"
ANCHOR_LINE = re.compile(r"^\s*/\* swdb-anchor (\S+) \*/$")
HEADERS = ("#include <stdbool.h>", "#include <stddef.h>", "#include <stdint.h>")
TIMEOUT_SECONDS = 120
_FOUND = {}

INTEGER_TYPES = {"bool", "char", "signed char", "unsigned char", "short", "unsigned short", "int", "unsigned int",
                 "long", "unsigned long", "long long", "unsigned long long", "size_t", "ptrdiff_t", "intptr_t",
                 "uintptr_t", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
                 "short int", "unsigned short int", "long int", "unsigned long int", "long long int",
                 "unsigned long long int", "signed", "unsigned", "signed int"}
SUFFIX = {"int": "", "unsigned int": "U", "long": "L", "unsigned long": "UL", "long long": "LL",
          "unsigned long long": "ULL"}
PASS_CASTS = {"LValueToRValue", "ArrayToPointerDecay", "FunctionToPointerDecay", "NoOp", "IntegralCast",
              "IntegralToBoolean", "PointerToBoolean", "BitCast"}
EXPLICIT_CASTS = {"CStyleCastExpr", "CXXStaticCastExpr", "CXXFunctionalCastExpr"}
LOOPS = {"ForStmt", "WhileStmt", "DoStmt"}
C_ONLY_KEYWORDS = {"restrict", "_Bool", "_Complex", "_Imaginary", "_Alignas", "_Alignof", "_Atomic", "_Generic",
                   "_Noreturn", "_Static_assert", "_Thread_local"}


class LoweringError(Exception):
    """The proof unit has no C lowering."""


class Unsupported(LoweringError):
    """A construct outside the subset (failure class unsupported_construct)."""

    def __init__(self, construct, line=None):
        self.construct, self.line = construct, line
        super().__init__(f"unsupported construct: {construct}" + (f" (line {line})" if line else ""))


class NotFound(LoweringError):
    """The source defines no such function (a usage error, not a failure class)."""


class ParseError(LoweringError):
    """clang could not parse the C++ (failure class parse_error)."""

    def __init__(self, message):
        super().__init__(f"parse error: {message}")


@dataclass(frozen=True)
class Tool:
    command: tuple
    version: str
    missing: str


@dataclass(frozen=True)
class Lowering:
    function: str
    text: str
    anchors: tuple
    declaration: str            # the C headers plus the unit function's prototype (for type-checking formal halves)
    parameters: tuple           # (name, C type, is_pointer) of the unit function
    source_sha256: str
    defines: tuple = ()
    tool: dict = field(default_factory=dict)
    externals: tuple = ()       # ticket 27: proof-semantics calls the unit makes (left undefined: the model defines them)
    probes: tuple = ()          # ticket 27: hazard probes {id, function, access, line, begin, end (C++ byte offsets)}

    @property
    def sha256(self):
        return hashlib.sha256(self.text.encode()).hexdigest()

    @property
    def anchors_json(self):
        data = {"tool": self.tool, "function": self.function, "c_lowering_sha256": self.sha256,
                "anchors": list(self.anchors)}
        return json.dumps(data, indent=1, sort_keys=True) + "\n"

    @property
    def anchors_sha256(self):
        return hashlib.sha256(self.anchors_json.encode()).hexdigest()

    def write(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        c_path, a_path = folder / f"{self.function}.c", folder / f"{self.function}.anchors.json"
        c_path.write_text(self.text)
        a_path.write_text(self.anchors_json)
        return c_path, a_path


# --- the tool and its identity ---------------------------------------------------------

def locate():
    """The clang++ this process uses: SWDB_CLANG (a command line; `none` = missing), else Homebrew's LLVM, else PATH."""
    key = os.environ.get("SWDB_CLANG", "")
    if key in _FOUND:
        return _FOUND[key]
    if key == "none":
        tool = Tool((), "", "clang disabled by SWDB_CLANG=none")
    else:
        if key:
            command = tuple(shlex.split(key))
        elif Path("/opt/homebrew/opt/llvm/bin/clang++").exists():
            command = ("/opt/homebrew/opt/llvm/bin/clang++",)
        elif shutil.which("clang++"):
            command = (shutil.which("clang++"),)
        else:
            command = ()
        tool = _probe(command)
    _FOUND[key] = tool
    return tool


def _probe(command):
    if not command:
        return Tool((), "", "clang++ not found (SWDB_CLANG, Homebrew LLVM or PATH)")
    try:
        done = subprocess.run([*command, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return Tool((), "", f"clang++ did not start: {exc}")
    match = re.search(r"clang version (\S+)", done.stdout)
    if done.returncode != 0 or not match:
        return Tool((), "", "clang++ did not report a version")
    if match.group(1) != REQUIRED_CLANG:
        return Tool((), match.group(1), f"clang {match.group(1)} found; the C lowering uses clang {REQUIRED_CLANG}")
    return Tool(tuple(command), match.group(1), "")


def identity():
    """{id, sha256} of the C lowering tool itself (this module's source) and of the clang binary it runs."""
    tool = locate()
    here = Path(__file__)
    found = {"c_lowering": {"id": f"{TOOL_ID}-{TOOL_VERSION}", "sha256": _file_sha256(here)}}
    if not tool.missing:
        found["clang"] = {"id": f"clang-{tool.version}", "sha256": _file_sha256(_binary(tool.command[0]))}
    return found


def _binary(command):
    path = shutil.which(command) or command
    return Path(path).resolve()


_SHA = {}


def _file_sha256(path):
    path = Path(path)
    key = (str(path), path.stat().st_mtime_ns, path.stat().st_size)
    if key not in _SHA:
        _SHA[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _SHA[key]


# --- clang's syntax tree -------------------------------------------------------------------

def _dump(tool, source, name, includes, defines):
    """Every top-level declaration clang's filtered dump prints for `name` (a list of JSON nodes)."""
    command = [*tool.command, "-x", "c++", f"-std={STD}", "-fopenmp", "-fsyntax-only", "-Xclang", "-ast-dump=json",
               "-Xclang", f"-ast-dump-filter={name}", f"-I{Path(source).parent}"]
    command += [f"-I{folder}" for folder in includes] + [f"-D{define}" for define in defines] + [str(source)]
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ParseError(f"clang did not finish: {exc}") from None
    if done.returncode != 0:
        errors = [line.strip() for line in done.stderr.splitlines() if "error:" in line]
        raise ParseError("; ".join(errors) or f"clang exited {done.returncode}")
    decoder, text, found, at = json.JSONDecoder(), done.stdout, [], 0
    while True:
        at = text.find("{", at)
        if at < 0:
            return found
        node, at = decoder.raw_decode(text, at)
        found.append(node)


def _named(nodes, name, kinds):
    return [n for n in nodes if n.get("name") == name and n.get("kind") in kinds and not n.get("isImplicit")]


# --- types -------------------------------------------------------------------------------------

def _qual(node):
    return (node.get("type") or {}).get("qualType", "")


def _ctype(qual_type, name="", line=None):
    """The C declarator of a core-subset type (with `name`, or abstract when name is empty)."""
    text = re.sub(r"\bstd::", "", qual_type).strip()
    if "&" in text:
        raise Unsupported(f"reference type {qual_type}", line)
    if re.search(r"[<>:(){}]", text):
        raise Unsupported(f"type {qual_type}", line)
    dims = ""
    match = re.fullmatch(r"(.*?)\s*((?:\[\d+\])+)", text)
    if match:
        text, dims = match.group(1), match.group(2)
        if not name:
            raise Unsupported(f"array type {qual_type} outside a declaration", line)
    parts = text.split("*")
    words = parts[0].split()
    base = " ".join(w for w in words if w not in ("const", "volatile"))
    if base in ("float", "double", "long double"):
        raise Unsupported(f"floating-point type {qual_type} (real-valued units come with later tickets)", line)
    if base not in INTEGER_TYPES and not (base == "void" and len(parts) > 1) and not (base == "void" and not name):
        raise Unsupported(f"type {qual_type}", line)
    stars = ""
    for quals in parts[1:]:
        quals = quals.split()
        if any(q not in ("const", "volatile") for q in quals):
            raise Unsupported(f"type {qual_type}", line)
        stars += "*" + ("".join(f"{q} " for q in quals))
    head = parts[0].strip()
    if not name:
        return f"{head} {stars}".rstrip() if stars else head
    return f"{head} {stars}{name}{dims}"


def _return_type(function_type, line):
    """The return type of a FunctionDecl's qualType `R (P1, P2)`."""
    depth = 0
    for at in range(len(function_type) - 1, -1, -1):
        char = function_type[at]
        if char == ")":
            depth += 1
        elif char == "(":
            depth -= 1
            if depth == 0:
                return function_type[:at].strip()
    raise Unsupported(f"function type {function_type}", line)


# --- the printer ---------------------------------------------------------------------------------

class _Printer:
    def __init__(self, function, semantics=None):
        self.function = function
        self.lines = []
        self.anchors = []
        self.line = None
        self.statements = 0
        self.loops = 0
        self.callees = []
        self.globals = []
        self.local_ids = set()
        # Ticket 27: calls a proof semantics covers stay undefined; tile pointers get a hazard probe at each access.
        self.semantics = semantics
        self.tile_vars = set()
        self.probes = []
        self._tile_ok = 0

    # positions and anchors
    def _at(self, node):
        loc = node.get("loc") or {}
        begin = (node.get("range") or {}).get("begin") or {}
        self.line = loc.get("line") or begin.get("line") or self.line

    def anchor(self, ident, kind, indent):
        self.lines.append("  " * indent + ANCHOR.format(ident))
        self.anchors.append({"id": ident, "kind": kind, "function": self.function, "line_in_function": len(self.lines)})

    def emit(self, text, indent):
        self.lines.append("  " * indent + text)

    # statements
    def body(self, node, indent):
        """A function or loop body: always braced; the caller wrote the opening line."""
        children = node.get("inner", []) if node.get("kind") == "CompoundStmt" else [node]
        for child in children:
            self.statement(child, indent)

    def statement(self, node, indent):
        self._at(node)
        kind = node.get("kind")
        if kind == "CompoundStmt":
            self.emit("{", indent)
            self.body(node, indent + 1)
            self.emit("}", indent)
            return
        self.statements += 1
        sid = f"{self.function}.s{self.statements}"
        self.anchor(f"{sid}.before", "before", indent)
        if kind in LOOPS:
            self.loops += 1
            self.anchor(f"{self.function}.loop{self.loops}.head", "loop_head", indent)
        self._statement(node, kind, indent)
        self.anchor(f"{sid}.after", "after", indent)

    def _statement(self, node, kind, indent):
        inner = node.get("inner", [])
        if kind == "DeclStmt":
            self.emit(" ".join(self.declaration(d) for d in inner), indent)
        elif kind == "ReturnStmt":
            self.emit(f"return {self.expr(inner[0], top=True)};" if inner else "return;", indent)
        elif kind == "BreakStmt":
            self.emit("break;", indent)
        elif kind == "ContinueStmt":
            self.emit("continue;", indent)
        elif kind == "NullStmt":
            self.emit(";", indent)
        elif kind == "IfStmt":
            if node.get("hasInit") or node.get("hasVar") or node.get("isConstexpr") or node.get("isConsteval"):
                raise Unsupported("if with an initializer, a condition variable or constexpr", self.line)
            self.emit(f"if ({self.expr(inner[0], top=True)}) {{", indent)
            self.body(inner[1], indent + 1)
            if node.get("hasElse"):
                self.emit("} else {", indent)
                self.body(inner[2], indent + 1)
            self.emit("}", indent)
        elif kind == "ForStmt":
            init, cond_var, cond, step, loop_body = inner
            if cond_var:
                raise Unsupported("for with a condition variable", self.line)
            head = self.declaration_list(init) if init.get("kind") == "DeclStmt" else \
                (self.expr(init, top=True) if init else "")
            cond_text = self.expr(cond, top=True) if cond else ""
            step_text = self.expr(step, top=True) if step else ""
            self.emit(f"for ({head}; {cond_text}; {step_text}) {{", indent)
            self.body(loop_body, indent + 1)
            self.emit("}", indent)
        elif kind == "WhileStmt":
            if node.get("hasVar"):
                raise Unsupported("while with a condition variable", self.line)
            self.emit(f"while ({self.expr(inner[0], top=True)}) {{", indent)
            self.body(inner[1], indent + 1)
            self.emit("}", indent)
        elif kind == "DoStmt":
            self.emit("do {", indent)
            self.body(inner[0], indent + 1)
            self.emit(f"}} while ({self.expr(inner[1], top=True)});", indent)
        elif kind and kind.endswith("Directive") and kind.startswith("OMP"):
            raise Unsupported(f"OpenMP directive {kind}", self.line)
        elif kind and (kind.endswith("Expr") or kind.endswith("Operator")):
            self.emit(f"{self.expr(node, top=True)};", indent)
        else:
            raise Unsupported(f"statement {kind}", self.line)

    def declaration_list(self, node):
        return ", ".join(self._var(d, first=i == 0) for i, d in enumerate(node.get("inner", [])))

    def declaration(self, node):
        return self._var(node, first=True) + ";"

    def _var(self, node, first):
        self._at(node)
        if node.get("kind") != "VarDecl":
            raise Unsupported(f"declaration {node.get('kind')}", self.line)
        if node.get("storageClass") in ("static", "extern") or node.get("tls"):
            raise Unsupported(f"{node.get('storageClass') or 'thread-local'} local variable {node.get('name')}", self.line)
        self.local_ids.add(node.get("id"))
        name = _name(node.get("name"), self.line)
        text = _ctype(_qual(node), name, self.line)
        if not first:                                        # for (int i = 0, j = 1; ...): repeat no type
            text = name
        init = node.get("inner", [])
        if init:
            tile = node.get("id") in self.tile_vars
            self._tile_ok += tile
            text += " = " + self.initializer(init[0], node.get("init"))
            self._tile_ok -= tile
        return text

    def initializer(self, node, style):
        if node.get("kind") == "InitListExpr":
            return "{" + ", ".join(self.initializer(e, "list") for e in node.get("inner", [])) + "}"
        if style not in ("c", "call", "list", None):
            raise Unsupported(f"initialization style {style}", self.line)
        return self.expr(node, top=True)

    # expressions
    def expr(self, node, top=False):
        text, atomic = self._expr(node)
        return text if top or atomic else f"({text})"

    # ticket 27: tile pointers and their hazard probes
    def _is_tile_pointer_call(self, node):
        node = _strip(node)
        if node.get("kind") != "CallExpr" or not self.semantics:
            return False
        callee = _strip(node.get("inner", [{}])[0])
        return (callee.get("referencedDecl") or {}).get("name") in self.semantics.get("tile_pointer", ())

    def _is_tile_pointer(self, node):
        node = _strip(node)
        if node.get("kind") == "DeclRefExpr":
            return (node.get("referencedDecl") or {}).get("id") in self.tile_vars
        if node.get("kind") == "BinaryOperator" and node.get("opcode") in ("+", "-"):
            return any(self._is_tile_pointer(child) for child in node.get("inner", []))
        return self._is_tile_pointer_call(node)

    def _tile_access(self, node):
        """Whether `node` reads or writes an element through a tile pointer (p[i], *p, *(p + i))."""
        node = _strip(node)
        if node.get("kind") == "ArraySubscriptExpr":
            return self._is_tile_pointer(node["inner"][0])
        if node.get("kind") == "UnaryOperator" and node.get("opcode") == "*":
            return self._is_tile_pointer(node["inner"][0])
        return False

    def _probe(self, node, access):
        """The access wrapped in its generated hazard probe; the site is recorded (C++ gets the same probe)."""
        node = _strip(node)
        ident = f"{self.function}.probe{len(self.probes) + 1}"
        begin, end = (node.get("range") or {}).get("begin") or {}, (node.get("range") or {}).get("end") or {}
        site = {"id": ident, "function": self.function, "access": access, "line": self.line,
                "begin": begin.get("offset"), "end": (end.get("offset") or 0) + (end.get("tokLen") or 0)}
        self.probes.append(site)
        self._tile_ok += 1
        if node.get("kind") == "ArraySubscriptExpr":
            text = f"{self.expr(node['inner'][0])}[{self.expr(node['inner'][1], top=True)}]"
        else:
            text = f"*{self.expr(node['inner'][0])}"
        self._tile_ok -= 1
        macro = "SWDB_TILE_READ" if access == "read" else "SWDB_TILE_WRITE"
        return f'(*{macro}(&({text}), "{ident}"))'

    def _expr(self, node):
        self._at(node)
        kind = node.get("kind")
        inner = node.get("inner", [])
        if self.semantics and kind == "ImplicitCastExpr" and node.get("castKind") == "LValueToRValue" and \
                self._tile_access(inner[0]):
            return self._probe(inner[0], "read"), True
        if self.semantics and kind in ("ArraySubscriptExpr", "UnaryOperator") and self._tile_access(node):
            return self._probe(node, "write"), True
        if self.semantics and self._tile_ok == 0 and kind == "DeclRefExpr" and \
                (node.get("referencedDecl") or {}).get("id") in self.tile_vars:
            raise Unsupported("a tile pointer used other than to read or write a tile element (p[i], *p)", self.line)
        if self.semantics and self._tile_ok == 0 and self._is_tile_pointer_call(node):
            raise Unsupported("a tile pointer call whose result is not kept in a local variable or read at once",
                              self.line)
        if kind == "ImplicitCastExpr":
            if node.get("castKind") not in PASS_CASTS:
                raise Unsupported(f"implicit conversion {node.get('castKind')}", self.line)
            return self._expr(inner[0])
        if kind in EXPLICIT_CASTS:
            if node.get("castKind") not in PASS_CASTS | {"IntegralToBoolean"}:
                raise Unsupported(f"cast {node.get('castKind')}", self.line)
            return f"({_ctype(_qual(node), '', self.line)}){self.expr(inner[0])}", False
        if kind == "ParenExpr":
            return f"({self.expr(inner[0], top=True)})", True
        if kind == "IntegerLiteral":
            qual = re.sub(r"\bstd::", "", _qual(node))
            if qual not in SUFFIX:
                raise Unsupported(f"integer literal of type {_qual(node)}", self.line)
            return f"{node['value']}{SUFFIX[qual]}", True
        if kind == "CXXBoolLiteralExpr":
            return ("true" if node.get("value") else "false"), True
        if kind == "CharacterLiteral":
            return f"((char){node['value']})", True
        if kind == "DeclRefExpr":
            ref = node.get("referencedDecl") or {}
            if ref.get("kind") == "FunctionDecl":
                if ref.get("name") not in self.callees and ref.get("name") != self.function:
                    self.callees.append(ref["name"])
            elif ref.get("kind") == "VarDecl":
                if ref.get("id") not in self.local_ids and ref.get("name") not in self.globals:
                    self.globals.append(ref["name"])
            elif ref.get("kind") != "ParmVarDecl":
                raise Unsupported(f"reference to a {ref.get('kind')} ({ref.get('name')})", self.line)
            if node.get("qualifier") or "::" in str(node.get("name", "")):
                raise Unsupported("qualified name", self.line)
            return _name(ref.get("name"), self.line), True
        if kind == "BinaryOperator":
            tile = bool(self.semantics) and node.get("opcode") == "=" and self._is_tile_pointer_call(inner[1])
            self._tile_ok += tile
            text = f"{self.expr(inner[0])} {node['opcode']} {self.expr(inner[1])}"
            self._tile_ok -= tile
            return text, False
        if kind == "CompoundAssignOperator":
            return f"{self.expr(inner[0])} {node['opcode']} {self.expr(inner[1])}", False
        if kind == "UnaryOperator":
            operand = self.expr(inner[0])
            if node.get("opcode") in ("__extension__", "__real", "__imag", "co_await"):
                raise Unsupported(f"operator {node.get('opcode')}", self.line)
            return (f"{operand}{node['opcode']}" if node.get("isPostfix") else f"{node['opcode']}{operand}"), False
        if kind == "ArraySubscriptExpr":
            return f"{self.expr(inner[0])}[{self.expr(inner[1], top=True)}]", True
        if kind == "ConditionalOperator":
            return f"{self.expr(inner[0])} ? {self.expr(inner[1])} : {self.expr(inner[2])}", False
        if kind == "CallExpr":
            callee = inner[0]
            while callee.get("kind") == "ImplicitCastExpr" and callee.get("castKind") == "FunctionToPointerDecay":
                callee = callee["inner"][0]
            ref = callee.get("referencedDecl") or {}
            if callee.get("kind") != "DeclRefExpr" or ref.get("kind") != "FunctionDecl":
                raise Unsupported("call through anything but a function name", self.line)
            if str(ref.get("name", "")).startswith("__builtin"):
                raise Unsupported(f"builtin call {ref.get('name')}", self.line)
            for argument in inner[1:]:
                if argument.get("kind") == "CXXDefaultArgExpr":
                    raise Unsupported("default argument", self.line)
            name, _ = self._expr(callee)
            return f"{name}({', '.join(self.expr(a, top=True) for a in inner[1:])})", True
        raise Unsupported(_describe(kind), self.line)


def _strip(node):
    """The node under parentheses and pass-through implicit conversions."""
    while node.get("kind") == "ParenExpr" or (node.get("kind") == "ImplicitCastExpr" and
                                               node.get("castKind") in PASS_CASTS):
        node = node["inner"][0]
    return node


def _tile_vars(printer, body):
    """IDs of the local variables that hold a tile pointer (initialized or assigned from a tile-pointer call)."""
    found, pending = set(), [body]
    while pending:
        node = pending.pop()
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        if kind == "VarDecl" and node.get("inner") and printer._is_tile_pointer_call(node["inner"][0]):
            found.add(node.get("id"))
        if kind == "BinaryOperator" and node.get("opcode") == "=" and printer._is_tile_pointer_call(node["inner"][1]):
            target = _strip(node["inner"][0])
            if target.get("kind") == "DeclRefExpr":
                found.add((target.get("referencedDecl") or {}).get("id"))
        pending += node.get("inner", [])
    return found


def _describe(kind):
    named = {"CXXMemberCallExpr": "member function call", "CXXOperatorCallExpr": "overloaded operator call",
             "MemberExpr": "member access (classes and structs)", "CXXThisExpr": "this",
             "CXXNewExpr": "new", "CXXDeleteExpr": "delete", "StringLiteral": "string literal",
             "FloatingLiteral": "floating-point literal (real-valued units come with later tickets)",
             "CXXNullPtrLiteralExpr": "nullptr", "LambdaExpr": "lambda", "UnaryExprOrTypeTraitExpr": "sizeof or alignof",
             "CXXReinterpretCastExpr": "reinterpret_cast", "CXXConstCastExpr": "const_cast",
             "MaterializeTemporaryExpr": "C++ temporary", "ExprWithCleanups": "C++ temporary"}
    return named.get(kind, f"expression {kind}")


def _name(name, line):
    if not name:
        return name
    if name in C_ONLY_KEYWORDS or not re.fullmatch(r"[A-Za-z_]\w*", name):
        raise Unsupported(f"name {name!r} that is not a C identifier", line)
    return name


# --- lowering ---------------------------------------------------------------------------------------

def lower(source, function, includes=(), defines=(), semantics=None):
    """The C lowering of `function` (and of every function and global it uses) from the C++ file `source`.

    `semantics` (ticket 27; the bounded verifier passes it, `swdb lower` does not): {externals: names a proof
    semantics defines (calls and queries; they may have no body and are not lowered), tile_pointer: the calls
    that return a tile pointer}. Every element access through a tile pointer then gets a generated hazard probe
    (`SWDB_TILE_READ` / `SWDB_TILE_WRITE`, ID `<function>.probe<N>`), listed in `Lowering.probes` with its C++
    source range so the C++ side gets the same probe. Without `semantics` the output is unchanged."""
    tool = locate()
    if tool.missing:
        raise LoweringError(tool.missing)
    source = Path(source)
    if not source.is_file():
        raise LoweringError(f"no source file {source}")
    defines = tuple(sorted(defines))
    externals = set((semantics or {}).get("externals", ()))
    unit = _function(tool, source, function, includes, defines, unit=True)
    order, seen, pending_globals, definitions, prototypes = [], set(), [], {}, {}
    called, probes = [], []

    def visit(name, node):
        seen.add(name)
        printer = _Printer(name, semantics)
        prototype, params = _signature(node, printer)
        body = [c for c in node.get("inner", []) if c.get("kind") == "CompoundStmt"][0]
        printer.local_ids.update(p.get("id") for p in node.get("inner", []) if p.get("kind") == "ParmVarDecl")
        if semantics:
            printer.tile_vars = _tile_vars(printer, body)
        printer.anchor(f"{name}.entry", "entry", 1)
        printer.body(body, 1)
        definitions[name] = (prototype, printer)
        prototypes[name] = (prototype, params)
        probes.extend(printer.probes)
        for callee in printer.callees:
            if callee in externals:
                if callee not in called:
                    called.append(callee)
                continue
            if callee not in seen:
                visit(callee, _function(tool, source, callee, includes, defines))
        for global_name in printer.globals:
            if global_name not in pending_globals:
                pending_globals.append(global_name)
        order.append(name)

    visit(function, unit)
    globals_text = [_global(tool, source, name, includes, defines) for name in pending_globals]
    lines = [f"/* C lowering of {function} from {source.name} (sha256 {_file_sha256(source)}) by {TOOL_ID} "
             f"{TOOL_VERSION} ({NAMING_RULES}), clang {tool.version}. Generated: do not edit. */"]
    if defines:
        lines.append(f"/* Build constants: {', '.join(defines)} */")
    lines += list(HEADERS)
    anchors = []
    lines.append(ANCHOR.format("ghost.globals"))
    anchors.append({"id": "ghost.globals", "kind": "ghost_globals", "function": None, "line": len(lines)})
    lines += globals_text
    lines += [f"{prototypes[name][0]};" for name in order]
    for name in order:
        prototype, printer = definitions[name]
        lines.append(ANCHOR.format(f"{name}.contract"))
        anchors.append({"id": f"{name}.contract", "kind": "contract", "function": name, "line": len(lines)})
        lines.append(f"{prototype} {{")
        start = len(lines)
        for anchor in printer.anchors:
            entry = dict(anchor)
            entry["line"] = start + entry.pop("line_in_function")
            anchors.append(entry)
        lines += printer.lines
        lines.append("}")
    ids = [a["id"] for a in anchors]
    if len(ids) != len(set(ids)):
        raise LoweringError("anchor IDs are not unique (a C lowering tool defect)")
    unit_prototype, unit_params = prototypes[function]
    declaration = "\n".join([*HEADERS, *globals_text, f"{unit_prototype};"]) + "\n"
    return Lowering(function=function, text="\n".join(lines) + "\n", anchors=tuple(anchors), declaration=declaration,
                    parameters=tuple(unit_params), source_sha256=_file_sha256(source), defines=defines,
                    tool={"id": TOOL_ID, "version": TOOL_VERSION, "naming_rules": NAMING_RULES, "clang": tool.version},
                    externals=tuple(sorted(called)), probes=tuple(probes))


def _function(tool, source, name, includes, defines, unit=False):
    nodes = _dump(tool, source, name, includes, defines)
    templates = _named(nodes, name, {"FunctionTemplateDecl"})
    if templates:
        raise Unsupported(f"function template {name}")
    methods = _named(nodes, name, {"CXXMethodDecl", "CXXConstructorDecl", "CXXDestructorDecl"})
    found = [n for n in _named(nodes, name, {"FunctionDecl"}) if any(c.get("kind") == "CompoundStmt" for c in n.get("inner", []))]
    if not found and methods:
        raise Unsupported(f"member function {name}")
    if not found and unit:
        raise NotFound(f"{Path(source).name} defines no function {name}")
    if not found:
        raise Unsupported(f"call to a function with no body in the translation unit: {name}")
    if len({(n.get("loc") or {}).get("offset") for n in found}) > 1:
        raise Unsupported(f"overloaded function {name}")
    node = found[0]
    mangled = node.get("mangledName", name)
    if mangled != name and mangled.startswith("_ZN"):
        raise Unsupported(f"function {name} inside a namespace or class")
    return node


def _signature(node, printer):
    printer._at(node)
    line = printer.line
    if node.get("variadic"):
        raise Unsupported(f"variadic function {node.get('name')}", line)
    for flag in ("isDeleted", "explicitlyDefaulted"):
        if node.get(flag):
            raise Unsupported(f"special function {node.get('name')}", line)
    params, texts, unnamed = [], [], 0
    for param in [c for c in node.get("inner", []) if c.get("kind") == "ParmVarDecl"]:
        if param.get("inner"):
            raise Unsupported("default argument", line)
        name = param.get("name")
        if not name:
            unnamed += 1
            name = f"swdb_unnamed_{unnamed}"
        name = _name(name, line)
        ctype = _ctype(_qual(param), name, line)
        texts.append(ctype)
        params.append((name, _ctype(_qual(param), "", line), "*" in _qual(param)))
    returns = _ctype(_return_type(_qual(node), line), "", line)
    head = "static " if node.get("storageClass") == "static" else ""
    return f"{head}{returns} {_name(node['name'], line)}({', '.join(texts) or 'void'})", params


def _global(tool, source, name, includes, defines):
    nodes = [n for n in _named(_dump(tool, source, name, includes, defines), name, {"VarDecl"})]
    if len(nodes) != 1:
        raise Unsupported(f"global variable {name} (not one plain declaration)")
    node = nodes[0]
    printer = _Printer(name)
    printer._at(node)
    if node.get("tls"):
        raise Unsupported(f"thread-local global {name}", printer.line)
    head = "static " if node.get("storageClass") == "static" else ""
    text = head + _ctype(_qual(node), _name(name, printer.line), printer.line)
    init = node.get("inner", [])
    if init:
        text += " = " + printer.initializer(init[0], node.get("init"))
    if printer.callees or printer.globals:
        raise Unsupported(f"global {name} initialized from other functions or globals", printer.line)
    return text + ";"


# --- swdb lower ---------------------------------------------------------------------------------------

def register_cli(commands):
    sub = commands.add_parser("lower", help="C lowering of one core-subset C++ function (kept names, anchors)",
                              description="lower one C++ function of the core subset (and what it uses) to C with the "
                                          "C++ names kept and anchors for proof hints; write <function>.c and "
                                          "<function>.anchors.json into --out. Deterministic: the same input gives "
                                          "the same bytes.")
    sub.add_argument("--source", type=Path, required=True, help="the C++ file that defines the function")
    sub.add_argument("--function", required=True)
    sub.add_argument("--include", type=Path, action="append", default=[], help="an include folder (repeatable)")
    sub.add_argument("--define", action="append", default=[], help="a build constant NAME or NAME=VALUE (repeatable)")
    sub.add_argument("--out", type=Path, required=True, help="the folder to write into")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=_cli)


def _cli(args):
    from swdb.cli import Failure
    try:
        lowering = lower(args.source, args.function, args.include, args.define)
    except LoweringError as exc:
        raise Failure(str(exc)) from None
    c_path, a_path = lowering.write(args.out)
    return {"function": lowering.function, "tool": lowering.tool,
            "c_lowering": {"path": str(c_path), "sha256": lowering.sha256},
            "anchors": {"path": str(a_path), "sha256": lowering.anchors_sha256, "count": len(lowering.anchors)}}
