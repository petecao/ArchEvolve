"""Source-only 2026-10-16 ET proposal; never writes shared production files.

Capture each physical base once, then require its exact bytes on subsequent
builds. The inverse delta is emitted for independent review. No imports from
the project, compiler calls, native calls, or subprocesses occur here.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRODUCTION = HERE.parents[4] / 'swdb'
EDITS = []


def sha(raw): return hashlib.sha256(raw).hexdigest()


def replace(text, old, new):
    assert text.count(old) == 1, old[:100]
    EDITS.append({'old':old, 'new':new, 'count':1})
    return text.replace(old, new, 1)


def lowering(text):
    text = replace(text,
        '    vector_reallocation_candidate: dict = field(default_factory=dict)',
        '    whole_source: object | None = None  # exact checked source unit, freshly revalidated\n'
        '    vector_reallocation_candidate: dict = field(default_factory=dict)')
    text = replace(text, '        if self.summaries:\n',
        '        if self.whole_source is not None:\n'
        '            data["whole_source"] = self.whole_source.certificate\n'
        '        if self.summaries:\n')
    text = replace(text, '          array_domains=None, array_domain_contract=None):',
        '          array_domains=None, array_domain_contract=None, whole_source_selection=None):')
    start = text.index('def lower(')
    position = text.index('    tool = locate()\n', start)
    branch = '''    if whole_source_selection is not None:
        from swdb import dx100_checked_source
        if includes or summaries or semantics or array_domains or array_domain_contract:
            raise Unsupported('checked whole source cannot mix generic summary/window inputs')
        try:
            unit = dx100_checked_source.compose(whole_source_selection, source=source,
                                               function=function, defines=defines)
            return Lowering(**dx100_checked_source.lowering_fields(unit))
        except (dx100_checked_source.Refused, ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
            raise Unsupported('checked whole source: ' + str(exc)) from None
'''
    tail = replace(text[position:], '    tool = locate()\n', branch + '    tool = locate()\n')
    return text[:position] + tail


def translator(text):
    text = replace(text, 'def prelude():\n    return PRELUDE.replace("@TOOL@", f"{TOOL_ID} {TOOL_VERSION}").replace("@CAPACITY@", ORACLE_CAPACITY)',
        '''def prelude(whole_source=None):
    text = PRELUDE.replace("@TOOL@", f"{TOOL_ID} {TOOL_VERSION}").replace("@CAPACITY@", ORACLE_CAPACITY)
    if whole_source is not None:
        from swdb import dx100_checked_source
        text = dx100_checked_source.native_prelude(whole_source, text)
    return text''')
    text = replace(text, '            state=(), finish=(), array_domains=None):',
        '            state=(), finish=(), array_domains=None, whole_source=None):')
    text = replace(text, '    for name in sizes:\n        if not interface.scalar(name):',
        '''    profile = None
    if whole_source is not None:
        from swdb import dx100_checked_source
        if call is not None or check or cap != 0:
            raise Untranslatable('checked whole source requires its original scalar proof interface')
        try:
            profile = dx100_checked_source.harness_profile(whole_source, interface, rows,
                sizes, knobs, setup, state, finish, array_domains)
        except (dx100_checked_source.Refused, ValueError, TypeError, KeyError) as exc:
            raise Untranslatable(str(exc)) from None
        setup = profile['setup']
    for name in sizes:
        if not interface.scalar(name):''')
    text = replace(text, '    lines += [f"  {statement}" for statement in setup]\n',
        '    lines += [f"  {statement}" for statement in setup]\n'
        '    if profile is not None:\n'
        '        plan.draws.extend(profile["draws"])  # setup already drew each slot exactly once\n')
    text = replace(text, '        else:\n            lines.append(f"  {_print(\'input \' + draw[\'name\'], draw[\'ctype\'], draw[\'name\'])};")',
        '        elif profile is not None and draw["role"] == "whole-model-choice":\n'
        '            lines.append(f"  {_print(\'input \' + draw[\'name\'], draw[\'ctype\'], draw[\'c_lvalue\'])};")\n'
        '        else:\n            lines.append(f"  {_print(\'input \' + draw[\'name\'], draw[\'ctype\'], draw[\'name\'])};")')
    text = replace(text, '            lines.append(f\'  SWDB_PROP({_frame(clause, interface, cap, caps, counter, logic)}, "{clause.name}");\')',
        '            frame = "1" if profile is not None else _frame(clause, interface, cap, caps, counter, logic)\n'
        '            lines.append(f\'  SWDB_PROP({frame}, "{clause.name}");\')')
    text = replace(text, '        "    fflush(stdout);",\n        "  }",',
        '        "    fflush(stdout);",\n'
        '        *(("    if (fgets(swdb_line, sizeof swdb_line, stdin)) return 3;", "    return 0;") if profile is not None else ()),\n'
        '        "  }",')
    return text


def semantics(text):
    text = replace(text, '    rules = {r.get("id") for r in data.get("rules") or [] if isinstance(r, dict)}',
        '    from swdb import dx100_whole_checked\n'
        '    if dx100_whole_checked.checked(data):\n'
        '        return dx100_whole_checked.check(library, data, error)\n'
        '    rules = {r.get("id") for r in data.get("rules") or [] if isinstance(r, dict)}')
    text = replace(text, 'def model_for(library, entry_id, defines=()):',
        'def model_for(library, entry_id, defines=(), *, source_unit=None):')
    start = text.index('def model_for(')
    at = text.index('    constants = _constants(data, defines)\n', start)
    branch = '''    from swdb import dx100_whole_checked, dx100_checked_source
    if dx100_whole_checked.checked(data):
        if source_unit is None or source_unit.selection.entry_id != entry_id:
            raise ValueError('whole checked model requires its exact complete source/receiver unit')
        dx100_whole_checked.policy(library, data)
        dx100_checked_source.recheck(source_unit)
        return Model(**dx100_checked_source.model_fields(source_unit))
    if source_unit is not None:
        raise ValueError('a checked whole source unit cannot select a legacy model')
'''
    prefix = text[start:at]
    text = replace(text, prefix + '    constants = _constants(data, defines)\n',
                   prefix + branch + '    constants = _constants(data, defines)\n')
    old = '    for entry in current(library):\n        model = model_for(library, entry, defines)'
    assert text.count(old) == 2
    new = (
        '    from swdb import dx100_whole_checked\n'
        '    for entry in current(library):\n'
        '        if dx100_whole_checked.checked(library.get(entry)):\n'
        '            continue  # whole units gain no generic per-call or pointer exemptions\n'
        '        model = model_for(library, entry, defines)')
    EDITS.append({'old':old, 'new':new, 'count':2})
    text = text.replace(old,new)
    helper = '''def _require_summary_form(data):
    from swdb import dx100_whole_checked
    if dx100_whole_checked.checked(data):
        from swdb.proof import AdapterError
        raise AdapterError("whole-interface checked bodies have no WP/ACSL summary form")


'''
    text = replace(text,'def acsl_source(data, texts, rows=None, *, constants=None):',
        helper + 'def acsl_source(data, texts, rows=None, *, constants=None):')
    text = replace(text,'    parts = [f"#define {name} {value}" for name, value in (data.get("constants") or {}).items()]',
        '    _require_summary_form(data)\n    parts = [f"#define {name} {value}" for name, value in (data.get("constants") or {}).items()]')
    for name in ('wp_prelude','wp_locations'):
        start = text.index('def '+name+'(')
        at = text.index('    data = library.get(entry_id)\n',start)
        prefix=text[start:at]
        text=replace(text,prefix+'    data = library.get(entry_id)\n',prefix+'    data = library.get(entry_id)\n    _require_summary_form(data)\n')
    text=replace(text,'    covered = covered_names(library)\n    if not covered:',
        '    from swdb import dx100_whole_checked\n    covered = covered_names(library)\n    if not covered:')
    text=replace(text,'for row in data.get("calls", []) if row.get("supported") is False}}',
        'for row in data.get("calls", []) if row.get("supported") is False or dx100_whole_checked.checked(data)}}')
    return text


def adapter(text):
    text=replace(text,'        covered = proof_semantics.covered_names(self.library)',
        '''        from swdb import dx100_checked_source, dx100_checked_adapter
        selected_whole = dx100_checked_source.select_baseline(self.library, entry.get('proof_unit') or {})
        if selected_whole is not None:
            return dx100_checked_adapter.run(self,job,entry,context,source,selected_whole)
        covered = proof_semantics.covered_names(self.library)''')
    text=replace(text,"        trace_plan = context.get('synthetic_trace_source_plan')",
        '''        if 'whole_source_unit' in context:
            from swdb import dx100_checked_adapter
            if inputs and any(Path(path) != Path(job.scratch) / 'job.c' for path,_ in inputs):
                raise AdapterError('whole checked CBMC callback requires its exact job.c input')
            dx100_checked_adapter.check_launch(self,job,context,[('c',path) for path,_ in inputs])
            return
        trace_plan = context.get('synthetic_trace_source_plan')''')
    text=replace(text,'        unit = code.interface(job.unit.function)',
        '''        if code.lowering.whole_source is not None:
            from swdb import dx100_checked_adapter
            if sizes:
                raise AdapterError('whole checked source has no size parameter')
            return dx100_checked_adapter.build(self,job,entry,code,context)
        unit = code.interface(job.unit.function)''')
    old='tr.prelude() + built["logic"]'
    new='tr.prelude(whole_source=code.lowering.whole_source) + built["logic"]'
    assert text.count(old)==4
    EDITS.append({'old':old,'new':new,'count':4});text=text.replace(old,new)
    text=replace(text,'        heap = code.lowering.allocation           # ticket 25:',
        '        whole = code.lowering.whole_source is not None\n'
        '        heap = code.lowering.allocation           # ticket 25:')
    old='''            problem = _compile(context["tools"]["clang"], side, paths_[side], binary,
                               ["-DSWDB_NATIVE", "-DSWDB_DIFFERENTIAL", "-O0", "-fwrapv", "-w",
                                *(("-fsanitize=address",) if heap else ()),
                                *(code.cxx_defines() if side == "cxx" else ())])'''
    new='''            if whole:
                from swdb import dx100_checked_adapter
                dx100_checked_adapter.check_launch(self,job,context,[(side,paths_[side])])
                problem = dx100_checked_adapter.compile_native(context['tools'],side,paths_[side],binary,
                    ['-DSWDB_NATIVE','-DSWDB_DIFFERENTIAL','-O0','-w',*SANITIZERS,*code.cxx_defines()])
            else:
'''+'\n'.join('    '+line for line in old.splitlines())
    text=replace(text,old,new)
    text=replace(text,'            done, crashed = _run_domain(binary, lines, sanitized=heap)',
        '''            if whole:
                dx100_checked_adapter.check_launch(self,job,context)
                done, crashed = dx100_checked_adapter.run_fresh_domain(binary,lines)
                dx100_checked_adapter.check_launch(self,job,context)
            else:
                done, crashed = _run_domain(binary, lines, sanitized=heap)''')
    text=replace(text,'            loops = self._model_loops(tools, scratch, code.model)',
        '''            if code.lowering.whole_source is not None:
                from swdb import dx100_checked_adapter
                loops = dx100_checked_adapter.model_loops(self,tools,scratch,code.lowering.whole_source,context)
            else:
                loops = self._model_loops(tools, scratch, code.model)''')
    old='''        problem = _compile(context["tools"]["clang"], "cxx", replay_cc, binary,
                           ["-DSWDB_NATIVE", "-DSWDB_REPLAY", "-O0", "-g", "-w", *SANITIZERS, *code.cxx_defines()])'''
    text=replace(text,old,'''        if code.lowering.whole_source is not None:
            from swdb import dx100_checked_adapter
            dx100_checked_adapter.check_launch(self,job,context,[('cxx',replay_cc)])
            problem=dx100_checked_adapter.compile_native(context['tools'],'cxx',replay_cc,binary,
                ['-DSWDB_NATIVE','-DSWDB_REPLAY','-O0','-g','-w',*SANITIZERS,*code.cxx_defines()])
        else:
'''+'\n'.join('    '+line for line in old.splitlines()))
    text=replace(text,'            with open(given) as stdin:',
        '''            if code.lowering.whole_source is not None:
                dx100_checked_adapter.check_launch(self,job,context)
            with open(given) as stdin:''')
    text=replace(text,'            text = replay_log.read_text(errors="replace")',
        '''            if code.lowering.whole_source is not None:
                dx100_checked_adapter.check_launch(self,job,context)
            text = replay_log.read_text(errors="replace")''')
    text=replace(text,'            inputs = _inputs(text)',
        '''            if code.lowering.whole_source is not None:
                retained_replay = out / f'whole-source-replay-{index}.log'
                retained_replay.write_text(text)
                context['reports'].append((f'whole_source_replay_termination_{index}',retained_replay))
                context['settings'].setdefault('whole_source_replay_terminations',[]).append({
                    'exit_code':done.exit_code,'original_assert_abort_observed':
                        bool(re.search(r'__assert_fail|Assertion .*failed',text)),
                    'scope':'original C++ assert abort is retained; missing exact failure marker grants no replay'})
            inputs = _inputs(text)''')
    prefix='''            assumptions += proof_semantics.record_assumptions(self.library, model.entry, model.sha256)
            from swdb import bounded_initialization
'''
    selected_prefix='''            if context.get('whole_source_unit') is not None:
                from swdb import dx100_checked_source
                assumptions += dx100_checked_source.record_assumptions(context['whole_source_unit'])
            else:
                assumptions += proof_semantics.record_assumptions(self.library, model.entry, model.sha256)
            from swdb import bounded_initialization
'''
    text=replace(text,prefix+'            if model.entry == bounded_initialization.DX100_TRACE_ENTRY:',selected_prefix+
        '''            if context.get('whole_source_unit') is not None:
                pass  # library-backed context rules were emitted once above
            elif model.entry == bounded_initialization.DX100_TRACE_ENTRY:''')
    text=replace(text,'        stubs = stubs or {}\n        tool = c_lowering.locate()',
        '''        stubs = stubs or {}
        if self.lowering.whole_source is not None:
            from swdb import dx100_checked_native
            if stubs:
                raise AdapterError('whole checked source cannot substitute C++ summary bodies')
            return self.model.c_text + dx100_checked_native.view(self.lowering.whole_source)['cxx_text']
        tool = c_lowering.locate()''')
    text=replace(text,'        if draw["role"] == "size":',
        '''        if draw['role'] == 'whole-model-choice':
            values = [0,1,2,3,2**31-1,2**31,2**32-1]
        elif draw["role"] == "size":''')
    return text


def setup(text):
    old='''        from swdb import bounded_initialization
        admissions = context.get("settings", {}).get("bounded_initialization") or {}'''
    start=text.index(old)
    end=text.index('    if adapter.name == "wp" and context.get("semantics"):',start)
    body=text[start:end]
    new='''        if context.get('whole_source_unit') is not None:
            from swdb import dx100_checked_adapter
            try:
                hashes['whole_source'] = dx100_checked_adapter.check_launch(adapter,job,context,[('c',path) for path,_ in inputs])
            except (ValueError,OSError,TypeError,KeyError,AttributeError) as exc:
                _fail('whole_source',str(exc))
        else:
'''+''.join('    '+line if line.strip() else line for line in body.splitlines(True))
    return replace(text,body,new)


def formal(text):
    old = "    options = proof_semantics.lowering_options(library)    # ticket 27: calls a proof semantics defines"
    text=replace(text, old, '''    from swdb import dx100_checked_source
    selection = dx100_checked_source.select_baseline(library, unit)
    if selection is not None:
        # Source bytes and summary names do not identify an atlas/receiver/TU.
        # Always freshly compose this route, bypassing the generic _LOWERED cache.
        try:
            return c_lowering.lower(path, unit['function'], defines=dx100_checked_source.DEFINES,
                                    whole_source_selection=selection)
        except c_lowering.LoweringError as exc:
            return exc
''' + old)
    text=replace(text,"    clauses = [c if isinstance(c, dict) else {} for c in clauses]",
        '''    clauses = [c if isinstance(c, dict) else {} for c in clauses]
    from swdb import dx100_checked_source
    whole_format = dx100_checked_source.checked_unit_format(library,entry_id,data)
    for reason in whole_format or ():
        error('whole_source_unit_contract',reason)''')
    text=replace(text,"            reasons = acsl_subset.check_formal_half(acsl['text'], acsl.get('uses', []), logic)",
        '''            reasons = ([] if whole_format == [] and dx100_checked_source.sole_whole_frame(acsl)
                       else acsl_subset.check_formal_half(acsl['text'], acsl.get('uses', []), logic))''')
    return text


TRANSFORMS = {'c_lowering.py': lowering, 'cbmc_translator.py': translator,
              'proof_semantics.py': semantics, 'formal_frame.py': formal,
              'cbmc_adapter.py':adapter, 'proof_setup.py':setup}


def main():
    bases = HERE / 'base-source'; bases.mkdir(exist_ok=True)
    manifest = HERE / 'hook-bases-v1.json'
    if manifest.exists():
        pins = json.loads(manifest.read_text())
    else:
        pins = {name: {'path': str(PRODUCTION / name), 'sha256': sha((PRODUCTION / name).read_bytes())}
                for name in TRANSFORMS}
        manifest.write_text(json.dumps(pins, indent=2, sort_keys=True) + '\n')
    deltas, diff, inverse = [], [], {}
    for name, transform in TRANSFORMS.items():
        original = (PRODUCTION / name).read_bytes()
        assert sha(original) == pins[name]['sha256'], 'concurrent base drift: ' + name
        base = bases / name
        if base.exists(): assert base.read_bytes() == original
        else: base.write_bytes(original)
        EDITS.clear()
        before = original.decode('utf-8'); after = transform(before)
        inverse[name] = list(EDITS)
        restored = after
        for row in reversed(EDITS):
            assert restored.count(row['new']) == row['count'], name
            restored = restored.replace(row['new'],row['old'])
        assert restored == before, 'exact inverse failed: ' + name
        ast.parse(after)
        output = HERE / 'proposed' / 'swdb' / name
        output.write_text(after)
        diff.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
            fromfile='a/swdb/' + name, tofile='b/swdb/' + name))
        deltas.append({'file': name, 'base_sha256': sha(original), 'proposed_sha256': sha(after.encode())})
    (HERE / 'production-hooks-v1.patch').write_text(''.join(diff))
    (HERE / 'hook-inverse-v1.json').write_text(json.dumps(inverse,indent=2,sort_keys=True)+'\n')
    (HERE / 'hook-delta-v1.json').write_text(json.dumps({'schema':'whole-source-hook-delta-1',
        'files': deltas, 'actual_public_route_complete': False,
        'source_hook_scope': 'prospective complete checked public orchestration; no actual execution/admission',
        'remaining': ['actual complete accepted capture under the selected supported transport',
            'actual complete TU exercise of original-source C++ runtime projection',
            'fresh complete method/producer/runtime admission and public proof/evidence controls']}, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'files':len(deltas), 'patch_sha256':sha((''.join(diff)).encode())}))


if __name__ == '__main__': main()
