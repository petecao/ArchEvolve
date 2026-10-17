# Closed Python runtime gate — 2026-10-16 ET

**Source-only helper, not wired into any existing entry. Root reviews the schema
and supplies guarded actual startup metadata before a successor can run.**

1. `closed_python_surface.py` consumes the coordinator's exact compact schema:
   `schema`, `surfaces`, `startup_pins`, `pth`, `interpreter`, and `absence`.
   Full inventories are not copied into this packet. Canonical JSON uses sorted
   keys, compact separators, UTF-8 and `allow_nan=False`. Entry ordering exactly
   matches the coordinator's `sorted(Path.rglob('*'))`: path-component order,
   not raw relative-string order. Every directory, regular file and known link
   contributes to digest/counts. Both full verification passes must agree.
2. Roots must be canonical real directories. A symlink needs its exact raw
   target text, strict resolved physical target and complete explicit chain.
   Resolution checks each component and refuses an unlisted hop before following
   it. File targets require size/hash; directory targets require complete
   digest/counts/bytes and currently allow no nested links. This accommodates
   the reviewed Babel data subtree without an arbitrary link exception.
3. Startup inputs include exact interpreter-chain/target bytes, source/config
   pins, the complete top-level `.pth` census and its source/line hashes.
   `.pth`, `_distutils_hack`, sitecustomize and pyvenv content are hashed, never
   executed or imported by the helper. Missing startup paths use `lexists` so a
   new dangling link also refuses. The existing no-link Why3 helper is unchanged.
4. `check_guarded_startup` requires a separate root-admitted actual receipt and
   the static metadata argument. It reads no candidate path guess. Exact
   sys.path/flags/executable/prefix/base-prefix/pycache/environment values must
   match root's guarded observation. Every path must be inside a pinned canonical
   root/descendant or an explicitly absent startup path. The executable must
   match the pinned interpreter, and prefix/pyvenv.cfg must be startup-pinned.
   The mandatory `root_receipt_bytes` argument must match its separate raw SHA
   pin and decode as exactly `{schema: root-guarded-python-startup-1, startup:
   <observed fields>}`. Receipt and physical-policy digests are separate.
   Namespace-specific cache,
   output, lock and RSS environment fields compare literally; no previous-probe
   wildcard or path substitution is admitted.
5. `cbmc_release_gate.py` keeps the unchanged method family `6.11` while
   comparing the full root-observed numeric version exactly, including a patch
   component. It uses the production locator's primary numeric capture and
   rejects malformed extensions or a different patch. Raw stdout/stderr hashes
   remain evidence. No runtime version is inferred from a deployment filename.
   Fourteen pure controls pass, including closed filesystem mutations, startup
   path/ZIP/executable/prefix/namespace refusals and exact 6.11.0 matching.

The compact coordinator metadata records four freshly scanned roots and seven
known links, with the 803-file Babel target captured separately. Its actual
sys.path flag remains false; candidate paths are explicitly unverified and are
not promoted by these helpers. Root still owns guarded observation, complete
pipeline review, new-version entry wiring and actual execution. Old initialized
V3, trace V1, production, static trace fixtures and original results remain
unchanged by this runtime slice. No child, compiler, native binary, verifier,
selected interpreter or SSH was executed by this packet's author.
