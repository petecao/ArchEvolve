"""BC kernel plug-in (gapbs-bc). Created: 2026-10-03 ET (ticket 40).

The native evaluator times one complete ``Brandes`` call for one fixed source
(``tools/bc_native/driver.cc.in``) and checks the returned scores with the
evaluator's reproduction of BCVerifier in ``swdb.bc_native``. Workload
registration refuses BC sources without an outgoing edge (see that module).

Ticket 42 (2026-10-03 ET): the BC instance of candidate certification. The
derived contract ``contract.bc_read_offload`` rewrites the forward pass (PBFS)
with ``library/dx100/bc_read_offload.inc``. A matrix cell passes when BCVerifier
prints PASS, the forward pass's per-level frontier prints and the evaluator's
trusted queue inspection both equal the oracle's per-depth counts, and an
accelerated chunk ran whenever a frontier reached the threshold.
"""

import re

from swdb import artifacts, paths
from swdb.bc_native import verify_scores
from swdb.kernels import KernelPlugin, register


BC_SOURCE = "benchmarks/gapbs/src/bc.cc"
FRONTIER_TEXT = 'std::cout << "Starting PBFS: " << queue.size() << " elements" << std::endl;'
CLAIM = "if(claimed){lqueue.push_back(v);}"
CPU_DEPTH = "const NodeID fresh=__atomic_load_n(&depths[v],__ATOMIC_RELAXED);"
# Negative control -> named checks that reject it; an empty set means a semantic
# rejection (BCVerifier FAIL or frontier inequality) with a clean process exit.
CONTROLS = {
    "shared_context": {"thread_ownership_tile", "thread_ownership_register"},
    "skipped_cas_recheck": {"duplicate_frontier"}, "dropped_continuation": set(),
    "chunk_off_by_one": {"tile_truncation"}, "dropped_wait": {"byte_offset_overflow", "read_before_wait"},
    "read_before_wait": {"read_before_wait"}, "index_wrap": {"stream_bounds", "byte_offset_overflow"},
    "forged_frontier": {"duplicate_frontier"},
    # BC-L1: the path-count test uses the DX100 depth hint instead of the CPU depth.
    "stale_depth_hint": set(),
}


def forward_pass_source(scalar):
    """The BC forward-pass read offload applied to the scalar-only DX100 bc.cc."""
    from swdb.certification import ROOT
    from swdb.cli import Failure
    start = scalar.index("void PBFS(")
    end = scalar.index("\npvector<ScoreT> Brandes(", start)
    source = scalar[:start] + (ROOT / "library/dx100/bc_read_offload.inc").read_text() + scalar[end:]
    include = "#include <MAA_utility.hpp>"
    if source.count(include) != 1:
        raise Failure("scalar BC includes differ from the pinned source")
    source = source.replace(include, include + '\n#include "swdb_dxc_lowering.hpp"', 1)
    setup = "    alloc_MAA();\n    init_MAA();\n"
    guarded = """    alloc_MAA();
    init_MAA();
    // E3: guards and setup run once per BC call after the existing allocation.
    swdb_dxc::chunks() = 0; swdb_dxc::races() = 0; swdb_dxc::violations() = 0;
    swdb_acceleration_enabled = uint64_t(g.num_nodes()) <= UINT64_C(1073741823) &&
        uint64_t(g.num_edges_directed()) <= UINT64_C(1073741823) && omp_get_max_threads() <= NUM_CORES;
    if (swdb_acceleration_enabled) {
        __dxc_session_begin();
#pragma omp parallel
        { swdb_contexts[omp_get_thread_num()] = __dxc_thread_context(); }
    }
"""
    if source.count(setup) != 1:
        raise Failure("scalar Brandes setup differs from the pinned source")
    source = source.replace(setup, guarded, 1)
    ending = "    return scores;\n}\n"
    if source.count(ending) != 1:
        raise Failure("scalar Brandes return differs from the pinned source")
    return source.replace(ending, "    __dxc_report();\n" + ending, 1)


