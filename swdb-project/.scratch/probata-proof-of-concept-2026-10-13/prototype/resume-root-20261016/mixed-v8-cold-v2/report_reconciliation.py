"""2026-10-16 ET. Closed observed mixed-WP report convention reconciliation.

No proof or hypothesis is accepted. Full original proof-task bytes remain absent.
This helper only attributes two exact inventory-only goals and four exact dual
caller/callee smoke labels, preserving complete native and normal record census.
"""


def query_callsites(query, caller):
    """Check actual original query caller scope/token/line, export metadata only."""
    need(caller in ('swdb_pair_pointer_values', 'swdb_pair_pointer_wrong_identity'),
         'exact two source caller functions required')
    # Erase comments/string/character payloads while retaining every newline;
    # tokens from comments/quotes can never stand in for a real direct call.
    stripped = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                      lambda m: ''.join('\n' if c == '\n' else ' ' for c in m.group()), query, flags=re.S)
    matches = list(re.finditer(r'\b'+re.escape(caller)+r'\s*\([^;{}]*\)\s*\{', stripped))
    need(len(matches) == 1, 'unique original query caller definition required')
    start = matches[0].end(); depth = 1; end = None
    for offset in range(start, len(stripped)):
        depth += (stripped[offset] == '{')-(stripped[offset] == '}')
        if depth == 0:
            end = offset; break
    need(end is not None, 'complete original query caller body required')
    calls = []
    for callee, sid, line in zip(CONTEXT['model_names'], (18,19,20,21), (45,49,53,56)):
        sites = list(re.finditer(r'\b'+re.escape(callee)+r'\s*\(', stripped[start:end]))
        need(len(sites) == 1, 'one exact callee call inside original caller required')
        offset = start+sites[0].start()
        need(stripped.count('\n',0,offset)+1 == line, 'exact source query call line differs')
        calls.append({'caller':caller,'callee':callee,'statement_id':sid,'line':line})
    return calls


def reconcile_wp_reports(native, standard, properties, record, query):
    """Closed exact-record projection of source-defined report conventions."""
    generated = {g['goal']:g for g in native}
    peers = {g['goal']:g for g in standard}
    rows = {g['goal']:g for g in record['goals']}
    props = {p['property']:p for p in properties}
    need(len(generated) == len(native) and len(peers) == len(standard) and
         len(rows) == len(record['goals']) and len(props) == len(properties),
         'unique complete native/standard/normal-record/property IDs required')
    need(set(generated) == set(rows) and set(peers) <= set(generated),
         'complete native inventory equals normal record; standard cannot add goals')
    model = record['subject']['kind'] == 'c_model'
    ident = record['subject']['id']
    if model:
        need(ident in CONTEXT['model_names'], 'exact four model subjects required')
        extras = {f'typed_real_{ident}_{suffix}' for suffix in ('terminates','exits')}
        need(set(generated)-set(peers) == extras, 'only exact two observed CFG inventory goals may lack standard rows')
        callsites = []
    else:
        need(record['subject']['kind'] == 'library_summary' and ident in
             ('contract.fixture_pair_pointer_values','contract.fixture_pair_pointer_wrong_identity'),
             'exact two caller subjects required')
        need(set(generated) == set(peers), 'caller inventory cannot omit any standard goal')
        extras = set()
        caller = 'swdb_pair_pointer_values' if ident.endswith('_values') else 'swdb_pair_pointer_wrong_identity'
        callsites = query_callsites(query, caller)
    special = {f"typed_real_{r['callee']}_wp_smoke_dead_call_s{r['statement_id']}":r for r in callsites}
    seen = set(); inventory_only = []; dual_owner = []
    for gid, goal in generated.items():
        normal = rows[gid]
        need(normal.get('property') == goal.get('property') and
             normal.get('smoke') is goal.get('smoke'), 'every normal record binds native property/smoke role')
        if gid in extras:
            suffix = gid.rsplit('_',1)[1]
            prop = props.get(goal.get('property'))
            need(goal.get('property') == ident+'_'+suffix and goal.get('function') == ident and
                 goal.get('line') == (13 if ident.endswith('_assign') else 11) and
                 goal.get('smoke') is False and goal.get('passed') is True and
                 isinstance(goal.get('results'),list) and 'valid' in goal['results'] and
                 normal.get('function') == ident and normal.get('status') == 'valid' and
                 normal.get('solver') is None and normal.get('seconds') is None and
                 normal.get('source') == 'wp_inventory', 'exact observed inventory-only CFG status/owner required')
            need(prop is not None and prop.get('function') == ident and
                 prop.get('line') == goal['line'] and prop.get('dependencies') == [] and
                 prop.get('extern') is False and prop.get('origin') is None and prop.get('call_context') is None,
                 'inventory-only CFG property graph must remain explicit and closed')
            inventory_only.append({'goal':gid,'property':goal['property'],'function':ident,
                                   'normal_status':'valid','source':'wp_inventory'})
            continue
        peer = peers[gid]
        need(all(goal.get(k) == peer.get(k) for k in ('goal','property','line','smoke','passed')),
             'all shared native/standard nonowner fields exact')
        need(normal.get('function') == peer.get('function') and normal.get('source') == 'wp_json',
             'normal shared goal retains exact standard-report owner/provenance')
        if gid in special:
            site = special[gid]; prop = props.get(goal.get('property'))
            need(goal.get('function') == site['callee'] and peer.get('function') == site['caller'] and
                 goal.get('line') == site['line'] and goal.get('smoke') is True and
                 goal.get('passed') is True and normal.get('status') == 'valid' and
                 goal.get('property') == gid.removeprefix('typed_real_') and
                 prop is not None and prop.get('function') == site['callee'] and
                 prop.get('line') == site['line'] and prop.get('dependencies') == [] and
                 prop.get('extern') is False and prop.get('origin') is None and
                 prop.get('call_context') is None, 'exact source-callsite/caller/callee smoke ownership required')
            seen.add(gid); dual_owner.append({'goal':gid,**site})
        else:
            need(goal.get('function') == peer.get('function'), 'unlisted native/standard owner difference refused')
    need(seen == set(special), 'all four exact callee-owned caller smokes required')
    return {'complete_native_normal_record_IDs_exact':True,
            'standard_is_exact_expected_subset':True,
            'inventory_only_CFG_goals':sorted(inventory_only,key=lambda r:r['goal']),
            'exact_source_bound_dual_owner_smokes':sorted(dual_owner,key=lambda r:r['goal']),
            'scientific_or_full_task_closure_accepted':False}
