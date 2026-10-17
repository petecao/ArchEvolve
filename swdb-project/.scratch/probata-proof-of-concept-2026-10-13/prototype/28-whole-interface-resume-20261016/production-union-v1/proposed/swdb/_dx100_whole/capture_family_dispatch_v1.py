"""Closed source family selection; original first-source gates stay unchanged."""
from swdb import dx100_checked_source as source
from swdb._dx100_whole import normalized_capture_ingress_v2 as first
from swdb._dx100_whole import memory_normalized_capture_ingress_v1 as memory
NORMALIZED_KINDS = (first.KIND, memory.KIND)


def complete_capture(policy, reads, project):
    selected = policy.get('capture')
    source.need(type(selected) is dict, 'typed closed source capture required')
    kind = selected.get('kind')
    if kind in (source.CAPTURE_KIND, first.KIND):
        return first.complete_capture(policy, reads, project)
    if kind == memory.KIND:
        source.need(type(policy.get('proof_source')) is dict
            and policy['proof_source'].get('sha256') == memory.SOURCE_SHA,
            'memory capture cannot authorize another source family')
        return memory.complete_capture(policy, reads, project)
    raise ValueError('unprepared or unknown source capture family refused')
