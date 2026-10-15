"""Private vector copy/scan relation; created 2026-10-15 ET (ticket25).

This is a checked source-to-view relation, never an original allocating C-body proof.
Only canonical int/vector and int/int pair operations are admitted. Successful fresh
allocation and the exact pinned standard-library model remain explicit trust boundaries.
"""
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from swdb import std_models

PROTOCOL = "private-vector-copy-scan-1"
SOURCE_CLOSURE_SHA256 = "60cdfb05a7ed6b87dde1770e0def1e97bcdb7c8c59b25abb75de6914fe863a26"
MODEL_SHA256 = "cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2"
MODELS = {"std_vector_int_ctor", "swdb_alloc_int", "swdb_free", "std_vector_int_dtor",
          "std_vector_int_recommend", "std_vector_int_grow", "std_vector_int_push_back",
          "std_pair_int_int_ctor", "std_vector_int_begin", "std_vector_int_end",
          "std_vector_int_size", "std_vector_int_operator_index"}
MODEL_TEXT_SHA256 = {
    "std_pair_int_int_ctor": "7f000ab6ce06710ec0054bed42f16b045d4ef6b237c8d16b3feaa80b922ed335",
    "std_vector_int_begin": "5bd8c7629f3fd6d7653c9398b488431eb27847b9e5ff6a5bc650ae812634d297",
    "std_vector_int_ctor": "9e4b81e87ab91f0e51d686553615cdccf721a861203bb175d8bca8e7c1dee440",
    "std_vector_int_dtor": "1056f4f83c59a30941ec9417c36aada8eab4b62160087ae10315cd2ac9778317",
    "std_vector_int_end": "d7ba1f155627e243c1c293f6eaccf3cb42499a95b0ce24b1fd6cb53d8e93599d",
    "std_vector_int_grow": "dc2049fa6f88a958fb88aee1e0a401f584630e8c302ad2e60b069ced2b587b1b",
    "std_vector_int_operator_index": "7b3548b6db64e22cd6b39bd968b4bface472f01f0477731f82187e35e347718f",
    "std_vector_int_push_back": "117daefdfbc40c0674b222d0cbe010af8e74cc49b44a646149c206556311f6d0",
    "std_vector_int_recommend": "938e73d80a11583b092a2a4d6944b6a5e2d3e67c5b447680899a26a576eb5936",
    "std_vector_int_size": "4842b64d109b55b6f26f3261845316b4a9d32c88a7aa01186c343f9ed7e03329",
    "swdb_alloc_int": "eb1f5833017762a8d83cc477b6d35e604be6906ebe70b7c0ba56abf032fa03b0",
    "swdb_free": "e301a232920b9439f2db75cccc278276c1e74ba760cbd9ca2ae7958210b401d4"
}
BODY = """{
  std::vector<int> v;
  for (int i=0; i<n; ++i) v.push_back(a[i]);
  std::pair<int,int> best(0,0);
  for (int x:v) {
    if (best.first==0 || x > best.second) { best.first=1; best.second=x; }
  }
  int checked=0;
  for (std::size_t i=0; i<v.size(); ++i) if (v[i]<=best.second) ++checked;
  return checked==n ? best.second : -1000;
}"""


class Refused(ValueError):
    pass


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")))


def identity():
    return {"id": PROTOCOL, "sha256": _sha(Path(__file__).read_bytes())}


def _children(node):
    return [c for c in node.get("inner", []) if isinstance(c, dict) and c.get("kind")]


def _walk(node):
    yield node
    for child in _children(node):
        yield from _walk(child)


def _span(node):
    from swdb import model_domains
    return model_domains.span(node)


def _tokens(text):
    # Tokenize before discarding whitespace: '+ +' must not turn into '++'.
    pattern = r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|//[^\n]*|/\*.*?\*/|::|\+\+|--|<=|>=|==|!=|\|\||&&|[A-Za-z_]\w*|\d+|[^\s]'''
    return tuple(m.group() for m in re.finditer(pattern, text, re.S)
                 if not m.group().startswith(("//", "/*")))


