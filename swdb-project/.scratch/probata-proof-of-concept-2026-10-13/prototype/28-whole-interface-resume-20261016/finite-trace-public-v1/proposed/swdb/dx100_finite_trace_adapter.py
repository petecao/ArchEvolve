"""2026-10-16 ET. Public finite-model proof/replay branch; no original-C++ claim.

Each prospective launch repeats physical Library/model/receiver/draw/runtime
checks. This source proposal grants no execution admission.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time

from swdb import c_lowering, cbmc_translator as tr, dx100_finite_trace as source, proof_semantics, proof_setup, rss_watchdog, stdlib_provenance
from swdb._dx100_finite import finite_checks_v1 as checks


def method_check(adapter,unit,tools):
    source.need(adapter.method.id==source.METHOD and not adapter.defines,'exact finite method without build overrides required')
    row=dict(id=source.MANIFEST,sha256=unit.certificate['producer_manifest']['sha256'])
    source.need(((adapter.method.data.get('c_lowering') or {}).get('translators') or []).count(row)==1,'finite method must pin its complete producer manifest')
    selected=unit.certificate['runtime'];wrapper=selected['compiler_wrapper'];driver=selected['compiler_driver']
    source.need(list(tools['clang'].command)==[wrapper['path']] and tools['clang'].version=='22.1.8','selected absolute LLVM22 compiler differs')
    actual=stdlib_provenance.runtime_identity(tools['clang'])
    source.need(actual.get('command_executable')=={key:wrapper[key] for key in ('path','sha256')} and actual.get('driver')=={key:driver[key] for key in ('path','sha256')},'actual compiler physical identity differs')
    for pin in selected.values():source.opaque_pin(pin)
    return dict(producers=row,compiler=actual,numeric_runtime_receipt_sha256=selected['numeric_runtime_receipt']['sha256'])


def texts(unit):
    prelude=tr.prelude()
    marker='static long long swdb_next(void) {\n  SWDB_CHECK'
    source.need(prelude.count(marker)==1,'exact translator prelude insertion seam required')
    prelude=prelude.replace(marker,checks.native_override()+marker)
    return prelude+unit.model_text+unit.source_text+checks.harness(source.strict(unit.profile_json)['draw_count'])


def plan(unit):
    rows=source.strict(unit.draw_rows_json)
    source.need(all(row==dict(name='finite_choice_'+str(i),role='finite-model-choice',ctype='uint32_t',c_lvalue='dws_choice_table[%d]'%i) for i,row in enumerate(rows)),'ordered exact independent full-u32 Plan required')
    return tr.Plan(draws=rows,capacity=len(rows))


def check_launch(adapter,job,context,inputs=()):
    unit=context['finite_trace_unit'];source.recheck(unit)
    source.need(method_check(adapter,unit,context['tools'])==context['finite_method'],'finite method/runtime changed')
    source.need(context['model'].c_text==unit.model_text and context['lowering'].text==unit.source_text and context['finite_plan']==plan(unit),'finite model/lowering/Plan digest changed')
    expected=texts(unit).encode()
    for path in inputs:
        path=Path(path);before=path.lstat()
        source.need(path.resolve(strict=True)==path and path.is_file() and before.st_size==len(expected),'generated finite input topology/extent differs')
        with path.open('rb') as stream:raw=stream.read(len(expected)+1)
        source.need(source.receiver.stable(path.lstat())==source.receiver.stable(before) and raw==expected,'generated finite role bytes differ')
    return dict(kind=source.KIND,certificate_sha256=source.sha(unit.certificate_json),generated_sha256=source.sha(expected),model_digest=unit.certificate['model_digest'])

def check_command(context,command):
    """Closed phase role; native invocations never borrow a CBMC command label."""
    from swdb import cbmc_adapter as base
    phase=context['finite_phase'];tools=context['tools'];scratch=Path(context['job'].scratch)
    native=scratch/'finite-native';cfile=scratch/'job.c'
    if phase=='finite-native-compile':
        expected=[*tools['clang'].command,'-x','c','-std=c11','-DSWDB_NATIVE','-O0','-g',*base.SANITIZERS,str(cfile),'-o',str(native)]
    elif re.fullmatch(r'finite-(?:sample|replay)-[0-9]+',phase):
        expected=[str(native)]
        source.need(base._sha256(native)==context['finite_native_sha256'],'exact compiled finite binary required')
    elif phase=='finite-show-loops':
        expected=[*tools['command'],'job.c','-DSWDB_CBMC',*base.FROZEN,*(flag for flag in tools['flags'] if flag not in base.FROZEN),'--show-loops']
        proof_setup.check_cbmc_flags(expected)
    else:
        source.need(phase=='finite-cbmc','unknown finite compiler/native/verifier phase')
        expected=[*tools['command'],'job.c',*context['finite_flags'],'--json-ui']
        proof_setup.check_cbmc_flags(expected)
    source.need(list(command)==expected,'actual finite phase command/role differs')
    return dict(phase=phase,command_sha256=source.sha(source.canonical(expected)))


def prepared_context(adapter,job,selection,context):
    unit=source.compose(selection)
    source.need(job.unit.function==source.FUNCTION and job.unit.contract==selection.contract_id and job.unit.contract_sha256==selection.contract_sha256,'job finite contract/function/digest differs')
    source.need(dict(job.bounds)=={'threads':1} and not job.summaries,'fixed sequential thread-tag order; no arbitrary summaries/bounds')
    lowering=c_lowering.Lowering(**source.lowering_fields(unit))
    model=proof_semantics.model_for(adapter.library,selection.entry_id,source_unit=unit)
    context.update(finite_trace_unit=unit,lowering=lowering,model=model,finite_plan=plan(unit),finite_method=method_check(adapter,unit,context['tools']))
    context['pins']=dict(c_lowering=dict(id=unit.function+'.c',sha256=source.sha(unit.source_text.encode())),proof_semantics=dict(id=model.entry,sha256=model.sha256),finite_trace=dict(id=source.KIND,sha256=source.sha(unit.certificate_json)))
    context['settings'].update(finite_trace=unit.certificate,finite_resource_profile=source.strict(unit.profile_json),finite_draws=context['finite_plan'].draws,
        forms={'finite_concrete_model':'pending actual CBMC/native replay','original_cpp':'not a SourceUnit; no correspondence claim'},
        scope='fixed finite sequential model events with literal software thread tags; no interleaving, fairness or hardware-body theorem',verifier_launched=False)
    return unit


def finish(adapter,verdict,context,*,failure_class=None,why='',counterexample=None,unreplayed=None):
    from swdb import cbmc_adapter as base
    from swdb.proof import Verdict
    if context.get('finite_trace_unit') is not None:check_launch(adapter,context['job'],context)
    assumptions=[];tools=[]
    for name in ('c_lowering','clang','translator','cbmc','solver'):
        ident,digest,version=context['tools']['identities'][name]
        assumptions.append(dict(kind='trusted_tool',reference=dict(id=ident,sha256=digest),sentence=base.SENTENCES[name].format(version=version)));tools.append(ident)
    unit=context.get('finite_trace_unit')
    if unit is not None:assumptions+=source.record_assumptions(unit)
    context['settings']['finite_outcome_reason']=why
    if verdict=='not_proven':adapter._handler(failure_class,why,context)
    context['settings']['forms']['finite_concrete_model']=verdict
    fields=dict(goals=context.get('goals',[]),settings=context['settings'])
    if verdict=='not_proven':fields['unproven_properties']=context.get('unproven',[])
    pins=dict(context.get('pins') or {});pins['translator']={key:context['tools']['translator'][key] for key in ('id','sha256')}
    return Verdict(verdict=verdict,bounds=dict(context['bounds']),assumptions=assumptions,failure_class=failure_class,counterexample=counterexample,
        unreplayed_counterexample=unreplayed,tools=tuple(tools),peak_rss_bytes=context.get('peak'),record_fields=fields,pins=pins,reports=tuple(context['reports']))


def run(adapter,job,entry,context,selection):
    from swdb import cbmc_adapter as base
    started=time.monotonic();cap=int(os.environ.get('SWDB_VERIFIER_RSS_CAP_BYTES') or base.DEFAULT_CAP_BYTES)
    def remaining():
        value=(job.budget_seconds or base.DEFAULT_WALL_SECONDS)-(time.monotonic()-started)
        source.need(value>0,'finite whole-job wall budget exhausted');return value
    def launch(label,command,inputs=(),stdin=None,native=False):
        context['finite_phase']=label
        check_launch(adapter,job,context,inputs)
        flags=context.get('finite_flags',[])
        proof_setup.check_generated(job,adapter,context,[(path,texts(context['finite_trace_unit'])) for path in inputs],flags,
            command=command,scratch=Path(job.scratch),lowering=context['lowering'])
        path=context['out']/(label+'.log');context['reports'].append((label,path))
        env={**os.environ,'TMPDIR':str(job.scratch)}
        if native:env.update(ASAN_OPTIONS='detect_leaks=0:abort_on_error=1',UBSAN_OPTIONS='halt_on_error=1')
        done=rss_watchdog.run(command,log=path,cap_bytes=cap,timeout=remaining(),cwd=job.scratch,env=env,stdin=stdin)
        context['peak']=max(context.get('peak',0),done.peak_rss_bytes)
        check_launch(adapter,job,context,inputs)
        source.need(not done.out_of_memory and not done.timed_out,'guarded finite phase exceeded resources')
        return done,path
    try:
        unit=prepared_context(adapter,job,selection,context)
        context['settings']['flags']=[]
        text=texts(unit);source_path=Path(job.scratch)/'job.c';source_path.write_text(text)
        retained=context['out']/'finite-job.c';retained.write_text(text);context['reports'].append(('cbmc_input',retained))
        flags=['-DSWDB_CBMC','--unwind','513',*base.FROZEN,*(flag for flag in context['tools']['flags'] if flag not in base.FROZEN)]
        proof_setup.check_cbmc_flags(flags);context['finite_flags']=flags
        binary=Path(job.scratch)/'finite-native'
        command=[*context['tools']['clang'].command,'-x','c','-std=c11','-DSWDB_NATIVE','-O0','-g',*base.SANITIZERS,str(source_path),'-o',str(binary)]
        done,path=launch('finite-native-compile',command,[source_path]);source.need(done.exit_code==0,'sanitized finite native compilation failed')
        binary_sha=base._sha256(binary);context['finite_native_sha256']=binary_sha
        count=len(context['finite_plan'].draws)
        def native(values,label):
            source.need(len(values)==count and all(type(x) is int and -(2**63)<=x<2**63 for x in values),'exact signed64 native oracle row required')
            source.need(base._sha256(binary)==binary_sha,'native binary changed after compilation')
            given=context['out']/(label+'-input.txt');given.write_text(' '.join(map(str,values))+'\n');context['reports'].append((label+'_input',given))
            with given.open() as stream:done,path=launch(label,[str(binary)],[source_path],stream,True)
            source.need(done.exit_code==0,'finite native process crashed');output=path.read_text();row=checks.native_row(output,count)
            source.need(row['inputs']==[x%(2**32) for x in values],'native receiver consumed different oracle values')
            source.need(base._sha256(binary)==binary_sha,'native binary changed while replaying')
            return row,source.sha(output.encode())
        corners=[[0]*count,[1]*count,[2**32-1]*count,[i%2 for i in range(count)]];observations=[]
        for i,values in enumerate(corners):
            row,digest=native(values,'finite-sample-'+str(i));observations.append(dict(output_sha256=digest,**row))
        context['settings']['finite_native_samples']=observations
        done,path=launch('finite-show-loops',[*context['tools']['command'],'job.c','-DSWDB_CBMC',*base.FROZEN,*(flag for flag in context['tools']['flags'] if flag not in base.FROZEN),'--show-loops'],[source_path])
        source.need(done.exit_code==0,'actual finite loop inventory failed')
        loops=re.findall(r'^Loop (\S+):',path.read_text(),re.M)
        rows=checks.loop_bounds(source.strict(unit.profile_json),loops,source.model_fields(unit)['functions'])
        flags+=['--unwindset',','.join(row['loop']+':'+str(row['unwind']) for row in rows)]
        context['finite_flags']=flags;context['settings'].update(flags=flags,finite_actual_loop_bounds=rows,verifier_launched=True)
        done,path=launch('finite-cbmc',[*context['tools']['command'],'job.c',*flags,'--json-ui'],[source_path])
        outcome=checks.read_outcome(done,path.read_text(),count,source.model_fields(unit)['functions']);context['goals']=outcome['goals']
        if outcome['verdict']=='proven':return finish(adapter,'proven',context,why=outcome['why'])
        if outcome['verdict']=='not_proven':return finish(adapter,'not_proven',context,failure_class=outcome['failure_class'],why=outcome['why'])
        attempts=[]
        for i,failure in enumerate(outcome['failures']):
            row,digest=native(failure['oracle'],'finite-replay-'+str(i))
            replayed=row['failed']==[failure['property']]
            counterexample=dict(**failure,inputs={name['name']:value for name,value in zip(context['finite_plan'].draws,row['inputs'])},
                replay=dict(form='finite_concrete_model_c',replayed=replayed,failed=row['failed'],end=row['end'],output_sha256=digest,original_cpp_equivalence=False))
            attempts.append(counterexample)
            if replayed:return finish(adapter,'refuted',context,why='actual CBMC property replayed on exact sanitized abstract model',counterexample=counterexample)
        return finish(adapter,'not_proven',context,failure_class='spurious_counterexample',why='no finite-model witness replayed its exact failed property',unreplayed=attempts[0])
    except (source.Refused,checks.Refused,OSError,ValueError,TypeError,KeyError,AttributeError,RuntimeError) as error:
        context['settings'].setdefault('forms',{'finite_concrete_model':'not_proven','original_cpp':'not a SourceUnit'})
        # A failed final physical closure cannot adopt any prior result.
        try:return finish(adapter,'not_proven',context,failure_class='unsupported_construct',why=str(error))
        except (source.Refused,OSError,ValueError,TypeError,KeyError,AttributeError) as final:
            raise base.AdapterError('final finite input closure refused; no verdict adopted: '+str(final)) from None
