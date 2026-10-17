# Triage Labels

Updated: 2026-09-22

The skills speak in terms of five canonical triage roles. This file maps those roles to the strings used in this repo's tracker. The tracker is local Markdown, so a "label" is the value of an issue file's `**Status:**` line.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

`claimed` and `resolved` are also valid `Status:` values (see `issue-tracker.md`); they are work states, not triage roles.

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding string from this table.
