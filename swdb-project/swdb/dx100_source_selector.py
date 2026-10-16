"""2026-10-16 ET. Narrow real-header uint32 selector certificate.

This admits one pure template body, never a general MMIO/header exemption.
Clang must fold the uniquely selected source function to its declared enum value
in the actual unit context. No solver is invoked here.
"""
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

from swdb import artifacts, stdlib_provenance
from swdb.dx100_interface import HEADERS

KIND = 'dx100-get-data-type-u32-v1'
PROTOTYPE = 'unsigned char get_data_type_unsigned_int(void)'
CONTRACT = r'assigns \nothing; ensures \result == 0;'


class Refused(ValueError):
    pass


def policy(library, definition):
    """Resolve immutable source pins; refusal survives as a lowering error."""
    try:
        if (not isinstance(definition, dict) or set(definition) != {'kind', 'value', 'sources'}
                or definition['kind'] != KIND or type(definition['value']) is not int or definition['value'] != 0
                or not isinstance(definition['sources'], list) or len(definition['sources']) != 2):
            raise Refused('only the closed uint32 selector definition policy is supported')
        pins = []
        for pin in definition['sources']:
            library._pin(pin)
            path = library.resolve(pin).resolve()
            if path.name not in HEADERS or artifacts.file_hash(path) != HEADERS[path.name]:
                raise Refused('selector source differs from the immutable interface header')
            pins.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': HEADERS[path.name]})
        if {Path(p['path']).name for p in pins} != set(HEADERS):
            raise Refused('selector requires both distinct immutable interface headers')
        return {'kind': KIND, 'value': 0, 'sources': pins}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return {'refused': str(exc)}


def check(library, data, error):
    valid = True
    for i, row in enumerate(data.get('calls') or []):
        if not isinstance(row, dict) or not isinstance(row.get('instances'), list):
            continue  # the shared instance validator reports malformed containers
        for j, instance in enumerate(row['instances']):
            if not isinstance(instance, dict) or 'definition' not in instance:
                continue
            if (instance.get('prototype') != PROTOTYPE or not isinstance(instance.get('contract'), str)
                    or re.sub(r'\s+', '', instance.get('contract', '')) != re.sub(r'\s+', '', CONTRACT)):
                error(f'calls[{i}].instances[{j}].definition', 'definition policy needs the exact u32 selector prototype and contract')
                valid = False
            selected = policy(library, instance['definition'])
            if ('refused' in selected or row.get('call') != 'get_data_type'
                    or instance.get('arguments') != ['unsigned int'] or instance.get('arity') != 0):
                error(f'calls[{i}].instances[{j}].definition', selected.get('refused') or
                      'source selector definition requires get_data_type<unsigned int>()')
                valid = False
    return valid



PURE_LAYOUT = 'dx100-pure-selector-u32-v1'
PURE_STATEMENT = ('Only the source-certified get_data_type<unsigned int>() helper is admitted; '
                  'all other interface calls are explicitly refused. No device commands or timing reduction are used.')


def pure_layout(data):
    return (data.get('model') or {}).get('layout') == PURE_LAYOUT


def check_layout(data, texts, error):
    """This closed stateless layout cannot suppress state checks for device calls."""
    layout = (data.get('model') or {}).get('layout')
    if layout is None:
        return True
    valid = True
    def refuse(reason):
        nonlocal valid
        valid = False
        error('model.layout', reason)
    if layout != PURE_LAYOUT:
        refuse('unsupported proof-semantics model layout')
        return False
    active = [r for r in data.get('calls', []) if isinstance(r, dict) and r.get('supported') is not False]
    instances = active[0].get('instances') if len(active) == 1 else None
    if (len(active) != 1 or active[0].get('call') != 'get_data_type'
            or not isinstance(instances, list) or len(instances) != 1
            or not isinstance(instances[0], dict) or 'definition' not in instances[0]):
        refuse('pure selector layout admits only the single certified u32 selector instance')
    if (not data.get('declaration_inventory') or data.get('constants') or data.get('queries') or data.get('wp')):
        refuse('pure selector layout requires complete declarations and no device constants, queries or WP premises')
    clean = lambda text: re.sub(r'/\*.*?\*/|//[^\n]*|\s+', '', text, flags=re.S)
    for key in ('ghost.acsl', 'model.state', 'model.logic'):
        if key in texts and clean(texts[key]):
            refuse('pure selector layout has no ghost/device state or logic axioms')
    if 'model.c' in texts and clean(texts['model.c']) != 'unsignedcharget_data_type_unsigned_int(void){return0;}':
        refuse('pure selector layout requires the exact constant selector C body')
    return valid

