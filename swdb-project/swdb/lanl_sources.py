"""LANL table group: `source_files`, `executables`, `definitions`, `data_structures`
(LANL-shaped-db ticket 03). Created 2026-10-11 ET. See `swdb/lanl.py` for what a group module
provides.

Only what records name; nothing is inferred, and an unstated value is NULL.

- `source_files`: each implementation code file and statement source (path relative to the SWDB
  home: `<application local_path>/<path>`, or `records/<path>`), and each file a source snapshot
  retains (`<artifact.path>/<path>`). One row per (kernel, path). `language` is the application's,
  but only for files a record names as code; other retained files (LICENSE, Makefile, ...) are NULL.
- `executables`: each implementation's build. The record names no binary file, so `name` is the
  implementation ID and `kind` and `path` are NULL.
- `definitions`: functions named by implementations (`function`, `run.kernel_symbols`), their
  statements, and the function regions of source snapshots; `kind` = `function`. `source_file_id`
  is NULL when no record states the function's file.
- `data_structures`: arrays named by access-pattern steps, one per (kernel, name); `kind` is the
  stated layout, NULL when it is `unknown` or the records disagree."""

ORDER = 30

SCHEMA = """
CREATE TABLE source_files (id INTEGER PRIMARY KEY, kernel_id INTEGER NOT NULL REFERENCES kernels(id),
    path TEXT NOT NULL, language TEXT, UNIQUE (kernel_id, path));
CREATE TABLE executables (id INTEGER PRIMARY KEY, kernel_id INTEGER NOT NULL REFERENCES kernels(id),
    name TEXT, kind TEXT, path TEXT);
CREATE TABLE definitions (id INTEGER PRIMARY KEY, source_file_id INTEGER REFERENCES source_files(id),
    name TEXT NOT NULL, kind TEXT NOT NULL);
CREATE TABLE data_structures (id INTEGER PRIMARY KEY, kernel_id INTEGER NOT NULL REFERENCES kernels(id),
    name TEXT NOT NULL, kind TEXT, UNIQUE (kernel_id, name));
"""

GUESSED = []


def fill(rows, store):
    files, functions, arrays = _SourceFiles(rows), _Definitions(rows), {}
    for record in sorted(store.of_kind("implementation"), key=lambda r: r.id):
        kernel = rows.id_of("kernels", record.data.get("kernel"))
        if kernel is not None:
            _implementation(rows, files, functions, record, kernel, store.application_of(record.data) or {})
            _arrays(arrays, record, kernel)
    for (kernel, name), named in arrays.items():
        # `kind` is the layout the records state; `unknown` states nothing, and records that
        # disagree leave it unknown too.
        layouts = {layout for layout, _, _ in named if layout not in (None, "unknown")}
        row = rows.add("data_structures", {"kernel_id": kernel, "name": name,
                                           "kind": layouts.pop() if len(layouts) == 1 else None},
                       *named[0][1:])
        for _, record_id, field in named[1:]:
            rows.origin("data_structures", row, record_id, field)
    for record in sorted(store.of_kind("source_snapshot"), key=lambda r: r.id):
        impl = store.get(record.data.get("implementation"), "implementation") or {}
        kernel = rows.id_of("kernels", impl.get("kernel"))
        if kernel is not None and (record.data.get("artifact") or {}).get("path"):
            _snapshot(files, functions, record, kernel, store.get(record.data.get("application"), "application") or {})


