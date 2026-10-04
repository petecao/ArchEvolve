"""BFS kernel plug-in (gapbs-bfs). Created: 2026-10-03 ET (ticket 38).

Every value here is the constant the evaluator used before the kernel seam, so
existing BFS records, frozen protocols and receipts keep their meaning. The
structural verifier itself stays in ``swdb.bfs_native`` (its file hash is the
retained ``verifier_sha256`` of native BFS evaluations).
"""

import re

from swdb import artifacts, paths
from swdb.kernels import KernelPlugin, register


class BFSPlugin(KernelPlugin):
    kernel = "gapbs-bfs"
    name = "BFS"
    native_function = "DOBFS"
    native_roi = "bfs.complete_call.v1"
    native_trial_format = "swdb.bfs.native.trial.v1"
    native_verifier = "swdb.bfs.structural.v1"
    native_driver = paths.HOME / "tools" / "bfs_native" / "driver.cc.in"
    native_binary = "bfs-native"
    binary_stem = "bfs"
    driver_call_anchor = "auto parent ="
    source_paths = {"gapbs": "src/bfs.cc", "dx100-gapbs": "benchmarks/gapbs/src/bfs.cc"}
    verifier_symbol = "BFSVerifier"
    statement_function = "TDStep"

    # gem5 side (ticket 39): the values the gem5 adapters used before the seam.
    gem5_roi = "bfs.complete_call.v1"
    gem5_checkers = frozenset({"dx100.bfs.verifier.v1", "dx100.bfs.verifier.v2"})
    gem5_witness_checker = "dx100.bfs.verifier.v2"
    gem5_functions = frozenset({"DOBFS", "DOBFSMAA"})
    gem5_result_field = "parent_results"
    gem5_storage_marker = "SWDB_BFS_PARENT_STORAGE"
    protected_verifier_key = "protected_bfs_verifier"
    gem5_bounds_check = "trusted driver validates parent length and values before BFSVerifier"
    gem5_oracle_symbol = "swdb_original::Graph::verify"
    gem5_oracle_bounds_check = ("trusted original-CSR oracle checks exact parent length and range "
                                "before traversal validation")
    frontier_text = 'std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;'
    frontier_prefix = "Starting TDStep:"
    read_only_rule_text = "S>=1,I>=1,R>=1,A=0,indirect_stores=0,I=3*R-S"
    race_companion = True  # ticket 44: the L3 parent-gather race companion is BFS-specific

    def gem5_driver(self, source, model, function, diagnostic=None, **options):
        from swdb.dx100_candidate import driver
        return driver(source, model, function, diagnostic, **options)

    def graph_verification_contract(self, application):
        from swdb.dx100_witness import graph_verification_contract
        return graph_verification_contract(application)

    def parse_gem5_result(self, line, number, after_seal):
        found = re.fullmatch(r"SWDB_BFS_RESULT source=(\d+) vertices=(\d+) parent_count=(\d+) parent_fnv1a64=([a-f0-9]{16})\s*", line)
        if not found:
            return None
        return {"source": int(found[1]), "vertices": int(found[2]), "parent_count": int(found[3]),
                "parent_fnv1a64": found[4], "line": number, "after_seal": after_seal,
                "fingerprint_kind": "noncryptographic FNV-1a over little-endian signed32 parent values"}

    def gem5_result_complete(self, row):
        return row["vertices"] == row["parent_count"]

    def gem5_failure_message(self):
        return "BFS structural verifier printed FAIL, independently of process exit status"

    def validate_completed_witness(self, evaluation, **options):
        from swdb.dx100_witness import validate_completed_witness
        return validate_completed_witness(evaluation, **options)

    def validate_record_witness(self, evaluation, store=None):
        from swdb.dx100_witness import validate_record_witness
        return validate_record_witness(evaluation, store=store)

    def read_only_rule(self, stream, indirect, ranges, alu, stores):
        # Peter section 5 order: per chunk one stream load, two row-bound gathers
        # and a final empty range loop; per non-empty range tile three gathers.
        return (stream >= 1 and indirect >= 1 and ranges >= 1 and alu == stores == 0
                and indirect == 3 * ranges - stream)

    # Candidate certification (ticket 42): the exact BFS functions used before.
    certification_source = "benchmarks/gapbs/src/bfs.cc"
    certification_snapshot = "bfs-dx100-scalar-only-20260929-a1.source"

    @property
    def certification_controls(self):
        from swdb.certification import _CONTROL_EXPECTED
        return _CONTROL_EXPECTED

    def certification_rewrite(self, scalar):
        from swdb.certification import peter_source
        return peter_source(scalar)

    def certification_instrument(self, source):
        from swdb.certification import instrument_source
        return instrument_source(source)

    def certification_oracle(self, graph, source):
        from swdb.certification import graph_oracle
        return graph_oracle(graph, source)

    def certification_judge(self, result, counts, *, threshold=64):
        from swdb.certification import judge_bfs
        return judge_bfs(result, counts, threshold=threshold)

    def certification_control(self, source, name):
        from swdb.certification import _rewrite_control
        return _rewrite_control(source, name)

    def native_output_limit(self, vertices):
        return vertices * 24 + 4096

    def native_verifier_sha256(self):
        from swdb import bfs_native
        return artifacts.file_hash(bfs_native.__file__)

    def check_native_trial(self, adjacency, source, observed, application=None):
        from swdb.bfs_native import verify_parents
        return verify_parents(adjacency, source, observed.get("parents"))


PLUGIN = register(BFSPlugin())
