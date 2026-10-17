"""Proof-semantics entries: their checks in `swdb validate`, the call inventory, and the C model a bounded job uses.

Created: 2026-10-14 ET (Probata proof of concept ticket 27). Design: formal-verification map 12 items 1-5 and 11
(the DX100 proof semantics: values at issue, hazards, gem5 citations or an owner), map 14 (the wait rule),
map 16 item 10 (one ghost state, declared once), S3 (ghost capacity K). Format:
docs/reference/format-v0.4-proof-semantics.md. Ticket 20 added the entry kind (`library/proof_semantics/`,
prefix `semantics.`) and its `rules`; this module adds what an entry that covers calls carries:

- `hardware_interface: {id, version, gem5_commit}`: every rule citation names this gem5 commit;
- `calls`: one row per covered call (`call`, `prototype`, `contract` (ACSL), `rules`, `lowerings`, `used_by`);
- `inventory: {sources, calls}`: where the call list was read from (pinned files) and what it found;
- `ghost: {acsl}`: the ghost state, declared once in ACSL; `model: {state, c, logic}`: the device state, the
  C model (the CBMC form) and the logic definitions of the ACSL contracts (the WP form), all pinned;
- `constants`: default build constants of the model (sizes; `--define` overrides them);
- `queries`: ghost queries a fixture may call (not hardware calls), with their prototypes;
- `sequence` and `target`: the version line (the current version has the highest sequence; swdb.level_rule).

`model_for(library, names)` gives the bounded verifier what it needs: the C text of the model (generated
ghost globals, state, model), the call and query names the C lowering may leave undefined, and the pin.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from swdb import artifacts, yamlio

FOLDER = "proof_semantics"
GHOST_LINE = re.compile(r"^\s*ghost\s+(?P<decl>[^;]+);\s*(//.*)?$")
DECL_NAME = re.compile(r"\b([A-Za-z_]\w*)\s*(\[[^\]]*\]\s*)*$")
API = re.compile(r"\b(maa_\w+|wait_ready|get_tile_size|get_tile_ready|get_cacheable_tile_pointer|get_new_tile|"
                 r"get_new_reg|add_mem_region|clear_mem_region|get_reg|set_reg|alloc_MAA|init_MAA)\s*"
                 r"(?:<[^<>();]*>)?\s*\(")
DXC_CALL = re.compile(r"\b(__dxc_\w+)\s*(?:<[^<>();]*>)?\s*\(")
DXC_DEF = re.compile(r"\b(__dxc_\w+)\s*\([^)]*\)\s*\{")
TILE_POINTER = "get_cacheable_tile_pointer"
CAPACITY = "swdb.ghost_capacity"
MEMORY_DOMAIN = "swdb.dx100_memory_domain"


# --- the call inventory -----------------------------------------------------------------------------------------

def _without_strict(text):
    """The text with `#ifdef SWDB_STRICT` branches removed (their `#else` branch kept): strict-layer only calls."""
    out, stack = [], []
    for line in text.splitlines():
        stripped = line.lstrip("+").strip()
        if stripped.startswith("#if"):
            stack.append("strict" if re.match(r"#ifdef\s+SWDB_STRICT\b", stripped) else "other")
            if stack[-1] == "strict":
                continue
        elif stripped.startswith("#else") and stack and stack[-1] in ("strict", "strict-else"):
            stack[-1] = "strict-else"
            continue
        elif stripped.startswith("#endif") and stack:
            if stack.pop() in ("strict", "strict-else"):
                continue
        if "strict" in stack:
            continue
        out.append(line)
    return "\n".join(out)


def _body(text, start):
    """The text of the brace-delimited body that opens at or after `start`."""
    open_at = text.index("{", start)
    depth = 0
    for at in range(open_at, len(text)):
        if text[at] == "{":
            depth += 1
        elif text[at] == "}":
            depth -= 1
            if depth == 0:
                return text[open_at:at + 1]
    raise ValueError("unbalanced braces")


def inventory(library_root, sources):
    """The sorted dx100 API calls the listed sources make (ticket 27's call inventory).

    Source roles: `lowerings` (the dxc lowering header: each `__dxc_*` function maps to the API calls in its body),
    `offload` (code whose `__dxc_*` calls and direct API calls count), `setup` (a patch: only its added `__dxc_*`
    calls count), `function` (the API calls in one function's body). `#ifdef SWDB_STRICT` code (the strict layer,
    not the hardware interface) never counts."""
    texts = []
    for source in sources:
        base = {"library": Path(library_root), "project": _project(), "repository": _project().parent}[
            source.get("root", "library")]
        texts.append((source, _without_strict((base / source["path"]).read_text())))
    lowering = {}
    for source, text in texts:
        if source.get("role") == "lowerings":
            for match in DXC_DEF.finditer(text):
                lowering[match.group(1)] = {m.group(1) for m in API.finditer(_body(text, match.start()))}
    found, dxc = set(), set()
    for source, text in texts:
        role = source.get("role")
        if role == "offload":
            dxc |= {m.group(1) for m in DXC_CALL.finditer(text)} - {m.group(1) for m in DXC_DEF.finditer(text)}
            found |= {m.group(1) for m in API.finditer(text)}
        elif role == "setup":
            added = "\n".join(line[1:] for line in text.splitlines()
                              if line.startswith("+") and not re.match(r"\+\s*(inline|template)\b", line))
            dxc |= {m.group(1) for m in DXC_CALL.finditer(added)}
        elif role == "function":
            match = re.search(rf"\b{re.escape(source['function'])}\s*\([^)]*\)\s*\{{", text)
            if match is None:
                raise ValueError(f"{source['path']} defines no function {source['function']}")
            found |= {m.group(1) for m in API.finditer(_body(text, match.start()))}
    for name in dxc:
        found |= lowering.get(name, set())
    return sorted(found)


def _project():
    from swdb import paths
    return paths.HOME


# --- validate --------------------------------------------------------------------------------------------------

def ghost_declarations(text):
    """[(name, declaration without `ghost`)] of a ghost.acsl file, in order."""
    found = []
    for line in text.splitlines():
        match = GHOST_LINE.match(line)
        if match:
            decl = match.group("decl").strip()
            name = DECL_NAME.search(decl)
            if name:
                found.append((name.group(1), decl))
    return found


def check(library, entry_id, data, error):
    """The checks of an entry that covers calls (called by swdb.formal_frame for proof_semantics entries)."""
    from swdb import dx100_whole_checked
    if dx100_whole_checked.checked(data):
        return dx100_whole_checked.check(library, data, error)
    rules = {r.get("id") for r in data.get("rules") or [] if isinstance(r, dict)}
    interface = data.get("hardware_interface")
    calls = data.get("calls")
    if calls is None and interface is None:
        return []                                         # a rules-only entry (ticket 20's frame)
    if not isinstance(interface, dict) or set(interface) != {"id", "version", "gem5_commit"} or \
            not re.fullmatch(r"[0-9a-f]{40}", str(interface.get("gem5_commit"))) or \
            not str(interface.get("version", "")).endswith("-" + str(interface.get("gem5_commit"))[:7]):
        error("hardware_interface", "an entry that covers calls names its hardware interface: {id, version, "
                                    "gem5_commit} (the full commit; the version ends with its first 7 digits)")
        return []
    commit = interface["gem5_commit"]
    for i, rule in enumerate(data.get("rules") or []):
        cites = rule.get("cites") if isinstance(rule, dict) else None
        if isinstance(cites, dict) and not (len(str(cites.get("gem5_commit"))) >= 7 and
                                            commit.startswith(str(cites.get("gem5_commit")))):
            error(f"rules[{i}].cites", f"rule {rule.get('id')} cites gem5 commit {cites.get('gem5_commit')}, which is "
                                       f"not the pinned gem5 commit {commit} of {interface['id']} {interface['version']}")
    if not isinstance(calls, list) or not calls:
        error("calls", "an entry that covers calls lists them: call, prototype, contract (ACSL), rules")
        return []
    names, malformed_overloads = [], False
    for i, row in enumerate(calls):
        where = f"calls[{i}]"
        if not isinstance(row, dict) or not isinstance(row.get("call"), str):
            error(where, "a call row names its call")
            continue
        names.append(row["call"])
        if "supported" in row and type(row["supported"]) is not bool:
            error(f"{where}.supported", "supported must be a boolean; false explicitly refuses this call")
        if "overloads" in row and (not isinstance(row["overloads"], list) or not row["overloads"] or
                any(not isinstance(variant, dict) or
                    not isinstance(variant.get("prototype"), str) or not variant["prototype"].strip() or
                    not isinstance(variant.get("contract"), str) or not variant["contract"].strip()
                    for variant in row["overloads"])):
            error(f"{where}.overloads", "overloads must list a C prototype and contract for each declaration")
            malformed_overloads = True
        if 'instances' not in row and (not isinstance(row.get("contract"), str) or not row["contract"].strip()):
            error(f"{where}.contract", f"call {row['call']} has no ACSL contract (one contract per covered call)")
        if 'instances' not in row and (not isinstance(row.get("prototype"), str) or not re.search(
                rf"\b{re.escape(row['call'])}\s*\(", row.get("prototype") or "")):
            error(f"{where}.prototype", f"call {row['call']} needs its C prototype (core-subset spelling)")
        listed = row.get("rules")
        if not isinstance(listed, list) or not listed:
            error(f"{where}.rules", f"call {row['call']} names the rules it implements")
        else:
            for rule in listed:
                if rule not in rules:
                    error(f"{where}.rules", f"call {row['call']} names rule {rule}, which the entry does not hold")
        suffix = f".{interface['id']}.{interface['version']}"
        for lowering in row.get("lowerings") or []:
            if not (isinstance(lowering, str) and lowering.startswith("lowering.") and lowering.endswith(suffix)):
                error(f"{where}.lowerings", f"call {row['call']} names lowering {lowering}, which is not a lowering of "
                                            f"{interface['id']} {interface['version']}")
    if len(set(names)) != len(names):
        error("calls", "each call is listed once")
    from swdb import dx100_interface
    malformed_instances = not dx100_interface.check_instances(data, error)
    from swdb import dx100_source_selector, dx100_stream_source, dx100_allocation_source, dx100_register_source, dx100_initialized_register_source
    if not dx100_stream_source.stream_layout(data) and not dx100_allocation_source.allocation_layout(data) and not dx100_register_source.register_layout(data) and not dx100_initialized_register_source.initialized_register_layout(data):
        malformed_instances = not dx100_source_selector.check(library, data, error) or malformed_instances
    dx100_interface.check(library, data, error)
    found = data.get("inventory")
    if not isinstance(found, dict) or not isinstance(found.get("sources"), list) or \
            not isinstance(found.get("calls"), list):
        error("inventory", "an entry that covers calls records its call inventory: sources (pinned) and calls")
    else:
        for i, source in enumerate(found["sources"]):
            try:
                library._pin({k: v for k, v in source.items() if k in ("root", "path", "sha256")})
            except (KeyError, TypeError, ValueError, OSError) as exc:
                error(f"inventory.sources[{i}]", f"{exc}: the inventory was read from other code; reopen it")
        for name in found["calls"]:
            if name not in names:
                error("calls", f"inventory call {name} has no call row (every call the inventory found needs a "
                               "contract)")
    texts = _files(library, data, error)
    from swdb import dx100_size_source
    malformed_layout = not dx100_stream_source.check(library, data, texts, error)
    malformed_layout = not dx100_allocation_source.check(library, data, texts, error) or malformed_layout
    malformed_layout = not dx100_register_source.check(library, data, texts, error) or malformed_layout
    malformed_layout = not dx100_initialized_register_source.check(library, data, texts, error) or malformed_layout
    if not dx100_stream_source.stream_layout(data) and not dx100_allocation_source.allocation_layout(data) and not dx100_register_source.register_layout(data) and not dx100_initialized_register_source.initialized_register_layout(data):
        malformed_layout = not dx100_size_source.check(library, data, texts, error) or malformed_layout
        if not dx100_size_source.size_layout(data):
            malformed_layout = not dx100_source_selector.check_layout(data, texts, error) or malformed_layout
    if len(texts) < 4 or malformed_overloads or malformed_instances or malformed_layout:
        return []
    return _typecheck(library, entry_id, data, texts, error)


def _require_summary_form(data):
    from swdb import dx100_whole_checked
    if dx100_whole_checked.checked(data):
        from swdb.proof import AdapterError
        raise AdapterError("whole-interface checked bodies have no WP/ACSL summary form")


def acsl_source(data, texts, rows=None, *, constants=None):
    """The C file Frama-C type-checks: constants, the ghost block, the device state, the logic definitions, then each
    call's (and query's) contract on its prototype. `rows` limits it to some call or query rows."""
    _require_summary_form(data)
    parts = [f"#define {name} {value}" for name, value in (data.get("constants") or {}).items()]
    from swdb.dx100_source_selector import pure_layout
    from swdb.dx100_size_source import size_layout
    from swdb.dx100_stream_source import stream_layout
    from swdb.dx100_allocation_source import allocation_layout
    from swdb.dx100_register_source import register_layout
    from swdb.dx100_initialized_register_source import initialized_register_layout
    parts.append("#include <stdint.h>")
    state, _objects = _model_state(data, texts["model.state"], constants or data.get("constants") or {},
                                   constant_table=True)
    if pure_layout(data) or size_layout(data) or stream_layout(data) or allocation_layout(data) or register_layout(data) or initialized_register_layout(data):
        parts.append(state)  # Closed plain C state; no empty/nested ACSL ghost or logic block.
    else:
        parts += ["/*@ ghost"]
        parts += [f"  {decl};" for _name, decl in ghost_declarations(texts["ghost.acsl"])]
        parts += ["*/", state, "/*@", texts["model.logic"], "*/"]
    from swdb.dx100_interface import contract_rows
    for row in rows if rows is not None else [*(data.get("calls") or []), *(data.get("queries") or []),
                                              *((data.get("wp") or {}).get("probes") or [])]:
        for variant in contract_rows(row):
            parts += ["/*@", variant.get("contract") or "", "*/", f"{variant.get('prototype')};"]
    return "\n".join(parts) + "\n"


def wp_prelude(library, entry_id, called, defines=()):
    """The WP form of a proof semantics for one unit, inserted at the C lowering's ghost.globals anchor: the size
    constants, the probe macros (each a call of a contracted probe function), the ghost state (ghost.acsl as
    written), the device state, the logic, and the contract of every call and query the unit makes."""
    data = library.get(entry_id)
    _require_summary_form(data)
    constants = _constants(data, defines)
    texts = {"ghost.acsl": library.resolve(data["ghost"]["acsl"]).read_text(),
             "model.state": library.resolve(data["model"]["state"]).read_text(),
             "model.logic": library.resolve(data["model"]["logic"]).read_text()}
    probes = (data.get("wp") or {}).get("probes") or []
    rows = [r for r in [*(data.get("calls") or []), *(data.get("queries") or [])]
            if (r.get("call") or r.get("query")) in called] + list(probes)
    parts = [f"/* WP form of {entry_id} (version {data.get('version')}), generated by swdb.proof_semantics. */"]
    parts += [f"#define {name} {value}" for name, value in constants.items()]
    for probe in probes:
        name = re.match(r".*?\b(\w+)\s*\(", probe["prototype"]).group(1)
        parts.append(f"#define {probe['macro']}(addr, id) {name}(addr)")
    body = acsl_source({"constants": {}, "model": data.get("model", {})}, texts, rows=rows, constants=constants)
    parts.append(body.replace("#include <stdint.h>\n", ""))
    return "\n".join(parts) + "\n"


def wp_locations(library, entry_id, defines=()):
    """The ACSL locations of the ghost and device state (a unit that calls into the semantics assigns them)."""
    data = library.get(entry_id)
    _require_summary_form(data)
    found = []
    decls = [d for _n, d in ghost_declarations(library.resolve(data["ghost"]["acsl"]).read_text())]
    state = library.resolve(data["model"]["state"]).read_text()
    decls += [m.group(1) for m in re.finditer(r"^\s*int\s+([^;]+);", state, re.M)]
    for decl in decls:
        match = re.search(r"\b([A-Za-z_]\w*)\s*((?:\[[^\]]*\]\s*)*)$", decl.strip())
        name, dims = match.group(1), re.findall(r"\[([^\]]*)\]", match.group(2) or "")
        found.append(name + "".join(f"[0 .. {d.strip()} - 1]" for d in dims))
    return found


def check_defines(defines):
    """Reject a command-slot count that cannot fit the C model's unsigned 32-bit masks before a tool starts."""
    from swdb.proof import AdapterError
    for define in defines:
        name, _, value = define.partition("=")
        if name != "DX_K":
            continue
        try:
            capacity = int(value or 1)
        except ValueError:
            capacity = 0
        if not 1 <= capacity <= 32:
            raise AdapterError("DX_K must be in 1..32: the DX100 proof model uses unsigned 32-bit command masks")


