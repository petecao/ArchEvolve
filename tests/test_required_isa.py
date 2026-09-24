"""Required ISA: implementations name the intrinsics they call, their build flags must enable
the extensions those need, and `swdb profile` refuses a machine that cannot run them.
Created 2026-09-23."""

import pytest

from test_strategies import edit, passes, rejected

JAC = "implementations/gapbs-pr-jacobi.yaml"


@pytest.fixture
def repo(records):
    return records.copy_repo()


def uses(repo, intrinsics, flags):
    def change(d):
        if intrinsics:
            d["uses_intrinsics"] = intrinsics
        else:
            d.pop("uses_intrinsics", None)
        d["build"]["flags"] = flags
    edit(repo, JAC, change)


def test_existing_implementations_need_no_edit(repo):
    passes(repo.validate())
    assert "uses_intrinsics" not in repo.read(JAC)


def test_uses_intrinsics_must_resolve(repo):
    uses(repo, ["mm512_i32gather_pd"], "-O3 -mavx512f")
    rejected(repo.validate(), "uses_intrinsics[0]", "refers to intrinsic 'mm512_i32gather_pd', which does not exist")


def test_explicit_extension_flag_satisfies_the_required_isa(repo):
    uses(repo, ["mm512_i32gather_ps"], "-std=c++11 -O3 -fopenmp -mavx512f")
    passes(repo.validate())


def test_missing_extension_flag_fails(repo):
    uses(repo, ["mm512_i32gather_ps"], "-std=c++11 -O3 -fopenmp")
    rejected(repo.validate(), JAC, "build.flags", "does not enable avx512f, which mm512_i32gather_ps needs; add -mavx512f")


def test_known_march_value_satisfies_the_required_isa(repo):
    uses(repo, ["mm512_i32gather_ps", "mm_prefetch"], "-O3 -march=icelake-server")
    passes(repo.validate())


def test_known_march_value_without_the_extension_fails(repo):
    uses(repo, ["mm512_i32gather_ps"], "-O3 -march=haswell")
    rejected(repo.validate(), "build.flags", "does not enable avx512f")


def test_unknown_march_value_fails_naming_it(repo):
    uses(repo, ["mm512_i32gather_ps"], "-O3 -march=hal9000")
    rejected(repo.validate(), "build.flags", "unknown -march value 'hal9000'")
    uses(repo, ["mm512_i32gather_ps"], "-O3 -march=native")
    rejected(repo.validate(), "build.flags", "-march=native depends on the build host")


def test_later_flags_win(repo):
    uses(repo, ["mm512_i32gather_ps"], "-O3 -mavx512f -mno-avx512f")
    rejected(repo.validate(), "does not enable avx512f")
    uses(repo, ["mm512_i32gather_ps"], "-O3 -march=icelake-server -march=haswell")
    rejected(repo.validate(), "does not enable avx512f")


@pytest.mark.parametrize("flags", ["-mno-avx512f -march=icelake-server",   # explicit flags beat -march, as in GCC
                                   "-march=icelake-server -mno-sse4",       # a group flag removes what builds on it
                                   "-march=icelake-server -mgeneral-regs-only",
                                   "-m32 -mavx512f -mno-avx2"])
def test_flags_that_disable_the_extension_fail(repo, flags):
    uses(repo, ["mm512_i32gather_ps"], flags)
    rejected(repo.validate(), "does not enable avx512f")


def test_explicit_flag_before_march_still_counts(repo):
    uses(repo, ["mm512_i32gather_ps"], "-mavx512f -march=x86-64")
    passes(repo.validate())


def test_32_bit_build_has_no_sse_baseline(repo):
    uses(repo, ["mm_prefetch"], "-O3 -m32")
    rejected(repo.validate(), "does not enable sse")


def test_sse_is_part_of_the_x86_64_baseline(repo):
    uses(repo, ["mm_prefetch"], "-std=c++11 -O3 -fopenmp")
    passes(repo.validate())


