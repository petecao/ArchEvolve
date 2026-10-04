# Typed library

Date: 2026-10-03 ET
Status: proposed

Amends ADR 0004: intrinsics include accelerator commands, and offload joins the strategy effects. Narrows ADR 0002: normative library YAML and buildable code stay outside the record store and SQLite until BC reuse.

One library folder holds intrinsic definitions, reference-semantics pins, lowerings, library operations and rewrite contracts. Entry hashes cover normative fields and pinned code only. Certification and review records derive evidence status and tier without changing an entry. Experimental entries become shared only through Yan-Ru’s recorded review of certified content. ArchEvolve mode accepts only shared certified entries.

## Scope and authority

Implementation follows the authorized tickets [01–37](../../.scratch/typed-library-dx100-bfs-2026-10-03/map.md). This proposed record does not assert Yan-Ru accepted the ADR or sent the team note. Human review and communication receipts remain separate.
