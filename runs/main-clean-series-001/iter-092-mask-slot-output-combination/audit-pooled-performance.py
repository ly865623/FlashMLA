from pathlib import Path
import json,hashlib,statistics,math
C=Path(__file__).resolve().parent;R=C.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
audits=[read(C/('performance-audit-'+n+'.json')) for n in ['001','002']]
for a in audits:
 assert a['passed'] and a['samples']==330
 for p,h in a['input_sha256'].items():assert sha(Path(p))==h,p
all_ratios=[];shapes={};direct=[]
for k in ['4096','8192','32768']:
 controls=[];candidates=[];ratios=[]
 for n in ['001','002']:
  d=C/('comparison-'+n);s=read(d/'summary.json');a=[];b=[]
  for rec in s['runs']:
   x=read(d/(rec['name']+'.json'));y=next(x for x in x['measurements'] if str(x['case']['s_kv'])==k)
   raw=[end-start for start,end in y['time_ranges_s']];assert raw==y['samples_s'] and len(raw)==10
   (a if rec['version']=='A' else b).append(statistics.mean(raw))
  assert len(a)==6 and len(b)==5
  ratios.extend(math.sqrt(a[i]*a[i+1])/b[i] for i in range(5));controls+=a;candidates+=b
 assert len(ratios)==10 and len(controls)==12 and len(candidates)==10
 mean=statistics.mean(candidates);initial=audits[0]['shapes'][k]['initial_mean_us'];r=statistics.geometric_mean(ratios)
 shapes[k]={'parent_mean_us':statistics.mean(controls)*1e6,'parent_round_sd_us':statistics.stdev(controls)*1e6,'candidate_mean_us':mean*1e6,'candidate_round_sd_us':statistics.stdev(candidates)*1e6,'paired_speedup_pct':(r-1)*100,'pair_speedup_pct':[(v-1)*100 for v in ratios],'initial_mean_us':initial,'versus_initial_speedup_pct':(initial/(mean*1e6)-1)*100,'theoretical_peak_pct':343597383680/(mean*2250e12)*100}
 direct.append(initial/(mean*1e6));all_ratios+=ratios
assert len(all_ratios)==30
r=statistics.geometric_mean(all_ratios);gain=(r-1)*100
replicates=[a['aggregate_speedup_pct'] for a in audits]
no_regression=all(x['paired_speedup_pct']>=-0.1 for x in shapes.values())
adopt=gain>0.5 and all(x>0.5 for x in replicates) and no_regression
goal=all(a['all_three_above45'] for a in audits) and adopt
out=dict(passed=True,samples=660,paired_ratios=30,shapes=shapes,replicate_aggregate_speedup_pct=replicates,aggregate_speedup_pct=gain,elapsed_reduction_pct=(1-1/r)*100,direct_initial_speedup_pct=(statistics.geometric_mean(direct)-1)*100,no_material_shape_regression=no_regression,adoption_gate_passed=adopt,goal_achieved=goal,input_sha256={str(p):sha(p) for p in [Path(__file__),C/'executable-plan.md',C/'plan-freeze.json',C/'performance-audit-001.json',C/'performance-audit-002.json']},method='all30 neighbor-paired raw ratios geometric mean; both complete330 replicates included; no selective stopping')
with (C/'pooled-performance-audit.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
