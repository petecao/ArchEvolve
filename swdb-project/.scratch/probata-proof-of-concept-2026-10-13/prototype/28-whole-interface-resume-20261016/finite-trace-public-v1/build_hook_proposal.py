"""2026-10-16 ET. Exact-base hook proposal; writes only this owned proposal."""
from pathlib import Path
import difflib
import hashlib
import json

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'production-route-v4/proposed/swdb'
TARGET=HERE/'proposed/swdb'

def build():
    edits={
      'cbmc_adapter.py':[(
'''        if summary_job:
            source = self.library.resolve((entry.get("proof_unit") or {}).get("source"))''',
'''        from swdb import dx100_finite_trace, dx100_finite_trace_adapter
        finite_selection = dx100_finite_trace.select_baseline(self.library,self.contract,entry)
        if finite_selection is not None:
            return dx100_finite_trace_adapter.run(self,job,entry,context,finite_selection)
        if summary_job:
            source = self.library.resolve((entry.get("proof_unit") or {}).get("source"))''')],
      'formal_frame.py':[(
'''    from swdb import dx100_checked_source
    whole_format = dx100_checked_source.checked_unit_format(library,entry_id,data)''',
'''    from swdb import dx100_checked_source, dx100_finite_trace
    whole_format = dx100_finite_trace.checked_unit_format(library,entry_id,data)
    if whole_format is None:
        whole_format = dx100_checked_source.checked_unit_format(library,entry_id,data)'''),(
'''    path = library.resolve(unit['source'])
    from swdb import dx100_checked_source''',
'''    from swdb import dx100_finite_trace
    try:
        finite = dx100_finite_trace.lowering_for(library,unit)
        if finite is not None:
            return finite
    except (ValueError,OSError,TypeError,KeyError,AttributeError) as exc:
        return c_lowering.LoweringError(str(exc))
    path = library.resolve(unit['source'])
    from swdb import dx100_checked_source''')],
      'proof_semantics.py':[(
'''        dx100_whole_checked.policy(library, data)
        dx100_checked_source.recheck(source_unit)''',
'''        dx100_whole_checked.policy(library, data)
        from swdb import dx100_finite_trace
        if type(source_unit) is dx100_finite_trace.TraceUnit:
            dx100_finite_trace.recheck(source_unit)
            return Model(**dx100_finite_trace.model_fields(source_unit))
        dx100_checked_source.recheck(source_unit)''')],
      'proof_setup.py':[(
'''    # Scan the actual translation units of both sides; scripted fixtures have no''',
'''    finite_selection = None
    if library is not None and job.unit.contract:
        from swdb import dx100_finite_trace
        finite_selection = dx100_finite_trace.select_baseline(library,job.unit.contract,library.get(job.unit.contract))
        if finite_selection is not None:
            finite = dx100_finite_trace.compose(finite_selection)
            report['hashes']['finite_trace'] = _sha(finite.certificate_json)
            job.setup['finite_trace_certificate_sha256'] = _sha(finite.certificate_json)
            for row in finite.input_pins:
                if row['bytes'] <= 8*1024*1024:
                    job.setup['files'][row['path']] = row['sha256']
    # Scan the actual translation units of both sides; scripted fixtures have no'''),(
'''    if library is not None and not str(job.unit.contract or "").startswith("c_model."):
        from swdb.wp_adapter import _unit_source''',
'''    if library is not None and finite_selection is None and not str(job.unit.contract or "").startswith("c_model."):
        from swdb.wp_adapter import _unit_source'''),(
'''        if context.get('whole_source_unit') is not None:
            from swdb import dx100_checked_adapter''',
'''        if context.get('finite_trace_unit') is not None:
            from swdb import dx100_finite_trace_adapter
            try:
                hashes['finite_trace'] = dx100_finite_trace_adapter.check_launch(adapter,job,context,[path for path,_ in inputs])
                if job.setup.get('finite_trace_certificate_sha256') != _sha(context['finite_trace_unit'].certificate_json):
                    _fail('finite_trace','selected finite certificate differs from startup')
            except (ValueError,OSError,TypeError,KeyError,AttributeError) as exc:
                _fail('finite_trace',str(exc))
        elif context.get('whole_source_unit') is not None:
            from swdb import dx100_checked_adapter'''),(
'''    elif adapter.name == "cbmc":
        check_cbmc_flags(list(command) if command else flags)''',
'''    elif adapter.name == "cbmc":
        if context.get('finite_trace_unit') is not None:
            from swdb import dx100_finite_trace_adapter
            hashes['finite_phase'] = dx100_finite_trace_adapter.check_command(context,command)
            check_cbmc_flags(flags)
        else:
            check_cbmc_flags(list(command) if command else flags)''')]
    }
    output=[];inverse={}
    for name,rows in edits.items():
        original=(BASE/name).read_text();text=original
        for before,after in rows:
            assert text.count(before)==1,(name,before)
            text=text.replace(before,after)
        restored=text
        for before,after in reversed(rows):
            assert restored.count(after)==1;restored=restored.replace(after,before)
        assert restored==original
        (TARGET/name).write_text(text)
        output.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/swdb/'+name,tofile='b/swdb/'+name))
        inverse[name]=dict(base_sha256=hashlib.sha256(original.encode()).hexdigest(),proposed_sha256=hashlib.sha256(text.encode()).hexdigest(),edits=[dict(before=a,after=b) for a,b in rows],byte_exact_inverse=True)
    (HERE/'finite-hooks.patch').write_text(''.join(output))
    (HERE/'hook-inverse.json').write_text(json.dumps(dict(date='2026-10-16 ET',base='frozen production-route-v4',files=inverse),sort_keys=True,indent=2)+'\n')
    return inverse
if __name__=='__main__':print(json.dumps(dict(files=len(build()),execution=False)))
