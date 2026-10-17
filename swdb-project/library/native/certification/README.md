# Native-CPU certification evaluator files

Created: 2026-10-05 ET (code-review fix F11).

The trusted C++ of native-CPU contract certification (ticket 75): `./` is native 1.3, `v1_4/` native
1.4 (also the evaluator side of 1.5), `v1_5/` the native 1.5 evaluator and client. The files of 1.3
and 1.4 are pinned by `library/profiles/native_bfs_tdstep.yaml` and must not change. The layout of
every certification folder, what each command version reads, and why the shared 1.5 cores live under
`library/dx100/certification/v1_5/` are in `library/dx100/certification/README.md`.
