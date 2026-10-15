"""The method-version file and the failure-class vocabulary (Probata proof of concept, ticket 11).

Created: 2026-10-14 ET. Updated: 2026-10-14 02:26 ET (failure class spurious_counterexample,
tied to the unreplayed_counterexample field; Yan-Ru's decision of 02:25 ET). Seams 1 and 4 of the formal-verification map's spec: `swdb validate`,
`swdb prove` (scripted adapter) and `swdb build`. Fixture method-version file only (evidence_kind
contract_fixture); no real verifier runs.
"""

import shutil

import pytest
import yaml

from conftest import FIXTURES, run_swdb
from swdb import paths, vocab
from test_proof_records import proof_seed, seed  # noqa: F401  (the certified fixture candidate artifact)

FAILURE_CLASSES = {"parse_error", "unsupported_construct", "unwinding_bound_too_small", "timeout",
                   "out_of_memory", "solver_error", "tool_crash", "vacuous_pass",      # 11 item 9
                   "unknown", "ghost_capacity", "memory_domain",                        # S3, DX admission
                   "hint_budget_spent",                                                 # 13
                   "below_minimum_bounds",                                              # 19
                   "spurious_counterexample"}                    # Yan-Ru 2026-10-14 02:25 ET (from 05)
SKIP_REASONS = {"no_contract_proof", "no_minimum_bounds", "outside_cpp_subset"}         # 25
UNREPLAYED = {"inputs": {"vertices": 3}, "replay": "the compiled code met the unit relation on these inputs"}


# --- the failure-class vocabulary --------------------------------------------------------

def test_the_vocabulary_holds_exactly_the_listed_failure_classes_and_skip_reasons_each_with_a_handler():
    vocabs, problems = vocab.load_all(paths.VOCAB)
    assert not problems
    entries = vocabs.entries["proof_failure_classes"]
    by_role = {}
    for value, entry in entries.items():
        by_role.setdefault(entry["role"], set()).add(value)
    assert by_role == {"failure_class": FAILURE_CLASSES, "skip_reason": SKIP_REASONS}
    assert all(entry["handler"].strip() for entry in entries.values())


# --- the method-version file -----------------------------------------------------------------

METHOD_FIXTURE = FIXTURES / "proof" / "methods" / "contract-fixture-1.yaml"
SECTIONS = ["lineup", "civl", "genmc", "openmp_runtime", "c_lowering", "acsl_version", "proof_hint_vocabulary",
            "checks", "budgets", "prompts", "shared_action_kinds", "sharing_classes", "logic_library", "models",
            "rocq_development", "ghost_capacity_k"]


class _Library:
    """An empty records folder with a library beside it that holds only method-version files."""

    def __init__(self, root):
        self.records = root / "records"
        self.records.mkdir()
        self.methods = root / "library" / "methods"
        self.methods.mkdir(parents=True)

    def write(self, data, name="contract-fixture-1"):
        path = self.methods / f"{name}.yaml"
        path.write_text(yaml.safe_dump(data, sort_keys=False))
        return path

    def validate(self):
        return run_swdb("validate", "--records", self.records)


@pytest.fixture
def library(tmp_path):
    return _Library(tmp_path)


def _method():
    return yaml.safe_load(METHOD_FIXTURE.read_text())


def _refused(library, path, field, reason):
    result = library.validate()
    assert result.returncode == 1, result.stdout + result.stderr
    problems = [line for line in result.stderr.splitlines() if path.name in line and field in line]
    assert problems and reason in problems[0], result.stderr


def test_validate_accepts_the_contract_fixture_method_version_with_every_section(library):
    data = _method()
    assert data["evidence_kind"] == "contract_fixture"
    assert set(SECTIONS) <= set(data)
    assert {"tool": "clang", "version": "22.1.8"}.items() <= next(e for e in data["lineup"] if e["tool"] == "clang").items()
    shutil.copy(METHOD_FIXTURE, library.methods / METHOD_FIXTURE.name)
    result = library.validate()
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("section", SECTIONS)
def test_validate_names_a_missing_section(library, section):
    data = _method()
    del data[section]
    _refused(library, library.write(data), section, "required section is missing")


