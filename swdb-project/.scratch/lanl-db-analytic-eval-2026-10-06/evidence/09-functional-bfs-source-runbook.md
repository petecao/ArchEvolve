# Fresh functional BFS read-offload source preparation

Updated: 2026-10-06 ET. Source-only preparation for ticket 09; agent-decided under Yan-Ru’s autonomous delegation, revisable. Parent owns SSH, lane leases and execution. This preparation does not claim ticket 09 or change its analytic runtime.

Use the current canonical scalar snapshot and typed-library BFS read-offload rewrite. The older provider-codex-a2 scalar redundant-store candidate is not a read-offload implementation. No old gem5 target, provider outcome, calibration or candidate is included in the new proposal. The normative library entry IDs are source/library pins; the old record `dxc_gather` is deliberately absent. Ticket 09’s implementer supplies fresh functional intrinsic identities for later counting.

The script verifies frozen scalar source, protection, header, read-offload body, contract/dependency and strict candidate 1.6 pins before creating new artifacts. It reconstructs the pinned scalar snapshot into the external runs folder, registers a fresh source ID with verification `unchecked`, obtains a public fixture package, creates the patch with `certification.create_peter_patch`, and calls public `submit` in ArchEvolve mode. The profile stays `contract_fixture`; the resulting candidate stays `unverified`. Source and profile metadata use new IDs and the producer `swdb-canonical-read-offload-preparation`, not an LLM provider. The shipped header is byte-identical to current `library/dx100/dxc_lowering.hpp`.

The v1.1 request explicitly pins source and current library content and identifies the fixture profile. Its closed schema has no separate profile/protection hash fields, so the script verifies those exact hashes immediately before submit and retains them in `source-preparation-receipt.json`. A changed source, protection, body, header, normative entry or declared procedure fails instead of selecting another pin. A prefix may be used once; preserve failed records and choose a fresh prefix on a retry.

Run in a Git-synced SWDB checkout that includes the certification fingerprint prerequisite and this script. Set the paths to the parent’s selected clean source checkout and external raw store. For a copied records store, its sibling `library` must resolve to that checkout’s current library. The script dispatches public CLI commands in one Python process to reuse the immutable parse cache; it records every argv, exit status and stdout/stderr hash. It never invokes a provider, certification or evaluator.

```bash
cd /data1/yanruj/ArchEvolve/swdb-project
PYTHONDONTWRITEBYTECODE=1 python3 .scratch/lanl-db-analytic-eval-2026-10-06/evidence/09_prepare_functional_bfs_candidate.py \
  --records records \
  --runs-dir /data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-source-20261006-a1 \
  --prefix bfs-functional-read-offload-20261006-a1
```

The script prints the receipt path and fresh candidate ID. The receipt includes exact source/profile/protection/request/candidate/header/library hashes and the full certification argv, whose raw destination is external. After verifying the source receipt and securing a parent-owned lane, execute that argv. The intended command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m swdb certify contract.bfs_read_offload \
  --candidate bfs-functional-read-offload-20261006-a1.proposal.candidate-1 \
  --records records --library library \
  --runs-dir /data/yanruj/EvolveSWDB_runs/lanl-functional-bfs-source-20261006-a1/bfs-functional-read-offload-20261006-a1/strict-certification \
  --command-version 1.6 --tile-sizes 16384,1024 --threads 4 --sources 0 \
  --mode archevolve
```

Candidate 1.6 is the strict current default, including the improved knob spelling and `_Pragma` controls. Both tile sizes and four worker threads in each run are required. A certificate is accepted only after the new candidate/source/current-library/procedure hashes match, every positive matrix cell passes, every negative control is rejected with its named attributed check, and the record store validates. Keep raw runs on mbit10 and export compact metadata only. Functional certification establishes finite strict-model correctness; counting and analytic estimation remain separate ticket 09 work, with no native speedup claim.

The prerequisite disposition and RED→GREEN procedure evidence are in `09-certification-fingerprint-redeclaration.{md,json}`. Local source-only public add → fixture-package → submit passed, with 590 copied-store records valid and all 584 original record files unchanged. The stale body-pin check refused before writes. Two CLI-option failures remain retained as fresh source-only attempts; the corrected attempt used fresh IDs. Exact evidence is in `09-functional-bfs-source-local-smoke.json`; it does not replace the pending remote strict matrix.

The first remote strict invocation (a1) stopped at argument parsing: `certify` rejects `--format json` and emits its compact JSON result by default. The corrected recipe omits that flag. Preserve the original failed argv/stdout/stderr and source receipt; a retry records the corrected argv separately while retaining the same verified candidate pins. Local public-parser RED→GREEN evidence is in `09-certify-argv-repair.json`; its intercepted dispatch does not execute certification.
