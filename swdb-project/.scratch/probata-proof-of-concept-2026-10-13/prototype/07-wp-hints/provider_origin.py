"""Scoped operation/record lineage for method22, created2026-10-15 ET.

The pinned local harness is trusted. Origin is the actual scoped MCP request or
CLI final artifact, corroborated against that call's raw CLI events at admission.
This is not authentication against a hostile same-UID editor.
"""
import hashlib
import json
from pathlib import Path

import loop as L

REQUIRED = [False]
CONTEXT = [None]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def record_digest(hint):
    return digest({k: hint[k] for k in ('id', 'anchor', 'kind', 'text')})


def records(hints):
    return [{'id': h['id'], 'record_sha256': record_digest(h), 'origin': h.get('provider_origin')} for h in hints]


def _rows(out):
    p = Path(out) / 'provider-origin.jsonl'
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []


def _validate_trace(rows):
    attempts = {}
    materialized, contents = {}, {}
    for row in rows:
        if row['event'] == 'attempt':
            unsigned = {k: v for k, v in row.items() if k != 'receipt_sha256'}
            if digest(unsigned) != row['receipt_sha256'] or digest(row['ops']) != row['ops_sha256']:
                raise RuntimeError('raw operation receipt changed')
            if row['receipt_sha256'] in attempts:
                raise RuntimeError('duplicate raw operation receipt')
            if any(materialized.get(h['record_sha256']) != h.get('origin') or not h.get('origin') for h in row['base_records']):
                raise RuntimeError('attempt base has no preceding provider lineage')
            attempts[row['receipt_sha256']] = row
        elif row['event'] == 'materialized':
            if row['receipt_sha256'] not in attempts:
                raise RuntimeError('materialized set has no preceding raw operation receipt')
            if digest(row['candidate_hints']) != row['candidate_set_sha256'] or records(row['candidate_hints']) != row['candidate_records']:
                raise RuntimeError('materialized record hash mismatch')
            base = {h['record_sha256']: h for h in attempts[row['receipt_sha256']]['base_records']}
            for h in row['candidate_hints']:
                origin = h.get('provider_origin')
                fingerprint = record_digest(h)
                if fingerprint in base:
                    if materialized.get(fingerprint) != origin:
                        raise RuntimeError('base record lacks preceding provider lineage')
                else:
                    if not isinstance(origin, dict) or origin.get('receipt_sha256') != row['receipt_sha256']:
                        raise RuntimeError('new record has no matching scoped operation')
                    index = origin['operation_index']
                    ops = attempts[row['receipt_sha256']]['ops']
                    if type(index) is not int or not 0 <= index < len(ops):
                        raise RuntimeError('record operation index invalid')
                    op = ops[index]
                    if op['op'] not in {'add', 'edit'} or origin['operation_sha256'] != digest(op) or h['text'] != op['text']:
                        raise RuntimeError('record differs from raw provider operation')
                    parent = next((old for old in attempts[row['receipt_sha256']]['base_records'] if old['id'] == op['id']), None) if op['op'] == 'edit' else None
                    if op['op'] == 'edit' and parent is None:
                        raise RuntimeError('edited record parent absent')
                    parent_hint = contents.get(parent['record_sha256']) if parent else None
                    placement = (parent_hint['anchor'], parent_hint['kind']) if parent_hint else (op['anchor'], op['kind'])
                    if (h['anchor'], h['kind']) != placement:
                        raise RuntimeError('record anchor/kind differs from raw operation lineage')
                    if origin['parent_record_sha256'] != (parent['record_sha256'] if parent else None):
                        raise RuntimeError('edit parent lineage mismatch')
                    ordinal = sum(o['op'] in {'add', 'edit'} for o in ops[:index+1])
                    if h['id'] != f"{row['materialization_tag']}h{ordinal}":
                        raise RuntimeError('record identity differs from operation placement')
                materialized[fingerprint] = origin
                contents[fingerprint] = h
        else:
            raise RuntimeError('unknown provider trace event')
    return materialized


def verify(out, hints):
    admitted = _validate_trace(_rows(out))
    for h in hints:
        origin = h.get('provider_origin')
        if h['id'].startswith('seed') or not h.get('provenance', '').startswith(f"codex {L.PIN['model']} {L.PIN['effort']} round ") or not isinstance(origin, dict) or admitted.get(record_digest(h)) != origin:
            raise RuntimeError('untraceable/provider-external hint record: ' + h['id'])


