"""Hint records, the deterministic merger and the proof hint check (WP only).

Created: 2026-10-14 ET (Probata proof of concept ticket 35). Design: formal-verification map spec ("Proof-hint
loop": hint form, vocabulary, three checks); map 13 items 2, 4, 5, 7, 8, 12; map 24 items 1, 7. Spike (c)
(ticket 07, prototype/07-wp-hints/hints.py) showed what this keeps: blame (each Frama-C error traced to the
hint that holds its line) and a WP goal-generation pass. Format: docs/reference/format-v0.4-proof-hints.md.

- A hint is a record `{anchor, kind, text, provenance}`; provenance is `{source: agent | seed | human}`, a seed
  also names its `seed_source`. A hint set is a list of hints (`{hints: [...]}` in a hint file).
- The merger inserts each hint as one ACSL annotation comment on its own lines right after its anchor line of
  the C lowering, in canonical order: anchors in lowering order, then the kind's rank, then the hint set's own
  order (ACSL and ghost code are declare-before-use, so same-rank hints at one anchor keep their order).
- The proof hint check judges a hint set in stages, recording every rejection by rule (vocabulary
  `proof_hint_rules`): (1) record: anchor exists, kind on the vocabulary (`proof_hint_kinds`), kind allowed at
  that anchor kind; (2) erase-and-diff: erasing the merged annotations gives back the C lowering byte for
  byte; (3) Frama-C 33.0 parses and type-checks the merged unit (with the contract and logic files WP sees),
  a refused hint is blamed by line and dropped, and the run repeats; (4) the syntax tree, read by the
  Frama-C module `hint_tree.ml`, holds exactly the declared kind for each hint and none of the rejected
  constructs; (5) WP generates its goals without a prover. One rejection rejects the set: it never reaches WP.
- Every result names the check version and the vocabulary version (each an ID plus sha256). The vocabulary
  files are pinned: a changed file without a new VOCABULARY_VERSION stops the check.
"""

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from swdb import framac, paths, yamlio

CHECK_VERSION = "1"
VOCABULARY_VERSION = "1"
VOCABULARY_SHA256 = "42d9d03ab4b6246ab882fb609cee787f41acf29dc6fbf889b2951d646c2921f9"     # sha256 of proof_hint_kinds.yaml + proof_hint_rules.yaml for VOCABULARY_VERSION
KINDS_FILE, RULES_FILE = "proof_hint_kinds.yaml", "proof_hint_rules.yaml"
TREE_MODULE = Path(__file__).with_name("hint_tree.ml")
SOURCES = ("agent", "seed", "human")
FIELDS = ("anchor", "kind", "text", "provenance")
UNIT = "hint_check.c"
FLAGS = ("-machdep", "x86_64")            # default warning levels: annot-error and ghost:bad-use abort
TIMEOUT_SECONDS = 300
ANCHOR_LINE = re.compile(r"^(\s*)/\* swdb-anchor (\S+) \*/$")
LINE_SPLICE = re.compile(r"\\\r?\n|\?\?/")
GHOST_BAD_USE = re.compile(r"ghost:bad-use|non-ghost|Ghost code breaks CFG|\\ghost")


class HintSetError(ValueError):
    """A hint file that does not hold well-formed hint records (nothing is checked or run)."""


class HintCheckError(RuntimeError):
    """The check could not judge the set (tool missing, vocabulary changed without a new version)."""


# --- records and the vocabulary ----------------------------------------------------------------------------

def read_hint_set(path):
    """The hint records of a hint file `{hints: [{anchor, kind, text, provenance}, ...]}`."""
    try:
        data = yamlio.load(Path(path))
    except (OSError, ValueError) as exc:
        raise HintSetError(f"cannot read the hint file {path}: {exc}") from None
    hints = data.get("hints") if isinstance(data, dict) else None
    if not isinstance(hints, list):
        raise HintSetError(f"hint file {path} holds hints: [{{anchor, kind, text, provenance}}, ...]")
    for position, hint in enumerate(hints):
        problem = record_problem(hint)
        if problem:
            raise HintSetError(f"hint file {path}, hints[{position}]: {problem}")
    return hints