def instrument_source(source):
    from swdb.certification import TRUSTED_FRONTIER
    from swdb.cli import Failure
    if source.count(FRONTIER_TEXT) != 1:
        raise Failure("BC forward-pass frontier logging statement differs from the protected exact text")
    if source.count("bool BCVerifier(") != 1:
        raise Failure("BC correctness check is missing or ambiguous")
    source = source.replace(FRONTIER_TEXT, "swdb_certification_frontier(queue);\n        " + FRONTIER_TEXT)
    # DX100 bc.cc includes the functional model's MAA.hpp directly (bfs.cc does
    # not); the strict layer's MAA_functional.hpp replaces both, so the private
    # build copy drops that include instead of mixing the two models.
    model = '#include "MAA.hpp"\n'
    if source.count(model) != 1:
        raise Failure("BC functional-model include differs from the pinned source")
    source = source.replace(model, "// MAA.hpp: replaced by the strict functional layer in certification builds\n", 1)
    # The certification build defines FUNC and GEM5 so Brandes registers its memory
    # regions with the strict layer; unlike bfs.cc, DX100 bc.cc includes m5ops only
    # without FUNC, so the evaluator's build copy includes the certification stub.
    harness = "#ifdef GEM5\n#include <gem5/m5ops.h>\n#endif\n"
    return ("#include <set>\n#include <cstdio>\n#include <cstdlib>\n#include <cstdint>\n" + harness
            + TRUSTED_FRONTIER + source)


def frontier_oracle(graph, source):
    """Per-depth counts of the forward pass; refuses a source BCVerifier cannot check."""
    from swdb.bfs_protocol import _sg_out_degrees
    from swdb.certification import graph_oracle
    from swdb.cli import Failure
    counts = graph_oracle(graph, source)
    if _sg_out_degrees({"path": str(graph), "format": "gapbs_sg32le"}, [source])[source] == 0:
        raise Failure(f"BC certification source {source} has no outgoing edge; BCVerifier would be vacuous")
    return counts


def judge(result, counts, *, threshold=64):
    output = result["stdout"]
    if result["timeout"]:
        return False, "timeout"
    if "SWDB_STRICT_ASSERT:" in output + result["stderr"]:
        return False, "strict_layer_assertion"
    if "SWDB_PRESERVATION_FAIL:" in output + result["stderr"]:
        return False, "frontier_size_equality"
    if result["returncode"] != 0:
        return False, "process_failure"
    if not re.search(r"Verification\s*:?\s*PASS", output):
        return False, "verifier"
    observed = [int(n) for n in re.findall(r"Starting PBFS: (\d+) elements", output)]
    trusted = [int(n) for n in re.findall(r"SWDB trusted_frontier=(\d+)", output)]
    if observed != counts or trusted != counts:
        return False, "frontier_size_equality"
    witnesses = re.findall(r"SWDB accelerated_chunks=(\d+)", output)
    if max(counts) >= threshold and (len(witnesses) != 1 or int(witnesses[0]) == 0):
        return False, "execution_witness"
    return True, "all_checks_passed"


