"""Validation rules for kernels, implementations, inputs, machines, and profiles.
Created 2026-09-22. Each rule has a passing case (the repo's own records, or a legal
variant) and a failing case, run through `swdb validate` as a separate process."""

import copy

import pytest

from conftest import load_fixture


def rejected(result, *fragments):
    assert result.returncode == 1, result.stdout + result.stderr
    for fragment in fragments:
        assert fragment in result.stderr, f"{fragment!r} not in stderr:\n{result.stderr}"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def edit(records, rel, change):
    data = records.read(rel)
    change(data)
    records.write(rel, data)


GS = "implementations/gapbs-pr-gs.yaml"
JAC = "implementations/gapbs-pr-jacobi.yaml"
KERNEL = "kernels/gapbs-pr.yaml"
KRON = "inputs/kron-g16-k16.yaml"


def gather(data):
    return next(p for p in data["access_patterns"] if p["id"] == "gather-contrib")


def test_repo_records_pass(repo):
    result = repo.validate()
    assert result.returncode == 0, result.stderr


# --- references and IDs --------------------------------------------------------------

def test_dangling_reference_fails(repo):
    edit(repo, KERNEL, lambda d: d.update(application="no-such-app"))
    rejected(repo.validate(), KERNEL, "application", "does not exist")


def test_reference_to_wrong_kind_fails(repo):
    edit(repo, GS, lambda d: d.update(kernel="gapbs"))
    rejected(repo.validate(), GS, "kernel", "is a application, not a kernel")


def test_duplicate_id_fails(repo):
    repo.write("inputs/copy.yaml", repo.read(KRON))
    rejected(repo.validate(), "duplicate ID 'kron-g16-k16'")


def test_baseline_must_implement_the_kernel(repo):
    kernel = repo.read(KERNEL)
    kernel["id"] = "gapbs-pr-other"
    repo.write("kernels/other.yaml", kernel)
    rejected(repo.validate(), "kernels/other.yaml", "baseline_implementation", "implements kernel 'gapbs-pr'")


def test_unknown_evidence_ref_fails(repo):
    edit(repo, GS, lambda d: gather(d)["semantics"]["ordering"].update(evidence_refs=["nobody-said-so"]))
    rejected(repo.validate(), "semantics.ordering.evidence_refs[0]", "not a provenance entry")


def test_loop_reference_must_resolve(repo):
    edit(repo, GS, lambda d: gather(d).update(loop="no-such-loop"))
    rejected(repo.validate(), "access_patterns[0].loop", "not a loop")


def test_duplicate_pattern_id_fails(repo):
    edit(repo, GS, lambda d: d["access_patterns"].append(copy.deepcopy(gather(d))))
    rejected(repo.validate(), "duplicate ID 'gather-contrib' in this record")


# --- facts and basis -----------------------------------------------------------------

def test_unknown_basis_with_a_value_fails(repo):
    rel = "inputs/kron-g22-k16.yaml"
    assert repo.read(rel)["properties"]["num_edges_directed"]["basis"] == "unknown"
    edit(repo, rel, lambda d: d["properties"]["num_edges_directed"].update(value=1234))
    rejected(repo.validate(), "properties.num_edges_directed.value", "basis unknown requires value: null")


def test_unknown_basis_with_null_passes(repo):
    edit(repo, KRON, lambda d: d["properties"].update(num_edges_undirected={"value": None, "basis": "unknown"}))
    assert repo.validate().returncode == 0


def test_known_basis_without_value_fails(repo):
    edit(repo, GS, lambda d: gather(d)["semantics"]["loop_carried_dependencies"].update(value=None))
    rejected(repo.validate(), "semantics.loop_carried_dependencies.value", "needs a value")


def test_fact_without_basis_fails(repo):
    edit(repo, GS, lambda d: gather(d)["semantics"]["ordering"].pop("basis"))
    rejected(repo.validate(), "semantics.ordering.basis", "states its basis")


def test_semantic_value_of_wrong_type_fails(repo):
    edit(repo, GS, lambda d: gather(d)["semantics"]["atomic_updates_required"].update(value="maybe"))
    rejected(repo.validate(), "semantics.atomic_updates_required.value")


# --- vocabularies ----------------------------------------------------------------------

@pytest.mark.parametrize("change, where, vocab", [
    (lambda d: gather(d).update(update_kind="scatter"), "update_kind", "update_kinds"),
    (lambda d: gather(d)["steps"][1].update(address_shape="gather"), "steps[1].address_shape", "address_shapes"),
    (lambda d: gather(d)["semantics"]["ordering"].update(basis="guess"), "semantics.ordering.basis", "basis"),
    (lambda d: gather(d)["semantics"]["ordering"].update(value="whenever"), "semantics.ordering.value", "orderings"),
    (lambda d: gather(d)["steps"][0]["array"].update(role="pointer"), "steps[0].array.role", "array_roles"),
    (lambda d: d["loops"][0]["trip_count"].update(scope="per_decade"), "trip_count.scope", "count_scopes"),
])
def test_value_outside_vocabulary_fails(repo, change, where, vocab):
    edit(repo, GS, change)
    rejected(repo.validate(), where, f"not in vocabulary {vocab}")