def record_problem(hint):
    """Why `hint` is not a hint record, or None."""
    if not isinstance(hint, dict):
        return "a hint is a mapping {anchor, kind, text, provenance}"
    missing = [name for name in FIELDS if name not in hint]
    if missing:
        return f"missing field {', '.join(missing)}"
    extra = sorted(set(hint) - set(FIELDS))
    if extra:
        return f"unknown field {', '.join(extra)}"
    for name in ("anchor", "kind", "text"):
        if not isinstance(hint[name], str) or not hint[name].strip():
            return f"field {name} must be a non-empty string"
    provenance = hint["provenance"]
    if not isinstance(provenance, dict) or provenance.get("source") not in SOURCES:
        return f"field provenance must be {{source: {' | '.join(SOURCES)}}}"
    allowed = {"source", "seed_source"} if provenance["source"] == "seed" else {"source"}
    if set(provenance) - allowed:
        return f"provenance of a {provenance['source']} hint holds only {', '.join(sorted(allowed))}"
    if provenance["source"] == "seed" and not str(provenance.get("seed_source") or "").strip():
        return "provenance of a seed names its seed_source"
    return None


@dataclass(frozen=True)
class Vocabulary:
    kinds: dict
    rules: dict
    identity: dict


def vocabulary():
    """The pinned proof hint vocabulary; a changed file without a new version is an error, never a silent change."""
    texts = [(paths.VOCAB / name).read_bytes() for name in (KINDS_FILE, RULES_FILE)]
    sha = hashlib.sha256(b"".join(texts)).hexdigest()
    if sha != VOCABULARY_SHA256:
        raise HintCheckError(f"the proof hint vocabulary ({KINDS_FILE}, {RULES_FILE}) changed (sha256 {sha}) "
                             f"without a new version: proof-hint-vocabulary-{VOCABULARY_VERSION} pins "
                             f"{VOCABULARY_SHA256}. Bump swdb.hint_check.VOCABULARY_VERSION and its pinned sha256")
    kinds = {entry["value"]: entry for entry in yamlio.load(paths.VOCAB / KINDS_FILE)["values"]}
    rules = {entry["value"]: entry for entry in yamlio.load(paths.VOCAB / RULES_FILE)["values"]}
    return Vocabulary(kinds, rules, {"id": f"proof-hint-vocabulary-{VOCABULARY_VERSION}", "sha256": sha})


def identity():
    """{check, vocabulary}: each {id, sha256}. The check's sha256 covers this module and the tree reader."""
    code = Path(__file__).read_bytes() + TREE_MODULE.read_bytes()
    return {"check": {"id": f"proof-hint-check-{CHECK_VERSION}", "sha256": hashlib.sha256(code).hexdigest()},
            "vocabulary": vocabulary().identity}


# --- canonical order, hash and the merger -------------------------------------------------------------------

def _anchor_kinds(anchors):
    return {a["id"]: a["kind"] for a in anchors}


def canonical(hints, anchors, kinds=None):
    """Indices of `hints` in canonical order (anchor order in the lowering, kind rank, then the set's order)."""
    kinds = kinds if kinds is not None else vocabulary().kinds
    order = {a["id"]: position for position, a in enumerate(anchors)}

    def key(index):
        hint = hints[index]
        return (order.get(hint["anchor"], len(order)), hint["anchor"] if hint["anchor"] not in order else "",
                (kinds.get(hint["kind"]) or {}).get("rank", 99), index)
    return sorted(range(len(hints)), key=key)


def hint_set_sha256(hints, anchors, kinds=None):
    """The hint set's hash: its records' anchor, kind and text, in canonical order (provenance aside)."""
    body = [{name: hints[i][name] for name in ("anchor", "kind", "text")} for i in canonical(hints, anchors, kinds)]
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Merged:
    text: str
    spans: dict          # hint index -> (first line, last line), 1-based, in `text`
    blocks: dict         # anchor -> (first line, last line) of everything inserted after it

    @property
    def sha256(self):
        return hashlib.sha256(self.text.encode()).hexdigest()


def _lines(text, indent, first):
    lines = text.strip().splitlines()
    return [indent + first + lines[0]] + [indent + "    " + line.rstrip() for line in lines[1:]]


