"""The C lowering tool: a C++ proof unit in the declared subset to C with the C++ names kept, plus anchors.

Created: 2026-10-14 ET (Probata proof of concept ticket 21). Updated: 2026-10-14 ET (ticket 24: the declared
C++ subset; ticket 25: `std::vector<T>` and `std::pair` through their C models, swdb.std_models). Design: formal-verification map 16 items 3 and 6 (the C lowering keeps C++ names, so formal
halves type-check unchanged; the subset by construct), 13 items 4 and 7 (stable anchors for proof hints),
11 item 3 (the C lowering tool is a trusted tool). Format: docs/reference/format-v0.4-c-lowering-wp.md.

- Deterministic code, never an LLM. clang 22.1.8 parses the C++ (`-ast-dump=json`, one filtered dump
  per declaration name); this module prints C from that syntax tree. The output names no absolute
  path and no time, so the same input gives the same bytes.
- The subset (ticket 24, map 16 item 6): C plus references; classes without inheritance or virtual
  functions; member functions and operators; constructors and destructors as explicit calls;
  instantiated templates; `new[]`/`delete[]`; `enum class`, `constexpr`, `static_assert`; `std::min`,
  `std::max`, `std::copy`, `std::swap` through C models; OpenMP `parallel`, `for` (static, dynamic,
  `nowait`), `critical`, `atomic`, `barrier`, `reduction`; `__sync_*` and `__atomic_*` through C models;
  calls named in `summaries` (and every `__dxc_*` and `maa_*` call, which needs one) kept as calls.
  OpenMP and atomics get their meaning for ONE thread here (a parallel region runs as one thread; a
  CAS is a read, a compare and a write); the program for one symbolic thread of N is ticket 45.
  Anything else raises `Unsupported` naming the construct and its source line: never a crash and
  never a partial C lowering. `std::vector<T>` (not `bool`) and `std::pair<A, B>` (scalar or pointer
  elements) lower to the structs and member functions of `swdb.std_models` (ticket 25); an iterator is a
  pointer, a range-for over a vector a pointer loop; any other member reads "unsupported construct".
- `float` and `double` (types, literals, conversions) print as the same C types: the lowering is faithful
  to IEEE semantics. What a proof means for them is the verifier's float model, a method-version choice:
  the frozen WP flags read `-wp-model +real` (floats as mathematical reals; the rounding gap is an
  assumption entry, map 11 item 6), `+float` would check IEEE rounding. `long double` stays outside.
- Naming rules (NAMING_RULES, a pinned part of every proof record's content-hash set; RULES below):
  C++ names are kept; a class becomes a struct of the same name and fields; references become
  pointers; operators, member functions, constructors and destructors become named functions.
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

from swdb import bounded_initialization, cpu_effects, std_models, stdlib_provenance, terminal_release, vector_ownership, wp_pointer_bounds

TOOL_ID = "swdb-c-lowering"
TOOL_VERSION = "9"                   # checked WP pointer formation and integer model receiving slots
NAMING_RULES = "kept-names.3"        # bump on any change to RULES
RULES = (
    "A function, parameter, local, global or field keeps its C++ name.",
    "An unnamed parameter becomes swdb_unnamed_<n> (n counts from 1 in each function).",
    "A class or struct C becomes `struct C` with the same fields in order, plus `typedef struct C C;`.",
    "An instantiated class template C<A1, ..., An> becomes the struct C_<a1>_..._<an> (defaulted arguments "
    "included), each argument "
    "spelled by its C type: spaces become `_`, `*` becomes `ptr`, a negative integer -k becomes `mk`.",
    "An instantiated function template f<A1, ..., An> becomes the function f_<a1>_..._<an> (the same spelling).",
    "A member function m of class C becomes C_m with a first parameter `C *this` (`const C *this` for a "
    "const member function); a static member function becomes C_m with no `this`.",
    "A constructor of C becomes C_ctor(C *this, ...), called right after the declaration of the object; a "
    "destructor becomes C_dtor(C *this), called at the end of the object's scope.",
    "An operator becomes a named function: operator@ of class C is C_operator_<name>, a free operator@ is "
    "operator_<name>, with <name> from OPERATOR_NAMES.",
    "A reference T& becomes a pointer T*: the callee dereferences it, the caller passes an address (a "
    "temporary bound to a reference becomes a C compound literal).",
    "An enum or enum class becomes its underlying integer type (int if none is fixed); an enumerator is "
    "printed as its value.",
    "std::min, std::max, std::swap and std::copy at type T become calls of the C models std_min_<t>, "
    "std_max_<t>, std_swap_<t>, std_copy_<t>.",
    "__atomic_<op>(p, ...) and __sync_<op>(p, ...) at type T become calls of the C models "
    "swdb_atomic_<op>_<t> and swdb_sync_<op>_<t> (one-thread meaning, memory order dropped).",
    "new T[n] becomes swdb_alloc_new_array_<t>((size_t)(n)), a C model whose contract is the assumption entry "
    "\"allocation succeeds\" (map 16 item 7); delete[] p becomes swdb_alloc_delete_array_<t>(p), likewise.",
    "An OpenMP directive becomes a comment line `/* omp <directive> (one thread) */` before its statement.",
    "A call to a summarized function keeps its (template-instantiated) name and gets a prototype only.",
    "std::vector<T> becomes the struct std_vector_<t> {data, size, capacity} and std::pair<A, B> the struct "
    "std_pair_<a>_<b> {first, second} (<t> spelled as for templates); a modeled member m becomes a call of the model "
    "function <struct>_<m> of swdb.std_models (operator[] is operator_index, = is operator_assign; constructors ctor, "
    "ctor_default, ctor_count, ctor_count_value, copy_ctor, move_ctor; the destructor dtor, called at scope end).",
    "A vector iterator becomes a pointer T *; a range-for over a vector becomes a block declaring clang's __rangeN, "
    "__beginN and __endN, then `for (; __beginN != __endN; ++__beginN)` with the loop variable first in its body.",
    "A return out of a scope that destroys objects stores its value in swdb_return, runs the destructors (innermost "
    "first), then returns it.",
)
RULES_SHA256 = hashlib.sha256("\n".join((NAMING_RULES, *RULES)).encode()).hexdigest()
OPERATOR_NAMES = {"[]": "index", "()": "call", "==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge",
                  "+": "add", "-": "sub", "*": "mul", "/": "div", "%": "mod", "&": "and", "|": "or", "^": "xor",
                  "<<": "shl", ">>": "shr", "=": "assign", "+=": "add_assign", "-=": "sub_assign",
                  "*=": "mul_assign", "/=": "div_assign", "%=": "mod_assign", "&=": "and_assign",
                  "|=": "or_assign", "^=": "xor_assign", "<<=": "shl_assign", ">>=": "shr_assign", "++": "inc",
                  "--": "dec", "!": "not", "~": "compl", "&&": "land", "||": "lor"}
REQUIRED_CLANG = "22.1.8"
STD = "c++17"
ANCHOR = "/* swdb-anchor {} */"
ANCHOR_LINE = re.compile(r"^\s*/\* swdb-anchor (\S+) \*/$")
HEADERS = ("#include <stdbool.h>", "#include <stddef.h>", "#include <stdint.h>")
TIMEOUT_SECONDS = 120
SUMMARY_PREFIXES = ("__dxc_", "maa_")    # calls that always need a summary (map 16 item 6)
_FOUND = {}

INTEGER_TYPES = {"bool", "char", "signed char", "unsigned char", "short", "unsigned short", "int", "unsigned int",
                 "long", "unsigned long", "long long", "unsigned long long", "size_t", "ptrdiff_t", "intptr_t",
                 "uintptr_t", "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
                 "short int", "unsigned short int", "long int", "unsigned long int", "long long int",
                 "unsigned long long int", "signed", "unsigned", "signed int"}
INTERNAL_TYPES = {"__size_t": "size_t", "__ptrdiff_t": "ptrdiff_t"}
FLOAT_TYPES = {"float", "double"}    # printed as C float/double; WP reads them under the method version's float model
UNSIGNED_OF = {"char": "unsigned char", "signed char": "unsigned char", "short": "unsigned short", "int": "unsigned int",
               "long": "unsigned long", "long long": "unsigned long long", "int8_t": "uint8_t", "int16_t": "uint16_t",
               "int32_t": "uint32_t", "int64_t": "uint64_t", "ptrdiff_t": "size_t", "intptr_t": "uintptr_t"}
SUFFIX = {"int": "", "unsigned int": "U", "long": "L", "unsigned long": "UL", "long long": "LL",
          "unsigned long long": "ULL"}
PASS_CASTS = {"LValueToRValue", "ArrayToPointerDecay", "FunctionToPointerDecay", "NoOp", "IntegralCast",
              "IntegralToBoolean", "PointerToBoolean", "BitCast", "FloatingCast", "IntegralToFloating",
              "FloatingToIntegral", "FloatingToBoolean"}      # C converts implicitly exactly as C++ does
EXPLICIT_CASTS = {"CStyleCastExpr", "CXXStaticCastExpr", "CXXFunctionalCastExpr", "CXXReinterpretCastExpr"}
LOOPS = {"ForStmt", "WhileStmt", "DoStmt"}
C_ONLY_KEYWORDS = {"restrict", "_Bool", "_Complex", "_Imaginary", "_Alignas", "_Alignof", "_Atomic", "_Generic",
                   "_Noreturn", "_Static_assert", "_Thread_local"}
STD_MODELS = {"min", "max", "swap", "copy"}
OMP_DIRECTIVES = {"OMPParallelDirective": "parallel", "OMPForDirective": "for",
                  "OMPParallelForDirective": "parallel for", "OMPCriticalDirective": "critical",
                  "OMPAtomicDirective": "atomic", "OMPBarrierDirective": "barrier"}
OMP_REDUCTION_OPS = {"+": ("+=", "-="), "-": ("+=", "-="), "*": ("*=",), "&": ("&=",), "|": ("|=",), "^": ("^=",)}
OMP_RUNTIME = {"omp_get_thread_num": 0, "omp_get_num_threads": 1, "omp_get_max_threads": 1, "omp_in_parallel": 0}
ATOMIC_OPS = {"load_n", "store_n", "exchange_n", "compare_exchange_n", "fetch_add", "fetch_sub", "fetch_and",
              "fetch_or", "fetch_xor", "add_fetch", "sub_fetch", "and_fetch", "or_fetch", "xor_fetch"}
SYNC_OPS = {"bool_compare_and_swap", "val_compare_and_swap", "fetch_and_add", "fetch_and_sub", "fetch_and_and",
            "fetch_and_or", "fetch_and_xor", "add_and_fetch", "sub_and_fetch", "and_and_fetch", "or_and_fetch",
            "xor_and_fetch"}
_ARITH = {"add": "+", "sub": "-", "and": "&", "or": "|", "xor": "^"}
UNSUPPORTED_KINDS = {
    "CXXMemberCallExpr": "member function call", "LambdaExpr": "lambda", "CXXThrowExpr": "exception (throw)",
    "CXXTryStmt": "exception (try)", "CXXCatchStmt": "exception (catch)", "CXXTypeidExpr": "RTTI (typeid)",
    "CXXDynamicCastExpr": "RTTI (dynamic_cast)", "CXXConstCastExpr": "const_cast",
    "StringLiteral": "string literal", "FloatingLiteral": "floating-point literal (not float or double; "
    "long double is outside the subset)", "CXXForRangeStmt": "range-based for", "SwitchStmt": "switch", "GotoStmt": "goto",
    "CXXTemporaryObjectExpr": "temporary object of a class", "CXXBindTemporaryExpr": "temporary with a destructor",
    "CoroutineBodyStmt": "coroutine", "CXXNoexceptExpr": "noexcept operator", "CXXPseudoDestructorExpr":
    "pseudo-destructor call", "UserDefinedLiteral": "user-defined literal", "CXXFoldExpr": "fold expression",
    "CXXStdInitializerListExpr": "std::initializer_list"}
STD_CONTAINERS = {"map", "multimap", "set", "multiset", "unordered_map", "unordered_set", "unordered_multimap",
                  "unordered_multiset", "list", "forward_list", "deque", "array", "tuple", "string",
                  "basic_string", "queue", "stack", "priority_queue", "bitset", "span", "optional", "variant"}
STD_STREAMS = {"basic_ostream", "basic_istream", "basic_iostream", "basic_ostringstream", "basic_istringstream",
               "basic_stringstream", "basic_ofstream", "basic_ifstream", "basic_fstream", "ostream", "istream",
               "iostream", "ostringstream", "istringstream", "stringstream", "ofstream", "ifstream", "fstream"}
STD_MODELED = {"vector", "pair"}       # ticket 25: modeled types (swdb.std_models), never lowered from libc++


class LoweringError(Exception):
    """The proof unit has no C lowering."""


class Unsupported(LoweringError):
    """A construct outside the subset (failure class unsupported_construct)."""

    def __init__(self, construct, line=None):
        self.construct, self.line = construct, line
        where = "" if not line else (f" (line {line})" if isinstance(line, int) else f" ({line})")
        super().__init__(f"unsupported construct: {construct}{where}")


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
    declaration: str            # the C headers, types and globals plus the unit function's prototype (formal halves)
    parameters: tuple           # (name, C type, is_pointer) of the unit function
    source_sha256: str
    defines: tuple = ()
    tool: dict = field(default_factory=dict)
    summaries: tuple = ()       # ({name, c_name, summary}) per summarized function the C calls (prototype only)
    models: tuple = ()          # C model functions the C defines (std::*, __atomic_*, __sync_*, OpenMP runtime)
    probes: tuple = ()          # ticket 27: hazard probes {id, function, access, line, begin, end (C++ byte offsets)}
    std_models: tuple = ()      # ticket 25: the modeled std types the C uses (struct names, e.g. std_vector_int)
    allocation: bool = False    # ticket 25: the C allocates (new[] or a std model): "allocation succeeds" applies
    cpu_effects: dict = field(default_factory=dict)  # source/model memory effects and sequenced call sites
    bounded_initialization: dict = field(default_factory=dict)
    pointer_bounds: dict = field(default_factory=dict)
    terminal_release: dict | None = None  # checked ownership certificate; native lowering retains delete[]
    stdlib_provenance: dict = field(default_factory=dict)  # original full-TU declarations and header closure
    stdlib_substitutions: tuple = ()  # printer-requested free std calls, independently bound in the original TU
    vector_reallocation_candidate: dict = field(default_factory=dict)  # pending obligations; grants no origin

    @property
    def sha256(self):
        return hashlib.sha256(self.text.encode()).hexdigest()

    @property
    def anchors_json(self):
        data = {"tool": self.tool, "function": self.function, "c_lowering_sha256": self.sha256,
                "anchors": list(self.anchors)}
        if self.summaries:
            data["summaries"] = list(self.summaries)
        if self.models:
            data["models"] = list(self.models)
        if self.std_models:
            data["std_models"] = {**std_models.identity(), "types": list(self.std_models)}
        if self.allocation:
            data["allocation"] = True
        data["cpu_effects"] = self.cpu_effects
        data["bounded_initialization"] = self.bounded_initialization
        data["pointer_bounds"] = self.pointer_bounds
        if self.terminal_release:
            data["terminal_release"] = self.terminal_release
        if self.stdlib_provenance:
            data["stdlib_provenance"] = self.stdlib_provenance
            data["stdlib_substitutions"] = list(self.stdlib_substitutions)
        if self.vector_reallocation_candidate:
            data["vector_reallocation_candidate"] = self.vector_reallocation_candidate
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
    """Pin lowering, ownership/effects checkers, CPU admission policy, naming rules and clang."""
    tool = locate()
    here = Path(__file__)
    admission = here.with_name("cpu_memory_admission.py")
    policy = admission.read_bytes() if admission.exists() else b"cpu-memory-admission:absent"
    digest = hashlib.sha256(here.read_bytes() + Path(terminal_release.__file__).read_bytes()
                            + Path(cpu_effects.__file__).read_bytes() + policy
                            + bounded_initialization.identity()["sha256"].encode()
                            + wp_pointer_bounds.identity()["sha256"].encode()
                            + here.with_name("array_domains.py").read_bytes()
                            + here.with_name("vector_ownership.py").read_bytes()
                            + here.with_name("vector_reallocation_model.py").read_bytes()
                            + here.with_name("vector_reallocation_calls.py").read_bytes()
                            + here.with_name("vector_reallocation_vcs.py").read_bytes()
                            + here.with_name("vector_reallocation_caller_vcs.py").read_bytes()
                            + here.with_name("heap_reallocation.mlw").read_bytes()
                            + here.with_name("vector_pipeline.py").read_bytes()
                            + here.with_name("model_domains.py").read_bytes()
                            + here.with_name("standard_model_view.py").read_bytes()
                            + here.with_name("helper_windows.py").read_bytes()
                            + here.with_name("nested_entry_reads.py").read_bytes()
                            + here.with_name("dx_array_domains.py").read_bytes()
                            + here.with_name("standard_range_calls.py").read_bytes()
                            + here.with_name("member_windows.py").read_bytes()
                            + here.with_name("stdlib_source_admission.py").read_bytes()
                            + here.with_name("dx100_source_selector.py").read_bytes()
                            + json.dumps(stdlib_provenance.runtime_identity(tool), sort_keys=True).encode()).hexdigest()
    found = {"c_lowering": {"id": f"{TOOL_ID}-{TOOL_VERSION}", "sha256": digest},
             "naming_rules": naming_rules()}
    if not tool.missing:
        found["clang"] = {"id": f"clang-{tool.version}", "sha256": _file_sha256(_binary(tool.command[0]))}
    return found


def naming_rules():
    """{id, sha256} of the naming rules: the pin a proof record's content-hash set carries (map 16 item 3)."""
    return {"id": NAMING_RULES, "sha256": RULES_SHA256}


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
    """Every top-level declaration clang's filtered dump prints for `name` (a list of JSON nodes), each node's
    location resolved (`_file`, `_line` on every location object; clang prints file and line only on change)."""
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
        _resolve_locations(node, {"file": str(source), "line": None})
        found.append(node)