def begin(out, best, ops, tag):
    """Retain raw operations before design/schema/parser refusal or candidate use."""
    context = CONTEXT[0]
    if not isinstance(context, dict) or context.get('pin') != L.PIN:
        raise RuntimeError('missing scoped provider context')
    r = context.get('round')
    if type(r) is not int or r < 1 or context.get('kind') not in {'mcp', 'final'}:
        raise RuntimeError('invalid scoped provider context')
    source = Path(out) / (f'tool-r{r}/provider-requests.jsonl' if context['kind'] == 'mcp' else f'codex-r{r}/final.json')
    if context['kind'] == 'mcp':
        lines = source.read_text().splitlines()
        request = json.loads(lines[context['request_index']])
        if digest(request) != context['request_sha256']:
            raise RuntimeError('raw MCP request changed')
        supplied = (request.get('params', {}).get('arguments') or {}).get('ops') or []
    else:
        if L.sha(source) != context['source_sha256']:
            raise RuntimeError('raw CLI final artifact changed')
        supplied = json.loads(source.read_text()).get('ops') or []
    if supplied != ops:
        raise RuntimeError('operations differ from scoped raw provider input')
    verify(out, best['hints'])
    row = {'event': 'attempt', 'tag': tag, 'context': context, 'ops': ops,
           'ops_sha256': digest(ops), 'base_records': records(best['hints']), 'time': L.now()}
    row['receipt_sha256'] = digest(row)
    with (Path(out) / 'provider-origin.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    return row


def bind(out, best, hints, ops, receipt, materialization_tag):
    """Link deterministic placement/IDs to exact operation text; never repair text."""
    materialized = [h for h in hints if h['id'] not in {x['id'] for x in best['hints']}]
    changes = [(i, o) for i, o in enumerate(ops) if o['op'] in {'add', 'edit'}]
    if len(materialized) != len(changes):
        raise RuntimeError('operation/record cardinality mismatch')
    parents = {h['id']: h for h in best['hints']}
    by_id = {h['id']: h for h in materialized}
    for ordinal, (index, op) in enumerate(changes, 1):
        h = by_id[f'{materialization_tag}h{ordinal}']
        old = parents.get(op.get('id')) if op['op'] == 'edit' else None
        anchor, kind = (old['anchor'], old['kind']) if old else (op['anchor'], op['kind'])
        if (h['text'], h['anchor'], h['kind']) != (op['text'], anchor, kind):
            raise RuntimeError('merger altered provider semantic content')
        h['provider_origin'] = {'receipt_sha256': receipt['receipt_sha256'], 'operation_index': index,
            'operation_sha256': digest(op), 'parent_record_sha256': record_digest(old) if old else None}
    row = {'event': 'materialized', 'receipt_sha256': receipt['receipt_sha256'],
           'candidate_records': records(hints), 'candidate_hints': hints, 'materialization_tag': materialization_tag, 'candidate_set_sha256': digest(hints)}
    with (Path(out) / 'provider-origin.jsonl').open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    return hints


def audit(out, best, history):
    """Corroborate every raw request with the exact owned CLI event stream."""
    errors, sessions = [], {}
    try:
        rows = _rows(out)
        verify(out, best['hints'])
        rounds = {h['round'] for h in history if h.get('codex') is not None}
        for r in rounds:
            path = Path(out) / f'codex-r{r}/stdout.jsonl'
            events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            threads = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
            sessions[str(r)] = {'thread': threads[-1] if threads else next((h.get('codex_thread') for h in history if h.get('round') == r), None),
                                'stdout_sha256': L.sha(path)}
            emitted = {}
            finals = []
            for e in events:
                item = e.get('item') or {}
                if item.get('type') == 'mcp_tool_call' and item.get('server') == 'probata':
                    emitted[item.get('id')] = {'tool': item.get('tool'), 'arguments': item.get('arguments') or {}}
                if item.get('type') == 'agent_message':
                    try:
                        finals.append(json.loads(item.get('text', '')))
                    except ValueError:
                        pass
            requests = Path(out) / f'tool-r{r}/provider-requests.jsonl'
            seen = set()
            for row in rows:
                if row['event'] != 'attempt' or row['context']['round'] != r:
                    continue
                c = row['context']
                if c['kind'] == 'mcp':
                    request = json.loads(requests.read_text().splitlines()[c['request_index']])
                    if digest(request) != c['request_sha256']:
                        raise RuntimeError('MCP raw request changed after use')
                    if c['request_index'] in seen:
                        continue
                    seen.add(c['request_index'])
                    want = {'tool': request['params']['name'], 'arguments': request['params'].get('arguments') or {}}
                    match = next((key for key, value in emitted.items() if value == want), None)
                    if match is None:
                        raise RuntimeError('raw MCP operation not corroborated by scoped CLI event')
                    emitted.pop(match)
                else:
                    final = Path(out) / f'codex-r{r}/final.json'
                    if L.sha(final) != c['source_sha256'] or not any(f.get('ops') == row['ops'] for f in finals):
                        raise RuntimeError('CLI final operations lack scoped message corroboration')
        threads = [session['thread'] for session in sessions.values()]
        if any(not thread for thread in threads) or len(set(threads)) > 1:
            raise RuntimeError('provider origin requires one exact fresh scoped conversation')
        for row in rows:
            if row['event'] == 'attempt':
                unsigned = {k: v for k, v in row.items() if k != 'receipt_sha256'}
                if digest(unsigned) != row['receipt_sha256'] or digest(row['ops']) != row['ops_sha256']:
                    raise RuntimeError('raw operation receipt changed')
            if row['event'] == 'materialized':
                if digest(row['candidate_hints']) != row['candidate_set_sha256'] or records(row['candidate_hints']) != row['candidate_records']:
                    raise RuntimeError('materialized record hash mismatch')
                if any(not h.get('origin') for h in row['candidate_records']):
                    raise RuntimeError('attempted set contains provider-external record')
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append(str(exc))
    return {'complete': not errors, 'errors': errors, 'sessions': sessions,
            'trace_sha256': L.sha(Path(out) / 'provider-origin.jsonl') if (Path(out) / 'provider-origin.jsonl').exists() else None,
            'trust_boundary': 'pinned local harness/scoped MCP transport, not hostile same-UID authentication'}
