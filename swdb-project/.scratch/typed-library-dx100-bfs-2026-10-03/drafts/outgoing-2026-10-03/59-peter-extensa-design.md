# Draft: Extensa-mode design note to Peter

Created: 2026-10-03 ET
Status: draft (Yan-Ru sends manually; the agent never sends)
To: Peter
Ticket: [59](../../issues/59-send-peter-extensa-design.md)

Subject: Extensa mode in SWDB: what is ported, and the license assumption

Hi Peter,

This note is about Extensa mode, the research loop I am building inside SWDB.
Everything below is on branch `yanrujhou_main`, commit `COMMIT_SHA`.

**What I ported.** I am porting four parts of Extensa (MemAcc
`af3d6d7f7a69a72facdc3b95b42e78c952f44a76`, folder `AgenticRefiner/`) into SWDB:

1. loop accounting;
2. contract-predicate runtime probes;
3. certification profiles;
4. CPU synthesis for the pack, regroup, gather and bin-drain families.

The seed library entries are pack, binning, relabeling, regrouping and gather staging.

**What I did not port.** Extensa's agent runtime, timing and speed rule are not ported. SWDB's evaluator supplies every number.

**Design and protocol.** The full list is in
`swdb-project/.scratch/typed-library-dx100-bfs-2026-10-03/extensa-design-2026-10-03.md`,
lines 35–80 (D1).

- Each campaign has one target.
- Native campaigns use scale-22 Kronecker and uniform graphs with 10 paired repetitions, because at scale 18 the baseline spread was 0.13–0.14.
- gem5 campaigns reuse the two scale-18 graphs from the first result, one run each.
- Results are labeled "single graph per class".

The protocol details are in the same file, lines 91–120 (D3, D4).

**License.** Every ported file carries `Apache-2.0 WITH LLVM-exception`, matching MemAcc's
LICENSE. That follows the assumption I recorded on 2026-10-03, lines 275–283 (D11) of the same file. Can you confirm that license, or name another? ArchEvolve has no license of its own. If you name another license, I will relabel the files listed in `swdb-project/swdb/_vendor/PROVENANCE.md` and `swdb-project/swdb/extensa/PROVENANCE.md`.

**Coming later.** A separate note will cover the "is the specification enough?" experiment, which
tests whether your v1.1 specification alone lets a coding agent rebuild the TDStep rewrite.

Thanks,
Yan-Ru
