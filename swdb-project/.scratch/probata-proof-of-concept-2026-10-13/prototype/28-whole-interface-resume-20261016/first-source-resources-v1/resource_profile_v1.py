"""2026-10-16 ET. Fixed first-source model resource selection, not a theorem.

The bounded assembly explicitly owns a 1024-node model. Every backend capacity,
evaluation-step and unwinding assertion remains. Unknown sources/components or
loop owners refuse; this module does not change any backend default or premise.
"""
import json
import re

SOURCE_SHA = '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'
FUNCTION = 'whole_interface_source_fixture'
NODE_CAPACITY = 1024
DEFAULT_HELPER_UNWIND = 513
EVALUATION_HELPER_UNWIND = 20 * NODE_CAPACITY + 1
COMPONENTS = {'whole_value_backend_v1.h': 'c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f', 'whole_adapters.h': 'e8efe60182d7fbd0d7c9f54c8fc6f70c235a91bd613cabd3be6ac893105c4a1a', 'whole_value_builders_v1.h': '88f6bd0d310e8a2a6ad522ae15fec32b9f32b4ed6d792a314e8a365e0118824e', 'whole_closed_routes_v1.h': '0168b2f78e0d5a6a6d42c8955ba45304533b8a0c63b92bebcabd50fd730969c7'}
ACCOUNTING = (('four_stream_loads', 4, 58), ('stream_store', 1, 56),
    ('scalar_vector_reduce', 1, 88), ('five_indirect_calls', 5, 36),
    ('range', 1, 208), ('source_scalar_CPU_observations', 1, 64))


class Refused(ValueError): pass


def need(value, message):
    if not value: raise Refused(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def select(source_sha256, function, components):
    need(source_sha256 == SOURCE_SHA and function == FUNCTION, 'exact first-source resource profile required')
    need(type(components) is dict and components == COMPONENTS, 'exact reviewed backend identities required')
    budget = sum(count * nodes for _name, count, nodes in ACCOUNTING)
    need(budget == 828 and budget < NODE_CAPACITY, 'fixed structural node budget differs')
    return {'schema': 'dx100-first-source-resource-profile-1', 'source_sha256': SOURCE_SHA, 'function': FUNCTION,
        'backend_components': dict(COMPONENTS), 'DXM_NODES': NODE_CAPACITY, 'backend_default_DXM_NODES': 128,
        'structural_node_accounting': [{'category': name, 'count': count, 'nodes_per': nodes}
                                      for name, count, nodes in ACCOUNTING],
        'structural_node_budget': budget, 'default_helper_unwind': DEFAULT_HELPER_UNWIND,
        'helper_owner_unwind': {'dxm_cover': EVALUATION_HELPER_UNWIND},
        'capacity_evaluation_and_unwinding_assertions_retained': True,
        'boundary': 'source-bound resource preflight only; actual capacity checks and scientific result remain mandatory'}


def checked(profile):
    expected = select(SOURCE_SHA, FUNCTION, dict(COMPONENTS))
    need(type(profile) is dict and canonical(profile) == canonical(expected), 'exact immutable resource selection required')
    return expected


def prefix(profile):
    checked(profile)
    return ('/* Exact first-source resource profile; all capacity checks retained. */\n'
        '#ifdef DXM_NODES\n#error first_source_profile_must_own_DXM_NODES\n#endif\n'
        '#define DXM_NODES 1024\n')


def helper_loop_bounds(profile, actual_loop_ids, helper_functions):
    """Apply bounds to retained actual opaque selectors; never invent a selector."""
    checked(profile)
    need(type(actual_loop_ids) is list and all(type(loop) is str for loop in actual_loop_ids)
         and len(actual_loop_ids) == len(set(actual_loop_ids))
         and type(helper_functions) in (tuple, list) and all(type(name) is str for name in helper_functions)
         and 'dxm_cover' in helper_functions, 'complete helper/actual-loop selector domain required')
    bounds = []
    for loop in actual_loop_ids:
        need(type(loop) is str and re.fullmatch(r'\S+\.\d+', loop) is not None
             and loop.rsplit('.', 1)[0] in helper_functions, 'actual helper loop owner required')
        owner = loop.rsplit('.', 1)[0]
        bounds.append({'loop': loop, 'owner': owner, 'unwind': EVALUATION_HELPER_UNWIND if owner == 'dxm_cover' else DEFAULT_HELPER_UNWIND})
    return bounds
