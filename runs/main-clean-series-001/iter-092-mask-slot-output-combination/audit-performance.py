from pathlib import Path
import argparse,json,hashlib,math,statistics
C=Path(__file__).resolve().parent;R=C.parents[2];P=C.parent/'iter-082-outlined-gather-tile'
ap=argparse.ArgumentParser();ap.add_argument('--attempt',default='001');args=ap.parse_args();D=C/('comparison-'+args.attempt);M=C/('comparison-'+args.attempt+'-monitor')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
m=read(M/'manifest.json');assert m['status']=='finished' and m['valid'] and m['exit_code']==0 and not m['invalid_reasons'] and not m['contaminated']
rows=[json.loads(x) for x in (M/'telemetry.jsonl').read_text().splitlines()];assert len(rows)==m['telemetry_samples']
before=[x for x in rows if x['phase']=='before'];assert len(before)>=3
for x in before[-3:]:assert not x['errors'] and not x['processes'] and float(x['gpu']['utilization.gpu'])==0 and float(x['gpu']['memory.used'])<10
assert rows[-1]['phase']=='after'
for x in rows:
 assert x['gpu']['uuid']=='GPU-847489a9-bc7e-726c-1c64-29c59e330fd8'
 if x['phase']!='before':assert not x['errors'] and not x['foreign_processes'] and all(y['pid'] in x['owned_pids'] for y in x['processes'])
assert sha(R/'scripts/kda_bench.py')=='e05683800ae11b7aff6d92e60d3af18f365d3fc8c0e34574aececfc028ea593d'
assert sha(R/'scripts/kda_compare.py')=='da7412c71d9804e3fcd8ad93bc4ff4c8fa1bd2ec4b9387b947db87f00e921247'
s=read(D/'summary.json');assert s['status']=='completed' and s['pairs_requested']==5 and len(s['runs'])==11
init=read(R/'runs/main-clean-series-001/baseline/benchmark-001/timing.json')
expected={x['case']['s_kv']:x['case'] for x in init['measurements']};assert set(expected)=={4096,8192,32768}
initial={k:statistics.mean(x['mean_s'] for x in init['measurements'] if x['case']['s_kv']==k) for k in expected}
controls={k:[] for k in expected};candidates={k:[] for k in expected};samples=0;pins={};rounds=[]
order=[v+f'{i:02d}' for i in range(5) for v in ['A','B']]+['A05']
assert [r['name'] for r in s['runs']]==order
for rec in s['runs']:
 p=D/(rec['name']+'.json');x=read(p);pins[str(p)]=sha(p);assert pins[str(p)]==rec['timing_json_sha256']
 assert rec['exit_code']==0 and rec['status']=='passed' and x['status']=='passed'
 pkg=P/'package' if rec['version']=='A' else C/'package'
 assert x['extension']['sha256']==sha(pkg/'flash_mla/cuda.abi3.so') and Path(x['package_root'])==pkg
 assert x['runner']['sha256']==sha(R/'scripts/kda_bench.py') and x['device']['cuda_visible_devices']==m['gpu_uuid']
 assert len(x['measurements'])==3 and x['requested_rounds']==1
 for y in x['measurements']:
  k=y['case']['s_kv'];assert y['case']==expected[k] and y['correctness']=='passed' and y['num_tests']==10
  assert len(y['samples_s'])==len(y['time_ranges_s'])==10
  vals=[b-a for a,b in y['time_ranges_s']]
  assert all(math.isfinite(v) and v>0 for v in vals) and vals==y['samples_s']
  mean=statistics.mean(vals);assert math.isclose(mean,y['mean_s'],abs_tol=1e-15)
  (controls if rec['version']=='A' else candidates)[k].append(mean);samples+=10
assert samples==330
per={};ratios=[];direct=[]
for k in sorted(expected):
 a,b=controls[k],candidates[k];assert len(a)==6 and len(b)==5
 r=[math.sqrt(a[i]*a[i+1])/b[i] for i in range(5)];ratios+=r
 mean=statistics.mean(b);base=statistics.mean(a);ratio=statistics.geometric_mean(r);direct.append(initial[k]/mean)
 row={'parent_mean_us':base*1e6,'parent_round_sd_us':statistics.stdev(a)*1e6,'candidate_mean_us':mean*1e6,'candidate_round_sd_us':statistics.stdev(b)*1e6,'paired_speedup_pct':(ratio-1)*100,'pair_speedup_pct':[(v-1)*100 for v in r],'initial_mean_us':initial[k]*1e6,'versus_initial_speedup_pct':(initial[k]/mean-1)*100,'theoretical_peak_pct':343597383680/(mean*2250e12)*100}
 assert math.isclose(mean,s['shapes'][str(k)]['candidate_round_means_s']['mean'],abs_tol=1e-15)
 per[str(k)]=row
ratio=statistics.geometric_mean(ratios)
assert math.isclose(ratio,s['aggregate']['paired']['speedup'],rel_tol=1e-13)
for p in [Path(__file__),D/'summary.json',M/'manifest.json',M/'telemetry.jsonl',R/'runs/main-clean-series-001/baseline/benchmark-001/timing.json',C/'correctness-qualification.json']+[R/'scripts'/n for n in ['kda_bench.py','kda_compare.py','kda_run.py']]:pins[str(p)]=sha(p)
out={'passed':True,'samples':samples,'shapes':per,'aggregate_speedup_pct':(ratio-1)*100,'elapsed_reduction_pct':(1-1/ratio)*100,'direct_initial_speedup_pct':(statistics.geometric_mean(direct)-1)*100,'min_pair_speedup_pct':(min(ratios)-1)*100,'max_pair_speedup_pct':(max(ratios)-1)*100,'all_three_above45':all(v['theoretical_peak_pct']>45 for v in per.values()),'input_sha256':pins,'telemetry_samples':len(rows)}
with (C/('performance-audit-'+args.attempt+'.json')).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'},indent=2))