def control(source, name):
    """Mutate the actual candidate code; no fabricated runtime results."""
    from swdb.cli import Failure
    mutations = {
        "shared_context": ("dxc_context c=swdb_contexts[omp_get_thread_num()];", "dxc_context c=swdb_contexts[0];"),
        "skipped_cas_recheck": (CLAIM, "if(hint==-1){lqueue.push_back(v);}"),
        "dropped_continuation": ("for(;;){", "for(int swdb_once=0;swdb_once<1;++swdb_once){"),
        "chunk_off_by_one": ("std::min(begin+size_t(SWDB_CHUNK_SIZE),size_t(queue.shared_out_end))",
                             "std::min(begin+size_t(SWDB_CHUNK_SIZE)+1,size_t(queue.shared_out_end))"),
        "dropped_wait": ("__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);", "/* negative control: omitted result waits */"),
        "read_before_wait": ("__dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);",
                             'if(__dxc_tile_pointer<int>(c.tile[5])[0]==int32_t(0xa5a5a5a5)){std::fprintf(stderr,"SWDB_DIFFERENTIAL_MISMATCH:read_before_wait\\n");std::_Exit(87);} __dxc_wait(c.tile[3]);__dxc_wait(c.tile[5]);'),
        "index_wrap": ("__dxc_const_i32(begin,c.reg[0]);", "__dxc_const_i32(INT32_MAX,c.reg[0]);"),
        "forged_frontier": (CLAIM, "if(claimed){lqueue.push_back(v); static std::atomic<bool> swdb_forged(false); "
                                   "if(!swdb_forged.exchange(true))lqueue.push_back(v);}"),
        "stale_depth_hint": (CPU_DEPTH, "const NodeID fresh=claimed?depth:hint;"),
    }
    if name not in mutations:
        raise Failure("unknown rewrite control")
    before, after = mutations[name]
    if source.count(before) != 1:
        raise Failure("candidate source lacks a unique negative-control mutation site: " + name)
    mutated = source.replace(before, after, 1)
    if name == "forged_frontier":
        # Prints the oracle's true counts at every depth despite the double enqueue;
        # only the trusted queue inspection can reject it.
        forged = "static unsigned swdb_forged_level=0; static const unsigned swdb_forged_counts[]={1,4200,17000};\n"
        mutated = forged + mutated.replace('<< queue.size() << " elements"',
                                           '<< swdb_forged_counts[swdb_forged_level++] << " elements"', 1)
    return mutated

class BCPlugin(KernelPlugin):
    kernel = "gapbs-bc"
    name = "BC"
    native_function = "Brandes"
    native_roi = "bc.complete_call.v1"
    native_trial_format = "swdb.bc.native.trial.v1"
    native_verifier = "swdb.bc.brandes_scores.v1"
    native_driver = paths.HOME / "tools" / "bc_native" / "driver.cc.in"
    native_binary = "bc-native"
    binary_stem = "bc"
    driver_call_anchor = "auto scores ="
    source_paths = {"gapbs": "src/bc.cc", "dx100-gapbs": "benchmarks/gapbs/src/bc.cc"}
    verifier_symbol = "BCVerifier"
    statement_function = "PBFS"
    # CountT per application source: float in DX100 bc.cc, double in upstream GAPBS.
    count_types = {"dx100-gapbs": "float", "gapbs": "double"}

    # Candidate certification (ticket 42).
    certification_source = BC_SOURCE
    certification_snapshot = "bc-dx100-scalar-only-20261003-a1.source"
    certification_controls = CONTROLS

    def certification_rewrite(self, scalar):
        return forward_pass_source(scalar)

    def certification_instrument(self, source):
        return instrument_source(source)

    def certification_oracle(self, graph, source):
        return frontier_oracle(graph, source)

    def certification_judge(self, result, counts, *, threshold=64):
        return judge(result, counts, threshold=threshold)

    def certification_control(self, source, name):
        return control(source, name)

    def native_output_limit(self, vertices):
        # Up to 9 significant digits, sign, exponent and separator per score.
        return vertices * 24 + 4096

    def native_verifier_sha256(self):
        from swdb import bc_native
        return artifacts.file_hash(bc_native.__file__)

    def check_native_trial(self, adjacency, source, observed, application=None):
        count_type = self.count_types.get(application)
        if count_type is None:
            return {"passed": False, "reason": f"BC application {application!r} has no known CountT for BCVerifier"}
        return verify_scores(adjacency, source, observed.get("scores"), count_type)

    def check_workload_sources(self, out_degrees):
        # Assumption (ticket 40): BCVerifier is vacuous for a source without an
        # outgoing edge, so registration refuses it, as GAPBS SourcePicker does.
        empty = [source for source, degree in out_degrees.items() if degree == 0]
        if empty:
            return f"BC sources need an outgoing edge (GAPBS SourcePicker rule); refused: {empty}"
        return None


PLUGIN = register(BCPlugin())
