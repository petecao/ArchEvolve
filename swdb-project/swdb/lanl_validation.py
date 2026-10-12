"""LANL table group: `Validation_definition`, `Validation_results`, and the four tables SWDB has
nothing for yet (`physics_assets`, `kernel_dependencies`, `code_chunks`, `embeddings`)
(LANL-shaped-db ticket 05). Created 2026-10-11 ET. See `swdb/lanl.py` for what a group provides.

Table names keep the slide's capitalization.

- A correctness outcome (a profile's `correctness` part, an evaluation's `correctness.state`)
  counts when what ran is an implementation (a kernel variant) and it names an input record.
  A profile runs its `implementation`. An evaluation runs the candidate its request names; that
  is an implementation only when the candidate is the implementation's unchanged source
  (`artifact_role: source_baseline`). A rewrite candidate's outcome is not its baseline's and
  stays in the `swdb_` tables (review fix, 2026-10-11 ET). The input record is a profile's
  `input`, or the `workload` record an evaluation's `request.workload.id` names
  (`request.workload` when it is a bare ID).
- `Validation_definition`: one row per (kernel, input) pair a counted outcome ran, named
  `<kernel>/<input>`; `input_json` is the input's `generator` or the workload's `definition`.
  No record states an expected output, so `expected_output_json` is NULL.
- `Validation_results`: one row per counted outcome; `passed` is 1, 0, or NULL when correctness
  was not established. No record states an error, so `max_abs_error` is NULL.
- `physics_assets`, `kernel_dependencies`, `code_chunks`, `embeddings`: created with the slide's
  columns so the database has LANL's full shape; nothing fills them. `code_chunks.source_file_id`
  references `source_files`, which ticket 03's group (`ORDER` 30) creates before this one.
"""

import json

ORDER = 50

SCHEMA = """
CREATE TABLE Validation_definition (id INTEGER PRIMARY KEY, kernel_id INTEGER NOT NULL REFERENCES kernels(id),
    name TEXT NOT NULL UNIQUE, input_json TEXT, expected_output_json TEXT);
CREATE TABLE Validation_results (id INTEGER PRIMARY KEY,
    fixture_id INTEGER NOT NULL REFERENCES Validation_definition(id),
    kernel_variant_id INTEGER NOT NULL REFERENCES kernel_variants(id), passed INTEGER, max_abs_error REAL);
CREATE TABLE physics_assets (id INTEGER PRIMARY KEY, kernel_id INTEGER REFERENCES kernels(id), asset_type TEXT,
    name TEXT, format TEXT);
CREATE TABLE kernel_dependencies (id INTEGER PRIMARY KEY, kernel_id INTEGER REFERENCES kernels(id),
    depends_on_kernel_id INTEGER REFERENCES kernels(id), dependency_type TEXT);
CREATE TABLE code_chunks (id INTEGER PRIMARY KEY, source_file_id INTEGER REFERENCES source_files(id),
    line_start INTEGER, line_end INTEGER, content TEXT);
CREATE TABLE embeddings (id INTEGER PRIMARY KEY, code_chunk_id INTEGER REFERENCES code_chunks(id), vector BLOB);
"""

_SEARCH = "the slide gives the search tables only a data type and size, no column names (spec layout rules)"
GUESSED = [
    ("Validation_results", "fixture_id",
     "on the slide, but the slide shows no fixtures table; links to Validation_definition.id (spec layout rules)"),
    ("code_chunks", "id", _SEARCH),
    ("code_chunks", "source_file_id", _SEARCH + "; links to source_files.id"),
    ("code_chunks", "line_start", _SEARCH + "; the slide's size is 'Variable (line_start to line_end)'"),
    ("code_chunks", "line_end", _SEARCH + "; the slide's size is 'Variable (line_start to line_end)'"),
    ("code_chunks", "content", _SEARCH + "; the slide's data type is TEXT"),
    ("embeddings", "id", _SEARCH),
    ("embeddings", "code_chunk_id", _SEARCH + "; links to code_chunks.id"),
    ("embeddings", "vector", _SEARCH + "; the slide's data type is BLOB, 768 dimensions (float32)"),
]


