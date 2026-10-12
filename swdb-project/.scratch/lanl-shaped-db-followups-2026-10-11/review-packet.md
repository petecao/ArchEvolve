# Review packet: re-pinned DX100 read-offload contracts (ticket 01)

**What to do:** (1) review BFS and run one `swdb promote` for it. (2) BC can't be promoted yet:
it needs a new certification first (Mac, about 30–60 min, no gem5). (3) Decide on the BFS
`evaluated_on_target` assertion. Without that decision, both tests still fail after promotion.

Prepared 2026-10-11 23:27 ET. Read-only check of `yanrujhou_main` @ 680298a3, `swdb-project/`.
Ticket: `swdb-project/.scratch/lanl-shaped-db-followups-2026-10-11/issues/01-re-review-read-offload-contracts.md`.

---

## 1. What changed: only hash pins, no meaning

| Contract | Reviewed hash (review record) | Current hash |
|---|---|---|
| `contract.bfs_read_offload` | `867fac18…77db51` (`review.contract.bfs_read_offload.9d24483b85b4`) | `3b2d7428…ee47` |
| `contract.bc_read_offload` | `969276431…0dc9a` (`review.contract.bc_read_offload.30a3747420b3`) | `7d2edf75…0b93` |

- Only one commit has touched either file since the reviews: **87e8646e** (2026-10-10).
- `content_sha256` is the digest of the YAML (`swdb/library.py:243`). So this YAML diff is the whole change.

**BFS** (`library/rewrite_contracts/bfs_read_offload.yaml`, 2 lines):
```
-    catalog_sha256: adf17f3e…72fb0      (provenance.<pattern>.catalog_sha256)
+    catalog_sha256: 7adeb7f9…5b85d
-    sha256: adf17f3e…72fb0              (provenance.catalog.sha256)
+    sha256: 7adeb7f9…5b85d
```
**BC** (`library/rewrite_contracts/bc_read_offload.yaml`, 3 lines): the same two catalog lines, plus
```
   derived_from: id: contract.bfs_read_offload
-    content_sha256: 867fac18…77db51
+    content_sha256: 3b2d7428…ee47       (follows the BFS re-pin)
```
Unchanged in both: rewrite, clauses, controls, knobs, guards, `design: dx100-artifact-e4fc4af`,
`revision: e4fc4afd…`, `claim_ids`.

