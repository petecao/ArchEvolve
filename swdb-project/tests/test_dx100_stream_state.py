"""2026-10-16 ET. One-element stream transition seam; no actual verifier."""
import hashlib,importlib.util,json,os,shlex,subprocess
from pathlib import Path
from conftest import REPO

PROTO=REPO/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-proof-semantics'

def stream_module():
    spec=importlib.util.spec_from_file_location('dx_stream_transition',PROTO/'stream_state.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def native(tmp_path,body):
    from swdb import c_lowering,stdlib_provenance
    unit=tmp_path/'stream.c';unit.write_text(stream_module().render_header()+'\n'+body)
    tool=c_lowering.locate();exe=tmp_path/'stream.bin';dep=tmp_path/'stream.d'
    command=[*tool.command,'-x','c','-std=c11','-O1','-Wall','-Werror','-Wno-unused-function',
             '-fsanitize=address,undefined','-MD','-MF',str(dep),str(unit),'-o',str(exe)]
    built=subprocess.run(command,capture_output=True,text=True,timeout=60)
    env={'ASAN_OPTIONS':'detect_leaks=0:abort_on_error=0','UBSAN_OPTIONS':'halt_on_error=1:exitcode=1'}
    ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30,env={**os.environ,**env}) if built.returncode==0 else None
    pin=lambda p:{'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    receipt={'compile_command':command,'compile_exit':built.returncode,'compile_stdout':built.stdout,'compile_stderr':built.stderr,
             'native_command':[str(exe)],'native_exit':ran.returncode if ran else None,
             'native_stdout':ran.stdout if ran else None,'native_stderr':ran.stderr if ran else None,
             'source':pin(unit),'headers':[pin(Path(p)) for p in sorted(set(shlex.split(dep.read_text().replace('\\\n','').split(':',1)[1])))] if dep.exists() else [],'executable':pin(exe) if exe.exists() else None,'runtime':stdlib_provenance.runtime_identity(tool),
             'scope':'Finite transition-kernel controls, not full source refinement or hardware liveness.'}
    (tmp_path/'native-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert built.returncode==0,built.stderr
    assert ran.returncode==0,ran.stdout+ran.stderr

def test_selected_dispatch_prefix_has_no_completion_and_blocked_wait(tmp_path):
    native(tmp_path,r'''
int main(void) {
 struct dxl_state s;
 if(dxl_fresh(&s,UINT64_C(0x1000),UINT64_C(0x2000))!=DXL_OK) return 1;
 if(dxl_packet(&s,0,UINT64_C(0x00ff00ff))!=DXL_OK) return 2;
 if(dxl_packet(&s,1,UINT64_C(0xffffffff000102ff))!=DXL_OK) return 3;
 if(dxl_packet(&s,2,UINT64_C(0x1000))!=DXL_OK) return 4;
 if(s.ack || s.tile_status!=2 || s.ready!=0 || s.size!=0) return 5;
 if(dxl_dispatch(&s)!=DXL_OK) return 6;
 if(!s.ack || s.tile_status!=0 || s.ready!=255 || s.size!=0) return 7;
 if(s.lane0_finished || s.other_lanes_finished || !s.payload_initialized) return 8;
 uint16_t out=99;
 if(dxl_wait_response(&s,&out)!=DXL_BLOCKED || out!=99) return 9;
 if(s.tile_status!=0 || s.ready!=255 || s.size!=0) return 10;
 return 0;
}
''')

def test_stream_publishes_size_only_after_matched_line_response_and_completed_timing(tmp_path):
    native(tmp_path,r'''
int main(void) {
 struct dxl_state s;_Alignas(64) uint32_t input[16]={7};uint16_t out=99;
 if(dxl_fresh(&s,UINT64_C(0x1000),UINT64_C(0x2000))!=DXL_OK) return 1;
 if(dxl_bind_input(&s,input,16)!=DXL_OK) return 2;
 if(dxl_packet(&s,0,UINT64_C(0x00ff00ff)) ||
    dxl_packet(&s,1,UINT64_C(0xffffffff000102ff)) ||
    dxl_packet(&s,2,UINT64_C(0x1000)) || dxl_dispatch(&s)) return 3;
 if(dxl_start(&s,0,1,1)!=DXL_OK || s.tile_status!=1) return 4;
 if(dxl_finish(&s,1,1)!=DXL_ORDER || s.ready!=255 || s.size!=0) return 5;
 if(dxl_request(&s,UINT64_C(0x2000),4,0,0)!=DXL_DOMAIN) return 6;
 if(dxl_request(&s,UINT64_C(0x2000),64,0,0)!=DXL_OK) return 7;
 if(dxl_response(&s,UINT64_C(0x2040),64,0,0,7)!=DXL_DOMAIN) return 8;
 if(dxl_response(&s,UINT64_C(0x2000),64,1,0,7)!=DXL_DOMAIN) return 9;
 if(dxl_response(&s,UINT64_C(0x2000),64,0,0,8)!=DXL_DOMAIN) return 10;
 if(dxl_get_size(&s,&out)!=DXL_BLOCKED || out!=99) return 11;
 if(dxl_response(&s,UINT64_C(0x2000),64,0,0,7)!=DXL_OK) return 12;
 if(s.payload0!=7 || !s.payload_initialized || !s.lane0_finished || s.other_lanes_finished) return 13;
 if(dxl_wait_response(&s,&out)!=DXL_BLOCKED || s.tile_status!=1 || s.size!=0 || s.ready!=255) return 14;
 if(dxl_finish(&s,0,1)!=DXL_BLOCKED || dxl_finish(&s,1,0)!=DXL_BLOCKED) return 15;
 if(dxl_finish(&s,1,1)!=DXL_OK || s.tile_status!=2 || s.size!=1 || s.ready!=0) return 16;
 if(dxl_wait_response(&s,&out)!=DXL_OK || out!=1) return 17;
 out=99;if(dxl_get_size(&s,&out)!=DXL_OK || out!=1 || s.other_lanes_finished) return 18;
 return 0;
}
''')

def test_stream_pending_hazard_covers_full_line_and_rejects_unbound_or_undefined_domains(tmp_path):
    native(tmp_path,r'''
int main(void) {
 struct dxl_state s;_Alignas(64) uint32_t input[16]={7};
 if(dxl_fresh(&s,0,UINT64_C(0x2000))!=DXL_DOMAIN) return 1;
 if(dxl_fresh(&s,UINT64_C(0x1004),UINT64_C(0x2000))!=DXL_DOMAIN) return 2;
 if(dxl_fresh(&s,UINT64_C(0x1000),UINT64_C(0x2000))) return 3;
 if(dxl_packet(&s,0,UINT64_C(0x01ff00ff))!=DXL_DOMAIN || s.phase!=DXL_BOOT) return 4;
 if(dxl_bind_input(&s,input,16)) return 5;
 if(dxl_packet(&s,0,UINT64_C(0x00ff00ff)) || dxl_packet(&s,1,UINT64_C(0xffffffff000102ff)) ||
    dxl_packet(&s,2,UINT64_C(0x1000)) || dxl_dispatch(&s)) return 6;
 if(dxl_memory_write(&s,UINT64_C(0x203f),1)!=DXL_DOMAIN) return 7;
 if(dxl_memory_write(&s,UINT64_C(0x1fff),2)!=DXL_DOMAIN) return 8;
 if(dxl_memory_write(&s,UINT64_C(0x2040),1)!=DXL_OK || dxl_memory_write(&s,UINT64_C(0x1fc0),64)!=DXL_OK) return 9;
 if(dxl_memory_write(&s,UINT64_MAX,2)!=DXL_DOMAIN) return 10;
 if(dxl_start(&s,0,0,1)!=DXL_DOMAIN || dxl_start(&s,1,0,1)!=DXL_DOMAIN || dxl_start(&s,0,1,0)!=DXL_DOMAIN) return 11;
 if(dxl_start(&s,INT_MIN,INT_MAX,1)!=DXL_DOMAIN || s.ready!=255 || s.tile_status!=0 || s.size!=0) return 12;
 s.input_bound=0;
 if(dxl_start(&s,0,1,1)!=DXL_DOMAIN) return 13;
 return 0;
}
''')

def test_stream_metadata_transitions_match_pinned_spd_source_excerpts(tmp_path):
    from testkit.dx100_stream_native import run_spd_transitions
    run_spd_transitions(tmp_path,stream_module().render_header())

def test_public_stream_model_exposes_only_conditional_return_and_preserves_arbitrary_stuttering(tmp_path):
    from swdb import dx100_stream_model
    model=dx100_stream_model.normal_return_model()
    assert set(model)=={'state','c','entry','contracts','termination_policy'}
    assert model['termination_policy']=='conditional normal return; no hardware liveness'
    assert set(model['contracts'])=={'maa_stream_load_unsigned_int','wait_ready','get_tile_size'}
    assert all(r'terminates \false;' in text for text in model['contracts'].values())
    native(tmp_path,model['state']+r'''
#include <assert.h>
#define DX_ASSERT(c) assert(c)
static unsigned stutters=17,choices;
static unsigned __swdb_dx_stream_choose(void) { ++choices; if(stutters) {--stutters;return 0;} return 1; }
'''+model['c']+r'''
int main(void) {
 uint32_t input[16]={7};
'''+ '\n'.join(model['entry'])+r'''
 maa_stream_load_unsigned_int(input,0,1,2,0,-1);
 if(__swdb_dx_stream_meta.phase!=1 || __swdb_dx_stream_meta.ready!=255 || __swdb_dx_stream_meta.size!=0) return 1;
 __swdb_dx_stream_step(0,0,0);
 if(__swdb_dx_stream_meta.phase!=1 || __swdb_dx_stream_meta.ready!=255 || __swdb_dx_stream_meta.size!=0) return 2;
 wait_ready(0);
 if(choices<=17 || get_tile_size(0)!=1 || __swdb_dx_stream_meta.status!=2 || __swdb_dx_stream_meta.ready!=0) return 3;
 if(!__swdb_dx_stream_meta.lane0_finished || __swdb_dx_stream_meta.other_lanes_finished) return 4;
 return 0;
}
''')


def test_all_closed_projected_cpu_device_prefixes_require_completion_for_a_returned_wait(tmp_path):
    # Complete finite CPU/device event graph for this selected projection. Self
    # stutters add no new state; infinite stutters remain allowed. Coverage of
    # arbitrary gem5 schedules by this projection is a separate unverified duty.
    native(tmp_path,r'''
#include <stdio.h>
static int advance(struct dxl_state *s,unsigned stage) {
 if(stage==0) return dxl_start(s,0,1,1);
 if(stage==1) return dxl_request(s,UINT64_C(0x2000),64,0,0);
 if(stage==2) return dxl_response(s,UINT64_C(0x2000),64,0,0,7);
 return dxl_finish(s,1,1);
}
int main(void) {
 struct item { struct dxl_state state;unsigned cpu,device; } queue[25];
 unsigned head=0,tail=1,seen[5][5]={{0}},returned=0,late_ack=0,unsafe_without_wait=0;
 struct dxl_state initial;uint32_t input[16]={7};
 if(dxl_fresh(&initial,UINT64_C(0x1000),UINT64_C(0x2000)) || dxl_bind_input(&initial,input,16) ||
    dxl_packet(&initial,0,UINT64_C(0x00ff00ff)) || dxl_packet(&initial,1,UINT64_C(0xffffffff000102ff)) ||
    dxl_packet(&initial,2,UINT64_C(0x1000)) || dxl_dispatch(&initial)) return 1;
 queue[0]=(struct item){initial,0,0};seen[0][0]=1;
 while(head<tail) {
  struct item n=queue[head++];uint16_t out=99;
  if(n.cpu==0 && n.device==4) late_ack=1; /* completion before CPU observes ack */
  if(n.cpu==1 && n.device<4 && dxl_get_size(&n.state,&out)==DXL_BLOCKED) unsafe_without_wait=1;
  if(n.cpu==4) {
   if(n.device!=4 || dxl_get_size(&n.state,&out)!=DXL_OK || out!=1 || n.state.ready!=0 ||
      n.state.received_responses!=1 || !n.state.lane0_finished || n.state.other_lanes_finished) return 2;
   returned++;
  }
  if(n.device<4) {
   struct item next=n;if(advance(&next.state,n.device)!=DXL_OK) return 3;next.device++;
   if(!seen[next.cpu][next.device]) { seen[next.cpu][next.device]=1;queue[tail++]=next; }
  }
  if(n.cpu<4) {
   int enabled=n.cpu!=2 || dxl_wait_response(&n.state,&out)==DXL_OK;
   if(enabled) {
    struct item next=n;next.cpu++;
    if(!seen[next.cpu][next.device]) { seen[next.cpu][next.device]=1;queue[tail++]=next; }
   }
  }
 }
 if(!returned || !late_ack || !unsafe_without_wait || tail>25) return 4;
 printf("closed projected states=%u returned=%u; late-ack and missing-wait counterpaths present\n",tail,returned);
 return 0;
}
''')
