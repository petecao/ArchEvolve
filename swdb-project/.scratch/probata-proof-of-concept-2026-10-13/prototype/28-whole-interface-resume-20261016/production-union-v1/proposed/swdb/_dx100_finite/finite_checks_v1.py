"""2026-10-16 ET. Closed finite harness/result policy; all execution is external."""
import json
import re

REACH='swdb_reach.finite_owned_entry'
NORMAL='finite.trace.normal_return'
FUNCTION='dwe_finite_trace'
CANDIDATE_FAILURES=frozenset(('finite-event-property','finite-pending-property','finite-critical-pending-store',
    'finite-object-lifetime-pending','finite-ready-relation','finite-ready-visible','tile-ownership','pending-tile-write',
    'pending-tile-read','store-footprint-cpu-access','same-thread-read-footprint-write'))
CAPACITY_FAILURES=frozenset(('node-capacity','node-capacity-domain','evaluation-step-capacity','evaluation-stack-capacity',
    'memory-event-capacity','history-capacity','command-history-capacity','action-capacity','tile-image-capacity',
    'tile-image-capacity-domain','whole-choice-capacity','whole-choice-domain','swdb.oracle_capacity'))
class Refused(ValueError):pass

def need(ok,message):
    if not ok:raise Refused(message)

def strict(raw):
    def pairs(items):
        result={}
        for key,value in items:need(key not in result,'duplicate verifier JSON key');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite verifier JSON')))

def native_override():
    # The fresh process terminates at a failed property. No longjmp or destructor claim.
    return r'''
#if defined(SWDB_NATIVE)
#undef SWDB_CHECK
#undef SWDB_PROP
#undef SWDB_ASSUME
#undef SWDB_REACH
#undef SWDB_MODEL_REQUIRE
static void dwe_fatal(const char *name,const char *function,unsigned line) { printf(" fail=%s origin_function=%s origin_line=%u end=check\n",name,function,line); fflush(stdout); _Exit(0); }
#define SWDB_CHECK(c,n) do { if(!(c)) dwe_fatal(n,__func__,__LINE__); } while(0)
#define SWDB_PROP(c,n) SWDB_CHECK(c,n)
#define SWDB_ASSUME(c) do { if(!(c)) { printf(" end=infeasible\n"); fflush(stdout); _Exit(0); } } while(0)
#define SWDB_REACH(n) printf(" reach=%s",n)
#define SWDB_MODEL_REQUIRE(c,n) SWDB_CHECK(c,n)
#endif
'''

def harness(draw_count):
    need(type(draw_count) is int and 1<=draw_count<=256,'bounded complete independent draw rows required')
    return r'''
static void swdb_run(void) {
  uint64_t result=dwe_finite_trace();
  SWDB_PROP(result==0,"finite.trace.normal_return");
}
int main(void) {
  long long oracle[@N@];
#if defined(SWDB_NATIVE)
  for(unsigned i=0;i<@N@u;++i) if(scanf("%lld",&oracle[i])!=1) return 65;
  int ch; do { ch=getchar(); } while(ch==' ' || ch=='\t' || ch=='\r');
  if(ch!='\n' && ch!=EOF) return 65;
  while((ch=getchar())!=EOF) if(ch!=' ' && ch!='\t' && ch!='\r' && ch!='\n') return 65;
  printf("run 0:");
#endif
  swdb_oracle=oracle; swdb_oracle_n=@N@; swdb_oracle_next=0;
  swdb_run();
  SWDB_CHECK(swdb_oracle_next==@N@,"finite.oracle_exact_consumption");
#if defined(SWDB_NATIVE)
  printf(" end=done\n"); fflush(stdout);
#endif
  return 0;
}
'''.replace('@N@',str(draw_count))

def oracle(trace,count):
    need(type(trace) is list,'complete property trace required')
    values=[]
    for step in trace:
        if type(step) is dict and step.get('stepType')=='assignment' and step.get('lhs')=='goto_symex$$return_value$$swdb_next':
            text=(step.get('value') or {}).get('data')
            need(type(text) is str and re.fullmatch(r'-?(?:0|[1-9][0-9]*)',text),'exact signed64 oracle witness required')
            value=int(text);need(-(2**63)<=value<2**63,'signed64 oracle witness domain');values.append(value)
    need(len(values)==count,'complete ordered draw witness required before finite entry')
    return values

