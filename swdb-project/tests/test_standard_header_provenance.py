"""Standard-model declaration provenance through prove; created 2026-10-15 ET.

The original TU's include search is authoritative; a clean macro probe or rebuilt
cut cannot certify a candidate-local shadow header. These controls use stand-in WP.
"""
import json

from test_c_lowering import lower
from test_closed_owner_data import SOURCE
from test_closed_owner_members import _record
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp


@needs_wp
def test_a_local_vector_header_with_an_allocation_override_refuses_before_verification(tmp_path):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("data_safe", 7)])
    # The main source, type spellings and genuine libc++ templates are unchanged.
    # The original TU nevertheless sees a replacement new with an observable write.
    (tmp_path / "library" / "proof_units" / "vector").write_text("""#include_next <vector>
#include <cstdlib>
int swdb_header_allocation_calls=0;
void *operator new(std::size_t count) {
  ++swdb_header_allocation_calls;
  return std::malloc(count);
}
""")
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])


@needs_wp
def test_a_transitive_header_new_handler_registration_refuses_before_verification(tmp_path):
    source = SOURCE.replace("#include <cstddef>", '#include <cstddef>\n#include "project_hooks.h"')
    seed = _ownership_seed(tmp_path, source=source, cases=[("data_safe", 7)])
    folder = tmp_path / "library" / "proof_units"
    (folder / "project_hooks.h").write_text('''#include <new>
inline void project_handler() {}
struct project_registration {
  project_registration() { std::set_new_handler(project_handler); }
};
inline project_registration project_registration_instance;
''')
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "scripted.lock")))
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])
    assert "handler registration" in record["settings"]["stdlib_provenance"]["reason"]


def test_an_ordinary_transitive_project_header_keeps_canonical_model_admission(tmp_path):
    source = tmp_path / "unit.cc"
    source.write_text('#include <vector>\n#include "project_support.h"\n'
        'int unit(int n) { std::vector<int> v(n,7); return v.size(); }\n')
    (tmp_path / "project_support.h").write_text(
        "#pragma once\ninline int project_identity(int x) { return x; }\n")
    out = tmp_path / "out"
    lower(source, "unit", out)
    certificate = json.loads((out / "unit.anchors.json").read_text())["stdlib_provenance"]
    assert certificate["verdict"] == "passed"
    assert certificate["parser"]["id"] == "libclang-22.1.8"
    assert any(row["path"].endswith("/project_support.h") for row in certificate["headers"])
