"""BC kernel plug-in (gapbs-bc). Created: 2026-10-03 ET (ticket 40).

The native evaluator times one complete ``Brandes`` call for one fixed source
(``tools/bc_native/driver.cc.in``) and checks the returned scores with the
evaluator's reproduction of BCVerifier in ``swdb.bc_native``. Workload
registration refuses BC sources without an outgoing edge (see that module).
"""


from swdb import artifacts, paths
from swdb.bc_native import verify_scores
from swdb.kernels import KernelPlugin, register


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
