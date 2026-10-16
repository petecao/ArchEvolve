"""2026-10-16 ET. Prepare a reviewable two-file patch; never apply it.

Only stdlib filesystem/source/hash work. Root owns production integration and
all public/actual execution. Refuse an unexpected base rather than overwrite it.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import tempfile

import trace_fixture as fixture


BASES = {
    'bounded_initialization.py': '12885e27dc1cb62b6c89ed4c2b5728c350dc6b0a5781b09ab70ff058e83b287d',
    'cbmc_adapter.py': 'a685bf063ce991372f68d115b7921da3b0afccea908e907bbf892f9094d191c0',
}


def generate():
    output = Path(__file__).resolve().parent
    project = output.parents[3]
    originals = {name: (project / 'swdb' / name).read_text() for name in BASES}
    for name, text in originals.items():
        if hashlib.sha256(text.encode()).hexdigest() != BASES[name]:
            raise ValueError('production base changed; review fresh bytes before proposing: ' + name)
    with tempfile.TemporaryDirectory(prefix='trace-proposal-') as folder:
        library = Path(folder) / 'library'
        (library / 'proof_semantics').mkdir(parents=True)
        entry = {}
        fixture.transform(entry, library, project=project)
    canonical = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    # Every pin is library-relative and deterministic. Freeze the complete entry,
    # including top-level/ghost/model key sets, source pins, premises and metadata.
    shape = entry
    queries = repr(fixture.QUERY_PROTOTYPES)
    hashes = repr(fixture.policy_document()['components'])
    helper = f'''# 2026-10-16 ET. Exact synthetic scalar trace only; no hardware/source call exemption.
DX100_TRACE_ENTRY = {fixture.ENTRY!r}
DX100_TRACE_ID = {fixture.POLICY_ID!r}
DX100_TRACE_COMPONENTS = {hashes}
DX100_TRACE_CONSTANTS = {fixture.CONSTANTS!r}
DX100_TRACE_QUERIES = {queries}
DX100_TRACE_SHAPE_SHA256 = {canonical(shape)!r}
DX100_TRACE_SCOPE = {fixture.SCOPE!r}


def _dx100_trace_policy(library, model, defines):
    """Exact initialized scalar trace closure; no parameterized/arbitrary model admission."""
    if library is None or model is None or model.entry != DX100_TRACE_ENTRY:
        return None
    from swdb import artifacts, proof_semantics
    try:
        entry = library.get(model.entry) or {{}}
        if (_hash(entry) != DX100_TRACE_SHAPE_SHA256
                or proof_semantics._constants(entry, defines) != DX100_TRACE_CONSTANTS
                or any(type(value) is not int for value in entry['constants'].values())
                or set(entry['model']) != {{'state', 'c', 'logic'}}
                or entry['ghost'].get('capacity') != {{'commands': 2}}):
            return None
        references = {{'ghost': entry['ghost']['acsl'], **entry['model']}}
        for reference in references.values():
            library._pin(reference)
        actual = {{key: hashlib.sha256(library.resolve(ref).read_bytes()).hexdigest()
                  for key, ref in references.items()}}
        if (actual != DX100_TRACE_COMPONENTS
                or artifacts.file_hash(library.files[model.entry]) != model.sha256
                or proof_semantics.model_for(library, model.entry, defines) != model
                or set(model.queries) != set(DX100_TRACE_QUERIES)
                or not set(model.queries) <= set(model.functions)
                or set(model.calls) & set(model.functions)):
            return None
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        return None
    return {{'id': DX100_TRACE_ID, 'entry': model.entry, 'entry_sha256': model.sha256,
            'components': actual, 'generated_sha256': hashlib.sha256(model.c_text.encode()).hexdigest(),
            'tile_objects': [{{'name': name, 'elements': extent}} for name, extent in model.tile_objects],
            'calls': sorted(DX100_TRACE_QUERIES), 'scope': DX100_TRACE_SCOPE}}


'''
    bounded = originals['bounded_initialization.py']
    anchor = 'def _dx100_policy(library, model, defines):\n'
    assert bounded.count(anchor) == 1
    bounded = bounded.replace(anchor, helper + anchor, 1)
    old = '        if actual != DX100_CONTENT or artifacts.file_hash(library.files[model.entry]) != model.sha256:\n            return None\n'
    assert bounded.count(old) == 1
    bounded = bounded.replace(old, '        if actual != DX100_CONTENT or artifacts.file_hash(library.files[model.entry]) != model.sha256:\n            return _dx100_trace_policy(library, model, defines)\n', 1)

    cbmc = originals['cbmc_adapter.py']
    old = '        source_kwargs = dict(defines=self.defines, **proof_semantics.lowering_options(self.library))\n'
    new = old + '''        # The exact synthetic trace imports scalar bodyless ghost queries only.
        # Reuse the established full-TU callee/signature checker, without adding
        # any pointer-domain or real-header exemption to the generic path.
        from swdb import bounded_initialization
        trace_policy = None
        if bounded_initialization.DX100_TRACE_ENTRY in proof_semantics.current(self.library):
            trace_model = proof_semantics.model_for(self.library, bounded_initialization.DX100_TRACE_ENTRY, self.defines)
            trace_policy = bounded_initialization._dx100_trace_policy(self.library, trace_model, self.defines)
            if trace_policy is not None:
                source_kwargs['semantics']['audited_imports'] = {
                    name: row for name, row in proof_semantics.imported_call_policies(self.library, self.defines).items()
                    if name in trace_policy['calls']}
'''
    assert cbmc.count(old) == 1
    cbmc = cbmc.replace(old, new, 1)
    old = '            context["model"] = model\n'
    new = old + '''            if model.entry == bounded_initialization.DX100_TRACE_ENTRY:
                settings = context['settings']['proof_semantics']
                settings.update(scope='synthetic abstract scalar event trace only',
                    exit_check='no pending abstract command at unit exit',
                    native_address_abi='scalar abstract cell/region/tile IDs; no caller pointer mapping',
                    counterexample_scope='abstract-model trace only; no hardware counterexample or source refinement')
                from swdb import wp_pointer_bounds
                try:
                    import_report = wp_pointer_bounds.check(lowering)
                    wp_pointer_bounds.check_semantic_origins(lowering, self.library, self.defines)
                except wp_pointer_bounds.Refused as exc:
                    context['settings']['verifier_launched'] = False
                    return self._not_proven('unsupported_construct', str(exc), context)
                imports = [row for row in import_report['sites'] if row.get('kind') == 'import'
                           and row.get('call') in (trace_policy or {}).get('calls', [])]
                settings['source_imports'] = [{k: v for k, v in row.items() if not k.startswith('_')} for row in imports]
                bound_names = {(row.get('binding') or {}).get('name') for row in imports
                               if row.get('binding') and not row.get('reason')}
                if (trace_policy is None or not set(externals) <= bound_names
                        or any(not row.get('binding') or row.get('reason') for row in imports)):
                    context['settings']['verifier_launched'] = False
                    return self._not_proven('unsupported_construct',
                        'synthetic scalar queries need exact bodyless full-TU imports and model policy', context)
                context['synthetic_trace_source_plan'] = {'source': str(source), 'kwargs': source_kwargs}
'''
    assert cbmc.count(old) == 1
    cbmc = cbmc.replace(old, new, 1)
    old = '        entry = self.library.get(self.contract) or {}\n        declarations = (entry.get(\'proof_unit\') or {}).get(\'array_domains\')\n'
    new = '''        trace_plan = context.get('synthetic_trace_source_plan')
        if trace_plan is not None:
            from swdb import bounded_initialization, bounded_entry_windows, wp_pointer_bounds
            model = context.get('model')
            if bounded_initialization._dx100_trace_policy(self.library, model, self.defines) is None:
                raise bounded_entry_windows.Refused('synthetic scalar model policy changed before launch')
            try:
                wp_pointer_bounds.recheck_source(context['lowering'], trace_plan)
                wp_pointer_bounds.check_semantic_origins(context['lowering'], self.library, self.defines)
            except wp_pointer_bounds.Refused as exc:
                raise bounded_entry_windows.Refused(str(exc)) from None
''' + old
    assert cbmc.count(old) == 1
    cbmc = cbmc.replace(old, new, 1)
    start = cbmc.index('            assumptions.append({"kind": "proof_semantics", "reference": {"id": model.entry, "sha256": model.sha256},\n', cbmc.index('    def _verdict('))
    stop = cbmc.index('        if context.get("lowering") is not None:', start)
    legacy = cbmc[start:stop]
    replacement = '''            from swdb import bounded_initialization
            if model.entry == bounded_initialization.DX100_TRACE_ENTRY:
                assumptions.append({'kind': 'proof_semantics',
                    'reference': {'id': model.entry, 'sha256': model.sha256},
                    'sentence': 'This is a synthetic abstract scalar trace. Deferred history, ownership, '
                                'region and pair checks describe its exact pinned model only; there is no '
                                'real-header, CPU-access, typed-value, physical-address or hardware refinement '
                                'certificate and no at-issue reduction claim.'})
            else:
'''
    replacement += ''.join('    ' + line if line.strip() else line for line in legacy.splitlines(keepends=True))
    cbmc = cbmc[:start] + replacement + cbmc[stop:]
    proposed = {'bounded_initialization.py': bounded, 'cbmc_adapter.py': cbmc}
    patch = ''
    for name, text in proposed.items():
        ast.parse(text)  # Python source parse only, never import/execute production.
        (output / (name + '.proposed')).write_text(text)
        patch += ''.join(difflib.unified_diff(originals[name].splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile='a/swdb-project/swdb/' + name, tofile='b/swdb-project/swdb/' + name))
    (output / 'integration.patch').write_text(patch)
    (output / 'integration-base.json').write_text(json.dumps({
        'date': '2026-10-16 ET', 'base_files_equal_HEAD_when_read': True,
        'base_sha256': BASES, 'entry_shape_sha256': canonical(shape),
        'proposed_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in proposed.items()},
        'patch_sha256': hashlib.sha256(patch.encode()).hexdigest(),
        'status': 'proposal only; production files untouched; root review/integration/actual admission required'}, indent=2) + '\n')
    return patch


if __name__ == '__main__':
    generate()
