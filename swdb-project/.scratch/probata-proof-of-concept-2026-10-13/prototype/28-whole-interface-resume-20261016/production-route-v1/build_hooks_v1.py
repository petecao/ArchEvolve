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
    return text


def formal(text):
    old = "    options = proof_semantics.lowering_options(library)    # ticket 27: calls a proof semantics defines"
    return replace(text, old, '''    from swdb import dx100_checked_source
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


TRANSFORMS = {'c_lowering.py': lowering, 'cbmc_translator.py': translator,
              'proof_semantics.py': semantics, 'formal_frame.py': formal}


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
        'remaining': ['checked adapter public orchestration and final generated-source gate',
            'actual complete accepted capture and bounded original-source C++ runtime projection',
            'fresh complete method/producer/runtime admission and public proof/evidence controls']}, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'files':len(deltas), 'patch_sha256':sha((''.join(diff)).encode())}))


if __name__ == '__main__': main()