def test_input_property_name_outside_vocabulary_fails(repo):
    edit(repo, KRON, lambda d: d["properties"].update(vertices={"value": 1, "basis": "code_reading"}))
    rejected(repo.validate(), "not in vocabulary input_properties")


def test_input_property_from_vocabulary_passes(repo):
    edit(repo, KRON, lambda d: d["properties"].update(weighted={"value": False, "basis": "code_reading"}))
    assert repo.validate().returncode == 0


# --- counts ----------------------------------------------------------------------------

def test_count_without_scope_fails(repo):
    edit(repo, GS, lambda d: d["loops"][2]["trip_count"].pop("scope"))
    rejected(repo.validate(), "loops[2].trip_count.scope", "every count needs a scope")


def test_count_with_known_basis_needs_value_or_formula(repo):
    edit(repo, GS, lambda d: d["loops"][2]["trip_count"].update(formula=None, value=None))
    rejected(repo.validate(), "loops[2].trip_count", "needs a value or a formula")


def test_count_with_value_passes(repo):
    edit(repo, GS, lambda d: d["loops"][2]["trip_count"].update(formula=None, value=65536))
    assert repo.validate().returncode == 0


# --- steps and chains ------------------------------------------------------------------

def test_stream_needs_stride(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][0].pop("stride"))
    rejected(repo.validate(), "steps[0].stride", "a stream step needs a stride")


def test_stream_with_stride_zero_passes(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][0].update(stride=0))
    assert repo.validate().returncode == 0


def test_stream_with_index_transform_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][0].update(index_transform="identity"))
    rejected(repo.validate(), "steps[0]", "index_transform belongs only to single_valued_indirect")


def test_single_valued_indirect_needs_index_transform(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2].pop("index_transform"))
    rejected(repo.validate(), "steps[2].index_transform", "needs an index_transform")


def test_single_valued_indirect_with_stride_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2].update(stride=1))
    rejected(repo.validate(), "steps[2]", "stride belongs only to stream steps")


def test_ranged_indirect_with_stride_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][1].update(stride=1))
    rejected(repo.validate(), "steps[1]", "take neither stride nor index_transform")


def test_chain_cannot_start_indirect(repo):
    edit(repo, GS, lambda d: gather(d).update(steps=gather(d)["steps"][1:]))
    rejected(repo.validate(), "steps[0].address_shape", "cannot start with ranged_indirect")


def test_chain_must_end_at_its_target(repo):
    edit(repo, GS, lambda d: gather(d).update(steps=gather(d)["steps"][:2]))
    rejected(repo.validate(), "steps[1].array.role", "the last step of a chain is its target")


def test_ranged_step_must_follow_offsets(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][0]["array"].update(role="index"))
    rejected(repo.validate(), "steps[1].address_shape", "follows a step whose array role is offsets")


# --- formulas ----------------------------------------------------------------------------

def test_formula_symbol_outside_vocabulary_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2]["array"].update(element_count="num_vertices"))
    rejected(repo.validate(), "steps[2].array.element_count", "symbol 'num_vertices' is not in vocabulary input_properties")


def test_malformed_formula_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2]["array"].update(element_count="num_nodes +"))
    rejected(repo.validate(), "steps[2].array.element_count", "not valid")


def test_formula_with_function_call_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2]["array"].update(element_count="max(num_nodes, 1)"))
    rejected(repo.validate(), "steps[2].array.element_count", "only + - * //")


def every_step_of(data, name):
    return [s for p in data["access_patterns"] for s in p["steps"] if s["array"]["name"] == name]


def test_formula_arithmetic_passes(repo):
    edit(repo, GS, lambda d: [s["array"].update(element_count="2 * num_nodes // 2")
                              for s in every_step_of(d, "outgoing_contrib")])
    assert repo.validate().returncode == 0


def test_unknown_element_count_passes(repo):
    # a size that depends on the data at run time is null, never a guessed formula
    edit(repo, GS, lambda d: [s["array"].update(element_count=None) for s in every_step_of(d, "outgoing_contrib")])
    assert repo.validate().returncode == 0


def test_one_array_with_two_sizes_fails(repo):
    edit(repo, GS, lambda d: gather(d)["steps"][2]["array"].update(element_count="num_nodes + 1"))
    rejected(repo.validate(), "array 'outgoing_contrib' differs from", "in element_count")


def test_one_array_in_two_roles_passes(repo):
    # the same array may be an index in one step and the target in another (comp[comp[n]])
    edit(repo, GS, lambda d: d["access_patterns"].append({
        **gather(d), "id": "contrib-twice",
        "steps": [gather(d)["steps"][0], gather(d)["steps"][1],
                  {**gather(d)["steps"][2], "array": {**gather(d)["steps"][2]["array"], "role": "index"}},
                  {"array": gather(d)["steps"][2]["array"], "address_shape": "pointer_chase"}]}))
    assert repo.validate().returncode == 0


