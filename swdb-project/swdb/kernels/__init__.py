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
    native_driver = None      # trusted driver template path
    native_binary = None      # timed binary name inside the build folder
    binary_stem = None        # prefix of diagnostic build artifacts ("bfs")
    driver_call_anchor = None  # driver text that starts the timed call
    source_paths = {}         # application -> translation-unit path
    verifier_symbol = None    # protected kernel verifier in the source
    statement_function = None  # function whose statements are profiled per line

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

    def check_native_trial(self, adjacency, source, observed):
        """Independent result check of one parsed trial output mapping."""
        raise NotImplementedError

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
        if plugin.native_verifier == verifier:
            return plugin
    raise Failure(f"no kernel plug-in owns native verifier {verifier!r}")


def by_native_roi(roi):
    return next((plugin for plugin in _REGISTRY.values() if plugin.native_roi == roi), None)


def native_rois():
    return sorted({plugin.native_roi for plugin in _REGISTRY.values() if plugin.native_roi})


from swdb.kernels import bfs as _bfs  # noqa: E402  (registers the BFS plug-in)

BFS = _bfs.PLUGIN
