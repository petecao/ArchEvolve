# Historical v0.1 schemas

`workload.schema.json` and `candidate-plan.schema.json` validate the retained SPARTA examples. They describe the pre-September-24 design and remain unchanged for those examples.

They **do not validate the current BFS draft-0.2 templates**. In particular:

- The new input is per statement/access and includes reuse, stride, and scoped working-set features.
- Josh's new output is hardware-request YAML with a block graph; Peter derives intrinsic specifications.
- Storage/window parameters remain open for later tuning. A fixed configuration and full software API are not prerequisites for the forward hardware request.

No replacement formal schema has been added. Align the lightweight YAML examples with Peter and LANL's forthcoming official exchange format before expanding validation machinery.
