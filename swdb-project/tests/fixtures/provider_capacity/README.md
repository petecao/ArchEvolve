# Provider capacity fixtures

Created: 2026-10-05 (Eastern Time), ticket 73.

`a7-call4.stdout.txt` and `a7-call5.stdout.txt` are byte copies of the raw Codex streams of native campaign
`extensa-native-bfs-20261004-a7` calls 4 and 5 on mbit10 (sha256 `62c80ca1...` and `3463b259...`);
`a7-stderr.txt` is their common stderr. Both calls were counted as failed rewrites; ticket 73 classifies
them as transient provider unavailability (uncounted, D7).
