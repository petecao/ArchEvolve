# LANL main database: preparation notes

Date: 2026-10-06 (Eastern Time)
Updated: 2026-10-09 ET (§5 rule 1 points to the access layer); 2026-10-06 ET (ticket 03: versioned crosswalk v0 and validation command)
Status: notes only. Nobody has contacted LANL, and we have no access to their database or repository.
Source: the LANL slides in the ArchEvolve overview deck dated 10/6/2026 (slides 7–12), and the
team meeting notes in `docs/meeting-2026-09-24.md` at the ArchEvolve root (branch `yanrujhou_main`).

## 1. Our position

- **LANL's database is the ArchEvolve main database.** Sumathi and Kyle own it.
- **SWDB is the research database** behind Yan-Ru's paper. It stays YAML in git
  ([ADR 0002](../../docs/adr/0002-yaml-in-git-is-the-master-copy-sqlite-is-generated.md)).
- **The two must stay compatible, and SWDB must be able to read LANL's database as the main one.**
- **Either database may go away later.** The two may merge into one, or SWDB may be dropped in
  favor of LANL's. Every design choice below keeps both outcomes cheap.

## 2. What the slides tell us

1. **Build:** `database/schema.sql` defines the tables; `database/ingest.py` fills `bootstrap.sqlite`
   from a kernels repo (`include/*.hpp`, `src/*.cpp`, `app/*_benchmark.cpp`,
   `database/openmc-kernels.json`). Like SWDB, their SQLite is generated from source files.
2. **Tables:** kernel information, source files, definitions, hardware details, run configs,
   performance metrics, data structures, executables. Semantic search adds `code_chunks` (one per
   class, function, struct or enum) and `embeddings` (blob, model name, dimension), filled by
   `database/generate_embeddings.py`.
3. **Measurements:** `perf stat` metrics with the build name, stored in the database and in CSV.
   Initial benchmarks ran on NVIDIA Grace and Intel Sapphire Rapids.
4. **Agent access:** an MCP server with tools to query the database, benchmark kernels, collect and
   analyze perf stats, and sweep a kernel's parameters.
5. **Content:** 80+ proxy kernels from fusion energy (OpenMC, Geant4, XSBench, RSBench) and nuclear
   fuel qualification codes.

## 3. What to ask LANL for, when we contact them

Ranked; the first item unblocks most of the rest.

1. **Read access to the kernels repo** (`schema.sql`, `ingest.py`, `openmc-kernels.json`). Their
   database is generated from it, so the repo shows the rules; the `.sqlite` file alone does not.
2. **Their ID scheme.** Are kernel and run IDs stable across rebuilds of `bootstrap.sqlite`?
3. **The long-term format.** Is SQLite the official format, or is the official exchange format
   (expected from Sumathi and Kyle, per the 2026-09-24 meeting notes) something else?
4. **How outside work enters the main database:** a pull request to the kernels repo followed by
   their ingest, or direct writes.
5. **The MCP tool list with signatures**, so SWDB could offer the same tools over its own records.

Later questions:

- What scope do performance metrics cover: the whole run, or the kernel's region of interest?
- How do they record hardware details, and do they plan accelerator templates?
- Which embedding model do they use, and do they re-embed when it changes?
- What license covers the extracted kernels?
- Do they plan an evaluator, and in what form?

## 4. Draft mapping (unverified: built from slide pictures only)

The versioned, machine-readable draft is
[lanl-crosswalk-v0.yaml](../../docs/compatibility/lanl-crosswalk-v0.yaml), with its
[small schema](../../schemas/compatibility/main_crosswalk.schema.json) and
[format and validation instructions](../../docs/compatibility/README.md).
It covers the ten table labels and visible field descriptions in slides 8–9 with
25 mapping rows, plus 19 separable extension concepts. Every row is `unverified`
and cites slide 8 or 9. Labels are separate from SQL identifiers: unseen identifiers
stay null, and an empty destination list explicitly means no counterpart.

The original overview PDF was inspected read-only; the crosswalk pins its filename,
date and SHA-256. This draft does not claim coverage of fields absent from the slides
or verified absence of extension concepts from LANL's unseen schema.

From `swdb-project/`, check it with:

```sh
python -m swdb validate --crosswalk docs/compatibility/lanl-crosswalk-v0.yaml
```

| LANL table | SWDB record kind | Gap |
|---|---|---|
| Kernel information | `kernel` (+ `application`) | none known |
| Source files, definitions, executables | `source_snapshot`, `implementation` | SWDB keeps no per-definition rows |
| Hardware details | `machine` | host specs only; accelerator templates belong to the hardware database |
| Run configs + performance metrics | `workload`/`input` + `profile` (basis `measured`) | see gap 1 in section 6 |
| Data structures, `code_chunks`, `embeddings` | none | use their search through the MCP server instead of copying it |

SWDB record kinds with no LANL counterpart: strategies, intrinsics, candidates, certifications,
evaluations, and the evidence basis on every metric (`measured`, `simulated`, `inferred`, ...;
unknown is never false).

## 5. Design rules that keep a merge or a replacement cheap

1. **One access layer.** Tools read records through one interface, so a different database means a
   new adapter, not edits across tools. Done in ticket 02: [`swdb/access.py`](../../swdb/access.py)
   owns record reads, record copies and generated-index SQLite access; see the access-interface
   section of [`docs/reference/database.md`](../../docs/reference/database.md).
2. **Both IDs on every record.** An imported record keeps its LANL ID; an exported row keeps its
   SWDB ID.
3. **SWDB-only concepts are a separable extension.** Strategies, intrinsics, certifications and the
   evidence basis travel as extra tables we can propose to LANL, or stay research-only.
4. **A round-trip test from day one.** Import, export, their ingest, import again: same records.
5. **Paper results cite a frozen snapshot.** Each result names an SWDB git commit, so a later merge
   or replacement does not break the paper's citations.

## 6. Gaps already visible

1. **perf stat needs hardware counters.** On mbit10, account `yanruj` has none
   (`perf_event_paranoid` = 4, checked 2026-09-22), so SWDB cannot produce rows like theirs there.
   Wall time only, unless that changes.
2. **"Hardware details" are host specs.** The accelerator templates (cache hierarchies,
   scratchpads, memory technologies) belong to the separate Hardware Database on slide 2, which
   Eric's catalog (`catalog/hardware-v0.1.yaml` at the ArchEvolve root) seeds today.
3. **No kernel overlap yet.** SWDB holds GAP graph kernels; LANL holds fusion and nuclear kernels.
   XSBench's cross-section lookups are random, indirect memory accesses, the access type DX100
   targets. It might bridge the two sets; check after we see their records.