def wp_base(lowering, anchors, context):
    """WP's input without hints: the C lowering with `context` ({anchor: [block]}: the contract, logic files)
    inserted right after its anchor lines (anchor lines stay). The `base` of `check` and `judge`."""
    return merge(lowering, anchors, [], context=context).text


def merge(base, anchors, hints, indices=None, context=None, kinds=None):
    """Insert the hints `indices` (default: all) after their anchor lines of `base` (the C lowering, or WP's input
    without hints), after any annotation comment already there (contract, logic files); `context`
    {anchor: [block text]} goes first at its anchor. Deterministic: same input, same bytes.

    Each hint is one annotation comment on its own lines; the hints of a loop head share one comment (Frama-C
    takes a loop's annotations from one comment only), each hint still on its own lines."""
    loops = {a["id"] for a in anchors if a["kind"] == "loop_head"}
    indices = list(range(len(hints))) if indices is None else list(indices)
    chosen = [i for i in canonical(hints, anchors, kinds) if i in set(indices)] if hints else []
    by_anchor = {}
    for index in chosen:
        by_anchor.setdefault(hints[index]["anchor"], []).append(index)
    out, spans, blocks = [], {}, {}
    source = base.splitlines()
    position = 0
    while position < len(source):
        line = source[position]
        position += 1
        out.append(line)
        match = ANCHOR_LINE.match(line)
        if not match:
            continue
        indent, anchor = match.groups()
        first = len(out) + 1
        for block in (context or {}).get(anchor, []):
            out += [indent + part for part in block.splitlines()]
        while position < len(source) and source[position].lstrip().startswith("/*@"):   # what base already holds
            while True:
                out.append(source[position])
                position += 1
                if "*/" in out[-1] or position >= len(source):
                    break
        group = by_anchor.get(anchor, [])
        for rank, index in enumerate(group):
            start = len(out) + 1
            shared = anchor in loops
            out += _lines(hints[index]["text"], indent, "/*@ " if rank == 0 or not shared else "    ")
            if not shared or rank == len(group) - 1:
                out[-1] += " */"
            spans[index] = (start, len(out))
        if len(out) >= first:
            blocks[anchor] = (first, len(out))
    return Merged("\n".join(out) + ("\n" if base.endswith("\n") else ""), spans, blocks)


def erase(text):
    """The C text with every ACSL annotation comment removed, and each line that held only annotations dropped.

    A C-level lexer: block and line comments, string and character literals. Non-annotation comments and code
    stay, so erase(merge(lowering, hints)) == lowering exactly when every hint added only annotation comments."""
    lines, current, removed, i, n = [], [], False, 0, len(text)

    def keep(segment):
        nonlocal current, removed
        for char in segment:
            if char == "\n":
                line = "".join(current)
                if not (removed and not line.strip()):
                    lines.append(line + "\n")
                current, removed = [], False
            else:
                current.append(char)

    while i < n:
        if text.startswith("/*", i):
            close = text.find("*/", i + 2)
            end = n if close < 0 else close + 2
            if text.startswith("/*@", i):
                removed = True
                newlines = text.count("\n", i, end)
                for _ in range(newlines):         # an annotation spanning lines: its inner lines are hint lines
                    line = "".join(current)
                    if line.strip():
                        lines.append(line + "\n")
                    current = []
            else:
                keep(text[i:end])
            i = end
        elif text.startswith("//", i):
            close = text.find("\n", i)
            end = n if close < 0 else close
            if text.startswith("//@", i):
                removed = True
            else:
                keep(text[i:end])
            i = end
        elif text[i] in "\"'":
            j = i + 1
            while j < n and text[j] != text[i] and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            keep(text[i:j + 1])
            i = j + 1
        else:
            keep(text[i])
            i += 1
    if current:
        line = "".join(current)
        if not (removed and not line.strip()):
            lines.append(line)
    return "".join(lines)


# --- the check -------------------------------------------------------------------------------------------------

