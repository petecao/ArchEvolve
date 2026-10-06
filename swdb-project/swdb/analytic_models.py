"""Reusable region-to-seconds mechanism models. Updated: 2026-10-06 ET.

No kernel/target IDs enter these formulas. Parameters are aggregate rates for the
frozen target and thread configuration. A required unknown is never replaced by zero.
"""
import math

CLASSES = ('integer', 'floating_point', 'branch', 'atomic')


def bound(model, seconds, formula, inputs, missing=(), notes=()):
    return {'model': model, 'seconds': seconds, 'basis': 'estimated',
            'state': 'unknown' if seconds is None else 'known', 'formula': formula,
            'inputs': inputs, 'missing': list(missing), 'notes': list(notes)}


def parameter(mechanism, name, unit):
    fact = mechanism['parameters'].get(name)
    if not fact or fact.get('value') is None or fact.get('unit') != unit:
        return None
    value = fact['value']
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0 else None


def compute_throughput(region, mechanism):
    values, missing, components = {}, [], []
    for category in CLASSES:
        count = region['operation_counts'][category]['value']
        name = category + '_ops_per_s'
        rate = parameter(mechanism, name, 'operations/s')
        values[category] = {'operations': count, 'rate': mechanism['parameters'].get(name)}
        if count is None:
            missing.append('operation_counts.' + category)
        elif count == 0:
            components.append(0.0)
        elif rate is None:
            missing.append(name)
        else:
            components.append(count / rate)
    return bound('compute_throughput', None if missing else max(components, default=0.0),
                 'max(operation_count[class] / operations_per_second[class])', values, missing,
                 ['Arithmetic counts include source loop control; address/cast instructions are excluded.'])


def streaming_bandwidth(region, mechanism):
    moved = 0
    missing = []
    access_inputs = []
    for access in region['access_patterns']:
        n = access['bytes_accessed']['value']
        shape = access['address_shape']['value']
        access_inputs.append({'access': access['id'], 'bytes': n, 'address_shape': shape})
        if n is None:
            missing.append(access['id'] + '.bytes_accessed')
        elif n == 0:
            continue
        elif shape != 'stream':
            missing.append(access['id'] + '.streaming_classification')
        else:
            moved += n
    rate = parameter(mechanism, 'bytes_per_s', 'bytes/s')
    if moved and rate is None:
        missing.append('bytes_per_s')
    seconds = None if missing else (moved / rate if moved else 0.0)
    return bound('streaming_bandwidth', seconds, 'sum(streaming useful bytes) / effective_bytes_per_second',
                 {'accesses': access_inputs, 'bytes': moved, 'bytes_per_s': mechanism['parameters'].get('bytes_per_s')}, missing,
                 ['Useful source element bytes; bandwidth must use this same convention, not bus bytes or a theoretical peak.'])


MODELS = {'compute_throughput': compute_throughput, 'streaming_bandwidth': streaming_bandwidth}


def evaluate(region, mechanism):
    implementation = MODELS.get(mechanism['model'])
    if implementation is None:
        return bound(mechanism['model'], None, 'unsupported mechanism model',
                     mechanism['parameters'], ['mechanism_model.' + mechanism['model']])
    return implementation(region, mechanism)
