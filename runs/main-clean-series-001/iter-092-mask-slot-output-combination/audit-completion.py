from pathlib import Path
import json,hashlib,statistics,math,subprocess,datetime
C=Path(__file__).resolve().parent;R=C.parents[2];P=C.parent/'iter-082-outlined-gather-tile';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={};requirements=[]
def read(p):
 p=Path(p);d=json.loads(p.read_text());pins[str(p)]=sha(p)
 for file,h in d.get('input_sha256',{}).items():assert sha(Path(file))==h,file;pins[file]=h
 return d
def req(name,evidence):requirements.append(dict(requirement=name,status='proven',evidence=evidence))
source_doc=R.parent/'FlashMLA/docs/kda/basic-flow.md';assert source_doc.read_bytes()==(R/'docs/kda/basic-flow.md').read_bytes();pins[str(source_doc)]=sha(source_doc);pins[str(R/'docs/kda/basic-flow.md')]=sha(R/'docs/kda/basic-flow.md')
req('Task scope and metric: original3head64 workloads; actual TFLOPS /2250TFLOPS >45%, not NCU activity',['docs/kda/basic-flow.md','executable-plan.md'])
f=read(C/'plan-freeze.json');g=read(C/'source-generation.json');assert f['plan_sha256']==g['plan_sha256']==sha(C/'executable-plan.md')==sha(R/'docs/draft.md')
for p in [C/'executable-plan.md',R/'docs/draft.md']:pins[str(p)]=sha(p)
req('Executable plan frozen before implementation; baseline, GPU, workload, risks, ranked choice, commands and adoption criteria recorded',['executable-plan.md','plan-freeze.json','source-generation.json'])
s=(C/'source-snapshot/phase1.cuh').read_text()
for old,new in reversed(g['edits']):assert s.count(new)==1;s=s.replace(new,old,1)
assert s==(P/'source-snapshot/phase1.cuh').read_text()
for n in ['config.h','common_subroutine.h']:assert (C/'source-snapshot'/n).read_bytes()==(P/'source-snapshot'/n).read_bytes()
tracked=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines();assert set(tracked)=={'csrc/cuda_kernels/sm100/prefill/sparse/fwd/head64/config.h','csrc/cuda_kernels/sm100/prefill/sparse/fwd/head64/phase1.cuh'}
req('Original CUDA C++/PTX implementation; candidate only7phase1 substitutions relative082; existing scope preserved',['source-edit.diff','source-generation.json','source-snapshot/phase1.cuh'])
cpu=read(C/'root-cpu-qualification.json');formal=read(C/'root-formal-qualification.json');actual=read(C/'actual-package-audit.json');assert cpu['passed'] and formal['passed'] and actual['status']=='passed'
for name in ['native-composition.json','native-controls.json','native-mask.json','native-mask-controls.json','lifetime-model-result.json','store-mapping-model-result.json']:assert read(C/name)['passed']
assert cpu['threads']==384 and cpu['dynamic_shared_bytes']==222480 and cpu['tmem_columns']==512 and cpu['clc_workers']==266 and cpu['producer_acks']==4
for x in actual['architectures'].values():assert x['native128_equal_to_isolated'] and not x['unexplained_nondebug_changes'] and x['resources']=={'REG':168,'STACK':0,'SHARED':1024,'LOCAL':0}
other=read(C/'other-cubins-audit.json');assert other['passed'] and other['non_target_cubins']==52 and len(other['negative_controls'])==6 and all(x['rejected'] for x in other['negative_controls'])
req('Source, compiled mechanisms, lifetimes, full mask bits, output mapping and negative controls verified before GPU',['root-cpu-qualification.json','native-composition.json','native-controls.json','native-mask-controls.json'])
req('Formal package has exact audited target native128/nondebug resources; all52other cubins preserve executable identity',['root-formal-qualification.json','actual-package-audit.json','other-cubins-audit.json'])
art=read(C/'artifact.json');dec=read(C/'decision.json');assert art['build_exit_code']==0 and art['sha256']==formal['extension_sha256']==actual['package_sha256']==sha(C/'package/flash_mla/cuda.abi3.so')
assert len(dec['current_files'])==8
for file,h in dec['current_files'].items():assert sha(Path(file))==h,file;pins[file]=h
req('Final live source/package equals validated adopted artifact, all8files bound; baseline/parent archives retained',['artifact.json','decision.json','package/flash_mla/cuda.abi3.so'])
q=read(C/'correctness-qualification.json');assert q['passed'] and q['original_cases']==316 and q['numeric_original_cases']==314 and q['run_only_original_cases']==2 and q['tail_cases']==6 and q['witness_queries']==16 and q['diagnostic_cases']==29
assert q['diagnostic_totals']=={'arrays':87,'elements':423174144,'all_bitwise_equal':True,'ignored_nan_payloads':0,'ignored_zero_signs':0}
log=(C/'original-001-monitor/stdout.log').read_text();assert log.count('Running on TestParam(')==316 and 'All 316 cases passed!' in log
req('All original316 cases plus tail6/witness16/29per-role diagnostics passed;87arrays423174144 elements bitwise, including NaN payload and signed zero',['correctness-qualification.json','original-001-monitor/stdout.log','diagnostic-differential-001.json'])
immutable={'scripts/kda_bench.py':'e05683800ae11b7aff6d92e60d3af18f365d3fc8c0e34574aececfc028ea593d','scripts/kda_compare.py':'da7412c71d9804e3fcd8ad93bc4ff4c8fa1bd2ec4b9387b947db87f00e921247','scripts/kda_run.py':'6b26ae1f8c8e9f658d5d368db53a3085126b6c0a920abc9741ba9fb9cda83d5a','tests/test-sparse-prefill.py':'cfc982fe26c645302d358702402e5332a38419b1f267feb5ca3d038115a1d1f0'}
for p,h in immutable.items():assert sha(R/p)==h;pins[str(R/p)]=h
initial=read(R/'runs/main-clean-series-001/baseline/benchmark-001/timing.json');expected={x['case']['s_kv']:x['case'] for x in initial['measurements']};assert set(expected)=={4096,8192,32768}
req('Original benchmark/test scripts, seeds, params, warmup, flush, cooldown and timing protocol unchanged; immutable initial baseline retained',['baseline/benchmark-001/timing.json','comparison-001-prelaunch.json','comparison-002-prelaunch.json','performance-audit-001.json','performance-audit-002.json'])
end=None;monitor_counts={}
for stage in ['original-001','tail-001','witness-001','diagnostic-parent-001','diagnostic-candidate-001','comparison-001','comparison-002']:
 m=read(C/(stage+'-monitor/manifest.json'));assert m['status']=='finished' and m['exit_code']==0 and m['valid'] and not m['contaminated'] and not m['invalid_reasons'];assert m['gpu_uuid']=='GPU-847489a9-bc7e-726c-1c64-29c59e330fd8' and m['selected_device']['index']=='7' and m['selected_device']['name']=='NVIDIA B200' and m['idle_samples_required']==3
 begin=datetime.datetime.fromisoformat(m['started_at']);finish=datetime.datetime.fromisoformat(m['finished_at']);assert finish>=begin
 if end is not None:assert begin>=end,(stage,begin,end)
 end=finish;p=C/(stage+'-monitor/telemetry.jsonl');rows=[json.loads(x) for x in p.read_text().splitlines()];assert len(rows)==m['telemetry_samples'];pins[str(p)]=sha(p);monitor_counts[stage]=len(rows)
 before=[x for x in rows if x['phase']=='before'];assert len(before)>=3
 for x in before[-3:]:assert not x['errors'] and not x['processes'] and float(x['gpu']['utilization.gpu'])==0 and float(x['gpu']['memory.used'])<10
 for x in rows:
  assert x['gpu']['uuid']==m['gpu_uuid']
  if x['phase']!='before':assert not x['errors'] and not x['foreign_processes'] and all(p['pid'] in x['owned_pids'] for p in x['processes'])