def _pin(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': artifacts.file_hash(path)}


def certify(unit, declaration, arguments, selected, *, standard, timeout):
    """Compile a pure probe in the actual source context, then inspect its IR.

    A single global source family is required. Canonical builtin arguments and
    cleared probe-only macros prevent late caller macros changing the probe's
    type/call spelling. Candidate function bodies receive no generic exemption.
    """
    if 'refused' in selected:
        raise Refused(selected['refused'])
    if selected.get('kind') != KIND or arguments != ['unsigned int']:
        raise Refused('unsupported source selector/type policy')
    headers = selected['sources']
    target = next(p for p in headers if Path(p['path']).name == 'MAA_gem5.hpp')
    location = declaration.get('loc') or {}
    if (location.get('spellingLoc') or location.get('expansionLoc') or
            Path(location.get('_file', location.get('file', ''))).resolve() != Path(target['path'])):
        raise Refused('selector definition does not originate in the pinned MMIO header')
    families = [n for n in unit.dump('get_data_type')
                if n.get('kind') == 'FunctionTemplateDecl' and n.get('name') == 'get_data_type']
    if len(families) != 1 or declaration.get('mangledName') not in {
            '_Z13get_data_typeIjE8DataTypev', '__Z13get_data_typeIjE8DataTypev'}:
        raise Refused('selector has no unique global template family: '
                      +str(len(families))+' '+str(declaration.get('mangledName')))
    source_hash = unit.source_digest

    def unchanged():
        if artifacts.file_hash(unit.source) != source_hash or any(_pin(p['path']) != p for p in headers):
            raise Refused('source/header changed during selector binding')

    unchanged()
    name = '__swdb_dx100_u32_type_certificate'
    probe = ('\nextern "C" unsigned int '+name+'() { return (unsigned int)::get_data_type<unsigned int>(); }\n')
    runtime_identity = stdlib_provenance.runtime_identity(unit.tool)
    with tempfile.TemporaryDirectory(prefix='swdb-dx100-selector-') as folder:
        source, depfile = Path(folder)/'probe.ii', Path(folder)/'original.d'
        # Preprocess the ORIGINAL main file with the parser's original flags.
        # Including it from an O2 probe changes __INCLUDE_LEVEL__, __BASE_FILE__
        # and __OPTIMIZE__. The resulting original tokens are compiled without
        # another preprocessing pass, so the optimization probe cannot reinterpret
        # any original conditional/macro directive.
        preprocess_command = [*unit.tool.command, '-x', 'c++', '-std='+standard, '-fopenmp',
                              '-E', '-MD', '-MF', str(depfile), '-I'+str(unit.source.parent)]
        preprocess_command += ['-I'+str(p) for p in unit.includes] + ['-D'+d for d in unit.defines]
        preprocess_command += [str(unit.source)]
        try:
            preprocessed = subprocess.run(preprocess_command, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.SubprocessError) as exc:
            raise Refused('original source preprocessing did not finish: '+str(exc)) from None
        if preprocessed.returncode:
            raise Refused('original source preprocessing refused: '+preprocessed.stderr[-500:])
        deps = depfile.read_text().replace('\\\n', '').split(':', 1)[1]
        inputs = [_pin(p) for p in sorted(set(shlex.split(deps)))]
        frozen_source = preprocessed.stdout+probe
        source.write_text(frozen_source)
        command = [*unit.tool.command, '-x', 'c++-cpp-output', '-std='+standard, '-fopenmp',
                   '-O2', '-S', '-emit-llvm', '-o', '-', str(source)]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.SubprocessError) as exc:
            raise Refused('selector compiler probe did not finish: '+str(exc)) from None
        if result.returncode:
            errors = [line.strip() for line in result.stderr.splitlines() if 'error:' in line]
            raise Refused('selector compiler probe refused: '+'; '.join(errors[:3]))
        matches = list(re.finditer(r'^define\b[^\n{]*@'+name+r'\([^)]*\)[^\n{]*\{(?P<body>.*?)^}',
                                   result.stdout, re.M | re.S))
        if len(matches) != 1:
            raise Refused('selector compiler probe has no unique constant function')
        body = re.sub(r';[^\n]*', '', matches[0]['body'])
        body = re.sub(r'^\s*[A-Za-z_][\w.]*:\s*', '', body, flags=re.M).strip()
        if body != 'ret i32 0':
            raise Refused('actual source selector does not fold to UINT32_TYPE0: '+body[:160])
        if any(_pin(p['path']) != p for p in inputs):
            raise Refused('original compiler input changed during the selector certificate')
        if stdlib_provenance.runtime_identity(unit.tool) != runtime_identity:
            raise Refused('compiler runtime changed during the selector certificate')
    unchanged()
    return {'kind': KIND, 'value': 0, 'arguments': arguments,
            'source_mangled': declaration['mangledName'], 'source_sha256': source_hash,
            'source_path': str(unit.source.resolve()),
            'headers': headers, 'compiler_inputs': inputs, 'compiler_command': command,
            'compiler_version': unit.tool.version, 'runtime_identity': runtime_identity,
            'preprocess_command': preprocess_command, 'preprocessed_source': preprocessed.stdout,
            'preprocessed_source_sha256': hashlib.sha256(preprocessed.stdout.encode()).hexdigest(),
            'preprocessed_bytes': len(preprocessed.stdout.encode()),
            'probe_source': probe, 'probe_source_sha256': hashlib.sha256(probe.encode()).hexdigest(),
            'llvm_function': matches[0].group(), 'llvm_module': result.stdout,
            'llvm_module_sha256': hashlib.sha256(result.stdout.encode()).hexdigest()}



