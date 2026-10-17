"""2026-10-16 ET. Exact AST-extracted production bounds seam; no imports of project modules.
Do not execute _build except with inert test doubles.
"""
from dataclasses import dataclass, field

def _bounds_argument(text):
    import json
    try:
        value = json.loads(text)
    except ValueError:
        value = None
    if not isinstance(value, dict) or "threads" not in value:
        raise ValueError("--bounds is a JSON object with a threads dimension")
    return value

def _sizes(bounds):
    """{parameter: bound} from the job's bounds; threads must be 1 (threads > 1 is CIVL's, ticket 46)."""
    if not isinstance(bounds, dict):
        raise AdapterError("the cbmc adapter needs --bounds: {\"threads\": 1, \"<integer parameter>\": <size bound>}")
    if bounds.get("threads") != 1:
        raise AdapterError(f"the cbmc adapter checks one thread (threads = 1), not threads = {bounds.get('threads')} "
                           "(threads > 1: CIVL and GenMC, tickets 46 and 47)")
    sizes = {}
    for name, value in bounds.items():
        if name == "threads":
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise AdapterError(f"bound {name} must be a size (an integer >= 0) for a bounded job, not {value!r}")
        sizes[name] = value
    return sizes

def _build(self, job, entry, code, sizes, summary_job, context):
        """The harness, the stubs and the plan."""
        unit = code.interface(job.unit.function)
        rows = [c for c in entry.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")]
        if summary_job:
            chosen = [c for c in rows if c.get("proof_placement") == {"once": "self"}]
        else:
            chosen = [c for c in rows if c.get("proof_placement") == "per_candidate"]
        knobs, symbolic = self._knobs(entry, code, rows, chosen)
        if not chosen:
            raise AdapterError(f"{self.contract} has no {'once: self' if summary_job else 'per-candidate'} formal "
                               "half to check")
        clauses = tr.clauses(self.contract, chosen)
        for name in sizes:
            if not unit.scalar(name):
                raise AdapterError(f"bound {name} is not an integer parameter of {unit.function} (its size dimensions "
                                   f"are its integer parameters: {', '.join(p[0] for p in unit.parameters if not p[2])})")
        pointers = [p for p in unit.parameters if p[2]]
        cap = max(sizes.values()) if sizes else 0
        if pointers and not sizes:
            raise AdapterError(f"{unit.function} takes arrays ({', '.join(p[0] for p in pointers)}): the bounds need a "
                               "size bound on an integer parameter")
        logic = logic_of(self.library)
        setup, state, finish = (), (), ()
        if code.model is not None:                    # ticket 27: ghost state g0, then havoc the tile elements
            setup = ("swdb_dx_init();",)
            state = proof_semantics.state_draws(self.library, code.model.entry, self.defines)
            finish = ("swdb_dx_check_exit();",)
        harness, plan = tr.harness(unit, clauses, sizes=sizes, cap=cap, knobs=knobs, logic=logic, setup=setup,
                                   state=state, finish=finish,
                                   array_domains=(entry.get('proof_unit') or {}).get('array_domains'))
        drop = stub_fault()
        stubs, summaries = {}, []
        for callee in code.functions:
            if callee == job.unit.function:
                continue
            from swdb import summary_bindings
            found = self._summary(callee, accept=lambda eid, rid: summary_bindings.check(
                self, code.source, job.unit.function, callee, eid, rid, caller_bounds=job.bounds))
            if found is None:
                continue
            entry_id, data, record_id = found
            from swdb import summary_bindings
            summary_bindings.bind(self, context, code.source, job.unit.function, callee, entry_id, record_id,
                                  caller_bounds=job.bounds)
            sha = self.library.content_sha256(entry_id)
            rows_s = [c for c in data.get("clauses") or [] if isinstance(c, dict) and c.get("acsl")
                      and c.get("proof_placement") == {"once": "self"}]
            clauses_s = tr.clauses(entry_id, rows_s)
            stubs[callee] = tr.stub(code.interface(callee), code.prototypes[callee], clauses_s, entry_id, sha,
                                    logic=logic, drop=drop,
                                    array_domains=(data.get('proof_unit') or {}).get('array_domains'))
            summaries.append({"id": entry_id, "sha256": sha, "proof_record": record_id,
                              "assumes": tr.stub_assumes(clauses_s, drop)})
        unwind = cap + 1
        context["settings"].update(unwind=unwind, array_length=cap, symbolic_knobs=symbolic,
                                   summaries=[s["id"] for s in summaries])
        if summaries:
            context["pins"]["summaries"] = summaries
        return {"harness": harness, "plan": plan, "stubs": stubs, "unwind": unwind, "sizes": sizes,
                "logic": logic.block()}

@dataclass(frozen=True)
class Interface:
    """One C function as the C lowering gives it (or, for a real-valued unit, as clang's syntax tree gives it)."""
    function: str
    returns: str                     # C return type ("void" for none)
    parameters: tuple                # (name, C type, is_pointer)
    globals: tuple = ()              # (name, C type of a scalar, or None for an array)

    def pointer(self, name):
        return next((p for p in self.parameters if p[0] == name and p[2]), None)

    def scalar(self, name):
        return any(p[0] == name and not p[2] for p in self.parameters)

    def global_scalar(self, name):
        return any(g[0] == name and g[1] for g in self.globals)

    def ctype(self, name):
        found = next((p[1] for p in self.parameters if p[0] == name), None)
        return found if found is not None else next((g[1] for g in self.globals if g[0] == name), None)

    @property
    def real_valued(self):
        return is_real_type(self.returns) or any(is_real_type(p[1]) for p in self.parameters)

@dataclass
class Plan:
    """What one generated harness draws from the oracle, in order: [{name, role, ctype, bound?, range?}]."""
    draws: list = field(default_factory=list)
    capacity: int = 0
    array_domains: dict = field(default_factory=dict)

    @property
    def inputs(self):
        return len(self.draws)