def _named(nodes, name, kinds):
    """Top-level dump nodes of kind in `kinds` named `name` (kept for ticket 22's cbmc_adapter._cut)."""
    return [n for n in nodes if n.get("name") == name and n.get("kind") in kinds and not n.get("isImplicit")]


def _resolve_locations(node, state):
    stack = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if "offset" in item:
                if "file" in item:
                    state["file"] = item["file"]
                if "line" in item:
                    state["line"] = item["line"]
                item["_file"], item["_line"] = state["file"], state["line"]
            stack.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            stack.extend(reversed(item))


def _where(node):
    """`<file name> line N` of a node (expansion location for a macro), or None."""
    loc = node.get("loc") or {}
    if not loc.get("_line"):
        loc = (node.get("range") or {}).get("begin") or {}
    if "expansionLoc" in loc:
        loc = loc["expansionLoc"]
    if not loc.get("_line"):
        return None
    return f"{Path(loc['_file']).name} line {loc['_line']}"


def _qual(node):
    return (node.get("type") or {}).get("qualType", "")


def _types(node):
    found = node.get("type") or {}
    return found.get("qualType", ""), found.get("desugaredQualType")


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict)]


# 2026-10-15 ET: these attributes affect diagnostics or inlining only. All other
# declaration attributes need an explicit model; in particular CleanupAttr invokes
# a callback at scope exit and cannot be discarded with an initializer's siblings.
BENIGN_DECLARATION_ATTRIBUTES = frozenset({
    "UnusedAttr", "DeprecatedAttr", "WarnUnusedResultAttr", "AlwaysInlineAttr", "NoInlineAttr",
})


def _declaration_attributes(node, line):
    for child in _children(node):
        kind = child.get("kind", "")
        if kind.endswith("Attr") and kind not in BENIGN_DECLARATION_ATTRIBUTES:
            raise Unsupported(f"declaration attribute {kind} on {node.get('name') or node.get('kind')}", line)


def _function_attributes(node, line):
    _declaration_attributes(node, line)
    for param in _children(node):
        if param.get("kind") == "ParmVarDecl":
            _declaration_attributes(param, _where(param) or line)


def _has_body(node):
    return any(c.get("kind") == "CompoundStmt" for c in _children(node))


def _strip(node):
    """The node under no-op wrappers (implicit casts that change nothing, parentheses, cleanups)."""
    while node.get("kind") in ("ImplicitCastExpr", "ParenExpr", "ExprWithCleanups", "ConstantExpr",
                               "SubstNonTypeTemplateParmExpr") and \
            (node.get("kind") != "ImplicitCastExpr" or node.get("castKind") in ("NoOp", "LValueToRValue")):
        node = _operand(node)
    return node


def _operand(node):
    """The expression a wrapper holds (a substituted template parameter also lists its parameter declaration)."""
    return [c for c in _children(node) if not c.get("kind", "").endswith("Decl")][-1]


def _is_std(node):
    mangled = node.get("mangledName", "")
    return mangled.startswith(("_ZNSt", "__ZNSt", "_ZSt", "__ZSt"))


# --- C++ types -------------------------------------------------------------------------------------

def _split_top(text, sep=","):
    """Split at `sep` outside <>, () and []."""
    parts, depth, start = [], 0, 0
    for at, char in enumerate(text):
        if char in "<([":
            depth += 1
        elif char in ">)]":
            depth -= 1
        elif char == sep and depth == 0:
            parts.append(text[start:at].strip())
            start = at + 1
    parts.append(text[start:].strip())
    return [p for p in parts if p]


def _type_tokens(text):
    """Top-level tokens of a C++ type: words (template ids kept whole), `*`, `&`, `&&`, `[N]`, parentheses."""
    tokens, at = [], 0
    while at < len(text):
        char = text[at]
        if char.isspace():
            at += 1
        elif text.startswith("&&", at):
            tokens.append("&&")
            at += 2
        elif char in "*&()":
            tokens.append(char)
            at += 1
        elif char == "[":
            end = text.index("]", at)
            tokens.append(text[at:end + 1])
            at = end + 1
        else:
            match = re.match(r"[A-Za-z_][\w:]*|-?\d+|\.\.\.", text[at:])
            if not match:
                tokens.append(char)
                at += 1
                continue
            word, at = match.group(0), at + len(match.group(0))
            while at < len(text) and text[at] == "<":                 # a template id: keep <...> with the word
                depth, end = 0, at
                while end < len(text):
                    depth += {"<": 1, ">": -1}.get(text[end], 0)
                    if depth == 0:
                        break
                    end += 1
                word, at = word + text[at:end + 1], end + 1
                while at < len(text) and text.startswith("::", at):  # Outer<T>::Inner
                    match = re.match(r"::[A-Za-z_]\w*", text[at:])
                    word, at = word + match.group(0), at + len(match.group(0))
            tokens.append(word)
    return tokens


@dataclass
class _CppType:
    base: str            # "unsigned long", "pvector", "std::map"
    args: tuple          # template arguments (raw text) or ()
    cv: tuple            # qualifiers of the base
    pointers: list       # qualifiers per `*`, innermost first
    ref: str             # "", "&" or "&&"
    dims: str            # "[8][2]"


def _parse_type(text, line):
    text = re.sub(r"\b(struct|class|union|typename)\s+", "", text.strip())
    if "(lambda at" in text:
        raise Unsupported("lambda", line)
    if "(unnamed " in text or "(anonymous " in text:
        raise Unsupported("unnamed type (a struct, union or enum with no name)", line)
    if "(" in text:
        raise Unsupported(f"type {text} (function or member pointer types are outside the subset)", line)
    tokens = _type_tokens(text)
    dims = ""
    while tokens and tokens[-1].startswith("["):
        dims = tokens.pop() + dims
    ref = ""
    if tokens and tokens[-1] in ("&", "&&"):
        ref = tokens.pop()
    star = tokens.index("*") if "*" in tokens else len(tokens)
    head, tail = tokens[:star], tokens[star:]
    cv = tuple(t for t in head if t in ("const", "volatile"))
    words = [t for t in head if t not in ("const", "volatile", "enum")]
    pointers = []
    for token in tail:
        if token == "*":
            pointers.append([])
        elif token in ("const", "volatile", "__restrict", "__restrict__", "restrict") and pointers:
            token = "restrict" if "restrict" in token else token          # C99 restrict, as C++'s __restrict
            pointers[-1].append(token)
        else:
            raise Unsupported(f"type {text}", line)
    if not words or any(t in ("&", "&&", "...") for t in words):
        raise Unsupported(f"type {text}", line)
    base, args = " ".join(words), ()
    if "<" in base:
        if len(words) != 1 or not base.endswith(">"):
            raise Unsupported(f"type {text}", line)
        base, inside = base.split("<", 1)
        args = tuple(_split_top(inside[:-1]))
    return _CppType(base, args, cv, [tuple(p) for p in pointers], ref, dims)


def _c_known(base):
    plain = re.sub(r"^std::", "", base)
    return plain in INTEGER_TYPES or plain in INTERNAL_TYPES or plain in FLOAT_TYPES or plain == "void"


def _std_name(base):
    return re.sub(r"^std::(__\w+::)?", "", base) if base.startswith("std::") else None


def _mangle_text(ctext):
    text = re.sub(r"\s*\*", " ptr", ctext.strip())
    text = re.sub(r"\s+", "_", text)
    return text.replace("-", "m")


def _return_and_params(function_type, line):
    """(return type, [parameter types], variadic) of a function type `R (P1, P2) const noexcept(...)`."""
    depth, start = 0, None
    for at, char in enumerate(function_type):
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        elif char == "(" and depth == 0:
            start = at
            break
    if start is None:
        raise Unsupported(f"function type {function_type}", line)
    depth = 0
    for end in range(start, len(function_type)):
        depth += {"(": 1, ")": -1}.get(function_type[end], 0)
        if depth == 0:
            break
    params = _split_top(function_type[start + 1:end])
    variadic = bool(params) and params[-1] == "..."
    params = [p for p in params if p not in ("void", "...")]
    return function_type[:start].strip(), params, variadic


# --- the translation unit -------------------------------------------------------------------------