def _protocol(node, source):
    from swdb import model_domains
    if std_models.identity()["sha256"] != MODEL_SHA256:
        raise Refused("private vector pipeline needs a new exact model-content audit")
    directives = re.findall(r"^\s*#.*$", source, re.M)
    if any(not re.fullmatch(r"\s*#\s*include\s*<(?:vector|utility|cstddef)>\s*", d) for d in directives):
        raise Refused("pipeline source closure permits only canonical standard headers, no macros or injected headers")
    tokens = _tokens(source)
    if (any(t in {"set_new_handler", "get_new_handler", "class", "struct", "union", "namespace", "asm", "__asm__", "malloc", "calloc", "realloc", "free", "aligned_alloc", "posix_memalign", "__malloc_hook", "__free_hook"} for t in tokens)
            or any(tokens[i] == "operator" and tokens[i+1] in {"new", "delete"} for i in range(len(tokens)-1))):
        raise Refused("allocation hooks, custom types/namespaces and assembly need a separate observability model")
    params = [n for n in _children(node) if n.get("kind") == "ParmVarDecl"]
    if [(p.get("name"), (p.get("type") or {}).get("qualType")) for p in params] != [("a", "const int *"), ("n", "int")]:
        raise Refused("pipeline requires the exact const-int input window and scalar count signature")
    body = next((n for n in _children(node) if n.get("kind") == "CompoundStmt"), {})
    statements = _children(body)
    if [n.get("kind") for n in statements] != ["DeclStmt", "ForStmt", "DeclStmt", "CXXForRangeStmt", "DeclStmt", "ForStmt", "ReturnStmt"]:
        raise Refused("pipeline has a changed phase, hidden effect or escaping object")
    spelling = source[slice(*_span(body))]
    comparison = next((op for op in (">", "<") if _tokens(spelling) == _tokens(BODY.replace("x > best.second", "x "+op+" best.second"))), None)
    if comparison is None:
        raise Refused("only the exact canonical input-copy, pair scan and size/index scan grammar is admitted")
    start, end = _span(body)
    closure = _digest(_tokens(source[:start]+BODY+source[end:]))
    if closure != SOURCE_CLOSURE_SHA256:
        raise Refused("pipeline needs its exact full source-token closure; extra declarations or allocation hooks are unsupported")
    vector = _children(statements[0])[0]
    pair = _children(statements[2])[0]
    if ((vector.get("type") or {}).get("qualType") != "std::vector<int>"
            or (pair.get("type") or {}).get("qualType") != "std::pair<int, int>"):
        raise Refused("custom allocator/element/pair template specializations are outside the audited relation")
    # Raw spelling alone is insufficient: bind the input read and push to their
    # actual declarations, types and call AST, including a const-reference argument.
    array_reads = [n for n in _walk(body) if n.get("kind") == "ArraySubscriptExpr"]
    pushes = [n for n in _walk(body) if n.get("kind") == "CXXMemberCallExpr"
              and _children(n) and _children(n)[0].get("name") == "push_back"]
    if len(array_reads) != 1 or len(pushes) != 1:
        raise Refused("pipeline input-copy needs exactly one typed source read and append site")
    read, push = array_reads[0], pushes[0]
    base = model_domains.strip(_children(read)[0])
    member = _children(push)[0]
    receiver = model_domains.strip(_children(member)[0])
    if ((base.get("referencedDecl") or {}).get("id") != params[0].get("id")
            or (receiver.get("referencedDecl") or {}).get("id") != vector.get("id")
            or (read.get("type") or {}).get("qualType") != "const int"):
        raise Refused("pipeline append/read observes a different input, receiver or element type")
    return {"comparison": comparison, "function": node["name"],
            "owner": {"name": "v", "begin": _span(vector)[0], "end": _span(vector)[1]},
            "input": {"name": "a", "begin": _span(params[0])[0], "end": _span(params[0])[1]},
            "phases": [{"kind": kind, "begin": _span(statements[i])[0], "end": _span(statements[i])[1]}
                       for i, kind in ((1, "pipeline_copy"), (3, "pipeline_range"), (5, "pipeline_index"))],
            "read_span": list(_span(read)), "push_span": list(_span(push)),
            "source_closure_sha256": closure,
            "closure": "exact full fixture source-token closure plus target AST; canonical int/pair types, no source allocation hooks, macros, user headers, namespaces or opaque effects"}


