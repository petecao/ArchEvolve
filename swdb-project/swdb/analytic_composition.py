"""Generic resource-domain composition. Updated: 2026-10-06 ET.
Description premises control overlap; no target/kernel identity or schedule inference.
"""
from swdb.analytic_models import bound


def domain(mechanism):
    return mechanism.get('selector',{}).get('domain','host')


def resource_composition(bounds,target):
    active={b['inputs'].get('composition_domain','host') for b in bounds if b['seconds']!=0}
    if len(active)<2:return []
    contract=target.get('composition_contract')
    overlap=(contract or {}).get('resource_domain_overlap')
    maxima={name:None if any(b['seconds'] is None for b in bounds
            if b['inputs'].get('composition_domain','host')==name)
        else max((b['seconds'] for b in bounds if b['inputs'].get('composition_domain','host')==name),default=0.)
        for name in sorted(active)}
    missing=[]
    if overlap not in ('serial','full_overlap'):missing.append('composition_contract.resource_domain_overlap')
    if any(value is None for value in maxima.values()):missing.append('composition.required_resource_unknown')
    seconds=None if missing else sum(maxima.values()) if overlap=='serial' else max(maxima.values())
    return [bound('domain_composition',seconds,
        'sum(domain resource maxima)' if overlap=='serial' else 'max(domain resource maxima)' if overlap=='full_overlap' else 'unknown cross-domain composition',
        {'domain_maxima':maxima,'composition_contract':contract,'composition_domain':'composed'},missing,
        ['Resource maxima compete within a domain; the description explicitly supplies cross-domain overlap.',
         'A declared overlap scenario is an analytic premise, not observed execution scheduling. Required unknowns remain null.'])]
