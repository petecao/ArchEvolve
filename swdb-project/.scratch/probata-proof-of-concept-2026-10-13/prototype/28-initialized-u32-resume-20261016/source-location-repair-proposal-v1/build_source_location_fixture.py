"""2026-10-16 ET. Pure deterministic synthetic diagnostic-fixture construction.

The local allocator capture is a normalized zero-argument get_new_reg AST.
These synthetic nodes replace its function diagnostic with the existing arity1
u32 requirement and reconstruct direct ranges. They are not the retained remote
initialized AST, and the fixed IDs below are not compiler process identities.
"""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = next(parent for parent in HERE.parents if parent.name == 'swdb-project')
CAPTURE = PROJECT / 'tests/fixtures/dx100_allocator_linux_assertions.json'


def children(node):
    return node.get('inner', [])


def walk(node):
    yield node
    for child in children(node):
        yield from walk(child)


def abort(node):
    calls = [item for item in walk(node) if item.get('kind') == 'CallExpr']
    assert len(calls) == 1
    return calls[0]


def extent(start, stop):
    assert 0 <= start < stop
    return {'begin': {'offset': start, 'tokLen': 1},
            'end': {'offset': stop - 1, 'tokLen': 1}}


def build():
    raw = CAPTURE.read_bytes()
    capture = json.loads(raw)
    result = {
        'date': '2026-10-16 ET',
        'scope': 'SYNTHETIC diagnostic-only replacements of local normalized allocator AST; not the retained initialized AST or compiler output',
        'capture': {'path': str(CAPTURE.relative_to(PROJECT)),
                    'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
        'adaptations': [
            'Select only captured get_new_reg unsigned int width/bound entries 6/7.',
            'Replace zero-argument pretty-function literal/type with existing exact arity1-u32 requirement.',
            'Add synthetic direct CallExpr/SourceLocExpr ranges, fixed noncompiler IDs, and Clang-E line markers.',
        ],
        'cases': [],
    }
    for index, expected, variable, line in (
            (6, 'width', 'num_regs_needed', 121), (7, 'bound', 'REG_count', 125)):
        row = capture['assertions'][index]
        assert (row['family'], row['type'], row['assertion']) == ('get_new_reg', 'unsigned int', expected)
        node = copy.deepcopy(row['ast'])
        call = abort(node)
        diagnostic = children(call)[4]
        wrapper = children(diagnostic)[0]
        predefined = children(wrapper)[0]
        literal = children(predefined)[0]
        text = 'int get_new_reg(T1) [T1 = unsigned int]'
        for item in (wrapper, predefined, literal):
            item['type'] = {'qualType': 'const char[' + str(len(text) + 1) + ']'}
        literal['value'] = json.dumps(text)
        prefix = '# ' + str(line) + ' "/synthetic/original/MAA_gem5.hpp" 1\n'
        source = row['source']
        tokens = prefix + source + '\n'
        # The source ends with the abort call's ')' and then the outer paren.
        call['range'] = extent(len(prefix) + source.index('__assert_fail'), len(prefix) + len(source) - 1)
        for position, builtin in ((2, '__builtin_FILE'), (3, '__builtin_LINE')):
            item = children(call)[position]
            assert item['kind'] == 'SourceLocExpr'
            begin = len(prefix) + source.index(builtin)
            stop = tokens.index(')', begin) + 1
            item['id'] = hex(0x7000 + index * 16 + position)
            item['range'] = extent(begin, stop)
        result['cases'].append({'capture_index': index, 'expected': expected,
                                'variable': variable, 'tokens': tokens, 'ast': node})
    return result


if __name__ == '__main__':
    (HERE / 'synthetic-source-location-fixture.json').write_text(
        json.dumps(build(), sort_keys=True, indent=2) + '\n')