class _Unit:
    """One lowering: clang dumps by name, the structs, functions, globals, models and summaries the C needs."""

    def __init__(self, tool, source, includes, defines, summaries, semantics=None):
        self.tool, self.source, self.includes, self.defines = tool, source, tuple(includes), defines
        self.source_digest = _file_sha256(source)
        self.summaries = dict(summaries or {})
        self.semantics = dict(semantics or {})      # ticket 27: {tile_pointer: names}; probes at tile accesses
        self.probes = []
        self.probe_nodes = set()
        self.pointer_sites = []
        self.pointer_nodes = set()
        self.pointer_calls = []
        self.standard_range_calls = []
        self.stdlib_substitutions = []
        self._dumps = {}
        self.structs, self.struct_order, self.classes = {}, [], {}
        self.functions, self.order, self.pending = {}, [], []
        self.prototypes_only = {}
        self.globals, self.global_text, self.global_nodes = [], {}, {}
        self.models, self.model_order = {}, []
        self.summaries_used = []
        self.names = {}
        self.needs_stdlib = False
        self._cache = {}
        self._pragma_text = {}
        self.std_types = {}          # ticket 25: struct name -> {kind, cpp, element(s), members}
        self.allocates = False       # ticket 25: new[] seen

    # dumps
    def dump(self, name):
        if name not in self._dumps:
            self._dumps[name] = _dump(self.tool, self.source, name, self.includes, self.defines)
        return self._dumps[name]

    def claim(self, cname, key, line):
        """Reserve a C name for one C++ entity (a name collision is outside the subset, never a silent merge)."""
        _name(cname, line)
        known = self.names.setdefault(cname, key)
        if known != key:
            raise Unsupported(f"two C++ entities lower to the same C name {cname}", line)
        return cname

    # types
    def ctype(self, qual, desugared=None, name="", line=None):
        """The C declarator of a C++ type (with `name`, or abstract when name is empty)."""
        try:
            parsed = _parse_type(qual, line)
        except Unsupported:
            if not desugared:                     # ticket 25: `std::vector<int>::iterator` reads through its sugar
                raise
            parsed = _parse_type(desugared, line)
        # A spelling such as uint64_t is an ordinary C++ typedef and may be
        # shadowed. The source-node type is authoritative even when its name
        # also occurs in the C prelude's fixed-width vocabulary.
        if desugared:
            parsed = _parse_type(desugared, line)
        if parsed.ref and not qual.rstrip().endswith('&'):
            raise Unsupported('reference typedef needs an explicit source reference binding', line)
        return self._declarator(parsed, name, line, qual)

    def _declarator(self, parsed, name, line, shown):
        if parsed.ref == "&&":
            raise Unsupported(f"rvalue reference type {shown}", line)
        base = self.base_type(parsed.base, parsed.args, line, shown)
        if parsed.dims and not name:
            raise Unsupported(f"array type {shown} outside a declaration", line)
        if base == "void" and not parsed.pointers and name:
            raise Unsupported(f"type {shown}", line)
        head = " ".join([*parsed.cv, base])
        stars = "".join("*" + "".join(f"{q} " for q in quals) for quals in parsed.pointers)
        if parsed.ref:
            stars += "*"
        if not name:
            return f"{head} {stars}".rstrip() if stars else head
        return f"{head} {stars}{name}{parsed.dims}"

    def base_type(self, base, args, line, shown=""):
        plain = re.sub(r"^std::", "", base)
        if not args and plain in (INTEGER_TYPES | set(INTERNAL_TYPES)) and '_' in plain:
            # Function types do not always carry desugaredQualType. Resolve
            # their typedef from the source, refusing shadowed contexts rather
            # than substituting the C prelude's unrelated same-spelled alias.
            nodes = [n for n in self.dump(plain) if n.get('name') == plain and not n.get('isImplicit')]
            target = self.typedef_target(nodes, base, line)
            parsed = _parse_type(target, line)
            if (parsed.base == plain or parsed.args or parsed.pointers or parsed.ref or parsed.dims
                    or not _c_known(parsed.base)):
                raise Unsupported(f'nonprimitive source typedef identity for {base}', line)
            return self.ctype(target, line=line)
        if not args and (plain in INTEGER_TYPES or base == "void"):
            return plain
        if not args and plain in INTERNAL_TYPES:
            return INTERNAL_TYPES[plain]
        if not args and plain in FLOAT_TYPES:
            return plain
        if plain == "long double":
            raise Unsupported(f"floating-point type {shown or base} (long double; float and double are in the subset)",
                              line)
        std = _std_name(base)
        if std in STD_MODELED or std == "__wrap_iter":         # ticket 25
            return self.std_type(std, args, line, shown or base)
        if std is not None:
            if std in STD_STREAMS:
                raise Unsupported(f"stream std::{std}", line)
            if std in STD_CONTAINERS:
                raise Unsupported(f"standard container std::{std} (only std::vector and std::pair are modeled)", line)
            raise Unsupported(f"standard library type std::{std}", line)
        if base.startswith("(") or "unnamed" in base or "anonymous" in base:
            raise Unsupported(f"unnamed type {base}", line)
        if "::" in base:
            raise Unsupported(f"type {base} inside a namespace or class", line)
        return self.named_type(base, args, line)

    def named_type(self, base, args, line):
        nodes = [n for n in self.dump(base) if n.get("name") == base and not n.get("isImplicit")]
        kinds = {n.get("kind") for n in nodes}
        if "EnumDecl" in kinds:
            enums = [n for n in nodes if n.get("kind") == "EnumDecl"]
            if len(enums) != 1 or kinds != {"EnumDecl"}:
                raise Unsupported(f"ambiguous enum type {base}", line)
            enum = enums[0]
            fixed = (enum.get("fixedUnderlyingType") or {})
            return self.ctype(fixed.get("qualType", "int"), fixed.get("desugaredQualType"), line=line) \
                if fixed else "int"
        if kinds & {"TypedefDecl", "TypeAliasDecl"} and not args:
            return self.ctype(self.typedef_target(nodes, base, line), line=line)
        return self.struct(base, args, line)

    def typedef_target(self, nodes, name, line):
        """A type spelling with no node-local binding needs a unique target.

        Filtered dumps can contain unrelated class/local/namespace aliases.
        Equal underlying targets are harmless; different targets or mixed
        declaration kinds must not choose the first result's type.
        """
        aliases = [n for n in nodes if n.get('kind') in {'TypedefDecl', 'TypeAliasDecl'}]
        targets = {desugared or qual for qual, desugared in map(_types, aliases)}
        if not aliases or len(aliases) != len(nodes) or len(targets) != 1:
            raise Unsupported(f'ambiguous source typedef identity for {name}', line)
        target = next(iter(targets))
        if _parse_type(target, line).ref:
            raise Unsupported('reference typedef needs an explicit source reference binding', line)
        return target

    def canonical(self, arg, line, desugared=None):
        """A template argument in one spelling: an integer, true/false, or a C type with every typedef resolved
        (so pvector<int32_t> and pvector<int> are one struct, as in C++)."""
        arg = arg.strip()
        if re.fullmatch(r"-?\d+[uUlL]*", arg):
            return re.sub(r"[uUlL]+$", "", arg)
        if arg in ("true", "false"):
            return arg
        text = self.ctype(arg, desugared, line=line)
        return re.sub(r"[A-Za-z_]\w*", lambda m: self._builtin(m.group(0), line), text)

    def _builtin(self, word, line):
        if word in ("bool", "char", "short", "int", "long", "signed", "unsigned", "void", "const", "volatile") or \
                word not in INTEGER_TYPES | set(INTERNAL_TYPES.values()):
            return word
        key = ("typedef", word)
        if key not in self._cache:
            nodes = [n for n in self.dump(word) if n.get('name') == word and not n.get('isImplicit')]
            target = self.typedef_target(nodes, word, line)
            if not re.fullmatch(r"[a-z ]+", target):
                target = re.sub(r"[A-Za-z_]\w*", lambda m: self._builtin(m.group(0), line), target)
            self._cache[key] = target
        return self._cache[key]

    def mangle(self, args, line):
        return "_".join(_mangle_text(self.canonical(a, line)) for a in args)

    def struct(self, base, args, line):
        """The C struct name of class `base<args>`; defines it (and the types of its fields) on first use."""
        key = (base, tuple(self.canonical(a, line) for a in args))
        if key in self.structs:
            return self.structs[key]
        node = self._class_node(base, key[1], line)
        full = (base, self._spec_args(node, line)) if args else key   # clang prints no defaulted arguments
        if full in self.structs:
            self.structs[key] = self.structs[full]
            return self.structs[full]
        cname = base if not args else f"{base}_{'_'.join(_mangle_text(a) for a in full[1])}"
        self.claim(cname, ("struct", full), line)
        self.structs[key] = self.structs[full] = cname
        self.classes[cname] = node
        where = _where(node) or line
        if node.get("bases"):
            raise Unsupported(f"inheritance (class {base} has a base class)", where)
        if node.get("tagUsed") == "union":
            raise Unsupported(f"union {base}", where)
        fields = []
        for child in _children(node):
            kind = child.get("kind")
            if kind == "CXXMethodDecl" and child.get("virtual"):
                raise Unsupported(f"virtual function {base}::{child.get('name')}", _where(child) or where)
            if kind == "CXXDestructorDecl" and child.get("virtual"):
                raise Unsupported(f"virtual destructor of {base}", _where(child) or where)
            if kind == "VarDecl":
                raise Unsupported(f"static data member {base}::{child.get('name')}", _where(child) or where)
            if kind == "FieldDecl":
                if child.get("isBitfield"):
                    raise Unsupported(f"bit-field {base}::{child.get('name')}", _where(child) or where)
                qual, desugared = _types(child)
                fields.append(self.ctype(qual, desugared, _name(child.get("name"), where), where) + ";")
        if not fields:
            raise Unsupported(f"class {base} with no fields (C has no empty struct)", where)
        self.struct_order.append((cname, fields))
        return cname

    def _class_node(self, base, cargs, line):
        found = []
        for node in self.dump(base):
            if node.get("name") != base or node.get("isImplicit"):
                continue
            if node.get("kind") == "CXXRecordDecl" and not cargs and node.get("completeDefinition"):
                found.append(node)
            elif node.get("kind") == "ClassTemplateDecl" and cargs:
                found += _with_params(node, [c for c in _children(node) if c.get("kind") == "ClassTemplateSpecializationDecl"])
            elif node.get("kind") == "ClassTemplateSpecializationDecl" \
                    and cargs:
                found.append(node)
        if cargs:
            found = [n for n in found if n.get("completeDefinition") and self._spec_args(n, line)[:len(cargs)] == cargs]
            exact = [n for n in found if len(self._spec_args(n, line)) == len(cargs)]
            found = exact or found                       # a longer argument list: the rest are defaulted arguments
        if not found:
            raise Unsupported(f"type {base}" + (f"<{', '.join(cargs)}>" if cargs else "") +
                              " (no complete class definition)", line)
        offsets = {(_where(n), json.dumps([c.get("name") for c in _children(n)])) for n in found}
        if len(offsets) > 1 and cargs:
            raise Unsupported(f"class template {base}<{', '.join(cargs)}> with defaulted arguments that match more "
                              "than one instantiation", line)
        if len(offsets) > 1:
            raise Unsupported(f"class {base} defined more than once", line)
        return found[0]

    def _spec_args(self, node, line):
        out, params = [], node.get("_param_types") or []
        for child in _children(node):
            if child.get("kind") != "TemplateArgument":
                continue
            kind = _qual(child) or (params[len(out)] if len(out) < len(params) else "")
            if "value" in child and kind == "bool":                  # clang prints a 1-bit true as -1
                out.append("false" if str(child["value"]).lower() in ("0", "false") else "true")
            elif "value" in child:
                out.append(self.canonical(str(child["value"]), line))
            elif child.get("type"):
                qual, desugared = _types(child)
                out.append(self.canonical(qual, line, desugared))
            else:
                raise Unsupported("template argument that is not a type or an integer", line)
        return tuple(out)

    def class_of(self, node, line, arrow=False):
        """(C struct name, class node) of the class an expression's type names (through `*` if arrow)."""
        qual, desugared = _types(node)
        parsed = _parse_type(desugared or qual, line)
        if arrow:
            if not parsed.pointers:
                raise Unsupported(f"member access through {qual}", line)
            parsed.pointers.pop()
        if parsed.pointers or parsed.dims:
            raise Unsupported(f"member access on {qual}", line)
        if _c_known(parsed.base) and not parsed.args:
            raise Unsupported(f"member access on {qual}", line)
        cname = self.base_type(parsed.base, parsed.args, line, qual)
        if cname not in self.classes:
            raise Unsupported(f"member access on {qual}", line)
        return cname, self.classes[cname]

    def field(self, cname, name, line):
        for child in _children(self.classes[cname]):
            if child.get("kind") == "FieldDecl" and child.get("name") == name:
                return child
        raise Unsupported(f"member {name} of {cname}", line)

    def methods(self, cname, name, kinds=("CXXMethodDecl",)):
        found = []
        for child in _children(self.classes[cname]):
            if child.get("kind") in kinds and child.get("name") == name:
                found.append(child)
            elif child.get("kind") == "FunctionTemplateDecl" and child.get("name") == name:
                found += _with_params(child, [c for c in _children(child) if c.get("kind") in kinds and _instantiated(c)])
        return found

    # enums
    def enum_value(self, ref, line):
        name, qual = ref.get("name"), (ref.get("type") or {}).get("qualType", "")
        key = (name, qual)
        enum_name = re.sub(r"^(enum\s+)", "", qual).strip()
        if enum_name.startswith("(") or "unnamed" in enum_name:
            nodes = [n for n in self.dump(name) if n.get("kind") == "EnumConstantDecl" and n.get("name") == name
                     and _qual(n) == qual]
            values = [_explicit_enum_value(n) for n in nodes]
            if len(values) != 1 or values[0] is None:
                raise Unsupported(f"enumerator {name} of an unnamed enum without an explicit value", line)
            self._cache[key] = values[0]
            return values[0]
        if "::" in enum_name:
            raise Unsupported(f"enumerator {name} of an enum inside a namespace or class", line)
        enums = [n for n in self.dump(enum_name) if n.get("kind") == "EnumDecl" and n.get("name") == enum_name]
        if not enums:
            raise Unsupported(f"enumerator {name} (no enum {enum_name})", line)
        if len(enums) != 1:
            raise Unsupported(f"enumerator {name} of ambiguous enum {enum_name}", line)
        if key in self._cache:
            return self._cache[key]
        value = -1
        for constant in [c for c in _children(enums[0]) if c.get("kind") == "EnumConstantDecl"]:
            explicit = _explicit_enum_value(constant)
            value = explicit if explicit is not None else value + 1
            self._cache[(constant.get("name"), qual)] = value
        if key not in self._cache:
            raise Unsupported(f"enumerator {name}", line)
        return self._cache[key]

    # functions
    def function_node(self, name, qual_type, line, unit=False):
        """The one definition (or declaration, for a summary) of free function `name` of type `qual_type`."""
        candidates, methods = [], []
        for node in self.dump(name):
            if node.get("name") != name or node.get("isImplicit"):
                continue
            if node.get("kind") == "FunctionDecl":
                candidates.append(node)
            elif node.get("kind") == "FunctionTemplateDecl":
                candidates += _with_params(node, [c for c in _children(node) if c.get("kind") == "FunctionDecl" and _instantiated(c)])
            elif node.get("kind") in ("CXXMethodDecl", "CXXConstructorDecl", "CXXDestructorDecl"):
                methods.append(node)
        if qual_type is not None:
            candidates = [c for c in candidates if _qual(c) == qual_type]
        defined = [c for c in candidates if _has_body(c)]
        if unit and not defined:
            if methods:
                raise Unsupported(f"member function {name} as the proof unit (the unit is a free function)")
            if any(n.get("kind") == "FunctionTemplateDecl" for n in self.dump(name) if n.get("name") == name):
                raise Unsupported(f"function template {name} as the proof unit (instantiate it in a free function)")
            raise NotFound(f"{Path(self.source).name} defines no function {name}")
        distinct = {(c.get("mangledName"), _qual(c)) for c in defined}
        if len(distinct) > 1:
            raise Unsupported(f"overloaded function {name}", line)
        return defined[0] if defined else (candidates[0] if candidates else None)

    def call_declaration(self, name, qual_type, call, caller, line):
        """Resolve template calls through one TU, never filtered-dump IDs.

        Equal function types do not identify template specializations (for
        example get_data_type<int>() and get_data_type<double>()). Source spans
        and the enclosing stable mangled name locate the actual call; only then
        can its declaration ID be followed inside the SAME full-TU dump.
        """
        if not any(n.get("kind") == "FunctionTemplateDecl" and n.get("name") == name
                   for n in self.dump(name)):
            return self.function_node(name, qual_type, line)

        def span(node):
            points = [(node.get("range") or {}).get(k) or {} for k in ("begin", "end")]
            if any("offset" not in p or not p.get("_file", p.get("file")) or
                   "spellingLoc" in p or "expansionLoc" in p for p in points):
                raise Unsupported(f"template call {name} without direct unique source coordinates", line)
            return tuple((str(Path(p.get("_file", p.get("file"))).resolve()), p["offset"], p.get("tokLen", 0))
                         for p in points)

        if not caller or not caller.get("mangledName"):
            raise Unsupported(f"template call {name} without an enclosing source function", line)
        wanted = span(call)
        declarations, templates, owners = {}, {}, []

        def visit(part):
            if part.get("kind") in {"FunctionDecl", "CXXMethodDecl", "CXXConstructorDecl", "CXXDestructorDecl"}:
                declarations[part.get("id")] = part
                if part.get("mangledName") == caller["mangledName"] and _has_body(part):
                    owners.append(part)
            if part.get("kind") == "FunctionTemplateDecl":
                for child in _children(part):
                    if child.get("kind") == "FunctionDecl":
                        templates[child.get("id")] = part
            for child in _children(part):
                visit(child)

        for root in self.dump(""):
            visit(root)
        if len(owners) != 1:
            raise Unsupported(f"template call {name} has no unique enclosing full-TU function", line)
        references = []

        def calls(part):
            if part.get("kind") == "CallExpr":
                try:
                    same = span(part) == wanted
                except Unsupported:
                    same = False
                if same:
                    callee = _children(part)[0]
                    while callee.get("kind") in {"ImplicitCastExpr", "ParenExpr"} and len(_children(callee)) == 1:
                        callee = _children(callee)[0]
                    ref = callee.get("referencedDecl") or {}
                    if callee.get("kind") == "DeclRefExpr" and ref.get("name") == name and _qual(ref) == qual_type:
                        references.append(ref)
            for child in _children(part):
                calls(child)

        calls(owners[0])
        target = declarations.get(references[0].get("id")) if len(references) == 1 else None
        if not target or target.get("name") != name or _qual(target) != qual_type:
            raise Unsupported(f"template call {name} has no unique full-TU specialization binding", line)
        parent = templates.get(target.get("id"))
        return _with_params(parent, [target])[0] if parent else target

    def lower_function(self, node, cname, owner=None, line=None):
        """Queue a function (or member function of struct `owner`) for lowering; returns its C name."""
        key = ("function", owner, node.get("mangledName") or node.get("name"), _qual(node))
        self.claim(cname, key, line)
        if cname not in self.functions:
            self.functions[cname] = None
            self.pending.append((cname, node, owner))
        return cname

    def summary(self, name, cname, qual_type, line, names=()):
        """A summarized call: a prototype from the call's function type (parameter names from its declaration,
        which the summary's formal halves name), recorded once."""
        self.claim(cname, ("summary", name, qual_type), line)
        if cname not in self.prototypes_only:
            returns, params, variadic = _return_and_params(qual_type, line)
            if variadic:
                raise Unsupported(f"variadic function {name}", line)
            names = [n if n and re.fullmatch(r"[A-Za-z_]\w*", n) and n not in C_ONLY_KEYWORDS else
                     f"swdb_unnamed_{i + 1}" for i, n in enumerate(list(names) + [None] * (len(params) - len(names)))]
            texts = [self.ctype(p, name=names[i], line=line) for i, p in enumerate(params)]
            self.prototypes_only[cname] = f"{_join(self.ctype(returns, line=line), cname)}({', '.join(texts) or 'void'})"
            self.summaries_used.append({"name": name, "c_name": cname, "summary": self.summaries[name]})
        return cname

    def summary_c_name(self, name, declaration, line):
        """Keep template overloads with different arities at distinct C ABIs.

        Inspect the whole source family, rather than whichever call appeared
        first. A single-arity family retains its existing emitted bytes. Same
        arity/type collisions still fail through claim; no overload is guessed.
        """
        if declaration is None or not _children_kind(declaration, "TemplateArgument"):
            return name
        cname = f"{name}_{'_'.join(_mangle_text(a) for a in self._spec_args(declaration, line))}"
        arities = {sum(child.get("kind") == "ParmVarDecl" for child in _children(function))
                   for template in self.dump(name)
                   if template.get("kind") == "FunctionTemplateDecl" and template.get("name") == name
                   for function in _children(template) if function.get("kind") == "FunctionDecl"}
        if len(arities) > 1:
            cname += f"_args{sum(child.get('kind') == 'ParmVarDecl' for child in _children(declaration))}"
        return cname

    def model(self, cname, text, line):
        self.claim(cname, ("model", text), line)
        if cname not in self.models:
            self.models[cname] = text
            self.model_order.append(cname)
        return cname

    def pragma(self, node, line):
        """The `#pragma omp ...` source text of an OpenMP directive (clang's JSON dump omits clause kinds)."""
        begin = (node.get("range") or {}).get("begin") or {}
        if "expansionLoc" in begin:
            begin = begin["expansionLoc"]
        path, offset = begin.get("_file"), begin.get("offset")
        if not path or offset is None:
            raise Unsupported("OpenMP directive whose pragma text cannot be read", line)
        if path not in self._pragma_text:
            try:
                self._pragma_text[path] = Path(path).read_bytes()
            except OSError:
                raise Unsupported("OpenMP directive whose pragma text cannot be read", line) from None
        data = self._pragma_text[path]
        end = offset
        while end < len(data) and (data[end:end + 1] != b"\n" or data[end - 1:end] == b"\\"):
            end += 1
        text = data[offset:end].decode(errors="replace").replace("\\\n", " ")
        return re.sub(r"\s+", " ", text).strip()

    # ticket 25: std::vector<T> and std::pair<A, B> as models (swdb.std_models)
    def std_type(self, std, args, line, shown):
        """The C type of a modeled std type: the struct of std::vector<T> or std::pair<A, B>, or `T *` for a vector
        iterator (libc++'s __wrap_iter<T *>)."""
        if std == "__wrap_iter":
            if len(args) != 1:
                raise Unsupported(f"iterator type {shown}", line)
            pointer = self.canonical(args[0], line)
            if not pointer.endswith("*"):
                raise Unsupported(f"iterator type {shown}", line)
            return pointer
        if std == "vector":
            # An unrelated global allocator<T> may have observable effects. Only
            # a qualified std allocator is eligible; the full-TU checker then
            # binds that namespace's declarations to the canonical library.
            if not args or len(args) > 2 or (len(args) == 2 and not re.match(r"std::(?:__\w+::)?allocator<", args[1])):
                raise Unsupported(f"std::vector with an allocator other than std::allocator ({shown})", line)
            elements = (self._std_element(args[0], line, "std::vector"),)
            if elements[0] == "bool":
                raise Unsupported("std::vector<bool> (a packed specialization; not modeled)", line)
        else:
            if len(args) != 2:
                raise Unsupported(f"std::pair type {shown}", line)
            elements = tuple(self._std_element(a, line, "std::pair") for a in args)
        cname = f"std_{std}_{'_'.join(_mangle_text(e) for e in elements)}"
        if cname not in self.std_types:
            self.claim(cname, ("std_model", std, elements), line)
            cpp = f"std::{std}<{', '.join(elements)}>"
            self.std_types[cname] = {"kind": std, "cpp": cpp, "elements": elements}
            if std == "vector":
                fields = std_models.vector_struct_fields(elements[0])
            else:
                fields = [f"{_join(elements[0], 'first')};", f"{_join(elements[1], 'second')};"]
                self.classes[cname] = {"kind": "CXXRecordDecl", "name": cname, "inner": [
                    {"kind": "FieldDecl", "name": "first", "type": {"qualType": elements[0]}},
                    {"kind": "FieldDecl", "name": "second", "type": {"qualType": elements[1]}}]}
            self.struct_order.append((cname, fields))
        return cname

    def _std_element(self, arg, line, container):
        element = self.canonical(arg, line)
        plain = element.replace("const ", "").strip()
        if plain != element or not (plain in INTEGER_TYPES or plain in FLOAT_TYPES or plain.endswith("*")):
            raise Unsupported(f"{container} of {element} (model version {std_models.MODELS_VERSION} holds scalars and "
                              "pointers)", line)
        return element

    def model_of(self, qual, desugared, line, arrow=False):
        """(struct name, model info) when a type (through const, a reference, or one `*` if arrow) is a modeled std
        type, else None."""
        text = desugared or qual
        if "vector<" not in text and "pair<" not in text:
            return None
        parsed = _parse_type(text, line)
        if arrow:
            if not parsed.pointers:
                return None
            parsed.pointers.pop()
        if parsed.pointers or parsed.dims or _std_name(parsed.base) not in STD_MODELED:
            return None
        cname = self.base_type(parsed.base, parsed.args, line, qual)
        return cname, self.std_types[cname]

    def std_member(self, cname, member, line):
        """The C name of a modeled member's function; defines it (with its helpers) on first use."""
        info = self.std_types[cname]
        if info["kind"] == "vector":
            self.needs_stdlib = True
            self.model("SWDB_MODEL_FAIL", std_models.MACROS, line)
            self.model(f"{cname}_valid", std_models.vector_logic(cname, info["elements"][0]), line)
            for name, text in std_models.vector_member(cname, info["elements"][0], member):
                self.model(name, text, line)
        else:
            self.model(*std_models.pair_member(cname, *info["elements"], member), line)
        return f"{cname}_{member}"


def _with_params(template, instances):
    """Mark each instantiation with its template's parameter types (a bool argument prints as -1 or 0)."""
    params = [_qual(p) for p in _children(template) if p.get("kind", "").endswith("ParmDecl")]
    for instance in instances:
        instance["_param_types"] = params
    return instances


