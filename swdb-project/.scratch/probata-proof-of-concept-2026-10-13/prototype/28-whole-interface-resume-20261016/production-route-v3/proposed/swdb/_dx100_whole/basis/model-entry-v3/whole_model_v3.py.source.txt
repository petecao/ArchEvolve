"""2026-10-16 ET. Pure checked-body model assembly, not source admission.

The producer supplies the actual compiler-certified ABI/ordinary-object atlas.
This emitter reuses the exact reviewed source binder and fixed concrete bodies.
It never turns the illustrative ABI/address headers into a source certificate.
The resulting packet remains inert until the public source/method consumer is
integrated and independently admitted. No WP summary is provided by this form.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import stat


KIND = "dx100-whole-interface-checked-body-1"
DESIGN_SHA = "a6139eea1e141c68bb351026b7cdb38a2458eb4b8be3a772a8251a7060db6e1c"
DISPATCH_SHA = "a2652610ae6198b7a3045e30155c77bfd9637a79ae2c9b668407ee5ae8eb7e9a"
BINDER_SHA = "074b974f4a4dd1074247a90d2a727d1cb0ee37b576055d738dd746fd6d4cc1db"
BACKENDS = (
    ("whole_value_backend_v1.h", "c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f"),
    ("whole_adapters.h", "e8efe60182d7fbd0d7c9f54c8fc6f70c235a91bd613cabd3be6ac893105c4a1a"),
    ("whole_value_builders_v1.h", "88f6bd0d310e8a2a6ad522ae15fec32b9f32b4ed6d792a314e8a365e0118824e"),
    ("whole_closed_routes_v1.h", "0168b2f78e0d5a6a6d42c8955ba45304533b8a0c63b92bebcabd50fd730969c7"),
)


class Refused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def stable_metadata(value):
    """Read-stable identity/content metadata; access time is observational."""
    return tuple(getattr(value, name) for name in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns", "st_ctime_ns"))


def read_pin(path, expected=None):
    path = Path(path)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path,
         "canonical regular assembly input required")
    raw = path.read_bytes()
    need(stable_metadata(path.lstat()) == stable_metadata(before), "assembly input changed while reading")
    row = {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}
    need(expected is None or row["sha256"] == expected, "frozen assembly input differs")
    return raw, row


def owned_module(path, expected):
    raw, pin = read_pin(path, expected)
    tree = ast.parse(raw)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            need(all(alias.name in {"hashlib", "json", "re"} for alias in node.names),
                 "unexpected owned module import")
        if isinstance(node, ast.ImportFrom):
            need(node.module == "pathlib", "unexpected owned module import")
    namespace = {"__name__": "inert_checked_body_assembly", "__file__": str(path)}
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace, pin


def checked_design(path):
    raw, pin = read_pin(path, DESIGN_SHA)
    design = json.loads(raw)
    calls = design["calls"]
    need(type(calls) is list and len(calls) == 26
         and len({row["call"] for row in calls}) == 26, "one contract per name required")
    need(sum(len(row["source_declarations"]) for row in calls) == 27,
         "complete two-header declaration inventory required")
    need(sum(len(row["typed_arity_instances"]) for row in calls) == 132,
         "complete exact source type/arity inventory required")
    for row in calls:
        contract = row["contract"]
        need(bool(contract["asserted_domain_checks"])
             and bool(contract["normal_return_state_value_relation"])
             and bool(contract["source_basis"])
             and set(contract["owned_rules"]) == {"compiler", "mmio", "numeric_runtime"},
             "checked domains, values and cited/owned rules required")
        need(row["execution"]["body"].startswith("Generated dws_"),
             "call must execute its fixed concrete body")
    return design, pin


def check_contract_inventory(calls, declarations):
    """Future validator seam: deleting even one source-name contract refuses.

    This structural gate does not establish the bodies' value correspondence;
    exact checked_design identity and source/model pins provide that boundary.
    """
    need(type(calls) is list and len(calls) == 26
         and len({row.get("call") for row in calls if type(row) is dict}) == 26,
         "exactly one checked-body contract for every interface name required")
    need({row["call"] for row in calls} == {row["name"] for row in declarations},
         "complete original interface contract inventory required")
    for row in calls:
        actual = row.get("source_declarations")
        expected = [item for item in declarations if item["name"] == row["call"]]
        need(type(actual) is list and len(actual) == len(expected),
             "every overload declaration needs its original source binding")


def hook_text(choice_budget):
    """All finite choices use independent harness draws and a fatal budget.

    These are future harness draws, not zero-initialized ghost assumptions. The
    public harness consumer must fill every uint32 entry independently before
    the source unit executes, and bind that draw plan in its method identity.
    Modulo maps the entire uint32 domain onto every positive uint32-sized choice domain; the draw count budget is independent of the alternative count.
    No source/capacity check or desired result is assumed by this emitter.
    """
    need(type(choice_budget) is int and 1 <= choice_budget <= 256,
         "bounded independently drawn choice table required")
    return """/* Checked-body hooks: preserve every ordinary property. */
