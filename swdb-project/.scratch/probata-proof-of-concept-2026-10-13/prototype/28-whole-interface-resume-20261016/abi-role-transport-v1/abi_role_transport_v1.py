"""Closed ABI-only paired-Type transport; never a source-TU/ID join.

The artificial container exists solely to reuse the exact reviewed complete
token grammar and role renamer. It is removed before the unchanged ABI reader.
Original compiler bytes, derived strict bytes and their inverse are distinct.
"""
import hashlib
import io
import json
from pathlib import Path
import stat

from swdb._dx100_whole import role_normalized_gzip_v2 as normalizer
from swdb._dx100_whole import strict_minify_v2 as tokens

NORMALIZER_SHA = '6301baede48b9b0f1d3beaef2873e59026f5e9e26135bc2f7ba0a3f76825f941'
TOKENS_SHA = 'b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897'
FAMILIES = {
    'first-source-v10': (127394, '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15'),
    'three-memory-g642': (127541, '493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c'),
}
LIMIT = 262144
PREFIX = b'{"kind":"TranslationUnitDecl","inner":['
SUFFIX = b']}'


class Refused(ValueError):
    pass


def need(value, message):
    if not value:
        raise Refused(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stable(value):
    return tuple(getattr(value, key) for key in ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid',
        'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def primitive(module, expected):
    path = Path(module.__file__)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path and before.st_size <= LIMIT,
         'canonical bounded ABI primitive source required')
    raw = path.read_bytes()
    need(sha(raw) == expected and stable(path.lstat()) == stable(before), 'ABI primitive identity changed')
    return {'path': str(path), 'bytes': len(raw), 'sha256': expected}


class Pairs(tuple):
    pass


def no_constant(_value):
    raise Refused('nonfinite ABI JSON refused')


def strict_pairs(rows):
    result = {}
    for key, value in rows:
        need(key not in result, 'unknown duplicate ABI key remains')
        result[key] = value
    return result


def roots(raw, *, strict):
    """Return exact original token spans, without merging declarations or IDs."""
    need(type(raw) is bytes and 0 < len(raw) <= LIMIT, 'bounded ABI stream required')
    try:
        text = raw.decode('ascii')
    except UnicodeError as error:
        raise Refused('closed selected ABI stream must remain ASCII') from error
    decoder = json.JSONDecoder(object_pairs_hook=strict_pairs if strict else Pairs, parse_constant=no_constant)
    rows = []
    at = 0
    while at < len(text):
        while at < len(text) and text[at] in ' \t\r\n':
            at += 1
        if at == len(text):
            break
        begin = at
        try:
            value, at = decoder.raw_decode(text, at)
        except (ValueError, RecursionError) as error:
            raise Refused('malformed ABI JSON stream') from error
        need(isinstance(value, dict if strict else Pairs), 'ABI object root required')
        rows.append(raw[begin:at])
        need(len(rows) <= 29, 'bounded ABI root census required')
    need(rows, 'nonempty ABI root stream required')
    return rows


def minified_tokens(raw):
    """Whitespace-only identity projection after complete grammar validation."""
    output = bytearray()
    quoted = escaped = False
    for byte in raw:
        if quoted:
            output.append(byte)
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
            output.append(byte)
        elif byte not in b' \t\r\n':
            output.append(byte)
    need(not quoted and not escaped, 'complete ABI string closure required')
    return bytes(output)


def _transport(raw, *, expected_roots, expected_renames):
    """Private token engine; public selection additionally pins exact originals."""
    selected = roots(raw, strict=False)
    need(len(selected) == expected_roots, 'exact complete ABI root count required')
    wrapped = PREFIX + b','.join(selected) + SUFFIX
    need(len(wrapped) <= LIMIT, 'bounded synthetic ABI transport container required')
    output = io.BytesIO()
    manifest = io.BytesIO()
    normalization = normalizer.normalize(io.BytesIO(wrapped), output, manifest, tokens.__dict__, lambda: None)
    normalized_wrapper = output.getvalue()
    inverse_manifest = manifest.getvalue()
    need(normalization['duplicate_events'] == normalization['prospective_role_renames'] == expected_renames
         and normalization['unknown_or_mismatched_duplicate_events'] == 0,
         'only exact complete ABI paired-Type roles may be renamed')
    need(normalization['original_minified_token_sha256'] == sha(minified_tokens(wrapped)),
         'complete original ABI container token identity differs')
    inverse = normalizer.inverse_stream_identity(io.BytesIO(normalized_wrapper), inverse_manifest, normalization, lambda: None)
    need(normalized_wrapper.startswith(PREFIX) and normalized_wrapper.endswith(SUFFIX),
         'synthetic ABI transport container changed')
    inner = normalized_wrapper[len(PREFIX):-len(SUFFIX)]
    # Each normalized root is located by the strict decoder. The comma delimiters
    # are container-only bytes and are removed, never source/declaration tokens.
    decoder = json.JSONDecoder(object_pairs_hook=strict_pairs, parse_constant=no_constant)
    text = inner.decode('ascii')
    at = 0
    pieces = []
    while at < len(text):
        begin = at
        value, at = decoder.raw_decode(text, at)
        need(type(value) is dict, 'strict normalized ABI root required')
        pieces.append(inner[begin:at])
        if at < len(text):
            need(text[at] == ',', 'exact synthetic ABI root separator required')
            at += 1
    need(len(pieces) == expected_roots and PREFIX + b','.join(pieces) + SUFFIX == normalized_wrapper,
         'complete strict ABI root/container inverse differs')
    derived = b'\n'.join(pieces) + b'\n'
    need(0 < len(derived) <= LIMIT and len(roots(derived, strict=True)) == expected_roots,
         'complete strict ABI output required')
    receipt = {'schema': 'closed-ABI-paired-type-transport-1', 'original_bytes': len(raw), 'original_sha256': sha(raw),
        'derived_strict_bytes': len(derived), 'derived_strict_sha256': sha(derived), 'root_count': expected_roots,
        'role_renames': expected_renames, 'normalization': normalization, 'inverse': inverse,
        'inverse_manifest_sha256': sha(inverse_manifest), 'synthetic_container': True,
        'synthetic_container_is_original_TU': False, 'source_call_IDs_joined': False,
        'all_root_tokens_preserved_except_documented_role_key': True, 'source_ABI_or_public_admission': False}
    return derived, receipt


def normalize_abi(raw):
    need(type(raw) is bytes, 'original ABI bytes required')
    family = [name for name, expected in FAMILIES.items() if (len(raw), sha(raw)) == expected]
    need(len(family) == 1, 'only exact retained first/memory ABI artifacts are selected')
    before = [primitive(normalizer, NORMALIZER_SHA), primitive(tokens, TOKENS_SHA)]
    derived, receipt = _transport(raw, expected_roots=29, expected_renames=4)
    need([primitive(normalizer, NORMALIZER_SHA), primitive(tokens, TOKENS_SHA)] == before,
         'ABI primitive source changed during transport')
    return derived, {**receipt, 'selected_family': family[0], 'primitive_sources': before,
        'eligibility_observed_by_this_call': True, 'prior_memory_ABI_eligibility_inferred': False}
