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


def _canonical(hints):
    return [{**{k: h[k] for k in ('id', 'anchor', 'kind', 'text')},
             'provider_origin': h.get('provider_origin')} for h in hints]


def _replay(base, ops, tag, receipt):
    """Independent complete transformation: unchanged, deleted and added records."""
    hints = json.loads(json.dumps(_canonical(base)))
    ordinal = 0
    for index, op in enumerate(ops):
        if op['op'] == 'delete':
            hints = [h for h in hints if h['id'] != op['id']]
            continue
        ordinal += 1
        if op['op'] == 'edit':
            old = next((h for h in hints if h['id'] == op['id']), None)
            if old is None:
                raise RuntimeError('edited parent absent from captured base')
            parent, anchor, kind = record_digest(old), old['anchor'], old['kind']
            position = hints.index(old)
        elif op['op'] == 'add':
            parent, anchor, kind, position = None, op['anchor'], op['kind'], len(hints)
        else:
            raise RuntimeError('invalid materialized operation')
        hint = {'id': f'{tag}h{ordinal}', 'anchor': anchor, 'kind': kind, 'text': op['text'],
                'provider_origin': {'receipt_sha256': receipt, 'operation_index': index,
                                   'operation_sha256': digest(op), 'parent_record_sha256': parent}}
        if op['op'] == 'edit':
            hints[position] = hint
        else:
            hints.append(hint)
    return hints


def _validate_trace(rows):
    attempts, materialized = {}, {}
    for row in rows:
        if row['event'] in {'attempt', 'pre-attempt-refusal'}:
            context = row['context']
            if context.get('kind') not in {'mcp', 'final'} or type(context.get('round')) is not int or context['round'] < 1 or context.get('pin') != L.PIN:
                raise RuntimeError('invalid scoped trace context')
            unsigned = {k: v for k, v in row.items() if k != 'receipt_sha256'}
            if digest(unsigned) != row['receipt_sha256'] or digest(row['ops']) != row['ops_sha256']:
                raise RuntimeError('raw operation receipt changed')
            if row['receipt_sha256'] in attempts or records(row['base_hints']) != row['base_records']:
                raise RuntimeError('duplicate receipt or captured base hash mismatch')
            if any(materialized.get((record_digest(h), digest(h.get('provider_origin')))) != _canonical([h])[0] for h in row['base_hints']):
                raise RuntimeError('attempt base has no preceding provider lineage')
            attempts[row['receipt_sha256']] = row
        elif row['event'] == 'materialized':
            attempt = attempts.get(row['receipt_sha256'])
            if attempt is None or attempt['event'] != 'attempt':
                raise RuntimeError('materialized set has no preceding raw operation attempt')
            if digest(row['candidate_hints']) != row['candidate_set_sha256'] or records(row['candidate_hints']) != row['candidate_records']:
                raise RuntimeError('materialized record hash mismatch')
            expected = _replay(attempt['base_hints'], attempt['ops'], row['materialization_tag'], row['receipt_sha256'])
            if _canonical(row['candidate_hints']) != expected:
                raise RuntimeError('full candidate differs from exact raw-operation transformation')
            for h in row['candidate_hints']:
                materialized[(record_digest(h), digest(h.get('provider_origin')))] = _canonical([h])[0]
        else:
            raise RuntimeError('unknown provider trace event')
    return materialized


def verify(out, hints):
    admitted = _validate_trace(_rows(out))
    for h in hints:
        origin = h.get('provider_origin')
        if h['id'].startswith('seed') or not h.get('provenance', '').startswith(f"codex {L.PIN['model']} {L.PIN['effort']} round ") or not isinstance(origin, dict) or admitted.get((record_digest(h), digest(origin))) != _canonical([h])[0]:
            raise RuntimeError('untraceable/provider-external hint record: ' + h['id'])


def begin(out, best, ops, tag, refusal=None):
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
    row = {'event': 'pre-attempt-refusal' if refusal else 'attempt', 'tag': tag, 'context': context, 'ops': ops,
           'refusal': refusal, 'base_hints': best['hints'],
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
        if any(row['context']['round'] not in rounds for row in rows if row['event'] in {'attempt', 'pre-attempt-refusal'}):
            raise RuntimeError('trace references an unscoped provider round')
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
                if item.get('type') == 'mcp_tool_call' and item.get('server') == 'probata' and item.get('tool') in {'check_edit', 'propose_edit'}:
                    emitted[item.get('id')] = {'tool': item.get('tool'), 'arguments': item.get('arguments') or {}}
                if item.get('type') == 'agent_message':
                    try:
                        finals.append(json.loads(item.get('text', '')))
                    except ValueError:
                        pass
            requests = Path(out) / f'tool-r{r}/provider-requests.jsonl'
            request_rows = [json.loads(line) for line in requests.read_text().splitlines()] if requests.exists() else []
            scoped = [row for row in rows if row['event'] in {'attempt', 'pre-attempt-refusal'} and row['context']['round'] == r]
            consumed = set()
            for index, request in enumerate(request_rows):
                name = request.get('params', {}).get('name')
                if name not in {'check_edit', 'propose_edit'}:
                    continue
                arguments = request['params'].get('arguments') or {}
                want = {'tool': name, 'arguments': arguments}
                match = next((key for key, value in emitted.items() if value == want), None)
                if match is None:
                    raise RuntimeError('raw MCP request not corroborated by scoped CLI event')
                emitted.pop(match)
                receipts = [row for row in scoped if row['context']['kind'] == 'mcp' and row['context']['request_index'] == index]
                if len(receipts) != 1:
                    raise RuntimeError('each raw edit request needs exactly one attempt or explicit refusal receipt')
                receipt = receipts[0]
                consumed.add(receipt['receipt_sha256'])
                if (receipt['context']['request_sha256'] != digest(request) or receipt['context']['pin'] != L.PIN
                        or receipt['ops'] != (arguments.get('ops') or [])):
                    raise RuntimeError('raw MCP request/operation receipt mismatch')
            if emitted:
                raise RuntimeError('scoped CLI edit request lacks raw MCP transport receipt')
            final = Path(out) / f'codex-r{r}/final.json'
            final_data = json.loads(final.read_text()) if final.exists() else {}
            final_receipts = [row for row in scoped if row['context']['kind'] == 'final']
            if len(final_receipts) != bool(final_data.get('ops')):
                raise RuntimeError('nonempty final operations need exactly one attempt or explicit refusal')
            for row in scoped:
                c = row['context']
                if c['kind'] == 'mcp':
                    if row['receipt_sha256'] not in consumed or not 0 <= c['request_index'] < len(request_rows):
                        raise RuntimeError('trace references missing raw MCP request')
                elif (L.sha(final) != c['source_sha256'] or c['pin'] != L.PIN or row['ops'] != final_data.get('ops')
                      or not finals or finals[-1] != final_data):
                    raise RuntimeError('CLI final operations lack exact last scoped message corroboration')
        threads = [session['thread'] for session in sessions.values()]
        if any(not thread for thread in threads) or len(set(threads)) > 1:
            raise RuntimeError('provider origin requires one exact fresh scoped conversation')
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        errors.append(str(exc))
    return {'complete': not errors, 'errors': errors, 'sessions': sessions,
            'trace_sha256': L.sha(Path(out) / 'provider-origin.jsonl') if (Path(out) / 'provider-origin.jsonl').exists() else None,
            'trust_boundary': 'pinned local harness/scoped MCP transport, not hostile same-UID authentication'}
