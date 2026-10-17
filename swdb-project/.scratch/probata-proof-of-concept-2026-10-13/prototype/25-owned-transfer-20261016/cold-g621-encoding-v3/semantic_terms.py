"""2026-10-16 ET. Independent mathematical ownership terms; no project imports.

This compares retained syntax. It never invokes or implements a prover. Unknown
lowerings are unresolved, not new assumptions. The source theory pin and complete
antecedents are separate inputs to the cold observation.
"""
import hashlib
import itertools
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


def substitute(tree, mapping):
    if isinstance(tree, str):
        return mapping.get(tree, tree)
    if tree and tree[0] in ("forall", "exists"):
        bound = {row[0] for row in tree[1]}
        local = {k: v for k, v in mapping.items() if k not in bound}
        # Source and driver use disjoint bound names for definition application.
        # Reject potential capture rather than silently alpha-renaming a binder.
        free = set().union(*(symbols(v) for v in local.values())) if local else set()
        need(not bound & free, "capture-free substitution")
        return [tree[0], tree[1], substitute(tree[2], local)]
    return [substitute(v, mapping) for v in tree]


def symbols(tree):
    if isinstance(tree, str):
        return {tree}
    return set().union(*(symbols(x) for x in tree)) if tree else set()


def canon(tree, env=None, depth=0, binder_depth=0):
    """Only alpha-renaming, let substitution and explicit propositional identities.

    Binder depth is separate from resource/traversal depth so inert lets and
    connective wrappers cannot rename otherwise identical bound variables.
    No antecedent is dropped. Quantifier reordering is limited to a same-kind
    adjacent block; conjunction/disjunction order and equality symmetry are
    normalized. There is no existential-witness elimination or arithmetic solver.
    """
    env = {} if env is None else env
    need(depth < 120, "normalization depth")
    if isinstance(tree, str):
        return env.get(tree, tree)
    need(bool(tree), "empty expression refused")
    head = tree[0]
    if head == "!":
        # Attributes affect triggers/labels, not the asserted formula. Retain the
        # original full command digest in the reader's census.
        need(len(tree) >= 4 and len(tree) % 2 == 0 and
             all(isinstance(tree[i], str) and tree[i].startswith(":")
                 for i in range(2, len(tree), 2)), "closed SMT annotation shape")
        return canon(tree[1], env, depth + 1, binder_depth)
    if head == "let":
        need(len(tree) == 3 and all(len(r) == 2 for r in tree[1]), "let shape")
        names = [r[0] for r in tree[1]]
        need(len(names) == len(set(names)), "unique simultaneous let names")
        additions = {r[0]: canon(r[1], env, depth + 1, binder_depth) for r in tree[1]}
        return canon(tree[2], {**env, **additions}, depth + 1, binder_depth)
    if head in ("forall", "exists"):
        need(len(tree) == 3, "quantifier shape")
        bindings = list(tree[1])
        body = tree[2]
        while isinstance(body, list) and body and body[0] == head:
            bindings += body[1]
            body = body[2]
        need(all(len(r) == 2 and isinstance(r[0], str) for r in bindings), "binder shape")
        need(len({r[0] for r in bindings}) == len(bindings), "no shadowed merged binder")
        groups = {}
        for name, typ in bindings:
            groups.setdefault(json.dumps(typ, sort_keys=True), []).append(name)
        ways = 1
        for names in groups.values():
            for n in range(1, len(names) + 1):
                ways *= n
        need(ways <= 720, "bounded alpha permutations")
        keys = sorted(groups)
        candidates = []
        for choices in itertools.product(*(itertools.permutations(groups[k]) for k in keys)):
            names = {name: "@%d:%s:%d" % (binder_depth, key, index)
                     for key, choice in zip(keys, choices) for index, name in enumerate(choice)}
            candidates.append(canon(body, {**env, **names}, depth + 1, binder_depth + 1))
        return [head, [[k, len(groups[k])] for k in keys],
                min(candidates, key=lambda x: json.dumps(x, sort_keys=True))]
    if head == "=>" and len(tree) > 3:
        return canon(["=>", tree[1], ["=>", *tree[2:]]], env, depth + 1, binder_depth)
    args = [canon(x, env, depth + 1, binder_depth) for x in tree[1:]]
    if head in ("and", "or"):
        flat = []
        for value in args:
            flat.extend(value[1:] if isinstance(value, list) and value and value[0] == head else [value])
        args = sorted(flat, key=lambda x: json.dumps(x, sort_keys=True))
        if len(args) == 1:
            return args[0]
    if head == "=" and len(args) == 2:
        args.sort(key=lambda x: json.dumps(x, sort_keys=True))
    if head == "+":
        # Standard mathematical SMT '+' only: preserve each complete operand.
        # No FP/BV/custom operator or association/tree shape is changed.
        args.sort(key=lambda x: json.dumps(x, sort_keys=True))
    if head == "=>" and len(args) == 2:
        antecedents = [args[0]]
        conclusion = args[1]
        while isinstance(conclusion, list) and len(conclusion) == 3 and conclusion[0] == "=>":
            antecedents.append(conclusion[1])
            conclusion = conclusion[2]
        if len(antecedents) > 1:
            complete = []
            for premise in antecedents:
                complete.extend(premise[1:] if isinstance(premise, list) and premise and premise[0] == "and" else [premise])
            complete.sort(key=lambda x: json.dumps(x, sort_keys=True))
            return ["=>", ["and", *complete], conclusion]
    return [env.get(head, head) if isinstance(head, str) else head, *args]


