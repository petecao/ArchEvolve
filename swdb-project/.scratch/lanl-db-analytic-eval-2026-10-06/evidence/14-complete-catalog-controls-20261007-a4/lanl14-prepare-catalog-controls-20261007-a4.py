"""Reuse compact metadata controls at the new admin helper paths; 2026-10-07 ET."""
import difflib
import json
from pathlib import Path
root=Path('/private/tmp')
old=root/'lanl14-pr-final-model-custody-controls-20261007-a3.py';new=root/'lanl14-pr-final-model-custody-controls-catalog-caps-20261007-a4.py'
text=old.read_text();assert text.count('/private/tmp/lanl14-pr-final-local-runner-20261007-a3.py')==1
text=text.replace('/private/tmp/lanl14-pr-final-local-runner-20261007-a3.py','/private/tmp/lanl14-pr-final-local-runner-catalog-caps-20261007-a4.py',1)
assert text.count('/private/tmp/lanl14-pr-final-model-custody-controls-proof-20261007-a3.json')==1
text=text.replace('/private/tmp/lanl14-pr-final-model-custody-controls-proof-20261007-a3.json','/private/tmp/lanl14-pr-final-model-custody-controls-proof-catalog-caps-20261007-a4.json',1)
assert not new.exists();new.write_text(text)
old=root/'lanl14_final_controls.py';new=root/'lanl14_final_controls_catalog_caps_a4.py';text=old.read_text()
for a,b in (('/private/tmp/lanl14_final_reports.py','/private/tmp/lanl14_final_reports_catalog_caps_a4.py'),('/private/tmp/lanl14_final_export.py','/private/tmp/lanl14_final_export_catalog_caps_a4.py')):
 assert a in text;text=text.replace(a,b)
assert not new.exists();new.write_text(text)
proof=json.loads((root/'lanl14-complete-catalog-cap-proof-20261007-a4.json').read_text());lines=[]
for row in proof['helpers']:
 old=Path(row['original']);new=Path(row['revision'])
 lines.extend(difflib.unified_diff(old.read_text().splitlines(keepends=True),new.read_text().splitlines(keepends=True),fromfile=str(old),tofile=str(new),n=0))
(root/'lanl14-complete-catalog-cap-diff-20261007-a4.patch').write_text(''.join(lines))
