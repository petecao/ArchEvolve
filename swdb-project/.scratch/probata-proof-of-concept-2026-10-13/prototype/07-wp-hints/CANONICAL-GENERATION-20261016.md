# Canonical generated source

2026-10-16 ET. Prospective preparation only; source, initializedness, lifetime,
full TD and counted-run gates remain closed.

The canonical generators now remove only spaces and tabs at line ends before
extracting final contracts and computing output hashes. They preserve line
structure and reject a trim that would introduce a backslash-newline splice.
The private-array generator physically pins the canonical out-slot inputs.

New outputs are in `standin_outslot_canonical` and
`standin_private_array_canonical`. Historical `standin_outslot` and
`standin_private_array` remain byte-identical; the 971ad632, 3940afd0 and e97fb191
freezes and retained native evidence remain intact. The normal control runners
now select the canonical directories; historical controls remain replayable
from their historical Git commits.

The old public generator reproduced the defect: 24 generated lines retained
trailing whitespace. Targeted shared-B/time/RSS-guarded pure controls regenerate
both stages, check all 18 generated C/header/site files against historical bytes
with only line-end whitespace removed, check emitted-contract maps and physical
hashes, refuse CRLF mutations and newly introduced line splices, and verify that
historical output directories remain unchanged. The first control-reader attempt
failed on an ambiguous suffix lookup; it is retained, and the corrected reader
uses the exact `void` declaration. The successful receipt is recorded in
`../../evidence/t07-canonical-generation-preparation-20261016.json`.

No native/compiler/formal job was run for this formatting successor. Earlier
native receipts qualify their exact historical source; the new source has only
the targeted pure equivalence and regeneration evidence described here. There
is no new proof, allocation correspondence, source correspondence or TD result.