def check(base, anchors, hints):
    """Ticket 34's frozen-wrapper interface: `check(base, anchors, hints) -> {passed, rejections, merged, ...}`.

    `base` is WP's input without hints (`wp_base`; the C lowering when there is no contract), `anchors` the
    anchors list or the whole `<f>.anchors.json` mapping, `hints` `{anchor, kind, text}` records (provenance is
    not needed to judge). No WP goal-generation stage (the wrapper's prove_hints runs WP itself). Its Frama-C runs
    are one verifier job under the machine-wide verifier lock (`swdb prove` calls `judge` inside its own job)."""
    import tempfile
    from swdb import verifier_lock
    anchors = anchors.get("anchors", []) if isinstance(anchors, dict) else anchors
    with tempfile.TemporaryDirectory(prefix="swdb-hint-check-") as workdir, verifier_lock.hold("proof hint check"):
        result = judge(base, anchors, hints, workdir)
    result["passed"] = result["verdict"] == "accepted"
    return result


def judge(base, anchors, hints, workdir, wp_flags=None, tool=None):
    """Judge `hints` against `base` (WP's input without hints: the C lowering with its contract and logic files
    at their anchors, `wp_base`) with anchors `anchors` ([{id, kind, ...}]).

    `wp_flags`, when given, are the frozen frama-c-wp flags for the goal-generation stage. Returns the result
    mapping (see the format document); `merged` is `base` with every hint at a known anchor merged (WP's input
    when accepted) and `accepted` the indices that reach WP (all of them or none)."""
    vocab = vocabulary()
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    kinds = _anchor_kinds(anchors)
    reference = erase(base)
    rejections = []

    def reject(index, rule, detail):
        hint = hints[index] if index is not None else {}
        rejections.append({"hint": index, "anchor": hint.get("anchor"), "kind": hint.get("kind"), "rule": rule,
                           "detail": str(detail)[:600]})

    alive = []
    for index, hint in enumerate(hints):                                  # (1) record rules
        if hint["anchor"] not in kinds:
            reject(index, "unknown_anchor", f"{hint['anchor']} is not an anchor of the C lowering")
        elif hint["kind"] not in vocab.kinds:
            reject(index, "kind_not_allowed", f"{hint['kind']} is not on proof-hint-vocabulary-{VOCABULARY_VERSION}")
        elif kinds[hint["anchor"]] not in vocab.kinds[hint["kind"]]["anchor_kinds"]:
            reject(index, "anchor_kind_mismatch", f"a {hint['kind']} hint may not sit at a {kinds[hint['anchor']]} "
                   f"anchor (allowed: {', '.join(vocab.kinds[hint['kind']]['anchor_kinds'])})")
        else:
            alive.append(index)
    merged = merge(base, anchors, hints, [i for i, h in enumerate(hints) if h["anchor"] in kinds], kinds=vocab.kinds)
    for index in list(alive):                                              # (2) erase-and-diff, per hint
        if LINE_SPLICE.search(hints[index]["text"]):
            detail = "the text holds a line splice or trigraph, which changes where its comment ends"
        elif erase(merge(base, anchors, hints, [index], kinds=vocab.kinds).text) != reference:
            detail = "erasing the hint's annotation leaves code or a comment the C lowering does not have"
        else:
            continue
        reject(index, "erase_and_diff", detail)
        alive.remove(index)
    if alive and erase(merge(base, anchors, hints, alive, kinds=vocab.kinds).text) != reference:
        reject(None, "erase_and_diff", "the merged hints together do not erase back to the C lowering")
        alive = []
    runs = 0
    if alive:
        alive, runs = _frama_c(base, anchors, hints, alive, workdir, tool, reject, vocab, wp_flags)
    verdict = "accepted" if not rejections else "rejected"
    ids = identity()
    return {"check": ids["check"], "vocabulary": ids["vocabulary"], "verdict": verdict,
            "hint_set_sha256": hint_set_sha256(hints, anchors, vocab.kinds), "merged_sha256": merged.sha256,
            "rejections": sorted(rejections, key=lambda r: (r["hint"] is None, r["hint"] or 0, r["rule"])),
            "frama_c_runs": runs, "merged": merged.text,
            "accepted": list(range(len(hints))) if verdict == "accepted" else []}


