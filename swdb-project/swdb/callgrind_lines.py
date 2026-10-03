"""Callgrind source self costs, independently validated from ROI totals.

Updated: 2026-10-03. Format: https://valgrind.org/docs/manual/cl-format.html.
Inclusive call-edge costs are excluded, so callees are never counted twice.
"""

import re
from collections import defaultdict

from swdb.cli import Failure

METHOD = "swdb.callgrind.lines.v1"
BOUND = 2**63


def _number(text):
    if not re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+)", text):
        raise Failure("malformed Callgrind per-line number")
    value = int(text, 16 if text.startswith("0x") else 10)
    if not 0 <= value < 2**64:
        raise Failure("Callgrind position or counter exceeds 64 bits")
    return value


def parse(raw):
    """Sum exclusive counters by (file, function, line), with compression support.

    Name IDs share a namespace across fn/cfn, fl/fi/fe/cfi/cfl, and ob/cob.
    Relative positions refer to the preceding cost line, including call costs.
    A source line zero is retained as unresolved debug attribution, never a
    statement. Multipart inputs and missing line positions are refused.
    """
    events, positions = None, ["line"]
    maps = {"file": {}, "function": {}, "object": {}}
    current, previous, associated = {}, None, False
    rows = defaultdict(lambda: defaultdict(int))
    parts = 0
    for original in raw.decode(errors="strict").splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("part:"):
            parts += 1
            if parts > 1:
                raise Failure("multipart Callgrind per-line inputs are unsupported")
        elif line.startswith("positions:"):
            positions = line.split()[1:]
            if (not positions or len(set(positions)) != len(positions)
                    or "line" not in positions or set(positions) - {"instr", "bb", "line"}):
                raise Failure("Callgrind per-line output needs unique source line positions")
            previous = None
        elif line.startswith("events:"):
            if events is not None:
                raise Failure("multiple Callgrind event parts are unsupported")
            events = line.split()[1:]
            if not events or len(set(events)) != len(events):
                raise Failure("invalid Callgrind per-line event inventory")
        elif ":" in line and "=" not in line.split(":", 1)[0]:
            continue  # Header summaries are independently parsed by parse_callgrind.
        elif "=" in line:
            key, value = line.split("=", 1)
            if key == "calls":
                if associated:
                    raise Failure("Callgrind calls association lacks its cost line")
                associated = True
                continue
            if key in {"jump", "jcnd"}:
                continue
            group = ("file" if key in {"fl", "fi", "fe", "cfi", "cfl"} else
                     "function" if key in {"fn", "cfn"} else
                     "object" if key in {"ob", "cob"} else None)
            if group is None:
                raise Failure("unsupported Callgrind per-line body field: " + key)
            match = re.fullmatch(r"\(([0-9]+)\)(?:\s+(.*))?", value.strip())
            if match:
                identity, name = match.groups()
                if name is not None:
                    old = maps[group].get(identity)
                    if old is not None and old != name:
                        raise Failure("Callgrind compressed name ID was redefined")
                    maps[group][identity] = name
                if identity not in maps[group]:
                    raise Failure("undefined Callgrind compressed name ID")
                value = maps[group][identity]
            else:
                value = value.strip()
            if not value:
                raise Failure("empty Callgrind name")
            if key in {"fl", "fi", "fe"}:
                current["file"] = value
            elif key == "fn":
                current["function"] = value
        else:
            if events is None or not current.get("file") or not current.get("function"):
                raise Failure("Callgrind cost line lacks events, file or function")
            fields = line.split()
            if len(fields) < len(positions) or len(fields) > len(positions) + len(events):
                raise Failure("Callgrind per-line cost width differs from its header")
            resolved = []
            for index, value in enumerate(fields[:len(positions)]):
                if value == "*" or value.startswith(("+", "-")):
                    if previous is None:
                        raise Failure("relative Callgrind position has no preceding cost line")
                    offset = 0 if value == "*" else _number(value[1:]) * (-1 if value[0] == "-" else 1)
                    number = previous[index] + offset
                    if not 0 <= number < 2**64:
                        raise Failure("relative Callgrind position is out of range")
                else:
                    number = _number(value)
                resolved.append(number)
            previous = resolved
            counts = [_number(v) for v in fields[len(positions):]]
            counts += [0] * (len(events)-len(counts))
            if any(v >= BOUND for v in counts):
                raise Failure("Callgrind per-line counters exceed the supported bound")
            if associated:
                associated = False
                continue
            location = (current["file"], current["function"], resolved[positions.index("line")])
            for event, count in zip(events, counts):
                rows[location][event] += count
                if rows[location][event] >= BOUND:
                    raise Failure("Callgrind per-line sum exceeds the supported bound")
    if associated:
        raise Failure("Callgrind calls association lacks its cost line")
    if events is None:
        raise Failure("Callgrind per-line output lacks events")
    result = [{"path": path, "function": function, "line": line,
               "events": dict(values), "basis": "simulated"}
              for (path, function, line), values in sorted(rows.items())]
    validate(result)
    return result


def validate(rows):
    """Independent line validator; repeated metrics on distinct lines are legal."""
    if not isinstance(rows, list):
        raise Failure("per_line_memory must be a list")
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or row.get("basis") != "simulated"
                or not isinstance(row.get("path"), str) or not row["path"]
                or not isinstance(row.get("function"), str) or not row["function"]
                or type(row.get("line")) is not int or not 0 <= row["line"] < 2**64
                or not isinstance(row.get("events"), dict) or not row["events"]
                or any(not isinstance(k, str) or not k or type(v) is not int or not 0 <= v < BOUND
                       for k, v in row["events"].items())
                or not isinstance(row.get("execution", {}), dict)
                or any(not isinstance(k, str) or type(v) is not int or v < 0
                       for k, v in row.get("execution", {}).items())):
            raise Failure("invalid Callgrind per-line row")
        identity = (row["path"], row["function"], row["line"],
                    tuple(sorted(row.get("execution", {}).items())))
        if identity in seen:
            raise Failure("duplicate Callgrind per-line identity")
        seen.add(identity)
        events = row["events"]
        for miss, reference in [("D1mr", "Dr"), ("D1mw", "Dw"), ("DLmr", "D1mr"), ("DLmw", "D1mw")]:
            if miss in events and reference in events and events[miss] > events[reference]:
                raise Failure(f"Callgrind per-line {miss} exceeds {reference}")
    return rows


def in_function(name, function="TDStep"):
    """Match the scalar function and its compiler-generated OpenMP outlined body."""
    return bool(re.search(r"(?<![A-Za-z0-9_])" + re.escape(function) + r"(?=\(|[ .]|$)", name))


def validate_record(record, context):
    """Cross-field validation hook for region_profile, without remote I/O."""
    from swdb.problems import Problem
    try:
        validate(record.data.get("per_line_memory", []))
    except (Failure, TypeError, ValueError) as error:
        yield Problem(record.rel, "per_line_memory", str(error))