def _join(ctype, name):
    """`int *f` rather than `int * f`."""
    return f"{ctype}{name}" if ctype.endswith("*") else f"{ctype} {name}"


def _instantiated(node):
    """A FunctionDecl inside a FunctionTemplateDecl that is an instantiation (not the pattern)."""
    return any(c.get("kind") == "TemplateArgument" for c in _children(node)) or "TemplateInstantiationPattern" in node


def _explicit_enum_value(node):
    stack = list(_children(node))
    while stack:
        item = stack.pop(0)
        if item.get("kind") == "ConstantExpr" and "value" in item:
            return int(item["value"])
        stack.extend(_children(item))
    return None


# --- the printer ---------------------------------------------------------------------------------

class _Printer:
    def __init__(self, function, unit):
        self.function = function
        self.source_declaration = None
        self.unit = unit
        self.lines = []
        self.anchors = []
        self.line = None
        self.statements = 0
        self.loops = 0
        self.callees = []
        self.globals = []
        self.local_ids = set()
        self.ref_ids = set()        # locals and parameters of reference type (printed dereferenced)
        self.returns_ref = False
        self.scopes = []            # per open block: [(object, destructor C name)]
        self.calls = []             # C names of the lowered functions this one calls, in order of appearance
        self.omp_reductions = []
        self.semantics = unit.semantics if unit is not None else {}   # ticket 27: tile pointers get probes
        self.tile_vars = set()
        self.probes = []
        self._tile_ok = 0
        self.loop_bases = []        # ticket 25: len(scopes) at each enclosing loop (break/continue leave only those)
        self.returns_ctype = "void"
        self.pointer_contexts = []
        self.pointer_access_seen = set()
        self.pointer_seen = set()
        self.pointer_rendering = False

    # positions and anchors
    def _at(self, node):
        where = _where(node)
        if where:
            self.line = where

    def _lower(self, node, cname, owner, line):
        cname = self.unit.lower_function(node, cname, owner, line)
        if cname not in self.calls and cname != self.function:
            self.calls.append(cname)
        return cname

    def anchor(self, ident, kind, indent):
        self.lines.append("  " * indent + ANCHOR.format(ident))
        self.anchors.append({"id": ident, "kind": kind, "function": self.function, "line_in_function": len(self.lines)})

    def emit(self, text, indent):
        self.lines.append("  " * indent + text)

    # statements
    def body(self, node, indent):
        """A function or loop body: always braced; the caller wrote the opening line."""
        children = node.get("inner", []) if node.get("kind") == "CompoundStmt" else [node]
        self.scopes.append([])
        for child in children:
            self.statement(child, indent)
        for name, dtor in reversed(self.scopes.pop()):
            self.simple(f"{dtor}(&{name});", indent)

    def simple(self, text, indent):
        """One generated statement (a constructor, destructor or member-initializer step) with its anchors."""
        self.statements += 1
        sid = f"{self.function}.s{self.statements}"
        self.anchor(f"{sid}.before", "before", indent)
        self.emit(text, indent)
        self.anchor(f"{sid}.after", "after", indent)

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
        loop = kind in LOOPS or kind == "CXXForRangeStmt"
        if loop:
            self.loop_bases.append(len(self.scopes))
        self.pointer_contexts.append((node, f"{sid}.before"))
        try:
            self._statement(node, kind, indent)
        finally:
            self.pointer_contexts.pop()
        if loop:
            self.loop_bases.pop()
        self.anchor(f"{sid}.after", "after", indent)

    def _exits(self, what):
        base = self.loop_bases[-1] if what in ("break", "continue") and self.loop_bases else 0   # ticket 25
        if any(scope for scope in self.scopes[base:]):
            raise Unsupported(f"{what} out of a scope that destroys an object", self.line)

    def _statement(self, node, kind, indent):
        inner = node.get("inner", [])
        if kind == "DeclStmt":
            decls = _children(node)
            if all(d.get("kind") in ("StaticAssertDecl", "TypedefDecl", "TypeAliasDecl", "UsingDecl") for d in decls):
                what = "static_assert" if decls[0].get("kind") == "StaticAssertDecl" else "type alias"
                self.emit(f"/* {what} (checked by the C++ front end) */", indent)
                return
            texts, after = [], []
            for decl in decls:
                text, extra = self.local(decl)
                texts.append(text + ";")
                after += extra
            self.emit(" ".join(texts), indent)
            for line in after:
                self.emit(line, indent)
        elif kind == "ReturnStmt" and any(scope for scope in self.scopes):
            self._return_destroying(inner, indent)                             # ticket 25
        elif kind == "ReturnStmt":
            self._exits("return")
            if not inner:
                self.emit("return;", indent)
            elif self.returns_ref:
                self.emit(f"return {self.address(inner[0])};", indent)
            else:
                self.emit(f"return {self.expr(inner[0], top=True)};", indent)
        elif kind == "BreakStmt":
            self._exits("break")
            self.emit("break;", indent)
        elif kind == "ContinueStmt":
            self._exits("continue")
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
        elif kind == "CXXForRangeStmt":
            self._range_for(node, indent)                                      # ticket 25
        elif kind in OMP_DIRECTIVES:
            self.omp(node, kind, indent)
        elif kind and kind.endswith("Directive") and kind.startswith("OMP"):
            raise Unsupported(f"OpenMP directive {kind}", self.line)
        elif kind in UNSUPPORTED_KINDS and not (kind.endswith("Expr") or kind.endswith("Operator")):
            raise Unsupported(UNSUPPORTED_KINDS[kind], self.line)
        elif kind == "CXXDeleteExpr":
            self.emit(f"{self.delete(node)};", indent)
        elif kind and (kind.endswith("Expr") or kind.endswith("Operator") or kind == "ExprWithCleanups"):
            text = self.expr(node, top=True)
            if text.startswith(("(swdb_atomic_", "(swdb_sync_", "(std_min_", "(std_max_", "(omp_")) \
                    and text.endswith(" + 0)"):
                # The expression identity below initializes a WP call-result receiving slot. A
                # discarded builtin result must remain warning-free under native -Wall -Werror.
                text = f"(void){text}"
            if _strip(node).get("kind") in ("CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr") and \
                    re.fullmatch(r"\(\*[A-Za-z_]\w*\(.*\)\)", text):
                text = text[2:-1]               # ticket 25: a call returning a reference, as a statement: no `*`
            self.emit(f"{text};", indent)
        else:
            raise Unsupported(f"statement {kind}", self.line)

    # OpenMP (one thread: map 15; the symbolic-N program is ticket 45)
    def omp(self, node, kind, indent):
        text = self.unit.pragma(node, self.line)
        match = re.match(r"(?:#\s*)?pragma\s+omp\s+(.*)$", text)
        if not match:
            raise Unsupported(f"OpenMP directive {kind} (pragma text {text!r})", self.line)
        rest, directive = match.group(1), OMP_DIRECTIVES[kind]
        words = directive.split()
        for word in words:
            rest = re.sub(rf"^\s*{word}\b", "", rest)
        if directive == "critical":
            rest = re.sub(r"^\s*\(\s*\w+\s*\)", "", rest)
        if directive == "atomic":
            rest = re.sub(r"^\s*\b(read|write|update|capture|seq_cst|relaxed|acquire|release|acq_rel)\b", "", rest)
        reductions = []
        for clause in re.finditer(r"(\w+)\s*(\(([^()]*(?:\([^()]*\)[^()]*)*)\))?", rest):
            name, args = clause.group(1), (clause.group(3) or "").strip()
            if name == "schedule" and re.fullmatch(r"(static|dynamic)\s*(,.*)?", args) and directive.endswith("for"):
                continue
            if name == "nowait" and directive == "for":
                continue
            if name == "reduction" and directive in ("parallel", "for", "parallel for"):
                op, _, names = args.partition(":")
                if op.strip() not in OMP_REDUCTION_OPS:
                    raise Unsupported(f"OpenMP reduction({op.strip()}:...) (only {', '.join(OMP_REDUCTION_OPS)})",
                                      self.line)
                reductions += [(n.strip(), op.strip()) for n in names.split(",")]
                continue
            raise Unsupported(f"OpenMP clause {name}" + (f"({args})" if args else "") + f" on omp {directive}",
                              self.line)
        statements = [c for c in _children(node) if c.get("kind")]
        self.emit(f"/* omp {directive} (one thread) */", indent)
        if directive == "barrier":
            return
        target = statements[-1] if statements else None
        if target and target.get("kind") == "CapturedStmt":
            captured = _children(target)[0]
            target = _children(captured)[0]
        if target is None:
            raise Unsupported(f"OpenMP directive {kind} without a statement", self.line)
        if reductions:
            _check_reductions(target, reductions, self.line)
        self.statement(target, indent)

    # declarations
    def declaration_list(self, node):
        texts = []
        for i, decl in enumerate(node.get("inner", [])):
            text, extra = self.local(decl, first=i == 0, copy_allowed=False)
            if extra:
                raise Unsupported("a constructor call in a for initializer", self.line)
            texts.append(text)
        return ", ".join(texts)

    def local(self, node, first=True, copy_allowed=True):
        """(declaration text without `;`, extra statement lines) of one local variable."""
        self._at(node)
        if node.get("kind") != "VarDecl":
            raise Unsupported(f"declaration {node.get('kind')}", self.line)
        if node.get("storageClass") in ("static", "extern") or node.get("tls"):
            raise Unsupported(f"{node.get('storageClass') or 'thread-local'} local variable {node.get('name')}", self.line)
        _declaration_attributes(node, self.line)
        self.local_ids.add(node.get("id"))
        name = _name(node.get("name"), self.line)
        qual, desugared = _types(node)
        unit = self.unit
        text = unit.ctype(qual, desugared, name, self.line)
        if not first:                                        # for (int i = 0, j = 1; ...): repeat no type
            text = name
        init = [child for child in _children(node) if not child.get("kind", "").endswith("Attr")]
        extra = []
        if qual.rstrip().endswith("&"):
            self.ref_ids.add(node.get("id"))
            if not init:
                raise Unsupported(f"reference {name} with no initializer", self.line)
            return text + " = " + self.address(init[0]), extra
        parsed = _parse_type(desugared or qual, self.line)
        if init and _strip(init[0]).get("kind") == "CXXConstructExpr":
            if parsed.dims:
                cname = unit.base_type(parsed.base, parsed.args, self.line)
                cls = unit.classes.get(cname)
                if cls is None or any(c.get("kind") == "CXXConstructorDecl" and not c.get("isImplicit")
                                      for c in _children(cls)):
                    raise Unsupported(f"array of class {cname} built by a constructor", self.line)
                self._trivial(cname, cls)
            else:
                try:
                    call = self.construct(_strip(init[0]), name)
                except _CopyInit as copy:
                    if not copy_allowed:
                        raise Unsupported("an implicit memberwise copy in a for initializer", self.line)
                    text = self.copy_guard(copy, exclude=node.get("id")) + " ; " + text + " = " + copy.text
                else:
                    if call:
                        extra.append(call)
        elif init:
            tile = node.get("id") in self.tile_vars             # ticket 27: a tile pointer's initializer
            self._tile_ok += tile
            text += " = " + self.initializer(init[0], node.get("init"))
            self._tile_ok -= tile
        if not parsed.pointers and not _c_known(parsed.base):
            cname = unit.base_type(parsed.base, parsed.args, self.line)
            if unit.std_types.get(cname, {}).get("kind") == "vector":           # ticket 25: destroyed at scope end
                if parsed.dims:
                    raise Unsupported(f"array of {unit.std_types[cname]['cpp']}", self.line)
                self.scopes[-1].append((name, unit.std_member(cname, "dtor", self.line)))
            elif cname in unit.classes:
                dtor = self.destructor(cname)
                if dtor and parsed.dims:
                    raise Unsupported(f"array of class {cname} with a destructor", self.line)
                if dtor:
                    self.scopes[-1].append((name, dtor))
        return text, extra

    def destructor(self, cname):
        dtors = [d for d in _children(self.unit.classes[cname])
                 if d.get("kind") == "CXXDestructorDecl" and not d.get("isImplicit")]
        if not dtors:
            for child in _children(self.unit.classes[cname]):     # members with destructors: outside the subset
                if child.get("kind") == "FieldDecl":
                    parsed = _parse_type((child.get("type") or {}).get("desugaredQualType") or _qual(child), self.line)
                    if not parsed.pointers and not parsed.ref and not _c_known(parsed.base):
                        inner = self.unit.base_type(parsed.base, parsed.args, self.line)
                        if self.unit.std_types.get(inner, {}).get("kind") == "vector":     # ticket 25
                            raise Unsupported(f"class {cname} with a std::vector member (not modeled)", self.line)
                        if inner in self.unit.classes and self.destructor(inner):
                            raise Unsupported(f"class {cname} with a member that has a destructor", self.line)
            return None
        if not _has_body(dtors[0]):
            raise Unsupported(f"destructor of {cname} with no body", self.line)
        return self._lower(dtors[0], f"{cname}_dtor", cname, self.line)

    def construct(self, node, target):
        """The constructor call statement for object `target` (None when the C declaration alone suffices)."""
        model = self.unit.model_of(*_types(node), self.line)
        if model:                                                              # ticket 25
            return self._std_construct(model, node, target)
        cname, cls = self.unit.class_of(node, self.line)
        ctors = [c for c in _children(cls) if c.get("kind") == "CXXConstructorDecl"]
        ctor_type = (node.get("ctorType") or {}).get("qualType")
        args = [a for a in _children(node)]
        chosen = [c for c in ctors if _qual(c) == ctor_type] or \
                 [c for c in ctors if len([p for p in _children(c) if p.get("kind") == "ParmVarDecl"]) == len(args)]
        if len(chosen) != 1:
            raise Unsupported(f"constructor of {cname} (not exactly one match)", self.line)
        ctor = chosen[0]
        if ctor.get("isImplicit") or ctor.get("explicitlyDefaulted") == "default":
            self._trivial(cname, cls)
            if args:                                            # implicit copy or move: a C struct copy
                raise _CopyInit(self.expr(args[0], top=True), args[0])
            return None
        if ctor.get("explicitlyDefaulted") or ctor.get("isDeleted"):
            raise Unsupported(f"special constructor of {cname}", self.line)
        if not _has_body(ctor):
            raise Unsupported(f"constructor of {cname} with no body", self.line)
        if len([c for c in ctors if not c.get("isImplicit")]) > 1:
            raise Unsupported(f"overloaded constructor of {cname}", self.line)
        name = self._lower(ctor, f"{cname}_ctor", cname, self.line)
        params = [p for p in _children(ctor) if p.get("kind") == "ParmVarDecl"]
        texts = [f"&{target}"] + self.arguments(params, args)
        return f"{name}({', '.join(texts)});"

    def copy_guard(self, copy, exclude=None):
        """Check the exact source lvalue before replacing memberwise C++ construction by a C copy.

        C struct copying need not read indeterminate scalar members. The C++ wording is still being
        discussed in CWG2264; our declared subset conservatively requires initialized sources. This is
        an obligation, never a premise. Restrict duplicated address evaluation to simple pure lvalues.
        """
        constants = {}

        def pure(node):
            node = _strip(node)
            kind, children = node.get("kind"), _children(node)
            if kind == "DeclRefExpr" and (node.get("referencedDecl") or {}).get("id") == exclude:
                return False
            if kind in ("DeclRefExpr", "CXXThisExpr", "IntegerLiteral"):
                return True
            if kind == "MemberExpr":
                return len(children) == 1 and pure(children[0])
            if kind == "UnaryOperator" and node.get("opcode") == "*":
                return len(children) == 1 and pure(children[0])
            if kind == "ArraySubscriptExpr":
                return len(children) == 2 and all(pure(c) for c in children)
            if kind == "ImplicitCastExpr" and node.get("castKind") == "ArrayToPointerDecay":
                return len(children) == 1 and pure(children[0])
            if kind == "CallExpr" and len(children) == 1:
                callee = children[0]
                if callee.get("kind") == "ImplicitCastExpr" and callee.get("castKind") == "FunctionToPointerDecay":
                    callee = _children(callee)[0]
                ref = callee.get("referencedDecl") or {}
                if callee.get("kind") == "DeclRefExpr" and ref.get("name") in OMP_RUNTIME:
                    target = self.unit.function_node(ref["name"], _qual(ref), self.line)
                    value = OMP_RUNTIME[ref["name"]]
                    if target is not None and _has_body(target):
                        body = next(c for c in _children(target) if c.get("kind") == "CompoundStmt")
                        statements = _children(body)
                        returns = _children(statements[0]) if len(statements) == 1 else []
                        if (not statements or statements[0].get("kind") != "ReturnStmt" or len(returns) != 1
                                or _strip(returns[0]).get("kind") != "IntegerLiteral"
                                or _strip(returns[0]).get("value") != str(value)):
                            return False
                    # The model (or exact constant shim body) has this value and no effects. C calls
                    # cannot occur in ACSL terms; substitute only this syntactically checked constant.
                    constants[self.expr(node, top=True)] = str(value)
                    return True
            return False
        node = _strip(copy.node)
        if node.get("valueCategory") != "lvalue" or not pure(node):
            raise Unsupported("an implicit memberwise copy without a simple source lvalue", self.line)
        address = self.address(node)
        for call, value in constants.items():
            address = address.replace(call, value)
        return (f"/*@ assert swdb_memberwise_source_initialized: "
                f"\\valid_read({address}) && \\initialized({address}); */")

    def _trivial(self, cname, cls):
        for child in _children(cls):
            if child.get("kind") == "FieldDecl" and _children(child):
                raise Unsupported(f"implicit constructor of {cname} that runs default member initializers", self.line)

    def initializer(self, node, style):
        if node.get("kind") == "InitListExpr":
            return "{" + ", ".join(self.initializer(e, "list") for e in node.get("inner", [])) + "}"
        if style not in ("c", "call", "list", None):
            raise Unsupported(f"initialization style {style}", self.line)
        return self.expr(node, top=True)

    # expressions
    def expr(self, node, top=False):
        text, atomic = self._expr(node)
        rendered = text if top or atomic else f"({text})"
        if not self.pointer_rendering:
            self._pointer_access(node, rendered)
            rendered = self._pointer_formation(node, rendered) or rendered
        return rendered

    def _pointer_access(self, node, expression):
        if not (node.get("kind") == "ArraySubscriptExpr" or
                node.get("kind") == "UnaryOperator" and node.get("opcode") == "*" and
                _children(node) and wp_pointer_bounds._pointer(_children(node)[0])):
            return
        key = node.get("id")
        if key in self.pointer_access_seen:
            return
        self.pointer_access_seen.add(key)
        statement, anchor = self.pointer_contexts[-1] if self.pointer_contexts else (None, "")
        self.unit.pointer_sites.append(wp_pointer_bounds.access_site(node, expression=expression,
            statement=statement, anchor=anchor, function=self.function, line=_where(node) or self.line))

    def _pointer_formation(self, node, expression):
        """Retain source pointer operations even when the later C AST discards their value."""
        inner, kind = _children(node), node.get("kind")
        pointer = lambda n: bool(re.search(r"\*\s*(?:(?:const|volatile|restrict)\s*)*$", _qual(n)))
        base, offset, reason = None, None, ""
        if kind == "BinaryOperator" and node.get("opcode") in ("+", "-"):
            pointers = [child for child in inner if pointer(child)]
            if len(pointers) == 1 and pointer(node):
                base = pointers[0]
                offset = next(child for child in inner if child is not base)
            elif len(pointers) == 2:
                base, reason = pointers[0], "pointer subtraction needs a checked same-array and representable-distance policy"
        elif kind == "CompoundAssignOperator" and inner and pointer(inner[0]):
            base, reason = inner[0], "pointer mutation needs a precise check placement"
        elif kind == "UnaryOperator" and inner:
            if node.get("opcode") in ("++", "--") and pointer(inner[0]):
                base, reason = inner[0], "pointer mutation needs a precise check placement"
            elif node.get("opcode") == "&" and _strip(inner[0]).get("kind") == "ArraySubscriptExpr":
                args = _children(_strip(inner[0]))
                base = next((arg for arg in args if pointer(arg)), None)
                offset = next((arg for arg in args if arg is not base), None)
        key = node.get("id") or ("generated", id(node))
        if base is None or key in self.pointer_seen:
            return
        if not node.get("id"):
            reason = reason or "pointer operation has no source AST identity"
        self.pointer_seen.add(key)
        self.pointer_rendering = True
        try:
            base_text = self.expr(base)
            offset_text = self.expr(offset) if offset is not None else None
        finally:
            self.pointer_rendering = False
        statement, anchor = self.pointer_contexts[-1] if self.pointer_contexts else (None, "")
        row = wp_pointer_bounds.site(node, expression=expression, base=base_text, offset=offset_text,
            statement=statement, anchor=anchor, function=self.function, line=_where(node) or self.line, reason=reason,
            literal_offset=int(offset["value"]) if offset is not None and offset.get("kind") == "IntegerLiteral" else None)
        self.unit.pointer_sites.append(row)
        self.unit.pointer_nodes.add((self.function, node.get("id")))
        return row["normalized_expression"]

    def address(self, node):
        """The C pointer to the object an lvalue expression names (how a reference is bound)."""
        self._at(node)
        node = _strip(node)
        kind = node.get("kind")
        if kind == "MaterializeTemporaryExpr":
            value = _children(node)[0]
            qual, desugared = _types(node)
            ctype = self.unit.ctype(qual, desugared, line=self.line)
            return f"&({ctype}){{{self.expr(value, top=True)}}}"
        if kind == "DeclRefExpr" and self._is_ref(node):
            return _name((node.get("referencedDecl") or {}).get("name"), self.line)
        if kind == "UnaryOperator" and node.get("opcode") == "*":
            return self.expr(_children(node)[0])
        if kind in ("CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr"):
            text, _ = self._expr(node)
            if node.get("valueCategory") == "lvalue" and text.startswith("(*") and text.endswith(")"):
                return text[2:-1]                            # a call returning a reference returns the pointer
            raise Unsupported("a reference bound to the result of a call that returns a value", self.line)
        if kind == "MemberExpr" and self._member_is_ref(node):
            return self._member(node, deref=False)
        return f"&{self.expr(node)}"

    def _is_ref(self, node):
        ref = node.get("referencedDecl") or {}
        return ref.get("id") in self.ref_ids or (ref.get("type") or {}).get("qualType", "").rstrip().endswith("&")

    # ticket 27: tile pointers and their hazard probes
    def _is_tile_pointer_call(self, node):
        node = _tile_strip(node)
        if node.get("kind") != "CallExpr" or not self.semantics:
            return False
        callee = _tile_strip(node.get("inner", [{}])[0])
        return (callee.get("referencedDecl") or {}).get("name") in self.semantics.get("tile_pointer", ())

    def _is_tile_pointer(self, node):
        node = _tile_strip(node)
        if node.get("kind") == "DeclRefExpr":
            return (node.get("referencedDecl") or {}).get("id") in self.tile_vars
        if node.get("kind") == "BinaryOperator" and node.get("opcode") in ("+", "-"):
            return any(self._is_tile_pointer(child) for child in node.get("inner", []))
        return self._is_tile_pointer_call(node)

    def _tile_access(self, node):
        """Whether `node` reads or writes an element through a tile pointer (p[i], *p, *(p + i))."""
        node = _tile_strip(node)
        if node.get("kind") in ("ArraySubscriptExpr", "UnaryOperator") and \
                (node.get("kind") == "ArraySubscriptExpr" or node.get("opcode") == "*"):
            return self._is_tile_pointer(node["inner"][0])
        return False

    def _probe(self, node, access):
        """The access wrapped in its generated hazard probe; the site is recorded (C++ gets the same probe)."""
        node = _tile_strip(node)
        ident = f"{self.function}.probe{len(self.probes) + 1}"
        begin, end = (node.get("range") or {}).get("begin") or {}, (node.get("range") or {}).get("end") or {}
        site = {"id": ident, "function": self.function, "access": access, "line": self.line,
                "begin": begin.get("offset"), "end": (end.get("offset") or 0) + (end.get("tokLen") or 0)}
        self.probes.append(site)
        self.unit.probes.append(site)
        self.unit.probe_nodes.add((self.function, access, node.get("id")))
        self._tile_ok += 1
        if node.get("kind") == "ArraySubscriptExpr":
            text = f"{self.expr(node['inner'][0])}[{self.expr(node['inner'][1], top=True)}]"
        else:
            text = f"*{self.expr(node['inner'][0])}"
        self._tile_ok -= 1
        self._pointer_access(node, text)
        macro = "SWDB_TILE_READ" if access == "read" else "SWDB_TILE_WRITE"
        return f'(*{macro}(&({text}), "{ident}"))'

    def _expr(self, node):
        self._at(node)
        kind = node.get("kind")
        inner = node.get("inner", [])
        if self.semantics:                                   # ticket 27: probes before any other printing
            if kind == "ImplicitCastExpr" and node.get("castKind") == "LValueToRValue" and self._tile_access(inner[0]):
                return self._probe(inner[0], "read"), True
            if kind in ("ArraySubscriptExpr", "UnaryOperator") and self._tile_access(node):
                return self._probe(node, "write"), True
            if self._tile_ok == 0 and kind == "DeclRefExpr" and \
                    (node.get("referencedDecl") or {}).get("id") in self.tile_vars:
                raise Unsupported("a tile pointer used other than to read or write a tile element (p[i], *p)",
                                  self.line)
            if self._tile_ok == 0 and kind == "CallExpr" and self._is_tile_pointer_call(node):
                raise Unsupported("a tile pointer call whose result is not kept in a local variable", self.line)
            if kind == "BinaryOperator" and node.get("opcode") == "=" and self._is_tile_pointer_call(inner[1]):
                self._tile_ok += 1
                text = f"{self.expr(inner[0])} = {self.expr(inner[1])}"
                self._tile_ok -= 1
                return text, False
        if kind == "ImplicitCastExpr":
            cast = node.get("castKind")
            if cast == "NullToPointer":
                return "((void *)0)", True
            if cast not in PASS_CASTS:
                raise Unsupported(f"implicit conversion {cast}", self.line)
            text, atomic = self._expr(inner[0])
            # Qualification conversions must not hide the underlying source
            # pointer operation from its independent formation inventory.
            if cast == "NoOp" and not self.pointer_rendering and wp_pointer_bounds._pointer(inner[0]):
                text = self._pointer_formation(inner[0], text) or text
            return text, atomic
        if kind in EXPLICIT_CASTS:
            cast = node.get("castKind")
            if kind == "CXXReinterpretCastExpr" and cast != "BitCast":
                raise Unsupported("reinterpret_cast other than between pointer types", self.line)
            if cast == "ToVoid":
                return f"(void){self.expr(inner[0])}", False
            if cast not in PASS_CASTS | {"IntegralToBoolean"}:
                raise Unsupported(f"cast {cast}", self.line)
            qual, desugared = _types(node)
            ctype = self.unit.ctype(qual, desugared, line=self.line)
            return f"({ctype}){self.expr(inner[0])}", False
        if kind in ("ParenExpr",):
            return f"({self.expr(inner[0], top=True)})", True
        if kind in ("ExprWithCleanups", "ConstantExpr", "SubstNonTypeTemplateParmExpr", "CXXDefaultArgExpr",
                    "CXXDefaultInitExpr", "MaterializeTemporaryExpr") and inner:
            if kind == "ConstantExpr" and "value" in node and _qual(node) in SUFFIX:
                return f"{node['value']}{SUFFIX[_qual(node)]}", True
            return self._expr(_operand(node))
        if kind == "IntegerLiteral":
            qual = re.sub(r"\bstd::", "", _qual(node))
            if qual not in SUFFIX:
                raise Unsupported(f"integer literal of type {_qual(node)}", self.line)
            return f"{node['value']}{SUFFIX[qual]}", True
        if kind == "FloatingLiteral":
            qual = _qual(node)
            try:
                value = repr(float(node["value"]))          # clang prints a round-trip decimal; re-spell it for C
            except (KeyError, ValueError):
                value = "nan"
            if qual not in FLOAT_TYPES or value in ("inf", "-inf", "nan"):
                raise Unsupported(f"floating-point literal {node.get('value')} of type {qual}", self.line)
            return value + ("f" if qual == "float" else ""), True
        if kind == "CXXBoolLiteralExpr":
            return ("true" if node.get("value") else "false"), True
        if kind == "CharacterLiteral":
            return f"((char){node['value']})", True
        if kind == "StringLiteral":
            return node["value"], True
        if kind == "CXXNullPtrLiteralExpr":
            return "((void *)0)", True
        if kind == "CXXThisExpr":
            return "this", True
        if kind == "DeclRefExpr":
            return self._declref(node)
        if kind == "BinaryOperator":
            return f"{self.expr(inner[0])} {node['opcode']} {self.expr(inner[1])}", False
        if kind == "CompoundAssignOperator":
            return f"{self.expr(inner[0])} {node['opcode']} {self.expr(inner[1])}", False
        if kind == "UnaryOperator":
            if node.get("opcode") in ("__extension__", "__real", "__imag", "co_await"):
                raise Unsupported(f"operator {node.get('opcode')}", self.line)
            if node.get("opcode") == "&":
                return self.address(inner[0]), False
            operand = self.expr(inner[0])
            text = f"{operand}{node['opcode']}" if node.get("isPostfix") else f"{node['opcode']}{operand}"
            if not self.pointer_rendering:
                self._pointer_access(node, text)
            return text, False
        if kind == "ArraySubscriptExpr":
            text = f"{self.expr(inner[0])}[{self.expr(inner[1], top=True)}]"
            if not self.pointer_rendering:
                self._pointer_access(node, text)
            return text, True
        if kind == "ConditionalOperator":
            return f"{self.expr(inner[0])} ? {self.expr(inner[1])} : {self.expr(inner[2])}", False
        if kind == "CallExpr":
            return self._call(node)
        if kind == "MemberExpr":
            return self._member(node), True
        if kind == "CXXMemberCallExpr":
            return self._member_call(node)
        if kind == "CXXOperatorCallExpr":
            return self._operator_call(node)
        if kind == "AtomicExpr":
            return self._atomic(node)
        if kind == "CXXNewExpr":
            return self._new(node)
        if kind == "CXXDeleteExpr":
            return self.delete(node), False
        if kind == "UnaryExprOrTypeTraitExpr" and node.get("name") == "sizeof" and "argType" in node:
            arg = node["argType"]
            size = self.unit.ctype(arg.get("qualType", ""), arg.get("desugaredQualType"), line=self.line)
            return f"sizeof({size})", True
        if kind in ("CXXScalarValueInitExpr", "ImplicitValueInitExpr"):
            return "0", True
        if kind == "CXXConstructExpr":
            raise Unsupported("a class object constructed inside an expression", self.line)
        if kind in UNSUPPORTED_KINDS:
            raise Unsupported(UNSUPPORTED_KINDS[kind], self.line)
        raise Unsupported(_describe(kind), self.line)

    def _declref(self, node):
        ref = node.get("referencedDecl") or {}
        kind = ref.get("kind")
        if kind == "EnumConstantDecl":
            return str(self.unit.enum_value(ref, self.line)), True
        if kind == "FunctionDecl":
            if ref.get("name") not in self.callees and ref.get("name") != self.function:
                self.callees.append(ref["name"])
        elif kind == "VarDecl":
            if ref.get("id") not in self.local_ids and ref.get("name") not in self.globals:
                self.globals.append(ref["name"])
        elif kind != "ParmVarDecl":
            raise Unsupported(f"reference to a {kind} ({ref.get('name')})", self.line)
        if node.get("qualifier") or "::" in str(node.get("name", "")):
            raise Unsupported("qualified name", self.line)
        name = _name(ref.get("name"), self.line)
        if kind in ("VarDecl", "ParmVarDecl") and self._is_ref(node):
            return f"(*{name})", True
        return name, True

    # members
    def _member_is_ref(self, node):
        base = _children(node)[0]
        cname, _ = self.unit.class_of(base, self.line, arrow=node.get("isArrow"))
        return _qual(self.unit.field(cname, node.get("name"), self.line)).rstrip().endswith("&")

    def _object(self, base, arrow):
        """C text of a pointer to the object `base` names (`base` is already a pointer when `arrow`)."""
        return self.expr(base) if arrow else self.address(base)

    def _member(self, node, deref=True):
        base = _children(node)[0]
        arrow = node.get("isArrow")
        cname, _ = self.unit.class_of(base, self.line, arrow=arrow)
        name = _name(node.get("name"), self.line)
        field_node = self.unit.field(cname, node.get("name"), self.line)
        stripped = _strip(base)
        through_pointer = (stripped.get("kind") == "DeclRefExpr" and self._is_ref(stripped)) or \
            (stripped.get("kind") == "MemberExpr" and self._member_is_ref(stripped)) or \
            (stripped.get("kind") in ("CallExpr", "CXXMemberCallExpr", "CXXOperatorCallExpr") and
             stripped.get("valueCategory") == "lvalue") or \
            (stripped.get("kind") == "UnaryOperator" and stripped.get("opcode") == "*")
        if not arrow and not through_pointer:
            text = f"{self.expr(base)}.{name}"
        else:
            text = f"{self._object(base, arrow)}->{name}"
        if deref and _qual(field_node).rstrip().endswith("&"):
            return f"(*{text})"
        return text

    def _member_call(self, node):
        callee, args = _children(node)[0], _children(node)[1:]
        if callee.get("kind") != "MemberExpr":
            raise Unsupported("call through a pointer to member", self.line)
        base, arrow = _children(callee)[0], callee.get("isArrow")
        model = self.unit.model_of(*_types(_strip(base)), self.line, arrow=arrow)
        if model:                                                              # ticket 25
            return self._std_member_call(model, callee.get("name"), self._object(base, arrow), args)
        cname, _ = self.unit.class_of(base, self.line, arrow=arrow)
        method = self._method(cname, callee.get("name"), None)
        return self._invoke(method, cname, [self._object(base, arrow)], args)

    def _operator_call(self, node):
        children = _children(node)
        callee = children[0]
        while callee.get("kind") == "ImplicitCastExpr":
            callee = _children(callee)[0]
        ref = callee.get("referencedDecl") or {}
        name = ref.get("name", "")
        modeled = self._std_operator(name, children[1:])                       # ticket 25
        if modeled is not None:
            return modeled
        if ref.get("kind") == "CXXMethodDecl":
            obj = children[1]
            cname, _ = self.unit.class_of(obj, self.line)
            method = self._method(cname, name, (ref.get("type") or {}).get("qualType"))
            if method.get("isImplicit") or method.get("explicitlyDefaulted"):
                if name in ("=", "operator="):
                    raise Unsupported("an implicit memberwise assignment (expression ordering is not checked)", self.line)
                raise Unsupported(f"implicit operator {name} of {cname}", self.line)
            return self._invoke(method, cname, [self.address(obj)], children[2:])
        if ref.get("kind") == "FunctionDecl":
            symbol = name[len("operator"):].strip()
            if symbol not in OPERATOR_NAMES:
                raise Unsupported(f"operator {name}", self.line)
            target = self.unit.function_node(name, (ref.get("type") or {}).get("qualType"), self.line)
            if target is None or not _has_body(target):
                raise Unsupported(f"call to a function with no body in the translation unit: {name}", self.line)
            cname = self._lower(target, f"operator_{OPERATOR_NAMES[symbol]}", None, self.line)
            return self._finish_call(target, cname, [], children[1:])
        raise Unsupported(f"overloaded operator call {name}", self.line)

    def _method(self, cname, name, qual_type):
        kinds = ("CXXMethodDecl",)
        found = self.unit.methods(cname, name, kinds)
        if qual_type:
            found = [m for m in found if _qual(m) == qual_type] or found
        found = [m for m in found if not m.get("isImplicit")] or found
        distinct = {(m.get("mangledName"), _qual(m)) for m in found}
        if not found:
            raise Unsupported(f"member function {name} of {cname} (not found)", self.line)
        if len(distinct) > 1:
            raise Unsupported(f"overloaded member function {cname}::{name}", self.line)
        return found[0]

    def _invoke(self, method, cname, this_args, args):
        name = method.get("name", "")
        if method.get("isImplicit") or method.get("explicitlyDefaulted"):
            raise Unsupported(f"implicit member function {cname}::{name}", self.line)
        if not _has_body(method):
            raise Unsupported(f"member function {cname}::{name} with no body", self.line)
        if name.startswith("operator"):
            symbol = name[len("operator"):].strip()
            if symbol not in OPERATOR_NAMES:
                raise Unsupported(f"operator {name} of {cname}", self.line)
            suffix = f"operator_{OPERATOR_NAMES[symbol]}"
        else:
            suffix = name
        targs = [c for c in _children(method) if c.get("kind") == "TemplateArgument"]
        if targs:
            suffix += "_" + "_".join(_mangle_text(a) for a in self.unit._spec_args(method, self.line))
        static = method.get("storageClass") == "static"
        lowered = self._lower(method, f"{cname}_{suffix}", cname, self.line)
        return self._finish_call(method, lowered, [] if static else this_args, args)

    def _finish_call(self, target, cname, leading, args):
        params = [p for p in _children(target) if p.get("kind") == "ParmVarDecl"]
        texts = leading + self.arguments(params, args)
        call = f"{cname}({', '.join(texts)})"
        returns, _, _ = _return_and_params(_qual(target), self.line)
        if returns.rstrip().endswith("&"):
            return f"(*{call})", True
        return call, True

    def arguments(self, params, args):
        out = []
        for i, arg in enumerate(args):
            qual = _qual(params[i]) if i < len(params) else ""
            if qual.rstrip().endswith("&&"):
                raise Unsupported("rvalue reference parameter", self.line)
            out.append(self.address(arg) if qual.rstrip().endswith("&") else self.expr(arg, top=True))
        return out

    # calls
    def _call(self, node):
        inner = _children(node)
        callee = inner[0]
        while callee.get("kind") == "ImplicitCastExpr" and callee.get("castKind") in ("FunctionToPointerDecay",
                                                                                       "BuiltinFnToFnPtr"):
            callee = callee["inner"][0]
        ref = callee.get("referencedDecl") or {}
        if callee.get("kind") != "DeclRefExpr" or ref.get("kind") not in ("FunctionDecl", "CXXMethodDecl"):
            raise Unsupported("call through anything but a function name", self.line)
        name = str(ref.get("name", ""))
        qual_type = (ref.get("type") or {}).get("qualType")
        args = inner[1:]
        if name.startswith("__sync_"):
            return self._sync(name, args)
        if name in ("__atomic_thread_fence", "__atomic_signal_fence"):
            if len(args) != 1:
                raise Unsupported(f"atomic fence {name} operand shape", self.line)
            self._atomic_order(args[0], set(range(6)))
            return "(void)0", False
        if name.startswith("__builtin"):
            raise Unsupported(f"builtin call {name}", self.line)
        if ref.get("kind") == "CXXMethodDecl":
            raise Unsupported(f"call of member function {name} without an object", self.line)
        unit = self.unit
        if name in unit.summaries or name.startswith(SUMMARY_PREFIXES):
            if name not in unit.summaries:
                raise Unsupported(f"call to {name} with no summary (__dxc_* and maa_* calls go through summaries)",
                                  self.line)
            if name in self.semantics.get("refused_calls", set()):
                raise Unsupported(f"proof-semantics explicitly refuses {name}", self.line)
            cname = name
            node_found = unit.call_declaration(name, qual_type, node, self.source_declaration, self.line) \
                if "<" not in name else None
            if node_found is not None:
                _function_attributes(node_found, self.line)
            policy = self.semantics.get("array_call_policies", {}).get(name)
            imported = self.semantics.get("audited_imports", {}).get(name)
            producer = self.semantics.get("array_origins", {}).get(name)
            if producer:
                policy = {"model": producer["policy"]}
            policy = policy or imported
            if policy:
                statement, anchor = self.pointer_contexts[-1] if self.pointer_contexts else (None, "")
                site = wp_pointer_bounds.call_site(node, statement=statement, anchor=anchor,
                    function=self.function, line=_where(node) or self.line)
                site["producer"] = bool(producer)
                site["import"] = imported
                if producer or name not in self.semantics.get("array_call_policies", {}):
                    # No duplicated argument evaluation or derived guard for
                    # row producers: their original call/RTE obligations remain.
                    site["reason"] = ""
                    site["placement"] = "original producer call; no derived expression evaluation"
                try:
                    site["binding"] = wp_pointer_bounds.imported_binding(node, unit.dump(""), name,
                        summary=unit.summaries[name], policy=policy)
                    if imported:
                        wp_pointer_bounds.check_import_signature(site["binding"], imported)
                except wp_pointer_bounds.Refused as exc:
                    site["reason"] = str(exc)
                unit.pointer_calls.append(site)
            cname = unit.summary_c_name(name, node_found, self.line)
            instance = None
            variants = self.semantics.get('template_instances', {}).get(name)
            if variants is not None:
                arguments = list(unit._spec_args(node_found or {}, self.line))
                returns, params, variadic = _return_and_params(qual_type, self.line)
                matches = [v for v in variants if [' '.join(a.split()) for a in v['arguments']] == arguments
                           and v['arity'] == len(params)]
                if len(matches) != 1 or variadic:
                    raise Unsupported(f"no proof-semantics template instance for {name}<{', '.join(arguments)}> "
                                      f"with arity {len(params)}", self.line)
                instance = matches[0]
                definition = None
                if _has_body(node_found or {}):
                    if 'definition' not in instance:
                        raise Unsupported('template instance needs a pinned interface definition; '
                                          'source-defined implementations cannot inherit a device contract', self.line)
                    from swdb import dx100_source_selector
                    try:
                        definition = dx100_source_selector.certify(unit, node_found, arguments, instance['definition'],
                                                                  standard=STD, timeout=TIMEOUT_SECONDS)
                    except dx100_source_selector.Refused as exc:
                        raise Unsupported('DX100 source selector definition: '+str(exc), self.line) from None
                elif 'definition' in instance:
                    raise Unsupported('DX100 source selector requires the real pinned definition', self.line)
                signature = unit.ctype(returns, line=self.line) + '(' + ','.join(
                    unit.ctype(p, line=self.line) for p in params) + ')'
                try:
                    wp_pointer_bounds.check_import_signature({'signature': signature},
                        {'prototype': instance['prototype'], 'call': cname})
                except wp_pointer_bounds.Refused as exc:
                    raise Unsupported(f'template instance C signature differs: {exc}', self.line) from None
            names = [p.get("name") for p in _children(node_found or {}) if p.get("kind") == "ParmVarDecl"]
            unit.summary(name, cname, qual_type, self.line, names)
            if instance is not None:
                used = next(row for row in unit.summaries_used if row['c_name'] == cname)
                used['semantic_instance'] = {'arguments': arguments, 'arity': len(params)}
                if definition is not None:
                    used['semantic_instance']['definition'] = definition
            returns, params, _ = _return_and_params(qual_type, self.line)
            texts = [self.address(a) if i < len(params) and params[i].rstrip().endswith("&") else self.expr(a, top=True)
                     for i, a in enumerate(args)]
            call = f"{cname}({', '.join(texts)})"
            if (name == "get_cacheable_tile_pointer" and name in self.semantics.get("tile_pointer", ())) or \
                    (name in self.semantics.get("calls", ()) and
                     (returns in INTEGER_TYPES or (instance is not None and unit.ctype(returns, line=self.line) in INTEGER_TYPES))):
                # 2026-10-15 ET: WP33 does not initialize a receiving local slot
                # for a modular call. An identity expression forces its ordinary
                # assignment path. Imported integer results have an exact identity;
                # only the tile-pointer contract returns a known non-null static
                # row. Nullable pointers and floating-point calls are unchanged.
                return f"({call} + 0)", True
            return (f"(*{call})", True) if returns.rstrip().endswith("&") else (call, True)
        if name in STD_MODELS:
            target = unit.function_node(name, qual_type, self.line)
            if target is not None and _is_std(target):
                return self._std(name, target, args, node)
        target = unit.call_declaration(name, qual_type, node, self.source_declaration, self.line)
        if target is None or not _has_body(target):
            if name in OMP_RUNTIME and not args:
                return self._omp_runtime(name), True
            raise Unsupported(f"call to a function with no body in the translation unit: {name}", self.line)
        if _is_std(target):
            raise Unsupported(f"standard library function std::{name}", self.line)
        mangled = target.get("mangledName", name)
        if mangled.startswith(("_ZN", "__ZN")):
            raise Unsupported(f"function {name} inside a namespace or class", self.line)
        cname = name
        if _children_kind(target, "TemplateArgument"):
            cname = f"{name}_{'_'.join(_mangle_text(a) for a in unit._spec_args(target, self.line))}"
        self._lower(target, cname, None, self.line)
        return self._finish_call(target, cname, [], args)

    def _omp_runtime(self, name):
        model, text = model_definition("omp", name, "int")
        return self._initialized_model_result(f"{self.unit.model(model, text, self.line)}()", "int")

    def _scalar(self, ctype, what):
        plain = ctype.replace("const ", "").replace("volatile ", "").strip()
        if plain not in INTEGER_TYPES | FLOAT_TYPES and not plain.endswith("*"):
            raise Unsupported(f"{what} on type {ctype} (scalars and pointers only)", self.line)
        return plain

    def _pointee(self, node, what):
        qual, desugared = _types(_strip(node))
        ctype = self.unit.ctype(qual, desugared, line=self.line)
        if not ctype.endswith("*"):
            raise Unsupported(f"{what} on a non-pointer", self.line)
        return self._scalar(ctype[:-1].strip().replace("volatile", "").strip(), what)

    def _std(self, name, target, args, call_node):
        unit = self.unit
        unit.stdlib_substitutions.append(stdlib_provenance.substitution(call_node, target))
        if name == "swap" and len(args) == 2:
            model = unit.model_of(*_types(_strip(args[0])), self.line)
            if model and model[1]["kind"] == "vector":
                return f"{unit.std_member(model[0], 'swap', self.line)}({self.address(args[0])}, {self.address(args[1])})", True
        if name in ("min", "max", "swap"):
            if len(args) != 2:
                raise Unsupported(f"std::{name} with a comparator or an initializer list", self.line)
            qual, desugared = _types(_strip(args[0]))
            ctype = self._scalar(unit.ctype(qual, desugared, line=self.line), f"std::{name}")
            model = unit.model(*model_definition("std", name, ctype), self.line)
            if name == "swap":
                return f"{model}({self.address(args[0])}, {self.address(args[1])})", True
            text = f"{model}({self.expr(args[0], top=True)}, {self.expr(args[1], top=True)})"
            return self._initialized_model_result(text, ctype), True
        if name == "copy":
            if len(args) != 3:
                raise Unsupported("std::copy with an execution policy", self.line)
            element = self._pointee(args[0], "std::copy")
            if element != self._pointee(args[2], "std::copy"):
                raise Unsupported("std::copy between different element types", self.line)
            model = unit.model(*model_definition("std", "copy", element), self.line)
            from swdb import standard_range_calls
            statement, anchor = self.pointer_contexts[-1] if self.pointer_contexts else (None, "")
            unit.standard_range_calls.append(standard_range_calls.site(call_node, statement=statement,
                anchor=anchor,function=self.function,line=_where(call_node) or self.line,model=model,target=target))
            return f"{model}({', '.join(self.expr(a, top=True) for a in args)})", True
        raise Unsupported(f"standard library function std::{name}", self.line)

    # ticket 25: std::vector<T> and std::pair<A, B> through swdb.std_models
    VECTOR_CALLS = {"size": 0, "empty": 0, "data": 0, "begin": 0, "end": 0, "clear": 0, "at": 1, "push_back": 1,
                    "resize": 1, "reserve": 1, "swap": 1}

    def _std_member_call(self, model, name, obj, args):
        cname, info = model
        args = [a for a in args if a.get("kind") != "CXXDefaultArgExpr"]
        if info["kind"] != "vector" or self.VECTOR_CALLS.get(name) != len(args):
            raise Unsupported(f"{info['cpp']} member {name} (not modeled)", self.line)
        function = self.unit.std_member(cname, name, self.line)
        texts = [obj] + ([self.address(args[0])] if name == "swap" else [self.expr(a, top=True) for a in args])
        call = f"{function}({', '.join(texts)})"
        return (f"(*{call})", True) if name == "at" else (call, True)

    def _std_operator(self, name, operands):
        """An operator on a modeled type or a vector iterator (None when the operands are neither)."""
        symbol = name[len("operator"):].strip()
        if any("__wrap_iter<" in "".join(t or "" for t in _types(o)) for o in operands):
            texts = [self.expr(o) for o in operands]
            if symbol == "*" and len(texts) == 1:
                return f"(*{texts[0]})", True
            if symbol in ("++", "--"):
                return (f"{symbol}{texts[0]}" if len(texts) == 1 else f"{texts[0]}{symbol}"), False
            if symbol == "[]":
                return f"{texts[0]}[{self.expr(operands[1], top=True)}]", True
            if symbol in ("==", "!=", "<", "<=", ">", ">=", "+", "-", "+=", "-=") and len(texts) == 2:
                return f"{texts[0]} {symbol} {texts[1]}", False
            raise Unsupported(f"vector iterator operator{symbol}", self.line)
        model = self.unit.model_of(*_types(_strip(operands[0])), self.line) if operands else None
        if model is None:
            return None
        cname, info = model
        if info["kind"] == "vector" and symbol == "[]":
            call = f"{self.unit.std_member(cname, 'operator_index', self.line)}({self.address(operands[0])}, " \
                   f"{self.expr(operands[1], top=True)})"
            return f"(*{call})", True
        if info["kind"] == "pair" and symbol == "=" and self.unit.model_of(*_types(_strip(operands[1])), self.line):
            call = f"{self.unit.std_member(cname, 'operator_assign', self.line)}({self.address(operands[0])}, " \
                   f"{self.address(operands[1])})"
            return f"(*{call})", True
        raise Unsupported(f"{info['cpp']} operator{symbol} (not modeled)", self.line)

    def _std_construct(self, model, node, target):
        cname, info = model
        args = [a for a in _children(node) if a.get("kind") != "CXXDefaultArgExpr"]
        _, params, _ = _return_and_params((node.get("ctorType") or {}).get("qualType", "()"), self.line)
        same = len(args) == 1 and self.unit.model_of(*_types(_strip(args[0])), self.line) == model
        source = None
        if same:
            source = _strip(args[0])
            if source.get("kind") == "CallExpr" and \
                    ((_children(source)[0].get("inner") or [{}])[0].get("referencedDecl") or {}).get("name") == "move":
                source = _children(source)[1]                     # std::move(x): the move constructor's source
        if info["kind"] == "vector":
            if not args:
                member, texts = "ctor", []
            elif same:
                member, texts = ("move_ctor" if params[0].rstrip().endswith("&&") else "copy_ctor"), [self.address(source)]
            elif len(args) == 1 and "size_type" in params[0]:
                member, texts = "ctor_count", [self.expr(args[0], top=True)]
            elif len(args) == 2 and "size_type" in params[0] and "value_type" in params[1]:
                member, texts = "ctor_count_value", [self.expr(a, top=True) for a in args]
            else:
                raise Unsupported(f"{info['cpp']} constructor {params} (not modeled)", self.line)
        else:
            if not args:
                member, texts = "ctor_default", []
            elif same:
                member, texts = "copy_ctor", [self.address(source)]
            elif len(args) == 2:
                member, texts = "ctor", [self.expr(a, top=True) for a in args]
            else:
                raise Unsupported(f"{info['cpp']} constructor {params} (not modeled)", self.line)
        function = self.unit.std_member(cname, member, self.line)
        return f"{function}({', '.join([f'&{target}'] + texts)});"

    def _range_for(self, node, indent):
        """`for (decl : v)` over a vector, as [stmt.ranged] defines it: __range, __begin, __end, a pointer loop."""
        parts = [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]
        if len(parts) != 7 or any(p.get("kind") != "DeclStmt" for p in (parts[0], parts[1], parts[2], parts[5])):
            raise Unsupported("range-based for with an init statement", self.line)
        range_stmt, begin_stmt, end_stmt, cond, step, var_stmt, loop_body = parts
        bound = _children(_children(range_stmt)[0])
        if not bound or not self.unit.model_of(*_types(_strip(bound[0])), self.line) or \
                self.unit.model_of(*_types(_strip(bound[0])), self.line)[1]["kind"] != "vector":
            raise Unsupported("range-based for over anything but a std::vector", self.line)
        self.emit("{", indent)
        self.scopes.append([])
        for stmt in (range_stmt, begin_stmt, end_stmt):
            text, extra = self.local(_children(stmt)[0])
            if extra:
                raise Unsupported("range-based for whose range needs a constructor call", self.line)
            self.simple(text + ";", indent + 1)
        self.loops += 1
        self.anchor(f"{self.function}.loop{self.loops}.head", "loop_head", indent + 1)
        self.emit(f"for (; {self.expr(cond, top=True)}; {self.expr(step, top=True)}) {{", indent + 1)
        statements = loop_body.get("inner", []) if loop_body.get("kind") == "CompoundStmt" else [loop_body]
        self.body({"kind": "CompoundStmt", "inner": [var_stmt, *statements]}, indent + 2)
        self.emit("}", indent + 1)
        self.scopes.pop()
        self.emit("}", indent)

    def _return_destroying(self, inner, indent):
        """A return out of scopes that destroy objects: keep the value, destroy innermost first, return it."""
        pending = [entry for scope in self.scopes for entry in scope]
        if self.returns_ref:
            raise Unsupported("return of a reference out of a scope that destroys an object", self.line)
        self.emit("{", indent)
        if inner:
            self.emit(f"{_join(self.returns_ctype, 'swdb_return')} = {self.expr(inner[0], top=True)};", indent + 1)
        for name, dtor in reversed(pending):
            self.emit(f"{dtor}(&{name});", indent + 1)
        self.emit("return swdb_return;" if inner else "return;", indent + 1)
        self.emit("}", indent)

    def _atomic(self, node):
        name = node.get("name", "")
        op = name[len("__atomic_"):] if name.startswith("__atomic_") else ""
        if op not in ATOMIC_OPS:
            raise Unsupported(f"atomic builtin {name}", self.line)
        children = _children(node)
        if len(children) != (2 if op == "load_n" else 6 if op == "compare_exchange_n" else 3):
            raise Unsupported(f"atomic builtin {name} operand shape", self.line)
        order = self._atomic_order(children[1], {0, 1, 2, 5} if op == "load_n" else
                                   {0, 3, 5} if op == "store_n" else set(range(6)))
        if op == "compare_exchange_n":
            # Failure has load semantics: release is incomparable with acquire,
            # so a numeric failure <= success comparison would admit invalid pairs.
            failure_orders = {0: {0}, 1: {0, 1}, 2: {0, 1, 2}, 3: {0}, 4: {0, 1, 2}, 5: {0, 1, 2, 5}}
            self._atomic_order(children[3], failure_orders[order])
            if self._atomic_constant(children[5], "weak flag") != 0:
                raise Unsupported("atomic weak compare-exchange may fail spuriously; only constant false is supported",
                                  self.line)
        ptr = children[0]
        ctype = self._pointee(ptr, name)
        if op == "load_n":
            values = []
        elif op == "compare_exchange_n":
            values = [children[2], children[4]]               # ptr, order, expected, order_fail, desired, weak
        else:
            values = [children[2]]                            # ptr, order, value
        model = self._atomic_model("atomic", op, ctype)
        texts = [self.expr(ptr, top=True)] + [self.expr(v, top=True) for v in values]
        text = f"{model}({', '.join(texts)})"
        return self._initialized_model_result(text, ctype, boolean=op == "compare_exchange_n",
                                              void=op == "store_n"), True

    def _atomic_constant(self, node, label):
        """Atomic operand admission v1: no runtime reads/effects or folded-away RTE."""
        kind, children = node.get("kind"), _children(node)
        wrappers = {"ParenExpr", "ConstantExpr", "ImplicitCastExpr", "CStyleCastExpr", "CXXStaticCastExpr"}
        if kind in wrappers and len(children) == 1:
            if kind in {"ParenExpr", "ConstantExpr"}:
                return self._atomic_constant(children[0], label)
            if (node.get("castKind") in {"NoOp", "IntegralCast", "IntegralToBoolean"}
                    and _qual(node) in INTEGER_TYPES | {"bool"}):
                value = self._atomic_constant(children[0], label)
                if not 0 <= value <= 5:
                    raise Unsupported(f"atomic {label} cast is outside the closed constant domain", self.line)
                return int(value != 0) if node.get("castKind") == "IntegralToBoolean" else value
        if kind == "IntegerLiteral" and not children:
            return int(node["value"])
        if kind == "CXXBoolLiteralExpr" and not children:
            return int(node["value"])
        if kind == "DeclRefExpr" and not children and node.get("referencedDecl", {}).get("kind") == "EnumConstantDecl":
            try:
                return self.unit.enum_value(node["referencedDecl"], self.line)
            except Unsupported as exc:
                raise Unsupported(f"atomic {label}: {exc.construct}", self.line) from None
        raise Unsupported(f"atomic {label} requires a literal or enum constant with safe integer wrappers", self.line)

    def _atomic_order(self, node, allowed):
        value = self._atomic_constant(node, "memory order")
        if value not in allowed:
            raise Unsupported("atomic memory order is invalid for this operation", self.line)
        return value

    def _sync(self, name, args):
        if name == "__sync_synchronize":
            return "(void)0", False
        op = re.sub(r"_\d+$", "", name[len("__sync_"):])
        if op not in SYNC_OPS:
            raise Unsupported(f"atomic builtin {name}", self.line)
        ctype = self._pointee(args[0], name)
        model = self._atomic_model("sync", op, ctype)
        text = f"{model}({', '.join(self.expr(a, top=True) for a in args)})"
        return self._initialized_model_result(text, ctype, boolean=op == "bool_compare_and_swap"), True

    @staticmethod
    def _initialized_model_result(text, ctype, *, boolean=False, void=False):
        """Ordinary integer assignment after WP33's modular call; preserve one evaluation.

        WP binds a returned value but leaves the receiving lvalue's initialized bit unknown.
        Adding integer zero is an exact identity and makes the assignment ordinary. It is
        deliberately excluded for pointers (including null) and floating-point results.
        """
        return f"({text} + 0)" if not void and (boolean or ctype in INTEGER_TYPES) else text

    def _atomic_model(self, family, op, ctype):
        try:
            return self.unit.model(*model_definition(family, op, ctype), self.line)
        except Unsupported as exc:
            raise Unsupported(exc.construct, self.line) from None

    def _new(self, node):
        if not node.get("isArray"):
            raise Unsupported("new of a single object (new[] is in the subset)", self.line)
        if node.get("initStyle") or node.get("isPlacement") or node.get("placementArgs"):
            raise Unsupported("new[] with an initializer or a placement", self.line)
        children = _children(node)
        if len(children) != 1:
            raise Unsupported("new[] with an initializer", self.line)
        qual, desugared = _types(node)
        ctype = self.unit.ctype(qual, desugared, line=self.line)
        element = ctype[:-1].strip()
        if element in self.unit.classes:
            cls = self.unit.classes[element]
            if any(c.get("kind") == "CXXConstructorDecl" and not c.get("isImplicit") for c in _children(cls)):
                raise Unsupported(f"new[] of class {element} with a constructor", self.line)
            self._trivial(element, cls)
        self.unit.needs_stdlib = True
        model = self.unit.model(*model_definition("alloc", "new_array", element), self.line)
        return f"{model}((size_t)({self.expr(children[0], top=True)}))", True

    def delete(self, node):
        if not node.get("isArray"):
            raise Unsupported("delete of a single object (delete[] is in the subset)", self.line)
        target = _children(node)[0]
        qual, desugared = _types(_strip(target))
        element = self.unit.ctype(qual, desugared, line=self.line)[:-1].strip()
        if element in self.unit.classes and self.destructor(element):
            raise Unsupported(f"delete[] of class {element} with a destructor", self.line)
        self.unit.needs_stdlib = True
        model = self.unit.model(*model_definition("alloc", "delete_array", element), self.line)
        return f"{model}({self.expr(target, top=True)})"


