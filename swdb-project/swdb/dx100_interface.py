"""2026-10-15 ET. Complete declarations of the immutable DX100 MMIO headers.

This inventory describes source declarations, independently of kernel call uses.
It does not certify a typed implementation or a call's ACSL contract.
"""
import re

from swdb import artifacts

COMMIT = 'e4fc4afdf894f295442cef3604667a469fab8e62'
HEADERS = {
    'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174',
}
_DEFINITION = re.compile(
    r'(?m)^[ \t]*(?P<declaration>(?:(?:inline|volatile)\s+)*[A-Za-z_]\w*(?:::\w+)*'
    r'(?:\s+|[ \t]*[*&][ \t]*)(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\))\s*\{')
_COMMENT_OR_STRING = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)


def contract_rows(row):
    """Concrete contracts of a family; no generic fallback for typed instances."""
    if 'instances' in row:
        return row['instances']
    return row.get('overloads') or [row]


def check_instances(data, error):
    """Reject absent contracts, ambiguous selectors and duplicate concrete ABIs.

    Template arguments are canonical source types, not device datatype codes.
    Source binding separately checks the actual instantiation and C signature.
    """
    valid, symbols = True, set()
    for i, row in enumerate(data.get('calls') or []):
        if not isinstance(row, dict) or 'instances' not in row:
            continue
        where = f'calls[{i}].instances'

        def refuse(reason):
            nonlocal valid
            valid = False
            error(where, reason)

        instances = row['instances']
        if not isinstance(instances, list) or not instances:
            refuse('instances must be a nonempty list')
            continue
        if 'overloads' in row:
            refuse('instances and overloads cannot both select the call contracts')
        selectors = set()
        for instance in instances:
            if not isinstance(instance, dict):
                refuse('instance needs its own C prototype and contract')
                continue
            if set(instance) - {'arguments', 'arity', 'prototype', 'contract', 'declaration'}:
                refuse('unknown template instance fields')
            arguments, arity = instance.get('arguments'), instance.get('arity')
            if not isinstance(arguments, list) or not arguments or any(
                    not isinstance(a, str) or not a.strip() for a in arguments):
                refuse('instance arguments must be a nonempty list of canonical type strings')
            elif type(arity) is not int or arity < 0:
                refuse('instance arity must be a nonnegative integer')
            else:
                selector = (tuple(' '.join(a.split()) for a in arguments), arity)
                if selector in selectors:
                    refuse('duplicate template arguments and arity')
                selectors.add(selector)
            prototype, contract = instance.get('prototype'), instance.get('contract')
            match = re.fullmatch(r'.*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)', prototype or '') \
                if isinstance(prototype, str) else None
            if not match or not isinstance(contract, str) or not contract.strip():
                refuse('instance needs its own C prototype and contract')
            elif match[1] in symbols:
                refuse('instance C symbols must be distinct')
            else:
                symbols.add(match[1])
    return valid


def declarations(text, header):
    """Global definitions in the two pinned headers; no closed API-name regex.

    Strings/comments are masked without moving source positions. Body definitions
    are excluded by brace depth. The accepted input bytes are checked separately;
    this is not a parser for arbitrary C++ or its conditional preprocessing.
    """
    clean = _COMMENT_OR_STRING.sub(lambda m: re.sub(r'[^\n]', ' ', m.group()), text)
    depths, depth = [], 0
    for char in clean:
        depths.append(depth)
        depth += (char == '{') - (char == '}')
    if depth:
        raise ValueError('unbalanced pinned interface header')
    return [{'file': header, 'line': text.count('\n', 0, m.start('declaration')) + 1,
             'name': m['name'], 'declaration': ' '.join(m['declaration'].split())}
            for m in _DEFINITION.finditer(clean) if depths[m.start()] == 0]


def check(library, data, error):
    """Validate an explicitly complete declaration inventory and its call rows."""
    manifest = data.get('declaration_inventory')
    if manifest is None:
        return                         # retained 0.1 use inventory stays unchanged
    try:
        if data['hardware_interface']['gem5_commit'] != COMMIT:
            raise ValueError('complete DX100 declaration inventory requires the pinned e4fc4af interface')
        sources = manifest['sources']
        if len(sources) != 2:
            raise ValueError('complete interface declaration inventory requires both pinned headers')
        actual, seen = [], set()
        for pin in sources:
            library._pin(pin)
            path = library.resolve(pin)
            if path.name in seen or path.name not in HEADERS or artifacts.file_hash(path) != HEADERS[path.name]:
                raise ValueError('interface declaration source differs from the immutable upstream header')
            seen.add(path.name)
            actual.extend(declarations(path.read_text(), path.name))
        if sorted(actual, key=lambda r: (r['file'], r['line'])) != sorted(
                manifest['declarations'], key=lambda r: (r['file'], r['line'])):
            raise ValueError('interface declaration inventory differs from the complete pinned header declarations')
        names = {r['name'] for r in actual}
        covered = {r['call'] for r in data.get('calls', [])}
        for name in sorted(names - covered):
            error('calls', f'interface declaration {name} has no call contract')
        for name in sorted(covered - names):
            error('calls', f'call {name} has no interface declaration; ghost queries belong in queries')
        for row in data.get('calls', []):
            signatures = [d['declaration'] for d in actual if d['name'] == row['call']]
            if 'instances' in row:
                instances = row['instances']
                if isinstance(instances, list) and all(isinstance(v, dict) for v in instances):
                    declared = {v.get('declaration') for v in instances}
                    if (len(signatures) > 1 and declared != set(signatures)) or \
                            any(d is not None and d not in signatures for d in declared):
                        error('calls', f'interface declaration {row["call"]} instances must cover its exact declarations')
                continue
            if len(signatures) < 2:
                continue
            overloads = row.get('overloads')
            if not isinstance(overloads, list) or len(overloads) != len(signatures) or \
                    sorted(o.get('declaration', '') for o in overloads) != sorted(signatures):
                error('calls', f'interface declaration {row["call"]} needs a distinct contract for every overload')
                continue
            symbols = []
            for overload in overloads:
                prototype = overload.get('prototype')
                match = re.fullmatch(r'.*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)', prototype or '')
                if not match or not isinstance(overload.get('contract'), str) or not overload['contract'].strip():
                    error('calls', f'interface declaration {row["call"]} overload needs its own C prototype and contract')
                elif match[1] in symbols:
                    error('calls', f'interface declaration {row["call"]} overload C symbols must be distinct')
                else:
                    symbols.append(match[1])
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
        error('declaration_inventory', str(exc))