def recheck(lowering):
    """Rehash the frozen compiler evidence and physical inputs before formal launch."""
    witnesses = []
    for row in getattr(lowering, 'summaries', ()):
        definition = row.get('semantic_instance', {}).get('definition')
        if definition is None:
            continue
        try:
            if definition['kind'] != KIND or definition['arguments'] != ['unsigned int'] or definition['value'] != 0:
                raise Refused('source selector certificate changed kind/type/value')
            for text, digest in (('preprocessed_source', 'preprocessed_source_sha256'), ('llvm_module', 'llvm_module_sha256'),
                                 ('probe_source', 'probe_source_sha256')):
                if hashlib.sha256(definition[text].encode()).hexdigest() != definition[digest]:
                    raise Refused('source selector frozen compiler evidence changed')
            if artifacts.file_hash(Path(definition['source_path'])) != definition['source_sha256']:
                raise Refused('source selector original main file changed')
            for pin in [*definition['headers'], *definition['compiler_inputs']]:
                if _pin(pin['path']) != pin:
                    raise Refused('source selector physical compiler input changed: '+pin['path'])
            witnesses.append({key: definition[key] for key in ('kind', 'source_sha256', 'preprocessed_source_sha256',
                                                              'llvm_module_sha256', 'compiler_inputs')})
        except (OSError, KeyError, TypeError, AttributeError) as exc:
            raise Refused('source selector evidence is unavailable: '+str(exc)) from None
    return witnesses
