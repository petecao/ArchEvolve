"""Method20 state design and non-promoting diagnostics, 2026-10-15 ET.

No result here is proof credit. Only the existing complete round may promote;
final all-goal/smoke and covering-wait acceptance remain independent.
"""
import hashlib
import json
import math
import re
from pathlib import Path

import goal_print as G
import hints as H
import loop as L
import staged_search as S

METHOD = 'design-focused-diagnostics-v1'
OBJECTIVES = ('cas_history', 'queue_phase', 'consumed_prefix')
FIELDS = {'relation', 'scope', 'witness', 'invalidated_by'}
PHASES = ('design_bridges', 'consumption', 'recovery')
GUIDANCE = (
    'First record your own structured state design: relation, scope, witness/lifetime, and invalidating operations for CAS history, queue phase, and consumed-prefix state. Then author local bridges. Focused results are diagnostic only, never milestones.',
    'Author consumption induction using your own saved pre-issue cursor and preserved state relations. Issuance is not consumption. Only complete checked rounds can score or promote.',
    'Recovery only: repair/remove unsupported cuts and recover the checked incumbent. No new temporary candidate. Focused diagnostics cannot change debt age, scores, or final reserve.',
)


def identity():
    return {'id': METHOD, 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def schedule(start_s, stop_s):
    plan=S.schedule(start_s,stop_s)
    return {**plan,'method':METHOD}


def phase(plan, counted_s):
    start,stop=plan['start_s'],plan['stop_s']
    if stop<=start or not all(math.isfinite(x) for x in (start,stop,counted_s)):
        raise ValueError('invalid method20 counted schedule')
    edges=(start,start+(stop-start)*.55,start+(stop-start)*.9,stop)
    i=0 if counted_s<edges[1] else 1 if counted_s<edges[2] else 2
    return {'index':i,'name':PHASES[i],'start_s':edges[i],'end_s':edges[i+1],'guidance':GUIDANCE[i]}



def rule(staged_rule):
    return staged_rule.replace('METHOD19: three counted search thirds: bridges, consumption, recovery.',
        'METHOD20: counted search phases: 55% design/bridges, 35% consumption, 10% recovery.').replace(
        'The last third permits recovery only:', 'The last phase permits recovery only:') + (
        '\n  First call record_design with your own relation/scope/witness/invalidating-operation descriptions for CAS history, queue phase, and consumed prefix; no concrete hints are supplied. '
        'focused_probe(goal) regenerates the full exact working-candidate inventory and solves only its closed target class. Every result is diagnostic only, even if all selected goals are Valid; it cannot score, promote, establish a milestone, reset debt/clock, or replace a full round. '
        'Use propose_edit for complete checked-round promotion. All generation/prover/error/design time is counted; the final reserve is unchanged.')


def record_design(state, value):
    if not isinstance(value,dict) or set(value)!=set(OBJECTIVES):
        raise ValueError('design must cover CAS history, queue phase, and consumed prefix')
    for name,row in value.items():
        if not isinstance(row,dict) or set(row)!=FIELDS or any(
            not isinstance(v,str) or not v.strip() or len(v)>4000 for v in row.values()):
            raise ValueError('each design relation needs bounded relation/scope/witness/invalidated_by text: '+name)
    report={'authority':'design_only','promoted':False,'check':identity(),'relations':value}
    (Path(state)/'state-design.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def has_design(state):
    try:
        report=json.loads((Path(state)/'state-design.json').read_text())
        return report['check']==identity() and set(report['relations'])==set(OBJECTIVES)
    except (OSError,ValueError,KeyError,TypeError):
        return False


def selection(goal):
    name=goal.get('goal','')
    if (goal.get('smoke') is not False or 'smoke' in name or goal.get('function')!='TDStep' or
            not re.fullmatch(r'typed_TDStep_[A-Za-z0-9_]+',name)):
        raise ValueError('focused target must be an ordinary TDStep goal in the fresh inventory')
    kind=H.goal_kind(name)
    tag={**G.TAGS,'requires':'@requires','call-site precondition':'@requires','terminates':'@terminates'}.get(kind)
    if tag is None:
        raise ValueError('focused target class is outside the initial closed diagnostic slice')
    # Class selection is deliberate: every generated result is retained, and no
    # member of the selected class can earn proof credit, even when all pass.
    return '-wp-fct TDStep -wp-prop='+tag


def diagnostic(rows, target, unselected):
    if sum(g.get('goal')==target for g in rows)!=1:
        raise ValueError('requested goal is missing/duplicated in the focused inventory')
    if any(g.get('smoke') is not False for g in rows):
        raise ValueError('smoke results cannot be focused proof targets')
    return {'authority':'diagnostic_only','promoted':False,'target':target,
            'selected':rows,'unselected_obligations':unselected,
            'boundary':'Selected results can depend on unchecked cuts/hints. No score, milestone, promotion or complete-proof claim. Run propose_edit for a complete checked round.'}


def _snapshot(paths):
    return {str(p):p.read_bytes() if p.is_file() else None for p in paths}


def run(out, best, target, tag, *, remaining_s, round_timeout):
    """Fresh inventory and class probe of the exact working set; no state mutation.

    The host loop accounts every generation/prover/error second. The ordinary
    verifier wrapper remains the only source of matching-clock wait exclusion.
    """
    out=Path(out)
    protected=[out/'best.json',out/'debt.json',out/'debt-events.jsonl']
    source_paths=[L.STANDIN_DIR/n for n in [L.UNIT]+L.HEADERS]
    before=_snapshot(protected+source_paths)
    S.check_inputs(L.STANDIN_DIR)
    merged=H.merge((L.STANDIN_DIR/L.UNIT).read_text(),best['hints'])
    if (Path(best['dir'])/L.UNIT).read_text()!=merged:
        raise ValueError('working candidate does not match the recorded source/hint set')
    try:
        if remaining_s()<=0:raise ValueError('search deadline before diagnostic generation')
        inventory=L.run_dir(out,'probe-inventory-'+tag,merged)
        log,status=L.verifier(out,inventory,'probe-gen',timeout=max(1,remaining_s()))
        checked=S.check_run(inventory,log,round_mode=True)
        rows=json.loads((inventory/'goals.json').read_text())+json.loads((inventory/'lemmas.json').read_text())
        matches=[g for g in rows if g.get('goal')==target]
        if len(matches)!=1:raise ValueError('target is absent/duplicated in the fresh full inventory')
        select=selection(matches[0])
        if remaining_s()<=0:raise ValueError('search deadline before focused solver')
        directory=L.run_dir(out,'probe-'+tag,merged)
        log,status=L.verifier(out,directory,'focused',timeout=max(1,remaining_s()),extra=(select,round_timeout))
        S.check_run(directory,log,round_mode=False)
        selected=json.loads((directory/'goals.json').read_text())
        selected_names={g['goal'] for g in selected}
        if not selected_names<={g['goal'] for g in rows}:
            raise ValueError('focused output contains a goal outside the fresh inventory')
        result=diagnostic(selected,target,[g['goal'] for g in rows if g['goal'] not in selected_names])
        result.update(result='diagnostic only',selection=select,dir=str(directory),inventory_dir=str(inventory),
                      generated_inventory=checked,source_sha256=hashlib.sha256(merged.encode()).hexdigest())
        (directory/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:
        if _snapshot(protected+source_paths)!=before:
            raise RuntimeError('diagnostic changed protected incumbent/debt/source state')
