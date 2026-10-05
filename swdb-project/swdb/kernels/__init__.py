"""Kernel plug-ins for the evaluator. Created: 2026-10-03 ET (ticket 38).

The evaluator's kernel-specific parts live behind one plug-in per kernel
record. A plug-in names the kernel's protected entry point, ROI, trusted
drivers, independent result checks (oracles), region-discovery anchors and
gem5 completion and execution-witness rules. Workflow modules select a plug-in
from the kernel record they already resolve (implementation, workload or
protocol), or from a retained checker ID when they revalidate old evidence.

BFS (``gapbs-bfs``) is the first plug-in; its values are exactly the constants
the evaluator used before the seam existed, so BFS records keep their meaning.
"""

from swdb.cli import Failure

_REGISTRY = {}


class KernelPlugin:
    """Base class: every attribute a workflow module may consult.

    Native side (ticket 38): workload/protocol identity, native evaluation,
    the native build adapter, native pairs, region discovery and profiling.
    gem5 side (ticket 39): gem5 build adapter driver and oracle, verifier
    binding, completion witness, accelerator cases and their extractors.
    """

    kernel = None             # kernel record ID
    name = None               # short label used in messages ("BFS")
    # Native evaluation and the native build adapter.
    native_function = None    # protected complete-call entry point
    native_roi = None         # protected ROI identifier
    native_trial_format = None
    native_verifier = None    # evaluator-owned result-check identifier
    native_scalable_verifier = None  # compiled result check of evaluator v2 (ticket 63)
    native_driver = None      # trusted driver template path
    native_binary = None      # timed binary name inside the build folder
    binary_stem = None        # prefix of diagnostic build artifacts ("bfs")
    driver_call_anchor = None  # driver text that starts the timed call
    source_paths = {}         # application -> translation-unit path
    verifier_symbol = None    # protected kernel verifier in the source
    statement_function = None  # function whose statements are profiled per line

    # gem5 side (ticket 39): build adapter driver/oracle, verifier binding,
    # completion witness, accelerator cases and their trace extractors.
    gem5_roi = None               # complete-call ROI of the trusted gem5 driver
    gem5_checkers = frozenset()   # accepted post-ROI checker identities
    gem5_witness_checker = None   # the checker whose runs carry a completion witness
    gem5_functions = frozenset()  # identified entry points the gem5 adapter may select
    gem5_result_field = None      # correctness-check field holding protected result lines
    gem5_storage_marker = None    # stdout marker naming the returned result storage
    protected_verifier_key = None  # context key retaining the protected source verifier
    gem5_bounds_check = None      # how the trusted driver bounds the result before the source verifier
    gem5_oracle_symbol = None     # trusted original-graph oracle symbol in the gem5 driver
    gem5_oracle_bounds_check = None
    # Trusted gem5 verification runtime: (driver, observer, parser) repository paths.
    gem5_verification_runtime = ("scripts/dx100_verify.py", "scripts/dx100_host_memory.py",
                                 "swdb/dx100_witness.py")
    frontier_text = None          # exact per-level frontier print in the rewritten region
    frontier_prefix = None
    race_companion = False        # read-only protocols require the parent-gather race companion (BFS L3)

    def gem5_driver(self, source, model, function, diagnostic=None, **options):
        raise NotImplementedError

    def graph_verification_contract(self, application):
        raise NotImplementedError

    def parse_gem5_result(self, line, number, after_seal):
        """Return the protected result row for one stdout line, or None."""
        return None

    def gem5_result_complete(self, row):
        return False

    def gem5_failure_message(self):
        return f"{self.name} verifier printed FAIL, independently of process exit status"

    def validate_completed_witness(self, evaluation, **options):
        raise NotImplementedError

    def validate_record_witness(self, evaluation, store=None):
        raise NotImplementedError

    def read_only_rule(self, stream, indirect, ranges, alu, stores):
        """Exact instruction-mix rule of the read-only execution case."""
        return False

    read_only_rule_text = None

    def frontier_oracle(self, adjacency, source):
        """Per-depth discovered-vertex counts from the trusted adjacency."""
        from collections import Counter, deque
        depth = [-1] * len(adjacency)
        depth[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v in adjacency[u]:
                if depth[v] == -1:
                    depth[v] = depth[u] + 1
                    queue.append(v)
        counts = Counter(value for value in depth if value >= 0)
        return [counts[level] for level in range(max(counts) + 1)]

    # Candidate certification (ticket 42): the matrix instance and pass rule of a
    # rewrite contract whose correctness check names this kernel.
    certification_source = None    # translation unit a certified candidate rewrites
    certification_snapshot = None  # registered scalar-only snapshot the rewrite starts from
    certification_controls = {}    # negative-control ID -> named checks that reject it
    # Certify 1.3 (ticket 70, 2026-10-04 ET): the evaluator-owned main appended to every build
    # (library-relative path), the kind of vector it records, and the out-of-process result check.
    # 2026-10-05 ET (review fix F10): `certification_drivers` maps each candidate certify version to its
    # driver; the version table (swdb.certification_procedures) reads it. `certification_driver` (1.3)
    # and the `_v14`/`_v15` attributes of the BFS and BC plug-ins are its earlier names.
    certification_drivers = {}
    certification_driver = None
    certification_result_kind = None   # "i32" or "f32"

    def certification_rewrite(self, scalar):
        """The library rewrite of the scalar translation unit (the deliverable patch)."""
        raise NotImplementedError

    def certification_instrument(self, source):
        """Insert the evaluator-owned preservation checks into a private build copy."""
        raise NotImplementedError

    def certification_oracle(self, graph, source):
        """Trusted per-level frontier counts for one serialized graph and source."""
        raise NotImplementedError

    def certification_check_result(self, adjacency, source, values):
        """{passed, reason} of the kernel's recorded result vector (certify 1.3, ticket 70)."""
        raise NotImplementedError

    def certification_control(self, source, name):
        """The candidate source with one named negative-control mutation, or a library fault."""
        raise NotImplementedError

    def control_source(self, sources):
        return sources[0]

    def native_entry_error(self):
        return f"native complete-call adapter supports the identified {self.native_function} entry point only"

    def native_entry_supported(self, implementation, candidate):
        function = self.native_function
        return (implementation.get("kernel") == self.kernel and implementation.get("function") == function
                and candidate["context"].get("function", implementation["function"]) == function)

    def native_output_limit(self, vertices):
        raise NotImplementedError

    def native_verifier_sha256(self):
        raise NotImplementedError

    def check_native_trial(self, adjacency, source, observed, application=None):
        """Independent result check of one parsed trial output mapping."""
        raise NotImplementedError

    def check_workload_sources(self, out_degrees):
        """Refusal reason for registered sources ({source: out-degree}), or None."""
        return None

    def __repr__(self):
        return f"<kernel plug-in {self.kernel}>"


def register(plugin):
    if not isinstance(plugin, KernelPlugin) or not plugin.kernel:
        raise TypeError("kernel plug-ins must name their kernel record")
    if plugin.kernel in _REGISTRY:
        raise ValueError(f"duplicate kernel plug-in {plugin.kernel}")
    _REGISTRY[plugin.kernel] = plugin
    return plugin


def ids():
    return sorted(_REGISTRY)


def plugins():
    return [_REGISTRY[key] for key in ids()]


def get(kernel_id):
    return _REGISTRY.get(kernel_id) if isinstance(kernel_id, str) else None


def require(kernel_id, purpose):
    plugin = get(kernel_id)
    if plugin is None:
        raise Failure(f"{purpose} requires a kernel with an evaluator plug-in ({', '.join(ids())}); "
                      f"{kernel_id!r} has none")
    return plugin


def by_native_verifier(verifier, default="gapbs-bfs"):
    """Select the plug-in that owns a retained native verifier identity.

    Native evaluations written before the seam carry only the BFS verifier, so
    an absent identity selects BFS; an unknown identity is refused.
    """
    if verifier is None:
        return _REGISTRY[default]
    for plugin in _REGISTRY.values():
        if verifier in (plugin.native_verifier, plugin.native_scalable_verifier):
            return plugin
    raise Failure(f"no kernel plug-in owns native verifier {verifier!r}")


def by_native_roi(roi):
    return next((plugin for plugin in _REGISTRY.values() if plugin.native_roi == roi), None)


def by_gem5_checker(checker):
    """The plug-in that owns a post-ROI checker identity, or None."""
    return next((plugin for plugin in _REGISTRY.values() if checker in plugin.gem5_checkers), None)


def by_gem5_roi(roi):
    return next((plugin for plugin in _REGISTRY.values() if plugin.gem5_roi == roi), None)


def gem5_checkers():
    return sorted(checker for plugin in _REGISTRY.values() for checker in plugin.gem5_checkers)


def witness_checkers():
    return {plugin.gem5_witness_checker for plugin in _REGISTRY.values() if plugin.gem5_witness_checker}


def native_rois():
    return sorted({plugin.native_roi for plugin in _REGISTRY.values() if plugin.native_roi})


from swdb.kernels import bfs as _bfs  # noqa: E402  (registers the BFS plug-in)
from swdb.kernels import bc as _bc  # noqa: E402  (registers the BC plug-in, ticket 40)

BFS = _bfs.PLUGIN
BC = _bc.PLUGIN
