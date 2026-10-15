"""Standard vector models require the actual default allocator; 2026-10-15 ET."""
import json

import pytest

from conftest import run_swdb


SOURCE = """#include <vector>
#include <cstdlib>
int allocation_calls=0;
template<class T> struct allocator {
  using value_type=T;
  allocator()=default;
  template<class U> allocator(const allocator<U>&) {}
  T *allocate(std::size_t n) { ++allocation_calls; return static_cast<T*>(std::malloc(n*sizeof(T))); }
  void deallocate(T *p,std::size_t) { std::free(p); }
};
int unit(int n) { std::vector<int, ALLOCATOR> v((std::size_t)n,7); return v.size(); }
"""


@pytest.mark.parametrize("actual_allocator,accepted", [("allocator<int>", False), ("std::allocator<int>", True)])
def test_vector_model_does_not_resolve_allocators_by_unqualified_name(tmp_path, actual_allocator, accepted):
    source = tmp_path / "unit.cc"
    source.write_text(SOURCE.replace("ALLOCATOR", actual_allocator))
    result = run_swdb("lower", "--source", source, "--function", "unit", "--out", tmp_path / "out", "--format", "json")
    if accepted:
        assert result.returncode == 0, result.stderr + result.stdout
        report = json.loads((tmp_path / "out/unit.anchors.json").read_text())
        assert report["stdlib_provenance"]["verdict"] == "passed"
    else:
        assert result.returncode == 1, result.stderr + result.stdout
        assert "allocator other than std::allocator" in result.stderr
        assert not (tmp_path / "out/unit.c").exists()