def _frama_c(base, anchors, hints, alive, workdir, tool, reject, vocab, wp_flags):
    """Stages (3)-(5): parse with blame (repeat without a blamed hint), the syntax tree, WP goal generation."""
    tool = tool or framac.locate()
    if tool.missing:
        raise HintCheckError(f"the proof hint check needs Frama-C: {tool.missing}")
    module = _compile_tree_module(workdir)
    runs = 0
    tree = workdir / "hint_tree.jsonl"

    def parse(subset):
        merged = merge(base, anchors, hints, subset, kinds=vocab.kinds)
        (workdir / UNIT).write_text(merged.text)
        tree.unlink(missing_ok=True)
        done = _run(tool, [*FLAGS, "-load-module", str(module), UNIT], workdir, {"SWDB_HINT_TREE_OUT": str(tree)})
        output = done.stdout + done.stderr
        return done.returncode == 0 and "Ignoring" not in output and tree.exists(), output, merged

    while alive:
        ok, output, merged = parse(alive)
        runs += 1
        if ok:
            break
        errors = _errors(output)
        if not errors:
            reject(None, "parse_error", _messages(output) or "Frama-C failed with no message")
            return [], runs
        blamed = {}
        for error in errors:                       # errors located in the hint's own lines: one run blames them all
            index = _holder(error["line"], merged, hints, alive) if error["line"] and error["reliable"] else None
            if index is not None:
                blamed.setdefault(index, error["message"])
        if not blamed:
            # "Ghost code breaks CFG starting at" a statement that may be real code: the culprit is the hint whose
            # removal makes the error go away; ghost hints first, then the others, nearest first.
            error = errors[0]
            near = _holder(error["line"], merged, hints, alive) if error["line"] else None
            order = sorted(alive, key=lambda i: (i != near, hints[i]["kind"] != "ghost",
                                                 abs(merged.spans[i][0] - (error["line"] or 0)), i))
            for index in order:
                _ok, again, _merged = parse([i for i in alive if i != index])
                runs += 1
                if error["signature"] not in {e["signature"] for e in _errors(again)}:
                    blamed[index] = error["message"]
                    break
        if not blamed:
            reject(None, "parse_error", errors[0]["message"])
            return [], runs
        for index, message in blamed.items():
            reject(index, "interfering_ghost_code" if GHOST_BAD_USE.search(message) else "parse_error", message)
            alive.remove(index)
    if not alive:
        return alive, runs                          # else the loop's last parse accepted `alive` and wrote its tree
    nodes = [json.loads(line) for line in tree.read_text().splitlines() if line.strip()]
    if not nodes or nodes[-1].get("node") != "end":
        raise HintCheckError("the syntax-tree reader stopped before its end marker")
    bad = _tree_rules(nodes[:-1], merged, hints, alive, vocab)
    for index, found in sorted(bad.items()):
        for rule, detail in found:
            reject(index, rule, detail)
    alive = [i for i in alive if i not in bad]
    if alive and not bad and wp_flags is not None:                        # (5) WP goal generation, no prover
        # 2026-10-15 ET: selectors accumulate in Frama-C; a trailing none does not cancel inherited solvers.
        generation_flags = list(wp_flags)
        for index in range(len(generation_flags) - 1, -1, -1):
            if generation_flags[index] == "-wp-prover":
                del generation_flags[index:index + 2]
            elif generation_flags[index].startswith("-wp-prover="):
                del generation_flags[index]
        done = _run(tool, [*generation_flags, *FLAGS, UNIT, "-wp-prover", "none"], workdir, {})
        runs += 1
        output = done.stdout + done.stderr
        if done.returncode != 0 or re.search(r"User Error|Invalid|invalid user input|aborted|Ignoring", output):
            blamed = {}
            for error in _errors(output):
                index = _holder(error["line"], merged, hints, alive) if error["line"] else None
                if index is not None:
                    blamed.setdefault(index, error["message"])
            if not blamed:
                reject(None, "wp_generation_error", _messages(output) or f"WP exited {done.returncode}")
            for index, message in blamed.items():
                reject(index, "wp_generation_error", message)
            alive = []
    return alive, runs