@pytest.mark.parametrize("section, part", [
    ("c_lowering", "subset"), ("c_lowering", "translators"), ("c_lowering", "naming_rules"),
    ("checks", "proof_setup_check"), ("checks", "proof_hint_check"), ("checks", "verdict_reading"),
    ("logic_library", "sum_library"), ("models", "std_vector"), ("models", "std_pair"),
    ("rocq_development", "composition_theorem"), ("rocq_development", "dx100_reduction_lemma"),
])
def test_validate_names_a_missing_part_of_a_section(library, section, part):
    data = _method()
    del data[section][part]
    _refused(library, library.write(data), f"{section}.{part}", "required")


def test_validate_names_a_check_without_its_version(library):
    data = _method()
    del data["checks"]["verdict_reading"]["version"]
    _refused(library, library.write(data), "checks.verdict_reading.version", "each check has its version")


# --- exact pins ----------------------------------------------------------------------------

def _clang(data):
    return next(entry for entry in data["lineup"] if entry["tool"] == "clang")


@pytest.mark.parametrize("version", [">=22.1", "22.x", "~22.1.8", "^22.1.8", "22.1.0-22.1.8", "latest", "22.*", ""])
def test_a_lineup_version_that_is_not_one_exact_version_fails(library, version):
    data = _method()
    _clang(data)["version"] = version
    _refused(library, library.write(data), "lineup.0.version", "one exact version")


def test_a_lineup_entry_without_a_flags_field_fails(library):
    data = _method()
    del _clang(data)["flags"]
    _refused(library, library.write(data), "lineup.0.flags", "flags")


def test_an_explicit_empty_flags_list_passes(library):
    data = _method()
    _clang(data)["flags"] = []
    library.write(data)
    result = library.validate()
    assert result.returncode == 0, result.stderr


# --- budgets -------------------------------------------------------------------------------

BUDGETS = {"hint_rounds": 10, "hint_loop_wall_minutes": 60, "bounded_job_minutes": 15,   # 25 item 2
           "counterexample_repair_rounds": 5,
           "wp_seconds_per_solver": 30,                                                  # 13 item 11
           "civl_k": 3}                                                                  # 15 item 9, S8


def test_the_fixture_budgets_are_the_starting_values():
    assert _method()["budgets"] == BUDGETS


@pytest.mark.parametrize("budget", sorted(BUDGETS))
def test_removing_a_budget_fails_and_names_it(library, budget):
    data = _method()
    del data["budgets"][budget]
    _refused(library, library.write(data), f"budgets.{budget}", "required")


# --- drafts --------------------------------------------------------------------------------

def test_a_draft_may_mark_a_section_not_yet_built_and_a_frozen_file_may_not(library):
    data = _method()
    data["status"] = "draft"
    data["rocq_development"] = {"not_yet_built": "Tickets 41-43 write the Rocq development."}
    path = library.write(data)
    result = library.validate()
    assert result.returncode == 0, result.stderr
    data["status"] = "frozen"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    _refused(library, path, "rocq_development", "only a draft")


# --- lifecycle: current means frozen; a draft is used only when named (fix-21, 2026-10-14) ---------

def _version(data, name, sequence, status):
    return {**data, "id": f"method.{name}", "sequence": sequence, "status": status}


def test_current_is_the_highest_sequence_frozen_version_never_a_higher_draft(library):
    from swdb import method_version
    data = _method()
    library.write(_version(data, "contract-fixture-1", 1, "frozen"), "contract-fixture-1")
    library.write(_version(data, "contract-fixture-2", 2, "frozen"), "contract-fixture-2")
    library.write(_version(data, "contract-fixture-3", 3, "draft"), "contract-fixture-3")
    root = library.methods.parent
    assert method_version.current(root).id == "method.contract-fixture-2"
    assert method_version.named(root, "method.contract-fixture-3").data["status"] == "draft"
    assert method_version.named(root, "method.never-written") is None
    assert library.validate().returncode == 0