class _CopyInit(Exception):
    """A declaration initialized by an implicit copy constructor: printed as a C struct copy."""

    def __init__(self, text, node):
        super().__init__(text)
        self.text = text
        self.node = node


def _tile_strip(node):
    """The node under parentheses and pass-through implicit conversions (ticket 27's tile-pointer tracking)."""
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
            target = _tile_strip(node["inner"][0])
            if target.get("kind") == "DeclRefExpr":
                found.add((target.get("referencedDecl") or {}).get("id"))
        pending += node.get("inner", [])
    return found


def _children_kind(node, kind):
    return any(c.get("kind") == kind for c in _children(node))


def _check_reductions(target, reductions, line):
    """At one thread a reduction is the plain update, if each use of the variable is an `op=` update."""
    names = dict(reductions)
    stack = [(target, None)]
    while stack:
        node, parent = stack.pop()
        if node.get("kind") == "DeclRefExpr":
            name = (node.get("referencedDecl") or {}).get("name")
            if name in names:
                ok = parent is not None and parent.get("kind") == "CompoundAssignOperator" and \
                    _children(parent)[0] is node and parent.get("opcode") in OMP_REDUCTION_OPS[names[name]]
                if not ok:
                    raise Unsupported(f"reduction variable {name} used other than in a `{names[name]}=` update", line)
        for child in _children(node):
            stack.append((child, node))


