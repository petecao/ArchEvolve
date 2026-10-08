"""Validate a paper mapping in memory; no simulator or numeric helper runs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from archevolve.hardware_catalog import load_catalog, query_catalog, validate_catalog
from tools.render_mermaid import RequestError

BASE = '5608d112667b72e971b3093325edda7454f579c8'
DESIGN = 'cobra-hpca2022-tuple-binning'


def apply_addition(catalog, addition):
    trial = deepcopy(catalog)
    for field in ('sources', 'claims'):
        assert not (trial[field].keys() & addition[field].keys())
        trial[field].update(deepcopy(addition[field]))
    for field in ('mechanism_families', 'decision_questions', 'designs'):
        assert not ({x['id'] for x in trial[field]} & {x['id'] for x in addition[field]})
        trial[field].extend(deepcopy(addition[field]))
    return trial


def main():
    addition = json.loads((HERE/'proposed-addition.json').read_text())
    provenance = json.loads((HERE/'provenance.json').read_text())
    assert addition['base_commit'] == BASE
    assert addition['production_admitted'] is False
    assert len(addition['designs']) == 1
    design = addition['designs'][0]
    assert design['id'] == DESIGN and design['record_kind'] == 'mapping'
    assert len(design['operations']) == 1
    op = design['operations'][0]
    assert (op['operation'], op['subtype'], op['execution_role']) == ('write','tuple_bin','execute')
    assert op['address_patterns'] == [] and 'type_constraints' not in op
    assert op['result']['old_value'] == 'not_applicable'
    assert all(p['domain'] is None for p in design['parameters'])
    checks = []
    for entry in provenance['sources'] + provenance['handoff_files'] + provenance['schema_files']:
        raw = Path(entry['path']).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == entry['sha256'] and len(raw) == entry['bytes'], entry['path']
        checks.append(dict(path=entry['path'],sha256=digest,bytes=len(raw)))
    pdf = next(s for s in provenance['sources'] if s['id']=='cobra-pdf')
    assert Path(pdf['path']).read_bytes().startswith(b'%PDF-')
    assert pdf['sha256'] == addition['sources']['cobra-hpca2022-paper']['sha256']
    info = subprocess.check_output(['pdfinfo', pdf['path']], text=True)
    assert next(line for line in info.splitlines() if line.startswith('Pages:')).split()[1] == '15'
    page = subprocess.check_output(['pdftotext','-f','1','-l','1',pdf['path'],'-'],text=True)
    normalized = ' '.join(page.split())
    assert addition['sources']['cobra-hpca2022-paper']['title'] in normalized
    assert all(a in normalized for a in ('Vignesh Balaji','Brandon Lucia'))
    text_entry = next(s for s in provenance['sources'] if s['id']=='cobra-text')
    pages = Path(text_entry['path']).read_text().split('\f')
    assert 'bininit' in pages[5] and 'binupdate' in pages[5]
    assert 'binflush' in pages[7] and 'Sniper' in pages[8]
    meta = next(s for s in provenance['sources'] if s['id']=='cobra-crossref')
    message = json.loads(Path(meta['path']).read_text())['message']
    assert message['title'] == [addition['sources']['cobra-hpca2022-paper']['title']]
    assert message['DOI'].lower() == '10.1109/hpca53966.2022.00047'
    assert message['page'] == '543-557'
    assert 'HPCA' in message['container-title'][0]
    assert message['published']['date-parts'] == [[2022,4]]
    assert [(a['given'],a['family']) for a in message['author']] == [('Vignesh','Balaji'),('Brandon','Lucia')]
    assert provenance['new_download_bytes'] == 0
    assert provenance['download_budget_bytes'] == 16*1024**2
    free = {str(p):shutil.disk_usage(p).free for p in (ROOT,Path('/tmp'))}
    assert all(n >= provenance['disk_floor_bytes'] == 16*1024**3 for n in free.values())
    path = ROOT/'catalog/hardware-v0.1.yaml'
    before = path.read_bytes()
    assert before == subprocess.check_output(['git','show',BASE+':catalog/hardware-v0.1.yaml'],cwd=ROOT)
    current,digest = load_catalog(path)
    frozen = deepcopy(current)
    trial = apply_addition(current,addition)
    validation = validate_catalog(trial)
    # All production registries/records remain byte/structurally identical.
    for field in ('sources','claims'):
        assert all(trial[field][k] == v for k,v in current[field].items())
    for field in ('mechanism_families','decision_questions','designs'):
        assert trial[field][:len(current[field])] == current[field]
    malformed = deepcopy(trial)
    malformed['designs'][-1]['operations'][0]['claim_refs'].append('missing-cobra-claim')
    try:
        validate_catalog(malformed)
    except RequestError as e:
        dangling_rejection = str(e)
    else:
        raise AssertionError('Dangling reference accepted')
    def proposal_rows(result):
        return [x for x in result['matches']+result['excluded'] if x['design_id']==DESIGN]
    query_checks=[]
    tests=[({'operation':'write','subtype':'tuple_bin'},'mapping_reference'),
           ({'operation':'write'},'mapping_reference'),
           ({'operation':'write','subtype':'tuple_bin','execution_role':'assist'},None),
           ({'operation':'write','subtype':'tuple_bin','require_old_value':True},'excluded')]
    tests += [({'operation':'write','subtype':'tuple_bin','address_pattern':p},'needs_evidence')
              for p in ('sequential','constant_stride','indirect','ranged_indirect','chained_indirect','pointer_chase')]
    tests += [({'operation':'write','subtype':'tuple_bin','payload_type':t,'index_width_bits':w},'needs_evidence')
              for t,w in [('uint32',32),('float32',32),('float64',64)]]
    tests += [(dict(operation=o,subtype=s),None) for o,s in
              [('read','gather'),('read','stream_load'),('read','prefetch'),('write','scatter'),
               ('read_modify_write','add'),('read_modify_write','cas'),('reduce','add')]]
    for q,wanted in tests:
        result=query_catalog(trial,**q)
        rows=proposal_rows(result)
        assert len(rows)==(0 if wanted is None else 1), (q,rows)
        if rows:
            assert rows[0]['status']==wanted,(q,rows)
            assert rows[0]['requirements']==design['requirements']
            assert rows[0]['operation']==op
            assert rows[0]['requirement_status']=='not_discharged_by_retrieval'
        # A proposal adds no capability to any pre-existing row, even in broad queries.
        original=query_catalog(current,**q)
        assert [x for x in result['matches'] if x['design_id']!=DESIGN]==original['matches']
        assert [x for x in result['excluded'] if x['design_id']!=DESIGN]==original['excluded']
        query_checks.append(dict(query=q,expected=wanted,proposal_rows=len(rows),unchanged_existing_entries=True))
    unchanged=0
    for d in current['designs']:
        for o in d['operations']:
            for typed in ({},{'payload_type':'float32','index_width_bits':32}):
                q=dict(operation=o['operation'],subtype=o['subtype'],design_id=d['id'],**typed)
                assert query_catalog(current,**q)==query_catalog(trial,**q)
                unchanged+=1
    assert current==frozen and path.read_bytes()==before
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    assert all(p.startswith('docs/proposals/cobra-hpca2022/') for p in changed)
    report=dict(format='cobra-proposal-validation-v1',base_commit=BASE,
                production_admitted=False,in_memory_validation=validation,
                production_validation=validate_catalog(current),production_catalog_sha256=hashlib.sha256(before).hexdigest(),
                loader_digest=digest,source_checks=checks,query_checks=query_checks,
                dangling_reference_rejected=dangling_rejection,unchanged_existing_designs=len(current['designs']),
                unchanged_existing_query_trials=unchanged,all_existing_records_unchanged=True,
                free_bytes=free,new_download_bytes=0,
                scope='Structure, references, source-byte/identity provenance and query boundaries only; no executable hardware, numeric correctness, OS binding, reorder legality or performance certification.')
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(valid=True,in_memory_designs=validation['designs'],production_designs=len(current['designs']),
                          query_checks=len(query_checks),unchanged_existing_queries=unchanged,production_admitted=False)))


if __name__=='__main__':
    main()