def test_with_only_drafts_there_is_no_current_method_version(library):
    from swdb import method_version
    library.write(_version(_method(), "contract-fixture-1", 1, "draft"))
    assert method_version.current(library.methods.parent) is None
    assert library.validate().returncode == 0


def test_two_frozen_versions_may_not_share_a_sequence_but_a_draft_may_share_one(library):
    data = _method()
    library.write(_version(data, "contract-fixture-1", 1, "frozen"), "contract-fixture-1")
    draft = library.write(_version(data, "draft-1", 1, "draft"), "draft-1")
    assert library.validate().returncode == 0, library.validate().stderr
    draft.unlink()
    _refused(library, library.write(_version(data, "frozen-1", 1, "frozen"), "frozen-1"), "sequence",
             "also used by")


# --- every proof record pins the method version ------------------------------------------------

def _method_file(seed):
    return seed.root / "library" / "methods" / METHOD_FIXTURE.name


def test_prove_pins_the_current_method_version_by_id_and_file_sha256(seed):
    import hashlib
    record = seed.prove(seed.script())["record"]
    sha = hashlib.sha256(_method_file(seed).read_bytes()).hexdigest()
    assert record["pins"]["method_version"] == {"id": "method.contract-fixture-1", "sha256": sha}
    assert seed.swdb("validate").returncode == 0


