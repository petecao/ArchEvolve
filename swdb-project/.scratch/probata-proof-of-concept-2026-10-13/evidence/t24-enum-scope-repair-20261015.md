# Enum context repair after atomic review

Updated: 2026-10-15 ET. Scope: lowering and public prelaunch controls only.

Independent review reproduced a blocker in initial atomic candidate `220ef337`:
an unused local `enum Flag { Weak=0 }` could replace the later global
`enum Flag { Weak=1 }`, admitting actual weak CAS into the strong model.
The same lookup defect reproduced for an ordinary enumerator return, an enum
parameter with a different underlying type, and a global record `sizeof` that
picked an unrelated local enum. These compiler RED controls justify fixing the
shared lookup rather than only the atomic call site.

The repair refuses duplicate matching named enum contexts before cached value
reuse, and mixed enum/other type contexts before choosing an underlying type.
Anonymous value lookup also requires matching qualified type. It does not
compare AST IDs from separate parser invocations. Ambiguous contexts remain
unsupported; one unique enum retains existing value and underlying-type rules.
Atomic refusals keep their operand context and physical source location.

The recorded final compiler/native profile passes 86 cases in 23.08 seconds,
including original constant atomic C/anchor/model/naming equality and native
agreement for every construct group. The watchdog reports exit 0, peak RSS
357,416,960 bytes, no OOM and no timeout. The public profile passes 29 cases in
188.14 seconds: 17 refused proof records, stale translator rejection without a
new record, and 11 corpus cases. Its stdout exists only in the tool transcript;
the physical records and all their report hashes are independently auditable.
The fourth mixed-kind corpus case was included in the recorded final 86.

[Compact metadata and physical pointers](t24-enum-scope-repair-20261015.json)
retain the initial candidate boundary, repaired source hash, all 17 refusal
records and guarded compiler log/resources. No actual WP proof is claimed.
Fresh method pins, independent review and actual current-source replay remain
required; ticket24 stays claimed. The earlier atomic-fix metadata is historical
and is not relabeled as this repaired source.
