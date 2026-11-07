# Iter092 目标v2完成审计

按当前主工作区与实验工作区一致的basic-flow.md逐项审核。不是仅检查pass标签：最终文件哈希、所有监控、原始660时间区间、30相邻配对和两轮逐负载理论利用率已重新计算核对。所有要求有证据，未缩小工作负载或容差。

| 要求 | 结论 | 证据 |
|---|---|---|
| Task scope and metric: original3head64 workloads; actual TFLOPS /2250TFLOPS >45%, not NCU activity | proven | docs/kda/basic-flow.md, executable-plan.md |
| Executable plan frozen before implementation; baseline, GPU, workload, risks, ranked choice, commands and adoption criteria recorded | proven | executable-plan.md, plan-freeze.json, source-generation.json |
| Original CUDA C++/PTX implementation; candidate only7phase1 substitutions relative082; existing scope preserved | proven | source-edit.diff, source-generation.json, source-snapshot/phase1.cuh |
| Source, compiled mechanisms, lifetimes, full mask bits, output mapping and negative controls verified before GPU | proven | root-cpu-qualification.json, native-composition.json, native-controls.json, native-mask-controls.json |
| Formal package has exact audited target native128/nondebug resources; all52other cubins preserve executable identity | proven | root-formal-qualification.json, actual-package-audit.json, other-cubins-audit.json |
| Final live source/package equals validated adopted artifact, all8files bound; baseline/parent archives retained | proven | artifact.json, decision.json, package/flash_mla/cuda.abi3.so |
| All original316 cases plus tail6/witness16/29per-role diagnostics passed;87arrays423174144 elements bitwise, including NaN payload and signed zero | proven | correctness-qualification.json, original-001-monitor/stdout.log, diagnostic-differential-001.json |
| Original benchmark/test scripts, seeds, params, warmup, flush, cooldown and timing protocol unchanged; immutable initial baseline retained | proven | baseline/benchmark-001/timing.json, comparison-001-prelaunch.json, comparison-002-prelaunch.json, performance-audit-001.json, performance-audit-002.json |
| Same UUID/physical7/logical0 throughout; three idle samples per launch; every sample free of foreign activity; all7stages serial | proven | *-monitor/manifest.json, *-monitor/telemetry.jsonl |
| Two predeclared complete330 comparisons, all660samples/30pairs included; no selective stopping or favorable rerun selection | proven | executable-plan.md, performance-audit-001.json, performance-audit-002.json, pooled-performance-audit.json |
| Both replicate aggregate gains and pooledGM strictly>0.5%; no per-shape regression; adopted only after full evidence | proven | decision.json, pooled-performance-audit.json |
| Every original shape strictly>45% theoretical utilization in BOTH full comparisons, recomputed from raw time intervals | proven | comparison-001/*.json, comparison-002/*.json, performance-audit-001.json, performance-audit-002.json |
| Latest cleanworktree request preserved:main-clean-36/main395cb3a clean;18..35 also untouched | proven | decision.json, git status --porcelain --untracked-files=all --ignored on18..36 |
| Markdown report includes per-shape parent/initial results, variation, aggregation, adoption, full failure history and current retained gains at top | proven | REPORT.md, docs/kda/performance.md |
| Exact commands/environment/compiler/driver/artifacts/raw data preserved; no device or benchmark changes | proven | formal-build-001/manifest.json, cpu-build/attempt-001/compile-argv.json, artifact.json, final-environment.json, *-prelaunch.json |

两轮逐负载理论利用率：

```json
{
  "001": {
    "4096": 46.324888405009034,
    "8192": 46.19538154391854,
    "32768": 45.151763997974726
  },
  "002": {
    "4096": 46.31999575297919,
    "8192": 46.19943723924047,
    "32768": 45.13658478301067
  }
}
```

全量正确性、每轮>0.5%采用门槛、三负载每轮>45%目标及报告均完成。当前最佳092已保留；main-clean-36保持干净。目标是约定设备与负载下的验证结果，并非全形状全设备或全局最优证明。
