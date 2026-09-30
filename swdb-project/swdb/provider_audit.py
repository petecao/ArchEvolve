"""Audit tool activity from retained provider events. Updated: 2026-09-29.

The audit complements confinement; a successful audit is not a correctness claim.
Only tool inputs are treated as actions, never a provider's quoted command output.
"""

import fnmatch
import json
import re
import shlex
from pathlib import Path

from swdb import artifacts


def audit(path, kind, workspace_root, visible_files, home_root=None, login_paths=(),
          editable_files=(), network_reasons=(), guard_reasons=()):
    """Return a JSON-compatible receipt, including failures and raw-log identity."""
    path, root = Path(path), Path(workspace_root).resolve()
    visible = set(visible_files)
    directories = {"."}
    for name in visible:
        directories.update(p.as_posix() for p in Path(name).parents)
    violations, events, commands, accesses = [], 0, 0, 0
    logins = {str(Path(p).resolve()) for p in login_paths if p}
    login_names = {Path(p).name for p in logins} | {"auth.json", ".credentials.json"}

    def fail(code, detail, event):
        item = {"code": code, "reason": detail, "event": event}
        if item not in violations:
            violations.append(item)

    def file_access(name, event, *, writing=False, cwd=None):
        nonlocal accesses
        accesses += 1
        if not isinstance(name, str) or not name.strip():
            fail("invalid_file_access", "provider tool has an invalid file path", event)
            return
        # Expansion is deliberately conservative: unknown homes cannot become roots.
        if name.startswith("~") or "$" in name or "\\" in name:
            fail("external_file_access", f"provider file access outside the visible set: {name}", event)
            return
        target = (Path(cwd or root) / name).resolve()
        try:
            rel = target.relative_to(root).as_posix()
        except ValueError:
            fail("external_file_access", f"provider file access outside the workspace: {name}", event)
            return
        if rel in visible or rel in directories:
            return
        if writing and any(fnmatch.fnmatchcase(rel, p) for p in editable_files):
            return
        # Providers may make and remove synthetic tests in the build directory.
        # Any surviving source helper still fails the final workspace diff check.
        if any(part in {"build", "dist", "__pycache__", ".pytest_cache", "CMakeFiles"} for part in Path(rel).parts):
            return
        # Temporary build outputs are visible only because the provider made them.
        from swdb.provider_workspace import generated_output
        if target.exists() and generated_output(target, rel):
            return
        fail("external_file_access", f"provider file access outside the visible set: {name}", event)

    def command(value, event, cwd=None, *, depth=0):
        nonlocal commands
        if depth == 0:
            commands += 1
        if depth > 8:
            fail("unparsed_command", "provider shell command nesting cannot be audited", event)
            return
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            value = shlex.join(value)
        if not isinstance(value, str) or not value.strip():
            fail("invalid_command", "provider event has an invalid command", event)
            return
        if (any(p in value for p in logins) or any(re.search(r"(?<![\w.-])" + re.escape(n) + r"(?![\w.-])", value)
                                                  for n in login_names)
                or re.search(r"(?:\$\{?(?:CODEX_HOME|CLAUDE_CONFIG_DIR)\}?|[~/]\.codex|[~/]\.claude)", value)):
            fail("login_file_access", "provider command touches the login file or provider home", event)
        try:
            lexer = shlex.shlex(value, posix=True, punctuation_chars="();<>|&\n")
            lexer.whitespace = " \t\r"
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except ValueError:
            fail("unparsed_command", "provider command cannot be audited", event)
            return
        if re.search(r"\b(?:https?|ftp|ssh)://|\b(?:socket|urllib|requests|httpx)\s*[.(]|/dev/(?:tcp|udp)/", value):
            fail("network_command", "provider ran a forbidden network command", event)
        working = root
        if isinstance(cwd, str):
            file_access(cwd, event)
            working = (root / cwd).resolve()
        # A shell's command-string operand is executable input, unlike other
        # quoted arguments or retained stdout. Recursively audit only that
        # operand, preserving the cwd established by preceding commands.
        shells = {"sh", "bash", "zsh", "dash", "ksh"}
        # Classify executable positions, not quoted text naming a command. These
        # recognized transfer/query tools are refused even with named endpoints
        # or local-only flags; proving each tool's option semantics is outside
        # this audit's supported build/read/status subset.
        network_tools = {"curl", "wget", "pip", "pip3", "conda", "nc", "ncat", "netcat", "ssh", "scp", "sftp",
                         "rsync", "socat", "rsh", "rcp", "rlogin", "dig", "drill", "kdig", "mdig", "host",
                         "nslookup", "nsupdate", "delv", "ftp", "lftp",
                         "ncftp", "ncftpget", "ncftpput", "tftp", "atftp", "telnet", "ping", "ping6",
                         "traceroute", "traceroute6", "mtr", "whois", "aria2c", "http", "https",
                         "git-remote-http", "git-remote-https", "git-remote-ftp", "git-remote-ftps", "git-remote-ext"}
        package_managers = {"npm", "npx", "pnpm", "yarn", "cargo", "uv", "brew", "apt", "apt-get"}
        separators = {"&&", "||", ";", "|", "&", "\n"}
        def separator(token):
            return token in separators or bool(re.fullmatch(r"(?:&&|\|\||[;|&\n])+", token))

        bodies = set()
        operands = set()
        data_operands = set()
        checked_file_options = set()
        redirections = {"<", ">", ">>", "<>", ">&", "<&"}
        system_bins = tuple(Path(p).resolve() for p in ("/usr/bin", "/bin", "/usr/local/bin"))
        compiler_names = ("cc", "c++", "gcc", "g++", "clang", "clang++", "icc", "icpc", "icx", "icpx",
                          "gfortran", "flang", "flang-new", "nvcc", "hipcc", "mpicc", "mpicxx", "mpic++")
        compiler_pattern = r"(?:[\w.+-]+-)?(?:" + "|".join(re.escape(n) for n in compiler_names) + r")(?:-\d+(?:\.\d+)*)?"
        compiler_flags = ("--sysroot", "--output", "-include", "-imacros", "-isystem", "-iquote", "-idirafter",
                          "-isysroot", "-MF", "-MJ", "-I", "-L", "-B", "-F", "-o")
        compiler_outputs = {"--output", "-o", "-MF", "-MJ"}
        delegated_tools = {"xargs", "busybox", "toybox", "sudo", "doas", "timeout", "time", "ccache", "sccache",
                           "distcc", "nice", "taskset", "numactl", "stdbuf", "nohup", "setsid", "ionice", "chrt",
                           "flock", "prlimit"}
        compiler_forwarding = ("-Wp,", "-Wa,", "-Wl,", "-Xpreprocessor", "-Xclang", "-Xassembler", "-Xlinker",
                               "-Xcompiler", "-Xptxas", "-Xnvlink", "-Xcudafe", "-Xarch_", "--config", "-specs",
                               "--specs", "-wrapper", "--options-file", "-optf", "--compiler-options", "--linker-options",
                               "--ptxas-options", "-fplugin", "-fmodule-file", "-fmodule-map-file", "-ivfsoverlay")
        controlling_env = {"PATH", "BASH_ENV", "ENV", "ZDOTDIR", "FPATH", "CDPATH", "CPATH", "C_INCLUDE_PATH",
                           "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "LIBRARY_PATH", "COMPILER_PATH", "GCC_EXEC_PREFIX",
                           "HOME", "XDG_CONFIG_HOME", "LD_PRELOAD", "LD_AUDIT", "LD_LIBRARY_PATH",
                           "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH",
                           "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "NODE_OPTIONS", "NODE_PATH", "PERL5OPT",
                           "PERL5LIB", "PERLLIB", "RUBYOPT", "RUBYLIB", "GIT_EXEC_PATH", "GIT_DIR", "GIT_WORK_TREE",
                           "TAR_OPTIONS", "RIPGREP_CONFIG_PATH", "GREP_OPTIONS", "AWKPATH", "AWKLIBPATH", "CFLAGS",
                           "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "CC", "CXX", "FC", "AS", "LD", "AR",
                           "MAKEFLAGS", "GNUMAKEFLAGS", "MAKEFILES", "MFLAGS", "TMPDIR", "TMP", "TEMP",
                           "LLVM_PROFILE_FILE", "GCOV_PREFIX", "GCCDEPENDENCIES_OUTPUT", "SUNPRO_DEPENDENCIES"}

        def git_network(arguments):
            # Git can resolve a short name such as origin through configuration;
            # absence of a URL does not establish that a query is local. Global
            # options are parsed only far enough to locate the real subcommand.
            switches = {"--no-pager", "--paginate", "-p", "-P", "--bare", "--no-replace-objects",
                        "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs",
                        "--no-optional-locks", "--no-lazy-fetch", "--no-advice"}
            selectors = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix"}
            i = 0
            while i < len(arguments) and arguments[i].startswith("-"):
                option = arguments[i]
                if option == "--":
                    i += 1
                    break
                if option in selectors:
                    i += 2
                elif option in switches or any(option.startswith(s + "=") for s in selectors if s.startswith("--")):
                    i += 1
                elif option.startswith(("-C", "-c")):
                    i += 1
                elif option in {"--version", "-v", "--help", "-h"}:
                    return False
                else:
                    fail("unparsed_command", "provider git global option cannot be audited", event)
                    return False
            if i >= len(arguments):
                return False
            subcommand = arguments[i]
            if subcommand in {"clone", "fetch", "pull", "push", "submodule", "ls-remote", "fetch-pack", "send-pack",
                              "http-fetch", "http-push", "daemon", "imap-send", "send-email", "svn"}:
                return True
            if subcommand == "remote":
                i += 1
                while i < len(arguments) and arguments[i].startswith("-"):
                    if arguments[i] == "--":
                        i += 1
                        break
                    if arguments[i] not in {"-v", "--verbose"}:
                        fail("unparsed_command", "provider git remote option cannot be audited", event)
                        return False
                    i += 1
                if i >= len(arguments):
                    return False
                operation = arguments[i]
                if operation in {"update", "show", "prune"}:
                    return True
                if operation in {"set-head", "add", "get-url"}:
                    options = ({"--auto": "network", "--delete": "local"} if operation == "set-head"
                        else {"--fetch": "network", "--no-fetch": "local", "--tags": "local", "--no-tags": "local",
                              "--track": "value", "--master": "value", "--mirror": "optional"} if operation == "add"
                        else {"--push": "local", "--all": "local"})
                    i += 1
                    while i < len(arguments):
                        option = arguments[i]
                        if option == "--":
                            break
                        if option.startswith("--"):
                            spelling, equals, value = option.partition("=")
                            # Git parse-options accepts unambiguous long-option
                            # abbreviations. Unknown/ambiguous options cannot
                            # establish the absence of a remote operation.
                            matches = [name for name in options if name.startswith(spelling)]
                            if len(matches) != 1:
                                fail("unparsed_command", "provider git remote option cannot be audited", event)
                                return False
                            role = options[matches[0]]
                            if role == "network":
                                return True
                            if role == "value" and not equals:
                                i += 1
                                if i >= len(arguments):
                                    fail("unparsed_command", "provider git remote value is missing", event)
                                    return False
                            elif equals and (role == "local" or not value):
                                fail("unparsed_command", "provider git remote option value cannot be audited", event)
                                return False
                        elif option.startswith("-"):
                            letters = option[1:]
                            for offset, character in enumerate(letters):
                                if (operation == "add" and character == "f"
                                        or operation == "set-head" and character == "a"):
                                    return True
                                if operation == "add" and character in {"t", "m"}:
                                    if offset == len(letters) - 1:
                                        i += 1  # A separate branch operand is data.
                                        if i >= len(arguments):
                                            fail("unparsed_command", "provider git remote value is missing", event)
                                    break
                                if operation != "set-head" or character != "d":
                                    fail("unparsed_command", "provider git remote short option cannot be audited", event)
                                    return False
                        i += 1
                    if operation == "get-url":
                        return False
                # Only listing and URL inspection belong to the supported local
                # remote-command subset. Configuration mutations stay opaque.
                fail("unparsed_command", "provider git remote operation cannot be audited", event)
                return False
            if subcommand == "archive":
                for option in arguments[i + 1:]:
                    if option == "--":
                        break
                    spelling = option.partition("=")[0]
                    if spelling.startswith("--") and len(spelling) > 2 and "--remote".startswith(spelling):
                        return True
                fail("unparsed_command", "provider git archive invocation cannot be audited", event)
            return False

        def getent_network(arguments):
            # These NSS databases may invoke getaddrinfo/gethostbyname and DNS.
            # The service override does not establish a safe historical lookup.
            i = 0
            while i < len(arguments) and arguments[i].startswith("-"):
                option = arguments[i]
                if option == "--":
                    i += 1
                    break
                if option in {"-h", "--help", "--usage", "-V", "--version"}:
                    return False
                if option in {"-s", "--service"}:
                    i += 2
                elif option in {"-i", "--no-idn"} or option.startswith(("-s", "--service=")):
                    i += 1
                else:
                    fail("unparsed_command", "provider getent option cannot be audited", event)
                    return False
            return i < len(arguments) and arguments[i] in {"hosts", "ahosts", "ahostsv4", "ahostsv6"}

        def python_network_module(arguments):
            # Consume the supported interpreter prefix, including bundles and
            # option data, before deciding where a script's arguments begin.
            i = 0
            while i < len(arguments):
                option = arguments[i]
                if option == "--":
                    if i + 1 < len(arguments):
                        file_access(arguments[i + 1], event, cwd=working)
                    break
                if option == "-":
                    fail("unparsed_command", "provider Python stdin body cannot be audited", event)
                    break
                if not option.startswith("-"):
                    file_access(option, event, cwd=working)
                    break
                if option in {"--help", "--help-env", "--help-xoptions", "--help-all", "--version"}:
                    return False
                if option == "--check-hash-based-pycs" or option.startswith("--check-hash-based-pycs="):
                    if "=" in option:
                        mode = option.split("=", 1)[1]
                    else:
                        i += 1
                        mode = arguments[i] if i < len(arguments) else None
                    if mode not in {"default", "always", "never"}:
                        fail("unparsed_command", "provider Python hash-pyc mode cannot be audited", event)
                        return False
                elif option.startswith("--"):
                    fail("unparsed_command", "provider Python prefix option cannot be audited", event)
                    return False
                else:
                    letters = option[1:]
                    for offset, character in enumerate(letters):
                        if character == "c":
                            fail("unparsed_command", "provider interpreter inline body cannot be audited", event)
                            return False
                        if character in {"h", "V"}:
                            return False
                        if character in {"m", "W", "X"}:
                            value = letters[offset + 1:]
                            if not value:
                                i += 1
                                value = arguments[i] if i < len(arguments) else None
                            if not value:
                                fail("unparsed_command", "provider Python option value is missing", event)
                                return False
                            if character == "m":
                                return value in {"pip", "pip._internal", "http.server", "urllib.request"}
                            harmless = (value in {"ignore", "default", "error", "always", "module", "once"}
                                or re.fullmatch(r"(?:ignore|default|error|always|module|once)::(?:Warning|UserWarning|"
                                    r"DeprecationWarning|PendingDeprecationWarning|SyntaxWarning|RuntimeWarning|"
                                    r"FutureWarning|ImportWarning|UnicodeWarning|BytesWarning|ResourceWarning)", value))
                            if character == "X":
                                harmless = (value in {"dev", "utf8", "utf8=0", "utf8=1", "faulthandler", "importtime",
                                    "warn_default_encoding", "no_debug_ranges", "frozen_modules=on", "frozen_modules=off"}
                                    or re.fullmatch(r"(?:tracemalloc|int_max_str_digits)=[0-9]+|tracemalloc", value))
                            if not harmless:
                                fail("unparsed_command", "provider Python prefix value cannot be audited", event)
                                return False
                            break  # Warning/runtime data consumes the remainder of the bundle.
                        if character not in "bBdEiIOPqRsSuvx":
                            fail("unparsed_command", "provider Python short prefix cannot be audited", event)
                            return False
                i += 1
            return False

        def quiet_sed(begin, end):
            # Only this literal print-only subset has no embedded filesystem or
            # execution operation. Do not infer safety from arbitrary sed code.
            quiet, program, files = False, None, False
            i = begin
            while i < end:
                argument = tokens[i]
                if argument.isdigit() and i + 1 < end and tokens[i + 1] in redirections:
                    i += 1
                    argument = tokens[i]
                if argument in redirections:
                    i += 2  # The shell parser checks these redirections below.
                    continue
                if not files and argument in {"-n", "--quiet", "--silent"}:
                    quiet = True
                elif not files and argument in {"-e", "--expression"}:
                    i += 1
                    if i >= end or program is not None:
                        return False
                    program = tokens[i]
                    bodies.add(i)
                elif not files and argument == "--":
                    files = True
                elif not files and argument.startswith("-"):
                    return False
                elif program is None:
                    program = argument
                    bodies.add(i)
                else:
                    files = True
                    file_access(argument, event, cwd=working)
                    operands.add(i)
                i += 1
            return quiet and program is not None and bool(re.fullmatch(r"[0-9]+(?:,[0-9]+)?p", program))

        def filesystem_value(value):
            # Unknown attached options are not allowed to smuggle path syntax.
            # This is deliberately conservative, not custom-program semantics.
            return (value in {".", ".."} or value.startswith(("/", "./", "../", "~"))
                    or "/" in value or "\\" in value
                    or Path(value).suffix.lower() in {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".sh", ".json",
                        ".yaml", ".yml", ".txt", ".conf", ".ini", ".toml", ".rsp", ".list", ".profdata", ".profraw"})

        def literal_file_option(begin, end, flags, *, writing_flags=()):
            # Operand options must be checked before the generic token loop,
            # including attached forms such as --file=/outside or -f/outside.
            i = begin
            while i < end:
                argument = tokens[i]
                if argument == "--":
                    break
                for flag in flags:
                    operand = None
                    option_index = i
                    if argument == flag:
                        i += 1
                        if i >= end:
                            fail("unparsed_command", "provider utility file operand is missing", event)
                            break
                        operand = tokens[i]
                        operands.add(i)
                    elif flag.startswith("--") and argument.startswith(flag + "="):
                        operand = argument[len(flag) + 1:]
                    elif not flag.startswith("--") and argument.startswith(flag) and len(argument) > len(flag):
                        operand = argument[len(flag):]
                    if operand is not None:
                        checked_file_options.add(option_index)
                        if not operand or operand.startswith("-") or any(c in operand for c in "$`\\"):
                            fail("unparsed_command", "provider utility file operand cannot be resolved", event)
                        else:
                            file_access(operand, event, writing=flag in writing_flags, cwd=working)
                        break
                i += 1

        def grep_patterns(begin, end):
            # Regex arguments are text, including strings such as name=/path.
            # Only known pattern positions get this exemption, never file args.
            i, positional, has_pattern = begin, False, False
            while i < end:
                argument = tokens[i]
                if argument.isdigit() and i + 1 < end and tokens[i + 1] in redirections:
                    i += 1
                    argument = tokens[i]
                if argument in redirections:
                    i += 2
                    continue
                if not positional and argument == "--":
                    positional = True
                elif not positional and argument in {"-e", "--regexp"}:
                    i += 1
                    if i >= end:
                        fail("unparsed_command", "provider grep pattern operand is missing", event)
                        break
                    data_operands.add(i)
                    has_pattern = True
                elif not positional and argument.startswith(("-e", "--regexp=")):
                    data_operands.add(i)
                    has_pattern = True
                elif not positional and argument in {"-f", "--file", "--exclude-from"}:
                    has_pattern = has_pattern or argument != "--exclude-from"
                    i += 1
                elif not positional and argument.startswith(("-f", "--file=")):
                    has_pattern = True
                elif not positional and argument in {"-A", "-B", "-C", "-m", "--after-context", "--before-context",
                                                      "--context", "--max-count", "--include", "--exclude"}:
                    i += 1
                    if i < end:
                        data_operands.add(i)
                elif (positional or not argument.startswith("-")) and not has_pattern:
                    data_operands.add(i)
                    has_pattern = True
                i += 1

        def literal_compiler(begin, end):
            # This is a bounded direct-build grammar, not a compiler-driver
            # interpreter. Unknown options can consume files, start helpers, or
            # route opaque arguments even when their values contain no slash.
            switches = {"-c", "-S", "-E", "-pipe", "-pthread", "-fPIC", "-fpic", "-fPIE", "-fpie", "-pie",
                        "-shared", "-static", "-static-libgcc", "-static-libstdc++", "-rdynamic", "-r", "-s", "-w",
                        "-v", "-H", "-M", "-MM", "-MD", "-MMD", "-MP", "-MG", "-nostdinc", "-nostdinc++",
                        "-nostdlib", "-nodefaultlibs", "-nostartfiles", "-ansi", "-pedantic", "-pedantic-errors",
                        "--version", "--help", "--target-help", "-dumpversion", "-dumpfullversion", "-dumpmachine",
                        "-fopenmp", "-fopenmp-simd", "-fsyntax-only", "-fexceptions", "-fno-exceptions", "-frtti",
                        "-fno-rtti", "-ffast-math", "-fno-fast-math", "-fmath-errno", "-fno-math-errno",
                        "-funroll-loops", "-fno-unroll-loops", "-fstrict-aliasing", "-fno-strict-aliasing",
                        "-fomit-frame-pointer", "-fno-omit-frame-pointer", "-fstack-protector", "-fstack-protector-all",
                        "-fstack-protector-strong", "-fno-stack-protector", "-ffreestanding", "-fhosted",
                        "-fno-builtin", "-fsigned-char", "-funsigned-char", "-fwrapv", "-fno-wrapv"}
            scalar = r"[A-Za-z0-9_+.-]+"
            i, positional = begin, False
            while i < end:
                argument = tokens[i]
                if argument.isdigit() and i + 1 < end and tokens[i + 1] in redirections:
                    i += 1
                    argument = tokens[i]
                if argument in redirections:
                    i += 2  # Shell redirection operands are audited separately.
                    continue
                if argument == "--":
                    positional = True
                    i += 1
                    continue
                if not positional:
                    file_flag = next((f for f in compiler_flags if argument == f
                        or f.startswith("--") and argument.startswith(f + "=")
                        or not f.startswith("--") and argument.startswith(f)), None)
                    if file_flag:
                        i += 2 if argument == file_flag else 1
                        continue
                    data_flag = next((f for f in ("-D", "-U", "-x", "-l") if argument.startswith(f)), None)
                    if data_flag:
                        data = argument[len(data_flag):]
                        if not data:
                            i += 1
                            if i >= end:
                                fail("unparsed_command", "provider compiler data operand is missing", event)
                                break
                            data = tokens[i]
                            operands.add(i)
                        valid = not any(c in data for c in "$`\\\n")
                        if data_flag == "-D":
                            valid = valid and bool(re.fullmatch(r"[A-Za-z_]\w*(?:=.*)?", data, re.S))
                        elif data_flag == "-U":
                            valid = valid and bool(re.fullmatch(r"[A-Za-z_]\w*", data))
                        elif data_flag == "-l":
                            valid = valid and bool(re.fullmatch(scalar, data))
                        else:
                            valid = valid and data in {"c", "c++", "c-header", "c++-header", "cpp-output",
                                "c++-cpp-output", "assembler", "assembler-with-cpp", "cuda", "hip", "none"}
                        if not valid:
                            fail("unparsed_command", "provider compiler data operand cannot be resolved", event)
                        i += 1
                        continue
                    if argument.startswith("-") and argument != "-":
                        allowed = (argument in switches
                            or re.fullmatch(r"-O(?:[0-3gsz]|fast)?", argument)
                            or re.fullmatch(r"-g(?:[0-3]|gdb[0-3]?|dwarf-[2-5]|line-tables-only)?", argument)
                            or re.fullmatch(r"-W[A-Za-z0-9_+=.,-]+", argument)
                            or re.fullmatch(r"-std=[A-Za-z0-9_+:.\-]+", argument)
                            or re.fullmatch(r"(?:--target|-target|-march|-mtune|-mcpu|-mabi|-mfpu|-mfloat-abi|-masm)=" + scalar, argument)
                            or re.fullmatch(r"-m(?:no-)?(?:avx(?:2|512[a-z0-9]*)?|sse[0-9.]*|aes|pclmul|bmi2?|fma|f16c|popcnt|lzcnt|neon|thumb|arm|32|64)", argument)
                            or argument in {"-stdlib=libc++", "-stdlib=libstdc++", "-fopenmp=libomp", "-fopenmp=libgomp",
                                "-fopenmp=libiomp5", "-fvisibility=hidden", "-fvisibility=default", "-ffp-contract=off",
                                "-ffp-contract=on", "-ffp-contract=fast", "-fdiagnostics-color=always",
                                "-fdiagnostics-color=never", "-fdiagnostics-color=auto"}
                            or re.fullmatch(r"-fmax-errors=[0-9]+", argument))
                        if not allowed:
                            fail("unparsed_command", "provider compiler option is outside the literal build subset", event)
                        i += 1
                        continue
                if argument == "-":
                    fail("unparsed_command", "provider compiler stdin source cannot be audited", event)
                elif not argument.startswith("@"):
                    file_access(argument, event, cwd=working)
                    operands.add(i)
                i += 1

        def literal_rg(begin, end):
            # File-pattern inputs are checked separately. Every other accepted
            # option is data-only; preprocessing, config, and unknown selectors
            # cannot inherit approval merely because they begin with '-'.
            switches = {"--line-number", "--no-line-number", "--files-with-matches", "--files-without-match",
                        "--count", "--count-matches", "--ignore-case", "--case-sensitive", "--smart-case",
                        "--fixed-strings", "--word-regexp", "--line-regexp", "--invert-match", "--quiet",
                        "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs", "--files", "--stats",
                        "--json", "--text", "--multiline", "--multiline-dotall", "--pcre2", "--no-config"}
            i, positional, has_pattern = begin, False, False
            while i < end:
                argument = tokens[i]
                if argument.isdigit() and i + 1 < end and tokens[i + 1] in redirections:
                    i += 1
                    argument = tokens[i]
                if argument in redirections:
                    i += 2
                    continue
                if not positional and argument == "--":
                    positional = True
                    i += 1
                    continue
                if not positional and argument in {"-f", "--file"}:
                    has_pattern = True
                    i += 2
                    continue
                if not positional and argument.startswith(("-f", "--file=")):
                    has_pattern = True
                    i += 1
                    continue
                if not positional and argument.startswith(("-e", "--regexp=")) and argument not in {"-e", "--regexp"}:
                    pattern = argument.split("=", 1)[1] if argument.startswith("--regexp=") else argument[2:]
                    if not pattern or any(c in pattern for c in "$`\\\n"):
                        fail("unparsed_command", "provider rg data operand cannot be resolved", event)
                    data_operands.add(i)
                    has_pattern = True
                    i += 1
                    continue
                if not positional and argument in {"-e", "--regexp", "-g", "--glob", "--iglob", "-A", "-B", "-C", "-m", "-j",
                                "--after-context", "--before-context", "--context", "--max-count", "--threads"}:
                    has_pattern = has_pattern or argument in {"-e", "--regexp"}
                    i += 1
                    if i >= end or any(c in tokens[i] for c in "$`\\\n"):
                        fail("unparsed_command", "provider rg data operand cannot be resolved", event)
                    else:
                        operands.add(i)
                    i += 1
                    continue
                if not positional and argument == "--files":
                    has_pattern = True
                if not positional and argument.startswith("-") and not (argument in switches
                        or re.fullmatch(r"-[nNiIsSFwxlcvqauUP]+", argument)
                        or re.fullmatch(r"-(?:A|B|C|m|j)[0-9]+", argument)
                        or re.fullmatch(r"--(?:after-context|before-context|context|max-count|threads)=[0-9]+", argument)
                        or argument in {"--color=never", "--color=always", "--color=auto"}):
                    fail("unparsed_command", "provider rg option is outside the literal search subset", event)
                if positional or not argument.startswith("-"):
                    if has_pattern:
                        file_access(argument, event, cwd=working)
                        operands.add(i)
                    else:
                        has_pattern = True
                        data_operands.add(i)
                i += 1

        start, executable, command_index, prefix = True, None, 0, None
        # Command paths are checked as well as file-tool paths. Shell redirections
        # and relative traversal count as accesses; system executable paths do not.
        for index, token in enumerate(tokens):
            if index in bodies or index in operands:
                continue
            if separator(token):
                start, executable, prefix = True, None, None
                continue
            if (token in {"{", "}"} or token.startswith("<<")
                    or re.fullmatch(r"[();<>|&\n]+", token) and any(c in token for c in "()")
                    or "$(" in token or "`" in token):
                fail("unparsed_command", "provider shell body has unsupported dynamic syntax", event)
            if start and (token in {"<", ">", ">>", "<>"}
                          or token.isdigit() and index + 1 < len(tokens)
                          and tokens[index + 1] in {"<", ">", ">>", "<>"}):
                fail("unparsed_command", "provider shell body has an unsupported leading redirection", event)
            assignment = (start or executable in {"export", "readonly", "declare", "typeset"}) and re.fullmatch(
                r"[A-Za-z_]\w*=.*", token, re.S)
            if assignment:
                # Literal assignments and exit-status capture do not execute a
                # command. Their later use as a target still fails closed below.
                name, rhs = token.split("=", 1)
                if ("$" in rhs and rhs != "$?") or "`" in rhs:
                    fail("unparsed_command", "provider shell assignment cannot be resolved", event)
                if name in controlling_env or name.startswith("GIT_"):
                    fail("unparsed_command", "provider filesystem or execution environment override cannot be audited", event)
                if filesystem_value(rhs):
                    file_access(rhs, event, cwd=working)
                    fail("unparsed_command", "provider filesystem-bearing assignment cannot be audited", event)
                continue
            if start and Path(token).name in {"env", "exec", "command"}:
                if "/" in token and not (token.startswith("/") and any(
                        Path(token).resolve().is_relative_to(p) for p in system_bins)):
                    file_access(token, event, cwd=working)
                prefix = Path(token).name
                continue
            if start and prefix and token.startswith("-"):
                if token != "--" and not (prefix == "env" and token == "-i"):
                    fail("unparsed_command", "provider execution prefix cannot be resolved", event)
                continue
            is_executable = start
            if start:
                executable = Path(token).name
                command_index = index
                start = False
                end = next((i for i in range(index + 1, len(tokens)) if separator(tokens[i])), len(tokens))
                arguments = tokens[index + 1:end]
                if (executable in network_tools or executable == "git" and git_network(arguments)
                        or executable.startswith("git-") and git_network([executable[4:], *arguments])
                        or executable in package_managers and any(a in {"install", "add", "update", "sync"} for a in arguments)
                        or executable == "getent" and getent_network(arguments)
                        or executable == "openssl" and arguments and arguments[0] == "s_client"):
                    fail("network_command", "provider ran a forbidden network command", event)
                if executable in delegated_tools or executable == "find" and any(
                        a in {"-exec", "-execdir", "-ok", "-okdir"} for a in arguments):
                    fail("unparsed_command", "provider utility uses unsupported delegated execution", event)
                if executable in {"awk", "gawk", "mawk", "nawk"}:
                    fail("unparsed_command", "provider awk program cannot be audited", event)
                if executable == "sed" and not quiet_sed(index + 1, end):
                    fail("unparsed_command", "provider sed requires a literal quiet range-print program", event)
                if re.fullmatch(compiler_pattern, executable):
                    # Response files and driver forwarding can introduce further
                    # arguments, including file accesses. Mutable response-file
                    # contents cannot reconstruct the historical invocation.
                    if any(a.startswith("@") or a.startswith(compiler_forwarding) for a in arguments):
                        fail("unparsed_command", "provider compiler forwarded or response operands cannot be audited", event)
                    literal_compiler(index + 1, end)
                if executable in {"grep", "egrep", "fgrep", "rg"}:
                    literal_file_option(index + 1, end, ("--file", "--exclude-from", "-f"))
                    if executable != "rg":
                        grep_patterns(index + 1, end)
                    else:
                        literal_rg(index + 1, end)
                    if any(a.startswith("-") and not a.startswith(("--", "-f")) and "f" in a[1:]
                           and index + 1 + position not in data_operands
                           for position, a in enumerate(arguments[:arguments.index("--") if "--" in arguments else len(arguments)])):
                        fail("unparsed_command", "provider bundled pattern-file options cannot be audited", event)
                if executable == "wc":
                    literal_file_option(index + 1, end, ("--files0-from",))
                    if any(a == "--files0-from" or a.startswith("--files0-from=") for a in arguments):
                        fail("unparsed_command", "provider wc file-list operands cannot be audited", event)
                if executable == "git" and any(a == "-c" or a.startswith(("-c", "--config-env")) for a in arguments):
                    fail("unparsed_command", "provider git command-line configuration cannot be audited", event)
                if executable == "git":
                    literal_file_option(index + 1, end, ("--git-dir", "--work-tree", "--output", "-C"),
                                        writing_flags={"--output"})
                    if any(a.startswith(("--git-dir", "--work-tree", "-C")) for a in arguments):
                        fail("unparsed_command", "provider git filesystem selectors cannot be audited", event)
                if executable == "tar":
                    fail("unparsed_command", "provider tar invocation cannot be audited", event)
                if executable == "sort":
                    literal_file_option(index + 1, end, ("--files0-from", "--output", "-o"),
                                        writing_flags={"--output", "-o"})
                    if any(a == "--files0-from" or a.startswith("--files0-from=") for a in arguments):
                        fail("unparsed_command", "provider sort file-list operands cannot be audited", event)
                if executable == "dd":
                    for operand_index in range(index + 1, end):
                        name, equals, operand = tokens[operand_index].partition("=")
                        if equals and name in {"if", "of"}:
                            checked_file_options.add(operand_index)
                            file_access(operand, event, writing=name == "of", cwd=working)
                if executable in shells:
                    body_index = None
                    for option_index in range(index + 1, len(tokens)):
                        option = tokens[option_index]
                        if option in {"--login", "--noprofile", "--norc", "--posix"}:
                            continue
                        if (not re.fullmatch(r"-[a-zA-Z]+", option)
                                or set(option[1:]) - set("abcefhlmnprstuvxBCEHPT")):
                            break
                        if "c" in option[1:]:
                            body_index = option_index + 1
                            break
                    if body_index is None or body_index >= len(tokens) or not tokens[body_index].strip():
                        fail("unparsed_command", "provider shell command body cannot be resolved", event)
                    else:
                        bodies.add(body_index)
                        command(tokens[body_index], event, str(working), depth=depth + 1)
                elif executable in {"fish", "csh", "tcsh", "eval", "source", ".", "alias", "if", "for", "while", "until", "case",
                                    "select", "function", "coproc"}:
                    fail("unparsed_command", "provider shell body uses unsupported delegated execution", event)
                elif "$" in token or "`" in token:
                    fail("unparsed_command", "provider command target cannot be resolved", event)
                if re.fullmatch(r"(?:python|pypy|perl|ruby|php|lua|tclsh)(?:\d+(?:\.\d+)*)?"
                                r"|node(?:js)?|bun|deno|luajit|julia|R(?:script)?|pwsh|powershell", executable):
                    end = next((i for i in range(index + 1, len(tokens)) if separator(tokens[i])), len(tokens))
                    if executable.startswith(("python", "pypy")):
                        flags = "c"
                        if python_network_module(arguments):
                            fail("network_command", "provider ran a forbidden network module", event)
                    elif executable.startswith("php"):
                        flags = "rRBE"
                    elif executable.startswith("perl") or executable == "julia":
                        flags = "eE"
                    else:
                        flags = "ep" if executable in {"node", "nodejs", "bun"} else "e"
                    inline = any(t == "-" or t == "eval" or t.lower().startswith(
                        ("--eval", "--execute", "--command", "--encodedcommand", "--print"))
                        or executable in {"pwsh", "powershell"} and t.lower().startswith(("-command", "-encodedcommand", "-c", "-e"))
                        or t.startswith("-") and not t.startswith("--") and any(f in t[1:] for f in flags)
                        for t in tokens[index + 1:end])
                    if executable.startswith(("python", "pypy")):
                        inline = False  # The prefix parser distinguishes bodies from script data.
                    if inline:
                        # Encodings and language semantics are opaque here. A
                        # workspace script may run under the independent guard;
                        # inline programs cannot get a static audit approval.
                        fail("unparsed_command", "provider interpreter inline body cannot be audited", event)
            elif "$" in token or "`" in token:
                # Status reporting may consume scalar variables as data. Do not
                # treat them as filenames, or accept them for arbitrary tools.
                scalar = re.fullmatch(r"(?:\$[A-Za-z_]\w*|\$\{[A-Za-z_]\w*\}|\$\?)", token)
                end = next((i for i in range(index + 1, len(tokens)) if separator(tokens[i])), len(tokens))
                arguments = tokens[command_index + 1:end]
                numeric_test = executable in {"test", "["} and any(
                    t in {"-eq", "-ne", "-gt", "-ge", "-lt", "-le"} for t in arguments) and not any(
                    t in {"-e", "-f", "-d", "-r", "-w", "-x", "-s", "-L", "-h"} for t in arguments)
                # Exit status expands only to digits. Permit literal reporting
                # fragments around it, solely as echo/printf data, not test args.
                status_data = (executable in {"printf", "echo"} and "$?" in token
                    and token.isascii() and token.isprintable()
                    and not any(c in token.replace("$?", "") for c in "/\\~*?[]{}$`"))
                if not (status_data or scalar and (executable in {"printf", "echo"} or numeric_test)):
                    fail("unparsed_command", "provider shell argument cannot be resolved", event)
            if not is_executable and executable and re.fullmatch(compiler_pattern, executable):
                for flag in compiler_flags:
                    operand = None
                    if token == flag:
                        if index + 1 < len(tokens) and not separator(tokens[index + 1]):
                            operand = tokens[index + 1]
                            operands.add(index + 1)
                        else:
                            fail("unparsed_command", "provider compiler file operand is missing", event)
                    elif flag.startswith("--") and token.startswith(flag + "="):
                        operand = token[len(flag) + 1:]
                    elif not flag.startswith("--") and token.startswith(flag):
                        operand = token[len(flag):]
                    else:
                        continue
                    if operand is not None:
                        if (not operand or operand.startswith(("-", "=", "~")) or "=" in operand or "$" in operand
                                or "`" in operand or "\\" in operand):
                            fail("unparsed_command", "provider compiler file operand cannot be resolved", event)
                        elif not (flag in compiler_outputs and operand == "/dev/null"):
                            file_access(operand, event, writing=flag in compiler_outputs, cwd=working)
                    break
            if (not is_executable and index not in data_operands
                    and index not in checked_file_options and executable not in {"echo", "printf"}
                    and not re.fullmatch(compiler_pattern, executable or "")):
                value = token.split("=", 1)[1] if "=" in token else None
                if (value is not None and filesystem_value(value) or token.startswith("-")
                        and (filesystem_value(token) or re.search(r"^-[A-Za-z0-9_-]+(?:\.\.(?:$|/)|~)", token))):
                    if value is not None:
                        file_access(value, event, cwd=working)
                    fail("unparsed_command", "provider attached filesystem operand has unsupported semantics", event)
            candidate = token.lstrip("<>")
            if index and tokens[index - 1] in {"<", ">", ">>", "<>"}:
                if candidate not in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
                    file_access(candidate, event, writing=tokens[index - 1] != "<", cwd=working)
                continue
            if index and tokens[index - 1] == "cd":
                file_access(candidate, event, cwd=working)
                working = (working / candidate).resolve()
                continue
            if not is_executable and (index in data_operands or executable in {"echo", "printf"}):
                continue
            if candidate.startswith("/"):
                if is_executable and any(Path(candidate).resolve().is_relative_to(p) for p in system_bins):
                    continue
                if candidate in {"/dev/null", "/dev/stdout", "/dev/stderr"}:
                    continue
                file_access(candidate, event, cwd=working)
            elif candidate == ".." or candidate.startswith(("../", "~/")) or "/../" in candidate:
                file_access(candidate, event, cwd=working)
            elif (not candidate.startswith("-") and re.fullmatch(r"[\w.+@/-]+", candidate)
                  and ("/" in candidate or Path(candidate).suffix in {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".sh", ".json", ".yaml", ".el", ".graph"})):
                file_access(candidate, event, writing=bool(index and tokens[index - 1] in {">", ">>", "-o"}), cwd=working)

    def glob_access(inputs, event):
        pattern = inputs.get("pattern")
        base = inputs.get("path", ".")
        file_access(base, event)
        if not isinstance(base, str) or not base.strip():
            return
        if not isinstance(pattern, str) or not pattern.strip():
            fail("invalid_file_access", "provider Glob has an invalid pattern", event)
            return
        if pattern.startswith("~") or "$" in pattern or "\\" in pattern:
            fail("external_file_access", "provider Glob pattern cannot be resolved within the workspace", event)
            return
        prefix, wildcard = [], False
        for part in Path(pattern).parts:
            if wildcard and part == "..":
                fail("external_file_access", "provider Glob pattern has unresolved traversal", event)
                return
            wildcard = wildcard or any(c in part for c in "*?[")
            if not wildcard:
                prefix.append(part)
        # Match expansion stays inside this statically known search root. A
        # parent traversal after a wildcard cannot supply such a root.
        search = str(Path(*prefix)) if wildcard else pattern
        file_access(search, event, cwd=(root / base).resolve())

    def tool(name, inputs, event):
        if not isinstance(inputs, dict):
            fail("invalid_tool_event", "provider tool inputs cannot be audited", event)
            return
        if name == "StructuredOutput":
            # Claude's schema transport is validated by the adapter as the final
            # response; it grants no filesystem, execution, or network operation.
            return
        if name in {"Bash", "bash", "shell", "exec_command", "shell_command"}:
            command(inputs.get("command", inputs.get("cmd")), event,
                    inputs.get("cwd", inputs.get("workdir")))
            return
        if name == "Glob":
            glob_access(inputs, event)
            return
        if name in {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Grep",
                    "read_file", "write_file", "edit_file", "list_directory"}:
            key = next((k for k in ("file_path", "path", "notebook_path") if k in inputs), None)
            file_access(inputs.get(key) if key else ".", event, writing=name in {"Write", "Edit", "MultiEdit", "write_file", "edit_file"})
            return
        fail("forbidden_tool", f"provider used a forbidden or unknown tool: {name}", event)

    if not path.is_file():
        fail("missing_event_log", "provider event log is missing", 0)
    else:
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                fail("invalid_event_log", "provider event log contains an unparsed event", number)
                continue
            if not isinstance(row, dict):
                fail("invalid_event_log", "provider event log contains a non-object event", number)
                continue
            events += 1
            item = row.get("item")
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type == "command_execution":
                    command(item.get("command"), number, item.get("cwd"))
                elif item_type == "file_change":
                    changes = item.get("changes")
                    if not isinstance(changes, list):
                        fail("invalid_tool_event", "provider file changes cannot be audited", number)
                    else:
                        for change in changes:
                            file_access(change.get("path") if isinstance(change, dict) else None, number, writing=True)
                elif item_type not in {"agent_message", "reasoning", "todo_list", "error"}:
                    fail("forbidden_tool", f"provider used a forbidden tool: {item_type}", number)
            message = row.get("message")
            content = message.get("content", []) if isinstance(message, dict) else row.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool(block.get("name"), block.get("input"), number)
            if row.get("type") in {"tool_use", "tool_call"}:
                tool(row.get("name"), row.get("input", row.get("arguments")), number)
            # Provider assertions cannot authorize a tool's connection. Legitimate
            # API transport is identified by the guard's independent network trace.
            if row.get("type") in {"connection", "network_connection"}:
                fail("outbound_connection", "provider made an outbound connection outside its model API", number)
    for reason in network_reasons:
        fail("outbound_connection", str(reason), 0)
    for reason in guard_reasons:
        text = str(reason)
        if re.search(r"resource limit|workspace exceeds|tool command exceeds|memory limit|thread limit", text, re.I):
            code = "resource_limit"
        elif "outbound connection is outside" in text:
            code = "outbound_connection"
        else:
            code = "guard_violation"
        fail(code, text, 0)
    receipt = {"format": "swdb.provider-audit.v1", "state": "passed" if not violations else "failed",
               "passed": not violations, "events": events, "commands": commands, "file_accesses": accesses,
               "reasons": list(dict.fromkeys(v["reason"] for v in violations)), "violations": violations,
               "raw_log": {"path": str(path)}}
    if path.is_file():
        receipt["raw_log"].update(sha256=artifacts.file_hash(path), bytes=path.stat().st_size)
    return receipt
