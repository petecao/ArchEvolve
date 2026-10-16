"""2026-10-16 ET. Export exact prepared parser inputs; never starts a tool."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def pin(path):
    path=Path(path)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    parser.add_argument('raw',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    sys.path.insert(0,str(args.project.resolve()))
    import yaml
    from swdb import framac,proof_semantics
    from swdb.library import Library
    output=args.output.resolve();output.mkdir(exist_ok=False)
    inputs=[];origins=[]
    selections=(('correct','test_public_stream_binds_sourc0'),('wrong','test_public_stream_binds_sourc1'),
                ('combined','test_public_stream_places_part0'))
    library=None
    for label,case in selections:
        folder=args.raw/'pytest'/case
        records=list((folder/'records/proofs').glob('*.yaml'))
        if len(records)!=1:raise ValueError('expected one retained public preparation record')
        record=yaml.safe_load(records[0].read_text())
        if record['failure_class']!='tool_crash' or record['settings']['verifier_launched']is not True:
            raise ValueError('expected the explicitly scripted exit99 preparation')
        wp=next(p for p in record['evidence']['reports']if p.get('name')=='wp_input')
        if pin(wp['path'])['sha256']!=wp['sha256']:raise ValueError('changed public WP input')
        target=output/f'wp-{label}.c';shutil.copyfile(wp['path'],target)
        inputs.append({'name':target.name,**{k:v for k,v in pin(target).items()if k!='path'},'role':'exact public WP input; parser only'})
        origins.append({'label':label,'record':pin(records[0]),'wp_input':pin(wp['path']),
                        'source':pin(folder/'library/proof_units/trust.cc'),
                        'contract':pin(folder/'library/rewrite_contracts/trust.yaml'),
                        'semantics':pin(folder/'library/proof_semantics/dx100_trust_fixture.yaml')})
        if label=='correct':library=Library(folder/'library')
    entry='semantics.dx100_stream_fixture_0_2';data=library.get(entry)
    texts={'ghost.acsl':library.resolve(data['ghost']['acsl']).read_text(),
           **{'model.'+k:library.resolve(data['model'][k]).read_text()for k in ('state','logic','c')}}
    generated={'all-contracts.c':proof_semantics.acsl_source(data,texts),
               'ordinary-model.c':('#include <stdint.h>\n'
                 'extern void __swdb_parser_assert(int);\n#define DX_ASSERT(e) __swdb_parser_assert(!!(e))\n'+
                 proof_semantics.model_for(library,entry).c_text)}
    for name,text in generated.items():
        target=output/name;target.write_text(text)
        inputs.append({'name':name,**{k:v for k,v in pin(target).items()if k!='path'},
                       'role':'normal all-contract validation input'if name=='all-contracts.c'else
                              'normal ordinary C model with explicitly parse-only assertion declaration'})
    # Standard C headers only. Their implementation is supplied by the root's
    # pinned Frama33 installation, not copied from this ARM compiler runtime.
    manifest={'date_et':'2026-10-16','status':'prepared; actual parser unexecuted by author',
      'parser_flags':list(framac.FLAGS),'inputs':inputs,'origins':origins,
      'stdlib_headers':['stdbool.h','stddef.h','stdint.h'],
      'generator_sources':[pin(args.project/'swdb'/name)for name in
          ('framac.py','proof_semantics.py','dx100_stream_model.py','wp_adapter.py')],
      'scope':'Parser/type check only. No WP, solvers, contract/body agreement, source refinement, totality, hardware liveness or full28 acceptance.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':pin(output/'manifest.json'),'inputs':len(inputs),
                      'input_bytes':sum(row['bytes']for row in inputs)},indent=2))


if __name__=='__main__':main()
