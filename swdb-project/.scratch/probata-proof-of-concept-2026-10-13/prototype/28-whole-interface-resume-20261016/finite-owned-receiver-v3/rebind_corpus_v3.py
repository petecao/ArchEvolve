"""Pure narrow source rebind; V2 artifacts are never edited."""
from pathlib import Path
import json
import sys
import importlib.util

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'finite-owned-receiver-v2'
spec=importlib.util.spec_from_file_location('finite_owned_v3_rebind',HERE/'finite_owned_receiver_v3.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)

def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=m.sha(raw))
def save(path,doc):path.write_bytes(m.canonical(doc)+b'\n');return pin(path)

def rebind(output):
    predecessor=json.loads((OLD/'source-packet-v2.json').read_bytes())
    for key in ('source_files','selected_input_union','prepared_owned_corpus'):
        for row in predecessor[key]:assert pin(Path(row['path']))==row
    output.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((OLD/'prepared-owned-corpus-v2/manifest.json').read_bytes());rows=[]
    for case in manifest['cases']:
        directory=output/case['case_id'];directory.mkdir()
        policy=json.loads(Path(case['selection']['path']).read_bytes());policy['composer']=pin(HERE/'finite_owned_receiver_v3.py')
        selected=save(directory/'composition-policy-v3.json',policy)
        result=m.prepare(m.OwnedSelection(m.Pin.parse(selected)))
        for key,raw in [('combined.c',result.c_text.encode()),('owned-receiver.c',result.receiver_c_text.encode()),
                        ('draw-binding.json',result.draw_binding_json),('integration.json',result.integration_json)]:
            assert raw==Path(case['outputs'][key]['path']).read_bytes()
        path=directory/'composition-certificate-v3.json';path.write_bytes(result.certificate_json)
        outputs=dict(case['outputs']);outputs['composition-certificate.json']=pin(path)
        rows.append(dict(case,selection=selected,outputs=outputs))
    current=dict(manifest,cases=rows,schema='finite-owned-composition-corpus-3',canonical_type_sensitive_metadata_identity=True,
        all_V2_entry_context_receiver_prepared_C_draw_resource_integration_artifacts_reused=True)
    save(output/'manifest-v3.json',current);return current

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('one fresh V3 source output directory required')
    current=rebind(Path(sys.argv[1]).resolve());print(json.dumps(dict(cases=len(current['cases']),actual_execution=False)))
