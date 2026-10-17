"""LANL table group: `kernels` and the guessed `kernel_variants` (LANL-shaped-db ticket 02).
Created 2026-10-11 ET. See `swdb/lanl.py` for what a group module provides.

`kernels.slug` is the SWDB kernel ID; `category` is the kernel's application domain when the
application states one, else NULL. Each implementation is one `kernel_variants` row (spec D3).
Rows are inserted sorted by record ID, so integer IDs follow ID order."""

ORDER = 20

SCHEMA = """
CREATE TABLE kernels (id INTEGER PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT, category TEXT);
CREATE TABLE kernel_variants (id INTEGER PRIMARY KEY, kernel_id INTEGER NOT NULL REFERENCES kernels(id),
    slug TEXT NOT NULL UNIQUE);
"""

_VARIANTS = ("table not on the slide (spec D3): one row per SWDB implementation, the working guess for "
             "the table that Validation_results.kernel_variant_id points to")
GUESSED = [("kernel_variants", "id", _VARIANTS),
           ("kernel_variants", "kernel_id", _VARIANTS + "; links to kernels.id"),
           ("kernel_variants", "slug", _VARIANTS + "; holds the SWDB implementation ID")]


def fill(rows, store):
    for record in sorted(store.of_kind("kernel"), key=lambda r: r.id):
        kernel = record.data
        application = store.get(kernel.get("application"), "application") or {}
        rows.add("kernels", {"slug": record.id, "name": kernel.get("name"), "category": application.get("domain")},
                 record.id)
    for record in sorted(store.of_kind("implementation"), key=lambda r: r.id):
        rows.add("kernel_variants", {"kernel_id": rows.id_of("kernels", record.data.get("kernel")), "slug": record.id},
                 record.id)
