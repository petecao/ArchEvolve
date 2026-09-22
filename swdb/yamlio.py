"""YAML loading with two guarantees records rely on.

1. Dates stay text: a bare `2026-09-22` is the string "2026-09-22", not a date object,
   so schemas can check it like any other string.
2. A key repeated in one mapping is an error, not a silent overwrite.
"""

import yaml

_TIMESTAMP = "tag:yaml.org,2002:timestamp"


class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != _TIMESTAMP]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _mapping_without_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_without_duplicates)


def load(path):
    """Parse one YAML file. Raises yaml.YAMLError on bad YAML or a duplicate key."""
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_Loader)
