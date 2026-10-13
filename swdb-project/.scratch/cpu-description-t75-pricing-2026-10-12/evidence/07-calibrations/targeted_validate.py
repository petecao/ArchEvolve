"""Targeted validation of named records: schema check plus every record rule, exactly as
`swdb validate` applies them, but only to the listed IDs. Written 2026-10-12 ET (cpud ticket 07).

Usage (from a checkout's swdb-project/): python3 targeted_validate.py <records dir> <id> [<id> ...]
Prints JSON: per-ID path, sha256 of the file and problems. Exit 1 if any problem or missing ID.
"""
import hashlib
import json
import sys
from pathlib import Path

from swdb import paths, rules, vocab
from swdb.schemas import SchemaSet
from swdb.store import Store
from swdb.validate import _check_record


def main(records_dir, ids):
    store = Store(Path(records_dir))
    vocabs, problems = vocab.load_all(paths.VOCAB)
    schemas = SchemaSet(paths.SCHEMAS, vocabs, store.index())
    wanted = [r for r in store.records if r.id in ids]
    found = {r.id for r in wanted}
    out = {'records_dir': str(records_dir), 'store_problems': [str(p) for p in store.problems],
           'missing': sorted(set(ids) - found), 'records': []}
    passed = []
    for record in wanted:
        probs = sorted(_check_record(record, schemas, vocabs))
        out['records'].append({'id': record.id, 'path': record.rel, 'problems': [str(p) for p in probs]})
        if not probs:
            passed.append(record)
    context = rules.Context(store, vocabs, store.dir, paths.HOME, valid={r.rel for r in store.records})
    for record in passed:
        entry = next(e for e in out['records'] if e['id'] == record.id)
        entry['problems'] += [str(p) for p in sorted(rules.check(record, context))]
    for entry in out['records']:
        entry['sha256'] = hashlib.sha256((Path(records_dir) / entry['path']).read_bytes()).hexdigest()
    out['ok'] = not out['missing'] and all(not e['problems'] for e in out['records'])
    print(json.dumps(out, indent=1))
    return 0 if out['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2:]))