def _constants(data, defines):
    check_defines(defines)
    constants = dict(data.get("constants") or {})
    for define in defines:
        name, _, value = define.partition("=")
        if name in constants:
            constants[name] = int(value or 1)
    return constants


def _typecheck(library, entry_id, data, texts, error):
    """Frama-C type-checks the ghost state, the logic and every contract; missing Frama-C: each contract unchecked."""
    from swdb import framac
    from swdb.dx100_interface import contract_rows
    from swdb.problems import Problem
    rows = [variant for row in [*(data.get("calls") or []), *(data.get("queries") or [])]
            for variant in contract_rows(row)]
    tool = framac.locate()
    path = str(library.files[entry_id])
    if tool.missing:
        return [Problem(path, "calls", f"not type-checked: {tool.missing}; the {len(rows)} ACSL contracts of "
                                       f"{entry_id} are unchecked, not valid")]
    if framac.typecheck(tool, acsl_source(data, texts)) is None:
        return []
    message = framac.typecheck(tool, acsl_source(data, texts, rows=[]))
    if message is not None:
        error("model.logic", f"Frama-C {tool.version} refuses the ghost state, device state or logic: {message}")
        return []
    for i, row in enumerate(data.get("calls") or []):
        message = framac.typecheck(tool, acsl_source(data, texts, rows=[row]))
        if message is not None:
            error(f"calls[{i}].contract", f"Frama-C {tool.version} refuses the contract of {row.get('call')}: {message}")
    for i, row in enumerate(data.get("queries") or []):
        message = framac.typecheck(tool, acsl_source(data, texts, rows=[row]))
        if message is not None:
            error(f"queries[{i}].contract", f"Frama-C {tool.version} refuses the contract of {row.get('query')}: "
                                            f"{message}")
    return []


