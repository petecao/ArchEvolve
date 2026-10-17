"""2026-10-16 ET. Emit owned fixed-order source cases; never execute them."""
import hashlib
import json
from pathlib import Path

from trace_cases import CASES, source


def prepare():
    output = Path(__file__).resolve().parent
    cases = output / 'cases'
    cases.mkdir(exist_ok=True)
    manifest = []
    for row in CASES:
        text = source(row)
        path = cases / (row['name'] + '.cc')
        path.write_text(text)
        manifest.append({'name': row['name'], 'source': str(path.relative_to(output)),
                         'sha256': hashlib.sha256(text.encode()).hexdigest(),
                         'expected_verdict': row['expected_verdict'],
                         'expected_property': row['expected_property']})
    document = {'date': '2026-10-16 ET', 'status': 'unexecuted prospective root-admitted public suite',
                'scope': 'abstract fixed-order model witnesses; never hardware/source-refinement witnesses',
                'junit_required': {'tests': 25, 'failures': 0, 'errors': 0, 'skipped': 0},
                'test': 'test_public_actual.py::test_actual_public_abstract_memory_trace', 'cases': manifest}
    (output / 'actual-policy.json').write_text(json.dumps(document, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    prepare()