# --- C models (each proven once: `swdb prove --model NAME`; a unit's record pins it) ------------------------

MODEL_TYPES = sorted(INTEGER_TYPES | FLOAT_TYPES)


def model_definition(family, op, ctype):
    """(C name, C text with its ACSL contract) of one C model: family std (min, max, swap, copy), atomic or sync
    (one-thread meaning, map 15: a CAS is a read, a compare and a write), or omp (the OpenMP runtime, one thread)."""
    if family == "omp":
        value = OMP_RUNTIME[op]
        return op, (f"/*@ assigns \\nothing;\n    ensures \\result == {value}; */\n"
                    f"static int {op}(void) {{ return {value}; }}")
    model = f"std_{op}_{_mangle_text(ctype)}" if family == "std" else f"swdb_{family}_{op}_{_mangle_text(ctype)}"
    if family == "alloc":
        # Allocation models rest on the assumption entry "allocation succeeds" (map 16 item 7; ticket 25 writes it):
        # their contracts are assumed, not proven. WP 33 has no deallocation (\fresh, \freeable and frees are not
        # supported), so a read after delete[] is beyond WP; the bounded verifier (CBMC) models free.
        if op == "new_array":
            return model, (f"/*@ requires 1 <= n;\n    assigns \\nothing;\n"
                           f"    ensures \\valid(\\result + (0 .. n - 1)); */\n"
                           f"static {ctype} *{model}(size_t n) {{ return ({ctype} *)malloc(sizeof({ctype}) * n); }}")
        if op == "delete_array":
            return model, (f"/*@ requires \\valid(p);\n    assigns \\nothing; */\n"
                           f"static void {model}({ctype} *p) {{ free(p); }}")
        raise Unsupported(f"C model alloc {op}")
    if family == "std" and op in ("min", "max"):
        pick = "(b < a) ? b : a" if op == "min" else "(a < b) ? b : a"
        return model, (f"/*@ assigns \\nothing;\n    ensures \\result == ({pick}); */\n"
                       f"static {ctype} {model}({ctype} a, {ctype} b) {{ return {pick}; }}")
    if family == "std" and op == "swap":
        return model, (f"/*@ requires \\valid(a) && \\valid(b);\n    requires \\initialized(a) && \\initialized(b);\n"
                       f"    assigns *a, *b;\n    ensures \\initialized(a) && \\initialized(b);\n"
                       f"    ensures *a == \\old(*b) && *b == \\old(*a); */\n"
                       f"static void {model}({ctype} *a, {ctype} *b) {{ {ctype} t = *a; *a = *b; *b = t; }}")
    if family == "std" and op == "copy":
        return model, (f"/*@ requires \\base_addr(first) == \\base_addr(last) && first <= last;\n"
                       f"    requires last - first <= PTRDIFF_MAX;\n"
                       f"    requires \\valid_read(first + (0 .. last - first - 1));\n"
                       f"    requires \\initialized(first + (0 .. last - first - 1));\n"
                       f"    requires \\valid(d_first + (0 .. last - first - 1));\n"
                       f"    requires \\separated(first + (0 .. last - first - 1), d_first + (0 .. last - first - 1));\n"
                       f"    assigns d_first[0 .. last - first - 1];\n"
                       f"    ensures \\initialized(d_first + (0 .. last - first - 1));\n"
                       f"    ensures \\forall integer k; 0 <= k < last - first ==> d_first[k] == \\old(first[k]);\n"
                       f"    ensures \\result == d_first + (last - first); */\n"
                       f"static {ctype} *{model}(const {ctype} *first, const {ctype} *last, {ctype} *d_first) {{\n"
                       f"  const ptrdiff_t n = first == last ? 0 : last - first;\n"
                       f"  /*@ loop invariant 0 <= i <= n;\n"
                       f"      loop invariant \\forall integer k; 0 <= k < i ==> d_first[k] == first[k];\n"
                       f"      loop invariant \\initialized(d_first + (0 .. i - 1));\n"
                       f"      loop assigns i, d_first[0 .. n - 1];\n"
                       f"      loop variant n - i; */\n"
                       f"  for (ptrdiff_t i = 0; i < n; ++i) d_first[i] = first[i];\n"
                       f"  return n == 0 ? d_first : d_first + n;\n}}")
    if family not in ("atomic", "sync") or op not in (ATOMIC_OPS if family == "atomic" else SYNC_OPS):
        raise Unsupported(f"C model {family} {op}")
    pointer = ctype.endswith("*")
    if not pointer and ctype not in INTEGER_TYPES:
        raise Unsupported(f"atomic {op} on type {ctype} (integers and pointers only)")
    unsigned = ctype if pointer or ctype.startswith("unsigned") or ctype.startswith("uint") or ctype == "bool" \
        or ctype == "size_t" or ctype == "uintptr_t" else UNSIGNED_OF.get(ctype)
    head = "/*@ requires \\valid(p);\n"
    if op != "store_n":
        head += "    requires \\initialized(p);\n"
    if op == "load_n":
        text = (f"{head}    assigns \\nothing;\n    ensures \\result == *p; */\n"
                f"static {ctype} {model}({ctype} *p) {{ return *p; }}")
    elif op == "store_n":
        text = (f"{head}    assigns *p;\n    ensures *p == v; */\n"
                f"static void {model}({ctype} *p, {ctype} v) {{ *p = v; }}")
    elif op == "exchange_n":
        text = (f"{head}    assigns *p;\n    ensures *p == v && \\result == \\old(*p); */\n"
                f"static {ctype} {model}({ctype} *p, {ctype} v) {{ {ctype} old = *p; *p = v; return old; }}")
    elif op == "compare_exchange_n":
        text = (f"/*@ requires \\valid(p) && \\valid(e) && \\separated(p, e);\n"
                f"    requires \\initialized(p) && \\initialized(e);\n    assigns *p, *e;\n"
                f"    ensures \\old(*p) == \\old(*e) ==> *p == d && *e == \\old(*e) && \\result == 1;\n"
                f"    ensures \\old(*p) != \\old(*e) ==> *p == \\old(*p) && *e == \\old(*p) && \\result == 0; */\n"
                f"static bool {model}({ctype} *p, {ctype} *e, {ctype} d) {{\n"
                f"  if (*p == *e) {{ *p = d; return true; }}\n  *e = *p;\n  return false;\n}}")
    elif op == "bool_compare_and_swap":
        text = (f"{head}    assigns *p;\n"
                f"    ensures \\old(*p) == o ==> *p == n && \\result == 1;\n"
                f"    ensures \\old(*p) != o ==> *p == \\old(*p) && \\result == 0; */\n"
                f"static bool {model}({ctype} *p, {ctype} o, {ctype} n) {{\n"
                f"  if (*p == o) {{ *p = n; return true; }}\n  return false;\n}}")
    elif op == "val_compare_and_swap":
        text = (f"{head}    assigns *p;\n"
                f"    ensures \\old(*p) == o ==> *p == n;\n    ensures \\old(*p) != o ==> *p == \\old(*p);\n"
                f"    ensures \\result == \\old(*p); */\n"
                f"static {ctype} {model}({ctype} *p, {ctype} o, {ctype} n) {{\n"
                f"  {ctype} old = *p;\n  if (old == o) *p = n;\n  return old;\n}}")
    else:
        if pointer or unsigned is None or ctype == "bool":
            raise Unsupported(f"atomic arithmetic on type {ctype}")
        words = op.split("_")
        fetch_first = words[0] == "fetch"
        arith = _ARITH[words[-1] if fetch_first else words[0]]
        new = f"({ctype})(({unsigned})old {arith} ({unsigned})v)"
        result = "old" if fetch_first else "*p"
        acsl_new = f"({ctype})(\\old(*p) {arith} v)"
        acsl_result = "\\old(*p)" if fetch_first else "*p"
        text = (f"{head}    assigns *p;\n    ensures *p == {acsl_new};\n"
                f"    ensures \\result == {acsl_result}; */\n"
                f"static {ctype} {model}({ctype} *p, {ctype} v) {{\n"
                f"  {ctype} old = *p;\n  *p = {new};\n  return {result};\n}}")
    if op != "load_n":
        initialized = "\\initialized(p)" + (" && \\initialized(e)" if op == "compare_exchange_n" else "")
        text = text.replace("    ensures ", f"    ensures {initialized};\n    ensures ", 1)
    return model, text


