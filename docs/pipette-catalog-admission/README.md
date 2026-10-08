# Pipette queue and reference-access mechanisms

Pipette (MICRO 2020) splits irregular computation into pipeline stages that
exchange values through register-backed queues. This decouples stages and lets
its reference accelerators perform indirect reads or half-open array scans
using spare core rename/register bandwidth and the existing load/store unit.
It is an older implementation reference, not a new member of a recent-paper cohort.

Catalog revision 0.1.11 adds an explicit queue/RA record, two read subtypes,
seven located primary claims and eight mechanism annotations. Ordinary gather
queries and the project's MAPLE selection are unchanged. A general read query
can discover the new record, but retrieval does not satisfy its mapping obligations.

The desired semantics are point-to-point queue ownership, committed producer
visibility, FIFO consumption, separate speculative/committed head and tail,
rollback of speculative progress, and release of queue storage at consumer
commit. Full queues and empty queues block; register mappings cannot change
while active. Control values, fault routing and OS save/quiesce are separate
implementation obligations.

The evaluated reference has 148 aggregate QRM entries, at most 16 queues and
default queue depth 24. These are shared resources: they do not imply 16
independent queues each with 24 available entries. The paper's RA implementation
has a 32-entry completion buffer. Exact payload/index ABI, address coalescing,
RA response association and completion-order code remain unbound.

The portable [queue model](../../examples/mechanism-scaffolds/pipette/queue_contract.py)
executes the committed/speculative lifecycle subset. Its ticket identity and
prototype capacity limits are explicit modeling choices. It omits control-handler
execution, `skip_to_ctrl`, core resource contention, connectors, translation,
cycle timing and circuit cost. It supplies no hardware or speedup certificate.

Run the standalone lifecycle tests from the repository root:

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/pipette -p 'test_*.py'
```

The [primary binding](primary-binding.json) identifies the cached author-hosted
proceedings edition by hash; the corpus PDF is not duplicated here. The located
claims in the catalog were checked against sections III–IV, Figure 7 and Tables
III–IV. [Implementation obligations](implementation-contract.json) describe what
a future simulator/RTL owner must bind before an experiment.
