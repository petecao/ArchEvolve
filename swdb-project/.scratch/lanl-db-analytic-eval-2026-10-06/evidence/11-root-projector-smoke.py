#!/usr/bin/env python3
"""Compile and verify the read-only root projector with static LLVM22 fixtures.

Created: 2026-10-06 ET. No application binary is linked or executed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


def run(argv, **kwargs):
    return subprocess.run([str(a) for a in argv], check=True, capture_output=True, text=True, **kwargs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--llvm-bin', type=Path, required=True)
    p.add_argument('--output-directory', type=Path)
    p.add_argument('--gcc-install-dir', help='optional Linux Clang standard library selection')
    a = p.parse_args()
    here = Path(__file__).resolve().parent
    root = next(v for v in here.parents if (v/'swdb/llvm/Characterize.cpp').is_file())
    out = a.output_directory or Path(tempfile.mkdtemp(prefix='lanl-root-projector-smoke-'))
    out.mkdir(parents=True, exist_ok=True)
    llvm = a.llvm_bin
    version = run([llvm/'llvm-config', '--version']).stdout.strip()
    assert version.split('.')[0] == '22', version
    flags = shlex.split(run([llvm/'llvm-config', '--cxxflags', '--ldflags', '--system-libs',
                            '--libs', 'core', 'irreader', 'analysis', 'passes', 'support']).stdout)
    compiler = [llvm/'clang++']
    if a.gcc_install_dir:
        compiler += ['--gcc-install-dir='+a.gcc_install_dir]
    probe = out/'root-projector'
    plugin = out/('Characterize.dylib' if sys.platform == 'darwin' else 'Characterize.so')
    run([*compiler, here/'11-normalized-root-projector.cpp', *flags, '-std=c++17', '-O2', '-o', probe])
    run([*compiler, '-fPIC', '-shared', root/'swdb/llvm/Characterize.cpp', *flags, '-std=c++17', '-O2', '-o', plugin])
    receipt = {'date':'2026-10-06 ET', 'scope':'static compiler fixtures; no application execution or empirical counts/timings',
               'llvm_version':version, 'projector_sha256':hashlib.sha256((here/'11-normalized-root-projector.cpp').read_bytes()).hexdigest(),
               'fixtures':[], 'negative_checks':{}}
    for level in ('O0','O1'):
        raw, norm, mapping, projection = (out/(level+suffix) for suffix in ('.raw.bc','.normalized.bc','.source.json','.projection.json'))
        args = ['-std=c++17','-g','-'+level]
        if level == 'O0':
            args += ['-Xclang','-disable-O0-optnone']
        run([*compiler, *args, '-emit-llvm', '-c', here/'11-root-projector-fixture.cc', '-o', raw])
        run([llvm/'opt', '-passes=function(sroa,mem2reg),cgscc(inline),function(loop-simplify)', raw, '-o', norm])
        env = dict(os.environ, SWDB_ANALYSIS_OUTPUT=str(mapping), SWDB_COUNT_FUNCTION='', SWDB_INSTRUMENT='0')
        env.pop('SWDB_REGION_MAP',None)
        run([llvm/'opt','--load-pass-plugin='+str(plugin),'-passes=swdb-characterize',norm,'-disable-output'],env=env)
        d = json.loads(mapping.read_text())
        sites = ','.join(str(v['site']) for v in d['accesses'])
        calls = ','.join(str(v['site']) for v in d['unmodeled_calls'])
        argv = [probe,norm,mapping,projection,sites,calls]
        before = hashlib.sha256(norm.read_bytes()).hexdigest()
        run(argv)
        q = json.loads(projection.read_text())
        assert q['normalized_ir_sha256'] == before == hashlib.sha256(norm.read_bytes()).hexdigest()
        assert q['source_json_sha256'] == hashlib.sha256(mapping.read_bytes()).hexdigest()
        assert q['enumerated_access_sites'] == len(d['accesses'])
        assert q['enumerated_call_sites'] == len(d['unmodeled_calls'])
        roots = q['roots']; classes = {v['root_class'] for v in roots}
        assert {'alloca','argument','global_definition','global_declaration','loaded_pointer'} <= classes
        assert any(v.get('extent_status') == 'dynamic_or_scalable' and v['constant_extent_bytes'] is None for v in roots)
        assert all(v['constant_extent_bytes'] is None for v in roots if v['root_class']=='global_declaration')
        assert any(v.get('abi_typed_referent_bytes')==4 and v.get('caller_producers') for v in roots)
        assert any(v.get('constant_extent_bytes')==12 for v in roots if v['root_class']=='alloca')
        assert all('address_expression' not in v for v in q['accesses'])
        if level == 'O0':
            assert any(v.get('constant_length_bytes')==8 for v in q['calls'])
            assert any(v.get('length_kind')=='runtime_value' for v in q['calls'] if v['name'].startswith('llvm.mem'))
        else:
            assert 'call_result' in classes
            assert any(v.get('lifetime_markers',{}).get('start_sites',0)>0 for v in roots)
            assert any(v.get('constant_length_bytes')==16 and v['static_alias_result']=='PartialAlias' for v in q['calls'])
        receipt['fixtures'].append({'optimization':level,'access_sites_cross_checked':len(d['accesses']),
          'call_sites_cross_checked':len(d['unmodeled_calls']),'root_classes':sorted(classes),
          'input_ir_unchanged':True,'extent_lifetime_caller_abi_bulk_contracts_checked':True})
        if level == 'O1':
            bad = out/'mismatched.source.json';d['accesses'][0]['line'] += 1;bad.write_text(json.dumps(d))
            bad_out = out/'refused.json'
            changed = subprocess.run([probe,norm,bad,bad_out,sites,calls],capture_output=True,text=True)
            assert changed.returncode==2 and 'access map mismatch at0' in changed.stderr.replace('at ','at')
            assert not bad_out.exists()
            missing = subprocess.run([probe,norm,mapping,bad_out,'999999',calls],capture_output=True,text=True)
            assert missing.returncode==2 and 'requested-site mismatch' in missing.stderr and not bad_out.exists()
            receipt['negative_checks']={'changed_source_map_exit':changed.returncode,'missing_requested_site_exit':missing.returncode,
                                        'no_refused_output_written':True}
    (out/'local-proof.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'proof':str(out/'local-proof.json'),'fixtures':receipt['fixtures'],'negative_checks':receipt['negative_checks']},indent=2))


if __name__=='__main__':
    main()
