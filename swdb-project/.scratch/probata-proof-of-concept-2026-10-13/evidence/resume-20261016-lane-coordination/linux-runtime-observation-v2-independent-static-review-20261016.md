# Runtime observation V2 — independent static review

Date: 2026-10-16 ET. Reviewer: `caller_assess`.

Decision: **PASS for the proposed guarded runtime observation only.** No recipe, package import, native tool, compiler, verifier, solver, project import or SSH execution was performed by this review. V1 remains unexecuted historical authoring.

| Input | SHA-256 |
| --- | --- |
| `prototype/resume-root-20261016/observe_linux_runtime_v2.py` | af963a7b69cfc19a2a60d1e218bdbaaf4d520b980d4ab76a6d6d8e5741d5c7a5 |
| `prototype/resume-root-20261016/observe-linux-runtime-command-v2.json` | a82929ac883958063b543f316566971f9de4d6fc5f3fcf81fb364678b1cd5e16 |

The command embeds the exact recipe bytes and parses as the same AST. It selects the pinned venv Python through the known opam switch with `-I -B -X pycache_prefix={OUTPUT}/python-source-cache`. The recipe checks isolated/no-bytecode/no-optimization flags, exact executable path/hash, disabled user site, exact output marker/cache path, absent fresh cache before/after, and the expected RSS environment marker. It imports exactly four named third-party roots (`pytest`, `yaml`, `jsonschema`, `psutil`) and records all loaded modules with a physical `__file__`, including transitive startup/import origins, sys.path, interpreter version and prefix metadata. Output is an exclusive-create file outside source; source/proof acceptance remains false.

V2 pins the exact selected CBMC binary (`a62af25d27425610608221d79c202f993efe1d5a85cece186119bec196382995`), then invokes only its `--version` once, with stdin closed, ten-second timeout, and child environment containing only PATH `/usr/bin:/bin`, LANG C and LC_ALL C. It requires exit zero, nonempty stdout and bounded recorded stdout/stderr; the full strings and argv are retained and `proof_requested` is false. No proof input or project path is supplied to CBMC.

Precision and limits: the text limits are 4,096 Python characters per stream, not a combined 4 KiB byte cap; capture itself is not a streaming output limiter and is subject to the known-binary/ten-second/outer-resource boundary. Python `-I` suppresses Python environment and cwd/user-site search, but the selected interpreter, native loader, installed site startup/.pth behavior and known package code remain runtime TCB. The recipe records physical `__file__` bytes and spec origin; it correctly warns that frozen/builtin executed code remains interpreter TCB. A `__file__` hash is not a claim that this disk file supplied a frozen module's actual executed code, nor a full native shared-library closure. The observation does not certify arbitrary inherited native-loader environment or prove package correctness. Actual unexpected module origins/path selectors require the subsequent cold review.

Root proposes the reviewed V6 lane0 wrapper, exact c978 source context, 60-second whole worker, 180-second outer, 8 GiB RSS, one worker and 16 MiB raw allowance. Those are external admission requirements, not facts established by this static recipe review or its RSS marker assertion. Actual lane/watch-execute ownership, raw limits, process/descendant settlement, source cleanliness and retained observation-byte closure must be checked after the admitted run. The recipe makes no caller, ticket, proof, compiler, hardware or runtime-policy acceptance claim.
