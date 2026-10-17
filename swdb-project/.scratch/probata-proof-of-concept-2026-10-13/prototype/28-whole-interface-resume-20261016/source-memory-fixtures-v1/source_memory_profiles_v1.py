"""2026-10-16 ET. Exact prospective same-thread original-source profile set.

This prepares compiler requests and expected rule verdicts. It never produces a
compiler/source/receiver certificate or runs a program/tool. A future source
policy must separately admit the complete same-TU, original physical project,
per-caller source/ABI/lifetime projection and owned mapping/runtime receipts.
The existing fixed79/80 source policy is unchanged.
"""
import hashlib
import json
from pathlib import Path
import stat

SOURCE_SHA = '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
INDEX_SHA = 'd48a3971f2e9421e736d72ff160074f22e9cbbb7c9c756ef52457a5c4314b3b6'
HEADERS = {
    'MAA.hpp': '4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',
    'MAA_gem5.hpp': '5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174',
}
PROFILES = (
    ('whole_same_thread_read_during_store', 7, 'refuted', 'store-footprint-cpu-access',
     ('maa_stream_store', 'std::uint32_t observed = data[0];', 'wait_ready(payload);')),
    ('whole_same_thread_write_during_gather', 9, 'refuted', 'same-thread-read-footprint-write',
     ('maa_indirect_load', 'data[0] = 9;', 'wait_ready(result);')),
    ('whole_same_thread_read_during_gather', 7, 'proven', None,
     ('maa_indirect_load', 'std::uint32_t observed = data[0];', 'wait_ready(result);')),
)


class Refused(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise Refused(message)


def stable(value):
    return tuple(getattr(value, name) for name in ('st_dev','st_ino','st_mode','st_nlink',
        'st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))


def read(path, expected, limit=131072):
    path=Path(path); before=path.lstat()
    need(path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode)
         and 0 < before.st_size <= limit, 'bounded canonical physical fixture input required')
    with path.open('rb') as handle:
        raw=handle.read(limit+1)
    need(len(raw)==before.st_size and stable(path.lstat())==stable(before)
         and hashlib.sha256(raw).hexdigest()==expected, 'fixture/source inventory pin differs')
    return raw, {'path':str(path),'bytes':len(raw),'sha256':expected}


def function_span(source, name):
    # Exact file SHA closes this tiny lexical grammar; it is not an AST/source
    # certificate. The actual caller range and ID must come from the full TU.
    marker='std::uint32_t '+name+'() {'
    need(source.count(marker)==1,'one exact prospective caller declaration required')
    start=source.index(marker); cursor=start+len(marker); depth=1
    while depth:
        need(cursor<len(source),'unclosed exact prospective caller')
        depth+=(source[cursor]=='{')-(source[cursor]=='}');cursor+=1
    return start,cursor


def prepare(project, source_path):
    project=Path(project)
    need(project.is_absolute() and project.resolve(strict=True)==project,'canonical original-header project required')
    raw,source_pin=read(source_path,SOURCE_SHA);text=raw.decode('ascii')
    header_pins=[]
    for name,expected in HEADERS.items():
        _,pin=read(project/'apps/dx100/benchmarks/API'/name,expected);header_pins.append(pin)
    inventory,index_pin=read(project/'tests/fixtures/proof/dx100/interface-declarations-e4fc4af.json',INDEX_SHA)
    declarations=json.loads(inventory)['declarations'];names={row['name'] for row in declarations}
    need(len(declarations)==27 and len(names)==26,'immutable complete interface inventory differs')
    cases=[]
    for name,result,verdict,rule,ordered in PROFILES:
        start,end=function_span(text,name);body=text[start:end]
        issue=body.index(ordered[0]);access=body.index(ordered[1],issue);wait=body.index(ordered[2],access)
        need(issue<access<wait and body.count(ordered[0])==1,'issue/CPU-access/covering-wait sequence differs')
        need('std::uint32_t data[16] = {7, 11};' in body
             and 'add_mem_region(data, data + 16);' in body,'one complete ordinary line and exact source registration required')
        case={'function':name,'prospective_mangled_name':'_Z'+str(len(name))+name+'v',
            'expected_source_range':[start,end], 'contract':{'ensures':r'\result == '+str(result),'assigns':r'\everything'},
            'predicted_verdict':verdict,'predicted_failure_rule':rule,'thread':0,
            'source_order_offsets':{'issue':start+issue,'CPU_access':start+access,'covering_wait':start+wait},
            'ordinary_allocation_request':{'source_name':'data','dtype':0,'extent':16,'bytes':64,
                'physical_alignment':64,'alignment_is_not_inferred_from_source':True,
                'requires_separately_owned_mapping':True},
            'expected_call_basis':'complete original 26-name/27-declaration interface; actual same-TU binding pending'}
        cases.append(case)
    return {'schema':'prospective-same-thread-original-source-profile-set-1','source':source_pin,
        'original_header_project':str(project),'headers':header_pins,'inventory':index_pin,
        'defines':['NUM_CORES=4','TILE_SIZE=16384'],'bounds':{'threads':1},'choice_budget':256,
        'capture_mode':'one complete original TU for all three callers; ABI probe separate with no declaration-ID joins',
        'cases':cases,'compiler_observed':False,'source_admission_granted':False,'receiver_context_granted':False,
        'old_fixed79_80_changed':False,'abstract25_reused_or_relabelled':False,
        'acceptance':'fresh public swdb prove: exact predicted verdict, no skip/frontend refusal, native agreement and reachability; both hazard failures must replay their exact rule on source-preserving C++ under new0.2 pins/assumptions'}