#: Correctness outcome -> `passed`. A profile is written only when its check passed (`complete`)
#: or, with `--allow-unverified`, timed out (not established). An evaluation's `unverified` is
#: not established either. Anything not established is NULL, never 0.
# A timed-out check stays NULL even if its output matched so far: `swdb_profiles.correctness` is
# `not_established` for it, and unknown is not true.
_PROFILE_PASSED = {"complete": 1}
_EVALUATION_PASSED = {"passed": 1, "failed": 0}


def _outcomes(store):
    """Each correctness outcome the records state: (record id, record field, implementation ID,
    input-or-workload record ID, the field naming it, passed)."""
    for record in store.of_kind("profile"):
        parts = record.data.get("parts") or []
        index = next((i for i, part in enumerate(parts) if part.get("part") == "correctness"), None)
        if index is not None:
            yield (record.id, f"parts[{index}].outcome", record.data.get("implementation"), record.data.get("input"),
                   "input", _PROFILE_PASSED.get(parts[index].get("outcome")))
    for record in store.of_kind("evaluation"):
        request = record.data.get("request") or {}
        workload = request.get("workload")
        state = (record.data.get("correctness") or {}).get("state")
        if state is not None:
            named, field = (workload.get("id"), "request.workload.id") if isinstance(workload, dict) \
                else (workload, "request.workload")
            yield (record.id, "correctness.state", _evaluated_implementation(store, record.data, request), named,
                   field, _EVALUATION_PASSED.get(state))


def _evaluated_implementation(store, evaluation, request):
    """The implementation an evaluation ran, or None when it ran something else. An evaluation
    runs the candidate its request names; only a candidate that is the implementation's unchanged
    source (`artifact_role: source_baseline`) is that implementation. A rewrite candidate's
    outcome is not its baseline's, so it stays in the `swdb_` tables."""
    if request.get("candidate") is None:
        return evaluation.get("implementation")
    candidate = store.get(request["candidate"], "candidate") if isinstance(request["candidate"], str) else None
    if candidate is None or candidate.get("artifact_role") != "source_baseline":
        return None
    return candidate.get("implementation")


def _fixture_input(store, input_id):
    """(input JSON, the field it was read from) for an input or workload record; None if it is neither."""
    data = store.get(input_id, "input")
    if data is not None:
        return ("generator", data["generator"]) if data.get("generator") is not None else ("id", None)
    data = store.get(input_id, "workload")
    if data is not None:
        return ("definition", data["definition"]) if data.get("definition") is not None else ("id", None)
    return None


def fill(rows, store):
    fixtures, results = {}, []
    for record_id, field, variant, input_id, input_field, passed in _outcomes(store):
        implementation = store.get(variant, "implementation") if isinstance(variant, str) else None
        stated = _fixture_input(store, input_id) if isinstance(input_id, str) else None
        if implementation is None or stated is None or rows.id_of("kernels", implementation.get("kernel")) is None:
            continue   # the outcome names no kernel variant or no input record: no fixture to link
        name = f"{implementation['kernel']}/{input_id}"
        fixture = fixtures.setdefault(name, {"kernel": implementation["kernel"], "input": input_id, "stated": stated,
                                             "named_by": []})
        fixture["named_by"].append((record_id, input_field))
        results.append((record_id, field, name, variant, passed))

    ids = {}
    for name, fixture in sorted(fixtures.items()):
        input_field, input_value = fixture["stated"]
        ids[name] = rows.add("Validation_definition", {
            "kernel_id": rows.id_of("kernels", fixture["kernel"]), "name": name,
            "input_json": None if input_value is None else json.dumps(input_value, sort_keys=True),
            "expected_output_json": None}, fixture["kernel"], "correctness_check")
        rows.origin("Validation_definition", ids[name], fixture["input"], input_field)
        for record_id, field in fixture["named_by"]:
            rows.origin("Validation_definition", ids[name], record_id, field)

    for record_id, field, name, variant, passed in sorted(results):
        rows.add("Validation_results", {"fixture_id": ids[name],
                                        "kernel_variant_id": rows.id_of("kernel_variants", variant),
                                        "passed": passed, "max_abs_error": None}, record_id, field)