def test_required_isa_is_the_union_of_the_intrinsics(repo):
    uses(repo, ["mm_prefetch", "mm512_i32gather_ps"], "-O3 -msse")
    rejected(repo.validate(), "does not enable avx512f, which mm512_i32gather_ps needs")


# --- swdb profile refuses before the host check and any build ------------------------

@pytest.fixture
def stub(records):
    records.add_stub()
    records.copy_repo("intrinsics")
    impl = records.read("implementations/stub-impl.yaml")
    impl["uses_intrinsics"] = ["mm512_i32gather_ps"]
    impl["build"]["flags"] = "-mavx512f"
    records.write("implementations/stub-impl.yaml", impl)
    machine = records.read("machines/testhost.yaml")
    machine["hostname"] = "some-other-host"     # the host check would fail too; the ISA check comes first
    records.write("machines/testhost.yaml", machine)
    return records


def run_profile(records, tmp_path):
    return records.swdb("profile", "stub-impl", "tiny-sym", "testhost", "--runs-dir", tmp_path / "runs",
                        "--threads", "1", "--trials", "1")


def test_profile_refuses_a_machine_without_the_extension(stub, tmp_path):
    edit(stub, "machines/testhost.yaml",
         lambda d: d["cpu"].update(flags=[f for f in d["cpu"]["flags"] if not f.startswith("avx512")]))
    result = run_profile(stub, tmp_path)
    rejected(result, "machine 'testhost' lacks avx512f, which the implementation needs (build.flags, mm512_i32gather_ps)")
    assert "this host is" not in result.stderr and not (tmp_path / "runs").exists()


def test_profile_refuses_a_machine_that_lists_no_flags(stub, tmp_path):
    def change(d):
        d["schema_version"] = "0.2"
        d["cpu"].pop("flags")
    edit(stub, "machines/testhost.yaml", change)
    result = run_profile(stub, tmp_path)
    rejected(result, "machine 'testhost' lists no CPU flags")
    assert not (tmp_path / "runs").exists()


def test_profile_with_the_extension_reaches_the_host_check(stub, tmp_path):
    rejected(run_profile(stub, tmp_path), "this host is")


def test_profile_refuses_a_march_the_machine_cannot_run_even_without_intrinsics(stub, tmp_path):
    def change(d):
        d.pop("uses_intrinsics")
        d["build"]["flags"] = "-O3 -march=icelake-server"   # the compiler may auto-vectorize with AVX-512
    edit(stub, "implementations/stub-impl.yaml", change)
    edit(stub, "machines/testhost.yaml",
         lambda d: d["cpu"].update(flags=[f for f in d["cpu"]["flags"] if not f.startswith("avx512")]))
    rejected(run_profile(stub, tmp_path), "machine 'testhost' lacks avx512bw, avx512cd, avx512dq, avx512f, avx512vl",
             "(build.flags)")


def test_unknown_march_fails_validation_even_without_intrinsics(repo):
    uses(repo, [], "-O3 -march=hal9000")
    rejected(repo.validate(), "build.flags", "unknown -march value 'hal9000'")


def test_march_native_without_intrinsics_validates(repo):
    uses(repo, [], "-O3 -march=native")
    passes(repo.validate())


def test_a_later_m64_restores_the_baseline(repo):
    uses(repo, ["mm_prefetch"], "-m32 -O3 -m64")
    passes(repo.validate())


def test_profile_refuses_an_unknown_march(stub, tmp_path):
    # validation refuses it first (profile validates the records before anything else)
    edit(stub, "implementations/stub-impl.yaml", lambda d: (d.pop("uses_intrinsics"), d["build"].update(flags="-march=hal9000")))
    result = run_profile(stub, tmp_path)
    rejected(result, "unknown -march value 'hal9000'")
    assert "this host is" not in result.stderr


def test_profile_accepts_march_native_built_on_the_machine(stub, tmp_path):
    def change(d):
        d.pop("uses_intrinsics")
        d["build"]["flags"] = "-O3 -march=native"
    edit(stub, "implementations/stub-impl.yaml", change)
    rejected(run_profile(stub, tmp_path), "this host is")   # past the ISA check, stopped by the host check
