
- Don't send mails. Only prepare drafts for me.
- Be careful about disk usage. Do not run out of my disk.
- **Writing for a person** (docs, web artifacts, reports, ticket and spec text, drafts): "Write as if your reader has ADHD: assume their attention is fragile, minimize cognitive load, and never make them backtrack to understand your point. Assume your reader is intelligent but attention-constrained. Make the path to understanding as short and frictionless as possible."
- **Branch cleanup (2026-10-08):** After verifying that an agent-created development branch is fully merged into `yanrujhou_main` and no longer needed for active work or resumption, automatically delete its remote ref with a lease on its verified tip, save a recoverable snapshot and remove any idle worktree directory and Git registration, then delete its local branch without further confirmation.