def test_prove_pins_the_method_version_with_the_highest_sequence(seed):
    data = _method()
    data.update(id="method.contract-fixture-2", sequence=2)
    (_method_file(seed).parent / "contract-fixture-2.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    record = seed.prove(seed.script())["record"]
    assert record["pins"]["method_version"]["id"] == "method.contract-fixture-2"


def _draft(seed, name="contract-fixture-2", sequence=2):
    data = _version(_method(), name, sequence, "draft")
    (_method_file(seed).parent / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    return f"method.{name}"


def test_prove_never_pins_a_draft_it_was_not_given_even_with_a_higher_sequence(seed):
    _draft(seed)
    record = seed.prove(seed.script())["record"]
    assert record["pins"]["method_version"]["id"] == "method.contract-fixture-1"


def test_prove_pins_a_draft_named_with_method_version_and_validate_accepts_it(seed):
    import hashlib
    draft = _draft(seed)
    record = seed.prove(seed.script(), "--method-version", draft)["record"]
    sha = hashlib.sha256((_method_file(seed).parent / "contract-fixture-2.yaml").read_bytes()).hexdigest()
    assert record["pins"]["method_version"] == {"id": draft, "sha256": sha}
    assert seed.swdb("validate").returncode == 0


def test_prove_refuses_a_method_version_name_with_no_file(seed):
    result = seed.prove(seed.script(), "--method-version", "method.never-written", ok=False)
    assert result.returncode == 1 and "method.never-written" in result.stderr
    assert not seed.proof_files()


def test_prove_with_only_a_draft_refuses_unless_the_draft_is_named(seed):
    _method_file(seed).unlink()
    draft = _draft(seed, "contract-fixture-1", 1)
    result = seed.prove(seed.script(), ok=False)
    assert result.returncode == 1 and "frozen" in result.stderr and "--method-version" in result.stderr
    assert not seed.proof_files()
    assert seed.prove(seed.script(), "--method-version", draft)["record"]["pins"]["method_version"]["id"] == draft


# --- the real draft in library/methods/ (fix-21) ----------------------------------------------------

REAL_DRAFT = "method.probata-draft-1"


def test_the_repository_draft_validates_and_is_never_current():
    from swdb import method_version
    root = paths.HOME / "library"
    assert method_version.validate(root) == []
    assert method_version.current(root) is None or method_version.current(root).id != REAL_DRAFT
    draft = method_version.named(root, REAL_DRAFT)
    assert draft is not None and draft.data["status"] == "draft" and draft.data["evidence_kind"] == "execution"


def test_the_repository_draft_holds_the_mac_lineup_and_the_starting_budgets():
    from swdb import method_version, proof, wp_adapter  # noqa: F401  (proof first: wp_adapter imports it)
    data = method_version.named(paths.HOME / "library", REAL_DRAFT).data
    tools = {(row["role"], row["tool"]): row for row in data["lineup"]}
    versions = {key: row["version"] for key, row in tools.items()}
    assert versions[("unbounded_verifier", "frama-c-wp")] == "33.0"
    assert versions[("bounded_verifier", "cbmc")] == "6.11"            # Yan-Ru 2026-10-14 13:19 ET
    assert versions[("concurrent_bounded_verifier", "civl")] == "1.23"
    assert versions[("second_refuter", "genmc")] == "0.19.0"
    assert versions[("proof_assistant", "rocq")] == "9.3.0"
    assert versions[("front_end", "clang")] == "22.1.8"
    assert {tool for role, tool in versions if role == "solver"} == {"alt-ergo", "z3", "cvc5"}
    assert not any(tool == "saw" for _role, tool in versions)        # CBMC replaced SAW (ticket 09)
    flags = tools[("unbounded_verifier", "frama-c-wp")]["flags"]
    for flag, value in (*wp_adapter.FROZEN, ("-wp-par", "1")):        # -wp-par 1: hard goals (ticket 08)
        assert flag in flags and flags[flags.index(flag) + 1] == value
    assert data["budgets"] == BUDGETS


def test_the_repository_draft_pins_logic_sum_as_its_sum_library_and_each_shared_logic_file():
    from swdb import artifacts, logic_library, method_version
    root = paths.HOME / "library"
    section = method_version.named(root, REAL_DRAFT).data["logic_library"]
    files = logic_library.files(root)
    assert section["sum_library"] == files["logic.sum"].pin() and section["sum_library"]["version"] == "1.0"
    assert section["files"] and all(pin == files[pin["id"]].pin() for pin in section["files"])
    assert section["sha256"] == artifacts.digest(section["files"])       # the library's hash: its file pins


def test_prove_logic_also_names_a_draft_with_method_version(library):
    result = run_swdb("prove-logic", "--records", library.records, "--runs-dir", library.records.parent / "runs",
                      "--lemmas", "logic.sum", "--method-version", "method.never-written")
    assert result.returncode == 1 and "method.never-written" in result.stderr, result.stderr + result.stdout


def test_a_reference_takes_an_optional_dotted_version_and_nothing_else(library):
    data = _method()
    data["logic_library"]["sum_library"]["version"] = "1.0"
    path = library.write(data)
    assert library.validate().returncode == 0, library.validate().stderr
    data["logic_library"]["sum_library"]["version"] = "latest"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    _refused(library, path, "logic_library.sum_library.version", "version")


def test_prove_refuses_to_run_without_a_method_version_file(seed):
    _method_file(seed).unlink()
    result = seed.prove(seed.script(), ok=False)
    assert result.returncode == 1 and "method-version file" in result.stderr
    assert not seed.proof_files()


def _edit_method_file_in_place(seed):
    path = _method_file(seed)
    path.write_text(path.read_text().replace("ghost_capacity_k: 8", "ghost_capacity_k: 9"))


def _pin_a_missing_file(seed):
    path = seed.proof_files()[0]
    _rewrite(path, lambda r: r["pins"]["method_version"].update(id="method.never-written"))


@pytest.mark.parametrize("change, reason", [
    (_edit_method_file_in_place, "does not match"),
    (_pin_a_missing_file, "no method-version file"),
])
def test_validate_rejects_a_method_version_pin_that_does_not_resolve(seed, change, reason):
    seed.prove(seed.script())
    change(seed)
    path = seed.proof_files()[0]
    problems = _problems(seed, path, "pins.method_version")
    assert problems and reason in problems[0]


# --- every listed class records; skips record --------------------------------------------------

def _build_rows(seed, query):
    import sqlite3
    result = seed.swdb("build")
    assert result.returncode == 0, result.stderr
    con = sqlite3.connect(f"file:{seed.root / 'build' / 'swdb.sqlite'}?mode=ro", uri=True)
    try:
        return con.execute(query).fetchall()
    finally:
        con.close()


def test_prove_writes_one_not_proven_record_per_listed_failure_class_that_validates_and_builds(seed):
    for value in sorted(FAILURE_CLASSES):
        extra = {"unreplayed_counterexample": UNREPLAYED} if value == "spurious_counterexample" else {}
        seed.prove(seed.script(value, verdict="not_proven", failure_class=value, **extra))
    records = [seed.read(path) for path in seed.proof_files()]
    assert sorted(r["failure_class"] for r in records) == sorted(FAILURE_CLASSES)
    assert {r["verdict"] for r in records} == {"not_proven"}
    result = seed.swdb("validate")
    assert result.returncode == 0, result.stderr
    rows = _build_rows(seed, "SELECT verdict, failure_class FROM swdb_proofs")
    assert sorted(rows) == sorted(("not_proven", value) for value in FAILURE_CLASSES)


def test_a_skip_runs_no_verifier_and_records_its_reason_for_each_skip_reason(seed):
    for reason in sorted(SKIP_REASONS):
        result = seed.prove(seed.script(), "--skip", reason)
        record = result["record"]
        assert record["skip_reason"] == reason
        assert not {"verdict", "failure_class", "counterexample", "evidence"} & set(record)
        assert record["pins"]["method_version"]["id"] == "method.contract-fixture-1"
        assert not (seed.runs / record["id"]).exists()          # no adapter ran, so no adapter log
    assert sorted(seed.read(p)["skip_reason"] for p in seed.proof_files()) == sorted(SKIP_REASONS)
    result = seed.swdb("validate")
    assert result.returncode == 0, result.stderr
    rows = _build_rows(seed, "SELECT verdict, skip_reason, log_path FROM swdb_proofs")
    assert sorted(rows) == sorted((None, reason, None) for reason in SKIP_REASONS)
    assert seed.level()["proven"] is None                       # the level rule ignores a skip


@pytest.mark.parametrize("value", ["cosmic_ray", "timeout"])
def test_validate_rejects_a_skip_reason_that_is_not_a_listed_skip_reason(seed, value):
    path = seed.records / seed.prove(seed.script(), "--skip", "no_minimum_bounds")["path"]
    _rewrite(path, lambda r: r.update(skip_reason=value))
    problems = _problems(seed, path, "skip_reason")
    assert problems and "proof_failure_classes" in problems[0]


def test_a_skip_record_carries_no_verdict(seed):
    path = seed.records / seed.prove(seed.script(), "--skip", "no_contract_proof")["path"]
    _rewrite(path, lambda r: r.update(verdict="proven"))
    problems = _problems(seed, path, "verdict")
    assert problems and "skip" in problems[0]


# --- an unlisted class stops the batch ---------------------------------------------------------

def _batch(seed, middle_class):
    """A three-job batch in one `swdb prove` call: proven, then `middle_class`, then proven."""
    scripts = [seed.script("first"),
               seed.script("middle", verdict="not_proven", failure_class=middle_class),
               seed.script("last")]
    return seed.swdb("prove", "--candidate", seed.candidate, "--function", "DOBFS", "--adapter", "scripted",
                     *[a for script in scripts for a in ("--script", script)],
                     "--runs-dir", seed.runs, "--batch", "batch.t11", "--format", "json")


def test_an_unlisted_failure_class_stops_the_batch(seed):
    result = _batch(seed, "cosmic_ray")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "cosmic_ray" in result.stderr
    runs = sorted(seed.runs.iterdir())
    assert len(runs) == 2                                      # the third job never started
    log = next(p / "adapter.log" for p in runs if "script-middle" in (p / "adapter.log").read_text())
    assert str(log) in result.stderr                           # the adapter's raw output, by path
    records = [seed.read(p) for p in seed.proof_files()]
    assert [(r["verdict"], r["job"]["position"]) for r in records] == [("proven", 1)]   # none for the stopped job


def test_control_the_same_batch_with_a_listed_class_runs_to_the_end(seed):
    import json
    result = _batch(seed, "timeout")
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["batch"] == "batch.t11" and len(out["jobs"]) == 3
    records = sorted((seed.read(p) for p in seed.proof_files()), key=lambda r: r["job"]["position"])
    assert [(r["verdict"], r["job"]["position"], r["job"]["batch"]) for r in records] == [
        ("proven", 1, "batch.t11"), ("not_proven", 2, "batch.t11"), ("proven", 3, "batch.t11")]
    assert seed.swdb("validate").returncode == 0


# --- a counterexample that does not replay (input from ticket 05; class: Yan-Ru 2026-10-14 02:25 ET) ---

def test_a_spurious_counterexample_record_carries_the_counterexample_that_did_not_replay(seed):
    record = seed.prove(seed.script("np", verdict="not_proven", failure_class="spurious_counterexample",
                                    unreplayed_counterexample=UNREPLAYED))["record"]
    assert record["failure_class"] == "spurious_counterexample"
    assert record["unreplayed_counterexample"] == UNREPLAYED and "counterexample" not in record
    assert seed.swdb("validate").returncode == 0


def test_prove_refuses_a_spurious_counterexample_without_the_counterexample_that_did_not_replay(seed):
    result = seed.prove(seed.script("np", verdict="not_proven", failure_class="spurious_counterexample"), ok=False)
    assert result.returncode == 1 and "unreplayed counterexample" in result.stderr
    assert not seed.proof_files()


def test_prove_refuses_an_unreplayed_counterexample_under_any_other_failure_class(seed):
    result = seed.prove(seed.script("np", verdict="not_proven", failure_class="unsupported_construct",
                                    unreplayed_counterexample=UNREPLAYED), ok=False)
    assert result.returncode == 1 and "spurious_counterexample" in result.stderr
    assert not seed.proof_files()


def test_a_refutation_never_carries_an_unreplayed_counterexample(seed):
    from test_proof_records import COUNTEREXAMPLE
    result = seed.prove(seed.script("r", verdict="refuted", counterexample=COUNTEREXAMPLE,
                                    unreplayed_counterexample=UNREPLAYED), ok=False)
    assert result.returncode == 1 and "never a refutation" in result.stderr
    assert not seed.proof_files()


def _rewrite(path, change):
    record = yaml.safe_load(path.read_text())
    change(record)
    path.write_text(yaml.safe_dump(record, sort_keys=False))


def _problems(seed, path, field):
    result = seed.swdb("validate")
    assert result.returncode == 1, result.stdout + result.stderr
    return [line for line in result.stderr.splitlines() if path.name in line and field in line]


@pytest.mark.parametrize("script, change, field, reason", [
    ({"failure_class": "spurious_counterexample", "unreplayed_counterexample": UNREPLAYED},
     lambda r: r.pop("unreplayed_counterexample"), "unreplayed_counterexample", "did not replay"),
    ({"failure_class": "timeout"},
     lambda r: r.update(unreplayed_counterexample=UNREPLAYED), "unreplayed_counterexample", "spurious_counterexample"),
    ({"verdict": "proven", "failure_class": None},
     lambda r: r.update(unreplayed_counterexample=UNREPLAYED), "unreplayed_counterexample", "only a not-proven"),
])
def test_validate_ties_an_unreplayed_counterexample_to_the_spurious_counterexample_class(seed, script, change,
                                                                                         field, reason):
    script = {"verdict": "not_proven", **script}
    if script["failure_class"] is None:
        del script["failure_class"]
    path = seed.records / seed.prove(seed.script("np", **script))["path"]
    _rewrite(path, change)
    problems = _problems(seed, path, field)
    assert problems and reason in problems[0], problems


@pytest.mark.parametrize("value", ["cosmic_ray", "no_contract_proof"])
def test_validate_rejects_a_failure_class_that_is_not_a_listed_failure_class(seed, value):
    path = seed.records / seed.prove(seed.script("np", verdict="not_proven", failure_class="timeout"))["path"]
    _rewrite(path, lambda r: r.update(failure_class=value))
    problems = _problems(seed, path, "failure_class")
    assert problems and "proof_failure_classes" in problems[0]
