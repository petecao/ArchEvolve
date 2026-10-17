# Source-copy staging R1: exact primary mode exception, 2026-10-07 ET

**NOT RUN.** This is a distinct source-only revision of the original three-source staging driver. The parent reported read-only metadata showing the owned nonsymlink primary `/data1/yanruj/ArchEvolve` has mode 02777 while its owned `/data1/yanruj` parent is private 0700. The original driver would refuse that checkout before copying. This preparation does not independently refresh or replace that parent observation.

Selected R1 is `/private/tmp/lanl-stage-reviewed17-input-author-sources-from-git-20261007-a1-r1.py`. Its sole change is the one remote `checked()` mode assertion:

```python
assert not s.st_mode&0o022 or (p == P('/data1/yanruj/ArchEvolve') and p.parent.stat().st_uid==os.getuid() and stat.S_IMODE(p.parent.stat().st_mode)==0o700)
```

The existing absolute/canonical/nonsymlink path, owned UID, directory/regular-file type checks precede this assertion. The base is checked before the primary. The exception applies only to that exact owned primary path beneath the owned 0700 base. It does not relax destination 0700, file 0600, exclusive/no-follow creation, stable inode/returned-byte checks, or any other path's mode gate. No chmod or primary/base modification is performed.

The 613-byte complete diff is `/private/tmp/lanl17-input-author-source-staging-primary-mode-exception-20261007-r1.diff`. Reversing its single replacement reproduces the original driver byte-for-byte: 23,483 bytes, SHA `304a16b59f1110c745188c0ce671047cf3415dbd6d2baa80b5a1aaf7d7ef4bf5`. Original driver, handoff, NOTRUN preparation and construction-pin metadata remain exact.

Future invocation still requires the parent's exact lowercase 40-hex delivered revision, after the complete archives are fully delivered:

```text
python3 /private/tmp/lanl-stage-reviewed17-input-author-sources-from-git-20261007-a1-r1.py <deliveredRevision>
```

The placeholder must be substituted; no future revision is assigned. Destination remains fresh `/data1/yanruj/lanl17-input-author-source-20261007-a1/`, containing only `publication_author.py` (791f95b5…, 28,419 bytes), `index_request_author.py` (a2e69aef…, 38,266 bytes), and `passive_inventory.py` (76b86959…, 29,653 bytes). Full immutable pins, original reviews/manifests and all custody semantics remain the original CONFIG and handoff. No remote receipt fourth file is added. The local success receipt retains its original a1 path because neither original nor R1 has staged anything.

All nine Git blob pins, original explicit True seals and selected-source review checks remain exact. HEAD/yanrujhou_main/tracked-clean and C185 Git-blob equality, custody F6, fixed captured Git stderr, class/hash diagnostics, source/prior-pin rechecks, 60-second remote/120-second SSH deadlines, and 16,384-byte receipt limit are unchanged. Earlier stages, including original7a, remain unopened; original7a still needs its separate reviewed private stderr envelope for execution.

Only byte hashing, exact reversal, local/decoded-remote syntax/AST parsing and metadata writing occurred. No SSH, tests, selected import/main, actual inputs/catalog, staging, Store/public validation, science, Git mutation or worktree edit occurred. Runtime gate acceptance and source copying are not claimed. Parent full R1 source review and separate staging authorization are required before its one future execution.
