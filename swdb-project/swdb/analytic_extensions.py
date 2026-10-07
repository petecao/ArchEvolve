"""Optional post-composition evidence hook. Updated: 2026-10-06 ET."""
from importlib import import_module


def finalize_estimate(result, *, store, protocol, characterization, target_description):
    try:
        module = import_module('swdb.cpu_error_band')
    except ModuleNotFoundError as exc:
        if exc.name != 'swdb.cpu_error_band':
            raise
        return result
    return module.finalize_estimate(result, store=store, protocol=protocol,
        characterization=characterization, target_description=target_description)
