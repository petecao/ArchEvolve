"""2026-10-16 ET. Independent read-only compact metadata for settled run630.

No project imports, external/native tools, generation, solver or remote writes.
Terms/source text stay in place; only metadata and hashes are returned.
"""
import csv
import hashlib
import json
import resource
import signal
import sys
from pathlib import Path

ROOT = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-615ddf50-t25-closed-no-growth-public-v1')
PROFILE = ROOT/'closed-no-growth-public-v1-profile'
DIRECTORY = PROFILE/'projected-c'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024**2), b''):
            digest.update(block)
    return digest.hexdigest()


def snapshot():
    rows = []
    for path in sorted(ROOT.rglob('*')):
        assert not path.is_symlink() and (path.is_file() or path.is_dir())
        if path.is_file():
            rows.append({'relative': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                         'sha256': sha(path)})
    return rows


def main():
    signal.alarm(90)
    resource.setrlimit(resource.RLIMIT_AS, (256*1024**2, 256*1024**2))
    def audit(event, args):
        if event in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            raise RuntimeError('external/native execution forbidden')
        if event == 'open' and len(args)>1 and isinstance(args[1], str) and any(x in args[1] for x in 'wax+'):
            raise RuntimeError('remote writes forbidden')
    sys.addaudithook(audit)
    before = snapshot()
    inventory = json.loads((DIRECTORY/'wp-inventory.json').read_bytes())
    standard = json.loads((DIRECTORY/'wp-goals.json').read_bytes())
    outcome = json.loads((DIRECTORY/'outcome.json').read_bytes())
    actual = json.loads((PROFILE/'result.json').read_bytes())
    expected = json.loads((PROFILE/'expected.json').read_bytes())
    properties = inventory['properties']
    goals = inventory['goals']
    assert inventory['complete'] is True and len(goals) == 21 and len(properties) == 72
    assert len({g['goal'] for g in goals}) == len({g['goal'] for g in standard}) == 21
    assert {g['goal'] for g in goals} == {g['goal'] for g in standard}
    assert len({p['property'] for p in properties}) == 72
    by_property = {p['property']: p for p in properties}
    assert all(d in by_property for p in properties for d in p['dependencies'])
    assert all(p['origin'] is None or p['origin'] in by_property for p in properties)
    with (DIRECTORY/'wp-properties.csv').open() as stream:
        reader = csv.reader(stream, delimiter='\t')
        header = next(reader)
        assert header == ['directory','file','line','function','property kind','status','property']
        csv_rows = []
        for fields in reader:
            if not fields:
                continue
            if len(fields) == 7:
                csv_rows.append(dict(zip(header, fields)))
            elif len(fields) == 1 and fields[0][:1].isspace() and csv_rows:
                csv_rows[-1]['property'] += '\n'+fields[0]
            else:
                raise ValueError('malformed multiline property CSV')
    pins = {name: sha(PROFILE/name) for name in (
        'entry.py','expected.json','result.json','projected-c/frama-c.log','projected-c/wp_input.c',
        'projected-c/wp-normalized.c','projected-c/wp-inventory.json','projected-c/wp-goals.json',
        'projected-c/wp-properties.csv','projected-c/outcome.json','anchors.fresh.json','closed-view-certificate.json')}
    assert pins['result.json'] == 'b25c1f791c7273f3f79e50b96e4e905cf4bedf6fda5b94e6e2683bcd18d89f30'
    assert pins['projected-c/frama-c.log'] == '5ba36b975ccdcf981fe3be4f21597ad1d014f4f30515919e7cdadb4b13a5ac00'
    assert pins['projected-c/wp_input.c'] == expected['wp_input_sha256']
    assert outcome['verdict'] == 'not_proven' and outcome['failure_class'] == 'unclassified_wp_outcome'
    assert actual['producer_complete'] is False and actual['caller_acceptance'] is False
    after = snapshot()
    assert before == after
    report = {'created':'2026-10-16 ET', 'scope':__doc__, 'raw':str(ROOT), 'pins':pins,
              'native_goals':[{key:g.get(key) for key in ('goal','property','function','line','smoke','passed','results')} for g in goals],
              'standard_goals':[{key:g.get(key) for key in ('goal','property','function','line','smoke','passed','verdict','provers')} for g in standard],
              'native_properties':[{key:p.get(key) for key in ('property','function','line','property_variant','status_registered','property_export_origin','origin','dependencies','extern','source_file')} for p in properties],
              'csv_rows':[{'function':r['function'] or None,'line':int(r['line']),'kind':r['property kind'],'status':r['status'],
                           'predicate_text_sha256':hashlib.sha256(r['property'].encode()).hexdigest()} for r in csv_rows],
              'ordinary_reader':{'verdict':outcome['verdict'],'failure_class':outcome['failure_class'],'why':outcome['why'],'assumptions':outcome['assumptions']},
              'original_entry_refusal':{'type':actual['error_type'],'error':actual['error'],'producer_complete':actual['producer_complete']},
              'resources':actual['resources'],
              'outer_metadata':{name:json.loads((ROOT/name).read_bytes()) for name in ('resources.json','outer-resources.json','source-after.json')},
              'raw_manifest':after, 'raw_unchanged':True, 'raw_file_count':len(after),
              'raw_bytes':sum(r['bytes'] for r in after),'actual_evaluations':0,
              'proof_acceptance':False,'source_typed_bridge_established':False,'caller_acceptance':False}
    raw = (json.dumps(report, sort_keys=True, indent=2)+'\n').encode()
    assert len(raw) < 1024**2
    signal.alarm(0)
    sys.stdout.buffer.write(raw)


if __name__ == '__main__':
    main()