req('Same UUID/physical7/logical0 throughout; three idle samples per launch; every sample free of foreign activity; all7stages serial',['*-monitor/manifest.json','*-monitor/telemetry.jsonl'])
pooled=read(C/'pooled-performance-audit.json');allratios=[];raw_count=0;round_peaks={}
for n in ['001','002']:
 a=read(C/f'performance-audit-{n}.json');summary=read(C/f'comparison-{n}/summary.json');assert a['passed'] and a['samples']==330 and a['aggregate_speedup_pct']>0.5 and a['all_three_above45'];assert [x['name'] for x in summary['runs']]==[v+f'{i:02d}' for i in range(5) for v in ['A','B']]+['A05']
 means={k:{'A':[],'B':[]} for k in expected}
 for run in summary['runs']:
  p=C/f"comparison-{n}/{run['name']}.json";x=read(p);assert sha(p)==run['timing_json_sha256'] and x['status']=='passed' and x['device']['logical_device']=='cuda:0' and x['device']['cuda_visible_devices']=='GPU-847489a9-bc7e-726c-1c64-29c59e330fd8';assert x['test_source']['sha256']==immutable['tests/test-sparse-prefill.py']
  for y in x['measurements']:
   k=y['case']['s_kv'];assert y['case']==expected[k] and y['correctness']=='passed';vals=[b-a for a,b in y['time_ranges_s']];assert len(vals)==10 and vals==y['samples_s'];raw_count+=len(vals);means[k][run['version']].append(statistics.mean(vals))
 ratios=[];round_peaks[n]={}
 for k,v in means.items():
  assert len(v['A'])==6 and len(v['B'])==5;r=[math.sqrt(v['A'][i]*v['A'][i+1])/v['B'][i] for i in range(5)];ratios+=r
  pct=343597383680/(statistics.mean(v['B'])*2250e12)*100;assert pct>45 and math.isclose(pct,a['shapes'][str(k)]['theoretical_peak_pct'],rel_tol=1e-13);round_peaks[n][str(k)]=pct
 assert math.isclose((statistics.geometric_mean(ratios)-1)*100,a['aggregate_speedup_pct'],rel_tol=1e-12);allratios+=ratios