#include <stdint.h>
#include <stddef.h>
#ifndef SWDB_CHECK
#error "public checked-property hooks must precede model assembly"
#endif
static uint32_t dws_choice_table[%d];
static unsigned dws_choice_used;
static unsigned dws_model_choose(unsigned alternatives) {
  SWDB_CHECK(alternatives>0,"whole-choice-domain");
  SWDB_CHECK(dws_choice_used<%du,"whole-choice-capacity");
  return dws_choice_table[dws_choice_used++] %% alternatives;
}
#define DXM_CHECK(condition,rule) SWDB_CHECK((condition),rule)
#define DXM_CHOOSE(alternatives) dws_model_choose(alternatives)
""" % (choice_budget, choice_budget)


def assemble(whole, project, *, abi, objects, choice_budget=128):
    """Return inert C/entry data. The actual producer supplies ABI and objects.

    This function is an emitter and carries no admission boolean that can
    authorize a source transformation. Public lowering must independently bind
    the original complete TU, all evaluated expressions and CPU effects before
    consuming these bytes. Actual and illustrative caller data remain distinct.
    """
    whole, project = Path(whole).resolve(strict=True), Path(project).resolve(strict=True)
    design, design_pin = checked_design(whole / "new-0.2-contract-design-v1.json")
    source, source_pin = owned_module(whole / "source_dispatch_v2.py", DISPATCH_SHA)
    binder, binder_pin = owned_module(whole / "whole_interface_v3.py", BINDER_SHA)
    declarations = binder["inventory"](project)
    names = {row["name"] for row in declarations}
    need(names == {row["call"] for row in design["calls"]},
         "contract names differ from pinned source inventory")
    check_contract_inventory(design["calls"], declarations)
    atlas = source["prepare_atlas"](objects)
    routes, instances = source["render_routes"](binder, declarations, abi)
    need(len(instances) == 132, "actual ABI routing lost a typed/arity instance")
    parts, pins = [hook_text(choice_budget)], [design_pin, source_pin, binder_pin]
    for item in design["inputs"]:
        _raw, pin = read_pin(item["path"], item["sha256"])
        need(pin["bytes"] == item["bytes"], "frozen contract design input size differs")
        if pin not in pins:
            pins.append(pin)
    for name, sha in BACKENDS:
        raw, row = read_pin(whole / name, sha)
        need(not re.search(rb'^\s*#\s*include\s*"', raw, re.M),
             "unchecked local include in fixed concrete model")
        parts.append(raw.decode("utf-8")); pins.append(row)
    parts += [source["render_direct_families"](binder, declarations),
              source["render_pointer_bridge"](atlas), routes]
    body = "\n".join(parts) + "\n"
    # The generated fixed wrapper bodies are preserved as code, never summaries.
    emitted = set(re.findall(r"\b(dws_[A-Za-z0-9_]+)\s*\([^;{}]*\)\s*\{", routes))
    need(all(row["c_name"] in emitted for row in instances),
         "a source-call concrete wrapper body is missing")
    for row in pins:
        need(read_pin(row["path"])[1] == row, "assembly input changed after emission")
    entry = {**design["prospective_entry"], "kind": "proof_semantics", "target": "dx100-mmio",
        "contract_form": KIND, "calls": design["calls"],
        "model": {"execution": "checked-concrete-C", "sha256": digest(body.encode()),
                  "source_inputs": pins, "source_atlas_sha256": digest(canonical(atlas)),
                  "supplied_abi_sha256": digest(canonical(abi))},
        "harness_draws": {"object": "dws_choice_table", "scalar_type": "uint32_t",
                          "count": choice_budget, "independent": True, "draw_before_source_unit": True},
        "WP": "unsupported contract form; never use as an assumed summary",
        "receiver_state_policy": "Public source/harness consumer must bind source globals and receiver state; assembly grants no fresh zero device, payload initialization or ownership.",
        "source_producer_admission": "required at public consumer; this emitter cannot grant it",
        "source_preconditions_assumed": False, "public_admission": False,
        "current_0_2": False, "full_ticket28": False}
    return {"entry": entry, "c_text": body, "instances": instances, "atlas": atlas}
