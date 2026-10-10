// EvolveSWDB advisor update. Date: 2026-09-30 (Eastern Time). Created 2026-09-27. Updated 2026-09-29 (slide 9: handoff first; monorepo paths; v4).
import fs from 'node:fs/promises';
import path from 'node:path';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {resolvePresentationFont,finalizePresentation} from '/Users/yanrujhou/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project';
const work=path.join(root,'weeklogs/2026-09-30');
const build=path.join(work,'.build');
const skill='/Users/yanrujhou/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const runtime='/Users/yanrujhou/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const family=resolvePresentationFont();
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={blue:'#00274C',maize:'#FFCB05',ice:'#E8F0F9',light:'#4A6FA5',body:'#1A1A1A',muted:'#555555',border:'#BDC3C7',alt:'#F4F4F4',white:'#FFFFFF',maizeLt:'#FFF4CC',green:'#27AE60',red:'#E74C3C',amber:'#F39C12'};
const DS='.scratch/bfs-rewrite-evaluation-2026-09-25/';
const notes=[];
function rect(s,x,y,w,h,fill,line){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:line?{fill:line,width:2}:{fill:'none',width:0}});}
function txt(s,text,x,y,w,h,size=28,bold=false,color=C.body,align){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=text;a.text.style={typeface:family,fontSize:size,bold,color,autoFit:'none',...(align?{alignment:align}:{})};return a;}
function slide(title,narration,sources,backup=false){const s=p.slides.add();s.background.fill=C.white;rect(s,0,0,1280,102,C.blue);rect(s,0,0,10,102,C.maize);txt(s,title,46,28,1190,60,38,true,C.white);txt(s,`EvolveSWDB    2026-09-30${backup?'    Backup':''}`,46,674,1070,30,18,false,C.muted);txt(s,String(p.slides.items.length),1190,674,50,30,18,false,C.muted);s.speakerNotes.textFrame.setText(narration+'\n\nSources:\n'+sources.join('\n'));notes.push({title,narration,sources});return s;}
function table(s,values,x,y,w,h,widths,size=24){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});t.borders.assign({fill:C.border,width:1,style:'solid'});for(let r=0;r<values.length;r++){t.rows[r].height=h/values.length;for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.blue:(r%2===0?C.alt:C.white);cell.text.style={typeface:family,fontSize:size,bold:r===0,color:r===0?C.white:C.body};}}return t;}
function bottom(s,text){rect(s,46,584,1188,64,C.maizeLt);txt(s,text,65,597,1150,44,24,true,C.blue);}
function box(s,label,x,y,w,h,primary=false,size=24){const a=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:primary?C.blue:C.ice,line:{fill:C.blue,width:2}});a.text=label;a.text.style={typeface:family,fontSize:size,bold:true,color:primary?C.white:C.blue,alignment:'center',verticalAlignment:'middle',autoFit:'none'};return a;}
function arrow(s,a,b){return s.shapes.connect(a,b,{kind:'straight',fromSide:'right',toSide:'left',line:{style:'solid',fill:C.blue,width:3},tail:{type:'arrow',width:'med',length:'med'}});}
function dot(s,x,y,color){s.shapes.add({geometry:'ellipse',position:{left:x,top:y,width:22,height:22},fill:color,line:{fill:'none',width:0}});}

// 1 Title
let s=p.slides.add();s.background.fill=C.white;rect(s,0,0,1280,720,C.blue);rect(s,0,0,14,720,C.maize);
txt(s,'EvolveSWDB weekly update',90,210,1100,80,48,true,C.white);
txt(s,'Profiling a workload and rewriting its code, with BFS as the first case',90,300,1100,60,28,false,C.maize);
txt(s,'Yan-Ru Jhou    2026-09-30',90,420,1100,50,24,false,C.white);
txt(s,'1',1190,674,50,30,18,false,C.white);
s.speakerNotes.textFrame.setText('0:00–0:15. Title. This week covers 2026-09-23 to 2026-09-29.');
notes.push({title:'Title',narration:'0:00–0:15. Title. This week covers 2026-09-23 to 2026-09-29.',sources:[]});

