# Hardware behavior handoff — October 6

Peter asked for the acceleration mechanism and desired hardware semantics. These sheets distinguish source-described mechanisms, observable operation contracts, conditional benefits and unresolved implementation obligations.

The pinned input is Eric's commit 1825dfd9fdbf3ad86a0c261b0e86319475fa15f9, catalog revision 0.1.10, now merged to main in PR #3. October 1 handoff files are unchanged. Earlier software certification remains bound to its original pins; executable proposals against the newer catalog require deliberate re-binding.

| BFS case | Option | Behavior description | Machine-readable contract |
|---|---|---|---|
| 1 | dx100-artifact-e4fc4af:read_execute | [Read](case-01/candidate-02/hardware-behavior.md) | [YAML](case-01/candidate-02/hardware-behavior.yaml) |
| 1 | maple-isca2022:read_assist | [Read](case-01/candidate-03/hardware-behavior.md) | [YAML](case-01/candidate-03/hardware-behavior.yaml) |
| 1 | maple-isca2022:read_execute | [Read](case-01/candidate-04/hardware-behavior.md) | [YAML](case-01/candidate-04/hardware-behavior.yaml) |
| 2 | dx100-artifact-e4fc4af:read_execute | [Read](case-02/candidate-02/hardware-behavior.md) | [YAML](case-02/candidate-02/hardware-behavior.yaml) |
| 2 | maple-isca2022:read_assist | [Read](case-02/candidate-03/hardware-behavior.md) | [YAML](case-02/candidate-03/hardware-behavior.yaml) |
| 2 | maple-isca2022:read_execute | [Read](case-02/candidate-04/hardware-behavior.md) | [YAML](case-02/candidate-04/hardware-behavior.yaml) |

Start with case 1 / candidate 2 for DX100 reads and candidate 4 for MAPLE queue supply. Candidate 3 is MAPLE LLC assistance and must retain its different result role.

[Short team guide](../../docs/hardware-behavior-handoff.md) · [Pinned catalog provenance](../../examples/received/eric-hardware-catalog.20261006.provenance.json)

No hardware execution or speedup was measured. Benefits labeled derived reasoning are hypotheses, not added source capabilities.
