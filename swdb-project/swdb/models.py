"""C models as proof subjects: each model function the C lowering defines is proven once against its ACSL contract
(`swdb prove --summary model.<name> --adapter wp`), and every unit that uses it pins that record.

Created: 2026-10-14 ET (Probata proof of concept ticket 25; ticket 24's std::min/max/swap/copy models use the same
mechanism). Design: formal-verification map 16 items 6 and 7 ("C models proven once"). Format:
docs/reference/format-v0.4-std-models.md ("Model proof records").

- A model is named by its C function name (`std_vector_int_push_back`, `std_min_int`); its proof subject is
  `{kind: library_summary, id: model.<name>}`. Generators registered here rebuild the model's C text from the name
  alone (no C++ source needed): the headers, the types, every model it calls (whose contracts the proof uses),
  then the model itself. The text's sha256 is the model's content hash: changing the model, or any contract it
  calls, gives a new hash, and older records stop counting.
- Units: `pins(lowering, records)` gives a `pins.summaries` entry `{id: model.<name>, sha256, proof_record}` for
  each provable model the lowering uses that has a proven record at its current hash, and one `summary`
  assumption entry for each that has none (used without a proof record of its own).
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

PREFIX = "model."
HEADERS = ("#include <stdbool.h>", "#include <stddef.h>", "#include <stdint.h>", "#include <stdlib.h>")
_GENERATORS = []          # (compiled regex, fn(match) -> [(name, text)] in definition order, the model itself last)


@dataclass(frozen=True)
class ModelUnit:
    name: str              # the C function proven
    text: str              # the whole C file WP reads
    sha256: str

    @property
    def id(self):
        return PREFIX + self.name

    def write(self, folder):
        path = Path(folder) / f"{self.name}.c"
        path.write_text(self.text)
        return path


def register(pattern, generator):
    """Register a generator for model names matching `pattern` (a regex over the C name)."""
    _GENERATORS.append((re.compile(pattern), generator))


def _generators():
    from swdb import c_lowering  # noqa: F401  (registers its models on import)
    from swdb import std_models  # noqa: F401
    return _GENERATORS


def unit(name):
    """The ModelUnit of model `name` (with or without the `model.` prefix), or None when no generator knows it."""
    name = name[len(PREFIX):] if name.startswith(PREFIX) else name
    for pattern, generator in _generators():
        match = pattern.fullmatch(name)
        if not match:
            continue
        parts = generator(match)
        if not parts or parts[-1][0] != name:
            continue
        seen, texts = set(), list(HEADERS)
        for part, text in parts:
            if part not in seen:
                seen.add(part)
                texts.append(text)
        body = "\n".join(texts) + "\n"
        text = f"/* Model proof unit {PREFIX}{name} (swdb.models). Generated: do not edit. */\n" + body
        return ModelUnit(name, text, hashlib.sha256(body.encode()).hexdigest())
    return None


def provable(lowering):
    """[ModelUnit] of the model functions a lowering defines that a generator can rebuild (macros and logic skipped)."""
    found = []
    for name in lowering.models:
        model = unit(name)
        if model is not None:
            found.append(model)
    return found


def proven_record(records, model):
    """The ID of the latest proven record of `model` at its current hash in the store `records`, or None."""
    if records is None or not Path(records).is_dir():
        return None
    from swdb.store import Store
    found = []
    for record in Store(Path(records)).of_kind("proof"):
        data = record.data
        subject = data.get("subject") or {}
        if subject.get("kind") == "library_summary" and subject.get("id") == model.id and \
                data.get("verdict") == "proven" and ((data.get("pins") or {}).get("code") or {}).get("sha256") == model.sha256:
            found.append(((data.get("job") or {}).get("batch", ""), record.id))
    return sorted(found)[-1][1] if found else None


def pins(lowering, records):
    """(summaries pins, assumption entries) for the models a unit's lowering uses (see the module docstring)."""
    summaries, assumptions = [], []
    for model in provable(lowering):
        record = proven_record(records, model)
        if record is not None:
            summaries.append({"id": model.id, "sha256": model.sha256, "proof_record": record})
        else:
            assumptions.append({"kind": "summary", "reference": {"id": model.id, "sha256": model.sha256},
                                "sentence": f"The C model {model.name} is used without a proof record of its own "
                                            f"(prove it once: swdb prove --summary {model.id} --adapter wp)."})
    return summaries, assumptions
