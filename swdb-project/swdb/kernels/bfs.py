"""BFS kernel plug-in (gapbs-bfs). Created: 2026-10-03 ET (ticket 38).

Every value here is the constant the evaluator used before the kernel seam, so
existing BFS records, frozen protocols and receipts keep their meaning. The
structural verifier itself stays in ``swdb.bfs_native`` (its file hash is the
retained ``verifier_sha256`` of native BFS evaluations).
"""

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

    def native_output_limit(self, vertices):
        return vertices * 24 + 4096

    def native_verifier_sha256(self):
        from swdb import bfs_native
        return artifacts.file_hash(bfs_native.__file__)

    def check_native_trial(self, adjacency, source, observed):
        from swdb.bfs_native import verify_parents
        return verify_parents(adjacency, source, observed.get("parents"))


PLUGIN = register(BFSPlugin())