def model_text(name):
    """The C text of the C model a lowering calls `name`, or None: what `swdb prove --model NAME` proves."""
    from swdb import vector_reallocation_model
    qualified = vector_reallocation_model.model_text(name)
    if qualified is not None:
        return qualified
    modeled = std_models.model_text(name)
    if modeled is not None:
        return modeled
    if name in OMP_RUNTIME:
        return model_definition("omp", name, "int")[1]
    types = [*MODEL_TYPES, *[f"{t} *" for t in MODEL_TYPES]]
    for family, ops in (("std", ("min", "max", "swap", "copy")), ("atomic", sorted(ATOMIC_OPS)),
                        ("sync", sorted(SYNC_OPS)), ("alloc", ("new_array", "delete_array"))):
        for op in ops:
            prefix = f"std_{op}_" if family == "std" else f"swdb_{family}_{op}_"
            if not name.startswith(prefix):
                continue
            for ctype in types:
                if _mangle_text(ctype) == name[len(prefix):]:
                    try:
                        return model_definition(family, op, ctype)[1]
                    except Unsupported:
                        return None
    return None


def _describe(kind):
    named = {"CXXMemberCallExpr": "member function call", "CXXOperatorCallExpr": "overloaded operator call",
             "MemberExpr": "member access (classes and structs)", "CXXThisExpr": "this",
             "CXXNewExpr": "new", "CXXDeleteExpr": "delete", "StringLiteral": "string literal",
             "FloatingLiteral": "floating-point literal (long double is outside the subset)",
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

def lower(source, function, includes=(), defines=(), summaries=None, semantics=None,
          array_domains=None, array_domain_contract=None):
    """The C lowering of `function` (and of every function, class and global it uses) from the C++ file `source`.

    `summaries` maps the C++ name of a function to the summary that stands for it ({name: summary ID or
    text}): each call to it stays a call (with a prototype), and the lowering lists the summary as used.
    Every `__dxc_*` and `maa_*` call needs one.

    `semantics` (ticket 27; the bounded verifier passes it with the proof semantics' calls as summaries):
    {tile_pointer: the calls that return a tile pointer}. Every element access through a tile pointer then
    gets a generated hazard probe (`SWDB_TILE_READ` / `SWDB_TILE_WRITE`, ID `<function>.probe<N>`), listed in
    `Lowering.probes` with its C++ source range so the C++ side gets the same probe. A tile pointer used any
    other way is outside the subset. Without `semantics` the output is unchanged."""
    tool = locate()
    if tool.missing:
        raise LoweringError(tool.missing)
    source = Path(source)
    if not source.is_file():
        raise LoweringError(f"no source file {source}")
    defines = tuple(sorted(defines))
    unit = _Unit(tool, source, includes, defines, summaries, semantics)
    node = unit.function_node(function, None, None, unit=True)
    mangled = node.get("mangledName", function)
    if mangled.startswith(("_ZN", "__ZN")):
        raise Unsupported(f"function {function} inside a namespace or class")
    if _children_kind(node, "TemplateArgument"):
        raise Unsupported(f"function template {function} as the proof unit")
    unit.lower_function(node, function, None, None)
    definitions, definition_nodes = {}, {}
    while unit.pending:
        cname, fnode, owner = unit.pending.pop(0)
        definitions[cname] = _define(unit, cname, fnode, owner)
        definition_nodes[cname] = fnode
        for global_name in definitions[cname][1].globals:
            if global_name not in unit.globals:
                unit.globals.append(global_name)
                unit.global_text[global_name] = _global(unit, global_name)
    order = _callees_first(function, definitions)
    lines = [f"/* C lowering of {function} from {source.name} (sha256 {_file_sha256(source)}) by {TOOL_ID} "
             f"{TOOL_VERSION} ({NAMING_RULES}), clang {tool.version}. Generated: do not edit. */"]
    if defines:
        lines.append(f"/* Build constants: {', '.join(defines)} */")
    headers = list(HEADERS) + (["#include <stdlib.h>"] if unit.needs_stdlib else [])
    lines += headers
    types = [f"typedef struct {cname} {cname};" for cname, _ in unit.struct_order]
    for cname, fields in unit.struct_order:
        types.append(f"struct {cname} {{ {' '.join(fields)} }};")
    lines += types
    anchors = []
    lines.append(ANCHOR.format("ghost.globals"))
    anchors.append({"id": "ghost.globals", "kind": "ghost_globals", "function": None, "line": len(lines)})
    globals_text = [unit.global_text[name] for name in unit.globals]
    lines += globals_text
    for model in unit.model_order:
        lines += unit.models[model].splitlines()
    lines += [f"{text};" for text in unit.prototypes_only.values()]
    lines += [f"{definitions[name][0]};" for name in order]
    for name in order:
        prototype, printer = definitions[name][:2]
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
    unit_prototype, unit_params = definitions[function][0], definitions[function][2]
    declaration = "\n".join([*headers, *types, *globals_text, f"{unit_prototype};"]) + "\n"
    text = "\n".join(lines) + "\n"
    from swdb import array_domains as domain_policy
    try:
        windows = domain_policy.bind(array_domains, unit_params) if array_domains else None
    except domain_policy.Refused as exc:
        raise Unsupported(str(exc)) from None
    certificate = terminal_release.certify(node, source=source.read_text(), source_sha256=_file_sha256(source),
                                            models=unit.model_order, anchors=anchors, text=text)
    owner = vector_ownership.certify_origins(node, source=source.read_text(), source_sha256=_file_sha256(source),
                                           models=unit.model_order, anchors=anchors, text=text, entry_windows=windows)
    from swdb import member_windows
    member_context, member_origins, member_refusal = None, {}, None
    if not owner:
        try:
            member_context, member_origins = member_windows.certify(
                definition_nodes, unit.classes, source=source, tool=tool, includes=includes, defines=defines,
                entry=function, windows=windows)
        except member_windows.Refused as exc:
            member_refusal = str(exc)
    models = tuple(n for n in unit.model_order if n != "SWDB_MODEL_FAIL" and not n.endswith("_valid"))
    allocation = unit.allocates or any(n.startswith("std_vector_") for n in unit.std_types) or any(n.startswith("swdb_alloc_new_array_") for n in unit.model_order)
    provenance_models = sorted(set((*models, *unit.std_types)))
    provenance = (stdlib_provenance.certify(tool, source, includes=includes, defines=defines,
                                          models=provenance_models, substitutions=unit.stdlib_substitutions)
                  if stdlib_provenance.needed(provenance_models, allocation) else {})
    from swdb import vector_reallocation_calls
    candidate = vector_reallocation_calls.certify(node, source=source.read_bytes().decode('utf-8'), text=text,
                    defines=defines, models=models, provenance=provenance)
    return Lowering(function=function, text=text, anchors=tuple(anchors), declaration=declaration,
                    parameters=tuple(unit_params), source_sha256=_file_sha256(source), defines=defines,
                    tool={"id": TOOL_ID, "version": TOOL_VERSION, "naming_rules": NAMING_RULES,
                          "naming_rules_sha256": RULES_SHA256, "clang": tool.version},
                    summaries=tuple(unit.summaries_used), models=models, probes=tuple(unit.probes),
                    std_models=tuple(sorted(unit.std_types)), allocation=allocation, stdlib_provenance=provenance,
                    stdlib_substitutions=tuple(unit.stdlib_substitutions),
                    vector_reallocation_candidate=candidate,
                    cpu_effects=cpu_effects.collect(definition_nodes, unit.probe_nodes, unit.models,
                                                    unit.summaries_used, INTEGER_TYPES | FLOAT_TYPES),
                    bounded_initialization=bounded_initialization.analyze(definition_nodes,
                        scalar_types=INTEGER_TYPES | FLOAT_TYPES, source_sha256=_file_sha256(source), text=text,
                        external_calls=unit.summaries_used, standard_types=unit.std_types),
                    pointer_bounds=wp_pointer_bounds.inventory(
                        wp_pointer_bounds.complete(unit.pointer_sites, definition_nodes, unit.pointer_nodes,
                            external_calls=unit.summaries_used,
                            known_pointer_calls=(semantics or {}).get("tile_pointer", ()),
                            global_nodes=unit.global_nodes.values(), known_origins=(semantics or {}).get("array_origins"),
                            terminal=certificate, entry_windows=windows, entry_function=function, owner=owner,
                            standard_calls=unit.standard_range_calls, member_origins=member_origins,
                            member_refusal=member_refusal,
                            call_sites=unit.pointer_calls, call_policies=(semantics or {}).get("array_call_policies"),
                            audited_imports=(semantics or {}).get("audited_imports")),
                        source_sha256=_file_sha256(source), text=text, entry_windows=windows,
                        entry_contract=array_domain_contract, owner=owner, member_context=member_context,
                        source_entries=wp_pointer_bounds.function_entries(definition_nodes, source)),
                    terminal_release=certificate)


def _callees_first(function, definitions):
    order, seen = [], set()

    def visit(name):
        seen.add(name)
        for callee in definitions[name][3]:
            if callee not in seen and callee in definitions:
                visit(callee)
        order.append(name)

    visit(function)
    order += [name for name in definitions if name not in seen]
    return order


def _define(unit, cname, node, owner):
    """(prototype, printer, parameters, callees) of one lowered function, method, constructor or destructor."""
    printer = _Printer(cname, unit)
    printer.source_declaration = node
    printer._at(node)
    line = printer.line
    kind = node.get("kind")
    _function_attributes(node, line)
    if node.get("variadic"):
        raise Unsupported(f"variadic function {node.get('name')}", line)
    if node.get("isDeleted") or (node.get("explicitlyDefaulted") and kind != "CXXDestructorDecl"):
        raise Unsupported(f"special function {node.get('name')}", line)
    params, texts, unnamed = [], [], 0
    if owner and node.get("storageClass") != "static":
        const = "const " if re.search(r"\)\s*const\b", _qual(node)) else ""
        texts.append(f"{const}{owner} *this")
    for param in [c for c in _children(node) if c.get("kind") == "ParmVarDecl"]:
        name = param.get("name")
        if not name:
            unnamed += 1
            name = f"swdb_unnamed_{unnamed}"
        name = _name(name, line)
        qual, desugared = _types(param)
        if qual.rstrip().endswith("&"):
            printer.ref_ids.add(param.get("id"))
        texts.append(unit.ctype(qual, desugared, name, line))
        parameter_type = unit.ctype(qual, desugared, "", line)
        params.append((name, parameter_type, '*' in parameter_type))
    printer.local_ids.update(p.get("id") for p in _children(node) if p.get("kind") == "ParmVarDecl")
    if kind in ("CXXConstructorDecl", "CXXDestructorDecl"):
        returns = "void"
    else:
        returns_text, _, _ = _return_and_params(_qual(node), line)
        printer.returns_ref = returns_text.rstrip().endswith("&")
        returns = unit.ctype(returns_text, None, "", line)
        printer.returns_ctype = returns
    head = "static " if node.get("storageClass") == "static" and not owner else ""
    prototype = f"{head}{_join(returns, cname)}({', '.join(texts) or 'void'})"
    printer.anchor(f"{cname}.entry", "entry", 1)
    if kind == "CXXConstructorDecl":
        _member_inits(printer, node, owner)
    bodies = [c for c in _children(node) if c.get("kind") == "CompoundStmt"]
    if not bodies:
        raise Unsupported(f"function {node.get('name')} with no body", line)
    if unit.semantics:                                       # ticket 27: before printing, which reads them
        printer.tile_vars = _tile_vars(printer, bodies[0])
    try:
        printer.body(bodies[0], 1)
    except _CopyInit:
        raise Unsupported("a class object copied in an expression", printer.line) from None
    return prototype, printer, params, printer.calls


def _member_inits(printer, node, owner):
    for init in [c for c in _children(node) if c.get("kind") == "CXXCtorInitializer"]:
        target = init.get("anyInit") or {}
        if target.get("kind") != "FieldDecl":
            raise Unsupported(f"constructor initializer of a base class or delegating constructor of {owner}",
                              printer.line)
        name = _name(target.get("name"), printer.line)
        value = _children(init)[0] if _children(init) else None
        if value is None:
            continue
        stripped = _strip(value)
        field_qual = (target.get("type") or {}).get("qualType", "")
        if field_qual.rstrip().endswith("&"):
            printer.simple(f"this->{name} = {printer.address(value)};", 1)
        elif stripped.get("kind") == "CXXConstructExpr":
            try:
                call = printer.construct(stripped, f"this->{name}")
            except _CopyInit as copy:
                printer.simple(printer.copy_guard(copy) + " ;", 1)
                printer.simple(f"this->{name} = {copy.text};", 1)
                continue
            if call:
                printer.simple(call, 1)
        elif stripped.get("kind") in ("ImplicitValueInitExpr", "CXXScalarValueInitExpr", "InitListExpr"):
            parsed = _parse_type(field_qual, printer.line)
            if parsed.dims or not (_c_known(parsed.base) or parsed.pointers):
                raise Unsupported(f"value-initialized member {owner}::{name} that is not a scalar", printer.line)
            printer.simple(f"this->{name} = 0;", 1)
        else:
            printer.simple(f"this->{name} = {printer.expr(value, top=True)};", 1)


def _global(unit, name):
    nodes = [n for n in unit.dump(name) if n.get("kind") == "VarDecl" and n.get("name") == name and
             "mangledName" in n and not n.get("isImplicit")]
    definitions = [n for n in nodes if n.get("storageClass") != "extern"] or nodes
    if len({_where(n) for n in definitions}) != 1:
        raise Unsupported(f"global variable {name} (not one plain declaration)")
    node = definitions[0]
    unit.global_nodes[name] = node
    printer = _Printer(name, unit)
    printer._at(node)
    if node.get("tls"):
        raise Unsupported(f"thread-local global {name}", printer.line)
    qual, desugared = _types(node)
    if qual.rstrip().endswith("&"):
        raise Unsupported(f"global reference {name}", printer.line)
    head = "static " if node.get("storageClass") == "static" else ""
    text = head + unit.ctype(qual, desugared, _name(name, printer.line), printer.line)
    init = node.get("inner", [])
    if init:
        value = _strip(init[0])
        if value.get("kind") == "CXXConstructExpr":
            parsed = _parse_type(desugared or qual, printer.line)
            cname = unit.base_type(parsed.base, parsed.args, printer.line)
            cls = unit.classes.get(cname)
            if cls is None:
                raise Unsupported(f"global {name} built by a constructor", printer.line)
            ctors = [c for c in _children(cls) if c.get("kind") == "CXXConstructorDecl" and not c.get("isImplicit")]
            if ctors or _children(value):
                raise Unsupported(f"global {name} of class {cname} built by a constructor", printer.line)
            printer._trivial(cname, cls)
        else:
            text += " = " + printer.initializer(init[0], node.get("init"))
    if printer.callees or printer.globals:
        raise Unsupported(f"global {name} initialized from other functions or globals", printer.line)
    return text + ";"


# --- swdb lower ---------------------------------------------------------------------------------------

def register_cli(commands):
    sub = commands.add_parser("lower", help="C lowering of one C++ function in the declared subset (kept names, anchors)",
                              description="lower one C++ function in the declared C++ subset (and what it uses) to C "
                                          "with the C++ names kept and anchors for proof hints; write <function>.c and "
                                          "<function>.anchors.json into --out. Deterministic: the same input gives "
                                          "the same bytes.")
    sub.add_argument("--source", type=Path, required=True, help="the C++ file that defines the function")
    sub.add_argument("--function", required=True)
    sub.add_argument("--include", type=Path, action="append", default=[], help="an include folder (repeatable)")
    sub.add_argument("--define", action="append", default=[], help="a build constant NAME or NAME=VALUE (repeatable)")
    sub.add_argument("--summary", action="append", default=[],
                     help="NAME=SUMMARY: calls to function NAME stay calls, standing for SUMMARY (repeatable)")
    sub.add_argument("--out", type=Path, required=True, help="the folder to write into")
    sub.add_argument("--format", choices=["yaml", "json"], default="yaml")
    sub.set_defaults(analytic_handler=_cli)


def _cli(args):
    from swdb.cli import Failure
    summaries = {}
    for item in getattr(args, "summary", []) or []:
        name, _, summary = item.partition("=")
        if not name or not summary:
            raise Failure(f"--summary {item!r}: expected NAME=SUMMARY")
        summaries[name] = summary
    try:
        lowering = lower(args.source, args.function, args.include, args.define, summaries=summaries)
    except LoweringError as exc:
        raise Failure(str(exc)) from None
    c_path, a_path = lowering.write(args.out)
    out = {"function": lowering.function, "tool": lowering.tool,
           "c_lowering": {"path": str(c_path), "sha256": lowering.sha256},
           "anchors": {"path": str(a_path), "sha256": lowering.anchors_sha256, "count": len(lowering.anchors)}}
    if lowering.summaries:
        out["summaries"] = list(lowering.summaries)
    if lowering.models:
        out["models"] = list(lowering.models)
    if lowering.std_models:
        out["std_models"] = {**std_models.identity(), "types": list(lowering.std_models)}
    if lowering.allocation:
        out["allocation"] = True
    out["cpu_effects"] = lowering.cpu_effects
    out["bounded_initialization"] = lowering.bounded_initialization
    out["pointer_bounds"] = lowering.pointer_bounds
    if lowering.terminal_release:
        out["terminal_release"] = lowering.terminal_release
    if lowering.vector_reallocation_candidate:
        out["vector_reallocation_candidate"] = lowering.vector_reallocation_candidate
    return out