def one(text):
    result = forms(text)
    need(len(result) == 1, "one independent term")
    return result[0]


# Independently transcribed from the pinned, definition-only Owners theory.
# mk_state is a comparison-level constructor name; an actual datatype must bind
# that role with exactly active/backing selector types before this alias is used.
DEFINITIONS = {
    "active_owner": ("(s state) (r Int)", "(= (select (active s) r) true)"),
    "buffer": ("(s state) (r Int)", "(select (backing s) r)"),
    "exclusive": ("(s state)", "(forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) true) (not (= (select (backing s) r) 0)) (= (select (backing s) r) (select (backing s) q))) (= r q)))"),
    "valid": ("(s state) (frontier Int)", "(and (< 0 frontier) (exclusive s) (forall ((r Int)) (=> (= (select (active s) r) true) (and (< 0 r) (< r frontier) (<= 0 (select (backing s) r)) (< (select (backing s) r) frontier)))) (forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) true) (not (= (select (backing s) r) 0))) (not (= (select (backing s) r) q)))))"),
    "begin_owner": ("(s state) (r Int)", "(mk_state (store (active s) r true) (store (backing s) r 0))"),
    "bind": ("(s state) (r Int) (b Int)", "(mk_state (active s) (store (backing s) r b))"),
    "move": ("(s state) (destination Int) (source Int)", "(mk_state (active s) (store (store (backing s) destination (select (backing s) source)) source 0))"),
    "swap": ("(s state) (left Int) (right Int)", "(ite (= left right) s (mk_state (active s) (store (store (backing s) left (select (backing s) right)) right (select (backing s) left))))"),
    "retire": ("(s state) (r Int)", "(mk_state (store (active s) r false) (store (backing s) r 0))"),
}

GOALS = {
    "empty.valid": ("(frontier Int)", "(=> (< 0 frontier) (valid (empty 0) frontier))"),
    "receiver.fresh": ("(s state) (frontier Int)", "(=> (valid s frontier) (and (valid (begin_owner s frontier) (+ frontier 1)) (active_owner (begin_owner s frontier) frontier) (= (buffer (begin_owner s frontier) frontier) 0)))"),
    "buffer.fresh": ("(s state) (frontier Int) (r Int)", "(=> (and (valid s frontier) (active_owner s r) (= (buffer s r) 0)) (and (valid (bind s r frontier) (+ frontier 1)) (= (buffer (bind s r frontier) r) frontier)))"),
    "move.transfer": ("(s state) (frontier Int) (destination Int) (source Int)", "(=> (and (valid s frontier) (active_owner s destination) (active_owner s source) (not (= destination source)) (= (buffer s destination) 0)) (and (valid (move s destination source) frontier) (= (buffer (move s destination source) destination) (buffer s source)) (= (buffer (move s destination source) source) 0)))"),
    "move.frame": ("(s state) (destination Int) (source Int) (q Int)", "(=> (and (not (= q destination)) (not (= q source))) (and (= (active_owner (move s destination source) q) (active_owner s q)) (= (buffer (move s destination source) q) (buffer s q))))"),
    "swap.exchange": ("(s state) (frontier Int) (left Int) (right Int)", "(=> (and (valid s frontier) (active_owner s left) (active_owner s right)) (and (valid (swap s left right) frontier) (= (buffer (swap s left right) left) (buffer s right)) (= (buffer (swap s left right) right) (buffer s left))))"),
    "swap.frame": ("(s state) (left Int) (right Int) (q Int)", "(=> (and (not (= q left)) (not (= q right))) (and (= (active_owner (swap s left right) q) (active_owner s q)) (= (buffer (swap s left right) q) (buffer s q))))"),
    "swap.self": ("(s state) (r Int)", "(= (swap s r r) s)"),
    "retire.frame": ("(s state) (frontier Int) (r Int) (q Int)", "(=> (and (valid s frontier) (active_owner s r) (not (= q r))) (and (valid (retire s r) frontier) (not (active_owner (retire s r) r)) (= (buffer (retire s r) r) 0) (= (active_owner (retire s r) q) (active_owner s q)) (= (buffer (retire s r) q) (buffer s q)) (=> (and (active_owner s q) (not (= (buffer s r) 0))) (and (not (= (buffer s q) (buffer s r))) (not (= q (buffer s r)))))))"),
    "shared_backing.rejected": ("(s state) (r Int) (q Int)", "(=> (and (active_owner s r) (active_owner s q) (not (= r q)) (not (= (buffer s r) 0)) (= (buffer s r) (buffer s q))) (not (exclusive s)))"),
}