# --- code excerpts ---------------------------------------------------------------------

def test_excerpt_that_differs_from_the_source_fails(repo):
    edit(repo, GS, lambda d: d["code"][0].update(excerpt=d["code"][0]["excerpt"].replace("kDamp", "0.85f")))
    rejected(repo.validate(), "code[0].excerpt", "differs from 'src/pr.cc' lines 34-61")


def test_excerpt_with_shifted_lines_fails(repo):
    edit(repo, GS, lambda d: d["code"][0].update(lines=[35, 62]))
    rejected(repo.validate(), "code[0].excerpt", "differs")


def test_lines_outside_the_file_fail(repo):
    edit(repo, GS, lambda d: d["code"][0].update(lines=[100, 900]))
    rejected(repo.validate(), "code[0].lines", "outside")


def test_missing_code_file_fails(repo):
    edit(repo, GS, lambda d: d["code"][0].update(path="src/pr_push.cc"))
    rejected(repo.validate(), "code[0].path", "does not exist")


def test_changed_record_code_file_fails_its_sha256(repo):
    path = repo.path / "implementations" / "gapbs-pr-jacobi" / "pr_spmv.cc"
    path.write_text(path.read_text() + "\n// edited\n")
    rejected(repo.validate(), "code[0].sha256", "does not match")


# --- inputs ---------------------------------------------------------------------------

def test_input_with_generator_and_file_fails(repo):
    edit(repo, KRON, lambda d: d.update(file={"path": "x.el", "format": "gapbs_el", "sha256": "0" * 64}))
    rejected(repo.validate(), KRON, "never both")


def test_input_with_neither_generator_nor_file_fails(repo):
    edit(repo, KRON, lambda d: d.pop("generator"))
    rejected(repo.validate(), KRON, "needs a generator or a file")


def test_file_input_passes(repo):
    data = repo.read(KRON)
    data.pop("generator")
    data["id"] = "from-file"
    data["file"] = {"path": "graphs/x.el", "format": "gapbs_el", "sha256": "a" * 64}
    repo.write("inputs/from-file.yaml", data)
    assert repo.validate().returncode == 0


# --- profiles --------------------------------------------------------------------------

@pytest.fixture
def with_profile(records):
    records.add_stub()
    records.write("profiles/p.yaml", load_fixture("profile/minimal-profile.yaml"))
    return records


def test_minimal_profile_passes(with_profile):
    result = with_profile.validate()
    assert result.returncode == 0, result.stderr


def test_metric_without_unit_fails(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["metrics"][0].pop("unit"))
    rejected(with_profile.validate(), "metrics[0].unit", "every metric needs a unit")


def test_metric_with_the_wrong_unit_fails(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["metrics"][0].update(unit="ms"))
    rejected(with_profile.validate(), "metrics[0].unit", "measured in 's', not 'ms'")


def test_metric_name_outside_vocabulary_fails(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["metrics"][0].update(name="llc_misses"))
    rejected(with_profile.validate(), "metrics[0].name", "not in vocabulary metrics")


def test_measured_bottleneck_without_counters_fails(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["bottleneck"].update(basis="measured"))
    rejected(with_profile.validate(), "bottleneck.basis", "can only be inferred")


def test_measured_bottleneck_with_counters_passes(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["bottleneck"].update(basis="measured"))
    edit(with_profile, "machines/testhost.yaml",
         lambda d: d["counters"]["hardware_counters_available"].update(value=True))
    assert with_profile.validate().returncode == 0


def test_profile_input_must_define_the_formula_symbols(with_profile):
    edit(with_profile, "inputs/tiny-sym.yaml", lambda d: d["properties"].pop("num_edges_directed"))
    rejected(with_profile.validate(), "profiles/p.yaml", "does not define 'num_edges_directed'")


def test_unscoped_profile_count_fails(with_profile):
    edit(with_profile, "profiles/p.yaml", lambda d: d["counts"]["iterations"].pop("scope"))
    rejected(with_profile.validate(), "counts.iterations.scope", "every count needs a scope")


# --- regular expressions ----------------------------------------------------------------

def test_sweep_count_regex_with_one_group_passes(repo):
    edit(repo, GS, lambda d: d["run"].update(sweep_count_regex=r"took (\d+) iterations"))
    assert repo.validate().returncode == 0


def test_sweep_count_regex_without_a_group_fails(repo):
    edit(repo, GS, lambda d: d["run"].update(sweep_count_regex=r"took \d+ iterations"))
    rejected(repo.validate(), "run.sweep_count_regex", "exactly 1 capture group")


def test_invalid_pass_regex_fails(repo):
    edit(repo, KERNEL, lambda d: d["correctness_check"].update(pass_regex="Verification:\\s+(PASS"))
    rejected(repo.validate(), "correctness_check.pass_regex", "not a valid regular expression")
