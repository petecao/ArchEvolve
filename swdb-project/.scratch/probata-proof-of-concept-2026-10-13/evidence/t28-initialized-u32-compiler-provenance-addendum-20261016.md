# Initialized-u32 compiler observation provenance timing — 2026-10-16 ET

This addendum preserves the admitted entry and plan unchanged. The selected
model, two project headers, and compiler binary are pinned before observation
and checked afterward. Complete used-header/dependency pins are first collected
after original preprocessing, then rechecked after capture. They are not a
before-preprocessing snapshot. Every subsequent AST and LLVM request consumes
the retained frozen preprocessed bytes with the separately retained probe
appended. The observation does not assume a poststore counter-load shape or
establish source/model correspondence, native execution, or proof acceptance.