def _implementation(rows, files, functions, record, kernel, application):
    """One implementation: its code files, its build, the functions it and its statements name."""
    impl, language = record.data, application.get("language")
    code = [files.add(kernel, _code_path(c, application), language, record.id, f"code[{i}]")
            for i, c in enumerate(impl.get("code") or [])]
    if impl.get("build"):
        rows.add("executables", {"kernel_id": kernel, "name": record.id, "kind": None, "path": None},
                 record.id, "build")
    # Where each function is, as far as records state it: the format puts the kernel function
    # in code[0] (the file built); statements give their own file. Other symbols: unknown.
    placed = {}
    if impl.get("function"):
        placed[impl["function"]] = code[0] if code else None
        functions.add(placed[impl["function"]], impl["function"], record.id, "function")
    statements = (impl.get("extensions") or {}).get("statements") or {}
    if statements.get("function"):
        sources = [files.add(kernel, _code_path(a["source"], application), language, record.id,
                             f"extensions.statements.annotations[{i}].source")
                   for i, a in enumerate(statements.get("annotations") or []) if (a.get("source") or {}).get("path")]
        where = sources[0] if len(set(sources)) == 1 else None
        if placed.get(statements["function"]) is None:
            placed[statements["function"]] = where
        functions.add(where, statements["function"], record.id, "extensions.statements.function")
    for i, name in enumerate((impl.get("run") or {}).get("kernel_symbols") or []):
        functions.add(placed.get(name), name, record.id, f"run.kernel_symbols[{i}]")


def _arrays(arrays, record, kernel):
    """Collect the arrays an implementation's access-pattern steps name, keyed by (kernel, name)."""
    for i, pattern in enumerate(record.data.get("access_patterns") or []):
        for j, step in enumerate(pattern.get("steps") or []):
            array = step.get("array") or {}
            if array.get("name"):
                arrays.setdefault((kernel, array["name"]), []).append(
                    (array.get("layout"), record.id, f"access_patterns[{i}].steps[{j}].array"))


def _snapshot(files, functions, record, kernel, application):
    """One source snapshot: every retained file, and the function regions it names."""
    snapshot = record.data
    tree = snapshot["artifact"]["path"]
    code = {c.get("path") for c in (snapshot.get("context") or {}).get("code") or [] if c.get("root") == "application"}
    ids = {}
    for i, item in enumerate(snapshot["artifact"].get("files") or []):
        ids[item["path"]] = files.add(kernel, f"{tree}/{item['path']}",
                                      application.get("language") if item["path"] in code else None,
                                      record.id, f"artifact.files[{i}]")
    for i, region in enumerate(snapshot.get("regions") or []):
        if region.get("kind") == "function" and region.get("name") and region.get("path") in ids:
            functions.add(ids[region["path"]], region["name"], record.id, f"regions[{i}]")


class _SourceFiles:
    """`source_files` rows, one per (kernel, path); a path several records name gets one origin each."""

    def __init__(self, rows):
        self.rows, self.ids = rows, {}

    def add(self, kernel, path, language, record_id, field):
        """The row of `path` for `kernel`, added if new. `language` is NULL unless a record names
        the file as code of an application that states its language."""
        key = (kernel, path)
        if key not in self.ids:
            self.ids[key] = self.rows.add("source_files", {"kernel_id": kernel, "path": path, "language": language},
                                          record_id, field)
            return self.ids[key]
        self.rows.origin("source_files", self.ids[key], record_id, field)
        if language is not None:
            self.rows.con.execute("UPDATE source_files SET language = ? WHERE id = ? AND language IS NULL",
                                  (language, self.ids[key]))
        return self.ids[key]


def _code_path(code, application):
    """A code reference as a path relative to the SWDB home: `<application local_path>/<path>` for
    application code, `records/<path>` for code kept beside its record."""
    if code.get("root") == "records":
        return f"records/{code['path']}"
    local = (application.get("source") or {}).get("local_path")
    return f"{local}/{code['path']}" if local else code["path"]


class _Definitions:
    """`definitions` rows (`kind` = `function`), one per (source file, name). A function whose file
    no record states has a NULL `source_file_id` and is kept per record: nothing says that two
    such names are the same function."""

    def __init__(self, rows):
        self.rows, self.ids = rows, {}

    def add(self, source_file, name, record_id, field):
        key = (source_file, name) if source_file is not None else (None, record_id, name)
        if key in self.ids:
            self.rows.origin("definitions", self.ids[key], record_id, field)
        else:
            self.ids[key] = self.rows.add("definitions", {"source_file_id": source_file, "name": name,
                                                          "kind": "function"}, record_id, field)
        return self.ids[key]
