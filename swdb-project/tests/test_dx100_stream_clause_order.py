"""2026-10-16 ET. ACSL output order; real Frama parser admission is separate."""
import re
import pytest
from swdb.dx100_stream_model import normal_return_model

@pytest.mark.parametrize('call',['maa_stream_load_unsigned_int','wait_ready','get_tile_size'])
def test_public_stream_contract_places_termination_after_requires_before_simple_clauses(call):
 text=normal_return_model()['contracts'][call]
 clauses=re.findall(r'\b(requires|terminates|assigns|ensures)\b',text)
 ranks={'requires':0,'terminates':1,'assigns':2,'ensures':3}
 assert clauses.count('terminates')==1
 assert [ranks[c]for c in clauses]==sorted(ranks[c]for c in clauses),text