// 2 Recap
s=slide('Where we are',
`0:15–1:05 (50 s). Last week we built the Software Database: real code, memory access patterns, inputs, machines, and profiles, with queries and exports for the agents. It stored knowledge but could not act on it. This week I built the two parts that let an agent act: profiling, which tells the agent where a specific workload spends time and how it touches memory, and rewriting, which turns the agent's proposal into real, checked code. BFS is the first complete case. DX100 is one prototype evaluation target; the profiling and rewriting do not depend on it.`,
['weeklogs/2026-09-24/speaker-notes.md',DS+'spec.md']);
txt(s,'Last week',64,140,540,46,30,true,C.blue);
txt(s,'Built the Software Database\n• Real code + memory access patterns\n• Inputs, machine, measured profiles\n• Queries and exports for agents',64,200,560,220,24);
txt(s,'This week: my part',690,140,540,46,30,true,C.blue);
txt(s,'Make the database actionable\n• Profiling: where does time go?\n• Rewriting: proposal → real code\n• Check + measure every candidate',690,200,560,220,24);
bottom(s,'First case: BFS. DX100 is one prototype evaluation target.');

// 3 Motivation
s=slide('Why profiling and rewriting?',
`1:05–2:05 (60 s). Motivation: the SW and HW ensemble agents will choose optimizations and propose code changes. Problem one: static source facts and whole-program counters do not say where a particular BFS run spends time, and a rewrite can create new hot code that no catalog lists. Problem two: a proposal in natural language is not code; someone must apply it to the exact source, keep it within scope, and check it. Solution: a profiling query that discovers hot functions and loops automatically and returns their code and memory behavior, and a rewrite path that turns four proposal forms into a checked candidate.`,
[DS+'spec.md']);
table(s,[['','Profiling','Rewriting'],['Problem','Which code is hot on this input?','A proposal is not yet code'],['Problem','A rewrite adds code no catalog knows','Edits can drift out of scope'],['Solution','Discover functions + loops, attach memory data','Apply to exact source, bounded repair'],['Result','Profile package for the agent','Checked, measured candidate']],56,140,1168,380,[190,489,489],22);
bottom(s,'The agent decides what to change; we supply evidence and a trustworthy verdict.');

// 4 Profiling
s=slide('Profiling: what the agent receives',
`2:05–3:30 (85 s). Given an implementation, a graph, a source vertex, and a thread count, the profiler parses the current source with libclang, finds every function and loop, and instruments them, with no annotations. It ranks them by CPU time, keeping inclusive and exclusive time separate. For memory, it runs the same code under Callgrind and records data reads, writes, and modeled cache misses for the BFS call; the cache model matches mbit10's L1 and L3 sizes. Everything is bundled into a profile package with the source code, callers, types, and a strategy lookup. We do not have hardware counters on the shared host, so memory numbers are simulated and labeled as such.`,
[DS+'issues/06-function-hotspot-discovery.md',DS+'issues/08-dynamic-memory-observations.md',DS+'issues/09-profile-packages-and-strategy-lookup.md']);
const pin=box(s,'Code +\nworkload',40,170,190,110,false,22);
const pp=box(s,'Profiler',300,170,190,110,true,24);
arrow(s,pin,pp);
const outs=[['Hot functions + loops','found by parsing source; no annotations'],['CPU time per region','inclusive and exclusive kept apart'],['Memory behavior','reads, writes, modeled cache misses'],['Context + strategies','source, callers, matching strategies']];
outs.forEach((o,i)=>{txt(s,o[0],560,135+i*95,650,36,24,true,C.blue);txt(s,o[1],560,171+i*95,650,34,20,false,C.muted);});
txt(s,'Output: one profile package',40,320,460,40,22,true,C.body);
bottom(s,'No hardware counters on the shared host: memory data is simulated and labeled so.');

// 5 Profiling example
s=slide('Example: a rewrite adds a new hot helper',
`3:30–4:45 (75 s). A small diagnostic test. We submitted a patch that adds a helper function with two nested loops to upstream BFS, then profiled before and after on a ten-vertex graph from three source vertices. The baseline had 11 functions and 20 loops. The rewritten code had 12 functions and 22 loops. The new helper was found without being named anywhere and ranked first by exclusive CPU time. Thirty unchanged code fragments were matched to their old measurements; changed fragments were measured fresh and not given old data. The memory view shows the same effect: data reads rose from 8,468 to 54,474 for source 0. This checks that profiling follows the code as it changes. It is not a performance result.`,
[DS+'issues/06-function-hotspot-discovery.md',DS+'issues/07-loop-discovery-and-reprofiling.md',DS+'issues/08-dynamic-memory-observations.md']);
table(s,[['','Before rewrite','After rewrite'],['Functions found','11','12 (new helper ranked #1)'],['Loops found','20','22 (2 new nested loops)'],['Unchanged fragments matched','—','30'],['Data reads, source 0 (Callgrind)','8,468','54,474']],56,140,1168,330,[480,300,388],22);
txt(s,'Diagnostic graph: 10 vertices, sources 0, 3, 8, 1 thread. Checks tracking, not speed.',56,490,1170,40,20,false,C.muted);
bottom(s,'Profiling follows the code after a rewrite; old numbers never carry over to changed code.');

