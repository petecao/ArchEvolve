def why3_runtime_check(expected):
    """Prospective additional closure; never retroactive historical identity."""
    manifests = expected["why3_runtime_extension"]["inventories"]
    result = {}
    for name, wanted in manifests.items():
        root = Path(name)
        need(root.resolve(strict=True) == root and root.is_dir() and not root.is_symlink(),
             "canonical Why3 runtime root required")
        rows, directories = [], []
        for path in sorted(root.rglob("*")):
            observed = path.lstat()
            relative = str(path.relative_to(root))
            if stat.S_ISDIR(observed.st_mode):
                directories.append(relative)
            else:
                need(stat.S_ISREG(observed.st_mode) and path.resolve(strict=True) == path,
                     "Why3 runtime special/link input refused")
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1048576), b""):
                        digest.update(block)
                rows.append({"relative": relative, "bytes": observed.st_size,
                             "sha256": digest.hexdigest(), "mode": stat.S_IMODE(observed.st_mode)})
        need(rows == wanted["files"] and directories == wanted["directories"],
             "Why3 package/dependency physical membership differs")
        need(all(expected["runtime_files"].get(str(root / row["relative"])) == row["sha256"] for row in rows),
             "Why3 additional physical pins must join the existing runtime gate")
        result[name] = {"count": len(rows), "inventory_sha256":
            hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()}
    need(WHY3_ROOT in result and expected["ocaml_packages"].get("why3") == WHY3_ROOT,
         "exact prospective Why3 package binding missing")
    return result

