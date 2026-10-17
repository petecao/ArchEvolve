"""Source fragment assembled into the controller; never independently executed."""

def bind_zlib(policy):
    import _imp
    import importlib.machinery
    if _imp.is_builtin("zlib") != 1:
        raise ValueError("exact selected built-in zlib required")
    spec = importlib.machinery.BuiltinImporter.find_spec("zlib")
    if spec is None or spec.origin != "built-in" or spec.loader is not importlib.machinery.BuiltinImporter:
        raise ValueError("exact builtin zlib loader required")
    import zlib
    if zlib.__spec__.origin != "built-in" or zlib.__spec__.loader is not importlib.machinery.BuiltinImporter or getattr(zlib, "__file__", None) is not None:
        raise ValueError("zlib import origin changed")
    paths = set()
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[-1].startswith("/") and ("libz." in fields[-1] or "/zlib." in fields[-1]):
            paths.add(fields[-1])
    observed = {"interpreter": sys.executable, "physical_interpreter": pin(Path(sys.executable).resolve(strict=True)),
        "builtin": _imp.is_builtin("zlib"), "spec_origin": zlib.__spec__.origin,
        "loader_type": type(zlib.__spec__.loader).__module__ + "." + type(zlib.__spec__.loader).__qualname__,
        "module_file": getattr(zlib, "__file__", None), "extension": None,
        "ZLIB_VERSION": zlib.ZLIB_VERSION, "ZLIB_RUNTIME_VERSION": zlib.ZLIB_RUNTIME_VERSION,
        "mapped_compression_objects": [pin(Path(path).resolve(strict=True)) for path in sorted(paths)]}
    if observed != policy["zlib_binding"]:
        raise ValueError("exact selected zlib interpreter/library binding differs")
    return zlib, observed


def lossless_recipe(adapter, *, compiler, project, raw):
    recipe = adapter.capture_recipe(compiler=compiler, project=project, raw=raw)
    caller = recipe["commands"][1]
    if caller["phase"] != "caller-ast" or caller["stdout"] != str(Path(raw) / "component/caller.ast.json"):
        raise ValueError("exact original caller AST recipe required")
    caller["stdout"] += ".gz"
    recipe["lossless_caller_stdout"] = {"codec": "gzip-single-member", "expanded_limit": 536870912,
        "retained_file_limit": STAGE_BYTES, "complete_original_json": True,
        "expanded_memory_is_not_retained_disk_bytes": True}
    return recipe


def stream_caller_ast(item, *, out, environment, remaining, bytes_used, limit, codec, zlib_module, row):
    stdout_path = Path(item["stdout"])
    stderr_path = out / "caller-ast.stderr"
    expires = time.monotonic() + remaining
    def check():
        if time.monotonic() >= expires or bytes_used() > TOTAL_BYTES - FINAL_METADATA_RESERVE:
            raise ValueError("lossless capture stage time/output allowance exceeded")
    receipt, failure = None, None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        capture = codec.Capture(zlib_module, stdout, expanded_limit=536870912, compressed_limit=STAGE_BYTES, check=check)
        process = subprocess.Popen(item["argv"], cwd=out, env=environment, stdout=subprocess.PIPE, stderr=stderr,
            start_new_session=True, preexec_fn=limit)
        try:
            os.set_blocking(process.stdout.fileno(), False)
            with selectors.DefaultSelector() as selected:
                selected.register(process.stdout, selectors.EVENT_READ)
                while True:
                    check()
                    if not selected.select(timeout=min(0.05, max(0, expires-time.monotonic()))):
                        continue
                    block = os.read(process.stdout.fileno(), codec.CHUNK)
                    if not block:
                        break
                    capture.feed(block)
            row["returncode"] = process.wait(timeout=max(0.001, expires-time.monotonic()))
            if row["returncode"] != 0:
                raise ValueError("capture phase failed: caller-ast")
            receipt = capture.finish()
        except BaseException as error:
            failure = error
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            row["returncode"] = process.wait()
        finally:
            process.stdout.close()
    row["stdout"], row["stderr"] = pin(stdout_path), pin(stderr_path)
    if failure is not None:
        raise failure
    if row["stdout"]["bytes"] != receipt["compressed_bytes"] or row["stdout"]["sha256"] != receipt["compressed_sha256"]:
        raise ValueError("physical compressed stdout differs from complete stream receipt")
    row["lossless_stdout"] = receipt
    save(out / "caller.ast.gzip.json", receipt)
    check()