// 6 Rewriting
s=slide('Rewriting: four proposal forms, one path',
`4:45–6:05 (80 s). A proposal can arrive in four forms: natural-language instructions, structured instructions, annotated source, or a patch. All go through one path. The rewriter applies the proposal to an identified source snapshot, using Claude as a bounded worker for the instruction and annotation forms. The result must be a real code change; a comment-only edit is rejected. If the candidate fails to build or fails the correctness check, a limited number of repairs is allowed; repairs cannot change the intent and cannot tune performance. Every attempt, including failures, is stored. The table shows real examples from this week.`,
[DS+'issues/04-instruction-rewriting-and-repair.md',DS+'issues/05-annotated-source-rewriting.md',DS+'issues/18-dx100-patch-route-acceptance.md',DS+'issues/19-upstream-instruction-route-acceptance.md']);
const forms=box(s,'4 forms',40,150,170,90,false,22);
const ap=box(s,'Apply to\nexact source',270,150,200,90,true,22);
const ck=box(s,'Build +\ncheck',530,150,170,90,false,22);
const rp=box(s,'Bounded\nrepair',760,150,170,90,false,22);
const cd=box(s,'Candidate',990,150,200,90,true,22);
arrow(s,forms,ap);arrow(s,ap,ck);arrow(s,ck,rp);arrow(s,rp,cd);
table(s,[['Form','Real example','Outcome'],['Annotated source','GAPBS BFS: tuning parameter alpha 15 → 16','Correct'],['Structured instructions','GAPBS BFS: remove one dead reset call','Correct'],['Patch','DX100 scalar BFS: 64-vertex chunks, drop redundant store','Correct']],56,280,1168,250,[300,610,258],21);
bottom(s,'Repairs fix only build or correctness failures; they never tune performance.');

// 7 Results
s=slide('Measuring the rewrites: no change yet',
`6:05–7:25 (80 s). Setup: mbit10, Intel Xeon Gold 6326, one socket, one thread. Ten paired repetitions per graph, baseline and candidate alternating, timing only the BFS call. We claim a gain only with at least 1.05 speedup and a run-to-run spread under 10 percent. The first two rows are the scalar BFS from the DX100 prototype run natively on the CPU; the last two are upstream GAPBS BFS. Result: both candidates were correct on all 30 timed trials per role. Speedups are 1.000 to 1.002, and every 95 percent interval includes 1. Spread was above the limit, so the verdict is inconclusive. Analysis: these were deliberately small edits, so no gain is expected. What matters is that the path from proposal to verdict works and does not report noise as a win.`,
[DS+'issues/18-dx100-patch-route-acceptance.md',DS+'issues/19-upstream-instruction-route-acceptance.md']);
txt(s,'mbit10 Xeon Gold 6326, 1 thread, 10 paired repetitions, BFS call only',56,120,1170,36,20,false,C.muted);
table(s,[['Starting code + form','Graph','Baseline (ms)','Candidate (ms)','Speedup','95% CI'],['DX100 scalar BFS, patch','Uniform','46.03','45.96','1.002','[0.998, 1.011]'],['DX100 scalar BFS, patch','Kronecker','23.26','23.23','1.000','[0.996, 1.020]'],['GAPBS BFS, instructions','Uniform','7.33','7.29','1.002','[0.999, 1.005]'],['GAPBS BFS, instructions','Kronecker','6.00','5.99','1.001','[0.999, 1.030]']],56,168,1168,300,[320,150,175,185,140,198],21);
txt(s,'Correct on all timed trials. Spread above the 10% limit, so the verdict is “inconclusive”.',56,490,1170,70,22);
bottom(s,'Small edits, no gain. The path from proposal to verdict works end to end.');