def source_goal(ident):
    bindings, body = GOALS[ident]
    return one("(not (forall (" + bindings + ") " + body + "))")


def definition_expected(name):
    bindings, body = DEFINITIONS[name]
    return one("(forall (" + bindings + ") " + body + ")")


def task_semantics(text, ident, support):
    commands = forms(text)
    allowed = {"set-logic", "set-info", "set-option", "declare-sort", "declare-fun",
               "declare-const", "declare-datatypes", "declare-datatype", "define-fun",
               "assert", "check-sat", "get-info"}
    need(all(isinstance(c, list) and c and isinstance(c[0], str) and c[0] in allowed
             for c in commands), "closed SMT command census")
    checks = [i for i, c in enumerate(commands) if c[0] == "check-sat"]
    need(len(checks) == 1 and commands[checks[0]] == ["check-sat"] and
         all(c == ["get-info", ":reason-unknown"] for c in commands[checks[0] + 1:]),
         "single complete SMT query/epilogue")
    assertions = [c[1] for c in commands if c[0] == "assert" and len(c) == 2]
    need(len(assertions) == sum(c[0] == "assert" for c in commands) and assertions,
         "complete assertion shapes")
    goal = assertions[-1]
    expected = source_goal(ident)
    goal_equal = canon(goal) == canon(expected)
    definitions = []
    # This first passive capture deliberately has no blessed record/empty-map
    # driver encoding. Even a coincidentally equal surface goal cannot bypass
    # complete source-to-SMT definition/type/constant-map attribution. A reviewed
    # successor must close this item against retained physical term metadata.
    unresolved = [{"kind": "Owners_record_and_empty_map_encoding_not_yet_admitted"}]
    for c in commands:
        if c[0] != "define-fun":
            continue
        need(len(c) == 5 and isinstance(c[1], str), "definition shape")
        name = c[1]
        role = name if name in DEFINITIONS else None
        matched = role is not None and canon(["forall", c[2], c[4]]) == canon(definition_expected(role))
        definitions.append({"name": name, "form_sha256": digest(c),
                            "role": role, "source_definition_equivalent": matched})
        if role is not None and not matched:
            unresolved.append({"kind": "source_definition", "name": name, "sha256": digest(c)})
    attribution = []
    for assertion in assertions[:-1]:
        key = digest(assertion)
        names = symbols(assertion)
        need(not any("t25_owned" in s or s.startswith(("check_lemma_", "wp_goal")) for s in names),
             "no desired or sibling theorem premise")
        row = {"sha256": key, "symbols": sorted(names), "source_attribution": support.get(key)}
        attribution.append(row)
        if key not in support:
            unresolved.append({"kind": "support_assertion", "sha256": key,
                               "symbols": sorted(names)})
    if not goal_equal:
        unresolved.append({"kind": "goal_lowering", "actual_sha256": digest(goal),
                           "expected_sha256": digest(expected), "symbols": sorted(symbols(goal))})
    # No unknown definition/datatype/declaration is implicitly admitted as a
    # source theorem. Full command hashes and symbol/type inventories are emitted
    # for independent attribution; semantic acceptance needs a reviewed complete
    # encoding map, including Owners record/empty-map lifting.
    unresolved += [{"kind": "encoding_declaration", "command": c[0],
                    "name": c[1] if isinstance(c[1], str) else None,
                    "sha256": digest(c)} for c in commands
                   if c[0] in {"declare-datatypes", "declare-datatype"} or
                   c[0] == "define-fun" and c[1] not in DEFINITIONS]
    return {"commands": [{"index": i, "kind": c[0], "sha256": digest(c)}
                         for i, c in enumerate(commands)],
            "goal_sha256": digest(goal), "goal_equivalent": goal_equal,
            "expected_goal_sha256": digest(expected), "definitions": definitions,
            "support_assertions": attribution, "unresolved": unresolved,
            "complete_semantic_match": not unresolved,
            "actual_submission_attested": False}
