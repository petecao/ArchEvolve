"""BC kernel plug-in (gapbs-bc). Created: 2026-10-03 ET (ticket 40).

The native evaluator times one complete ``Brandes`` call for one fixed source
(``tools/bc_native/driver.cc.in``) and checks the returned scores with the
evaluator's reproduction of BCVerifier in ``swdb.bc_native``. Workload
registration refuses BC sources without an outgoing edge (see that module).

Ticket 42 (2026-10-03 ET): the BC instance of candidate certification. The
derived contract ``contract.bc_read_offload`` rewrites the forward pass (PBFS)
with ``library/dx100/bc_read_offload.inc``. A matrix cell passes when the scores the
evaluator-owned driver records pass BCVerifier's criterion (``bc_native.verify_scores``), the
recorded frontier windows have no duplicate and match the oracle's per-depth counts, and an
accelerated chunk ran whenever a frontier reached the threshold (certify 1.3, ticket 70,
2026-10-04 ET: all judged out of process from evaluator records; up to 1.2 from printed lines).
"""

from swdb import artifacts, paths
from swdb.bc_native import verify_scores
from swdb.kernels import KernelPlugin, register


BC_SOURCE = "benchmarks/gapbs/src/bc.cc"
FRONTIER_TEXT = 'std::cout << "Starting PBFS: " << queue.size() << " elements" << std::endl;'
CLAIM = "if(claimed){lqueue.push_back(v);}"
CPU_DEPTH = "const NodeID fresh=__atomic_load_n(&depths[v],__ATOMIC_RELAXED);"
# L4 parts (2026-10-04 ET, final code review of ticket 43): the successor bit, the edge index
# and the path-count source must come from the same chunk position as the claimed vertex.
SUCCESSOR_BIT = "succ.set_bit_atomic(edges[k]);"
CHUNK_PAIR = "const NodeID v=vertices[k],u=frontier[k];"
TOKEN_CONTROLS = {
    # BC-L1: the path-count test uses the DX100 depth hint instead of the CPU depth.
    "stale_depth_hint": (CPU_DEPTH, "const NodeID fresh=claimed?depth:hint;"),
    # L4 successor bit: the CPU no longer records the shortest-path successor edge.
    "dropped_successor_bit": (SUCCESSOR_BIT, "(void)edges[k];"),
    # L4 edge index: the successor bit names the next edge, not the edge that reached v.
    # (Another position of the same chunk is not observable on the control graph, whose
    # accelerated levels claim every edge of a chunk.)
    "shifted_edge_index": (SUCCESSOR_BIT,
                           "succ.set_bit_atomic((edges[k]+1)%g.num_edges_directed());"),
    # L4 path count: the path-count source is another chunk position's frontier vertex.
    "shifted_path_count_source": (CHUNK_PAIR, "const NodeID v=vertices[k],u=frontier[k==0?count-1:k-1];"),
}
# Negative control -> named checks that reject it; an empty set means a semantic
# rejection (BCVerifier FAIL or frontier inequality) with a clean process exit.
CONTROLS = {
    "shared_context": {"thread_ownership_tile", "thread_ownership_register"},
    "skipped_cas_recheck": {"duplicate_frontier"}, "dropped_continuation": set(),
    "chunk_off_by_one": {"tile_truncation"}, "dropped_wait": {"byte_offset_overflow", "read_before_wait"},
    "read_before_wait": {"read_before_wait"}, "index_wrap": {"stream_bounds", "byte_offset_overflow"},
    "forged_frontier": {"duplicate_frontier"},
    **{name: set() for name in TOKEN_CONTROLS},
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


def instrument_source(source, frontier_hook=True):
    """The evaluator's frontier inspection before the protected print (certify 1.3, ticket 70:
    it only records the window; the declaration comes from the forced candidate prelude).

    Ticket 76 (certify 1.4, 2026-10-05 ET): with ``frontier_hook=False`` nothing is inserted into
    the candidate's function; the forced prelude's queue records each window at its slide."""
    from swdb.cli import Failure
    if source.count(FRONTIER_TEXT) != 1:
        raise Failure("BC forward-pass frontier logging statement differs from the protected exact text")
    if source.count("bool BCVerifier(") != 1:
        raise Failure("BC correctness check is missing or ambiguous")
    if frontier_hook:
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
    return harness + source


def frontier_oracle(graph, source):
    """Per-depth counts of the forward pass; refuses a source BCVerifier cannot check."""
    from swdb import sg_graph
    from swdb.certification import graph_oracle
    from swdb.cli import Failure
    counts = graph_oracle(graph, source)
    # Certification graphs are DX100 GAPBS serializations (the scalar-only snapshot's loader).
    if sg_graph.out_degrees({"path": str(graph), "format": sg_graph.application_format("dx100-gapbs")},
                            [source])[source] == 0:
        raise Failure(f"BC certification source {source} has no outgoing edge; BCVerifier would be vacuous")
    return counts


def control(source, name):
    """One negative control of the candidate (ticket 62, 2026-10-04 ET).

    The eight controls shared with BFS act at the library seam
    (``swdb.certification_faults``). BC-L1 has no library seam: it rewrites the CPU's
    depth reread at a token-matched site, insensitive to whitespace and comments.
    """
    from swdb.certification_faults import LIBRARY_FAULTS, library_control, replace_tokens
    from swdb.cli import Failure
    if name in LIBRARY_FAULTS:
        return library_control(source, name)
    if name not in TOKEN_CONTROLS:
        raise Failure("unknown rewrite control")
    before, after = TOKEN_CONTROLS[name]
    return replace_tokens(source, before, after, name)

# --- gem5 side (ticket 44, 2026-10-03 ET) ----------------------------------
# The trusted complete-call gem5 driver mirrors BFS's v2 driver: the evaluator
# preloads the original serialized CSR before the checkpoint, times one Brandes
# call, prints the returned score storage and a fingerprint, then checks the
# exact returned scores after the ROI with the oracle below.

GEM5_CHECKER = "dx100.bc.verifier.v2"
GEM5_ROI = "bc.complete_call.v1"

BC_ORACLE_METHOD = r"""
  // BCVerifier's serial Brandes on the evaluator-owned original CSR, in the
  // source's float types (Count = CountT). Ticket 44, 2026-10-03 ET.
  template <class Count> bool verify_scores(const float *tested, uint64_t count) {
    if (!tested || count != nodes_) return false;
    if (offsets_[source_] == offsets_[source_+1]) return false;  // vacuous source
    std::vector<int32_t> depth(nodes_, -1), order;
    std::vector<Count> paths(nodes_, Count(0));
    order.reserve(nodes_);
    depth[source_] = 0; paths[source_] = Count(1); order.push_back(source_);
    for (uint64_t at = 0; at < order.size(); ++at) {
      const int32_t u = order[at];
      for (uint64_t e = offsets_[u]; e < offsets_[u+1]; ++e) {
        const int32_t v = neighbors_[e];
        if (depth[v] == -1) { depth[v] = depth[u]+1; order.push_back(v); }
        if (depth[v] == depth[u]+1) paths[v] += paths[u];
      }
    }
    int32_t deepest = 0;
    for (uint64_t v = 0; v < nodes_; ++v) deepest = std::max(deepest, depth[v]);
    std::vector<std::vector<int32_t> > levels(deepest+1);
    for (uint64_t v = 0; v < nodes_; ++v) if (depth[v] != -1) levels[depth[v]].push_back(int32_t(v));
    std::vector<float> deltas(nodes_, 0.0f), scores(nodes_, 0.0f);
    for (int32_t level = deepest; level >= 0; --level)
      for (int32_t u : levels[level]) {
        for (uint64_t e = offsets_[u]; e < offsets_[u+1]; ++e) {
          const int32_t v = neighbors_[e];
          if (depth[v] == depth[u]+1) deltas[u] += (paths[u] / paths[v]) * (1 + deltas[v]);
        }
        scores[u] += deltas[u];
      }
    const float biggest = *std::max_element(scores.begin(), scores.end());
    if (!(biggest > 0.0f)) return false;  // vacuous reference
    for (uint64_t v = 0; v < nodes_; ++v) {
      const float reference = scores[v] / biggest;
      if (!std::isfinite(reference)) return false;
      // Stricter than BCVerifier's '>' test: NaN or infinite scores fail.
      if (!(std::fabs(tested[v] - reference) <= std::numeric_limits<float>::epsilon())) return false;
    }
    return true;
  }
"""


def bc_oracle():
    from swdb.dx100_candidate import ORIGINAL_GRAPH_ORACLE
    anchor = "  bool verify(const int32_t *parent, uint64_t count) {"
    if ORIGINAL_GRAPH_ORACLE.count(anchor) != 1:
        raise ValueError("original graph oracle anchor changed")
    return ORIGINAL_GRAPH_ORACLE.replace(anchor, BC_ORACLE_METHOD + anchor, 1)


def gem5_driver(source, model, function, diagnostic=None, *, sg_offset_bytes=8, trusted_graph=True,
                count_type="float"):
    """Trusted complete-call BC evaluator for gem5 (same treatment as BFS's v2 driver)."""
    import json
    from swdb.dx100_candidate import SUPPRESSED
    if type(sg_offset_bytes) is not int or sg_offset_bytes not in {4, 8}:
        raise ValueError('serialized graph offsets must be 4 or 8 bytes')
    if not trusted_graph:
        raise ValueError('BC gem5 evaluation always uses the trusted original-graph oracle')
    if count_type not in {"float", "double"}:
        raise ValueError('count_type must be float or double')
    prefix = "\n".join(f"#define {name}(...) ((void)0)" for name in SUPPRESSED)
    suffix = "\n".join(f"#undef {name}" for name in SUPPRESSED)
    instrumentation = (f"#define SWDB_REGION_COUNT {len(diagnostic['regions'])}\n#include "
        + json.dumps(diagnostic['runtime']['path'])) if diagnostic else ""
    return f'''// Trusted generated evaluator, 2026-10-03 (ticket 44). Complete BC call only.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cerrno>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>
#include <iostream>
#include {json.dumps(str(model / 'include/gem5/m5ops.h'))}
{bc_oracle()}
{instrumentation}
{prefix}
#define main swdb_gem5_original_main
#include {json.dumps(str(source))}
#undef main
{suffix}
int main(int argc, char **argv) {{
  try {{
  swdb_original::Graph oracle(argc, argv, {sg_offset_bytes});
  CLIterApp cli(argc, argv, "SWDB complete-call BC", 1);
  if (!cli.ParseArgs()) return 2;
  Builder builder(cli);
  Graph graph = builder.MakeGraph();
  const int64_t source = cli.start_vertex();
  if (source < 0 || source >= graph.num_nodes()) return 3;
  if (uint64_t(graph.num_nodes()) != oracle.nodes() || source != oracle.source()) return 3;
  const uint64_t original_nodes = oracle.nodes();
  SourcePicker<Graph> picker(graph, static_cast<NodeID>(source));
  m5_checkpoint(0, 0);
  std::cout << "ROI started: 4 configured threads" << std::endl;
  m5_work_begin(0, 0);
  m5_reset_stats(0, 0);
  {'::swdb_profile::start();' if diagnostic else ''}
  auto scores = {function}(graph, picker, 1, cli.logging_en());
  {'::swdb_profile::stop();' if diagnostic else ''}
  m5_dump_stats(0, 0);
  m5_work_end(0, 0);
  std::printf("SWDB_BC_SCORE_STORAGE address=%llx count=%llu element_bytes=4\\n",
      static_cast<unsigned long long>(reinterpret_cast<uintptr_t>(scores.data())),
      static_cast<unsigned long long>(scores.size()));
  std::cout << "ROI End!!!" << std::endl;
  m5_exit(0);
  {'::swdb_profile::write();' if diagnostic else ''}
  // Continuation sees precisely the score object returned by the timed call.
  const float *score_values = scores.data();
  const uint64_t score_count = scores.size();
  bool valid = score_count == original_nodes;
  uint64_t digest = UINT64_C(14695981039346656037);
  for (uint64_t i = 0; i < score_count && i < original_nodes; ++i) {{
    uint32_t bits = 0;
    std::memcpy(&bits, &score_values[i], 4);
    for (unsigned b = 0; b < 4; ++b) {{
      digest ^= (bits >> (8 * b)) & 255u;
      digest *= UINT64_C(1099511628211);
    }}
  }}
  if (valid) valid = oracle.verify_scores<{count_type}>(score_values, score_count);
  std::printf("SWDB_BC_RESULT source=%lld vertices=%lld score_count=%llu score_fnv1a64=%016llx\\n",
      static_cast<long long>(source), static_cast<long long>(original_nodes),
      static_cast<unsigned long long>(score_count), static_cast<unsigned long long>(digest));
  std::printf("Verification: %s\\n", valid ? "PASS" : "FAIL");
  std::fflush(stdout);
  return valid ? 0 : 4;
  }} catch (const std::exception &error) {{
    std::fprintf(stderr, "Trusted BC evaluator: %s\\n", error.what());
    return 5;
  }}
}}
'''


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
    result_noun = "score"

    # gem5 side (ticket 44): BC's v2 completion witness and read-only execution case.
    gem5_roi = GEM5_ROI
    gem5_checkers = frozenset({GEM5_CHECKER})
    gem5_witness_checker = GEM5_CHECKER
    gem5_functions = frozenset({"Brandes"})
    gem5_result_field = "score_results"
    gem5_storage_marker = "SWDB_BC_SCORE_STORAGE"
    protected_verifier_key = "protected_bc_verifier"
    gem5_bounds_check = "trusted driver checks the returned score length before the original-graph oracle"
    gem5_oracle_symbol = "swdb_original::Graph::verify_scores"
    gem5_oracle_bounds_check = ("trusted original-CSR oracle checks exact score length, a non-vacuous source "
                                "and finite scores within float epsilon of serial Brandes")
    # The frozen BFS driver accepts only BFS checkers; BC has its own copy. The
    # kernel-agnostic syscall-trace parser and memory observer are shared.
    gem5_verification_runtime = ("scripts/dx100_bc_verify.py", "scripts/dx100_host_memory.py",
                                 "swdb/dx100_witness.py")
    frontier_text = FRONTIER_TEXT
    frontier_prefix = "Starting PBFS:"
    race_companion = False  # BC's L3 stays assumed; no parent-gather race case

    def gem5_driver(self, source, model, function, diagnostic=None, **options):
        # compile_candidate selects the application's offset width; CountT follows from the
        # same table (`swdb.sg_graph`: 8-byte upstream GAPBS double, 4-byte DX100 GAPBS float).
        from swdb.sg_graph import count_type_for_offset_bytes
        options.setdefault("count_type", count_type_for_offset_bytes(options.get("sg_offset_bytes", 8)))
        return gem5_driver(source, model, function, diagnostic, **options)

    def graph_verification_contract(self, application):
        from swdb.bc_witness import graph_verification_contract
        return graph_verification_contract(application)

    def parse_gem5_result(self, line, number, after_seal):
        from swdb.bc_witness import parse_result
        return parse_result(line, number, after_seal)

    def gem5_result_complete(self, row):
        return row["vertices"] == row["score_count"]

    def gem5_failure_message(self):
        return "BC original-graph oracle printed FAIL, independently of process exit status"

    def validate_completed_witness(self, evaluation, **options):
        from swdb.bc_witness import validate_completed_witness
        return validate_completed_witness(evaluation, **options)

    def validate_record_witness(self, evaluation, store=None):
        from swdb.bc_witness import validate_record_witness
        return validate_record_witness(evaluation, store=store)

    # Candidate certification (ticket 42).
    certification_source = BC_SOURCE
    certification_snapshot = "bc-dx100-scalar-only-20261003-a1.source"
    certification_driver = "dx100/certification/bc_driver.inc"   # ticket 70
    certification_driver_v14 = "dx100/certification/v1_4/bc_driver.inc"   # ticket 76
    certification_driver_v15 = "dx100/certification/v1_5/bc_driver.inc"   # ticket 78
    # Ticket 76: BC claims address PBFS's private depths array, which Brandes does not return.
    certification_claims_address_result = False
    certification_result_kind = "f32"
    certification_controls = CONTROLS
    # On the two-level control graph every accelerated frontier vertex has path count 1, so a
    # wrong path-count source is invisible there; the Kronecker matrix graph has unequal counts.
    certification_control_graphs = {"shifted_path_count_source": "kronecker-16"}
    # L4 names the CAS, successor bit, path count and same-chunk edge index; the contract's
    # control (skipped_cas_recheck) exercises only the CAS. Recorded per clause by certify.
    certification_clause_controls = {"L4": [("dropped_successor_bit", "verifier"),
                                            ("shifted_edge_index", "verifier"),
                                            ("shifted_path_count_source", "verifier")]}

    def certification_rewrite(self, scalar):
        return forward_pass_source(scalar)

    def certification_instrument(self, source, frontier_hook=True):
        return instrument_source(source, frontier_hook=frontier_hook)

    def certification_oracle(self, graph, source):
        return frontier_oracle(graph, source)

    def certification_check_result(self, adjacency, source, values):
        # Ticket 70: BCVerifier's criterion (evaluator reproduction) on the recorded scores.
        return verify_scores(adjacency, source, values, "float")

    def certification_control(self, source, name):
        return control(source, name)

    def native_verifier_sha256(self):
        from swdb import bc_native
        return artifacts.file_hash(bc_native.__file__)

    def check_native_trial(self, adjacency, source, observed, application=None):
        from swdb.sg_graph import application_graph
        count_type = (application_graph(application) or {}).get("bc_count_type")
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