def _files(library, data, error):
    """The pinned ghost, state, model and logic files; a ghost array is declared once (in ghost.acsl only)."""
    texts = {}
    for key, pin in (("ghost.acsl", (data.get("ghost") or {}).get("acsl")),
                     *((f"model.{k}", (data.get("model") or {}).get(k)) for k in ("state", "c", "logic"))):
        try:
            library._pin(pin)
            texts[key] = library.resolve(pin).read_text()
        except (KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
            error(key, f"{exc} (an entry that covers calls pins ghost.acsl, model.state, model.c and model.logic)")
    if "ghost.acsl" not in texts:
        return texts
    ghost = ghost_declarations(texts["ghost.acsl"])
    from swdb.dx100_source_selector import pure_layout
    from swdb.dx100_size_source import size_layout
    from swdb.dx100_stream_source import stream_layout
    from swdb.dx100_allocation_source import allocation_layout
    from swdb.dx100_register_source import register_layout
    from swdb.dx100_initialized_register_source import initialized_register_layout
    if not ghost and not pure_layout(data) and not size_layout(data) and not stream_layout(data) and not allocation_layout(data) and not register_layout(data) and not initialized_register_layout(data):
        error("ghost.acsl", "the ghost file declares no ghost array")
    for key in ("model.state", "model.c"):
        for name, _decl in ghost:
            if key in texts and re.search(rf"^\s*(static\s+)?((unsigned|signed|const|long|short)\s+)*"
                                          rf"(int|long|short|char|unsigned|_Bool|bool|u?int\d+_t)\b[\s\*]*{name}\s*(\[|=|;)",
                                          texts[key], re.M):
                error(key, f"ghost array {name} is declared again in {key}: the ghost state is declared once, in "
                           "ghost.acsl (the C globals are generated from it)")
    return texts


# --- the bounded verifier's view ---------------------------------------------------------------------------------

@dataclass(frozen=True)
class Model:
    entry: str
    sha256: str                      # the file hash of the entry (what a proof record pins)
    calls: tuple
    queries: tuple
    c_text: str
    functions: tuple                 # model function names (their loops get the model's unwinding bound)
    unwind: int                      # the model's loop bound + 1
    tile_objects: tuple = ()         # independent bounded C objects: (name, element count)


def current(library):
    """{entry ID: data} of the current proof-semantics versions that cover calls (highest sequence per target)."""
    best = {}
    for entry_id, data in library.entries.items():
        if data.get("kind") != "proof_semantics" or not data.get("calls"):
            continue
        key = data.get("target")
        if key not in best or data.get("sequence", 0) > best[key][1].get("sequence", 0):
            best[key] = (entry_id, data)
    return dict(best.values())


def covered_names(library):
    """{call or query name: entry ID} over the current versions."""
    found = {}
    for entry_id, data in current(library).items():
        for row in data.get("calls") or []:
            found[row["call"]] = entry_id
        for row in data.get("queries") or []:
            found[row["query"]] = entry_id
    return found


def record_assumptions(library, entry_id, sha256):
    """Trust rules recorded on EVERY verdict using this exact semantics version.

    Rule statements and their cited/owned evidence live in the pinned entry.
    References use its content hash plus a distinct rule fragment; a mutation
    cannot silently attach new trust text to a verdict for older bytes.
    """
    from swdb.proof import AdapterError
    path = library.files[entry_id]
    try:
        unchanged = (artifacts.file_hash(path) == sha256
                     and yamlio.load(path) == library.get(entry_id)
                     and artifacts.file_hash(path) == sha256)
    except (OSError, UnicodeError, yaml.YAMLError):
        unchanged = False
    if not unchanged:
        raise AdapterError('proof-semantics trust entry changed during the job')
    return [{'kind': 'proof_semantics', 'reference': {'id': f'{entry_id}#{rule["id"]}', 'sha256': sha256},
             'sentence': rule['statement']}
            for rule in library.get(entry_id).get('rules', []) if rule.get('record_assumption') is True]


def lowering_options(library):
    """The keyword arguments of `c_lowering.lower` for a unit that may call into a current proof semantics: its
    calls and queries as summaries (calls kept, prototype only) and the tile-pointer calls (hazard probes)."""
    from swdb import dx100_whole_checked
    covered = covered_names(library)
    if not covered:
        return {}
    instances = {row['call']: row['instances'] for data in current(library).values()
                 for row in data.get('calls', []) if 'instances' in row}
    semantics = {"tile_pointer": {TILE_POINTER}, "calls": set(covered),
                 "refused_calls": {row["call"] for data in current(library).values()
                                   for row in data.get("calls", []) if row.get("supported") is False or dx100_whole_checked.checked(data)}}
    if instances:
        from swdb import dx100_source_selector, dx100_stream_source, dx100_allocation_source, dx100_register_source, dx100_initialized_register_source
        instances = {name: [{**v, 'definition': (dx100_initialized_register_source.policy if isinstance(v['definition'],dict) and v['definition'].get('kind')==dx100_initialized_register_source.KIND else dx100_register_source.policy if isinstance(v['definition'],dict) and v['definition'].get('kind')==dx100_register_source.KIND else dx100_allocation_source.policy if isinstance(v['definition'],dict) and v['definition'].get('kind')==dx100_allocation_source.KIND else dx100_stream_source.policy if isinstance(v['definition'],dict) and v['definition'].get('kind')==dx100_stream_source.KIND else dx100_source_selector.policy)(library, v['definition'])}
                            if 'definition' in v else v for v in variants]
                     for name, variants in instances.items()}
        semantics['template_instances'] = instances
    from swdb import dx100_size_source
    semantics['source_definitions'] = {r['call']: dx100_size_source.policy(library,r['definition'])
        for data in current(library).values() if dx100_size_source.size_layout(data)
        for r in data.get('calls',[]) if r.get('supported') is True}
    from swdb import dx100_stream_source
    semantics['source_definitions'].update({r['call']: dx100_stream_source.policy(library,r['definition'])
        for data in current(library).values() if dx100_stream_source.stream_layout(data)
        for r in data.get('calls',[]) if r.get('supported') is True and 'definition' in r})
    from swdb import dx100_allocation_source
    semantics['source_definitions'].update({r['call']:dx100_allocation_source.policy(library,r['definition'])
        for data in current(library).values() if dx100_allocation_source.allocation_layout(data)
        for r in data.get('calls',[]) if r.get('supported') is True and 'definition' in r})
    from swdb import dx100_initialized_register_source
    semantics['source_definitions'].update({r['call']:dx100_initialized_register_source.policy(library,r['definition'])
        for data in current(library).values() if dx100_initialized_register_source.initialized_register_layout(data)
        for r in data.get('calls',[]) if r.get('supported') is True and 'definition' in r})
    return {"summaries": dict(covered), "semantics": semantics}


def called(lowering, covered):
    """The proof-semantics calls and queries a C lowering makes (sorted)."""
    return sorted({row["name"] for row in lowering.summaries if row.get("name") in covered})


def instance_bindings(lowering):
    """Persistent source-instantiation identities, independently of family names."""
    return [{'name': row['name'], 'c_name': row['c_name'], **row['semantic_instance']}
            for row in lowering.summaries if 'semantic_instance' in row]


def contract_names(library, entry_id, called):
    from swdb.dx100_interface import contract_rows
    data = library.get(entry_id)
    return [re.match(r'.*?\b(\w+)\s*\(', variant['prototype'])[1]
            for row in [*data.get('calls', []), *data.get('queries', [])]
            if row.get('call', row.get('query')) in called for variant in contract_rows(row)]


def _model_state(data, text, constants, *, constant_table=False):
    from swdb.dx100_source_selector import pure_layout
    from swdb.dx100_size_source import size_layout
    from swdb.dx100_stream_source import stream_layout
    from swdb.dx100_allocation_source import allocation_layout
    from swdb.dx100_register_source import register_layout
    from swdb.dx100_initialized_register_source import initialized_register_layout
    if pure_layout(data) or size_layout(data) or stream_layout(data) or allocation_layout(data) or register_layout(data) or initialized_register_layout(data):
        return text, ()
    return _bounded_state(text, constants, constant_table=constant_table)


def _bounded_state(text, constants, *, constant_table=False):
    """Give each tile its own C object; created 2026-10-15 ET.

    CBMC pointer checks follow allocation objects, so rows of one 2D array do
    not enforce each tile's extent. Static rows preserve initialization and
    indexed access without assuming heap allocation succeeds. WP uses the same
    distinct objects and an immutable initialized pointer table.
    """
    count, extent = int(constants["DX_NT"]), int(constants["DX_TS"])
    if count < 1 or extent < 1:
        raise ValueError("bounded tile object dimensions must be positive")
    objects = tuple((f"swdb_dx_tile_row_{i}", extent) for i in range(count))
    declaration = r"\bint\s+dx_tile_data\s*\[DX_NT\]\s*\[DX_TS\]\s*;"
    if len(re.findall(declaration, text)) != 1:
        raise ValueError("bounded state needs the canonical single tile array declaration")
    rows = [f"static int {name}[DX_TS];" for name, _size in objects]
    table_type = "int * const" if constant_table else "int *"
    rows.append(table_type + " dx_tile_data[DX_NT] = {" + ", ".join(name for name, _size in objects) + "};")
    return re.sub(declaration, lambda _match: "\n".join(rows), text), objects


def model_for(library, entry_id, defines=(), *, source_unit=None):
    """The Model of one entry, with the build constants `defines` (NAME or NAME=VALUE) overriding its defaults."""
    data = library.get(entry_id)
    from swdb import dx100_whole_checked, dx100_checked_source
    if dx100_whole_checked.checked(data):
        if source_unit is None or source_unit.selection.entry_id != entry_id:
            raise ValueError('whole checked model requires its exact complete source/receiver unit')
        dx100_whole_checked.policy(library, data)
        dx100_checked_source.recheck(source_unit)
        return Model(**dx100_checked_source.model_fields(source_unit))
    if source_unit is not None:
        raise ValueError('a checked whole source unit cannot select a legacy model')
    constants = _constants(data, defines)
    parts = [f"/* Generated by swdb.proof_semantics: the C model of {entry_id} (version {data.get('version')}). */"]
    parts += [f"#define {name} {value}" for name, value in constants.items()]
    parts.append(f'#define DX_RULE(r) "{entry_id}#" r')
    ghost = ghost_declarations(library.resolve(data["ghost"]["acsl"]).read_text())
    parts.append("/* ghost state, generated from ghost.acsl (declared once there) */")
    parts += [f"{decl};" for _name, decl in ghost]
    state, tile_objects = _model_state(data, library.resolve(data["model"]["state"]).read_text(), constants)
    parts.append(state)
    model = library.resolve(data["model"]["c"]).read_text()
    parts.append(model)
    functions = sorted(set(re.findall(r"^(?:static\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{",
                                      model, re.M)))
    unwind = max([int(constants.get(k, 0)) for k in ("DX_K", "DX_NT", "DX_NR", "DX_NM")] +
                 [int(constants.get("DX_TS", 0)) + 1]) + 1
    return Model(entry=entry_id, sha256=artifacts.file_hash(library.files[entry_id]),
                 calls=tuple(r["call"] for r in data["calls"]), queries=tuple(r["query"] for r in data.get("queries") or []),
                 c_text="\n".join(parts) + "\n", functions=tuple(functions), unwind=unwind, tile_objects=tile_objects)


def array_call_policies(library, defines=()):
    """Exact audited host-pointer call footprints, separately checked at each source call.

    A matching call name alone grants no exemption. The lowering must certify its
    imported AST binding, stable typed source origin, placement and fresh guard view.
    """
    from swdb import bounded_initialization, dx_array_domains
    found = {}
    from swdb import dx100_whole_checked
    for entry in current(library):
        if dx100_whole_checked.checked(library.get(entry)):
            continue  # whole units gain no generic per-call or pointer exemptions
        model = model_for(library, entry, defines)
        policy = bounded_initialization._dx100_policy(library, model, defines)
        if policy is None:
            continue
        for call in sorted(set(policy["calls"]) & set(dx_array_domains.ARITIES)):
            if call in found:
                raise ValueError("ambiguous audited DX100 pointer-call policy: " + call)
            found[call] = {"check": dx_array_domains.identity(), "model": policy, "call": call}
    return found


def imported_call_policies(library, defines=()):
    """Every audited external call needs its exact prototype and model binding."""
    from swdb import bounded_initialization
    found = {}
    from swdb import dx100_whole_checked
    for entry in current(library):
        if dx100_whole_checked.checked(library.get(entry)):
            continue  # whole units gain no generic per-call or pointer exemptions
        model = model_for(library, entry, defines)
        policy = bounded_initialization._dx100_policy(library, model, defines)
        if policy is None:
            continue
        data = library.get(entry)
        for row in [*data.get("calls", []), *data.get("queries", [])]:
            name = row.get("call", row.get("query"))
            if name not in policy["calls"]:
                continue
            if name in found:
                raise ValueError("ambiguous audited DX100 imported-call policy: " + name)
            found[name] = {"model": policy, "call": name, "prototype": row["prototype"]}
            if row.get("query"):
                found[name]["query_contract"] = row["contract"]
    return found


def state_draws(library, entry_id, defines=()):
    """The device-state elements the harness draws from the oracle at the start (havoc): tile elements."""
    data = library.get(entry_id)
    from swdb.dx100_source_selector import pure_layout
    from swdb.dx100_size_source import size_layout
    from swdb.dx100_stream_source import stream_layout
    from swdb.dx100_allocation_source import allocation_layout
    from swdb.dx100_register_source import register_layout
    from swdb.dx100_initialized_register_source import initialized_register_layout
    if pure_layout(data) or size_layout(data) or stream_layout(data) or allocation_layout(data) or register_layout(data) or initialized_register_layout(data):
        return []
    constants = _constants(data, defines)
    return [f"dx_tile_data[{t}][{k}]" for t in range(int(constants["DX_NT"])) for k in range(int(constants["DX_TS"]))]
