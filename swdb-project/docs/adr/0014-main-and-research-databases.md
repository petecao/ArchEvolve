# Two databases, one crosswalk; either may go away

Date: 2026-10-06 ET
Status: proposed (decided by Yan-Ru on 2026-10-06; no access to the main database yet)

Narrows [ADR 0002](0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md): YAML in git stays the
master copy of the research database, not of the team's kernel data.

LANL's kernel database is ArchEvolve's main database; EvolveSWDB is the research database behind
Yan-Ru's papers. They stay compatible through a crosswalk instead of a shared schema, because we
have not seen the main database and the two may later merge, or the research database may be
dropped. SWDB reads the main database through an import that keeps every main-database ID, and
contributes to it only by producing that database's own ingest inputs, never by writing its SQLite
file. Concepts the main database lacks (strategies, intrinsics, certifications, the evidence basis)
stay a separable extension. Each paper result cites a frozen research-database commit, so a merge
or a replacement never breaks its citations.

## Considered Options

- **Adopt the main database's schema now:** impossible without access, and it would lose the
  evidence basis (unknown is never false) that the research rests on.
- **Merge now into one database:** same blocker; the crosswalk becomes the migration plan when
  access arrives.