// 8 Ongoing + lessons
s=slide('Ongoing work and what we learned',
`7:25–8:40 (75 s). What is still in progress and what we learned. Rewriting: several LLM proposal attempts timed out, and one returned a patch that did not apply. We added a whole-file edit format, and it produced a new candidate that waits for a build. Profiling: coverage is partial; code in headers, libraries, and one OpenMP region is not yet attributed, and we report that explicitly. Evaluation on the DX100 prototype needs gem5 simulations that take hours, and the shared host runs at most two jobs. We also cut our harness cost per trial from 8.7 to 1.0 seconds.`,
[DS+'issues/20-upstream-annotated-route-acceptance.md',DS+'issues/06-function-hotspot-discovery.md',DS+'issues/18-dx100-patch-route-acceptance.md',DS+'resume-plan-20260927.md']);
table(s,[['Area','Limitation','Response'],['Rewriting','LLM timeouts, one patch failed to apply','Whole-file edit format; new candidate'],['Profiling','Headers, libraries, 1 OpenMP region not attributed','Reported as partial coverage'],['DX100 prototype','gem5 runs take hours; 2 jobs per host','Parallel runs within one socket'],['Harness','Save cost per trial','8.7 s → 1.0 s']],56,140,1168,360,[240,500,428],21);
bottom(s,'Lesson: report what is not covered instead of hiding it.');

// 9 Plan
s=slide('Plan for this week',
`8:40–9:50 (70 s). This week the handoff comes first. At the 2026-09-24 meeting the team fixed a linear pipeline: my side, then Peter, then Josh and Eric, then back through Peter to me. So my first deliverable is for Peter's agent: the DX100 BFS top-down step with its exact source revision, build and graph commands, and raw logs, annotated with Josh's seven statement IDs so that Peter's per-statement features and Josh's hardware requests refer to the same lines. One detail to settle with Peter: this source stores edge offsets as 32-bit integers, while his feature report assumes 64-bit. Second, Eric asked who builds and tests the proposed hardware, and the pipeline names no owner for that yet. I already have a gem5 path for the DX100 prototype that checks BFS correctness and times the run, so I will offer it as the evaluator, at least for DX100-based designs. Then I continue with a profile-driven rewrite that targets a measured hot loop on a pilot-sized graph. The remaining proposal forms move after the handoff.`,
['../docs/meeting-2026-09-24.md','../examples/bfs.source-observations.yaml','apps/dx100/benchmarks/gapbs/src/graph.h',DS+'spec.md']);
const plan=[['1','Hand off annotated BFS to Peter’s agent','Pinned source, build and graph commands, logs, Josh’s 7 statement IDs'],['2','Offer our gem5 DX100 path as the evaluator','Answers “who builds and tests the proposed hardware?”'],['3','Then: profile-driven rewrite on a pilot-sized graph','Target a measured hot loop, not a toy edit']];
plan.forEach((r,i)=>{box(s,r[0],64,150+i*130,70,70,true,28);txt(s,r[1],160,152+i*130,1060,40,26,true,C.blue);txt(s,r[2],160,196+i*130,1060,36,22,false,C.muted);});
bottom(s,'Team pipeline (09-24): Yan-Ru → Peter → Josh/Eric → Peter → Yan-Ru');

// 9 Backup
s=slide('Backup: native measurement protocol',
`Backup. The native protocol was frozen from a one-thread pilot study. Baseline and candidate trials alternate in pairs to reduce drift on a shared host. Correctness is verified outside the timed region. A speedup is claimed only if the lower confidence bound exceeds 1 and the minimum speedup and spread rules pass. The host load is recorded with every run. No hardware counters are available to our account, so profiling uses region timers and Callgrind memory simulation.`,
[DS+'issues/18-dx100-patch-route-acceptance.md','.claude/rules/remote_server.md'],true);
table(s,[['Setting','Value'],['Host','mbit10, Intel Xeon Gold 6326, one socket lane'],['Threads','1'],['Repetitions','10 paired (baseline / candidate alternating)'],['Claim rule','Speedup ≥ 1.05 and spread ≤ 10%'],['Correctness','BFS tree checked on every timed trial'],['Profiling','Region timers + Callgrind (no HW counters)']],56,140,1168,420,[300,868],22);

await fs.writeFile(path.join(work,'speaker-notes.md'),'# EvolveSWDB weekly update\n\nDate: 2026-09-30 (Eastern Time). Created 2026-09-27. Updated 2026-09-29.\n\nTen-minute talk: slides 1–9. Slide 10 is backup.\n\n'+notes.map((n,i)=>`## ${i+1}. ${n.title}\n\n${n.narration}\n${n.sources.length?'\nSources:\n'+n.sources.map(x=>'- `'+x+'`').join('\n')+'\n':''}`).join('\n'));
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){const png=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));}
const final=path.join(work,'slides/evolveswdb-week-02-v4.pptx');
await finalizePresentation({workspaceDir:work,candidatePath:candidate,finalPath:final,pythonExecutable:path.join(runtime,'python/bin/python3'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,5,6,7,8,10].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[3,5,6,7,8,10],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:[family]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation-v4.json')});
console.log('FINAL',final);