def _window(windows):
    return bool(windows and set(windows.get("windows", {})) == {"a"}
                and windows["windows"]["a"].get("element_type") == "int"
                and windows["windows"]["a"].get("extent_tree") == {"kind": "parameter", "name": "n"})


def _model_text(name):
    from swdb import c_lowering
    return dict(std_models.allocator("int")).get(name) or c_lowering.model_text(name)


def certify(node, *, source, source_sha256, models, anchors, text, entry_windows, owner_check):
    from swdb import c_lowering, model_domains
    if not _window(entry_windows) or _sha(source) != source_sha256:
        raise Refused("private vector pipeline requires the explicitly declared entry a:n typed window")
    protocol = _protocol(node, source)
    names = set(models) - {"SWDB_MODEL_FAIL", "std_vector_int_valid"}
    if names != MODELS:
        raise Refused("pipeline source uses a changed or unmodeled standard operation")
    if any(_sha(_model_text(name)) != MODEL_TEXT_SHA256[name] for name in names):
        raise Refused("pipeline model contract/body needs a new exact per-member audit")
    eligibility = [{"id": name, "sha256": _sha(_model_text(name)),
                    "eligibility": "checked closed-pipeline transition only",
                    "standalone_body_proof": False,
                    "standalone_requirement": (
                        "imported allocator contract only; not WP allocation-body evidence" if name in {"swdb_alloc_int","swdb_free"} else
                        "WP33 lifetime/fresh-frame support or separately qualified relational model proof" if name in {
                            "std_vector_int_dtor","std_vector_int_grow","std_vector_int_push_back"} else
                        "explicit incoming typed-owner domain and caller discharge" if name in {
                            "std_vector_int_begin","std_vector_int_end","std_vector_int_operator_index"} else
                        "separate original C-body proof under its unchanged formal domain"),
                    "required_domain": "private int-vector initialized copy prefix; immutable post-copy scan",
                    "allocation_boundary": "successful fresh allocation" if name in {
                        "swdb_alloc_int", "swdb_free", "std_vector_int_grow", "std_vector_int_push_back", "std_vector_int_dtor"} else "none"}
                   for name in sorted(names)]
    accesses = [{**phase, "allocation_site": "logical-copy-prefix", "bounds_guard": phase["kind"]+"_range",
                 "liveness_guard": "no captured alias survives a source append; scans have an immutable owner"}
                for phase in protocol["phases"]]
    out = {"protocol": PROTOCOL, "check": model_domains.identity(), "pipeline_check": identity(),
           "owner_check": owner_check, "source_sha256": source_sha256, "lowering_sha256": _sha(text),
           "function": node["name"], "owner": protocol["owner"], "source_accesses": accesses,
           "source_protocol": protocol, "entry_windows": entry_windows, "model": std_models.identity(),
           "model_eligibility": eligibility, "anchors_sha256": _digest(list(anchors)),
           "allocation_executions": "unbounded; projected, never a finite pool",
           "projection": "v[k] equals unchanged input a[k]; addresses and allocation events have no admitted observation"}
    out["certificate_sha256"] = _digest(out)
    return out


def bind_access(root, certificate, access):
    kinds = {"pipeline_copy": "ForStmt", "pipeline_range": "CXXForRangeStmt", "pipeline_index": "ForStmt"}
    matches = [n for n in _walk(root) if n.get("kind") == kinds.get(access.get("kind"))
               and _span(n) == (access["begin"], access["end"])]
    if certificate.get("pipeline_check") != identity() or len(matches) != 1:
        raise Refused("pipeline phase has no exact current source AST binding")
    return matches[0]


