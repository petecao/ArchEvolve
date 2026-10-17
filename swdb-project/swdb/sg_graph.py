"""GAPBS serialized graphs (`.sg`): formats, offset widths and readers.

Created 2026-10-05 ET (code review S14, F11). Original SWDB code moved out of
`swdb.bfs_protocol` (`_sg_graph`, `_sg_out_degrees`, which stay as aliases) so other modules
need no private imports, plus the one table that maps an application's GAPBS build to its
serialized format, offset width and BC `CountT`. Every value is the one the evaluator used before;
emitted graph-verification contracts are unchanged. (`swdb/dx100_witness.py` keeps its own literal:
its file hash is pinned as `parser_sha256`.)
"""
import struct
from bisect import bisect_left
from pathlib import Path

from swdb.cli import Failure

#: Serialized format -> byte width of its CSR offsets (`gapbs_sg32le`: DX100 GAPBS, `SGOffset` int32).
FORMAT_OFFSET_BYTES = {"gapbs_sg32le": 4, "gapbs_sg64le": 8}

#: Application (GAPBS build) -> its loader's serialized format, the witness contracts' input format
#: name, and BC's `CountT` (float in DX100 bc.cc, double in upstream GAPBS).
APPLICATION_GRAPHS = {
    "gapbs": {"format": "gapbs_sg64le", "input_format": "gapbs.sg64", "bc_count_type": "double"},
    "dx100-gapbs": {"format": "gapbs_sg32le", "input_format": "gapbs.sg32", "bc_count_type": "float"},
}


def application_graph(application):
    """The table row of one application, or None."""
    return APPLICATION_GRAPHS.get(application)


def application_format(application):
    row = application_graph(application)
    return row["format"] if row else None


def application_offset_bytes(application):
    """Offset width of an application's loader (8 for upstream GAPBS, 4 for DX100 GAPBS)."""
    return FORMAT_OFFSET_BYTES[APPLICATION_GRAPHS[application]["format"]]


def count_type_for_offset_bytes(offset_bytes):
    """BC `CountT` of the application whose loader uses this offset width."""
    return next(row["bc_count_type"] for row in APPLICATION_GRAPHS.values()
                if FORMAT_OFFSET_BYTES[row["format"]] == offset_bytes)


def _fail(condition, message):
    if not condition:
        raise Failure(message)


def read_graph(raw, width, *, max_vertices, max_edges):
    """Read the unweighted GAPBS binary format, including the inverse CSR of a directed graph."""
    offset_format = "i" if width == 4 else "q"
    _fail(len(raw) >= 1 + 2 * width and raw[0] in (0, 1), "invalid SG header")
    directed = bool(raw[0])
    m, n = struct.unpack_from("<" + offset_format * 2, raw, 1)
    _fail(0 < n <= max_vertices and 0 <= m <= max_edges, "SG dimensions exceed parser limits")
    block_bytes = (n + 1) * width + m * 4
    _fail(len(raw) == 1 + 2 * width + block_bytes * (2 if directed else 1), "truncated or trailing SG data")

    def csr(position):
        offsets = [item[0] for item in struct.iter_unpack("<" + offset_format, raw[position:position + (n+1)*width])]
        position += (n + 1) * width
        _fail(offsets[0] == 0 and offsets[-1] == m and all(0 <= a <= b <= m for a, b in zip(offsets, offsets[1:])),
              "invalid SG CSR offsets")
        rows = [[item[0] for item in struct.iter_unpack("<i", memoryview(raw)[position+offsets[u]*4:position+offsets[u+1]*4])]
                for u in range(n)]
        for u, row in enumerate(rows):
            _fail(all(0 <= v < n and v != u for v in row), "SG neighbor is outside graph or a self loop")
            _fail(all(a < b for a, b in zip(row, row[1:])), "SG adjacency must already be sorted and deduplicated")
        return rows

    position = 1 + 2 * width
    outgoing = csr(position)
    if directed:
        incoming = csr(position + block_bytes)
        # Both CSR blocks have exactly m distinct arcs. Membership therefore
        # shows inverse equivalence without constructing another edge list.
        for v, row in enumerate(incoming):
            for u in row:
                at = bisect_left(outgoing[u], v)
                _fail(at < len(outgoing[u]) and outgoing[u][at] == v,
                      "SG inverse adjacency does not match outgoing edges")
    return {"num_vertices": n, "directed": directed,
            "adjacency": outgoing}


def out_degrees(row, sources):
    """Out-degrees of the requested sources read from a verified SG file's CSR offsets.

    `row` names the file (`path`) and its `format` (a key of `FORMAT_OFFSET_BYTES`)."""
    width = FORMAT_OFFSET_BYTES[row["format"]] if row["format"] in FORMAT_OFFSET_BYTES else 8
    offset_format = "<" + ("i" if width == 4 else "q")
    degrees = {}
    with Path(row["path"]).open("rb") as handle:
        header = handle.read(1 + 2 * width)
        _fail(len(header) == 1 + 2 * width, "invalid SG header")
        _, n = struct.unpack_from(offset_format[0] + offset_format[1] * 2, header, 1)
        for source in sources:
            _fail(0 <= source < n, "source vertex is outside the graph")
            handle.seek(1 + 2 * width + source * width)
            pair = handle.read(2 * width)
            _fail(len(pair) == 2 * width, "truncated SG offsets")
            first, last = struct.unpack(offset_format[0] + offset_format[1] * 2, pair)
            degrees[source] = last - first
    return degrees