def failure_origin(location):
    """Closed job.c phase plus actual macro-expansion owner/line, not description."""
    need(type(location) is dict and location.get('file')=='job.c','failed property must originate in the exact generated job.c')
    function=location.get('function');line=location.get('line')
    need(type(function) is str and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',function),'exact failure function required')
    need(type(line) is str and re.fullmatch(r'[1-9][0-9]*',line),'exact positive CBMC source line required')
    return dict(file='job.c',function=function,line=int(line))

def same_origin(left,right):
    def valid(value):
        return (type(value) is dict and set(value)=={'file','function','line'} and value['file']=='job.c'
            and type(value['function']) is str and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',value['function'])
            and type(value['line']) is int and value['line']>0)
    return bool(valid(left) and valid(right) and left==right)

def replay_matches(failure,row):
    return (type(failure) is dict and type(row) is dict and failure.get('property') in CANDIDATE_FAILURES
        and row.get('failed')==[failure['property']] and row.get('end')=='check'
        and same_origin(failure.get('origin'),row.get('origin'))
        and failure.get('function')==failure['origin']['function'])

def check_adoption(verdict,samples,counterexample=None):
    if verdict=='proven':
        need(type(samples) is list and len(samples)==4 and all(type(row) is dict and row.get('failed')==[] and row.get('end')=='done' and row.get('origin') is None for row in samples),'native failure or incomplete sample blocks proven finite adoption')
    elif verdict=='refuted':
        need(type(counterexample) is dict and replay_matches(counterexample,counterexample.get('replay') or {}),'exact failed assertion origin must replay before refuted adoption')

def read_outcome(result,text,count,owners):
    def out(verdict,why,goals=(),failures=(),failure_class=None):return dict(verdict=verdict,why=why,goals=list(goals),failures=list(failures),failure_class=failure_class)
    if result.out_of_memory:return out('not_proven','RSS cap exceeded',failure_class='out_of_memory')
    if result.timed_out:return out('not_proven','wall budget exceeded',failure_class='timeout')
    need(result.exit_code in (0,10),'CBMC must settle with complete result exit0/10')
    need(type(owners) in (tuple,list,set) and {'dwe_trace_program','dxm_cover','dxm_cpu_write','dxm_device_write'}<=set(owners),'exact generated model property-owner census required')
    allowed=set(owners)|{FUNCTION,'main','swdb_run','swdb_next','swdb_next_real','__CPROVER_initialize'}
    messages=strict(text);need(type(messages) is list and all(type(row) is dict for row in messages),'complete CBMC JSON message list required')
    need(not any(row.get('messageType')=='ERROR' for row in messages),'CBMC error message refuses finite result')
    batches=[row['result'] for row in messages if 'result' in row]
    need(len(batches)==1 and type(batches[0]) is list and batches[0],'one complete nonempty CBMC property batch required')
    rows=batches[0];goals=[];seen=set();failures=[];reaches=[];normal=[]
    for row in rows:
        need(type(row) is dict,'malformed property row');prop=row.get('property');description=row.get('description');location=row.get('sourceLocation')
        need(type(prop) is str and prop and prop not in seen and type(description) is str and type(location) is dict,'unique identified property and owner required');seen.add(prop)
        status=row.get('status');need(status in ('SUCCESS','FAILURE'),'unknown/skipped property status refuses')
        owner=location.get('function');need(type(owner) is str and owner in allowed,'known generated property owner required')
        goals.append(dict(goal=prop,property=description,function=owner,status=status.lower(),solver=None,seconds=None,
            origin=failure_origin(location) if status=='FAILURE' and description in CANDIDATE_FAILURES else None))
        if description==REACH:
            need(owner==FUNCTION,'finite entry reachability owner differs');reaches.append(row);continue
        need(not description.startswith('swdb_reach.'),'unknown reachability marker refuses')
        if description==NORMAL:need(owner=='swdb_run','normal-return property owner differs');normal.append(row)
        if status=='FAILURE':failures.append(row)
    need(len(reaches)==1 and reaches[0]['status']=='FAILURE','exact owned receiver entry must be reachable')
    need(len(normal)<=1 and any(g['property'] not in (REACH,NORMAL) for g in goals),'nonempty checked model property census required')
    # Entry reachability itself fails, so complete runs exit10 even for safe traces.
    need(result.exit_code==10,'failure-marked reachability requires CBMC exit10')
    if any('.unwind.' in row['property'] for row in failures):return out('not_proven','actual unwinding assertion failed',goals,failure_class='unwinding_bound_too_small')
    if any(row['description'] in CAPACITY_FAILURES for row in failures):return out('not_proven','model/oracle capacity failed',goals,failure_class='ghost_capacity')
    if any(row['description'] not in CANDIDATE_FAILURES for row in failures):return out('not_proven','prestate, runtime-domain, RTE or unclassified property failed',goals,failure_class='unsupported_construct')
    observed=[]
    for row in failures:
        observed.append(dict(check=row['property'],property=row['description'],function=row['sourceLocation']['function'],origin=failure_origin(row['sourceLocation']),oracle=oracle(row.get('trace'),count)))
    if not observed:need(len(normal)==1 and normal[0]['status']=='SUCCESS','proven finite unit must retain its checked normal-return property')
    return out('failed' if observed else 'proven','checked finite model properties with reachable owned entry',goals,observed)

def native_row(text,count):
    need(type(text) is str and len(text)<=65536 and len(text.splitlines())==1,'one bounded fresh-process native row required')
    line=text.rstrip('\n');need(line.startswith('run 0:'),'native run identity differs')
    pairs=re.findall(r' input finite_choice_(\d+)=(\d+)',line)
    need([int(key) for key,_ in pairs]==list(range(count)),'complete ordered native draw readback required')
    values=[int(value) for _,value in pairs];need(all(0<=value<2**32 for value in values),'native full-u32 draw domain')
    need(line.count(' reach='+REACH)==1,'native owned receiver entry marker missing/duplicate')
    failures=re.findall(r' fail=(\S+)',line);end=re.findall(r' end=(\S+)',line)
    origins=re.findall(r' origin_function=([A-Za-z_][A-Za-z_0-9]*) origin_line=([1-9][0-9]*)',line)
    need(len(end)==1 and end[0] in ('done','check'),'native settled done/check marker required')
    need((end[0]=='done' and not failures) or (end[0]=='check' and len(failures)==1 and failures[0] in CANDIDATE_FAILURES),'native prestate/capacity/domain failure cannot refute a Plan')
    need(len(origins)==(1 if failures else 0),'one exact native failed assertion origin required')
    origin=dict(file='job.c',function=origins[0][0],line=int(origins[0][1])) if origins else None
    # No arbitrary unparsed stdout may masquerade as the exact protocol.
    canonical='run 0:'+''.join(' input finite_choice_%d=%d'%(i,value) for i,value in enumerate(values))+' reach='+REACH
    canonical+=(' fail='+failures[0]+' origin_function='+origin['function']+' origin_line='+str(origin['line']) if failures else '')+' end='+end[0]
    need(line==canonical,'unexpected native output token')
    return dict(inputs=values,failed=failures,origin=origin,end=end[0])

def loop_bounds(profile,actual,helpers):
    need(type(actual) is list and actual and len(actual)==len(set(actual)),'actual nonempty unique loop selectors required')
    need(type(helpers) in (set,tuple,list) and {'dxm_cover','dxm_cpu_write','dxm_device_write'}<=set(helpers),'exact emitted helper owner census required')
    allowed=set(helpers)|{FUNCTION,'main','swdb_run','swdb_next','swdb_next_real'}
    need(all(type(loop) is str and '.' in loop and loop.rsplit('.',1)[0] in allowed for loop in actual),'unclassified actual loop owner')
    needed={'dxm_cover','dxm_cpu_write','dxm_device_write'}
    need(needed<={loop.rsplit('.',1)[0] for loop in actual},'actual capacity-owner loop observation incomplete')
    cap=profile['node_limit'];need(type(cap) is int and 16<=cap<=512 and cap&(cap-1)==0 and cap>profile['nodes_required'],'source-derived node profile differs')
    rows=[]
    for loop in actual:
        owner=loop.rsplit('.',1)[0]
        bound=20*cap+1 if owner=='dxm_cover' else cap+1 if owner in ('dxm_cpu_write','dxm_device_write') else 513
        rows.append(dict(loop=loop,owner=owner,unwind=bound))
    return rows


def public_record(record,row,profile):
    """Actual CLI record gate, separate from a prediction or interpreter exit."""
    need(type(record) is dict and record.get('kind')=='proof' and not record.get('skip_reason') and record.get('evidence_kind')=='execution','actual unskipped execution proof record required')
    need(record.get('verdict')==row['conditional_predicted_verdict'] and record.get('bounds')=={'threads':1},'actual finite verdict/bounds differ from the closed prediction')
    pins=record.get('pins') or {};need(pins.get('contract')==row['contract'],'actual contract semantic pin differs')
    need((pins.get('proof_semantics') or {}).get('sha256')==profile['entry']['sha256'],'actual same physical new0.2 entry differs')
    settings=record.get('settings') or {};need(settings.get('verifier_launched') is True,'actual CBMC launch required')
    cert=settings.get('finite_trace') or {};need(cert.get('case_id')==row['case_id'] and cert.get('kind')=='dx100-whole-interface-finite-trace-1','actual TraceUnit kind/case differs')
    need((settings.get('forms') or {}).get('finite_concrete_model')==record['verdict'],'actual abstract-model form verdict differs')
    expected=profile['record_assumptions'];actual=record.get('assumptions')
    need(type(actual) is list and all(item in actual for item in expected),'every normal same-entry base and finite entry#rule assumption must be retained')
    need(all(item.get('kind')=='proof_semantics' and '#' in item.get('reference',{}).get('id','') for item in expected),'proper noncapping same-entry assumption references required')
    goals=record.get('goals');need(type(goals) is list and len(goals)>2 and len({g.get('goal') for g in goals})==len(goals),'complete unique actual finite goal census required')
    need(all(g.get('status') in ('success','failure') for g in goals),'unknown/skipped actual goals refuse')
    reach=[g for g in goals if g.get('property')==REACH];need(len(reach)==1 and reach[0].get('status')=='failure' and reach[0].get('function')==FUNCTION,'owned entry reachability required')
    normal=[g for g in goals if g.get('property')==NORMAL]
    need(len(normal)<=1,'normal-return property may not be duplicated')
    samples=settings.get('finite_native_samples');need(type(samples) is list and len(samples)==4 and all(type(s.get('output_sha256')) is str and len(s['output_sha256'])==64 for s in samples),'four actual native sample observations required')
    need(type(settings.get('finite_actual_loop_bounds')) is list and settings['finite_actual_loop_bounds'],'actual complete loop bounds must be retained')
    failed=[g for g in goals if g.get('status')=='failure' and g.get('property')!=REACH]
    need(not any('.unwind.' in g.get('goal','') or g.get('property') in CAPACITY_FAILURES for g in failed),'actual unwind/capacity failure cannot satisfy a prediction')
    if record['verdict']=='proven':need(len(normal)==1 and not failed and all(s.get('failed')==[] and s.get('end')=='done' for s in samples),'proven finite unit needs normal return, successful samples and all safety properties')
    else:
        need(failed and all(g.get('property') in CANDIDATE_FAILURES for g in failed),'only named finite safety failures may refute')
        counterexample=record.get('counterexample') or {};replay=counterexample.get('replay') or {}
        exact=[g for g in failed if g.get('goal')==counterexample.get('check') and g.get('property')==counterexample.get('property') and g.get('function')==counterexample.get('function') and same_origin(g.get('origin'),counterexample.get('origin'))]
        need(len(exact)==1 and replay.get('form')=='finite_concrete_model_c' and replay.get('replayed') is True and replay_matches(counterexample,replay)
            and replay.get('original_cpp_equivalence') is False,'actual exact sanitized abstract-model replay required')
    check_adoption(record['verdict'],samples,record.get('counterexample'))
    return dict(case_id=row['case_id'],verdict=record['verdict'],goal_count=len(goals),skip_count=0,original_cpp_or_hardware_equivalence=False)