def _run(tool, args, cwd, extra_env):
    env = {k: v for k, v in os.environ.items() if not k.startswith("FRAMAC_WP")}
    env.update(extra_env)
    try:
        return subprocess.run([*tool.command, *args], cwd=cwd, capture_output=True, text=True, env=env,
                              timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise HintCheckError(f"Frama-C did not finish within {TIMEOUT_SECONDS} s") from None
    except OSError as exc:
        raise HintCheckError(f"Frama-C did not start: {exc}") from None


def _compile_tree_module(workdir):
    """hint_tree.cmxs, compiled against the Frama-C kernel of the opam switch (or SWDB_OCAMLFIND)."""
    out = Path(workdir) / "hint_tree.cmxs"
    source = Path(workdir) / "hint_tree.ml"
    shutil.copyfile(TREE_MODULE, source)
    command = _ocamlfind()
    try:
        done = subprocess.run([*command, "ocamlopt", "-shared", "-package", "frama-c.kernel", "-o", out.name,
                               source.name], cwd=workdir, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as exc:
        raise HintCheckError(f"cannot compile the syntax-tree reader: {exc}") from None
    if done.returncode != 0 or not out.exists():
        raise HintCheckError(f"cannot compile the syntax-tree reader: {(done.stderr or done.stdout).strip()[:600]}")
    return out


def _ocamlfind():
    given = os.environ.get("SWDB_OCAMLFIND")
    if given:
        return tuple(shlex.split(given))
    command = framac.locate().command
    if command[:2] == ("opam", "exec") and "--" in command:
        return (*command[:command.index("--") + 1], "ocamlfind")
    if framac._switch_exists():
        return ("opam", "exec", "--switch=framac-33", "--", "ocamlfind")
    return ("ocamlfind",)


LOCATION = re.compile(re.escape(UNIT) + r":(\d+)")


ERROR_HEAD = re.compile(r"^\[[\w:-]+\].*(User Error|Failure|syntax error|Error:|not found|Invalid)", re.I)


def _errors(output):
    """Frama-C's error messages, each {line (of the unit, or None), reliable, message, signature (no line)}.

    A message is a `[plugin...]` head line plus its indented lines; under a `Deferred error` head each indented
    `<unit>:<line>:` line starts one message of its own. `reliable`: the line is the hint's own (an annotation
    error, or ghost code refused where it stands); "Ghost code breaks CFG" names the statement where the CFG
    change starts, which may be real code."""
    messages, lines, position = [], output.splitlines(), 0
    while position < len(lines):
        raw = lines[position]
        position += 1
        if not raw.startswith("["):
            continue
        body = []
        while position < len(lines) and lines[position].startswith(" "):
            body.append(lines[position].strip())
            position += 1
        if "Deferred error" in raw:
            current = None
            for line in body:
                if LOCATION.match(line):
                    current = [line]
                    messages.append(current)
                elif current is not None:
                    current.append(line)
            continue
        if "Parsing" in raw or "aborted" in raw:
            continue
        messages.append([raw.strip()] + [b for b in body if not b[:1].isdigit()])
    found, seen = [], set()
    for block in messages:
        message = " ".join(block)
        if not ERROR_HEAD.search(message) and not LOCATION.match(block[0]):
            continue
        located = LOCATION.search(message)
        error = {"line": int(located.group(1)) if located else None, "message": message[:600],
                 "reliable": "breaks CFG" not in message, "signature": " ".join(LOCATION.sub("", message).split())}
        if (error["line"], error["signature"]) not in seen:
            seen.add((error["line"], error["signature"]))
            found.append(error)
    return found



def _holder(line, merged, hints, alive):
    for index in alive:
        start, end = merged.spans.get(index, (0, -1))
        if start <= line <= end:
            return index
    anchor = _block_above(line, merged)                    # an error at the statement right below a hint block
    inside = [i for i in alive if hints[i]["anchor"] == anchor and i in merged.spans]
    return max(inside, key=lambda i: merged.spans[i][1]) if inside else None


def _block_above(line, merged):
    """The anchor whose inserted block ends right above line `line`, anchor lines between them skipped."""
    lines = merged.text.splitlines()
    above = line - 1
    while above >= 1 and ANCHOR_LINE.match(lines[above - 1]) and \
            not any(last == above for _first, last in merged.blocks.values()):
        above -= 1
    return next((anchor for anchor, (_first, last) in merged.blocks.items() if last == above), None)


def _messages(output):
    keep = [line.strip() for line in output.splitlines()
            if line.strip() and not line.startswith("[kernel] Parsing") and "Frama-C aborted" not in line]
    return " ".join(keep)[:600]


# --- the syntax-tree rules -----------------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {("wp", "strategy"), ("wp", "proof")}
OTHER_NODES = {"logic_type", "type_invariant", "model_field", "code_invariant", "loop_allocation", "code_extension"}


def node_rules(node):
    """The rules a syntax-tree node breaks wherever it stands (empty: the node is on the vocabulary)."""
    kind, found = node["node"], []
    if node.get("kind") == "admit":                    # Frama-C's tree: "axioms are admit lemmas"
        found.append("axiom" if kind == "lemma" else "admit")
    if node.get("kind") == "check":
        found.append("check")
    if node.get("behaviors"):
        found.append("contract")
    if kind == "logic_definition":
        if node["body"] == "inductive":
            found.append("inductive_definition")
        elif node["body"] in ("none", "reads"):
            found.append("bodyless_declaration")
        elif node["recursive"]:
            found.append("recursive_definition")
    elif kind == "axiomatic":
        found.append("axiom")
    elif kind == "module":
        found.append("import" if node.get("loader") else "not_on_vocabulary")
    elif kind == "global_invariant":
        found.append("global_invariant")
    elif kind == "volatile":
        found.append("volatile_clause")
    elif kind == "extension" and (node.get("plugin"), node.get("name")) not in ALLOWED_EXTENSIONS:
        found.append("not_on_vocabulary")
    elif kind in ("contract_clause", "statement_contract"):
        found.append("statement_contract" if kind == "statement_contract" or node.get("of") == "statement"
                     else "contract")
    elif kind == "ghost_function":
        found.append("ghost_function")
    elif kind == "loop_variant":                       # a non-integer measure: the kernel's type check refuses it
        if node.get("relation"):
            found.append("variant_relation")
        elif not node.get("integer"):
            found.append("kind_mismatch")
    elif kind == "loop_assigns":
        if node.get("from"):
            found.append("from_clause")
        if node.get("unbounded_range"):
            found.append("unbounded_range")
    elif kind in OTHER_NODES:
        found.append("not_on_vocabulary")
    return found


def _attribute(nodes, merged, hints, alive):
    """{hint index: [nodes]}: by line span; a node located only by its statement goes to the block right above."""
    owned = {index: [] for index in alive}
    nodes = [n for n in nodes if n.get("file") == UNIT]
    for node in [n for n in nodes if not n.get("at_statement")]:
        for candidate in alive:
            start, end = merged.spans.get(candidate, (0, -1))
            if start <= node["line"] <= end:
                owned[candidate].append(node)
                break
    for node in [n for n in nodes if n.get("at_statement")]:     # after the located nodes: "holds none yet" is final
        anchor = _block_above(node["line"], merged)
        inside = [i for i in alive if hints[i]["anchor"] == anchor]
        pick = [i for i in inside if hints[i]["kind"] == node["node"]] or [i for i in inside if not owned[i]]
        if pick:
            owned[pick[0]].append(node)
    return owned


def _tree_rules(nodes, merged, hints, alive, vocab):
    """{hint index: [(rule, detail)]} for every hint whose syntax tree is not exactly its declared kind."""
    bad = {}
    for index, owned in _attribute(nodes, merged, hints, alive).items():
        kind = hints[index]["kind"]
        allowed = set(vocab.kinds[kind]["nodes"])
        found = []
        for node in owned:
            for rule in node_rules(node):
                found.append((rule, f"{_describe(node)} (line {node['line'] - merged.spans[index][0] + 1} of the hint)"))
        if not found:
            single = kind != "ghost"
            shape = [n for n in owned if n["node"] in allowed]
            if kind in ("predicate", "logic"):
                shape = [n for n in shape if n.get("predicate") == (kind == "predicate")]
            if not owned:
                found.append(("kind_mismatch", f"the text holds no {kind} annotation"))
            elif len(shape) != len(owned) or (single and len(owned) != 1):
                found.append(("kind_mismatch", f"declared {kind}; the syntax tree holds "
                                               f"{', '.join(_describe(n) for n in owned)}"))
        if found:
            bad[index] = sorted(set(found))
    return bad


def _describe(node):
    detail = node["node"]
    for key in ("kind", "clause", "body", "name"):
        if node.get(key):
            detail += f" {key}={node[key]}"
    return detail
