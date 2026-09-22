"""The repo's own records: what the pilot records must state. Created 2026-09-22."""

import hashlib

from conftest import REPO, read_yaml, run_swdb

RECORDS = REPO / "records"
APP = REPO / "apps" / "gapbs"


def rec(rel):
    return read_yaml(RECORDS / rel)


def source_lines(path, lines):
    first, last = lines
    return "\n".join(path.read_text().splitlines()[first - 1:last])


def test_recorded_code_equals_the_copied_source():
    for rel in ("implementations/gapbs-pr-gs.yaml", "implementations/gapbs-pr-jacobi.yaml", "kernels/gapbs-pr.yaml"):
        data = rec(rel)
        refs = data["code"] if data["kind"] == "implementation" else [data["correctness_check"]["verifier"]["code"]]
        refs += [loop["code"] for loop in data.get("loops", []) if loop.get("code")]
        for code in refs:
            base = APP if code["root"] == "application" else RECORDS
            if code.get("excerpt") is not None:
                assert source_lines(base / code["path"], code["lines"]) == code["excerpt"].rstrip("\n"), (rel, code["lines"])


def test_gapbs_copy_is_upstream_without_local_additions():
    app = rec("applications/gapbs.yaml")
    assert app["source"]["local_path"] == "apps/gapbs"
    assert app["source"]["commit"] in (APP / "PROVENANCE.md").read_text()
    assert not (APP / "src" / "pr_push.cc").exists()
    assert (APP / "LICENSE").is_file()


def test_jacobi_code_file_is_upstream_pr_spmv_unchanged():
    stored = RECORDS / "implementations" / "gapbs-pr-jacobi" / "pr_spmv.cc"
    assert stored.read_bytes() == (APP / "src" / "pr_spmv.cc").read_bytes()
    code = rec("implementations/gapbs-pr-jacobi.yaml")["code"][0]
    assert code["sha256"] == hashlib.sha256(stored.read_bytes()).hexdigest()


def test_baseline_is_gauss_seidel_with_a_loop_carried_dependency():
    kernel = rec("kernels/gapbs-pr.yaml")
    assert kernel["baseline_implementation"] == "gapbs-pr-gs"
    gs = rec("implementations/gapbs-pr-gs.yaml")
    assert gs["function"] == "PageRankPullGS"
    lcd = {p["id"]: p["semantics"]["loop_carried_dependencies"] for p in gs["access_patterns"]}
    assert lcd["gather-contrib"]["value"] is True and lcd["gather-contrib"]["basis"] == "code_reading"
    assert "Gauss-Seidel" in lcd["gather-contrib"]["note"]


def test_jacobi_has_no_loop_carried_dependency():
    jac = rec("implementations/gapbs-pr-jacobi.yaml")
    assert jac["function"] == "PageRankPull" and jac["origin"]["kind"] == "upstream_alternative"
    for p in jac["access_patterns"]:
        fact = p["semantics"]["loop_carried_dependencies"]
        assert fact["value"] is False and fact["basis"] == "code_reading", p["id"]


def test_types_follow_the_source():
    gs = rec("implementations/gapbs-pr-gs.yaml")
    arrays = {s["array"]["name"]: s["array"] for p in gs["access_patterns"] for s in p["steps"]}
    assert arrays["g.in_neighbors_"]["element_bytes"] == 4 and "int32_t" in arrays["g.in_neighbors_"]["element_type"]
    assert arrays["outgoing_contrib"]["element_bytes"] == 4 and "float" in arrays["outgoing_contrib"]["element_type"]
    assert arrays["g.in_index_"]["element_bytes"] == 8   # CSR index arrays hold pointers


def test_pilot_inputs():
    for gen, flag in (("kron", "g"), ("urand", "u")):
        for scale in (16, 22):
            data = rec(f"inputs/{gen}-{flag}{scale}-k16.yaml")
            assert data["generator"]["arguments"] == f"-{flag} {scale} -k 16"
            props = data["properties"]
            assert props["num_nodes"] == {**props["num_nodes"], "value": 2 ** scale, "basis": "code_reading"}
            assert props["requested_degree"]["value"] == 16
            assert props["num_edges_directed"]["basis"] in {"unknown", "measured"}
            assert props["degree_distribution"]["basis"] == "inferred"
            assert props["input_density"]["value"] == "sparse_scattered"


def test_mbit10_machine_record():
    m = rec("machines/mbit10.yaml")
    assert m["cpu"]["model"].startswith("Intel(R) Xeon(R) Gold 6326")
    assert (m["cpu"]["sockets"], m["cpu"]["cores_per_socket"]) == (2, 16)
    l3 = next(c for c in m["caches"] if c["level"] == 3)
    assert l3["size_bytes"] == 24 * 2 ** 20 and l3["shared_by"] == "socket"
    assert m["counters"]["perf_event_paranoid"] == 4
    assert m["counters"]["hardware_counters_available"]["value"] is False
    assert m["capture"]["command"].startswith("ssh mbit10")


def test_repo_records_validate():
    result = run_swdb("validate")
    assert result.returncode == 0, result.stderr
