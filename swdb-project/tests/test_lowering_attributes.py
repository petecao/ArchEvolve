"""Declaration attribute admission through swdb lower; created 2026-10-15 ET."""
import pytest

from swdb import c_lowering
from test_c_lowering import lower

pytestmark = pytest.mark.skipif(bool(c_lowering.locate().missing), reason="clang22.1.8 required")


def test_a_local_cleanup_callback_is_refused_instead_of_erased(tmp_path):
    source = tmp_path / "cleanup.cc"
    source.write_text("""int cleanup_count=0;
void release_local(int *value) { cleanup_count += *value; }
int unit(int n) {
  int value __attribute__((cleanup(release_local)))=n;
  return 7;
}
""")
    result = lower(source, "unit", tmp_path / "out", ok=False)
    assert "unsupported construct" in result.stderr
    assert "CleanupAttr" in result.stderr
    assert not (tmp_path / "out" / "unit.c").exists()


@pytest.mark.parametrize("declaration,attribute", [
    ("int unit(int *p __attribute__((noescape))) { return 7; }", "NoEscapeAttr"),
    ("__attribute__((constructor)) void unit() {}", "ConstructorAttr"),
    ("__attribute__((nonnull(1))) int unit(int *p) { return 7; }", "NonNullAttr"),
])
def test_unmodeled_parameter_and_function_attributes_are_refused(tmp_path, declaration, attribute):
    source = tmp_path / "attribute.cc"
    source.write_text(declaration + "\n")
    result = lower(source, "unit", tmp_path / "out", ok=False)
    assert attribute in result.stderr


@pytest.mark.parametrize("declaration", [
    "int unit(int n) { [[maybe_unused]] int ignored; return n; }",
    "int unit([[maybe_unused]] int n) { return n; }",
    "__attribute__((unused)) int unit(int n) { return n; }",
    "[[deprecated]] int unit(int n) { return n; }",
    "[[nodiscard]] int unit(int n) { return n; }",
    "__attribute__((always_inline)) inline int unit(int n) { return n; }",
    "__attribute__((noinline)) int unit(int n) { return n; }",
])
def test_diagnostic_and_inlining_attributes_preserve_ordinary_lowering(tmp_path, declaration):
    source = tmp_path / "benign.cc"
    source.write_text(declaration + "\n")
    lower(source, "unit", tmp_path / "out")
    text = (tmp_path / "out" / "unit.c").read_text()
    assert "return n;" in text
    assert "__attribute__" not in text


def test_an_inherited_function_attribute_is_not_lost_with_the_prototype(tmp_path):
    source = tmp_path / "inherited.cc"
    source.write_text("int unit(int *p) __attribute__((nonnull(1)));\n"
                      "int unit(int *p) { return 7; }\n")
    result = lower(source, "unit", tmp_path / "out", ok=False)
    assert "NonNullAttr" in result.stderr


def test_a_summarized_declaration_keeps_attribute_admission(tmp_path):
    source = tmp_path / "summary.cc"
    source.write_text("int helper(int *p) __attribute__((nonnull(1)));\n"
                      "int unit(int *p) { return helper(p); }\n")
    result = lower(source, "unit", tmp_path / "out", "--summary", "helper=fixture.helper", ok=False)
    assert "NonNullAttr" in result.stderr


def test_an_ordinary_gapbs_helper_retains_its_source_include_closure(tmp_path):
    from conftest import REPO
    source = tmp_path / "gapbs.cc"
    source.write_text('#include <cstdint>\n#include "platform_atomics.h"\nint unit(int n) { return n+1; }\n')
    lower(source, "unit", tmp_path / "out", "--include", REPO / "apps" / "gapbs" / "src")