assert raw_count==660 and len(allratios)==30 and pooled['samples']==660 and pooled['adoption_gate_passed'] and pooled['goal_achieved'];assert math.isclose((statistics.geometric_mean(allratios)-1)*100,pooled['aggregate_speedup_pct'],rel_tol=1e-12)
assert all(x['paired_speedup_pct']>=-0.1 for x in pooled['shapes'].values()) and dec['adopted'] and dec['goal_achieved']
req('Two predeclared complete330 comparisons, all660samples/30pairs included; no selective stopping or favorable rerun selection',['executable-plan.md','performance-audit-001.json','performance-audit-002.json','pooled-performance-audit.json'])
req('Both replicate aggregate gains and pooledGM strictly>0.5%; no per-shape regression; adopted only after full evidence',['decision.json','pooled-performance-audit.json'])
req('Every original shape strictly>45% theoretical utilization in BOTH full comparisons, recomputed from raw time intervals',['comparison-001/*.json','comparison-002/*.json','performance-audit-001.json','performance-audit-002.json'])
for n in range(18,37):
 w=R.parent/f'FlashMLA-main-clean-{n}';assert subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=all','--ignored'],cwd=w)==b'';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=w,text=True).strip()=='395cb3afbb331fef7b1b21e9340861b9436b42d8'
req('Latest cleanworktree request preserved:main-clean-36/main395cb3a clean;18..35 also untouched',['decision.json','git status --porcelain --untracked-files=all --ignored on18..36'])
report=(C/'REPORT.md').read_text();perf=(R/'docs/kda/performance.md').read_text();assert '当前最佳为 iter092' in perf[:2500] and '目标v2已达标' in perf[:2500] and '## Iter091' in perf and '## Iter090' in perf and perf.count('## Iter092')==1
for text in [report,perf]:
 for required in ['0.677353666','20.747824068','338.271670','46.322442','46.197409','45.144173','423,174,144','595.71.05','kerutils','list当dict']:assert required in text,required
req('Markdown report includes per-shape parent/initial results, variation, aggregation, adoption, full failure history and current retained gains at top',['REPORT.md','docs/kda/performance.md'])
req('Exact commands/environment/compiler/driver/artifacts/raw data preserved; no device or benchmark changes',['formal-build-001/manifest.json','cpu-build/attempt-001/compile-argv.json','artifact.json','final-environment.json','*-prelaunch.json'])
for p in [Path(__file__),C/'REPORT.md',R/'docs/kda/performance.md',C/'final-environment.json',C/'source-edit.diff',C/'formal-build-001/manifest.json']:pins[str(p)]=sha(p)
md='# Iter092 目标v2完成审计\n\n按当前主工作区与实验工作区一致的basic-flow.md逐项审核。不是仅检查pass标签：最终文件哈希、所有监控、原始660时间区间、30相邻配对和两轮逐负载理论利用率已重新计算核对。所有要求有证据，未缩小工作负载或容差。\n\n| 要求 | 结论 | 证据 |\n|---|---|---|\n'+'\n'.join('| '+x['requirement']+' | proven | '+', '.join(x['evidence'])+' |' for x in requirements)+'\n\n两轮逐负载理论利用率：\n\n```json\n'+json.dumps(round_peaks,indent=2)+'\n```\n\n全量正确性、每轮>0.5%采用门槛、三负载每轮>45%目标及报告均完成。当前最佳092已保留；main-clean-36保持干净。目标是约定设备与负载下的验证结果，并非全形状全设备或全局最优证明。\n'
(C/'completion-audit.md').write_text(md);pins[str(C/'completion-audit.md')]=sha(C/'completion-audit.md')
out=dict(passed=True,goal_achieved=True,requirements=requirements,raw_samples_recomputed=raw_count,paired_ratios_recomputed=len(allratios),theoretical_utilization_by_replicate=round_peaks,monitor_counts=monitor_counts,aggregate_speedup_pct=pooled['aggregate_speedup_pct'],input_sha256=pins)
with (C/'completion-audit.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k not in ['requirements','input_sha256']},indent=2));print('requirements:',len(requirements),'pinned inputs:',len(pins))
