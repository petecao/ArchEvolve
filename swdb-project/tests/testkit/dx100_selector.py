"""2026-10-16 ET. Fixture-only partial interface, never installed as current0.2."""
import hashlib
import json
from pathlib import Path

from conftest import FIXTURES
from testkit.dx100_trust import TRUST

def selector_row():
    from swdb.dx100_interface import HEADERS
    return {'call': 'get_data_type', 'rules': ['allocation'],
            'instances': [{'arguments': ['unsigned int'], 'arity': 0,
                           'prototype': 'unsigned char get_data_type_unsigned_int(void)',
                           'contract': r'assigns \nothing; ensures \result == 0;',
                           'definition': {'kind': 'dx100-get-data-type-u32-v1', 'value': 0,
                                          'sources': [{'root': 'project', 'path': 'apps/dx100/benchmarks/API/'+name,
                                                       'sha256': digest} for name,digest in HEADERS.items()]}}]}


LAYOUT = 'dx100-pure-selector-u32-v1'
MODEL = 'unsigned char get_data_type_unsigned_int(void) { return 0; }\n'
STATEMENT = ('Only the source-certified get_data_type<unsigned int>() helper is admitted; '
             'all other interface calls are explicitly refused. No device commands or timing reduction are used.')


def pure_selector(data, library):
    manifest = json.loads((FIXTURES/'proof/dx100/interface-declarations-e4fc4af.json').read_text())
    data.update(id='semantics.dx100_selector_fixture_0_2', version='0.2', sequence=2,
                description='Synthetic first pure-selector gate; remaining interface behavior unsupported.',
                constants={}, queries=[], wp={}, declaration_inventory={k:manifest[k] for k in ('sources','declarations')})
    data['inventory'] = {'sources': manifest['sources'], 'calls': sorted({d['name'] for d in manifest['declarations']})}
    data['rules'] = [
        {'id':'selector_value','statement':'The actual pinned u32 selector folds to UINT32_TYPE0 under the checked compiler context.',
         'cites':{'gem5_commit':manifest['upstream_commit'],'path':'apps/MAA/MAA_gem5.hpp','lines':'165-171'}},
        {'id':'selector_scope','statement':STATEMENT,
         'assumed':{'owner':'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'}}]
    data['rules'] += [{'id': name,'statement':sentence,'record_assumption':True,
                      'assumed':{'owner':'Eric' if name=='no_stale_cpu_copy' else
                                 'Probata proof-semantics maintainer; pending Yan-Ru freeze review (59)'}}
                     for name,sentence in TRUST.items()]
    calls=[]
    for name in data['inventory']['calls']:
        if name=='get_data_type':
            row=selector_row();row['rules']=['selector_value'];row['supported']=True
        else:
            row={'call':name,'prototype':'int '+name+'(void)','contract':r'requires \false; assigns \nothing;',
                 'supported':False,'rules':['selector_scope']}
            declarations=[d['declaration'] for d in manifest['declarations'] if d['name']==name]
            if len(declarations)>1:
                row['overloads']=[{'declaration':d,'prototype':'int swdb_refused_'+name+'_'+str(i)+'(void)',
                                   'contract':r'requires \false; assigns \nothing;'} for i,d in enumerate(declarations)]
        calls.append(row)
    data['calls']=calls
    folder=library/'proof_semantics/pure-selector';folder.mkdir()
    def pin(name,text):
        path=folder/name;path.write_text(text)
        return {'root':'library','path':str(path.relative_to(library)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    data['ghost']={'acsl':pin('ghost.acsl','/* No ghost state: pure selector. */\n')}
    data['model']={'layout':LAYOUT,'state':pin('state.h','/* No device state: pure selector. */\n'),
                   'logic':pin('logic.acsl','/* No added axioms. */\n'), 'c':pin('model.h',MODEL)}



def prove_selector(tmp_path, expected, *, actual=False):
    """Same unchanged source for the true and deliberately false result contracts."""
    from conftest import REPO
    from testkit.dx100_trust import run_semantics_fixture
    source = ('#include '+json.dumps(str(REPO/'apps/dx100/benchmarks/API/MAA_gem5.hpp'))+
              '\nint trust_fixture() { int observed=(int)get_data_type<uint32_t>(); return observed; }\n')
    def contract_only(contract):
        contract['proof_unit'].pop('array_domains', None)
        contract['concurrency_frame'] = []
        contract['provenance']['origin']['intrinsic_specification'] = 'ticket28-source-selector-first-gate-fixture'
        contract['clauses'][0]['statement'] = 'Synthetic u32 selector result '+str(expected)+'.'
    return run_semantics_fixture(tmp_path, 'wp', source=source, semantics_transform=pure_selector,
        contract_transform=contract_only, tool_environment={} if actual else None,
        source_files={'gem5/m5ops.h': '#pragma once\n#include <stdint.h>\n'
                      'extern "C" void m5_add_mem_region(void*,void*,uint64_t);\n'
                      'extern "C" void m5_clear_mem_region(void);\n'},
        postcondition=r'assigns \nothing; ensures \result == '+str(expected)+';')