def checked_handles(root, certificate, entry_windows):
    """Core seam: exact source IDs, never persisted IDs or a generic call waiver."""
    saved = dict(certificate)
    digest = saved.pop("certificate_sha256", None)
    if (digest != _digest(saved) or root.get("name") != certificate.get("function")
            or certificate.get("model") != std_models.identity()
            or certificate.get("source_protocol", {}).get("source_closure_sha256") != SOURCE_CLOSURE_SHA256):
        raise Refused("pipeline source/model/closure certificate changed before exact-ID binding")
    if certificate.get("protocol") != PROTOCOL or not _window(entry_windows) or certificate.get("entry_windows") != entry_windows:
        raise Refused("pipeline needs its exact explicit input window")
    body = next(n for n in _children(root) if n.get("kind") == "CompoundStmt")
    reads = [n for n in _walk(body) if n.get("kind") == "ArraySubscriptExpr"
             and list(_span(n)) == certificate["source_protocol"]["read_span"]]
    calls = [n for n in _walk(body) if n.get("kind") == "CXXMemberCallExpr"
             and list(_span(n)) == certificate["source_protocol"]["push_span"]]
    if certificate.get("pipeline_check") != identity() or len(reads) != 1 or len(calls) != 1:
        raise Refused("pipeline source copy read/append identity changed")
    for access in certificate["source_accesses"]:
        bind_access(root, certificate, access)
    return {"accesses": {reads[0]["id"]}, "calls": {calls[0]["id"]}}


def _render(lowering, comparison):
    # Every original anchor is retained exactly once. Hints are refused: original
    # iterator/local names cannot acquire arbitrary scope in this relational view.
    globals_anchor = "/* swdb-anchor ghost.globals */"
    contract = "/* swdb-anchor "+lowering.function+".contract */"
    entry = "/* swdb-anchor "+lowering.function+".entry */"
    others = "\n".join("/* swdb-anchor "+a["id"]+" */" for a in lowering.anchors
                       if a["id"] not in {"ghost.globals", lowering.function+".contract", lowering.function+".entry"})
    return "\n".join(["#include <stddef.h>", "#include <stdint.h>", "#include <limits.h>",
        "struct swdb_pipeline_pair { int first; int second; };", globals_anchor, contract,
        "int "+lowering.function+"(const int *a,int n) {", entry, others,
        "  /*@ assert pipeline_count: 0 <= n; */",
        "  int swdb_pipeline_copy=0;",
        "  /*@ loop invariant 0 <= swdb_pipeline_copy <= n;",
        "      loop assigns swdb_pipeline_copy; loop variant n-swdb_pipeline_copy; */",
        "  for(swdb_pipeline_copy=0;swdb_pipeline_copy<n;++swdb_pipeline_copy) {",
        "    /*@ assert pipeline_copy_range: 0 <= swdb_pipeline_copy < n; */",
        "    /*@ assert pipeline_copy_initialized: \\initialized(a+swdb_pipeline_copy); */",
        "    int swdb_pipeline_value=a[swdb_pipeline_copy]; }",
        "  struct swdb_pipeline_pair best={0,0};",
        "  int swdb_pipeline_range=0;",
        "  /*@ loop invariant 0 <= swdb_pipeline_range <= n;",
        "      loop invariant \\initialized(&best);",
        "      loop invariant best.first == (swdb_pipeline_range == 0 ? 0 : 1);",
        "      loop invariant swdb_pipeline_range == 0 ==> best.second == 0;",
        "      loop invariant \\forall integer k; 0 <= k < swdb_pipeline_range ==> a[k] <= best.second;",
        "      loop invariant swdb_pipeline_range > 0 ==> \\exists integer k; 0 <= k < swdb_pipeline_range && a[k] == best.second;",
        "      loop assigns swdb_pipeline_range,best.first,best.second; loop variant n-swdb_pipeline_range; */",
        "  for(swdb_pipeline_range=0;swdb_pipeline_range<n;++swdb_pipeline_range) {",
        "    /*@ assert pipeline_range_range: 0 <= swdb_pipeline_range < n; */",
        "    int x=a[swdb_pipeline_range];",
        "    if(best.first==0 || x "+comparison+" best.second) {best.first=1;best.second=x;} }",
        "  int checked=0; size_t swdb_pipeline_index=0;",
        "  /*@ loop invariant 0 <= swdb_pipeline_index <= n;",
        "      loop invariant checked == (integer)swdb_pipeline_index;",
        "      loop assigns swdb_pipeline_index,checked; loop variant n-swdb_pipeline_index; */",
        "  for(swdb_pipeline_index=0;swdb_pipeline_index<(size_t)n;++swdb_pipeline_index) {",
        "    /*@ assert pipeline_index_range: 0 <= swdb_pipeline_index < n; */",
        "    if(a[swdb_pipeline_index]<=best.second) ++checked; }",
        "  return checked==n ? best.second : -1000;", "}", ""])


