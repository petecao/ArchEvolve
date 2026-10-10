"""The one shape every validation finding takes."""

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Problem:
    file: str   # path relative to the folder being checked
    field: str  # dotted path inside the record, or "-" for the whole file
    reason: str

    def __str__(self):
        return f"{self.file}: {self.field}: {self.reason}"