**What changed in the pinned catalog** (`catalog/hardware-v0.1.yaml`: `adf17f…` = a8710cc2,
2026-10-01; `7adeb7…` = Eric's 4849bcdc, 2026-10-07):
- The 5 cited claims are **byte-identical** (checked by parsing YAML): `dxc-gather`,
  `dxc-range`, `dxc-stream`, `dxc-completion`, `dxc-byte-offset-domain`.
- The `dx100-artifact-e4fc4af` design gains only:
  - 8 `internal_mechanisms` entries, all `status: described` (prose about the public model: admission, grouping, slice cycle, …)
  - 4 new source refs (`dx100-tables-header`, `dx100-maa-header`, `dx100-cache-port`, `dx100-memory-port`)
- Everything else in the catalog diff is other designs (Azul, Telos, SVR, Triangel, …).

The same commit also re-pinned the 20 intrinsic and lowering YAMLs. Those diffs are catalog-sha lines only.
They change the dependency closure, which is why old certifications stop counting.

**Verdict: as you expected, it's a hardware-catalog re-pin only. No normative change.**

---

## 2. Which certification covers each current hash

`current_certification()` (`swdb/library.py:281`) needs **both** the entry hash and the full
dependency closure to match the current library.

| Contract | Current certification | Current state |
|---|---|---|
| BFS | **`certification.df1986d8f0d64a28b19fd23ae672055c`** (e2d28a7e): procedure 1.7, mbit10 node 0, 10/10 cells, 20 controls, `verdict: certified`, `evidence_basis: simulated` (strict functional model, not gem5) | `experimental` / `certified` |
| BC | **none.** Its two certifications (`1e389a95…` 1.0, `1e424fce…` 1.6) pin `969276…` and the old BFS/intrinsic hashes | `experimental` / `draft` |

The 7 older BFS certifications all pin `867fac…`, so none of them counts now.

**What BC needs:** a new candidate certification under the current default procedure (1.7):
```bash
cd swdb-project
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m swdb certify contract.bc_read_offload \
  --snapshot bc-dx100-scalar-only-20261003-a1.source \
  --patch library/dx100/bc-forward-pass.patch \
  --tile-sizes 16384,1024 --threads 4 --sources 0 \
  --runs-dir <outside the repo, e.g. $TMPDIR/bc-cert17>
```
- **Where:** the Mac works. The 1.6 BC certification (`1e424fce`) ran on `YanRus-Mac-Studio`
  with `/opt/homebrew/bin/g++-16`. mbit10 also works (BFS 1.7 took 35 min there, 10:51–11:26 ET).
- **gem5:** none. It is the strict functional model, so ADR 0013 is fine with it.
- **Cost:** 10 matrix cells plus about 28 controls. Expect about 30–60 min. That's an estimate: no BC 1.7 run exists yet.
- **What it writes:** a canonical `records/certifications/certification.<uuid>.yaml`. That needs your
  go-ahead, the same as the BFS run did (issue 12, 2026-10-10 note).
- **Does `swdb promote` refuse without it?** Yes. Today it stops at
  `promotion requires certification for current content; status is draft` (`swdb/library.py:668`).
  It would also stop at `no current passing certification receipt` (`:679`).
- **Order:** BC's dependency closure includes `contract.bfs_read_offload@3b2d7428…`, which already matches. So BC can be certified now, before or after BFS is promoted.

---

## 3. Commands you run (in dependency order)

There is **no `--dry-run`**. `promote` validates the library, then writes one file:
`records/reviews/review.<id>.<12 hex>.yaml`. It holds the target `{id, content_sha256}`,
`reviewer: Yan-Ru Jhou`, `reviewed_at`, `evidence` = every current certified receipt, and
provenance `human_report`. It does not commit to git. Run it from the main checkout, in `swdb-project/`.

```bash
cd swdb-project
# 1. BFS (parent). Evidence will be [certification.df1986d8f0d64a28b19fd23ae672055c]
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m swdb promote contract.bfs_read_offload

# 2. BC: only after the certify run in section 2 lands a certified record
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m swdb promote contract.bc_read_offload
```
- Optional: `--review-document <repo path>` puts this packet's path in the record.
- `--reviewer` defaults to `Yan-Ru Jhou`. Leave `--performed-by` unset so the record says a human did the review.
- Promotion order doesn't matter to the code: tier is per entry. Parent first is just tidy.
- After both: `git add records/reviews/ records/certifications/` and commit.

---

## 4. Will the two tests pass after promotion? **No, not with promotion alone.**

Both tests also assert **`contract.bfs_read_offload` status == `evaluated_on_target`**:
- `tests/test_library_index.py:81`: `parent["tier"] == "shared" and parent["status"] == "evaluated_on_target"`
- `tests/test_bc_certification.py:95`: `library.state(parent) == {'tier': 'shared', 'status': 'evaluated_on_target'}`

**Why it fails:** `evaluated_on_target` comes only from a target evaluation whose proposal pins
the entry's **current** hash and closure (`swdb/library.py:530–545`). The old one is gem5
`typed-library-bfs-gem5-20261003-a2`, and its proposal pins `867fac…`. No proposal or evaluation
pins `3b2d7428…`. So after promotion, BFS = `{shared, certified}`.

| Assertion | After BFS promote only | After BC cert + both promotes |
|---|---|---|
| BC tier `shared` (index :79, bc :94) | fail (BC experimental) | **pass** (BC certified) |
| BFS tier `shared` | pass | pass |
| BFS status `evaluated_on_target` | **fail** | **fail** |
| Everything else (clauses, deps, citation hash, validate) | already passes | passes |

**Two ways out. Your call:**
- **A. Re-run BFS on gem5 with current pins.** That means a new proposal and an Extensa-mode gem5 timed run on mbit10.
  The last one took about 1 h of gem5 (`host_wall_s` 2473 for the timed stage alone). ADR 0013 allows it in
  Extensa mode only, never in ArchEvolve mode.
- **B. Relax the two assertions** to `status in {'certified', 'evaluated_on_target'}`. That's what the BC line
  already does. A re-pin is supposed to drop target status, and the comment can say so. It's a
  small test edit inside `swdb-project/` (a code change, so it needs your approval).

---

## Before you sign: checklist
- [ ] Diff above is pin-only (catalog sha + BC `derived_from` hash).
- [ ] Cited catalog claims are unchanged. The added DX100 text is descriptive only.
- [ ] BFS evidence `certification.df1986d8…` is procedure 1.7, strict functional, certified.
- [ ] Approve the BC certify run (Mac) → then promote BC.
- [ ] Pick A or B for `evaluated_on_target`.