def _view_check(text, protocol, directory):
    """Independent C-AST inventory: exact effects/bindings and a closed annotation set."""
    from swdb import c_lowering, model_domains
    path = Path(directory) / "pipeline-view-ast.c"
    path.write_text(text)
    result = subprocess.run([*c_lowering.locate().command, "-x", "c", "-std=c11", "-fsyntax-only",
                             "-Xclang", "-ast-dump=json", str(path)], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise Refused("pipeline view is not independently parseable C")
    ast = json.loads(result.stdout)
    definitions = [n for n in _walk(ast) if n.get("kind") == "FunctionDecl"
                   and any(c.get("kind") == "CompoundStmt" for c in _children(n))]
    if len(definitions) != 1 or definitions[0].get("name") != protocol["function"]:
        raise Refused("pipeline view has an untracked function/call")
    params = [n for n in _children(definitions[0]) if n.get("kind") == "ParmVarDecl"]
    if [(n.get("name"),(n.get("type") or {}).get("qualType")) for n in params] != [("a","const int *"),("n","int")]:
        raise Refused("pipeline C view changed its original signature")
    prefix = text.partition("/* swdb-anchor ghost.globals */")[0]
    expected_prefix = "#include <stddef.h>\n#include <stdint.h>\n#include <limits.h>\nstruct swdb_pipeline_pair { int first; int second; };\n"
    if prefix != expected_prefix:
        raise Refused("pipeline C view has a changed layout/global declaration")
    body = next(n for n in _children(definitions[0]) if n.get("kind") == "CompoundStmt")
    top = _children(body)
    if [n.get("kind") for n in top] != ["DeclStmt", "ForStmt", "DeclStmt", "DeclStmt", "ForStmt", "DeclStmt", "DeclStmt", "ForStmt", "ReturnStmt"]:
        raise Refused("pipeline view has an untracked phase/effect")
    raw = text.encode()
    expression = lambda n: _tokens(raw[slice(*_span(n))].decode())
    declarations = {n.get("name"): n for n in _walk(body) if n.get("kind") == "VarDecl"}
    initial = {"swdb_pipeline_copy": "0", "best": "{0,0}", "swdb_pipeline_range": "0",
               "checked": "0", "swdb_pipeline_index": "0", "swdb_pipeline_value": "a[swdb_pipeline_copy]", "x": "a[swdb_pipeline_range]"}
    if len([n for n in _walk(body) if n.get("kind") == "VarDecl"]) != len(initial) or set(declarations) != set(initial):
        raise Refused("pipeline view has an untracked local/shadow")
    for name, expected in initial.items():
        values = _children(declarations[name])
        if len(values) != 1 or expression(values[0]) != _tokens(expected):
            raise Refused("pipeline view initializer changes source values or roots")
    expected_bodies = {1: "{int swdb_pipeline_value=a[swdb_pipeline_copy];}",
        4: "{int x=a[swdb_pipeline_range];if(best.first==0||x"+protocol["comparison"]+"best.second){best.first=1;best.second=x;}}",
        7: "{if(a[swdb_pipeline_index]<=best.second)++checked;}"}
    for at, variable, stop in ((1,"swdb_pipeline_copy","n"),(4,"swdb_pipeline_range","n"),(7,"swdb_pipeline_index","(size_t)n")):
        parts = _children(top[at])
        if (len(parts) != 4 or [expression(n) for n in parts[:3]] != [_tokens(variable+"=0"), _tokens(variable+"<"+stop), _tokens("++"+variable)]
                or expression(parts[3]) != _tokens(expected_bodies[at])):
            raise Refused("pipeline view loop/branch no longer matches the source transition")
    if expression(_children(top[-1])[0]) != _tokens("checked==n?best.second:-1000"):
        raise Refused("pipeline result observation changed")
    if any(n.get("kind") == "CallExpr" for n in _walk(body)):
        raise Refused("pipeline view has an opaque call")
    # Guards must precede the actual access inside its loop, never merely occur
    # before the loop or as an assumption. All other annotations are generated
    # proof obligations; no ghost mutation, assumes, requires or axioms.
    annotations = re.findall(r"/\*@\s*(.*?)\*/", text, re.S)
    if "//@" in text or text.count("/*@") != len(annotations):
        raise Refused("pipeline has an untracked annotation form")
    assertions = {m.group(1):(m.start(),m.end(),_tokens(m.group(2))) for m in
                  re.finditer(r"/\*@\s*assert\s+(\w+)\s*:\s*(.*?);\s*\*/", text, re.S)}
    if len(assertions) != 5 or sum(a.lstrip().startswith("assert ") for a in annotations) != 5:
        raise Refused("pipeline guard inventory changed")
    loops = [a for a in annotations if a.lstrip().startswith("loop invariant ")]
    if len(loops) != 3 or any(re.search(r"\b(?:requires|assumes|axiom|ghost|ensures)\b", a) for a in annotations):
        raise Refused("pipeline accepts only checked assertions and loop proof obligations")
    for a in annotations:
        if not (a.lstrip().startswith("assert ") or a.lstrip().startswith("loop invariant ")):
            raise Refused("pipeline has an untracked ACSL effect")
    expected_loops = [
        "loop invariant 0 <= swdb_pipeline_copy <= n; loop assigns swdb_pipeline_copy; loop variant n-swdb_pipeline_copy;",
        r"loop invariant 0 <= swdb_pipeline_range <= n; loop invariant \initialized(&best); "
        r"loop invariant best.first == (swdb_pipeline_range == 0 ? 0 : 1); "
        r"loop invariant swdb_pipeline_range == 0 ==> best.second == 0; "
        r"loop invariant \forall integer k; 0 <= k < swdb_pipeline_range ==> a[k] <= best.second; "
        r"loop invariant swdb_pipeline_range > 0 ==> \exists integer k; 0 <= k < swdb_pipeline_range && a[k] == best.second; "
        "loop assigns swdb_pipeline_range,best.first,best.second; loop variant n-swdb_pipeline_range;",
        "loop invariant 0 <= swdb_pipeline_index <= n; loop invariant checked == (integer)swdb_pipeline_index; "
        "loop assigns swdb_pipeline_index,checked; loop variant n-swdb_pipeline_index;"]
    located_loops = [(m.start(),m.end(),m.group(1)) for m in re.finditer(r"/\*@\s*(loop invariant.*?)\*/",text,re.S)]
    if len(located_loops) != 3:
        raise Refused("pipeline loop annotation inventory changed")
    for (begin,end,annotation),expected,at in zip(located_loops,expected_loops,(1,4,7)):
        if (_tokens(annotation) != _tokens(expected) or not _span(top[at-1])[1] < begin < end < _span(top[at])[0]):
            raise Refused("pipeline loop obligations/effects changed or moved phase")
    count = assertions.get("pipeline_count",(0,0,()))
    initialized = assertions.get("pipeline_copy_initialized",(0,0,()))
    copy_body = _children(top[1])[-1]
    copy_read = next(n for n in _walk(copy_body) if n.get("kind") == "ArraySubscriptExpr")
    if (count[2] != _tokens("0 <= n") or not count[1] < _span(top[0])[0]
            or initialized[2] != _tokens(r"\initialized(a+swdb_pipeline_copy)")
            or not _span(copy_body)[0] < initialized[0] < initialized[1] < _span(copy_read)[0]):
        raise Refused("pipeline count/initializedness obligations changed or moved")
    accesses = []
    for node in _walk(body):
        if node.get("kind") != "ArraySubscriptExpr":
            continue
        base, index = _children(node)
        if model_domains.reference(base) != "a":
            raise Refused("pipeline read does not name its typed input")
        name = model_domains.reference(index)
        if name not in {"swdb_pipeline_copy", "swdb_pipeline_range", "swdb_pipeline_index"}:
            raise Refused("pipeline read offset changed")
        phase = name.removeprefix("swdb_pipeline_")
        guard = "pipeline_"+phase+"_range"
        start,end,predicate = assertions.get(guard,(0,0,()))
        loop = top[{"copy":1,"range":4,"index":7}[phase]]
        block = _children(loop)[-1]
        if not (_span(block)[0] < start < end < _span(node)[0] and predicate == _tokens("0 <= "+name+" < n")):
            raise Refused("pipeline access lacks its exact in-loop numerical guard")
        accesses.append({"phase":phase,"origin":"entry:a","bounds_guard":guard,"source_projection":"immutable vector initialized copy prefix"})
    if len(accesses) != 3:
        raise Refused("pipeline source/view reads differ")
    return {"check":identity(),"complete":True,"view_sha256":_sha(text),"view_accesses":accesses,
            "boundary":"exact private-copy phase relation; no generic field origin or C-model body proof"}


def wp_view(lowering, source, formal_texts, hints):
    from swdb import c_lowering, vector_ownership
    if hints or lowering.defines or lowering.summaries or lowering.probes:
        raise Refused("pipeline hints/preprocessing/opaque effects need a separate relational audit")
    planned = (lowering.pointer_bounds or {}).get("owner") or {}
    if planned.get("protocol") != PROTOCOL or not _window(planned.get("entry_windows")):
        raise Refused("pipeline needs its generator-owned explicit input-domain certificate")
    source = Path(source)
    unit = c_lowering._Unit(c_lowering.locate(), source, (), (), {}, None)
    node = unit.function_node(lowering.function, None, None, unit=True)
    cert = certify(node, source=source.read_text(), source_sha256=lowering.source_sha256,
        models=lowering.models, anchors=lowering.anchors, text=lowering.text,
        entry_windows=planned["entry_windows"], owner_check=vector_ownership.identity())
    if cert != planned:
        raise Refused("pipeline source/model/window certificate changed")
    checked = c_lowering.lower(source, lowering.function, array_domains={"a":{"extent":"n"}},
        array_domain_contract=lowering.pointer_bounds.get("entry_contract"))
    if checked != lowering:
        raise Refused("pipeline source inventory differs from fresh lowering")
    formal = "\n".join(formal_texts)
    if len(re.findall(r"assigns\s+\\nothing\s*;", formal)) != 1 or len(re.findall(r"\bassigns\b",formal)) != 1:
        raise Refused("private pipeline requires the unchanged original assigns nothing frame")
    text = _render(lowering, cert["source_protocol"]["comparison"])
    with tempfile.TemporaryDirectory(prefix="swdb-vector-pipeline-") as folder:
        origins = _view_check(text, cert["source_protocol"], folder)
    certificate = {"protocol":PROTOCOL,"source_origins":cert,"origins":origins,
        "source_sha256":lowering.source_sha256,"original_c_sha256":lowering.sha256,
        "original_contract_sha256":_sha(formal),"view_contract_sha256":_sha(formal),
        "view_sha256":_sha(text),"source_frame":r"assigns \nothing;","view_frame":r"assigns \nothing;",
        "source_frame_preservation":"checked: input unchanged, pair/control local, vector writes fresh nonescaping storage",
        "model_eligibility":cert["model_eligibility"],"allocation_executions":cert["allocation_executions"],
        "input_premises_added":[],"projection":cert["projection"]}
    pins = {"vector_pipeline_check":identity(),"vector_ownership_check":vector_ownership.identity(),
            "vector_ownership_certificate":{"id":lowering.function+".private-vector-copy-scan","sha256":_digest(certificate)},
            "vector_pipeline_allocator":{"id":"swdb_alloc_int","sha256":MODEL_TEXT_SHA256["swdb_alloc_int"]}}
    assumptions = ({"kind":"trusted_tool","reference":pins["vector_pipeline_allocator"],"sentence":
        "Allocation succeeds under the pinned allocation-model contract, including its frame: successful allocation "
        "and library growth leave preexisting input unchanged. Source-defined allocation/deallocation overrides, "
        "handler registrations, custom allocator/element effects and extra source closure are refused. This imported "
        "allocator-frame premise is explicit and is not a WP-supported allocation-lifetime fact."},
        {"kind":"trusted_tool","reference":identity(),"sentence":
        "The exact checked private int-vector copy/scan relation preserves each appended input value, scalar result "
        "and original frame. Successful fresh allocation separates source vector storage from preexisting input; "
        "no allocation hook, custom element, escaped alias or observable source address is admitted. Allocation "
        "count is unbounded and no finite pool is used. WP proves the checked view, not original allocating model bodies."},)
    return vector_ownership.View(text,(),formal,certificate,pins,assumptions,{})
