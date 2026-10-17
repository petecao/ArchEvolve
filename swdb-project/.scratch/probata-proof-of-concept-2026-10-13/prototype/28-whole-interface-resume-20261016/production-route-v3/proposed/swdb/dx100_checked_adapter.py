"""Checked-only CBMC orchestration; legacy adapters keep their existing path.

Every launch freshly rebuilds the selected source/receiver/view. No metadata
boolean can skip these checks. This module is a source proposal, not an actual
evaluation result or a hardware-body refinement claim.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from swdb import c_lowering, cbmc_translator as tr, dx100_checked_source as source
from swdb import dx100_checked_native as native, proof_semantics

MANIFEST_ID = 'swdb-dx100-whole-checked-producers-1'


def method_check(adapter, unit, tools):
    source.need(adapter.method.id == source.METHOD, 'separate fresh checked-source method required')
    policy = json.loads(unit.policy_json)
    manifest = {'id': MANIFEST_ID, 'sha256': policy['producer_manifest']['sha256']}
    translators = (adapter.method.data.get('c_lowering') or {}).get('translators') or []
    source.need(translators.count(manifest) == 1, 'method does not pin this complete active producer manifest')
    selected = source.Inputs(unit.selection.library)
    receiver_policy = selected.document(policy['receiver_selection'])
    physical = receiver_policy['physical_inputs']
    wrapper, driver = physical['compiler_wrapper'], physical['compiler_driver']
    source.need(list(tools['clang'].command) == [wrapper['path']] and tools['clang'].version == '22.1.8',
        'actual absolute compiler command/version differs from owned selected runtime')
    selected.absolute(wrapper, retain=False); selected.absolute(driver, retain=False)
    from swdb import stdlib_provenance
    runtime = stdlib_provenance.runtime_identity(tools['clang'])
    source.need(runtime.get('command_executable') == {key:wrapper[key] for key in ('path','sha256')}
        and runtime.get('driver') == {key:driver[key] for key in ('path','sha256')},
        'actual compiler wrapper/underlying driver differs from receiver runtime')
    selected.recheck()
    return {'producer_manifest':manifest, 'compiler_runtime':runtime,
        'numeric_runtime_receipt_sha256':receiver_policy['inputs']['runtime_receipt']['sha256']}


def run(adapter, job, entry, context, source_path, selection):
    """One complete checked unit, retaining ordinary verifier/replay criteria."""
    from swdb import cbmc_adapter as base
    try:
        source.need(dict(job.bounds) == {'threads':1} and tuple(sorted(adapter.defines)) == source.DEFINES,
            'first no-parameter source fixture has exact threads=1 bounds and fixed constants')
        selection = source.SourceSelection(selection.library, selection.entry_id, selection.project, adapter.method.id)
        lowering = c_lowering.lower(source_path, job.unit.function, defines=adapter.defines, whole_source_selection=selection)
        unit = lowering.whole_source
        context['whole_source_unit'] = unit
        checked_method = method_check(adapter, unit, context['tools'])
        model = proof_semantics.model_for(adapter.library, selection.entry_id, adapter.defines, source_unit=unit)
        code = base.Code(lowering, source_path, adapter.defines, model)
        view = native.view(unit)
        header = context['out'] / 'dws_original_runtime.hpp'
        header.write_text(view['runtime_header'])
        context['reports'].append(('whole_source_runtime_header',header))
        context.update(lowering=lowering, model=model, whole_source_unit=unit, whole_source_code=code,
                       whole_source_native_view=view, whole_source_header=header, whole_source_method=checked_method)
        context['pins'] = {'c_lowering':{'id':lowering.function+'.c','sha256':code.c_sha256},
            'naming_rules':c_lowering.naming_rules(),
            'proof_semantics':{'id':model.entry,'sha256':model.sha256},
            'whole_source':{'id':source.KIND,'sha256':hashlib.sha256(unit.certificate_json).hexdigest()}}
        context['settings'].update(whole_source=unit.certificate, whole_source_method=checked_method,
            whole_source_native_identity=view['runtime_identity'], verifier_launched=False,
            proof_semantics={'id':model.entry,'calls':list(model.calls),
                'scope':'fixed actual-source scalar trace with owned complete compiler/MMIO/numeric premises',
                'hardware_refinement_proved':False,'precise_frame_projection':'unsupported'})
        built = adapter._build(job, entry, code, {}, job.unit.candidate is None, context)
        context['whole_source_built'] = built
        check_launch(adapter,job,context)
        problem = adapter._differential(job,code,built,context)
        if problem: return problem
        check_launch(adapter,job,context)
        result = adapter._cbmc(job,code,built,context)
        check_launch(adapter,job,context)
        return result
    except subprocess.TimeoutExpired as error:
        return adapter._not_proven('timeout','checked-source native/compiler probe exceeded its wall budget',context)
    except (source.Refused, native.projection.Refused, c_lowering.LoweringError, tr.Untranslatable,
            OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        context['settings']['whole_source_refusal'] = str(error)
        return adapter._not_proven('unsupported_construct',str(error),context)
    finally:
        if 'whole_source_unit' in context:
            try:
                source.recheck(context['whole_source_unit'])
                if 'whole_source_built' in context:
                    check_launch(adapter,job,context)
            except (source.Refused,native.projection.Refused,OSError,ValueError,TypeError,KeyError,AttributeError) as error:
                context['settings']['whole_source_post_input_refusal'] = str(error)
                return adapter._not_proven('unsupported_construct','post-run source/runtime closure refused: '+str(error),context)


def texts(context):
    unit, built, view = context['whole_source_unit'], context['whole_source_built'], context['whole_source_native_view']
    prefix = tr.prelude(whole_source=unit) + built['logic'] + unit.model_text
    return {'c':prefix + unit.source_text + built['harness'],
            'cxx':prefix + view['cxx_text'] + built['harness']}


def check_launch(adapter, job, context, inputs=()):
    unit = context['whole_source_unit']
    source.recheck(unit)
    source.need(method_check(adapter,unit,context['tools']) == context['whole_source_method'],
        'method/runtime changed after source planning')
    code = context['whole_source_code']
    expected_fields = source.lowering_fields(unit)
    source.need(all(getattr(context['lowering'],key) == value for key,value in expected_fields.items())
        and code.text == unit.source_text and code.model.c_text == unit.model_text,
        'generated source lowering/model changed after complete source admission')
    source.need(native.view(unit) == context['whole_source_native_view'], 'source-preserving native view changed')
    native.check_generated_header(unit,context['out'],context['whole_source_native_view']['runtime_header'])
    entry = adapter.library.get(adapter.contract)
    rebuilt = adapter._build(job,entry,code,{},job.unit.candidate is None,{'settings':{},'pins':{}})
    source.need(rebuilt == context['whole_source_built'], 'choice Plan/harness/formal properties changed')
    check_role_inputs(texts(context),inputs)
    return {'kind':source.KIND,'certificate_sha256':hashlib.sha256(unit.certificate_json).hexdigest(),
        'draw_plan_sha256':unit.certificate['draw_plan_sha256'],
        'native_view_sha256':source.digest(context['whole_source_native_view']['runtime_identity'])}


def check_role_inputs(expected, inputs):
    """The caller supplies a fixed role/path; only freshly generated bytes authorize it."""
    source.need(type(expected) is dict and set(expected) == {'c','cxx'} and expected['c'] != expected['cxx'],
        'distinct checked C and original-source C++ views required')
    for role,path in inputs:
        source.need(type(role) is str and role in expected, 'exact c/cxx generated-input role required')
        raw=expected[role].encode('utf-8')
        source.receiver.check_file(source.receiver.Pin(str(Path(path)),len(raw),hashlib.sha256(raw).hexdigest()))


def build(adapter, job, entry, code, context):
    unit = code.lowering.whole_source
    rows = [row for row in entry.get('clauses',[]) if isinstance(row,dict) and row.get('acsl')]
    selected = [row for row in rows if row.get('proof_placement') ==
        ({'once':'self'} if job.unit.candidate is None else 'per_candidate')]
    clauses = tr.clauses(adapter.contract,selected)
    source.unit_contract(adapter.library,unit,adapter.contract,job.unit.contract_sha256,clauses)
    source.need(not entry.get('knobs') and not (entry.get('proof_unit') or {}).get('array_domains'),
        'first source fixture has no generic knobs/windows or summary substitution')
    harness, plan = tr.harness(code.interface(job.unit.function),clauses,sizes={},cap=0,whole_source=unit)
    context['settings'].update(unwind=1,array_length=0,symbolic_knobs=[],summaries=[],
        whole_source_draws=plan.draws, source_loop_bound=1, helper_loop_bound=513)
    return {'harness':harness,'plan':plan,'stubs':{},'unwind':1,'sizes':{},'logic':''}


def compile_native(tools, side, path, binary, flags):
    """Keep the selected wrapper command intact; never infer a clang executable by renaming it."""
    standard = 'gnu11' if side == 'c' else 'gnu++17'
    language = 'c' if side == 'c' else 'c++'
    done = subprocess.run([*tools['clang'].command,'-x',language,'-std='+standard,*flags,str(path),'-o',str(binary)],
        capture_output=True,text=True,timeout=300)
    return None if done.returncode == 0 else done.stderr[-400:]


def run_fresh_domain(binary, lines):
    """A separate program per oracle row. Any crash/UB prevents agreement."""
    from swdb.cbmc_adapter import _Done
    rows=[]
    for index,line in enumerate(lines):
        done=subprocess.run([str(binary)],input=' '.join(map(str,line))+'\n',capture_output=True,text=True,
            timeout=60,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:abort_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
        output=done.stdout.splitlines()
        if done.returncode or len(output)!=1 or not re.fullmatch(r'run 0:.* end=(done|check|infeasible)',output[0]) or \
                re.search(r'AddressSanitizer|runtime error:',done.stderr):
            return _Done(done.returncode or 1,'\n'.join(rows)+'\n',done.stderr[-400:]),set()
        rows.append(re.sub(r'^run 0:',f'run {index}:',output[0]))
    return _Done(0,'\n'.join(rows)+'\n',''),set()


def model_loops(adapter, tools, scratch, unit, context):
    """Retain the actual opaque CBMC selectors; unknown loop owners refuse."""
    from swdb import cbmc_adapter as base
    check_launch(adapter,context['job'],context,[('c',Path(scratch)/'job.c')])
    done=subprocess.run([*tools['command'],'job.c','-DSWDB_CBMC',*base.FROZEN,
        *(flag for flag in tools['flags'] if flag not in base.FROZEN),'--show-loops'],cwd=scratch,
        capture_output=True,text=True,timeout=300)
    source.need(done.returncode==0,'actual CBMC loop inventory failed')
    path=context['out']/'whole-source-show-loops.txt';path.write_text(done.stdout)
    context['reports'].append(('whole_source_actual_loop_ids',path))
    stderr=context['out']/'whole-source-show-loops.stderr.txt';stderr.write_text(done.stderr)
    context['reports'].append(('whole_source_actual_loop_stderr',stderr))
    check_launch(adapter,context['job'],context,[('c',Path(scratch)/'job.c')])
    loops=re.findall(r'^Loop (\S+):',done.stdout,re.M)
    source.need(len(loops)==len(set(loops)),'duplicate actual CBMC loop IDs refused')
    helpers=set(source.model_fields(unit)['functions'])
    allowed=helpers|{source.FUNCTION,'dws_source_program','swdb_run','main','swdb_next','swdb_next_real'}
    source.need(all(loop.rsplit('.',1)[0] in allowed for loop in loops),'unclassified source/helper loop owner')
    return [loop for loop in loops if loop.rsplit('.',1)[0] in helpers]
