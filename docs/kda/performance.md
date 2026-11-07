# head64 prefill 性能报告

**目标v2已达标。** 原benchmark实测TFLOPS除以B200 BF16 dense额定峰值2250 TFLOPS，三组原负载在预声明的两轮完整测量中均严格超过45%。下面iter001–007的NCU周期利用率与旧完成审计保留为历史诊断，不作为本次达标依据。

当前最佳为 iter092：在082基础上组合提前mask选择、QK范围previous KV slot维护和O TMA evict-first。完整原正确性与423,174,144元素逐位比较通过；660样本汇总相对082加速0.677354%，耗时降低0.672796%，两轮各自均超过0.5%，已采用。三组汇总理论利用率46.322442%/46.197409%/45.144173%；最大负载两轮分别45.151764%/45.136585%。直接相对初始汇总加速20.747824%，未叠加历史收益。[092采用决定](../../runs/main-clean-series-001/iter-092-mask-slot-output-combination/decision.json) · [完成审计](../../runs/main-clean-series-001/iter-092-mask-slot-output-combination/completion-audit.md)。

| 优化点 | 迭代 | 对比对象 | 各负载加速（4096/8192/32768） | 汇总加速 / 耗时降低 | 当前保留 | 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| rowwise-max成对同步 | iter-001-rowmax-pair | 初始baseline的交错重测 | 0.138339% / 0.181489% / 0.227713% | 0.182507% / 0.182175% | 否，未达0.5%门槛 | [A/B原始结果](../../runs/main-clean-series-001/iter-001-rowmax-pair/comparison-001/summary.json) |
| 12.5% degree-5软件指数混用 | iter-005-softmax-poly5-mix | 初始baseline的交错重测 | 1.942094% / 1.892157% / 1.770365% | 1.868180% / 1.833919% | 是 | [有效A/B](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/comparison-001/summary.json) |
| 移除冗余循环开头pair barrier | iter-006-remove-loop-barrier | iter005交错重测 | 0.746801% / 0.713921% / 0.695035% | 0.718584% / 0.713457% | 否，iter007需恢复该同步 | [有效A/B](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/comparison-001/summary.json) |
| shared Q128 + TMEM Q384非dual QK | iter-007-nondual-qk | iter006交错重测 | 8.801719% / 8.807827% / 8.039307% | 8.549017% / 7.875720% | 是 | [有效A/B](../../runs/main-clean-series-001/iter-007-nondual-qk/comparison-001/summary.json) |
| 三输入rowmax平衡树 | iter-023-rowmax-tree | iter007交错重测 | 0.487759% / 0.502143% / 0.409369% | 0.466415% / 0.464250% | 否，汇总未达0.5%门槛 | [有效A/B](../../runs/main-clean-series-001/iter-023-rowmax-tree/comparison-002/summary.json) |
| 运行时全有效mask跳转 | iter-024-mask-branch | iter007交错重测 | 0.429211% / 0.397433% / 0.392600% | 0.406414% / 0.404769% | 否，汇总未达0.5%门槛 | [有效A/B](../../runs/main-clean-series-001/iter-024-mask-branch/comparison-001/summary.json) |
| producer全负索引符号位AND | iter-035-producer-sign-and | iter007，两份有效交错比较 | 0.563198% / 0.544178% / 0.456985% | 0.521443% / 0.518738% | 是 | [两次有效汇总](../../runs/main-clean-series-001/iter-035-producer-sign-and/combined-valid-results.json) |
| producer首索引有效时跳过invalid归约 | iter-036-producer-valid-first | iter035，五对交错比较 | 1.258047% / 1.271734% / 1.028585% | 1.186060% / 1.172158% | 是 | [有效A/B](../../runs/main-clean-series-001/iter-036-producer-valid-first/comparison-001/summary.json) |
| 条件pair rowmax交换及query末最大值合并 | iter-043-conditional-rowmax | iter036，两次有效完整比较 | 0.492276% / 0.486185% / 0.653666% | 0.544012% / 0.541069% | 是 | [660样本汇总](../../runs/main-clean-series-001/iter-043-conditional-rowmax/combined-valid-results.json) |
| 原mask acquire及共享读取提前到QK等待前 | iter-046-mask-before-qk | iter043，五对交错比较 | 1.050524% / 1.001062% / 0.835285% | 0.962249% / 0.953078% | 是 | [330样本有效A/B](../../runs/main-clean-series-001/iter-046-mask-before-qk/comparison-001/summary.json) |
| producer下一tile索引读取提前 | iter-049-producer-index-lookahead | iter046，五对交错比较 | 0.938406% / 0.884567% / 0.817318% | 0.880085% / 0.872407% | 是 | [330样本有效A/B](../../runs/main-clean-series-001/iter-049-producer-index-lookahead/comparison-001/summary.json) |
| 全有效mask选择值/跳转表加载提前到QK阻塞分支前 | iter-054-early-mask-selector | iter049，五对交错比较 | 0.414122% / 0.408990% / 0.278376% | 0.367143% / 0.365800% | 单项未采用；实现随092组合保留 | [330样本有效重算](../../runs/main-clean-series-001/iter-054-early-mask-selector/performance-audit-001.json) |
| 提前mask选择值/跳转表与平衡FTZ rowmax树组合 | iter-055-early-mask-rowmax | iter049，五对交错比较 | 0.403679% / 0.392771% / 0.342208% | 0.379549% / 0.378114% | 否，汇总未达0.5%门槛 | [330样本有效重算](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/performance-audit-001.json) |
| 跨query提前Q TMA | iter-063-early-next-q | iter049，五对交错比较 | 2.742242% / 2.683751% / 2.087281% | 2.503997% / 2.442829% | 是 | [330样本有效重算](../../runs/main-clean-series-001/iter-063-early-next-q/performance-audit-001.json) |
| O TMA写回EVICT_FIRST（仅32768局部收益） | iter-070-output-evict-first | iter063，五对交错比较 | -0.078605% / -0.079905% / +0.547431% | +0.129205% / +0.129038% | 单项未采用；实现随092组合保留 | [330样本有效重算](../../runs/main-clean-series-001/iter-070-output-evict-first/performance-audit-001.json) |
| 提前mask/平衡rowmax与O EVICT_FIRST组合（32768收益） | iter-071-consumer-output-combined | iter063，两次完整交错比较 | -0.194422% / -0.161386% / +0.522118% | +0.054893% / +0.054862% | 否，未达预声明采用门槛 | [660样本有效重算](../../runs/main-clean-series-001/iter-071-consumer-output-combined/pooled-performance-audit.json) |
| QK分支内缓存前一KV槽（小幅收益） | iter-074-qk-scoped-prev-slot | iter063，五对交错比较 | +0.437365% / +0.399205% / +0.113829% | +0.316696% / +0.315696% | 单项未采用；实现随092组合保留 | [330样本有效重算](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/performance-audit-001.json) |
| 静态gather half设备函数（4096/8192局部收益） | iter-081-outlined-gather-half | iter063，五对交错比较 | +0.442612% / +0.437478% / -0.020422%（32768噪声） | +0.286321% / +0.285503% | 否，汇总未达0.5%门槛 | [330样本有效重算](../../runs/main-clean-series-001/iter-081-outlined-gather-half/performance-audit-001.json) |
| 单个32笔gather设备函数 | iter-082-outlined-gather-tile | iter063，五对交错比较 | +0.817187% / +0.823722% / +0.564753% | +0.735148% / +0.729783% | 是 | [330样本有效重算](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/performance-audit-001.json) |
| O提交后计算/写回元数据（4096/8192局部收益） | iter-091-late-metadata | iter082，五对交错比较 | +0.139466% / +0.174993% / +0.028625%（32768噪声） | +0.114342% / +0.114212% | 否，汇总未达0.5%门槛 | [330样本有效重算](../../runs/main-clean-series-001/iter-091-late-metadata/performance-audit-001.json) |
| early mask / QK previous slot / O EVICT_FIRST组合 | iter-092-mask-slot-output-combination | iter082，两轮完整交错比较 | +0.505191% / +0.504860% / +1.022897% | +0.677354% / +0.672796% | 是；三负载两轮均>45% | [660样本有效重算](../../runs/main-clean-series-001/iter-092-mask-slot-output-combination/pooled-performance-audit.json) |



历史048双P缓冲方案已拒绝：有效330样本相对046汇总速度下降0.259568%，全部15个配对回退；当时源码与运行包恢复046，随后049通过完整验证并已采用。[048完整记录](../../runs/main-clean-series-001/iter-048-double-p-buffer/decision.json)。

工作区 `/home/liuyong/FlashMLA-main-clean`，分支 `worktree/main-clean`。协议见 [执行计划](../draft.md)，任务约定见 [basic-flow.md](basic-flow.md)。所有时间以 Asia/Shanghai 记录。

| 迭代 | 优化/事件 | 正确性 | 相对初始/父版本收益 | 状态与证据 |
| --- | --- | --- | --- | --- |
| baseline-build-001 | 未修改 main 的首次构建 | N/A | N/A | 失败：CUTLASS 初始化尚未完成，缺少 cutlass/bfloat16.h；[原始日志](../../runs/main-clean-series-001/baseline/build.log)。等待依赖完成后重建。 |

## 2026-11-04 16:21：初始化比较系列 main-clean-series-001

尚未运行 GPU correctness/benchmark。初次多次设备采样显示空闲卡在采样期间被其他任务占用，因此继续选择设备；[原始设备记录](../../runs/main-clean-series-001/device-selection.json)。本系列不复用旧 worktree 的结果或产物。

## 2026-11-04 16:26：基线构建检查失败，验证工具链

`baseline-build-002`：CUDA 13.2.78 完成 35 个 translation units 和 extension 链接，但仓库自身的 spill 检查退出 1。报错来自已有 head64 sparse decode，目标 head64 prefill 在 SM100a/SM103a 都为 152 registers、0 stack / spill stores / spill loads。没有修改源码或关闭检查；性能/正确性均 N/A。

证据：[构建日志](../../runs/main-clean-series-001/baseline/build-002.log)、[构建规则](../../runs/main-clean-series-001/baseline/build-cuda132.ninja)、失败产物保存在 `baseline/failed-cuda132-package/`。开始使用仓库允许的 CUDA 13.1 验证能否通过原检查；尚未测量初始基线，因此工具链选择仍在基线准备阶段。

已固定物理 GPU 7，B200，UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。[选择依据](../../runs/main-clean-series-001/device-selection-002.json)、[设备标识](../../runs/main-clean-series-001/device.json)。其三次连续采样无 compute process、利用率 0%、显存仅 1–4 MiB 驱动残留。

## 2026-11-04 16:27：基线构建成功

`baseline-build-003`：NVCC 13.1.115，原 setup.py、原源码完整构建退出 0，寄存器溢出检查通过（仅保留仓库已有 upstream CUTLASS 豁免）。本系列后续候选和对照统一使用此工具链；不把编译器选择计作 kernel 优化收益。

- [准确命令、产物 SHA256](../../runs/main-clean-series-001/baseline/artifact.json)
- [构建日志](../../runs/main-clean-series-001/baseline/build-003-cuda131.log)
- [初始源码归档](../../runs/main-clean-series-001/baseline/source.tar)、[原实现 diff（空）](../../runs/main-clean-series-001/baseline/source.patch)
- 完整原始 suite 运行中：[日志](../../runs/main-clean-series-001/baseline/correctness-001/stdout.log)、[设备监控与退出状态](../../runs/main-clean-series-001/baseline/correctness-001/manifest.json)。

## 2026-11-04 16:28：原始基线正确性通过

`baseline-correctness-001`：原始 `tests/test-sparse-prefill.py --run-to-finish` 全部 316 cases 通过，退出 0。监控未发现外来进程或查询错误，manifest `valid=true, contaminated=false`。其中 314 cases 做数值比较、2 个 s_q=70000 case 按原脚本仅检查可运行。五轮 head64 固定 benchmark 开始采集，性能和 TC 利用率结论仍待完整证据。

## 2026-11-04 16:30：初始固定 benchmark

五轮，每轮每个 workload 保留原始 10 个 kernel 样本和正确性比较；15 个 workload executions 全部通过，监控 valid=true。以下为每轮均值的均值 ± 样本标准差（微秒），不同于单次 kernel 样本的波动。

| s_kv | 初始基线 μs | 五轮范围 μs | 相对初始/父版本 |
| --- | ---: | ---: | --- |
| 4096 | 401.016500 ± 0.339129 | 400.444300–401.346900 | 1.000× / 0% |
| 8192 | 401.042960 ± 0.157821 | 400.869300–401.199400 | 1.000× / 0% |
| 32768 | 403.530180 ± 0.123358 | 403.355700–403.660400 | 1.000× / 0% |

[原始计时及全部样本](../../runs/main-clean-series-001/baseline/benchmark-001/timing.json)、[运行日志](../../runs/main-clean-series-001/baseline/benchmark-001/stdout.log)、[监控结果](../../runs/main-clean-series-001/baseline/benchmark-001/manifest.json)。后续对照重测另立目录，不覆盖本初始结果。

`baseline-profile-001`：NCU driver 启动失败（报缺少 --output；后续定位到 driver 名 profile.py 遮蔽 Python 标准库同名模块），退出2；无 kernel 采集，结果 N/A。[失败记录](../../profile/head64-baseline-kv8192/REPORT.md)。使用独立 driver 的明确 argv 在新目录重试。

## 2026-11-04 16:36：iter-001-rowmax-pair（待验证）

父版本：初始 main 395cb3a。假设：rowwise-max仅warp0/2、warp1/3成对交换，128-thread barrier引入了不必要的两组耦合；原source报告在紧邻该barrier的line252有333个barrier samples。只把这一个同步替换为两组64线程独立barrier，保留循环顶部pair同步、P交换、全部mbarrier和epilogue同步。

构建通过（NVCC13.1，原spill检查通过）。[源码补丁](../../runs/main-clean-series-001/iter-001-rowmax-pair/source.patch)、[产物hash/准确命令](../../runs/main-clean-series-001/iter-001-rowmax-pair/artifact.json)、[编译日志](../../runs/main-clean-series-001/iter-001-rowmax-pair/build.log)。正确性/逐负载时间/波动/相对初始和父版本收益均为 **N/A，等待固定GPU空闲执行**；尚未采用。当前源码是实验候选，当前已验证最佳仍为baseline。

GPU被其他任务重新占用，剩余baseline profiles及候选验证等待同一UUID，不换卡；[持续采样](../../profile/head64-baseline-kv4096/full-execution/telemetry.jsonl)。

逐PC复核补充：baseline的实际与理想shared wavefront均为15,848,904，额外wavefront为0；不采用仅依赖汇总bank-conflict规则的P/S布局改动。见 [NCU诊断](../../profile/head64-baseline-kv8192-r2/REPORT.md)。

## 2026-11-04 16:42：iter-001 正确性通过

原始316 cases全部通过，exit=0，监控valid=true、contaminated=false。[正确性日志](../../runs/main-clean-series-001/iter-001-rowmax-pair/correctness-001/stdout.log)、[监控](../../runs/main-clean-series-001/iter-001-rowmax-pair/correctness-001/manifest.json)。交错A/B五对已排队开始，采用决定待结果。

## 初始 NCU 三组利用率

| s_kv | Tensor core elapsed | Tensor core active | 45%目标 |
| --- | ---: | ---: | --- |
| [4096](../../profile/head64-baseline-kv4096/REPORT.md) | 40.537727% | 41.680688% | 未达成 |
| [8192](../../profile/head64-baseline-kv8192-r2/REPORT.md) | 40.506992% | 41.643883% | 未达成 |
| [32768](../../profile/head64-baseline-kv32768/REPORT.md) | 40.387628% | 41.601590% | 未达成 |

以上为NCU默认replay/clock/cache控制下的计数，elapsed为本任务目标口径；性能采用使用原kernelkit，二者明确区分。

## 2026-11-04 16:47：iter-001 测量完成，拒绝

A0/B0/A1/.../B4/A5：A为归档初始baseline，B为候选；各轮三组原输入/原10次kernelkit benchmark，输入/产物hash校验通过，monitor valid=true。表中时间为外层轮均值的均值±标准差，收益按相邻A几何插值逐pair计算。

| s_kv | 初始基线 μs | 当前A μs | 候选B μs | 相对初始加速 | 相对父版本交错加速 | 相对父版本耗时降低 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 400.105733 ± 0.079656 | 399.554120 ± 0.210666 | 0.366003% | 0.138339% | 0.138148% |
| 8192 | 401.042960 | 400.996483 ± 0.214311 | 400.238060 ± 0.032368 | 0.201105% | 0.181489% | 0.181160% |
| 32768 | 403.530180 | 403.523567 ± 0.200054 | 402.619700 ± 0.159437 | 0.226139% | 0.227713% | 0.227196% |

等权几何平均相对初始加速0.264390%，相对交错父版本加速0.182507%（1.00182507×），耗时降低0.182175%。五对汇总加速范围0.150422%–0.210513%。该小幅重复收益不足采用门槛，撤回本轮同步改动；不能叠加到后续候选收益中。

[监控有效性](../../runs/main-clean-series-001/iter-001-rowmax-pair/comparison-001-monitor/manifest.json)、[完整A/B数据](../../runs/main-clean-series-001/iter-001-rowmax-pair/comparison-001/summary.json)、[决定](../../runs/main-clean-series-001/iter-001-rowmax-pair/decision.json)。未为拒绝候选额外采集TC，候选TC栏N/A，不宣称达到45%。

## 2026-11-04 16:51：iter-002-softmax-batch4 未形成机器码改动，拒绝

父版本baseline。将softmax每4个float2分批FMA/exp/求和，保持求和次序；编译成功，152 registers、0 spill。但去除cuobjdump容器头后，2656条SM100指令及编码/调度位与baseline完全相同。无实质机器码改变，未再运行GPU correctness/计时，逐负载和汇总比较均N/A，不将同一代码的计时噪声记作收益。

[补丁](../../runs/main-clean-series-001/iter-002-softmax-batch4/source.patch)、[构建](../../runs/main-clean-series-001/iter-002-softmax-batch4/build.log)、[产物](../../runs/main-clean-series-001/iter-002-softmax-batch4/artifact.json)、[codegen证据](../../profile/head64-iter002-codegen/REPORT.md)。决定：拒绝、撤回。

## 2026-11-04 16:53：iter-003-softmax-scalar-fma（待验证）

父版本baseline。head64局部用两条fma.rn.f32替代每条fma.rn.f32x2，保留RN运算、exp2、sum次序及所有同步；用于检验packed临时寄存器复用是否限制调度。编译通过，154 registers（原152）、0 spill；SASS确实从16条FFMA2变为scalar FFMA，仍重复使用一个临时寄存器，因此收益不能由源码推断。原316正确性正在运行，性能/采用决定待验证。

[补丁](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/source.patch)、[构建](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/build.log)、[产物](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/artifact.json)、[SASS](../../profile/head64-iter003-codegen/REPORT.md)。

## 2026-11-04 17:00：iter-003 首次A/B无效，重测

原316cases通过，correctness monitor valid=true。comparison-001完成所有A/B进程，但监控在末尾发现外来GPU PID891805（2026-11-04T08:59:36.521658Z）；监控valid=false、contaminated=true。本轮逐负载/汇总比较填N/A，不使用其计时得出收益或回退结论。原始数据保留，comparison-002在同一UUID重测相同5对协议。

[无效原始数据](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/comparison-001/summary.json)、[污染证据](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/comparison-001-monitor/telemetry.jsonl)、[无效状态](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/comparison-001-monitor/manifest.json)。

## 2026-11-04 17:05：iter-003 有效重测，拒绝回退

comparison-002在同一UUID按相同五对协议完成，monitor valid=true、contaminated=false；全部benchmark正确性通过。

| s_kv | 初始baseline μs | 当前A μs ± std | B μs ± std | 相对初始加速 | 相对父版本交错加速 | 耗时降低（负值为变慢） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 400.283400 ± 0.165923 | 410.129740 ± 0.083857 | -2.222038% | -2.402456% | -2.461595% |
| 8192 | 401.042960 | 400.809550 ± 0.179031 | 410.959940 ± 0.132057 | -2.413126% | -2.469474% | -2.532001% |
| 32768 | 403.530180 | 403.557983 ± 0.198344 | 413.321320 ± 0.314955 | -2.368893% | -2.370952% | -2.428531% |

汇总相对交错父版本加速比0.975856975×，耗时增加2.474033%；相对初始baseline加速-2.334720%。拒绝、恢复baseline，不能沿用首次无效测量得出结论。

[有效数据](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/comparison-002-monitor/manifest.json)、[决定](../../runs/main-clean-series-001/iter-003-softmax-scalar-fma/decision.json)。

## 2026-11-04 17:07：iter-004-double-s（待验证）

父版本baseline。新增S与SO-ready双缓冲；S[k]只需等SV[k−2]释放对应槽，需要rescale时额外等SV[k−1]。使用全局rs管理双槽phase，同时MMA在下一query的Q TMA前显式等待复用KV槽释放，保留跨query安全性。原数学、精度、其它同步和测试参数不变。编译通过，152 registers、0 spill。

[源码补丁](../../runs/main-clean-series-001/iter-004-double-s/source.patch)、[构建](../../runs/main-clean-series-001/iter-004-double-s/build.log)、[产物](../../runs/main-clean-series-001/iter-004-double-s/artifact.json)。正确性/性能暂为N/A，待固定GPU验证。

## 2026-11-04 17:11：iter-004 有效测量，拒绝回退

原316 cases通过（314数值比较、2按原脚本只运行），correctness与五对交错benchmark的monitor均valid=true、contaminated=false，所有benchmark数值检查通过。固定GPU UUID为 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。

| s_kv | 初始baseline μs | 当前A μs ± std | B μs ± std | 相对初始加速 | 相对父版本交错加速 | 耗时降低（负值为变慢） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 400.230833 ± 0.177154 | 405.750580 ± 0.081949 | -1.166746% | -1.356392% | -1.375043% |
| 8192 | 401.042960 | 400.965867 ± 0.209631 | 406.510600 ± 0.174124 | -1.345018% | -1.353512% | -1.372083% |
| 32768 | 403.530180 | 403.549867 ± 0.160837 | 408.923800 ± 0.167476 | -1.318979% | -1.313233% | -1.330709% |

汇总交错加速比0.986589524×（-1.341048%），耗时增加1.359276%；相对初始baseline加速-1.276946%。五对汇总均回退，各组无已验证局部收益，拒绝并恢复baseline源码。候选TC为N/A，未额外profile拒绝版本。

[正确性](../../runs/main-clean-series-001/iter-004-double-s/correctness-001/manifest.json)、[计时与波动](../../runs/main-clean-series-001/iter-004-double-s/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-004-double-s/comparison-001-monitor/manifest.json)、[同步审查](../../runs/main-clean-series-001/iter-004-double-s/synchronization-review.md)、[决定](../../runs/main-clean-series-001/iter-004-double-s/decision.json)。

## 2026-11-04 17:24：iter-005-softmax-poly5-mix（待验证）

父版本baseline；head64 softmax中12.5%元素采用degree-5软件exp2，有限[-126,127] guard外维持原exp2f。原求和顺序、BF16转换、其他数学与同步不变。NVCC13.1构建退出0，152 registers、0 spill。CPU采样仅验证多项式局部数值，不能代替GPU suite。完整正确性与交错测量待完成，性能及TC暂为N/A。

[参考及数值约束](exp2-reference-notes.md)、[补丁](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/source.patch)、[构建](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/build.log)、[产物](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/artifact.json)。

## 2026-11-04 17:29：iter-005 有效测量，保留

原316 cases及全部benchmark数值比较通过；correctness和comparison-001外层monitor均valid=true、contaminated=false。设备UUID不变。五对汇总加速1.851706%–1.882301%，最大相邻对照漂移逐组为0.130989%/0.085406%/0.109629%，明显小于重复收益。

| s_kv | 初始baseline μs | 当前A μs ± std | B μs ± std | 相对初始加速 | 相对父版本交错加速 | 耗时降低 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 400.261250 ± 0.174900 | 392.643420 ± 0.170575 | 2.132490% | 1.942094% | 1.905095% |
| 8192 | 401.042960 | 400.697550 ± 0.158696 | 393.255140 ± 0.087257 | 1.980348% | 1.892157% | 1.857019% |
| 32768 | 403.530180 | 403.247767 ± 0.158429 | 396.229180 ± 0.053975 | 1.842620% | 1.770365% | 1.739568% |

汇总相对初始baseline加速1.985084%，相对交错父版本加速1.868180%（1.018681797×）、耗时降低1.833919%。通过采用门槛，保留为当前最佳；该测量不是与rowmax-pair相加的组合收益。SASS显示额外多项式让编译器更早生成多个独立scale结果，同时4个fallback MUFU带谓词；性能变化不能全部归因于MUFU数量。三组NCU待完成后继续审计45%目标。

[正确性](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/correctness-001/manifest.json)、[A/B全部样本](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/comparison-001/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/comparison-001-monitor/manifest.json)、[SASS审查](../../profile/head64-iter005-codegen/REPORT.md)、[决定](../../runs/main-clean-series-001/iter-005-softmax-poly5-mix/decision.json)。

## 2026-11-04 17:33：iter-006-remove-loop-barrier（待验证）

父版本为已保留iter005，只删除k循环开头的64-thread pair barrier；P_exchange上一轮读完成由rowmax的128-thread barrier保证，保留helper内部pair barrier保护rowmax_buf复用，其他同步不变。两份独立静态审查认为安全，仍需原测试验证。构建退出0，151 registers（父版本152）、0 spill。完整suite已排入同一UUID锁队列，不与NCU重叠。性能/TC暂为N/A。

[相对父版本补丁](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/parent.patch)、[相对main完整补丁](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/source.patch)、[产物](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/artifact.json)、[构建](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/build.log)。

## 2026-11-04：iter-005 三组NCU完成，目标尚未达到

三组full+PM/source均在固定UUID完成且valid=true。

| s_kv | 初始TC elapsed | iter005 TC elapsed | iter005 TC active | elapsed绝对变化 | 证据 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4096 | 40.537727% | 41.471360% | 42.666275% | 0.933633 pp | [NCU证据](../../profile/head64-iter005-kv4096/REPORT.md) |
| 8192 | 40.506992% | 41.396393% | 42.609470% | 0.889401 pp | [NCU证据](../../profile/head64-iter005-kv8192/REPORT.md) |
| 32768 | 40.387628% | 41.302939% | 42.514621% | 0.915311 pp | [NCU证据](../../profile/head64-iter005-kv32768/REPORT.md) |

三组elapsed均未超过45%。8192逐PC显示softmax pred-on MUFU线程指令减少12.5%（167772160→146800640），四条guard fallback的pred-on计数均0；scale FFMA2上的short_scoreboard样本402/406（source/full）均降至0。MUFU等待下降但BF16 pack等待增加，SO-ready等待source下降、full略升，不能声称SO-ready已稳定改善。shared excessive wavefront仍0，无spill，继续研究同步和P交换。此处TC变化为百分点，不与计时加速比例混用；原benchmark收益不与NCU计时相加。

[8192逐PC对照](../../profile/head64-iter005-kv8192/analysis/softmax-comparison.txt)。完整原始报告、metrics、PM图和匹配源码快照保存在各profile目录。

## 2026-11-04 17:38：iter-006 有效测量，保留

原316 cases和所有benchmark数值检查通过，correctness与comparison-001均valid=true、contaminated=false，固定UUID不变。五对汇总加速0.681779%–0.769836%，全部超过0.5%；相邻A漂移最大逐组0.146022%/0.103487%/0.097803%。

| s_kv | 初始baseline μs | 父版本iter005 A μs ± std | iter006 B μs ± std | 相对初始加速 | 相对父版本交错加速 | 父版本耗时降低 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 392.349217 ± 0.211458 | 389.415160 ± 0.159916 | 2.979170% | 0.746801% | 0.741266% |
| 8192 | 401.042960 | 392.759833 ± 0.194183 | 390.003220 ± 0.183182 | 2.830679% | 0.713921% | 0.708860% |
| 32768 | 403.530180 | 395.707617 ± 0.231882 | 393.017560 ± 0.156574 | 2.674847% | 0.695035% | 0.690238% |

汇总交错相对父版本加速0.718584%（1.007185836×）、耗时降低0.713457%；相对不可变初始baseline直接测得加速2.828157%、耗时降低2.750372%。采用为当前最佳，不能将iter005与iter006不同测量的百分比相加。TC尚未测得，继续三组NCU。

[完整计时](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/comparison-001/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/comparison-001-monitor/manifest.json)、[决定](../../runs/main-clean-series-001/iter-006-remove-loop-barrier/decision.json)。

## 2026-11-04 17:44：iter006/4096首次NCU无效，准备同卡重测

[首次full监控](../../profile/head64-iter006-kv4096/full-execution/manifest.json)检测外来GPU进程，valid=false。即使ncu子进程退出0，此次TC/性能结果均N/A，source未启动；原报告和telemetry保留。改用 `profile/head64-iter006-kv4096-r2` 重测同UUID，不切卡、不终止其他用户任务。已完成的8192 full/source仍为valid=true。

## 2026-11-04 17:46：iter-007-nondual-qk 实现与构建（验证结论见后文）

父版本iter006。shared Q128+TMEM Q384的WS M64N64 QK直接生成最终P，删除跨warp P交换与partial求和；TMA拆为两个Q描述符，原PV/S/O和KV三槽不变，补回loop pair barrier保证单槽rowmax复用。固定NVCC13.1构建退出0；B200对应SM100a为168 registers（父版本151），SM103a为152，均0 spill。CPU sizeof动态shared仍222480 B，加静态1024 B；尚未用NCU测本候选。静态SASS确认48条Q UTCCP、32条QK MMA（8SS+24TS）和原8条PV MMA。CPU布局及实际diff审查通过，但K累加次序改变，此时尚待原316case证明；后续已通过，完整计时及采用结论见17:53段。此构建阶段性能/TC为N/A。

[完整补丁](../../runs/main-clean-series-001/iter-007-nondual-qk/source.patch)、[父版本补丁](../../runs/main-clean-series-001/iter-007-nondual-qk/parent.patch)、[产物](../../runs/main-clean-series-001/iter-007-nondual-qk/artifact.json)、[实际diff审查](../../runs/main-clean-series-001/iter-007-nondual-qk/implementation-review.md)、[构建](../../runs/main-clean-series-001/iter-007-nondual-qk/build.log)。

## 2026-11-04 17:53：iter-007 有效测量，保留

原316 cases通过（314数值比较、2原脚本run-only），correctness monitor valid=true；comparison-001五对完整交错、所有benchmark数值检查通过且valid=true、无外来竞争。五对汇总加速8.534043%–8.568845%，全部超过采用门槛。

| s_kv | 初始baseline μs | 父iter006 A μs ± std | iter007 B μs ± std | 相对初始加速 | 相对父版本交错加速 | 父版本耗时降低 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 401.016500 | 389.627133 ± 0.147456 | 358.091840 ± 0.137347 | 11.987053% | 8.801719% | 8.089688% |
| 8192 | 401.042960 | 390.266533 ± 0.220032 | 358.698440 ± 0.183400 | 11.805047% | 8.807827% | 8.094847% |
| 32768 | 403.530180 | 393.439217 ± 0.744655 | 364.089000 ± 0.610437 | 10.832840% | 8.039307% | 7.441094% |

相对父版本汇总加速比1.085490167×、耗时降低7.875720%；相对不可变初始baseline直接加速11.540494%、耗时降低10.346461%。保留iter007，并继续三组TC profile。不同迭代收益不相加；iter006的单独删除barrier不保留，因为P exchange消失后需补回它保护rowmax_buf。软件指数仍在当前组合中，最终收益以本次组合测量为准。

[正确性](../../runs/main-clean-series-001/iter-007-nondual-qk/correctness-001/manifest.json)、[全部样本](../../runs/main-clean-series-001/iter-007-nondual-qk/comparison-001/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-007-nondual-qk/comparison-001-monitor/manifest.json)、[采用决定](../../runs/main-clean-series-001/iter-007-nondual-qk/decision.json)、[codegen/资源](../../runs/main-clean-series-001/iter-007-nondual-qk/codegen-review.md)。

## 2026-11-04：iter006三组profile收尾

包含4096独立重测在内，三组full+PM/source均已完成且valid=true；第一次4096污染测量仍为N/A，不混入结果。

| s_kv | iter006 TC elapsed | TC active | 证据 |
| --- | ---: | ---: | --- |
| 4096 | 41.800841% | 42.965092% | [有效profile](../../profile/head64-iter006-kv4096-r2/REPORT.md) |
| 8192 | 41.727284% | 42.939076% | [有效profile](../../profile/head64-iter006-kv8192/REPORT.md) |
| 32768 | 41.530242% | 42.773502% | [有效profile](../../profile/head64-iter006-kv32768/REPORT.md) |

iter006三组均未达到45%。8192逐PC确认删除loop barrier，104条softmax算术指令保持与iter005相同；shared actual=ideal、excessive0、无local读写。该轮删除barrier已被iter007布局需要的同步取代，历史收益保留，不能描述为iter007仍包含这项删除。

## 2026-11-04：最终iter007三组NCU与交付审计

三组使用同一固定UUID、同一归档iter007 extension、原benchmark参数和seed。full+PM/source共六次采集均退出0、valid=true、无外来竞争；tensor core目标采用elapsed口径，active另列。

| s_kv | 初始TC elapsed | iter007 TC elapsed | iter007 TC active | elapsed绝对提升 | 证据 |
| --- | ---: | ---: | ---: | ---: | --- |
| 4096 | 40.537727% | 46.132773% | 47.560727% | 5.595047 pp | [有效full/source](../../profile/head64-iter007-kv4096/REPORT.md) |
| 8192 | 40.506992% | 46.103603% | 47.573632% | 5.596612 pp | [有效full/source](../../profile/head64-iter007-kv8192/REPORT.md) |
| 32768 | 40.387628% | 45.891123% | 47.253414% | 5.503495 pp | [有效full/source](../../profile/head64-iter007-kv32768/REPORT.md) |

三组均超过45%。8192逐PC动态证据显示P TMEM加载warp指令327680→163840，P交换STS/LDS各1310720→0、partial FADD2 2621440→0；shared实际/理想wavefront均从15848904降至5363144，excessive0、local读写0。新增Q复制和QK发行成本已包含在原benchmark测量中，不以指令数量推导收益。B200寄存器168，动态+driver预留shared223504 B，无spill。

最终代码仅修改head64的config.h与phase1.cuh，保留CUDA C++及API；未修改原测试、容差或负载。原316 cases全部通过，其中314数值比较、2按原脚本只运行；五对交错汇总相对父版本加速8.549017%、相对不可变初始baseline加速11.540494%（耗时降低10.346461%）。后者是最终组合直接测量，未累加历史收益。初始基线、拒绝候选、失败构建及两次污染测量均保留。

[最终产物及hash](../../runs/main-clean-series-001/iter-007-nondual-qk/artifact.json)、[最终完整补丁](../../runs/main-clean-series-001/iter-007-nondual-qk/source.patch)、[正确性](../../runs/main-clean-series-001/iter-007-nondual-qk/correctness-001/manifest.json)、[最终A/B](../../runs/main-clean-series-001/iter-007-nondual-qk/comparison-001/summary.json)、[8192机制对照](../../profile/head64-iter007-kv8192/REPORT.md)、[完成审计](../../runs/main-clean-series-001/completion-audit.md)。结论范围为固定B200和仓库现有工作负载；未将其外推为其他硬件或未测输入的性能保证。

## 2026-11-04：目标v2继续，iter007首次刷新无效

用户改为原benchmark TFLOPS/B200 BF16 dense额定峰值2250 TFLOPS，旧NCU elapsed完成状态不适用于新目标。源码/.so已核对等于归档iter007，继续同一UUID及既定协议。`goal-v2/iter007-refresh-001`子进程完成，但监控记录外来进程，valid=false；所有当前刷新性能/理论利用率填N/A，不能用作收益或达标证据。原日志与timing.json保留，改用独立目录refresh-002同卡重试。

[无效监控](../../runs/main-clean-series-001/goal-v2/iter007-refresh-001/manifest.json)、[遥测](../../runs/main-clean-series-001/goal-v2/iter007-refresh-001/telemetry.jsonl)、[历史v1快照](../../runs/main-clean-series-001/goal-v2/goal-v1-snapshot/performance.md)。

## 目标v2：iter007有效刷新与iter008构建

[分母与FLOPs依据](theoretical-utilization-reference.md)：原测试F=343597383680，固定B200 BF16 dense2250TFLOPS，>45%要求>1012.5TFLOPS及时间<339.355441μs。iter007-refresh-002五轮valid=true、全部数值检查通过，按轮调用原比较器核对参数/seed/runner/module/env与初始baseline一致；它是当前复测，不替换初始测量。

| s_kv | 刷新 μs ± 轮间std | TFLOPS | 理论利用率 |
| --- | ---: | ---: | ---: |
| 4096 | 358.721620 ± 0.314784 | 957.838515 | 42.570601% |
| 8192 | 358.750280 ± 0.121770 | 957.761994 | 42.567200% |
| 32768 | 363.899500 ± 0.160133 | 944.209551 | 41.964869% |

[有效刷新](../../runs/main-clean-series-001/goal-v2/iter007-refresh-002/manifest.json)、[原始样本](../../runs/main-clean-series-001/goal-v2/iter007-refresh-002/timing.json)、[理论换算](../../runs/main-clean-series-001/goal-v2/iter007-refresh-002/theoretical-utilization.json)。

iter008-double-rowmax以007为父版本：双槽rowmax并删除loop pair barrier，保留每轮128-thread rowmax barrier，复用由中间迭代barrier保护。构建退出0，SM100a168、SM103a150 registers，0 spill；未改数学与负载。原316cases正在运行，正式交错性能待验证，性能/采用暂N/A。

[补丁](../../runs/main-clean-series-001/iter-008-double-rowmax/parent.patch)、[构建](../../runs/main-clean-series-001/iter-008-double-rowmax/build.log)、[产物](../../runs/main-clean-series-001/iter-008-double-rowmax/artifact.json)。


## 2026-11-04：iter008完整正确性通过，启动固定协议比较

双槽rowmax候选使用归档扩展SHA256 `a2940eaf6c4592723859c7f5045d723397c49379bf31fa93f5e682d6d2f1210f`，原316cases全部通过（314数值比较、2个原run-only case）；退出0，固定UUID设备监控valid=true、无外来任务。静态同步审查通过，CPU sizeof probe确认动态shared222992B，相比父版增加512B；原spill检查通过。

证据：[正确性日志](../../runs/main-clean-series-001/iter-008-double-rowmax/correctness-001/stdout.log)、[有效性](../../runs/main-clean-series-001/iter-008-double-rowmax/correctness-001/manifest.json)、[同步审查](../../runs/main-clean-series-001/iter-008-double-rowmax/synchronization-review.md)。以007为A、008为B的原五对交错比较已启动，完整结果前不作采用决定；runner三个文件与冻结SHA256一致。

另按用户请求创建了 `/home/liuyong/FlashMLA-main-clean-2` / `worktree/main-clean-2`，基于原main `395cb3a` 且CUTLASS初始化完成、git状态干净；该目录保持为干净起点，本优化系列继续在原 `FlashMLA-main-clean`，不改变基线或评测协议。


## 2026-11-04：iter008双槽rowmax拒绝，收益未过门槛

以iter007为父版本，只有rowmax双槽及移除循环入口pair barrier。原316cases和五对交错比较均退出0，固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8` 全程监控valid=true。候选扩展SHA256 `a2940eaf6c4592723859c7f5045d723397c49379bf31fa93f5e682d6d2f1210f`。

| s_kv | 父007重测 μs ± SD | 候选008 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.015000 ± 0.154148 | 357.633460 ± 0.109256 | 0.100481% / 0.100380% | 12.130588% | 960.752900 / 42.700129% |
| 8192 | 358.495850 ± 0.549402 | 358.015620 ± 0.331745 | 0.143239% / 0.143034% | 12.018286% | 959.727354 / 42.654549% |
| 32768 | 363.884033 ± 0.450207 | 363.607680 ± 0.082898 | 0.097851% / 0.097755% | 10.979554% | 944.967344 / 41.998549% |

汇总交错加速 **0.113855%**、耗时降低0.113725%；相对不可变初始baseline直接加速11.708271%、耗时降低10.481114%。相邻A最大漂移分别0.102842%/0.289023%/0.299445%，小幅变化不构成足以保留的可复现收益；不能把消除barrier静态证据当性能收益。**拒绝**：未过>0.5%门槛，源码及工作区扩展恢复已验证iter007。当前最佳保持007，不将008加入收益汇总。全部候选均值仍高于339.355441μs，未达新目标。

[原始A/B及汇总](../../runs/main-clean-series-001/iter-008-double-rowmax/comparison-001/summary.json)、[有效设备监控](../../runs/main-clean-series-001/iter-008-double-rowmax/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-008-double-rowmax/comparison-001/theoretical-utilization.json)、[采用决定](../../runs/main-clean-series-001/iter-008-double-rowmax/decision.json)。


## 2026-11-04：iter009 shared Q64构建成功

父版本007；D_sQ128→64、P448→480及对应注释，保持其他同步/数学/流水不变。CPU穷举确认Q448、P与K切片和56次copy地址完整无误，动态shared214288B，比007减少8192B；QK保持32条K16，4SS+12TS+16TS，原K累加顺序不变。固定CUDA13.1完整增量构建exit0，原spill检查通过，SM100a168/SM103a152 registers、无spill。

归档扩展SHA256 `eb2bedad875e8b4703a70ebc94a4ace0d16fefaf211123b0693149c3f2b7a8e8`。完整316case已启动，正确性及性能结论待实际结果；当前最佳仍007。

[构建/产物](../../runs/main-clean-series-001/iter-009-shared-q64/artifact.json)、[相对007补丁](../../runs/main-clean-series-001/iter-009-shared-q64/parent.patch)、[CPU布局审查](../../profile/head64-dsq64-design/REPORT.md)。


## 2026-11-04：iter009完整正确性通过

原316cases全部通过（314数值比较、2原run-only），退出0；固定UUID监控valid=true、无污染。已启动007/009五对交错原benchmark，正确性通过不代表候选已经采用。[测试日志](../../runs/main-clean-series-001/iter-009-shared-q64/correctness-001/stdout.log)、[有效监控](../../runs/main-clean-series-001/iter-009-shared-q64/correctness-001/manifest.json)。


## 2026-11-04：iter009 comparison001受干扰，性能N/A

五对交错子进程完成退出0，但监控发现外来 `python` PID2029605（约972–1124MiB），manifest `valid=false, contaminated=true, foreign_compute_process_observed`。整次相对父版/初始版收益、时间及理论利用率均 **N/A**，不使用局部干净片段作采用判断。完整原始记录保留；comparison002在同UUID等候空闲后重跑，不终止外来进程、不更换GPU。

[无效监控](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-001-monitor/manifest.json)、[干扰证据](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-001/invalidity.json)、[原始数据（不可用于性能结论）](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-001/summary.json)。


## 2026-11-04：iter009有效重测回退，拒绝

comparison002在同UUID完成五对原交错，所有11轮子进程数值检查通过，外层退出0、valid=true、无外来任务。以下仅使用有效002；无效001不混入统计。父版本007，候选扩展SHA256 `eb2bedad875e8b4703a70ebc94a4ace0d16fefaf211123b0693149c3f2b7a8e8`。

| s_kv | 父007重测 μs ± SD | 候选009 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.012817 ± 0.206586 | 360.160020 ± 0.091201 | -0.591041% / -0.594555% | 11.343980% | 954.013118 / 42.400583% |
| 8192 | 358.628317 ± 0.181520 | 360.935700 ± 0.105140 | -0.629642% / -0.633631% | 11.112024% | 951.962867 / 42.309461% |
| 32768 | 363.945917 ± 0.202963 | 365.943360 ± 0.095188 | -0.536724% / -0.539620% | 10.271212% | 938.935970 / 41.730488% |

汇总交错加速 **−0.585809%**（耗时**增加0.589261%**）；相对不可变初始baseline仍加速10.908113%、耗时降低9.835270%，后者不能掩盖相对父版的回退。五个aggregate pair均回退0.543501%–0.644272%，三组均回退；**拒绝**，恢复007源码和工作区扩展。没有可收录的局部收益，新目标尚未达到。

实际SASS确认4SS/28TS、56UTCCP、8个Q-TMA atoms与零local/spill；QK主要发行窗口222→229条，寄存器搬运合计144→151。因此减少shared Q payload未转化为收益，且增加了prologue复制与发行开销；不能仅靠静态计数确定回退的唯一原因。

[有效A/B](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-002-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-009-shared-q64/comparison-002/theoretical-utilization.json)、[SASS审计](../../profile/head64-iter009-codegen/REPORT.md)、[决定](../../runs/main-clean-series-001/iter-009-shared-q64/decision.json)。


## 2026-11-04：CPU代码生成筛选与iter010

归档007的完整head64 TU重编译能复现全部2752条SM100a SASS及编码。25%软件指数候选（pairs3/7/11/15）维持SM100a168/SM103a152、零spill；regular MUFU28→24，额外40条SASS，收益尚未验证。同占比11/15与13/15保留为后备，不能把静态排布当作收益。[完整CPU探针报告](../../profile/head64-exp2-pair-probes/REPORT.md)。

另外，runtime full-valid mask快路径的普通if与__all_sync两次CPU探针均未生成绕过mask的真实分支，ptxas仍if-convert为谓词指令并增加静态指令；因此未应用到主kernel，正确性/性能为N/A。这类CPU拒绝记录不构成任何已验证收益。

下一候选iter010仅将007中的degree-5混用比例12.5%→25%，其他数学/布局/同步不变。实施前可执行计划已写入draft.md，构建进行中；008/009均已撤回，不叠加。


## 2026-11-04：iter010构建及原316cases通过

固定CUDA13.1原构建/spill检查通过，SM100a168/SM103a152、0spill，shared布局保持007。归档扩展SHA256 `dfa78ea806a09d3b9db7004936845dd740d6695051d5ec8aec07dff655c88b83`。原316cases全部通过（314数值比较，2原run-only），固定UUID监控valid=true、无污染，已启动原五对007/010交错比较；在有效测量前当前最佳保持007。

[构建/产物](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/artifact.json)、[正确性日志](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/correctness-001/stdout.log)、[有效监控](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/correctness-001/manifest.json)。


## 2026-11-04：iter010有效测量回退，拒绝

固定UUID原五对007/010交错完成，11轮数值检查均通过，外层exit0、valid=true、无污染。父007，候选扩展SHA256 `dfa78ea806a09d3b9db7004936845dd740d6695051d5ec8aec07dff655c88b83`。

| s_kv | 父007重测 μs ± SD | 候选010 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.057167 ± 0.126322 | 359.532920 ± 0.132860 | -0.416361% / -0.418102% | 11.538187% | 955.677115 / 42.474538% |
| 8192 | 358.815683 ± 0.037343 | 360.170280 ± 0.044619 | -0.376625% / -0.378048% | 11.348155% | 953.985942 / 42.399375% |
| 32768 | 364.174817 ± 0.137771 | 365.471360 ± 0.156879 | -0.359890% / -0.361190% | 10.413626% | 940.148590 / 41.784382% |

汇总交错加速 **−0.384295%**（耗时**增加0.385777%**）；相对不可变初始baseline直接加速11.098900%、耗时降低9.990108%。五个aggregate pair均回退0.339310%–0.423968%，各shape/pair也全部回退；相邻A最大漂移0.055464%/0.027846%/0.091479%。**拒绝**，恢复007的12.5% selector及工作区扩展。增加软件指数并未产生净收益，不将SFU指令减少或较均匀RAW静态排布当作有效加速；无可收录局部收益，目标仍未达到。

[有效A/B](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/comparison-001/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-010-softmax-poly5-quarter/decision.json)。


## 2026-11-04：iter011 shared Q192构建成功

基于007，只改D_sQ192/P416及注释，未叠加008–010。CPU布局与完整TU代码生成均已核验：QK32条变12SS+20TS，UTCCP40，Q-TMA8atoms，发行窗口222→209条；每tile增加8KiB shared Q读取，性能仍待测量。动态shared230672B，加driver预留1024B为231696B，分别在232448B opt-in及233472B/SM限制内。

正式CUDA13.1原构建exit0、原spill检查通过，SM100a168/SM103a152regs、0spill；归档扩展SHA256 `a1e572a53cba0a446bcfd51bc6cf6dd685858fa938c2210b1c79acabb909c74d`。原316case正在运行，当前最佳保持007。

[构建/产物](../../runs/main-clean-series-001/iter-011-shared-q192/artifact.json)、[父版补丁](../../runs/main-clean-series-001/iter-011-shared-q192/parent.patch)、[布局证据](../../profile/head64-dsq192-design/REPORT.md)、[CPU代码生成](../../profile/head64-dsq192-codegen/REPORT.md)。


## 2026-11-04：iter011原316通过，首次比较污染后同卡重测

原316cases全部通过（314数值比较、2原run-only），正确性运行exit0、valid=true。正式包两架构所有SASS机器编码与CPU probe一致，已有12SS+20TS/40UTCCP/209条issuer窗口计数适用。[正确性日志](../../runs/main-clean-series-001/iter-011-shared-q192/correctness-001/stdout.log)、[有效性](../../runs/main-clean-series-001/iter-011-shared-q192/correctness-001/manifest.json)、[正式包审计](../../profile/head64-dsq192-codegen/actual-package-audit.md)。

comparison001五对交错子进程完成exit0，但监控捕获外来 `python` PID2148570（2026-11-04T12:15:18–12:15:42Z，最高1124MiB），外层valid=false、contaminated=true。整轮耗时/父版与初始收益/理论利用率 **N/A**，不使用局部片段作采用决定。[无效监控](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-001-monitor/manifest.json)、[干扰证据](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-001/invalidity.json)。

comparison002已在同UUID重新启动，仍使用007为A/011为B及原五对协议；当前最佳仍007，011只作为工作区实验源码/归档扩展，不提前采用。旧v1 JSON审计已明确`goal_version=1,applies_to_current_goal=false`并指向冻结v1规格；原始未改审计仍保存在v1快照。


## 2026-11-04：iter011 comparison002再次污染，性能N/A

comparison002子进程完整结束exit0，但外层再次捕获外来GPU进程，`valid=false`。整次所有耗时、父版及初始收益、理论利用率均N/A；不以原始summary的表面结果决定采用或拒绝。原记录保留，并在相同UUID启动comparison003，协议不变。

[无效监控](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-002-monitor/manifest.json)、[全部外来进程证据](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-002/invalidity.json)。


## 2026-11-04：iter011第三次比较有效，回退后拒绝

固定UUID原五对007/011交错comparison003完成，11轮数值检查均通过，外层exit0、valid=true、无污染。001/002全部排除。父007，候选扩展SHA256 `a1e572a53cba0a446bcfd51bc6cf6dd685858fa938c2210b1c79acabb909c74d`。

| s_kv | 父007重测 μs ± SD | 候选011 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 357.967750 ± 0.079754 | 360.958560 ± 0.100078 | -0.828648% / -0.835572% | 11.097656% | 951.902578 / 42.306781% |
| 8192 | 358.602800 ± 0.134870 | 361.805520 ± 0.120159 | -0.892527% / -0.900565% | 10.844898% | 949.674244 / 42.207744% |
| 32768 | 363.921350 ± 0.112783 | 366.501520 ± 0.243234 | -0.703804% / -0.708793% | 10.103276% | 937.506026 / 41.666935% |

汇总交错加速 **−0.808357%**（耗时**增加0.814945%**）；相对不可变初始baseline直接加速10.681138%、耗时降低9.650369%。五个aggregate pair均回退0.750774%–0.828934%，各shape/pair也全部回退；相邻A最大漂移0.067107%/0.071255%/0.091580%。**拒绝**，恢复007源码和工作区扩展。静态减少13条issuer指令及8次Qcopy未转化为净收益，不能据此忽略增加shared Q读取的代价；没有单独NCU证明回退的唯一原因。无可收录局部收益，目标仍未达到。

[有效A/B](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-003/summary.json)、[监控](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-003-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-011-shared-q192/comparison-003/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-011-shared-q192/decision.json)。


## 2026-11-04：iter012两槽KV与全shared Q实现、构建中

父007；Q512常驻独立shared、移除Q的TMEM复制/UTCCP barrier，KV三槽改两槽；QK改成两个K256 SS视图，仍32条K16且按原序累加，P448、singleS、softmax数学与原epilogue不变。为保护跨query O/K0复用，四个producer的原O-done wait移到query tile loop之前，ack仍4次；Q expect65536B/等待保留在MMA callback入口。

同步审查与780序列依赖模型没有新增等待环，CPU布局Q/K各32768坐标及P4096坐标零错误，header预测动态shared206032B。减少48次Qcopy和三槽状态运算须与更多shared Q读取、较浅prefetch及K0输出等待的成本一并实测；不从静态简化推定性能。

可执行计划先于编辑写入draft.md。补丁/源码已归档，固定CUDA13.1构建进行中；正确性和性能N/A待验证。新worktree `FlashMLA-main-clean-2`保持干净。

[父版补丁](../../runs/main-clean-series-001/iter-012-full-shared-q/parent.patch)、[同步审查](full-shared-q-review.md)、[CPU布局](../../profile/head64-fullshared-design/REPORT.md)。


## 2026-11-04：iter012构建/静态审查通过，等待固定GPU空闲

原CUDA13.1构建exit0，原spill检查通过；SM100a/SM103a均168寄存器、0spill。正式object SASS确认40条WS MMA（32 QK+8 PV）、0 UTCCP、8 Q-TMA atoms，无LDL/STL。归档扩展SHA256 `7ba4b5512521bb4820ed2bf20b33719ec9d9c0944f7ff8f41c7ebe79579de3f9`。

独立实现审查通过：冻结snapshot与parent.patch相符，softmax/epilogue/12.5%helper/PV及globalrs等保留段与007逐字一致，实际header CPU sizeof206032、Q/K/P布局穷举零错误。[实现审查](../../runs/main-clean-series-001/iter-012-full-shared-q/implementation-review.md)、[产物](../../runs/main-clean-series-001/iter-012-full-shared-q/artifact.json)、[SASS](../../runs/main-clean-series-001/iter-012-full-shared-q/codegen/sm100a.sass.txt)。

原316case runner已经启动，但固定GPU有外来进程，正在等待空闲；尚无GPU正确性或性能结论。沿用同一session/UUID，不重启重复任务、不换卡。


## 2026-11-04：iter012原316通过，五对性能比较开始

原316cases全部通过（314数值比较、2原run-only），固定UUID正确性运行exit0、valid=true、contaminated=false。原runner因外来进程等待空闲后于12:40:26Z开始，12:42:20Z结束，保留完整监控。随后启动007/012原五对交错comparison001；当前最佳仍007。

[正确性日志](../../runs/main-clean-series-001/iter-012-full-shared-q/correctness-001/stdout.log)、[有效性](../../runs/main-clean-series-001/iter-012-full-shared-q/correctness-001/manifest.json)、[实际包CPU审计](../../profile/head64-iter012-codegen/REPORT.md)。CPU审计表明QK首次KV trywait至commit窗口224→158条、全SM100a SASS2752→2616；同时全kernel R2UR179→212，UR保存/恢复各45→55，因此不能把局部指令减少直接当作性能收益。

用户另行要求的新干净worktree已创建为 `/home/liuyong/FlashMLA-main-clean-3`，保持main `395cb3a`，不混入本系列优化源码。


## 2026-11-04：iter012有效测量明显回退，拒绝

固定UUID原五对007/012交错comparison001完成，11轮数值检查与原benchmark参数/源文件/产物核对均通过，外层exit0、valid=true、无污染。候选SHA256 `7ba4b5512521bb4820ed2bf20b33719ec9d9c0944f7ff8f41c7ebe79579de3f9`。

| s_kv | 父007重测 μs ± SD | 候选012 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.009633 ± 0.124376 | 477.479620 ± 0.572954 | -25.015738% / -33.361318% | -16.013902% | 719.606386 / 31.982506% |
| 8192 | 358.832567 ± 0.190651 | 478.047800 ± 0.204615 | -24.940442% / -33.227536% | -16.108188% | 718.751103 / 31.944493% |
| 32768 | 364.099600 ± 0.214893 | 531.908300 ± 0.289945 | -31.543687% / -46.078565% | -24.135386% | 645.971089 / 28.709826% |

汇总交错加速 **−27.233770%**，耗时**增加37.426385%**；相对不可变初始baseline直接加速−18.843730%、耗时增加23.219069%。全部shape/pair均回退，最大相邻A漂移0.097315%/0.116938%/0.177767%，远小于回退。拒绝，不收录任何局部收益。静态issuer缩短没有转化为性能，较大s_kv回退更严重；尚不能区分两槽预取距离、shared Q读取和跨query O等待的贡献。

以冻结012包启动8192 full/source NCU进一步诊断；为让采集时源码与lineinfo匹配，工作区012仅暂留至采集结束，随后恢复007。当前最佳一直为007，新目标未达。

[有效A/B](../../runs/main-clean-series-001/iter-012-full-shared-q/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-012-full-shared-q/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-012-full-shared-q/comparison-001/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-012-full-shared-q/decision.json)。


iter012诊断NCU首次full子进程exit0，但监控发现外来进程、valid=false，整次剖析结论N/A；保留[无效记录](../../profile/head64-iter012-kv8192/analysis/invalidity.json)，另目录同UUID重试，不影响此前有效五对benchmark的拒绝决定。

iter012第二次8192 full也被外来PID2324915干扰（子进程exit0，valid=false）；[r2无效记录](../../profile/head64-iter012-kv8192-r2/analysis/invalidity.json)保留，剖析结论N/A，在同UUID新r3目录重试。


## 2026-11-04：iter012有效full诊断与iter013实施准备

012第三次8192 full采集有效，source仍等固定GPU空闲。相对007，eligible warps0.651152→0.366327，issue44.326464%→30.575001%；首半KV ready long-scoreboard23→870、QKdone1093→6143，MMA MIO190→0；shared LSU actual/ideal均5363144、无spill，DRAM字节与L2命中近似不变。证据支持预取/流水重叠不足，不能精确分离两槽、fullshared Q和O alias等待的贡献。[当前诊断](../../profile/head64-iter012-kv8192-r3/REPORT.md)。

iter013执行计划先于实现追加draft，基于007在独立snapshot构建N128 QK+独立K/V流水。CPU softmax64局部probe直接扩展出现spill，232/96/96寄存器分配可消除局部spill，但完整候选新增producer/MMA寄存器仍需检查。所有隔离构建失败和修正均保留，尚无013 GPU正确性/性能结果；007为当前最佳。


012 r3 source随后也有效完成：QKdone long-scoreboard1238→6713、KV0 23→799、Odone13→296，支持full中的就绪等待扩大结论。[完整诊断](../../profile/head64-iter012-kv8192-r3/REPORT.md)。采集完毕后已恢复007源码/扩展，再应用冻结013实验源码，正式构建开始；两次污染剖析均不使用。


## 2026-11-04：iter013 N128完整实现资源修正与正式构建

父007，未保留012。实现独立K128KiB/V64KiB、Q128shared+Q384TMEM、N128 QK及两半PV；G>=1、物理topk%64尾部在global LD前guard、64bit mask双槽、CLC274。保留原single rowmax/pair barrier和12.5%软件exp。隔离实现先于主目录应用完成双架构完整TU、实际header布局与同步模型检查。

| 隔离attempt / 动态WG寄存器 | SM100a stack / spill store / load B | SM103a stack / spill store / load B | 结论 |
| --- | ---: | ---: | --- |
| 001 / 232,96,96 | 160 / 192 / 212 | 296 / 644 / 692 | 资源门槛失败，性能N/A |
| 002 / 232,128,128 | 24 / 32 / 40 | 136 / 188 / 196 | 资源门槛失败，性能N/A |
| 003 / 200,152,152 | 0 / 0 / 0 | 0 / 0 / 0 | 通过，静态initial REG两架构均168 |

三次NVCC均exit0，但前两次出现spill，不作为有效候选；未改编译选项或关闭检查。最终动态池128×(200+152+152)=64512，等于初始384×168；两个donor均在依赖wait之前释放，供WG0增量4096。实际sizeof230624，加driver1024为231648，距固定设备限制余1824B；P/S8192、K65536、Q24576及V32768坐标零差异。完整跨query模型3905序列无环，10个破坏性对照被检出；这不能替代GPU数值验证。

正式CUDA13.1原setup构建exit0、原spill检查通过。扩展SHA256 `fd0f2d4529c6bb58d0b7b63a0d7d4fa114c3e4f77fb8d2774b4f481f5fbd8f67`，原316case runner已启动，结果待定。之后另做6个物理topk192/320和logical边界专项，仍复用原reference与容差；未修改原suite。单V槽PVlo→Vhi load→PVhi存在暴露gather延迟风险，性能必须实测；当前最佳007不变。

[正式产物](../../runs/main-clean-series-001/iter-013-n128-independent-kv/artifact.json)、[实现/资源报告](../../runs/main-clean-series-001/iter-013-n128-independent-kv/implementation-report.md)、[CPU验证](../../runs/main-clean-series-001/iter-013-n128-independent-kv/cpu-validation.json)、[同步模型](n128-independent-kv-sync-review.md)、[专项计划](../../runs/main-clean-series-001/iter-013-n128-independent-kv/tail-tests/README.md)。


## 2026-11-04：iter013原316通过，专项尾部验证开始

原316 cases全部通过（314数值比较、2原run-only），固定UUID监控exit0、valid=true、无污染。正式包两架构全部SASS与attempt003逐条编码一致，动态200/152/152、initial168、0spill均确认；cubin文件差异仅调试路径/内部symbol元数据。随后启动6个额外tail case，结果未出前不进行性能采用。

[原正确性日志](../../runs/main-clean-series-001/iter-013-n128-independent-kv/correctness-001/stdout.log)、[监控](../../runs/main-clean-series-001/iter-013-n128-independent-kv/correctness-001/manifest.json)、[正式包审计](../../runs/main-clean-series-001/iter-013-n128-independent-kv/actual-package-audit.md)。


## 2026-11-04：iter013额外6个尾部case有效通过

物理topk192/320、有/无logical length、交错G1/2/3、0/1/64/127/128/129等边界、无效高半及all-invalid query、sink关闭/有限/±Inf共6个专项全部通过原out/max_logits/lse reference与容差。额外runner exit0、valid=true、无污染，加载扩展hash与正式013一致。h_q padding未绕过公开API限制；本补充不代替此前原316。

[逐case结果](../../runs/main-clean-series-001/iter-013-n128-independent-kv/tail-tests/gpu-results-001.json)、[有效监控](../../runs/main-clean-series-001/iter-013-n128-independent-kv/tail-tests/correctness-001/manifest.json)。原五对007/013交错comparison001已启动；当前最佳仍007。


## 2026-11-04：iter013有效比较回退，拒绝并恢复007

固定UUID原五对007/013交错comparison001完成，外层exit0、valid=true、无污染；11轮数值、原参数与测试/runner/module/hash核验均通过。原316和额外6tail均有效通过。正式013 SHA256 `fd0f2d4529c6bb58d0b7b63a0d7d4fa114c3e4f77fb8d2774b4f481f5fbd8f67`。

| s_kv | 父007重测 μs ± SD | 候选013 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 357.870167 ± 0.138979 | 527.888620 ± 0.332437 | -32.205235% / -47.504014% | -24.033880% | 650.889924 / 28.928441% |
| 8192 | 358.554100 ± 0.126589 | 529.622540 ± 0.275001 | -32.299532% / -47.709466% | -24.277588% | 648.758989 / 28.833733% |
| 32768 | 363.923283 ± 0.267350 | 541.597200 ± 0.404897 | -32.806985% / -48.824994% | -25.492565% | 634.414993 / 28.196222% |

汇总交错加速 **−32.437768%**、耗时**增加48.011688%**；相对不可变初始baseline加速−24.604054%、耗时增加32.633125%。各shape和五个pair均回退，最大相邻A漂移0.110822%/0.083130%/0.195864%，远小于回退。**拒绝，已恢复007源码及扩展**；无可收录局部收益。N128减少QK issue没有抵消新数据路径和等待成本；没有单独013 NCU，不能断言全部回退由某个等待造成。012有效profile及013源码暴露的单V槽重载链，仅支持后续优先保留三KV槽而非继续加重单槽依赖。

[有效A/B](../../runs/main-clean-series-001/iter-013-n128-independent-kv/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-013-n128-independent-kv/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-013-n128-independent-kv/comparison-001/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-013-n128-independent-kv/decision.json)。新目标尚未达，当前最佳仍007。


## 2026-11-04：iter014三槽KV拆分QK/PV issuer

父007。保留原数学、三KV槽和全部布局；将warp8 QK与warp10 PV分别发射/commit，CLC workers266→267，QK尾部按finalPfree→finalSO→fence保护跨query的Q与Qt槽复用。隔离双架构完整TU通过，SM100a168/SM103a152 registers、0stack/spill、shared222480B，独立15项实际源码审查通过；GPU正确性与性能尚待验证，当前最佳仍007。

正式构建准备首次使用了错误的嵌套snapshot路径，在任何源码编辑前报FileNotFoundError；后续shell误继续构建未变的007。该日志保留为preparation-failed-parent-rebuild.log，性能N/A；已核对父源码、修正路径并以失败即停止的shell重新应用014冻结源码。真正014正式build.log独立保留，不使用这次父版构建作候选证据。

[冻结实现](../../runs/main-clean-series-001/iter-014-split-issuers/implementation-report.md)、[独立审查](../../runs/main-clean-series-001/iter-014-split-issuers/independent-sync-review.md)、[准备失败记录](../../runs/main-clean-series-001/iter-014-split-issuers/preparation-failure.json)。

014正式构建及实际包审计通过：两架构全部机器码与隔离attempt001一致，REG168/152、0spill。扩展SHA256 `9c41e1f7b8666c8bb65dd9c8dbcc796f6a2fbe0f9d039ed47df1367b6ce1aa8b`。原316case已全部通过（314数值、2原run-only），监控exit0/valid=true/无污染；继续六个额外边界case。复用013冻结harness时其N128分组元数据不能代表014，014实际G=max(ceil(logical_length/64),2)；已单独记录G2/3/5输入覆盖。

[原正确性](../../runs/main-clean-series-001/iter-014-split-issuers/correctness-001/stdout.log)、[监控](../../runs/main-clean-series-001/iter-014-split-issuers/correctness-001/manifest.json)、[正式包审计](../../runs/main-clean-series-001/iter-014-split-issuers/actual-package-audit.md)、[014专项分组说明](../../runs/main-clean-series-001/iter-014-split-issuers/tail-harness-reuse.json)。

014额外六个topk192/320、logical边界、无效索引与sink专项全部通过原三项数值检查；监控exit0、valid=true、无污染，包hash一致。原五对007/014交错比较开始，尚不采用。证据：[tail结果](../../runs/main-clean-series-001/iter-014-split-issuers/tail-results-001.json)、[tail监控](../../runs/main-clean-series-001/iter-014-split-issuers/tail-correctness-001/manifest.json)。


## 2026-11-04：iter014有效比较回退，拒绝并恢复007

固定UUID原五对007/014交错comparison001有效完成，监控exit0、valid=true、无污染；11轮原参数、环境、数值及模块/产物hash重新核验通过。原316+6tail全部有效通过。

| s_kv | 父007重测 μs ± SD | 候选014 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.179833 ± 0.160536 | 361.029540 ± 0.104650 | -0.789515% / -0.795798% | 11.075814% | 951.715429 / 42.298464% |
| 8192 | 358.602183 ± 0.175191 | 361.831940 ± 0.160658 | -0.894026% / -0.902091% | 10.836805% | 949.604901 / 42.204662% |
| 32768 | 364.152567 ± 0.455130 | 368.804580 ± 0.158197 | -1.252684% / -1.268575% | 9.415718% | 931.651618 / 41.406739% |

汇总交错加速 **-0.978941%**、耗时**增加0.988619%**；相对不可变初始baseline加速10.440341%、耗时降低9.453376%。三shape及全部五pair均回退，最大相邻A漂移0.095519%/0.141026%/0.260919%。**拒绝，已恢复007源码及扩展并更新header时间戳保证下轮重编译**。拆分issuer未达到采用门槛；没有本候选NCU，不能将回退归因于某个单一等待或调度变化。当前最佳007及新目标未达状态不变。

[有效比较](../../runs/main-clean-series-001/iter-014-split-issuers/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-014-split-issuers/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-014-split-issuers/comparison-001/theoretical-utilization.json)、[采用决定](../../runs/main-clean-series-001/iter-014-split-issuers/decision.json)。


## 2026-11-04：iter015预取下一query indices前缀的隔离准备

014已有效拒绝，主源码/扩展恢复007。015计划先于实现写入draft：仅CLC lane提前预取valid next_job的前min(physical topk,3*64)个indices到L2，最多768B；其余角色编译期禁用hook，原同步/数学/三KV布局不变。依据007有效NCU中mask indices依赖long-scoreboard599/629及producer169/224(source/full)，根已从原报告复核。提示可能无效或只改善部分冷加载，不能由采样数推算收益；先检查完整双架构TU、prefetch实际位置、资源和边界。GPU正确性/性能N/A，当前最佳仍007。

[研究与原始证据](post014-next-direction.md)、[执行计划](../draft.md)。

015隔离attempt001完整双架构TU通过：REG168/152、0stack/spill、sizeof222480、workers266不变。独立源审查及20300组物理地址/182084组logical边界核验通过：invalid响应不计算地址，宽乘法先于指针加法，非16B对齐跳过，hint范围仅行内512/768B。SASS新增一条UBLKPF.L2，全部新guard仅CLC；ptxas把一条indices指针参数LDCU.64提到warp9角色分支前，使mask lanes也执行这次参数读取，此实际代价已明确接受进入实测，其他非CLC序列除地址重定位相同。

原CUDA13.1正式setup也exit0，原spill检查通过。扩展SHA256 `472d8ff90fac159c7eecd1450816e09fe13db928c6b6d46c5ce1f2c01771aa5e`；原316开始。尚无015性能结论。

[实现报告](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/implementation-report.md)、[资源](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/cpu-validation.json)、[独立CPU审查](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/cpu-audit.json)、[产物](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/artifact.json)。

015原316 attempt001子进程exit0且全部通过，但运行中观察到外来GPU进程（PID列表[2625866]，包括build/split_boundaries），外层exit2、valid=false，整轮按协议无效、性能N/A。保留[污染记录](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/correctness-001/invalidity.json)与原日志；不切卡、不终止外来进程，原包与原协议在同UUID重试correctness002。

015原316 attempt002有效通过（314数值+2原run-only）：子进程/外层exit0、valid=true、无污染。正式包审计确认两架构全部机器码与隔离attempt001相同。继续复用冻结013六个边界case，015实际B_TOPK64分组另记tail-harness-reuse.json；性能比较尚未开始。证据：[原测试](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/correctness-002/stdout.log)、[有效监控](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/correctness-002/manifest.json)、[正式包审计](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/actual-package-audit.md)。

015六个额外边界case全部有效通过，原reference/out/max_logits/lse容差不变，尾部monitor exit0、valid=true、无污染，扩展hash与正式包一致。随后开始007/015原五对交错comparison001；当前最佳仍007。证据：[tail结果](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/tail-results-001.json)、[tail监控](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/tail-correctness-001/manifest.json)。


## 2026-11-04：degree4 exp2可行性研究在CPU阶段否决

在007相同12.5%软件路径、范围fallback和FP32求和顺序下，四阶替换仅省每线程每tile两条FFMA2，不减少MUFU。CPU近零LSE标量模型中四阶绝对差2.4841003e-6，超过原1e-6逐元素容差；五阶同例9.9914631e-8。软件元素数量比例不能约束其概率质量（反例为80.72%）。六点差商证书还给出任意精确实四阶在[0,1]相对一致误差下限2.5404133e-6，根用独立高精度计算交叉核验该值。

因此在进入完整TU前否决该替换，性能N/A，保留五阶与原精度。该反例是logit/softmax层CPU模型，**没有声称完整BF16 Q/K或原316 GPU suite失败**；实多项式下界也不等于任意FP32程序不可能性定理。未修改kernel/包/测试，未运行GPU。[可行性结论](degree4-exp-feasibility.md)、[原始CPU证据与推导](../../profile/head64-degree4-exp-feasibility/REPORT.md)。

015原五对比较comparison001已完成，但运行中出现外来进程PID[2657970]；外层exit2、valid=false，子比较exit0不改变污染结论。**全部性能N/A**，不引用该轮均值或收益作决定。所有11轮和[污染记录](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/comparison-001/invalidity.json)保留；同UUID/原包/原协议开始comparison002。


## 2026-11-04：iter015有效002未达到采用门槛，拒绝并恢复007

固定UUID原五对007/015交错comparison002有效完成：外层exit0、valid=true、无污染；11轮原参数、环境、数值与模块/扩展hash重新核验通过。原316 valid002与6tail valid001通过；原correctness001/comparison001均因外来进程无效，完全排除其性能。

| s_kv | 父007重测 μs ± SD | 候选015 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 357.923333 ± 0.091616 | 357.746260 ± 0.074063 | 0.053666% / 0.053637% | 12.095232% | 960.449967 / 42.686665% |
| 8192 | 358.495267 ± 0.034253 | 358.400320 ± 0.126561 | 0.024927% / 0.024920% | 11.898047% | 958.697201 / 42.608764% |
| 32768 | 364.007433 ± 0.144295 | 363.815660 ± 0.281820 | 0.053645% / 0.053616% | 10.916111% | 944.427141 / 41.974540% |

汇总交错加速 **0.044078%**、耗时降低 **0.044059%**；相对不可变初始baseline加速11.635270%、耗时降低10.422575%。最大相邻A漂移0.062626%/0.027646%/0.092352%。变化远低于严格>0.5%采用门槛，不能证明新的可复现收益；**拒绝，已恢复007源码与扩展并touch headers保证下次重编译**。本轮不追加NCU，不把预取指令存在当作收益证据。三组理论利用率均未达45%，当前最佳仍007。

[有效比较](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/comparison-002-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/comparison-002/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/decision.json)。

并行研究的[CLC独立warp](clc-warp-placement-review.md)在同步语义上可行，但既有profile显示CLC主要等待消费者释放response，没有把它识别为关键路径；暂列低优先级，不实施、不编号正式候选，性能N/A。

独立CPU结果复核也已完成：[014](../../runs/main-clean-series-001/iter-014-split-issuers/independent-result-audit.md)、[015](../../runs/main-clean-series-001/iter-015-clc-indices-prefetch/independent-result-audit.md)。两轮采用结论一致；全部无效尝试已排除，原316、额外6tail、有效11轮与固定2250口径逐项核验。


## 2026-11-04：CTA320资源假设否决，准备iter016 CTA256

CTA320仅删除原warp10/11，但CUDA13.1官方occupancy实现将10warp向4个subpartition取整为12，统一寄存器上限仍168；实际分配减少不等于可用更高REG。007有效NCU表明空warp仅在148个实际CTA初始化时执行，理论减少7696条warp指令约占总指令0.004963%，不是速度预测。没有足够收益依据，因此CPU阶段否决320、不做TU、不跑GPU，性能N/A。[完整反证](cta320-feasibility.md)。

016计划先于实现写入draft，父007。拟256线程保留128softmax，KV producer四warp缩为两个warp，各处理八个int4；MMA/Mask+CLC迁到warp6/7，CLC workers202、Odone ack2。保持三KV槽、全部数学/布局及跨query等待。源级审查及gather映射集合支持可行；主要风险是每issuer发行工作和indices live翻倍，可能暴露TMA延迟。先做完整双架构TU及独立源码/覆盖/字节守恒核验，再进入原协议GPU验证。当前主源码/包仍007，016 GPU正确性和性能N/A。

[设计审查](cta256-design-review.md)、[独立同步审查](cta256-independent-review.md)、[执行计划](../draft.md)。

016完整隔离attempt001与正式CUDA13.1原setup均exit0、原spill检查通过。CPU资源SM100a157/SM103a156 REG、零stack/local/spill，按256-register/warp粒度各CTA实际分配40960；shared222480不变，仍不增加resident CTA。独立源码审查、32768个CuTe位置覆盖、128个gather tuple、202参与者/2Oack及混合skip字节守恒通过。新增producer静态gather32→64/LDG1284→8和UR保存/恢复45→55已记录，不能将更低REG当作更快。扩展SHA256 `22cab09030d70fbb0da3c9eae418ba9a58de9f335ae70ed04d0a6c13733f4c48`；原316开始，运行正确性/性能尚待验证。

[CPU实现与资源](../../runs/main-clean-series-001/iter-016-cta256-two-producers/implementation-report.md)、[独立核验](../../runs/main-clean-series-001/iter-016-cta256-two-producers/independent-cpu-audit.json)、[正式产物](../../runs/main-clean-series-001/iter-016-cta256-two-producers/artifact.json)。

016原316 case全部有效通过（314数值+2原run-only）：外层/子进程exit0、valid=true、无污染。正式包两架构全部SASS/机器码/control与隔离attempt001相同，实际资源157/156 REG、零stack/local确认。继续原6case边界harness，性能尚未作采用判断。证据：[原测试](../../runs/main-clean-series-001/iter-016-cta256-two-producers/correctness-001/stdout.log)、[监控](../../runs/main-clean-series-001/iter-016-cta256-two-producers/correctness-001/manifest.json)、[实际包审计](../../runs/main-clean-series-001/iter-016-cta256-two-producers/actual-package-audit.md)。

016六个补充边界case也全部有效通过：原reference/out/max_logits/lse容差不变，monitor exit0、valid=true、无污染，包hash一致。独立结果preliminary已核验原316和6tail，性能pending。开始007/016原五对交错comparison001；当前最佳仍007。证据：[tail结果](../../runs/main-clean-series-001/iter-016-cta256-two-producers/tail-results-001.json)、[tail监控](../../runs/main-clean-series-001/iter-016-cta256-two-producers/tail-correctness-001/manifest.json)。


## 2026-11-04：iter016有效比较回退，拒绝并追加诊断

原316与6tail有效通过，五对007/016交错comparison001也有效完成（exit0、valid=true、无污染）。根以冻结runner复核11轮原参数/环境/数值/包及模块hash，并由原样本重新生成summary，与保存结果一致；独立结果审计亦通过。

| s_kv | 父007重测 μs ± SD | 候选016 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 357.947567 ± 0.065227 | 376.907540 ± 0.107595 | -5.031903% / -5.298520% | 6.396518% | 911.622473 / 40.516554% |
| 8192 | 358.630950 ± 0.186970 | 378.021480 ± 0.076982 | -5.117713% / -5.393750% | 6.089993% | 908.936137 / 40.397162% |
| 32768 | 363.927950 ± 0.180028 | 384.197600 ± 0.167038 | -5.264966% / -5.557570% | 5.031937% | 894.324649 / 39.747762% |

汇总交错加速 **-5.138243%**、耗时**增加5.416559%**；相对不可变初始baseline加速5.837865%、耗时降低5.515857%。15个shape-pair全部回退，最大相邻A漂移仅0.119422%。**拒绝016，当前最佳保持007**。为定位两producer与角色迁移产生的等待变化，先保留匹配016源码采原8192 full/source NCU，采完恢复007；该诊断不改变拒绝决定，不把REG下降当成性能收益。

[有效比较](../../runs/main-clean-series-001/iter-016-cta256-two-producers/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-016-cta256-two-producers/comparison-001-monitor/manifest.json)、[独立审计](../../runs/main-clean-series-001/iter-016-cta256-two-producers/independent-result-audit.md)、[理论利用率](../../runs/main-clean-series-001/iter-016-cta256-two-producers/comparison-001/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-016-cta256-two-producers/decision.json)。

非WS M64 QK研究也已结束：两warp不能访问全部四个TMEM DP子分区；四warp替代与原WS O行归属不兼容，任意输入rescale需额外跨warp发布同步，且Q duplication不能沿用。该直接替换在CPU研究阶段停止，未编译/运行GPU，性能N/A；不声称所有非WS设计不可行。[布局与同步约束](nonws-qk-feasibility.md)。

016诊断NCU首次full因外来进程PID [2855664]无效（子进程exit0、外层exit2、valid=false），全部指标排除、性能N/A。[无效证据](../../profile/head64-iter016-kv8192/invalidity.json)保留；同UUID另建r2重试。

016诊断r2 full有效完成；随后独立source采集因外来进程PID [2873260]无效（子进程exit0、外层exit2、valid=false）。只排除该source的全部指标，已有效full保留；在新source-r3目录重试source并与r2 full配对，不覆盖。[source污染](../../profile/head64-iter016-kv8192-r2/source-execution/invalidity.json)。

016有效诊断已完成：r2 full与独立source-r3均valid=true/exit0/无污染。相对007，full QKdone long-scoreboard1093→2762、KV两半23/24→293/185，producer等旧槽311→0；source趋势一致。eligible .651152→.476597、issue44.326464%→37.887653%，DRAM字节/L2命中几乎不变，支持保留四producer和三槽的提前量。角色迁移/调度也变化，不把所有回退归因于单因子。动态gather不变，UR保存恢复与总指令下降但实际变慢，不能用静态指令减少推收益。

**已恢复007源码和扩展，并touch headers**；hash核验与冻结007一致。有效full/source、两次独立无效采集及诊断全部保留：[六维报告](../../profile/head64-iter016-kv8192-r2/REPORT.md)、[有效source](../../profile/head64-iter016-kv8192-source-r3/REPORT.md)、[恢复记录](../../runs/main-clean-series-001/iter-016-cta256-two-producers/restoration.json)。目标v2仍未达成。


## 2026-11-04：iter017准备保留TMA内层列循环

016已拒绝并恢复007。基于007 producer正式SASS，39个uniform保存对应32个索引标量及7个列常量，检查保留四producer而只取消local_col四次展开能否减小搬运/发行成本。可执行计划已先写draft，候选仅一处pragma变化；完整双架构TU、机器码/资源和gather覆盖核验通过后才进入原316与五对比较。新增循环分支/依赖可能抵消收益，性能尚N/A。

[更宽gather研究](wider-gather-feasibility.md)已因SW128宽度限制及SW_NONE与MMA atom不兼容，在CPU阶段否决直接替换，不编译/GPU，性能N/A。[五阶指数指令研究](poly5-codegen-review.md)只提出可检查的RN-FTZ打包减法，尚未实施、不编号，未宣称收益。

017隔离完整TU与正式原setup均exit0，双架构原spill检查通过（仅原CUTLASS34豁免各一次）。SM100a168/SM103a152 REG，zero stack/local/spill，sizeof222480、384threads/266workers保持。唯一pragma差异和每producer32次gather原序、128tuple/整tile覆盖、各skip组合每half32768B已独立核验。实际SASS producer39对uniform保存/恢复消失，但新增31次列循环branch判定（23taken）/有效tile，九静态gather站点实际执行7×4+1+3=32次。不能从代码缩短推收益。

正式扩展SHA256 `5d7a409948553751deab61e03bf63dd8ee481523bed2ca7d3ea9c37f09dda849`，全部机器码/control/text/nv.info与隔离版一致；原316开始。[独立CPU审查](../../runs/main-clean-series-001/iter-017-producer-col-loop/independent-cpu-audit.md)、[正式包审计](../../runs/main-clean-series-001/iter-017-producer-col-loop/actual-package-audit.md)、[产物](../../runs/main-clean-series-001/iter-017-producer-col-loop/artifact.json)。

017额外静态control-flow核算：从成功SVwait后的有效TMA发行窗口计，每producer原007为383条动态SASS、017为382条，搬运减少大致被循环地址递推/比较/branch抵消。这是该窗口的精确指令计数，不涵盖indices/minmax/其他路径，不能当性能预测；保留原协议实测决定。

017原316（314数值+2原run-only）全部有效通过：原测试子进程/外层exit0，valid=true，无污染。开始复用原6case边界harness验证，benchmark尚未采用判断。[原日志](../../runs/main-clean-series-001/iter-017-producer-col-loop/correctness-001/stdout.log)、[监控](../../runs/main-clean-series-001/iter-017-producer-col-loop/correctness-001/manifest.json)。

017六个边界case全部有效通过，原reference/容差不变，monitor valid=true/exit0/无污染，扩展hash一致。开始原五对007/017交错comparison001。[tail结果](../../runs/main-clean-series-001/iter-017-producer-col-loop/tail-results-001.json)、[tail监控](../../runs/main-clean-series-001/iter-017-producer-col-loop/tail-correctness-001/manifest.json)。


## 2026-11-04：iter017有效比较回退，拒绝并恢复007

原316与6tail均有效通过，原五对comparison001也exit0/valid=true/无污染。根以冻结runner复核全11轮原参数、环境、样本、module/package hash及不可变初始结果；从原样本重算summary逐项相同。

| s_kv | 父007重测 μs ± SD | 候选017 μs ± SD | 交错加速 / 耗时降低 | 相对初始加速 | TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.138083 ± 0.105427 | 385.760020 ± 0.131215 | -7.159263% / -7.711338% | 3.954915% | 890.702421 / 39.586774% |
| 8192 | 358.845700 ± 0.094780 | 386.353680 ± 0.070940 | -7.123456% / -7.669812% | 3.802029% | 889.333793 / 39.525946% |
| 32768 | 364.292517 ± 0.096724 | 390.207940 ± 0.130439 | -6.642232% / -7.114814% | 3.414139% | 880.549442 / 39.135531% |

汇总交错加速 **-6.975282%**、耗时**增加7.498311%**；相对不可变初始baseline加速3.723444%、耗时降低3.589781%。15个shape-pair全部回退，相邻A最大漂移0.070668%/0.064349%/0.071696%。**拒绝，已恢复007源码与扩展并touch headers**。没有追加017 NCU，不能把全部回退分摊到某一类branch/address指令；已知局部动态发行数383→382近似不变，也不支持由静态代码缩短推收益。当前最佳007、新目标尚未达成的状态保持。

[有效比较](../../runs/main-clean-series-001/iter-017-producer-col-loop/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-017-producer-col-loop/comparison-001-monitor/manifest.json)、[理论利用率](../../runs/main-clean-series-001/iter-017-producer-col-loop/comparison-001/theoretical-utilization.json)、[决定](../../runs/main-clean-series-001/iter-017-producer-col-loop/decision.json)、[CPU机制与代价](../../runs/main-clean-series-001/iter-017-producer-col-loop/implementation-report.md)、[恢复记录](../../runs/main-clean-series-001/iter-017-producer-col-loop/restoration.json)。

017[独立终态结果审计](../../runs/main-clean-series-001/iter-017-producer-col-loop/independent-result-audit.md)也已complete_verified：原316/6tail/11轮330样本/44输入hash及固定2250口径均通过，拒绝结论一致。根再次核验主源码/扩展已精确恢复007。


## 2026-11-04：iter018直接O向量store的隔离计划

父版本仍007，主源码与扩展hash再次核验相同，当前无GPU运行。S布局[主可行性](s-layout-feasibility.md)/[独立审查](s-layout-independent-review.md)均确认INTER和SW128合法，但原Sstore actual=ideal且无充分tensor读取收益证据，暂不实施，性能N/A；明确不采用KernelWiki“必须SW128”的错误泛化。

下一候选018检查O epilogue一次shared中转与逐块发布成本：保留原FP32scale/BF16转换/TMEM数据映射，改为16B global stores，四个chunk barrier改成末尾单一无条件128barrier，保护末query TMEM free；保持原Odone/ack/CLC和全部其他同步。原007 Ostore的2097152个shared wavefront虽已ideal，仍代表一次完整中转。全局写入更分散，收益未知。执行计划先于实现写入draft，先完整TU/CPU映射与独立同步核验，性能N/A。

018 CPU attempt001 callback末屏障版完整双架构TU通过（REG168/153，zero stack/spill），尚无GPU数据。进一步独立同步审查证明，可以用原newS→SOready128→首PV链保护跨query旧O读取、原首rowmax128保护旧li读取，仅在outer-loop结束后由全128softmax加一次屏障再允许warp3 free。draft已先修订；001源码/完整TU保留为CPU通过但GPU前被替代，性能N/A。接下来以仅移动末barrier的attempt002重新冻结/编译/独审，原316及五对最终验证均针对002。


### iter018 正式构建与原测试启动

最终attempt002独立源码/数学/同步/地址和完整TU门槛通过，phase `82c0e2e7e969156c9c3627d45a1f386d92d33ce9ac95628484950e794f2158c1`。正式原setup exit0，两架构仅原34 CUTLASS exemptions；归档包SHA `719b05381fdf7d718958a259fae3eb5c814a93654777b0615e1e85234a0bc606`。实际包全部SASS及control编码、text/.nv.info与隔离attempt002一致，REG168/153、零stack/local/spill。原316已启动固定UUID监控runner，等待空闲；性能仍N/A，未采用。

准备阶段曾误要求git diff与difflib生成的patch文本字节相等，断言失败；源文件当时已逐字节匹配冻结快照，正式编译正常启动。已将归档patch独立应用到main并确认重建所有文件完全一致；差别仅diff序列化/上下文，详见[preparation-audit.json](../../runs/main-clean-series-001/iter-018-direct-o-store/preparation-audit.json)。不是GPU或编译失败，不涉及测试/编译参数变化。


iter018原correctness-001测试进程exit0，但运行时监测到外部PID3094974/3095088，monitor valid=false、wrapper exit2。本轮全部原日志/telemetry保留并排除有效证据；正确性结论等待同UUID原316重试002，性能N/A。


iter018原316在correctness-002有效通过（314数值+2原run-only），另6个冻结tail用例在tail-correctness-001有效通过，均同UUID/childexit0/valid=true/无污染。原runners与冻结版本逐字节一致；正式包仍719b0538…bc606。007/018原五对交错comparison-001已启动，最终性能裁决待全部11次测量及监控完成。


iter018 comparison-001全部11次测量完成、childexit0，但固定GPU监控出现外部PID[3126149]，valid=false、wrapper2。整组排除，性能N/A；保留原summary和telemetry，不从局部未污染片段推断收益。同UUID原五对comparison-002重试。


## iter018裁决：direct16B O store正确但回退，拒绝

相对父版007，仅将O shared/TMA中转改成每lane16B global store，保留全部浮点scale/转换及原数学和主循环同步；最终128-thread退出barrier位于outer-loop之后。双架构正式编译与机器码审计通过168/153 REG、zero stack/local/spill；sizeof222480、384threads266workers、4producer ack不变。原316有效002及6tail有效001通过，第一次316因foreign3094974/3095088无效；五对comparison001因foreign3126149整组无效，全部保留排除。

正式包SHA `719b05381fdf7d718958a259fae3eb5c814a93654777b0615e1e85234a0bc606`。固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8` 上comparison002完整11次（6A+5B、每shape每次10样本），monitor finished/exit0/valid=true/无污染；根使用冻结runner重验全部11报告、包和输入/环境/hash并重算exact summary。A为007交错重测，初始baseline保持不可变。

| s_kv | 007 A均值±SD μs（6轮） | 018 B均值±SD μs（5轮） | 相对007加速 / 耗时增加 | 相对初始加速 / 耗时降低 | B TFLOPS / 理论利用率 | 最大相邻A漂移 |
|---|---:|---:|---:|---:|---:|---:|
| 4096 | 358.054800 ± 0.124652 | 389.871280 ± 0.139295 | -8.159561% / +8.884497% | +2.858692% / 2.779242% | 881.309810 / 39.169325% | 0.048316% |
| 8192 | 358.933000 ± 0.084545 | 391.054560 ± 0.207872 | -8.214500% / +8.949671% | +2.554222% / 2.490606% | 878.643082 / 39.050804% | 0.040426% |
| 32768 | 364.124933 ± 0.114330 | 393.358440 ± 0.156648 | -7.429027% / +8.025222% | +2.585871% / 2.520689% | 873.496915 / 38.822085% | 0.075481% |

汇总相对007加速 **-7.935057548%**、耗时 **+8.618978448%**；五个汇总pair和全部15个shape-pair均回退。相对不可变初始baseline直接加速2.666170525%、耗时降低2.596931892%，不等于相对当前最佳有收益。三组理论利用率38.82–39.17%，均未达45%。**拒绝018**，最佳仍007。

归档：[有效比较](../../runs/main-clean-series-001/iter-018-direct-o-store/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-018-direct-o-store/comparison-002-monitor/manifest.json)、[裁决](../../runs/main-clean-series-001/iter-018-direct-o-store/decision.json)、[原316](../../runs/main-clean-series-001/iter-018-direct-o-store/correctness-002/manifest.json)、[6tail](../../runs/main-clean-series-001/iter-018-direct-o-store/tail-results-001.json)、[正式包审计](../../runs/main-clean-series-001/iter-018-direct-o-store/actual-package-audit.md)。当前018源码仅暂留用于原8192 NCU full/source诊断，采集后恢复007；不能由删除barrier或shared wavefront直接归因回退。


### iter018 NCU收尾与019隔离CPU计划

原8192 full/source均有效完成，主源码与扩展已恢复007并核对SHA，改变的phase header已touch，config/common原本相同。根直接解析原NCU：replay370.016→404.640μs，TCelapsed46.103603→41.811554%、eligible0.651152→0.576374、issue44.326464→39.189579%，资源/occupancy基本不变。O BF16pack long-scoreboard从0/0变1637/1710（source/full），部分高样本pack覆盖前面STG的数据寄存器；FMUL2的259/251另有TMEM读取依赖。O16B store实测sector请求16777216、ideal8388608，LG-throttle0，DRAM读/写字节近似不变。不能称为HBM翻倍或已证明的LG队列饱和。完整六维、时间线限制、PC证据及复现脚本见[018 NCU REPORT](../../profile/head64-iter018-kv8192/REPORT.md)，恢复证据见[restoration.json](../../runs/main-clean-series-001/iter-018-direct-o-store/restoration.json)。

下一轮019先在独立candidate目录做完整TU代码生成探针：在每次原LDTM64后，先按原顺序将32个float2 scale/pack，再批量8次16B写出。保持原in-place o更新和全部数学/地址/同步/缓存策略；不同时引入32B宽度。CPU须追踪8组STG数据寄存器及下一LDTM/首写，证明减少原覆盖等待链且无spill；若ptxas重交错后无改善，则CPU拒绝、性能N/A。执行计划已先写入docs/draft.md，主工作区保持007。32B与转置PV仅研究，其中转置PV令PV issue8→32、需重做scale/输出，暂缓。


## iter019裁决：分阶段O打包被编译为原机器码，CPU拒绝

性能父版007，隔离实现基于已拒绝018 attempt002。仅将每次LDTM64后的convert/store拆成先32个原in-place float2 scale/BF16 RN pack、后8个原16B global store，地址、cache policy、所有数学与同步原样。冻结phase SHA `61ed343dcb4dea7a8c93e97a3151fa59cbae2ae385507a2db004ccf94d657da3`；独立源审严格重建全文，数学/地址/all-invalid/生命周期通过。

原CUDA13.1完整TU attempt001 exit0，SM100a168/SM103a153 REG、zero stack/local/spill。**两架构各2584条SASS以及每条完整128bit机器码/control，均与018最终attempt002完全相同，changed words=0。** 根独立逐行核对5168个编码行/架构，见[root-codegen-audit.json](../../runs/main-clean-series-001/iter-019-prepacked-direct-o/root-codegen-audit.json)。普通两段C++未改变寄存器分配和调度；首STG前仍只有12/12/12/16个pack，原STG数据寄存器覆写链原封不动。

**CPU拒绝019**。本候选未应用主工作区、未构建正式扩展、未运行GPU；原316、tail、benchmark以及相对007/不可变初始的耗时/加速全部 **N/A**。不把018的测量冒作019的新性能数据，也不因source重排而宣称消除了WAR。主工作区始终保持007。见[独立源审查](prepacked-o-store-review.md)和[019隔离证据](../../runs/main-clean-series-001/iter-019-prepacked-direct-o/)。下一步评估独立32B向量store方案；不继续叠加任意同步来强制打包相位。

## iter020：32B O输出与16B对齐回退，构建与验证记录

性能父版仍007，实现基于018最终attempt002，仅合并相邻16B输出并增加CTA统一的基址对齐判断。32B对齐使用默认cache `st.global.v8.b32`；仅16B对齐使用原两次uint128写。数学、地址64位首乘法、padding guard和原同步保持。执行计划先于实现，源快照phase `d568e866c33023334050226a8896d500162422f6950e26d7b0d327105b972486`。

CPU完整TU与正式原setup均exit0，双架构REG168/153、零stack/local/spill；正式包 `d7ee6204eccb4bd1eaa7101c19ca539ae3cf757b990ac9a29806767b066cc88e` 全部2744条SASS/control及text/nv.info与隔离attempt001相同。实际16个256bit和32个128bit静态位点互斥；新增160条静态指令，仍存在store数据寄存器重用，不能据此宣称提速。实际CuTe、hq1..64双对齐覆盖、70000 query地址和独立源数学审查通过。正式准备脚本第一次因根误抄007预期SHA而在任何源码修改/构建前停止；独立核对主扩展与归档007相同后修正断言，实际正式构建仅一次，记录见[准备尝试](../../runs/main-clean-series-001/iter-020-direct-o-store256/preparation-attempt-001.json)。

固定UUID原316监控已启动，随后6tail与10场景实际kernel双对齐检查，再运行原五对007/020比较。正式构建时，正确性及逐shape/汇总相对007与初始性能均 **N/A（待有效运行，终态见下）**，未采用020，最佳仍007；不得把CPU检查计作运行验证。[实现报告](../../runs/main-clean-series-001/iter-020-direct-o-store256/implementation-report.md)、[正式包审计](../../runs/main-clean-series-001/iter-020-direct-o-store256/actual-package-audit.md)、[双对齐测试说明](../../runs/main-clean-series-001/iter-020-direct-o-store256/alignment-tests/README.md)。

原316 correctness-001子进程exit0、All316 passed，但monitor发现foreign_compute_process_observed，wrapper exit2、valid=false。该尝试完整保留并排除，测试内附带的耗时不参与性能结论；同UUID新correctness-002等待空闲后重跑。

correctness-002原316、tail-001六例与alignment-001十例均有效通过（monitor finished/exit0/valid=true/无污染）。实际20次低层调用和7次public control验证两种基址逐位相同、前后canary完好、原FP32 reference与容差通过，低层hq1/31/63 padding单独标记；[独立运行审计](../../runs/main-clean-series-001/iter-020-direct-o-store256/independent-result-audit.md)。comparison-001虽然子进程完成11次交错测量，但晚期foreign污染使整组无效，全部排除且不报告其耗时均值；comparison-002同UUID重跑中。


## iter020裁决：32B直接输出仍慢于007，拒绝

固定UUID原五对comparison002全部有效，6A+5B共11报告、330个原kernel样本，monitor finished/exit0/valid=true/无污染。根使用冻结runner严格复验全部包/输入/环境/协议，并从原始样本重算summary逐值相等；原316valid002、6tailvalid001及10场景实际kernel双对齐valid001全部通过。correctness001与comparison001受foreign污染，仅保留原始证据并排除。

| s_kv | 007 A均值±SD μs（6轮） | 020 B均值±SD μs（5轮） | 相对007加速 / 耗时增加 | 相对初始加速 / 耗时降低 | B TFLOPS / 理论利用率 | 最大相邻A漂移 |
|---|---:|---:|---:|---:|---:|---:|
| 4096 | 358.063333 ± 0.062424 | 370.264200 ± 0.261734 | -3.294811% / +3.407067% | +8.305502% / 7.668587% | 927.978950 / 41.243509% | 0.038389% |
| 8192 | 358.888267 ± 0.065817 | 371.746920 ± 0.179180 | -3.458835% / +3.582757% | +7.880641% / 7.304963% | 924.277688 / 41.079008% | 0.038999% |
| 32768 | 364.271967 ± 0.183325 | 376.497500 ± 0.216363 | -3.243736% / +3.352482% | +7.180042% / 6.699048% | 912.615313 / 40.560681% | 0.118589% |

汇总相对007加速 **-3.332504086%**、耗时 **+3.447388446%**；五个汇总pair与全部15个shape-pair均回退，没有可保留的局部收益。相对不可变初始baseline直接加速7.787728681%、耗时降低7.225060567%，不代表相对当前最佳有收益。三组理论利用率40.56–41.24%，仍未达45%。**拒绝020，最佳仍007。**

[有效比较](../../runs/main-clean-series-001/iter-020-direct-o-store256/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-020-direct-o-store256/comparison-002-monitor/manifest.json)、[根重验](../../runs/main-clean-series-001/iter-020-direct-o-store256/comparison-002-root-revalidation.json)、[裁决](../../runs/main-clean-series-001/iter-020-direct-o-store256/decision.json)。020相对018历史有效结果的回退幅度明显缩小，但两候选并非直接交错，不能把跨实验耗时差当成精确的018→020加速。依原计划补采原8192 full/source检查实际32B请求与依赖；当前源码暂留020匹配采集，之后恢复007。

### iter020诊断收尾

原8192 full/source均有效完成，无污染；[完整NCU诊断](../../profile/head64-iter020-kv8192/REPORT.md)。此次捕获实际wide pred-on8388608、fallback0；全局LSU store requests278528、sectors8454144、bytes/sector32。两个原max/LSE scalar store逐PC共65536 sectors，扣除后O残差8388608，是018逐PC O sectors16777216的一半；020宽store逐PC sector counter本身返回0，不能将0当作未写或ideal证明。O pack long-scoreboard从0181637/1710降为961/1077（source/full），但007为0/0，实际store数据寄存器复用链仍在。DRAM字节近似保持、LG-throttle0、local0，未证明HBM/队列饱和。NCU replay384.288μs只作诊断，不替代有效benchmark或目标口径。

源码与扩展已恢复007，phase header已touch、三文件和归档007扩展SHA逐项核对，见[恢复证据](../../runs/main-clean-series-001/iter-020-direct-o-store256/restoration.json)。020最终拒绝，原>45%目标仍未达到。

## iter021隔离CPU：完整O stage单次发布

唯一源码/性能父版007，先写入可执行计划，再隔离实现。保留原四轮LDTM64/scale/BF16/32个shared向量写，随后所有128线程一次proxy fence与named barrier，再原八条动态TMA及commit；所有其他数学、地址、query入口read-wait/Odone/ack/CLC保持。冻结phase `ab98de66a9a834837bacba259e13963d1653d76d0df8272db7e7afa1a470d984`。

完整原TU attempt001 exit0，REG168/152，zero stack/local/spill、sizeof222480；SM100/103分别2728/2800条SASS，原007为2752/2816。O实际仅一轮发布，全部32STS在其前、全部TMA在其后；四读取、128mul/128pack逐值追踪通过，含SM103寄存器XOR置换。实际CuTe覆盖32768元素/4096向量/8tile，根独立源码重建及地址枚举亦通过。此前两份设计审查不代替当前实际diff独审，后者仍在进行；当前无正式包或GPU结果，逐shape/汇总对007与初始性能全部 **N/A**。主源码仍007，不根据少三次屏障推断收益；首TMA延后可能损失重叠。[CPU实现报告](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/implementation-report.md)。

021实际冻结diff独立审查现已通过（[源码/数学/同步审计](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/independent-math-audit.json)）；020采集收尾并恢复007核验之后，root应用021 snapshot、touch phase，原setup正式构建进行中。

021正式原setup现已exit0，扩展SHA `a7e8ab4d0e396af7b069dfc1a6ffcfebf620081ba02b0eabc1b7a6c44f31416a`；实际包双架构全部SASS/control/text/nv.info与CPUattempt001相同，REG168/152，zero stack/local/spill，原CUTLASS豁免仅[34,34]。原316 correctness001及6tail001均有效通过，独立运行审计确认包/参数/原reference/监控一致。comparison001监控发现foreign，整组排除、不汇总其耗时，等终态后同UUID新编号重跑；正式采用仍未决定。


## iter021裁决：合并O发布正确但回退，拒绝

正式扩展a7e8ab4d…f31416a与冻结CPU版本一致，原316及6tail均有效001通过。comparison001子进程完成但4个运行期监控样本发现foreign PID3557787，整组无效保留、耗时结论N/A。固定UUID同卡comparison002的91条监控样本无污染，6A+5B共11报告/330原kernel样本完整通过原协议。根与独立审计分别重算全部均值、SD和配对汇总，结果完全一致。

| s_kv | 007 A均值±SD μs（6轮） | 021 B均值±SD μs（5轮） | 相对007加速 / 耗时增加 | 相对初始加速 / 耗时降低 | B TFLOPS / 理论利用率 | 最大相邻A漂移 |
|---|---:|---:|---:|---:|---:|---:|
| 4096 | 358.169883 ± 0.093354 | 360.487500 ± 0.094107 | -0.641368% / +0.645508% | +11.242831% / 10.106567% | 953.146458 / 42.362065% | 0.069745% |
| 8192 | 358.888517 ± 0.194708 | 361.317420 ± 0.261888 | -0.670586% / +0.675113% | +10.994637% / 9.905557% | 950.957149 / 42.264762% | 0.114175% |
| 32768 | 364.136500 ± 0.200118 | 370.654320 ± 0.179599 | -1.749523% / +1.780676% | +8.869682% / 8.147063% | 927.002237 / 41.200099% | 0.094799% |

汇总相对007加速 **-1.021838802%**、耗时 **+1.032388145%**；全部15个shape-pair及5个汇总pair回退，无可保留的局部收益。相对不可变初始直接加速10.363888700%、耗时降低9.390651980%，不能替代相对当前最佳的采用门槛。三组理论利用率41.20–42.36%，未达到45%。**拒绝021，007继续为最佳。**

本轮不额外采集NCU。源级已证明第一批TMA会推迟，但没有本候选的运行依赖采样，故不能把回退确定归因为失去TMA重叠，也不能按减少的三次屏障估算收益。全部原始数据与无效尝试保留：[有效比较](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/comparison-002/summary.json)、[有效监控](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/comparison-002-monitor/manifest.json)、[根重验](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/comparison-002-root-revalidation.json)、[独立完整审计](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/independent-result-audit.md)、[裁决](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/decision.json)。

主源码三文件和扩展已恢复007并逐项核对SHA，改变的phase header已touch；[恢复记录](../../runs/main-clean-series-001/iter-021-tma-o-single-publish/restoration.json)及独立审计再次确认。当前无本任务存活GPU运行，目标保持原三workload实测TFLOPS/2250均>45%，尚未完成。


## iter022裁决：B_EPI128完整编译产生spill，CPU拒绝

父版007；先写可执行计划，隔离仅将B_EPI64改128、sO_addrs[8]改为[B_EPI/8]。意图是四轮LDTM64/发布改两轮LDTM128/发布，保持原数学及按轮TMA。CuTe模板研究提示64×128 logical tile仍拆为两个8KiB atom，总TMA未必减少，未据源码调用数宣称性能收益。

原完整TU/原CUDA13.1 flags的attempt001编译exit0，但资源检查失败：SM100a/SM103a均REG168、stack64 B；ptxas分别报告spill stores/loads **68/68 B** 和 **64/64 B**。根独立读取build.log、resource和SASS验证。cuobjdump的LOCAL0不能否定这些stack/spill记录，SHARED1024是driver reserve。

**CPU拒绝022**，不放宽原zero-spill门槛、不额外setmaxnreg、不做正式构建或GPU测试。实际代码生成和原始失败产物完整保留；未继续昂贵layout/dataflow门槛，不将未执行的检查写为通过。三个工作负载及汇总相对007、不可变初始的性能全部 **N/A**，没有局部收益证据。主源码和扩展始终为007，根逐项核验；目标未完成。

[隔离实现/资源报告](../../runs/main-clean-series-001/iter-022-epi128/implementation-report.md)、[原始编译日志](../../runs/main-clean-series-001/iter-022-epi128/cpu-build/attempt-001/build.log)、[CPU gate](../../runs/main-clean-series-001/iter-022-epi128/cpu-validation.json)、[根独立复核与裁决](../../runs/main-clean-series-001/iter-022-epi128/decision.json)。


## iter023完整构建：rowmax四层树进入原验证

父版007，不叠加022。仅head64局部32元素rowmax改为16个三输入max构成的平衡树；全部mask、scale、求和、exp、输出和同步保持。原max_num/FTZ语义、NaN忽略、+0优先、-Inf初值已独立核对；树无浮点加法重排。

隔离原完整TU双架构通过：实际SASS从17个max/最长9级变为16个max3/最长4级，32个masked p均恰覆盖一次且后续softmax原输入顺序保持；其他opcount仅NOP+1，无额外MOV。REG168/152、zero stack/local/spill。主config/common逐字节等同007，共享布局沿用已验证定义。正式原setup exit0且原spill检查通过，扩展SHA `2377d37f8cd2e6dd4ace81af8a133ce1430ab739279bf0bbb8cc5dedef72451d`；实际两架构全部SASS机器/control、.text/.nv.info与隔离attempt001相同。root发现复用artifact helper的cpu_evidence指向未运行的resource probe，已在GPU前修正文档metadata为实际cpu-validation及既有布局证据，没有改kernel或运行协议。

原316、6tail、五对交错比较尚待完成，当前三个shape及汇总对007/初始性能 **N/A**，不由依赖深度宣布收益。[实现报告](../../runs/main-clean-series-001/iter-023-rowmax-tree/implementation-report.md)、[CPU gate](../../runs/main-clean-series-001/iter-023-rowmax-tree/cpu-validation.json)、[独立数学审查](../../runs/main-clean-series-001/iter-023-rowmax-tree/independent-math-audit.md)、[正式包核验](../../runs/main-clean-series-001/iter-023-rowmax-tree/actual-package-audit.md)。

023 correctness001子进程原316全部完成exit0，但运行期间检测foreign，monitor valid=false、wrapper exit2；整次保留无效，不计作有效正确性通过。按同UUID重跑002，性能仍N/A。

023原316已在correctness002完整有效通过，6tail也在001有效通过，正式包与参数/容差保持冻结。五对007/023 comparison001已启动，终态和有效性审计前不报告性能收益。

023 comparison001的11报告已全部完成，但运行期间foreign使整组无效；wrapper exit2、child exit0，结果保留不作为收益证据。固定UUID重跑comparison002，不改测量协议。


## iter023裁决：小幅正收益，未过0.5%门槛，不采用

原316 valid002、6tail valid001通过；original001和comparison001的污染记录保留并排除。有效comparison002全部11报告/330原kernel样本按原协议重算一致，全部15个shape-pair和5个汇总pair为正；这些是本次固定负载的小幅改善，不叠加既有收益。没有通过反复测量挑选跨过门槛的结果。

| s_kv | 007 A均值±SD μs（6轮） | 023 B均值±SD μs（5轮） | 相对007加速 / 耗时降低 | 相对初始加速 / 耗时降低 | B TFLOPS / 理论利用率 | 最大相邻A漂移 |
|---|---:|---:|---:|---:|---:|---:|
| 4096 | 358.175417 ± 0.063143 | 356.436460 ± 0.121522 | 0.487759% / 0.485392% | 12.507149% / 11.116760% | 963.979341 / 42.843526% | 0.046494% |
| 8192 | 358.843533 ± 0.213699 | 357.055200 ± 0.245244 | 0.502143% / 0.499634% | 12.319597% / 10.968341% | 962.308863 / 42.769283% | 0.072890% |
| 32768 | 364.162833 ± 0.130868 | 362.656340 ± 0.380276 | 0.409369% / 0.407700% | 11.270681% / 10.129066% | 947.446234 / 42.108722% | 0.064038% |

汇总相对007加速 **0.466415392%**、耗时降低 **0.464250059%**，低于严格>0.5%门槛，**拒绝023**。8192形状均值加速0.502143%仅略过门槛，4096/32768为0.487759%/0.409369%；已在开头记录这些小幅收益，不能改写汇总采用标准。相对不可变初始直接加速12.031151717%、耗时降低10.739112767%，三组理论利用率42.108722–42.843526%，仍未达到45%。

本轮不另采NCU，真实机器码证明max依赖树缩短，但未测定它在总耗时中的独立贡献。[有效比较](../../runs/main-clean-series-001/iter-023-rowmax-tree/comparison-002/summary.json)、[根重验](../../runs/main-clean-series-001/iter-023-rowmax-tree/comparison-002-root-revalidation.json)、[裁决](../../runs/main-clean-series-001/iter-023-rowmax-tree/decision.json)。主源码/扩展已恢复007并逐项核验、phase touch，见[恢复证据](../../runs/main-clean-series-001/iter-023-rowmax-tree/restoration.json)。[独立完整运行审计](../../runs/main-clean-series-001/iter-023-rowmax-tree/independent-result-audit.md)已complete_verified，并在024应用前再次核验007恢复。

## iter024隔离CPU：全有效mask的真实跳转

父版007，先写可执行计划，只改本地32元素mask helper/调用。attempt001用bra.uni仍被ptxas ifconvert：32predicated LOP3+32FSEL顺序发行，2776/2840 SASS、168/151 REG、zero spill；按计划CPU拒绝该attempt，不GPU，性能对parent/initial均N/A。

attempt002采用合法0/1索引的两目标brx.idx.uni，同一asm块32个+f保持原bits，mask先复制。原完整TU双架构zero stack/local/spill、REG168/152；实际BRX0xfc0与constant2表[0xfd0,0x1250]使fullmask跳过40条mask指令，guard6条含LDC。partial/allinvalid走原位逐bit精确-Inf，原17节点9层rowmax和其他数学/同步保持。root源码重建和独立数学/CFG审查通过；实际分支表8字节d00f000050120000必须在正式包核验，不能只比.text。

这只证明更短fast path可表达，未证明>0.5%收益；shared mask读取和同步仍在，slow路径受调度影响。正式GPU验证尚未进行，对007/初始的三个shape及汇总性能N/A。[CPU实现报告](../../runs/main-clean-series-001/iter-024-mask-branch/implementation-report.md)、[CPU gate](../../runs/main-clean-series-001/iter-024-mask-branch/cpu-validation.json)、[独立审计](../../runs/main-clean-series-001/iter-024-mask-branch/independent-math-audit.md)。

024原setup正式构建exit0，扩展SHA `4720e165100b90a2c16216d361f628747de1666900df1b9b6f6b739a321d06fd`。实际包双架构全部SASS/control/text/nv.info与成功attempt002相同，REG168/152且zero stack/spill；root另外从ELF直接核对两架构新增constant2均为d00f000050120000，与隔离对象逐字节相同。见[正式包核验](../../runs/main-clean-series-001/iter-024-mask-branch/actual-package-audit.md)和[分支表专项核验](../../runs/main-clean-series-001/iter-024-mask-branch/actual-branch-table-audit.json)。原316 correctness001在固定UUID等待空闲/执行，性能仍N/A。

024原316和6tail均在001有效通过，无污染；正式包独审也已通过（包含constant2表）。comparison001按原五对协议启动，完成有效性和独立重算前不报告收益。


## iter024裁决：真实跳过mask后小幅加速，仍未过采用门槛

原316、6tail及五对交错comparison均在001有效完成，无污染重试。root按冻结工具/初始baseline/包SHA重验11报告330样本，原协议和数值汇总完全一致。全部15个shape-pair与5个汇总pair为正，小幅收益记录在开头；不能以静态跳过40条、只加6条推定总性能改善比例。

| s_kv | 007 A均值±SD μs（6轮） | 024 B均值±SD μs（5轮） | 相对007加速 / 耗时降低 | 相对初始加速 / 耗时降低 | B TFLOPS / 理论利用率 | 最大相邻A漂移 |
|---|---:|---:|---:|---:|---:|---:|
| 4096 | 357.996367 ± 0.125206 | 356.492480 ± 0.044809 | 0.429211% / 0.427377% | 12.489470% / 11.102790% | 963.827859 / 42.836794% | 0.063415% |
| 8192 | 358.758800 ± 0.131714 | 357.360480 ± 0.129934 | 0.397433% / 0.395860% | 12.223646% / 10.892220% | 961.486798 / 42.732747% | 0.099869% |
| 32768 | 364.152383 ± 0.256735 | 362.733880 ± 0.128881 | 0.392600% / 0.391065% | 11.246895% / 10.109851% | 947.243703 / 42.099720% | 0.161776% |

汇总相对007加速 **0.406413689%**、耗时降低 **0.404768654%**，低于严格>0.5%，**拒绝024单独方案**。相对不可变初始直接加速11.985393670%、耗时降低10.702640119%；三组理论利用率42.099720–42.836794%，目标未完成。所有shape均改善但无一均值达到0.5%，不改门槛、不挑重复测量。未采NCU，不把实际分支与性能之间的贡献拆分当作已测事实。

[有效比较](../../runs/main-clean-series-001/iter-024-mask-branch/comparison-001/summary.json)、[根重验](../../runs/main-clean-series-001/iter-024-mask-branch/comparison-001-root-revalidation.json)、[裁决](../../runs/main-clean-series-001/iter-024-mask-branch/decision.json)。007源码/包已恢复并逐项核对、phase touch，见[恢复记录](../../runs/main-clean-series-001/iter-024-mask-branch/restoration.json)。[独立完整运行审计](../../runs/main-clean-series-001/iter-024-mask-branch/independent-result-audit.md)已complete_verified，并再次核验当前007源码/扩展恢复。023与024均有小幅稳定正向结果，可作为后续组合候选的依据；组合必须独立编译、测试与交错比较，不能把0.466415%和0.406414%相加后宣称收益或提前保留。

另完成[dual QK同warp归约可行性研究](dual-qk-local-reduction-feasibility.md)：固定006 WS M64N128K256/16 QK MMA时，两partial处于相隔64DP的不同warp访问区；16dp/两段load或仅重排Q/K不能免费消除exchange。只读数学/布局反证，不启动实现或GPU，也不是新性能结果。


## iter025：组合全有效mask分支与rowmax平衡树（2026-11-05 02:42，有效比较完成，拒绝）

父版本仍为007。组合023冻结16max3/4层rowmax与024成功attempt002的运行时全有效mask分支，其他数学、布局和同步保持007。两种应用顺序、main/007/023/024四补丁均精确重建phase `422132b48d85252e7fc48ec13dacf465e52b62d8fe1dc43881b2bf9ddb0b8017`。没有叠加023/024单独测量的收益。

原完整双架构CPU编译attempt001和正式构建均exit0；SM100a/SM103a为168/152 registers，0 stack/local/spill。原setup保留的CUTLASS豁免仍为34/34。正式扩展SHA `fd583aaa165c52776bbdad718b63990cee30b02499ece141c841b8965e3b8740`，全部SASS/control/.text/.nv.info及.nv.constant2与隔离产物匹配；actual CFG确认6指令guard跳过40指令mask慢路径，两路32个p均进入16节点4层max，再保留原32个softmax输入。[CPU证据](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/cpu-validation.json)、[正式包审计](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/actual-package-audit.json)、[独立审计](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/independent-artifact-audit.json)。静态减少指令不能当实测收益。


固定原UUID的correctness001原316（314 numeric+2 run-only）和tail001六项均exit0/valid=true/contaminated=false，独审逐项核参数、seed、包hash及冻结参考。[正确性监控](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/correctness-001/manifest.json)、[边界结果](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/tail-results-001.json)。

comparison001在同卡空闲后完成，monitor finished/exit0/valid=true，无污染；原6A+5B、每轮3shape×10samples不变。根从冻结工具重新校验11报告/330样本、包/初始基线/输入hash，原始样本重算与summary逐字段相等。下表为外层轮均值的均值±标准差，收益由相邻A几何插值计算，不能仅用表中A/B均值相除。

| s_kv | 007对照A μs | 025候选B μs | 对007加速 / 耗时降低 | 对初始加速 / 耗时降低 | 实测TFLOPS / 理论利用率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.349517 ± 0.414234 | 357.680400 ± 0.359154 | 0.177457% / 0.177143% | 12.115872% / 10.806563% | 960.626816 / 42.694525% |
| 8192 | 359.006517 ± 0.590372 | 358.242680 ± 0.640576 | 0.181924% / 0.181594% | 11.947287% / 10.672243% | 959.119063 / 42.627514% |
| 32768 | 364.133200 ± 0.831365 | 363.875460 ± 0.456990 | 0.064541% / 0.064500% | 10.897882% / 9.826953% | 944.271932 / 41.967641% |

汇总对007加速 **0.141292714%**，耗时降低 **0.141093359%**；对不可变初始加速 11.652377447%、耗时降低 10.436300340%。五对汇总加速分别为 0.197930%, 0.080674%, -0.014640%, 0.060378%, 0.382600%。三shape最大相邻A漂移分别为0.201597% / 0.349217% / 0.526090%；存在负pair，本轮不证明稳定的小幅收益，不收入开头的可复现收益表。

**拒绝025。** 汇总未达严格>0.5%采用门槛，三原shape也均未达45%。单项023/024各自小幅正收益不能相加预测组合，025实测即本表。没有GPU污染记录，不追加同候选benchmark挑数据。[完整比较](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/comparison-001/summary.json)、[监控](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/comparison-001-monitor/manifest.json)、[根复验](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/comparison-001-root-revalidation.json)、[采用决定](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/decision.json)。

为解释组合未复现单项收益，按draft追加原8192 full/source诊断，核真实fast/slow执行、LDC/BRX及rowmax/pipeline等待；该采集不改变拒绝结论，不是新benchmark尝试。full/source诊断均有效完成，根直接读取四份原始报告并经独审核对；当前已恢复007源码和扩展并touch phase，恢复hash已独立验证。静态PC分类在profile/head64-iter025-codegen，原捕获在profile/head64-iter025-kv8192。


025诊断补充：40个slowmask PC在full/source都具有明确的0执行计数；guard为6×163840、rowmax为16×163840，目标代码生成真实生效。但guard新增constant-LDC依赖，其消费者source/full short-scoreboard为108/104；必要mask-LDS消费者为204/216。未执行的slow首PC仍有129/138个branch-resolving采样，不能据采样说慢路径实际执行。QK-done long为1326/1225（007为1238/1093），SO-ready为141/148（007160/138）；这些采样支持等待仍在，不构成耗时分解或组合收益损失的确定因果证明。

full occupancy15.568175%、TC elapsed46.202077%、DRAM读/写峰值10.155201%/7.606718%，57个非零LSU共享PC全为actual=ideal，合计5363144，无local流量。NCU replay368.864μs仅诊断，仍不能替代原TFLOPS/2250口径。详见[六维诊断](../../profile/head64-iter025-kv8192/REPORT.md)、[根原报告解析](../../profile/head64-iter025-kv8192/analysis/root-evidence.json)、[独立原报告复核](../../profile/head64-iter025-kv8192/analysis/independent-review.json)、[007恢复记录](../../runs/main-clean-series-001/iter-025-mask-rowmax-combined/restoration.json)。CPU parser曾因BRX显示可选逗号失败，严格语法规范化后通过；原失败日志保留，未重采GPU。

并行完成[poly5两层减法打包研究](poly5-subtract-pack-feasibility.md)：语义可保持，但未实现/编译/测速；理想净减指令仅约0.423%，目标PC等待很少，暂缓性能候选。025不保留、最终45%目标未达到，下一轮须重新以实际瓶颈证据选定方案。


## iter026 准备：合并 QK 等待，原数学保持

父版007已恢复；新候选目录 [iter-026-qk-wait-coalesce](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/)；[执行计划](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/executable-plan.md)已在实现前冻结。仅将第二半KV的expect/wait移动到全部32条QK MMA之前，最后统一执行after-thread-sync；原8SS+24TS、同P448、K16顺序和清C/累加规则不变。不会把PTX排序约束称为硬件drain，也不依据原KV1零重试承诺提前等待仍为零。

root重新直接解析007/025各full/source：[原始证据](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/root-parent-ncu-evidence.json)。四份均32QK、每tile一次KV1初查且无失败/重试；第一半仍有大量等待。隔离完整TU attempt001双架构编译exit0，168/152 registers、zero stack/spill/local，实际两半KV检查均位于首QK之前、32QK间无wait/branch。独立审查/正式构建/原316+tail6/交错比较待完成，当前性能 **N/A**，未采用。

本轮研究还完成 [双P与等待合并](qk-two-accumulator-feasibility.md)、[collector](qk-collector-feasibility.md)与[四warp nonWS布局](nonws-fourwarp-followup.md)。双P的额外读取/加法成本确定而收益未证，暂缓；原WS QK无重复B可直接利用collector。nonWS O的Interleaved布局确实只占256列，消除了先前特定布局的容量否决，但Q搬运、P/O线程归属和32-head lazy-rescale通信须整体重做。它们不是已通过完整TU/GPU的候选，也不计入收益表。

## iter026 有效比较：等待前移导致回退，拒绝

原316（314数值+2run-only）及6tail均valid001通过；正式与独立artifact审计通过。phase `8304b8454674b9814513b9f427789e9ccbe4de93362d529074483f61eba4daa9`，extension `6451aab1070752a88419b8b92fce6f6d73d7d7cc4dc0aea9c8155e1449e6af72`。完整双架构CUDA13.1.115原flags：168/152 regs、zero stack/local/spill；原setup仅34/34 CUTLASS豁免。机器码每架构少16条，原32QK/8PV及所有数学保持，仍不足以证明收益。

固定UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原五对、11report/330样本；comparison001 monitor finished/valid/exit0、无污染，无重跑挑选。下表SD为五个B round means和六个A round means的样本标准差，不是置信区间。

| s_kv | 007 A µs ± SD | 026 B µs ± SD | vs007加速 | vs007耗时降低 | vs初始加速 | vs初始耗时降低 | TFLOPS | /2250理论利用率 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 358.112867 ± 0.206076 | 362.199960 ± 0.148773 | -1.118718% | -1.131375% | +10.716881% | +9.679537% | 948.640038 | 42.161779% |
| 8192 | 358.772383 ± 0.079003 | 362.889780 ± 0.125887 | -1.137954% | -1.151052% | +10.513710% | +9.513490% | 946.836760 | 42.081634% |
| 32768 | 364.048250 ± 0.245793 | 370.697700 ± 0.175920 | -1.801929% | -1.834994% | +8.856942% | +8.136313% | 926.893757 | 41.195278% |

汇总加速 **-1.353379092%**，耗时增加 **1.371946732%**；对初始加速 +10.026013525%，耗时降低 9.112402789%。五对汇总均负，全部15个shape-pairs回退；各shape最大相邻A漂移0.126111%、0.062503%、0.152991%，远小于本轮回退。决定拒绝，不加入已验证收益表，不叠加前几轮收益。三组45%目标未达到，当前最佳仍007。

证据：[原比较](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/comparison-001/summary.json)、[根复算](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/comparison-001-root-revalidation.json)、[决定](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/decision.json)、[正式包审计](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/actual-package-audit.md)。已在比较结束前追加独立诊断计划；保留026仅用于原8192 full/source，完成后恢复007。当前尚不把回退定量归因于KV1重试或fence。


### iter026 诊断完成并恢复007

[完整NCU报告](../../profile/head64-iter026-kv8192/REPORT.md)及[根四raw解析](../../profile/head64-iter026-kv8192/analysis/root-evidence.json)已归档。原8192 full47/source5 passes均valid/exit0/无污染，使用冻结026正式包。KV1原007两capture初查失败/重试都为0；026 full/source首次失败33135/33163（每份40960tile），重试236124/231686。QKdone long-scoreboard采样从1093/1238增至1349/1508；QK MMA MIO采样从190/210降至116/129。实际发行更紧凑但等待更早暴露，支持损失搬运/计算重叠的解释；不把次数/采样换算成微秒，也不称移除fence消除了硬件drain。

资源、32QK/8PV、Qcopy/TMA和数学均保持。026 full tensor elapsed45.478434%仍不是目标口径；原8192 benchmark理论利用率只有42.081634%。四raw57个LSU shared位点actual=ideal5363144，不能直接采用全客户端bank-conflict警告做源码归因。PM长等待贯穿主体；026 wait PM无数组，不按0处理。详细六维及缺失/窗口限制见报告。

已按[恢复记录](../../runs/main-clean-series-001/iter-026-qk-wait-coalesce/restoration.json)恢复007源码与包365dfcb7，phase重新touch并SHA核验；当前无GPU句柄，未重复benchmark。独立原316/tail6/330样本及恢复审计已complete_verified；四raw与根报告独审为raw_full_source_and_root_report_verified，所有输入哈希由root再次核验。三组45%目标保持未完成。

下一方向已有[nonWS Qcopy 研究](nonws-qcopy-options.md)：rank4 OOB低head16/group4可在两批48KiB staging中构造目标DP行，预计QT仍6TMA而cp48→24；纯CPU坐标模型通过，driver encode、真实CuTe布局、两批phase与全hq fallback尚未验证。此为下一候选的可行性输入，不计为已实现性能收益。


## iter027 立项：四warp nonWS P/O与两批QT

父版007；[冻结可执行计划](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/executable-plan.md)已在实现前写入docs/draft.md，SHA `b8451d77657debb0cda455b41fe01ec65a5c8d4079ade82ad1a42eeac4164ea6`。本轮改P/O为nonWS，用warp内xor16合并同行partial；双代flags保持原32head缩放组，用一次128barrier替代旧rowmax交换及loop64。QT经raw rank4 OOB生成padded布局，复用48KiB staging两批，预计24cp；低层hq1..63用同kernel rank3四组fallback。保留007分半QK与KV1搬运重叠，不叠加026的等待前移。

[根重新读取007原NCU](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/root-parent-ncu-evidence.json)：loop64/rowmax128各163840 warp instructions，peer load+consumer的full/source barrier采样385/369、short239/239，Qcopy48/query。新方案仍有32QK/8PV，并增加QT shared读量与内部cp完成等待，收益未知。真实CuTe/driver/Qcopy功能探针、完整TU资源、独立数学/同步、原316+tail与固定协议性能尚待验证；当前性能N/A，未采用。


### iter027 CPU布局/编译与driver编码进展

隔离snapshot phase `b31022f546563abf438a3baadb22fc535bf3aec4981da1047240cf46513916d2`，config `bf39995c6ab1989b4c9ddd20fa2e77f5c62fd9a22a80db4201b70fa06b8e9e3a`，common与007逐字相同。首次完整TU编译attempt001 exit0；SM100a157、SM103a155寄存器（相对007168/152为−11/+3），两者stack/spill/local均0。实际CuTe布局检查通过，SharedMemoryPlan=221504 B（007222480 B），原384threads/266workers/4acks/3slots保持。

真实布局探针attempt001因无cudart链接失败、002缺CCCL include、003纯host不能解析host.h kernel launch，均保留；attempt004使用仅省略host launcher的include shim、真实device traits/layout库完成逐坐标检查，不是候选kernel编译失败。独立源码审查发现rank4 stride组乘法可能先int溢出，已在首次TU编译前提升为uint64，旧snapshot保留source-revisions/precompile-001。

root在固定UUID执行 [encode-run-001](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/probes/encode-run-001/manifest.json)，finished/valid/exit0、无污染；真实driver13020的128组hq1..64×contiguous/padded编码全部成功、map128B对齐。此检查没有启动GPUkernel，不代表QT搬运正确。

实际双arch机器码各3160条含padding，普通nonWS UTCMMA32QK+8PV、UTCCP24/query，原分半QK中间KV1等待保留。单个16x32bx2 PTX P load展开为两条LDTM（半warp各一），不能按单机器指令报告；hq64动态QS2+QT6TMA与fallback静态分支须区分。Qcopy功能probe、独立数学/同步终审、正式构建及原316+tail+额外case/五对比较待完成；性能N/A，未采用，主源码与包仍007。


027 Qcopy probe build001显式归档编译失败（-arch简写带入不支持tcgen05的sm100），build002成功未运行，build003补probe自身proxy/跨线程fence后运行。qcopy-run001无污染但exit1，monitor因command_failed而valid=false：128case所有12582912 QT BF16与canary均正确，126case的QS/stage裸shared读回失败。root与map查到probe把smem_ptr_flag布局直接作为元素下标，而真实CuTe将swizzle放在byte pointer；正在用实际tensor指针CPU回放和新probe验证修复，不删除或放宽检查。失败原始日志及根记录[root-qcopy-failure-001.json](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/probes/root-qcopy-failure-001.json)保留；此时尚不能宣称Qcopy gate通过，candidate源码不变，性能N/A。


### iter027 正式构建与完整正确性通过，性能比较待完成

Qcopy probe读回修复的纯CPU真实pointer回放精确复现run001全部128case的5085184错误，正确CuTe tensor访问全0；补验S4096/O32768实际向量pointer/对齐/唯一覆盖通过。build004仅修probe读回，candidate源码不变；固定UUID qcopy-run002 finished/valid/exit0，无污染，128case×4query的QT12582912、QS4194304、stage12582912 BF16检查与canary全部通过，独立审核同意。run001仍保留失败。

正式原setup exit0；extension `1366b19b2aa90f8846e739f0ee574294e9ade3d508fb81de0c8617d12ec6953f`。两arch实际全部SASS/control/.text/.nv.info及constant2对隔离CPU001一致，157/155 REG、零stack/local/spill，原34/34 CUTLASS豁免。root与独立artifact审计均passed；独审第一次仅因operand证书格式包含PV附行与旧32行假设不符而失败，schema修正及原日志保留，未重编或变更kernel。

原316（314numeric+2runonly）、冻结013tail6、027extra14全部valid001/exit0/无污染。extra14覆盖28次真实lowlevel调用+3次publiccontrol，原reference/容差、连续/带padding三输出bits、输出canary、全无效行零输出均通过。对应[root preflight](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/root-preflight-review.json)、[artifact audit](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/actual-package-audit.md)、[extra结果](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/extra-results-001.json)。

原五对comparison001已启动监控，当前在同UUID等待其他GPU任务结束，尚无有效benchmark结果；性能N/A，未采用，verified best仍007。正式027源码仅暂留实验工作区供比较和随后原8192 full/source诊断；新main-clean-5保持干净。


## iter027 有效比较：四warp nonWS方案明显回退，拒绝

固定UUID、原五对、11report/330样本全部完成且monitor valid/exit0/无污染。比较开始前等待了其他任务结束，运行期间没有污染；没有挑选重跑。原316+tail6+extra14均通过，正式包及双架构资源见上一节。下表SD来自五个B round means和六个A round means，不是置信区间。

| s_kv | 007 A µs ± SD | 027 B µs ± SD | vs007加速 | vs007耗时降低 | vs初始加速 | vs初始耗时降低 | TFLOPS | /2250理论利用率 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 358.012150 ± 0.069239 | 454.221960 ± 0.439901 | -21.182688% | -26.875680% | -11.713538% | -13.267649% | 756.452602 | 33.620116% |
| 8192 | 358.668983 ± 0.056625 | 452.584540 ± 0.410587 | -20.750162% | -26.183224% | -11.388277% | -12.851885% | 759.189396 | 33.741751% |
| 32768 | 364.043600 ± 0.199927 | 457.742320 ± 0.221840 | -20.467966% | -25.735500% | -11.843375% | -13.434470% | 750.634950 | 33.361553% |

汇总加速 **-20.800818055%**，耗时增加 **26.263930440%**；相对初始加速 -11.648603703%，耗时增加 13.184402501%。全部15个shape-pairs回退，五对汇总都负。各shape最大相邻A漂移 0.047443%/0.040199%/0.116155%，远小于回退。拒绝027，当前最佳仍007，三组45%目标未达成。

证据：[原比较](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/comparison-001/summary.json)、[根复算](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/comparison-001-root-revalidation.json)、[决定](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/decision.json)。已在采集前冻结原8192 full/source诊断计划；诊断完成后恢复007。当前不将回退定量归因于P双load、nonWS MMA或QT等待，须读原始NCU证据。


## iter028 准备：保留原重叠的 K64 QK 小循环

父版本007。实现前已冻结[执行计划](../../runs/main-clean-series-001/iter-028-qk-k64-loop/executable-plan.md)，SHA `bd0f92b4d1b9138374337f7c15962037493fa4e6fd45e0e33a085f1f4110d516`，同时写入docs/draft.md。原三个QK调用改为2/2/4轮K64组，组内保留原4条K16；目标静态12个MMA位点、动态仍32条，同8SS+24TS顺序，KV1等待仍在动态第16/17条之间。只研究缩短描述符存活及UR/GPR搬运，不混入026等待前移或027模式切换。

007原full/source每tile相关operand定义176条，另6 MOV.SPILL+6 R2UR.FILL；这些为UR/GPR搬运，并非local spill，也不是188条全部可删除。循环控制和重复descriptor构造可能抵消收益。当前仅授权隔离完整TU CPU实现；必须通过真实CFG动态操作数、完整新增loop-control计数与净指令减少、双架构零spill资源及独审，再考虑GPU。性能 **N/A**，主源/包仍007，三组45%目标保持未完成。


### iter027 诊断完成：减少同步未弥补 nonWS 模式成本

原8192 full47/source5 passes均finished/valid/exit0、无污染。根直接读取007/027四份原始NCU，分别核对每份2751/3159个可用PC与正式SASS；独审重新核四raw的指标、全部PC/组/PM及最终报告，已通过。[完整报告](../../profile/head64-iter027-kv8192/REPORT.md)、[根解析](../../profile/head64-iter027-kv8192/analysis/root-evidence.json)、[独立审查](../../profile/head64-iter027-kv8192/analysis/independent-report-review.md)。

每份原8192capture的QK/PV动态MMA保持1310720/327680，Qcopy196608→98304，named barrier411376→247536；但P load163840→327680。QKdone long-scoreboard full/source由1093/1238升到4285/4505，SVdone S复用148/144→555/579。原rowmax peer的barrier样本385/369降至flags peer的159/173，是局部改善，不能抵消或量化整体回退。

由采集的SM elapsed cycles和tensor elapsed百分比推导归一化活动量C/R，41943040→83886080；active口径复算相同。原始裸tensor周期和peak rate未单独采到，不能把该乘积冒充裸counter或逐MMA延迟。官方PTX明确M64 nonWS仅一半datapath，结合相同数学/MMA数和完成等待增长，支持模式/shape执行效率损失的主要解释；不证明隐藏M128计算或单条指令恰慢两倍。NCU72.232504%仍不是目标理论利用率，实际benchmark仅约33.4–33.7%。

027资源157/155 registers、零stack/local/spill，dynamic shared221504；仍1CTA/SM。DRAM读/写峰值8.142658%/6.125541%，无HBM带宽饱和证据。四raw共性为57个非零LSU shared位点actual=ideal5363144，只能排除该客户端的差额，不能外推TMA/tcgen。PM长等待贯穿主体，独立窗口和缺失值限制见报告。零动态O rescale只在这四份8192 profile捕获中观察到，不覆盖所有benchmark调用。

007源码/扩展已按[恢复记录](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/restoration.json)恢复，根再次验证phase `cf25f7dd…c4fa0`、config `e7fbe863…3723`和扩展 `365dfcb7…03da`。027拒绝不变，全部失败probe/解析尝试及修订记录保留。下一方向保持007 WS与原KV重叠；028仅进入隔离CPU检查，尚无性能结论。

027最终结果/恢复独审已 `complete_verified`，并与冻结决定逐项一致；root重核artifact、result、NCU文本审查的全部输入哈希。见[最终审计](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/independent-result-audit.md)及[根哈希复核](../../runs/main-clean-series-001/iter-027-nonws-fourwarp/root-independent-checks.json)。原316、6tail、14extra、11报告330样本及主007恢复全部闭合，45%目标仍未达成。


028 CPU attempt001 原完整双架构编译 exit255，14.44s后日志仅 `Segmentation fault`；无object/cubin/资源数据，不能判零spill或codegen通过。冻结phase为 `edaa66bd515a66d4e16549f10617e0e3d22227d37d252a1c849c85fd1e518266`，config/common仍007。独立源级审查同意2/2/4分组数学和同步，但实际机器码门槛仍未知。根与实现agent确认旧进程终止后，在原设计不变前提下先冻结[诊断附录](../../runs/main-clean-series-001/iter-028-qk-k64-loop/build-diagnostic-addendum-001.md)，仅允许新attempt002增加keep/verbose输出以定位编译阶段；不降低优化或放宽spill检查。性能N/A、未运行GPU。


### iter028 关闭：固定编译器后端失败，性能 N/A

诊断attempt002同一源码及原base flags，在两个架构都成功生成PTX后，sm100a/sm103a的ptxas分别报 `--error 0x8b--` / `Segmentation fault`，exit255、14.1325s，无cubin/object。这定位了本次失败阶段，未证明具体后端缺陷或源码语义错误；attempt001的稀疏日志仍只记阶段未知。全部13个中间文件/命令/源码SHA/终态检查均保留；未做第三次尝试或改优化flags。

独立源级审查重建全部五处替换、原32步数学序列与262144 shared地址模型，原KV1仍在动态16/17之间；但PTX20个静态WS位点（12QK+8PV）不证明实际SASS循环、资源或净指令下降。两架构codegen/资源均**未知**，不能写成零spill通过。故按计划CPU拒绝，正式构建、原316/tail及性能比较均未执行；对007/初始基线的收益和理论利用率全部 **N/A**，不是实测性能回退。

[实现记录](../../runs/main-clean-series-001/iter-028-qk-k64-loop/implementation-report.md)、[独立终审](../../runs/main-clean-series-001/iter-028-qk-k64-loop/independent-source-audit.md)、[决定](../../runs/main-clean-series-001/iter-028-qk-k64-loop/decision.json)、[主007保持记录](../../runs/main-clean-series-001/iter-028-qk-k64-loop/main-preservation.json)。root重核独立审计全部输入hash。当前主源/扩展始终007，无GPU任务，三原45%目标仍未完成。后续双consumer方案仅处于独立状态/资源可行性审查，尚未实现新候选。


## iter029 — 两个consumer交替tile：CPU寄存器分配失败

父版本007；新实现512线程/394 workers、单P/S、两槽early-mi/partial-li交接，WG0固定输出。完整可执行计划先于隔离实现冻结。原完整TU attempt001退出255（23.109s），ptxas C7600明确无法按168寄存器目标分配；同源同优化选项的keep/verbose诊断002退出255（17.335s），定位SM100a ptxas同一错误。SM103a只产出PTX，日志没有其ptxas执行结果，不能称两架构均已失败或通过。两次均无object/cubin/实际资源或SASS。

实际host sizeof/offsetof probe exit0：shared226112 B、align16，512线程394参与者，满足232448 B上限。原公式、数学helper及epilogue源级检查通过；模型v3的784序列与phase反例检查完成，均不能代替GPU正确性和机器码证明。独立源码审查已请求，结果尚待返回。

| 原负载skv | 实测耗时/波动 | 对父007收益 | 对初始收益 | TFLOPS/2250 | 正确性 |
|---|---|---|---|---|---|
|4096|N/A|N/A|N/A|N/A|未运行GPU|
|8192|N/A|N/A|N/A|N/A|未运行GPU|
|32768|N/A|N/A|N/A|N/A|未运行GPU|

拒绝本配置，原源码/包从未应用029并已验证仍为007；固定GPU UUID仍为GPU-847489a9-bc7e-726c-1c64-29c59e330fd8，本轮未使用。这不是实测回退。诊断PTX显示两元素phase数组产生local访问，但由于无最终SASS，不能把它当成已证最终spill或C7600根因；下一独立计划先验证phase标量化。全部失败日志、13项中间产物SHA、source/parent补丁和root审计见[029实现报告](../../runs/main-clean-series-001/iter-029-dual-consumer/implementation-report.md)及[决定](../../runs/main-clean-series-001/iter-029-dual-consumer/decision.json)。45%三负载目标仍未达成。


## iter030 — phase两bit标量化：消除前端local，但仍分配失败

父版本007，实现基础为未通过资源门槛的029；仅5处源码改写将h[2]两parity压入uint32，预算保持168/168/128/48。生成器148410项公式检查通过，包含784组跨query序列；config/common不变。完整TU原flags attempt001退出255（16.820625s），C7600 target168；冻结诊断002后同源keep/verbose退出255（15.683758s），日志明确两架构ptxas均报同错。两架构PTX已无.local声明、ld.local、st.local，说明该前端对象已去除，但不证明实际无spill，更不证明它是此前失败的唯一原因。无成功object/cubin/SASS/实际寄存器资源。

三个原负载skv4096/8192/32768的正确性、耗时波动、对007收益、对初始收益和TFLOPS/2250全部N/A（未运行GPU）。拒绝030；主源码/包007未改。原固定GPU UUID及协议保持，本轮未使用GPU。证据见[030决定](../../runs/main-clean-series-001/iter-030-dual-consumer-phase-bits/decision.json)和其cpu-build/attempt-001、002原日志/中间产物；独立增量审查待绑定。

## iter031 — 176/176/96/64寄存器预算：CPU分配失败

父版本仍007，实现基础030；单独调整三个完整WG寄存器操作：consumer176、producer96、control64。按初始128的静态总数65536仍仅为预算假设，未得到成功metadata证明。依据是原producer有96预算无spill的完整TU历史编译实例，不能当新候选资格。新方案先冻结计划，再以原完整TU/双架构flags编译；attempt001退出255（16.480449s），C7600 target176。该单条日志未分开架构或角色，因此不指认具体失败角色或声称双方分别失败。无object/cubin/成功资源记录。

三个原负载skv4096/8192/32768的正确性、耗时波动、父/初始收益、TFLOPS/2250全部N/A；拒绝此预算和CFG配置，不是实测回退。主源码/包仍007，GPU未使用。证据见[031决定](../../runs/main-clean-series-001/iter-031-dual-consumer-reg176/decision.json)与原build.log。下一研究比较持续角色分支内的setmaxnreg位置与当前分支汇合后的分配约束；尚未证明C7600原因，不继续盲目提高预算。三负载45%目标保持未完成。


029–031独立审查已收尾：各自source_math_lifecycle_passed=true，但总体passed=false，因为编译资源门槛失败。root逐项复核三份审计输入和脚本SHA，绑定各decision与root-independent-checks.json；三版均没有机器码/运行/性能通过。此前“待独审”是当时阶段状态，以上为最终CPU关闭状态。


## iter032 — 持续角色分支内重配：B200无spill，SM103仍失败

父007，实现基础031；保持176/176/96/64预算，只把三只setmaxnreg移至完整consumer/producer/control角色分支入口。原完整TU双架构编译exit0（22.129595s），说明这种源码CFG已能生成实际产物；不把这一对照推广为全部C7600的唯一原因。actual ELF两架构均initial REG128/MAXREG_COUNT128/MAX_THREADS512；动态inc176/dec96/dec64与整WG角色路径对应。

SM100a stack/spill均0、无LDL/STL；SM103a stack8B、spill store4B/load36B，actual1STL+9LDL。root与独立审查均追踪SM103 00b0 tid>>7→00d0 SHFL→00f0 STL为独立WGidx值，后续在热路径读回；不是可豁免的guard-only路径。resources的LOCAL:0不覆盖这份stack/spill证据。保持原双架构零spill门槛，拒绝032，尚未正式build或GPU运行。

三个原负载skv4096/8192/32768：正确性、耗时与波动、对父007/初始收益、TFLOPS/2250全部N/A。固定GPU UUID未变，本轮未使用；主源码与包007从未被032替换。源码/实际资源独审及root逐输入hash核验完成，证据见[032决定](../../runs/main-clean-series-001/iter-032-dual-consumer-role-reg/decision.json)、[独审](../../runs/main-clean-series-001/iter-032-dual-consumer-role-reg/independent-source-audit.md)及root-resource-evidence.json。下一033仅从已有uniform warp编号推导WGidx，不放宽预算或spill门槛。


## iter033：由统一 warp identity 推导 WG，CPU 资格通过，正式验证进行中

采用父版本仍为007；实现基础为032，仅将 WG identity 改为既有 `warp_idx / 4`。原 flags 双架构完整TU均exit0，实际初始128 registers/thread，动态预算176/176/96/64，零stack/local/spill，512线程、dynamic shared226112。实际QK/PV操作数与007匹配，新增R128–R175的首次读取有先行定义；完整源生命周期、实际寄存器范围与独立审查均通过。根代理重核77个输入文件及实际cubins/host launch，见 [CPU资格](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/root-cpu-qualification.json)。

当前仅允许推进正式构建。原316、tail6、额外数值/存储、typed replay与真实CLC覆盖均尚未运行；性能与三负载理论利用率为 **N/A**，未采用、未计入开头收益表。UUID仍为GPU-847489a9-bc7e-726c-1c64-29c59e330fd8，正式测量参数、2250 TFLOPS分母及>0.5%采用门槛不变。

iter033正式构建补记：原setup exit0，24.037447秒，原34/34 CUTLASS豁免不变；extension `66ecbdd6694b13f5bd51522caed95e4199aa7f8f9bbe83529bc0db780929a61c`。双架构正式完整text、SASS/control、nv.info与CPU001相同，constant2均不存在，只有debug/internal ID差异。根代理独立核21输入、10工具输出及实际ELF sections，见 [正式资格](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/root-formal-qualification.json)。原316 runner001已启动，等待固定GPU上的外部进程退出；未获得正确性或性能结果。额外验证计划在实现前已冻结到docs/draft.md。

iter033额外验证准备补记：formal harness已实现67个case，计划135低层调用+4公开对照；host-only ABI实测通过，根代理与独审CPU复算通过。首个freeze001的branch预期mi初值错误已在freeze002修正，原记录保留且从未GPU执行；当前只使用002。见 [formal harness资格](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/extra-tests/root-formal-harness-qualification.json)。typed replay/真实CLC派生源码已生成，仍待编译与运行资格。原316仍在固定卡空闲等待，所有runtime及性能结果保持N/A。

iter033原316运行结果：correctness-001 finished/exit0/valid=true、无foreign干扰，全部316通过（314 numeric、2原run-only，head64子集158），逐case参数与seed0…315精确等于初始基线。见 [根代理原suite复核](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/root-original-runtime-001.json)。验证suite附带的单次性能输出不替代五对正式comparison，当前采用/45%结论仍未成立。tail6及extra formal已按同UUID锁排队，diagnostic CPU仍进行中。

iter033诊断资源门槛失败（正式候选仍零spill）：typed replay与真实CLC trace的attempt001均完成原flags双架构编译exit0，但新增诊断记录后出现如下stack/spill，驱动按既定门槛exit2，均未link、无DSO、无GPU运行。编译期shared size/alignment/response offset断言通过；原产物与完整日志保留，接下来只分析实际对象，不改flags/预算或删记录绕过门槛。

| 诊断变体 | 架构 | REG | stack bytes | spill stores bytes | spill loads bytes |
|---|---|---:|---:|---:|---:|
| replay | sm_103a | 128 | 8 | 48 | 108 |
| replay | sm_100a | 128 | 16 | 52 | 744 |
| clc-trace | sm_103a | 128 | 16 | 64 | 864 |
| clc-trace | sm_100a | 128 | 16 | 56 | 756 |

此失败不撤销033正式原316通过，也不能证明诊断运行通过。性能比较仍N/A。见 [诊断资源失败证据](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/extra-tests/diagnostic-resource-failure-001.json)。

iter033正式运行验证补记：tail-correctness-001和extra-tests/runs/formal-001均finished/exit0/valid=true，无外部竞争。原六tail通过；67个额外case完成135次低层+4次公开控制，原FP32 reference/checker、三输出A/B bits、R1换poison重复、405份输出guard、1044次完整输入backing检查和150次allinvalid行检查均通过。根代理核所有逐call记录、原参数/seed、冻结代码、加载DSO/module hash与监控： [tail复核](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/root-tail-runtime-001.json)、[extra正式结果复核](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/extra-tests/root-formal-result-audit-001.json)。这些结果不证明真实CLC复用覆盖；诊断资源门槛仍未通过，原五对comparison尚未运行，未采用033，45%目标未完成。


### 033 diagnostic fresh-TID attempt002 — resource gate failed

Frozen addendum `extra-tests/diagnostic-fresh-tid-plan.md` SHA528cd483… was appended to draft before implementation. Only seven helper identity expressions and one forceinline volatile PTX accessor changed. Root and independent actual complete-tree/inverse/argv checks passed; every original phase/config/callback/Q-copy byte and all formal freeze002 files stayed unchanged. The original dualarch flags and176/176/96/64 budgets were retained.

|Diagnostic|Arch|REG|Stack B|Spill store B|Spill load B|
|---|---|---:|---:|---:|---:|
|clc-trace|sm_100a|128|8|8|8|
|clc-trace|sm_103a|128|8|4|44|
|replay|sm_100a|128|8|8|8|
|replay|sm_103a|128|8|4|44|

Both compilers exited0 (replay21.4561s;CLC18.8836s); builders exited2 at the unchanged resource gate before link. No diagnostic DSO or GPU run exists. Root independently dumped both objects and reproduced ptxas spill byte totals from actual STL/LDL. The remaining100 slots carry WG-local thread identity;103 saves canonical warp identity. The original repeated bounds/predicate spills are no longer observed, so the bounds proposal is deferred. Preserve attempts001/002 and investigate narrow identity lifetime changes before a new source attempt.

Performance vs007/initial: **N/A**; these diagnostic resource reductions are not speedup evidence and do not change formal033 validation or adopt033. Best007 remains unchanged. Evidence: `iter-033-dual-consumer-uniform-wg/extra-tests/diagnostic-resource-failure-002.json`, `root-resource-analysis-002/`, `build/{replay,clc-trace}/attempt-002/`, and independent fresh source review. Goal remains unmet.


### 033 diagnostic scoped identities attempt003 — SM100a clean, SM103a resource failure

Frozen local-ID plan SHA c4f6dd25… added two per-tile/epilogue local ID declarations and six late warp ID reads. Full trees differ only in phase1.cuh; the eight exact operations reverse to002 and the full diagnostic inverse restores033. Root and independent512-thread value/scope/argv checks passed, preserving original role dispatch and producer local identity. A CPU proof-generation interruption caused solely by four concurrently added analysis files was preserved and recovered without source/script/old-file changes.

Original dualarch compilers exited0: replay20.2354s,CLC22.6150s. Both variants now have initial REG128 and **zero stack/store/load spill on SM100a**. Both SM103a targets retain stack8/store4/load24; actual object dumps confirm one scalar store and six loads. Both builders therefore exited2 before link; no diagnostic DSO/GPU exists. Formal033 and best007 remain unchanged.

Performance vs007/initial: **N/A**. This is partial diagnostic resource progress, not kernel speedup or adoption. Preserve attempt003 and inspect its remaining WG-derived identity before any further repair. Evidence: `extra-tests/diagnostic-resource-failure-003.json`, `root-resource-analysis-003/`, `build/*/attempt-003/`, and `independent-local-ids-source-review.*`.


### 033 diagnostic consumer WG attempt004 — zero spill; helper artifact gate pending

Frozen plan SHA5ef36fa0… adds one consumer-local WG ID immediately after inc176. Exact scope/value, single inverse003/full inverse033, all6864-file tree and unchanged callback/helper checks passed root and independent review. Both original dualarch compilers and link commands exited0 (replay19.2900s;CLC17.9043s). Root independently dumped both final DSOs: all four kernels have initial128,zero stack/local/spill,noLDL/STL,original176/96/64 role instructions,32QK+8PV WS and48Qcopy.

The unchanged builder then rejected an actual helper CALL body differing from its fixed MOV/R2 template. Preserve both failed manifests and exact DSOs; do not silently whitelist the pattern or treat zero spill as runtime qualification. Actual caller/callee semantics,full register ranges/initialization,host launch and object-to-DSO binding audits are in progress. No diagnostic GPU run has occurred.

DSO SHA256: replay `c61aa28ce390fb3f66a18c584d4744a5f464950f0a606eb1d40792d01f3f9489`;CLC `abb7bad2c94b673b614078b85bf28c79c344c25a50cfde13ff03e303c72af124`. Performance vs007/initial: **N/A**. Evidence: `extra-tests/diagnostic-resource-status-004.json`, `root-resource-analysis-004/`, and `build/*/attempt-004/`. Formal033 and best007 unchanged; goal not achieved.


033 diagnostic004资格补记：实际双架构callee、寄存器范围/被观测位初始化、source/ABI、object与linked cubin、host launch及操作数审计完成。根代理重核234项输入、两个6864文件源码树并通过两个实际pre-Torch cpu_gate，独立artifact-qualification与qualified指针已封存。原builder failed和wholeword false均保留：helper等价清零及packedword被观测位补证分别说明，不声称所有高位已初始化。见 extra-tests/artifact-qualification-004-summary.json。下一步按冻结命令串行replay001/CLC001；此时GPU诊断未运行，性能N/A，未采用033。

033诊断运行补记：replay001 finished/exit0/valid=true，67cases/135calls，原数值与存储检查通过；root逐call405输出guard、1014输入backing、150allinvalid检查及41条原始telemetry复核通过，CPU checker重开所有raw payload/allocation复算通过。独立raw重建尚待完成。CLC001 childexit0但被2条foreign-process样本整体判invalid，完整保留，不用于覆盖/采用；按同UUID完整新编号002重跑，未改变源码或测试配方。性能仍N/A。

033 replay001最终补记：root与独立逐raw分配/记录/图链/mi/vote重建及数值、存储、输入配方、原始监控审计全部通过，root重核2844个绑定文件。共1192个query、469648个worker、320648对actual rs、305152对state、523264个tile-lane记录。见 extra-tests/root-replay-001-final-review.json。CLC002也被3条foreign样本判无效，001/002完整排除；16次×2秒连续空闲观察后按原wrapper规则启动003。正式五对performance仍未运行，best007和45%目标状态不变。

033额外验证全部收尾：CLC003 finished/exit0/valid=true，root完整原始44条telemetry、3case/7call、21输出guard、54输入backing、1408allinvalid检查通过；重开rawbuffer的原checker与独立successor图/128lane递推均通过。每份六主capture各1536queries、148actualorigins、最长13querychain，各自覆盖全部7项，repeat不补覆盖。001/002污染capture完整排除。见 extra-tests/root-clc-trace-003-final-review.json。现原316/tail6/extraformal/replay/realCLC全部符合冻结门槛；3110文件绑定的comparison-001-prelaunch.json封存后，已启动原6A5B/330样本比较，当前尚无性能采用结论。


### iter033 最终原协议结果：正确性通过，性能回退，拒绝采用

原五对 comparison001 在固定UUID上 finished/exit0/valid=true，77条原始监控无foreign。root与独立脚本分别复核11轮/330原始样本、加载包/原参数/seed/原始采样区间及相邻A漂移。A为007，B为正式033；诊断DSO未进入计时。

|skv|007均值±轮间SD µs|033均值±轮间SD µs|配对加速率vs007|耗时减少vs007|加速率vs初始|033 TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|358.002350 ±0.220273|374.351520 ±0.191771|-4.375565%|-4.575782%|7.122979%|917.846904|40.793196%|
|8192|358.751617 ±0.186402|374.997300 ±0.082994|-4.327773%|-4.523542%|6.945559%|916.266287|40.722946%|
|32768|364.071617 ±0.084500|379.831460 ±0.105537|-4.148329%|-4.327863%|6.239273%|904.604857|40.204660%|

汇总配对加速率−4.283939%，耗时增加4.475674%；全部15个shape-pair均回退（加速率−4.500517%至−4.123912%），三负载最大相邻A漂移0.102766%/0.087570%/0.025470%。相对最初main仍加速6.768587%，但不满足对当前最佳007的>0.5%采用门槛，因此拒绝033，开头保留收益表不新增033。三负载均未超过45%；仍保留完整目标。

正式316（314numeric+2原run-only）、tail6、extraformal67/135+4、replay001及真实CLC003全部通过冻结验证；CLC001/002因外部竞争整体排除。证据：[决定](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/decision.json)、[root复算](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/comparison-001-root-revalidation.json)、[独立复算](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/independent-comparison-001/REPORT.md)。033源码/正式包和所有失败诊断均留档，下一步按已冻结full/source计划定位回退；当前尚无NCU根因结论。

033拒绝后的恢复已完成：在独立profiling目录冻结033头文件和158份实际编译依赖后，将主worktree phase1.cuh/config.h/extension精确恢复为已采用007，三项before/after SHA均验证。正式033归档包与全部实验结果未改；见 [恢复记录](../../runs/main-clean-series-001/iter-033-dual-consumer-uniform-wg/restoration-007.json)。后续NCU使用033归档包和冻结源码，不把已恢复的主头文件误作033来源。

033首个NCU full尝试在新增profile入口的LD_LIBRARY_PATH精确检查处失败，发生于Torch/attention启动之前，无launch JSON或.ncu-rep；不是kernel数值或性能失败。外层原CUDA13.2环境正确，需实测NCU注入后的child环境后再冻结窄修复/newprofiling目录。原有效330样本拒绝决定与main007恢复不变，失败见 profile/head64-iter033-kv8192/failure.json。


### 033：r2 NCU诊断完成（不改变拒绝决定）

在原固定UUID、原8192/seed311输入和原Full/Source参数下，两次r2采集均exit0且监控有效。旧采集的pre-Torch环境guard失败完整保留；r2只绑定NCU实际注入后的子进程LD_LIBRARY_PATH，父环境和正式kernel均未改。Full有6个CTC指标缺失警告，Source无警告。

相对007，033 active warps从15.55%升到21.78%，但eligible从0.6512降到0.6158、issue从44.33%降到42.20%、tensor pipe elapsed从46.10%降到43.89%。Source QKdone组long-scoreboard样本1238→5587；新增query-start1047、finalearly296、finalli163。previousearly/li首次失败和重试均0，不能把该两条交接重试当成观察到的主要延迟。32QK/8PV/48Qcopy的动态计数一致，DRAM/L2流量与命中基本不变，未发现spill。更多消费者未在本次测量中改善有效发射或tensor活动。

[完整六维报告](../../profile/head64-iter033-kv8192-r2/REPORT.md)包含四份raw逐PC验证、独立审查、PM窗口限制、shareddriver标签修正、全部解析失败与24个域外采样PC的保留方式。上述NCU指标仅解释机制；原始330样本的汇总加速−4.283939%、耗时增加4.475674%及三组理论40.79/40.72/40.20%不变。033仍拒绝，已采纳007保持，严格全三组>45%目标尚未达到。


### 034：007上的固定四条TS指令块（正确性通过，性能小幅回退，拒绝）

父版本007。根据已复核的原QK发射窗口操作数准备和033未改善issue的证据，仅将原24条WS TS QK组织为六个静态4×K16 asm块，每组首操作数仍由原CuTe取得。SS8、KV1第16/17条边界、全部数学/布局/同步不改，不重复028的runtime循环。假设是减少实际操作数准备和UR/GPR搬运，不预报性能。

[执行计划](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/executable-plan.md)已在实现前冻结并写入docs/draft.md。隔离CPU及独立源代码/操作数/完整路径成本审查通过：每有效QK tile净少1条issued instruction，每初始issuer CTA增加2条；first-to-last MMA截断窗口反而196→197，不能将其当完整循环。正式构建exit0，双架构全部SASS及control编码、text/nv.info/constant2与CPU产物一致，REG168/152，stack/local/spill0，原34/34 exemptions保留。正式包SHA `dcda2ffe791e396ad8ac8a94964a7b5cd8ea9c616a6c93a8767432da7a8e1d55`，曾应用于实验主源码供验证；最终拒绝并精确恢复007。见 [CPU根复核](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/root-cpu-qualification.json)、[正式包复核](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/actual-package-audit.md)。


正式原316（314numeric+2run-only，head64子集158）与6tail全部通过根复核和独立审查。原5对比较共11轮/330样本，固定GPU UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；67条监控（3before/63running/1after）无foreign观测，最大运行采样间隔4.447s，不将采样监控表述为连续独占证明。

|skv|007均值±轮间SD µs|034均值±轮间SD µs|配对加速率vs007|耗时减少vs007|加速率vs初始|034 TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|358.187533 ±0.085404|359.142800 ±0.073116|-0.266399%|-0.267110%|11.659346%|956.715222|42.520677%|
|8192|358.870517 ±0.093519|359.969380 ±0.155559|-0.305597%|-0.306534%|11.410298%|954.518364|42.423038%|
|32768|364.141667 ±0.245625|365.085900 ±0.171327|-0.258406%|-0.259076%|10.530201%|941.141205|41.828498%|

汇总配对加速率−0.276803%，耗时增加0.277571%；全部15个shape-pair负（−0.346569%至−0.133368%）。三shape最大相邻对照漂移0.047256%/0.068534%/0.158131%。相对最初main的汇总加速仍为11.198892%，但不满足相对已采用007的严格>0.5%门槛，故拒绝034，开头已验证收益表不新增本轮。三组均未超过45%，完整目标仍未完成。

根复核直接验证全部330个原始end-start区间，独审独立计算均值/方差/几何均值与漂移。独审首轮把二进制.so误作UTF-8文本读取而失败，保留旧脚本和失败结果；audit002仅分开hash与文本读取，使用同一有效GPU采样，未重跑测量。

证据：[决定](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/decision.json)、[根复算](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/comparison-001-root-revalidation.json)、[独立复算](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/independent-runtime/comparison-001-audit002/REPORT.md)、[精确恢复007](../../runs/main-clean-series-001/iter-034-qk-ts-static-packets/restoration-007.json)。034全部源码、正式包、CPU和GPU证据保持归档。最小静态指令减少没有转化为本轮耗时收益；不将此结果直接归因为某条指令的延迟。


### 035：producer仅归约索引符号位（两次确认通过，采用）

父版本为已恢复007。原max只用于判断16个索引是否全部负数；计划以unsigned bit31 AND精确替换该局部归约，保留signed min、前三轮强制TMA和全部坐标/同步。原007 NCU定位18条max独占指令，但其计数不等于净可省工作或耗时。[执行计划](../../runs/main-clean-series-001/iter-035-producer-sign-and/executable-plan.md)已在实现前冻结并追加docs/draft.md；先隔离完整TU与实际codegen审查，当前主源码/包保持007，GPU尚未运行，正确性和各shape性能均N/A。

035 CPU进展：attempt001完整双架构编译exit0/22.186s，REG168/152、stack/local/spill0，静态指令计数2752→2744 /2816→2808；静态总量不能替代完整producer路径净成本和实际操作数证明，独审仍进行中。主007未改，GPU未运行，性能N/A。原研究1.902%混用source计数分子与硬件聚合分母，已[单独更正](../../runs/main-clean-series-001/iter-035-producer-sign-and/parent-counter-evidence-correction.md)；18个站点的2949120次执行经root直接重读raw确认，假设及门槛不变。

035 CPU完整审查已通过：两架构完整producer有效/skip路径每tile净少9条issued instruction，startup/query transition及相同retry结果净增0；索引/等待/短query/CLC及全部其他角色机器码已复核。78项输入在应用前重新hash；正式原setup构建exit0，归档包SHA `bc58f48c14a4f1ddd63e797b51d6154367b380b84f82dc72647810d89961aea6`，实际全部SASS/control及text/nv.info/全部constant与CPU相同，REG168/152，stack/local/spill0，34/34 exemptions。根复核和独立正式产物审查均通过，主源码/包暂为035供原协议验证，原316正在运行；GPU正确性结论和各shape性能仍N/A。

035原316（314numeric+2run-only）及tail6均通过根复核和独审。comparison001运行中监测到外部进程，整轮无效，性能N/A；root仅中断自己的wrapper，原finally清理自己的子进程组后终态exit-15（session exit241），全部原始数据和stop-request保留。未停止外部任务。随后在原UUID按完全相同协议开启comparison002，启动前仍要求连续3次idle；001任何已采样子轮不用于收益或采用结论。

035 comparison002有效：70条监控（4before/65running/1after），无foreign观测，330原始区间/包/参数均经root和独立复算。汇总加速0.528536287%，耗时减少0.525757468%；三shape加速0.575737843%/0.559113412%/0.450803402%，15pair均正。尚未采用：该汇总仅高出0.5%门槛0.028536个百分点，现按[事前冻结确认计划](../../runs/main-clean-series-001/iter-035-producer-sign-and/confirmation-executable-plan.md)再采一份完整同协议比较；保留002结果，无论确认结果如何均报告。当前理论42.876869%/42.777475%/42.116219%，全三组45%目标未达。

035有效comparison002逐负载（采用确认待003；±为轮间SD）：

|skv|007 µs ±SD|035 µs ±SD|配对加速vs007|耗时减少vs007|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|358.179950 ±0.163725|356.159280 ±0.189991|0.575738%|0.572442%|12.594708%|964.729555|42.876869%|
|8192|358.968633 ±0.130265|356.986820 ±0.049838|0.559113%|0.556005%|12.341111%|962.493191|42.777475%|
|32768|364.218200 ±0.036727|362.591780 ±0.227254|0.450803%|0.448780%|11.290493%|947.614929|42.116219%|

[002根复算](../../runs/main-clean-series-001/iter-035-producer-sign-and/comparison-002-root-revalidation.json) · [002独立复算](../../runs/main-clean-series-001/iter-035-producer-sign-and/independent-runtime/comparison-002-audit001/REPORT.md)。最大相邻A漂移依次0.094678%/0.066057%/0.020097%；数据采样监控不等于连续独占证明。

035确认comparison003运行中再次观测foreign，整轮无效、性能N/A。root只中断自己的wrapper2633749，由原finally终止自己的command2636969，终态exit-15，全部数据/stop-request保存。002仍是唯一有效性能结果；按先前冻结确认规则在原UUID开启004重试，不使用003子轮或改变门槛。


### 035：有效confirmation004与最终采用

004完成11轮/330样本，原UUID监控73条（9before/63running/1after），无foreign观测，最大running采样间隔4.754970s。根复算和独审通过；汇总配对加速0.514350%，耗时减少0.511718%，相对初始加速12.079446%。逐负载如下（±为轮间SD）：

|skv|007 µs ±SD|035 µs ±SD|配对加速vs007|耗时减少vs007|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|358.116200 ±0.071456|356.160880 ±0.170723|0.550660%|0.547645%|12.594202%|964.725221|42.876676%|
|8192|358.899533 ±0.100870|357.001800 ±0.112625|0.529244%|0.526458%|12.336397%|962.452805|42.775680%|
|32768|364.198717 ±0.290423|362.522200 ±0.214431|0.463168%|0.461032%|11.311853%|947.796807|42.124303%|

004全部15shape-pairs为正（0.332872%至0.635622%），最大相邻A漂移0.050948%/0.076568%/0.220913%。002与004各自严格超过0.5%，满足冻结确认条件，因此采用035并保留主源码/包；无形状回退。001/003受外部竞争影响整体排除，其子轮不计收益。边际虽小，原始两次结果都保留，不追加择优测量。

两次有效结果共660原样本、12A/10B轮。等权几何配对加速0.521443%、耗时降低0.518738%；三shape合并配对加速分别0.563198%/0.544178%/0.456985%。绝对耗时按10B轮算术均值为356.160080/356.994310/362.556990µs，理论42.876773%/42.776578%/42.120260%，仍全部低于45%。相对初始值直接计算，未叠加任何历史收益。

证据：[004根复算](../../runs/main-clean-series-001/iter-035-producer-sign-and/comparison-004-root-revalidation.json)、[004独审](../../runs/main-clean-series-001/iter-035-producer-sign-and/independent-runtime/comparison-004-audit001/REPORT.md)、[独立确认门槛](../../runs/main-clean-series-001/iter-035-producer-sign-and/independent-runtime/comparison-004-audit001/confirmation-gate.json)、[合并值与原始输入绑定](../../runs/main-clean-series-001/iter-035-producer-sign-and/combined-valid-results.json)、[采用决定](../../runs/main-clean-series-001/iter-035-producer-sign-and/decision.json)。下一候选须以已采用035为唯一父本，不能把007与035的指令节省或性能收益简单相加。


### 036：首索引有效时绕过归约（隔离CPU阶段）

唯一父本为已采用035。若本producer首索引在[0,s_kv)内，原signed min必小于s_kv，符号AND必为0，故invalid=false；否则保留完整035归约。只拆分原四次load与归约循环并包住归约，原should_skip及之后所有同步/传输逐字不变。[执行计划](../../runs/main-clean-series-001/iter-036-producer-valid-first/executable-plan.md)在源码生成前冻结并写入docs/draft；另冻结一个16query输入用例补足“首值无效、后续有效”的覆盖，仍使用原reference和容差。

隔离完整TU attempt001原NVCC13.1双架构19.510632s/exit0；REG168/152，stack/local/spill0，原flags只改路径。12659个边界向量/75954个skip比较一致。静态指令总数仍2744/2808，不能据此判断实际分支路径是否节省；完整actual producer/nonproducer/等待和成本复核正在进行。主源码/包保持035，未正式构建036或运行GPU，正确性/各shape性能N/A。见[基本CPU检查](../../runs/main-clean-series-001/iter-036-producer-valid-first/cpu-basic-audit.json)。

036完整CPU审查已通过：双架构960个producer路径/父本覆盖首值有效、fallback gather和skip及k0/1/2、ring/phase变化；四次int4 load无条件位于见证分支之前。完整tile相对035净少46条issued instruction，fallback增加2条；startup每个producer warp每CTA首次少1条，query重入和同等待结果的retry条数不变。其他角色2132/2196站点、短query/CLC边界、UR15借用后恢复及实际ULOP3/PLOP3形式均已核对；opcode依据显式PTX同工具链探针和实际PTX/SASS数据流，未声称硬件真值测量。144项输入重新hash后冻结[root CPU资格](../../runs/main-clean-series-001/iter-036-producer-valid-first/root-cpu-qualification.json)，现已应用036 snapshot并启动原setup正式构建；035仍为当前已采用版本，GPU正确性/性能仍N/A。新建的main-clean-12保持干净，未用于优化。

036正式原setup构建exit0，DSO `23fb5df9a4451a3ce4f65cb1a887c8c856d8d88bc04905bd76e8b443338f9b37`。实际完整SASS/control、text/nv.info/全部constant与隔离CPU一致，REG168/152，stack/local/spill0，原34/34 exemptions；root和[独立正式审查](../../runs/main-clean-series-001/iter-036-producer-valid-first/independent-formal/report.md)通过。144项资格输入按140冻结项+4项明确035→036主工作区转换核对。原316已通过原kda_run启动，tail6和额外16query随后串行运行；当前不作GPU正确性或性能结论。

036原316通过（314numeric+2run-only，158head64），64条监控23before/40running/1after；tail6通过（9条3/5/1）；新增16query单case通过（9条3/5/1）。三次原wrapper均exit0/valid，无运行期foreign观测，root及独审核对原参数、seed、包、实际输入和检查器结果。额外用例全部524288个Q与266752个KV BF16值及5120索引独立解码一致；输入推导Wfalse320/TMA208/skip112/末值valid fallback16，不当成硬件branchcounter。root witness首版审计仅selected_run元数据因变量遮蔽写成kv，原报告/脚本保留，v2重新读取同一GPU原始证据纠正为witness-correctness-001；没有重跑GPU或改测试。84项启动证据冻结后开始comparison001，按原6A5B共330样本对035；性能尚N/A。

### 036：有效comparison001与采用

原UUID、原6A5B共11轮330样本全部有效，65条监控为3before/61running/1after，无foreign观测。根复算原时间区间及独立复算均通过。逐负载（±为轮间SD）：

|skv|035 µs ±SD|036 µs ±SD|配对加速vs035|耗时减少vs035|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|356.050867 ±0.085305|351.638740 ±0.118752|1.258047%|1.242416%|14.042184%|977.131768|43.428079%|
|8192|356.787550 ±0.114088|352.308680 ±0.045553|1.271734%|1.255764%|13.832835%|975.273682|43.345497%|
|32768|362.591633 ±0.094361|358.899600 ±0.240922|1.028585%|1.018113%|12.435394%|957.363518|42.549490%|

汇总相对035加速1.186060%、耗时减少1.172158%；相对初始直接加速13.434556%、耗时减少11.843442%。五个pair汇总均为1.164977%至1.208807%，全部15个shape-pair为0.952622%至1.320035%，均严格超过0.5%；三shape最大相邻A漂移0.062066%/0.063081%/0.046874%，无形状回退，采用036。保留全部数据，无追加择优测量。当前三组耗时仍高于339.355441µs，全部45%目标未达，优化继续。

独立比较审计v2首次仅因仓外工具绝对路径pin的relative_to调用失败，未把该审计失败当成GPU失败或择优重测依据；新增v3只修复路径处理并另存audit002，重读同一有效comparison001后通过。原错误脚本、log和audit001保留。

证据：[根复算](../../runs/main-clean-series-001/iter-036-producer-valid-first/comparison-001-root-revalidation.json)、[330原始区间](../../runs/main-clean-series-001/iter-036-producer-valid-first/comparison-001-raw-interval-audit.json)、[独立复算](../../runs/main-clean-series-001/iter-036-producer-valid-first/independent-runtime/comparison-001-audit002/REPORT.md)、[采用决定](../../runs/main-clean-series-001/iter-036-producer-valid-first/decision.json)。新建main-clean-12仍干净；下一候选以已采用036为唯一父本。


## 2026-11-05 15:31：036 当前剖析完成，037 隔离编译

036 原 skv8192 full/source 在固定UUID均正常完成、监控有效；root直接读取原始报告、SASS和冻结源码，独立核验46项输入/实际加载包。DRAM18.09%，tensor elapsed47.0011%只是NCU诊断指标；当前理论43.43%/43.35%/42.55%的目标差距不变。14个PM指标没有可用实例，明确不作尾部结论；解析器两次修正保留原失败/旧输出，GPU未重测。见[六维诊断](../../profile/head64-iter036-kv8192/REPORT.md)。

iter037 唯一父本036，计划已先冻结并写入draft。只在隔离snapshot中缓存consumer前一tile的slot/phase，保留原k>0等待位置和全部同步/数学；当前每个重复准备PC动态147456次，但可回收净成本尚待编译。原main源码/正式包仍为036。原NVCC13.1完整TU双架构CPU编译进行中，正确性/各负载均值及波动/相对父本和初始性能均N/A，尚未采用。[执行计划](../../runs/main-clean-series-001/iter-037-consumer-prev-sv-cache/executable-plan.md)、[源码差异](../../runs/main-clean-series-001/iter-037-consumer-prev-sv-cache/parent.patch)。

037 CPU attempt001已正常退出0（18.9404s），SM100a/SM103a为154/152 registers、零stack/local/spill；主源码及正式包仍036。root核对三处literal反向重建、原完整编译参数仅路径不同，并与独立源审一致。完整loop初计k0增加2条、k>0每轮减少4条；这一局部数尚未包含query边界，因此还不是CPU完整资格或性能收益。正式构建和GPU验证尚未开始；性能各栏仍N/A。


## 2026-11-05 15:47：iter037 完整成本未通过，CPU拒绝

父本036；缓存前一SV slot/phase的源级等价、两架构编译及基础资源通过（154/152 registers、零stack/local/spill）。完整路径计数发现SM100 epilogue新增108条LOP3并少47条MOV等，净增64条，抵消G10循环少34条及query前导少1条，故每consumer warp/query净**增加29条**；首query含persistent startup增加32条。SM103对应减少35/32条，不能代替固定B200的SM100门槛。按事前冻结的净成本下降条件拒绝；这不是实测性能回退。

未正式构建、未运行037数值正确性或benchmark；4096/8192/32768各耗时/波动/相对父本与初始加速均**N/A**。原036主源码及五个正式包文件逐字节保持，不需要恢复。剩余完整nonconsumer/epilogue值证明在足够拒绝证据成立后停止，不标记为通过。全部隔离源码/cubins/日志/审计器失败与修订保留。[决定](../../runs/main-clean-series-001/iter-037-consumer-prev-sv-cache/decision.json)、[完整成本](../../runs/main-clean-series-001/iter-037-consumer-prev-sv-cache/independent-consumer-cost/report.md)、[root复核及PC示例勘误](../../runs/main-clean-series-001/iter-037-consumer-prev-sv-cache/root-rejection-review.md)。

未来witness命令原本错指036硬绑定harness，已在单独附录中修正并通过037副本CPU audit；没有GPU运行失败，也未变更16query输入或checker。正式脚本仅准备，随拒绝候选归档。当前最佳仍036，原实测理论利用率43.428079%/43.345497%/42.549490%，三组均>45%的目标继续。


## 2026-11-05 15:53：iter038 无初值缓存，隔离 CPU 实验

唯一父本仍为036。037的query入口清零值从未被有效读取；本轮独立从036构造相同guarded previous-SV cache，但不提供初值，仍在原循环尾部写回。k0不读、k>0由上一轮必经赋值定义；全部同步和数学不动。若仅删除一条CS2R而保留037的epilogue开销，完整SM100成本仍增加，按计划CPU拒绝；没有预设编译器分配会改善。

计划已先写入draft并冻结，原NVCC13.1完整TU双架构编译开始。主源码/正式包维持036，正确性/三负载耗时及波动/相对父本和初始性能均N/A。[计划](../../runs/main-clean-series-001/iter-038-consumer-prev-sv-noinit/executable-plan.md)、[源码差异](../../runs/main-clean-series-001/iter-038-consumer-prev-sv-noinit/source-edit.diff)。


## 2026-11-05 16:00：iter038 成本未改善，CPU拒绝

原NVCC13.1双架构完整TU编译exit0（20.3301s），154/152 registers、零stack/local/spill。独立源级definite-assignment审查通过，但实际机器码没有少一条指令：每架构2808站点，与037相比仅13站点改变（6个前导重排、7个cache寄存器换名），其余2795站点文本及128bit编码完全相同，全部控制转移保持原PC/编码。编译器仍在d60生成单寄存器清零，SM100输出epilogue增加64条的成本完整保留。

相对唯一采用父本036，原G10每consumer warp/query仍**增加29条**，首query增加32条；SM103仍减少35/32条。037只是解释代码差异的拒绝产物，未作为性能父本。按冻结净成本门槛拒绝，不再扩展与拒绝无关的完整kernel证明。主目录三headers和五个正式包文件逐字节保持036。

正式构建、GPU数值正确性及benchmark未运行；三负载耗时/波动/相对父本和初始性能均**N/A**，不把CPU指令数称作实测性能回退。独立审计脚本的路径定位失败及修正版全部保留，候选没有重编择优。见[决定](../../runs/main-clean-series-001/iter-038-consumer-prev-sv-noinit/decision.json)、[机器码成本](../../runs/main-clean-series-001/iter-038-consumer-prev-sv-noinit/independent-codegen/REPORT.md)、[root复核](../../runs/main-clean-series-001/iter-038-consumer-prev-sv-noinit/root-rejection-review.md)。


## 2026-11-05T08:12:01.813004+00:00：iter039 producer 两half循环，隔离CPU实验

唯一父本036。两half由一个不展开的外层循环处理，每half仍静态展开4行×4列共16次gather；四次indices读取、见证/fallback、全部wait/skip及传输顺序和字节数保持。计划先冻结并写入draft，再从036构造隔离snapshot。主源码/正式包仍036。实际循环形态、完整producer净成本与双架构资源待CPU验证，不预记收益。正式构建、GPU正确性、三负载耗时/波动/相对父本与初始性能均N/A。[执行计划](../../runs/main-clean-series-001/iter-039-producer-half-loop/executable-plan.md)、[源码差异](../../runs/main-clean-series-001/iter-039-producer-half-loop/source-edit.diff)。


## 2026-11-05T08:25:57.187950+00:00：iter039 两half循环成本增加，CPU拒绝

原NVCC13.1完整TU双架构编译exit0（20.4779s），REG168/152、零stack/local/spill。源级32笔gather有序tuple/地址/字节等价及基础门槛通过；实际16条静态gather循环两次，无runtime row/column循环。成功gather区含出口383→396条，MOV.SPILL/R2UR.FILL动态各39→48（UR/GPR搬运，并非local spill）。前导准备少9、SV准备多1，完整Wtrue每tile仍多5条；G10每个elected producer warp/query 4652→4709（+57），首query含角色startup4660→4722（+62），两架构一致。fallback gather/skip每tile分别少3/16，不能满足主路径门槛。

按事前冻结条件拒绝；这是CPU指令成本结论，不是实测速度回退。root重hash55项并核420条路径记录的实际PC相邻关系/分支/count。充分拒绝后停止完整操作数和无关角色证明，未正式构建、未运行数值GPU或benchmark，三负载耗时/波动/相对父本036与初始加速均**N/A**。主三headers和五包逐字节保持036。见[决定](../../runs/main-clean-series-001/iter-039-producer-half-loop/decision.json)、[完整成本](../../runs/main-clean-series-001/iter-039-producer-half-loop/independent-codegen/REPORT.md)、[root复核](../../runs/main-clean-series-001/iter-039-producer-half-loop/root-rejection-review.md)。


## 2026-11-05T08:31:24.768121+00:00：iter040 仅第二half静态行倒序

唯一父本036，第一half行0123保持，第二half改为3210，每行列序/32笔gather集合/原同步/数学保持；没有039的runtime half循环。当前036 first-half wait约68%首次未完成，second-half首次未完成为0，因此保留第一half第16笔完成。已存在的row3边界UR包提供局部复用假设，但总索引存活量不下降，不承诺编译器少搬运。计划已先冻结和追加draft，隔离CPU编译启动，主源码/包仍036。

本轮事前明确：指令计数用于诊断与风险解释，不当成耗时门槛；实际语义、资源和机器码变化通过后，按原完整正确性与交错benchmark判定。尚无性能结果，三负载耗时/波动/相对父本及初始加速均N/A。[计划](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/executable-plan.md)、[源码差异](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/source-edit.diff)。

040 CPU资格通过：双架构实际32传输按允许置换对应、所有等待/skip与startup/query状态核对；168/152 registers、零stack/local/spill。诊断Wtrue每tile+5，half0第16笔前+6，G10每query+50/首+51，UR/GPR保存恢复各39→46；未从这些计数推出速度。按事前040计划仍进入原实测。root审核并冻结105项输入后启动原setup正式构建，036继续作为已采用父本，040仅为实验源码。原GPU正确性/性能尚N/A。

040正式构建exit0，DSO `74dad7fb13b2d6c6bd18957b0c2f5aa60369cd0eec5b9ea498efdb92c8b5cb3f`。原34/34 exemptions、双arch代码/control/text/nv.info/constants及资源与隔离产物一致，root重新核142项身份后关闭正式资格。原316已exit0/valid通过（314numeric+2run-only，158head64，47条监控11before/35running/1after）；tail6也exit0/valid通过（9条4/4/1）。固定UUID在验证前有其他进程时原wrapper等待连续三次空闲，运行期无foreign观测。focused16query正在运行，性能仍N/A。独立runtime首次审计因rootformal改用input_sha256映射而缺少旧的顶层摘要字段退出，原脚本/失败日志保留；正在最小兼容修订后重读同一GPU证据，未重跑GPU。

040 witness001：child exit0、数值通过，但8条监控中的运行期观测到foreign compute process，wrapper exit2/valid=false/contaminated=true。本attempt无效，不作为正确性采用证据；原始日志和实际输入保留。同UUID按原16query参数及checker重试witness002，原316/tail的有效结果不重跑。见[无效记录](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/witness-001-invalid.json)。

040 witness002在同UUID原参数重测exit0/valid，9条监控3before/5running/1after，无foreign观测。root和独审复核完整Q/KV bits与5120indices、原reference/checker通过；输入推导Wfalse320/TMA208/skip112/later-valid16，不当作硬件branchcounter。独审v2仅改formal pin读取及新结果路径，对同一原316/tail/有效witness002均通过；root逐字反向核入口改动并重hash输入。100项比较启动证据冻结后，开始原6A5B共330样本的comparison001，以采用036为A、040为B，性能仍待终态。


## 2026-11-05T09:07:27.302464+00:00：iter040 正确性通过，原比较未达门槛，拒绝

固定UUID原6A5B共330样本有效，68条监控5before/62running/1after，无foreign观测；root与独立复算逐时间区间、原参数/seed、包及环境一致。三组形状均值配对结果均为负，五个汇总pair为−0.150234%至−0.048752%。轮间SD如下：

|skv|036 A µs ±SD|040 B µs ±SD|配对加速vs036|耗时降低vs036|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|351.449883 ±0.038922|351.695780 ±0.146634|-0.070609%|-0.070658%|14.023688%|976.973291|43.421035%|
|8192|351.999550 ±0.118286|352.183420 ±0.101951|-0.046468%|-0.046489%|13.873322%|975.620555|43.360914%|
|32768|358.414250 ±0.188029|358.947080 ±0.107657|-0.145943%|-0.146157%|12.420522%|957.236882|42.543861%|

汇总相对036加速−0.087682%，耗时增加0.087759%；直接对初始加速13.436867%、耗时减少11.845238%，这是完整候选对初始的比较，不能当成本轮收益。各shape最大相邻A漂移0.026402%/0.077744%/0.112255%；没有超过0.5%的可复现提升，不追加择优测量。拒绝040，三headers和五个正式包文件逐字节恢复036。已验证最佳和报告开头保留收益不变，全部>45%目标仍未完成。

原316（314numeric+2run-only）、tail6、有效witness002均通过root与独审；污染witness001和首次独审schema失败保留。040本轮没有已验证局部正收益可加入开头汇总，微小波动不称为收益。

证据：[root复算](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/comparison-001-root-revalidation.json)、[独立复算](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/independent-runtime/comparison-001-audit002/REPORT.md)、[330原始区间](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/comparison-001-raw-interval-audit.json)、[决定](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/decision.json)、[恢复036](../../runs/main-clean-series-001/iter-040-producer-half1-reverse-rows/restoration-036.json)。


## 2026-11-05T09:12:28.397215+00:00：iter041 producer uniform int4读取，隔离CPU实验

唯一父本036。只把原四次indices __ldg向量读取改为head64局部ldu.global.v4.s32 inline asm，原地址/顺序/四输出、见证/fallback、全部gather与wait保留。warp索引及query/CLC状态来源提供uniform地址证明，沿用原16B/只读前提；官方PTX不保证直接UR，实际33条来回搬运能否改变尚未知。计划先冻结和追加draft后才生成snapshot，原NVCC13.1完整TU双架构CPU编译已启动。主三headers/五包保持036；正式构建、GPU数值正确性、三负载耗时/波动/父本和初始加速均N/A。[计划](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/executable-plan.md)、[研究](../../profile/head64-iter036-kv8192/analysis/post040-ldu-research-001.md)、[源差异](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/source-edit.diff)。

041完整TU编译exit0（19.949779s），双arch2744/2808sites、REG168/152、零stack/local/spill。完整新反汇编和ELF证明每arch只有四个load去.CONSTANT，text恰四字节各变一个bit，其余2740/2804指令及全部控制编码、nv.info/constants等相同；原16R2UR+17回搬完全保留。按同分支/等待结果继承036实际路径，G10 steady4652/first4660、half0见证367均不变，不能预测实际重试数或速度。root基础审计首次把全部UTMALDG（40，含8个Q加载）误算为32 gather，修正为精确GATHER4统计并保留失败；runtime inverse首检遗漏一条候选标签注释，读diff后纠正，无测试/源码更改。122项输入冻结后关闭[root CPU资格](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/root-cpu-qualification.json)，现已应用041源码并开始原setup正式构建；036仍为已采用最佳，原GPU正确性/性能尚N/A。

041正式构建exit0，DSO `b553cfcb8b288f4ffc4cbd53b8d5c5c30b8995d4f055cff650f0f530c5592558`，原34/34 exemptions。root及独立fresh提取确认双架构完整代码/control/nv.info/constants与隔离产物一致；122项CPU资格按118 immutable+4明确036→041转换核验。root正式资格再核136项，runtime43项冻结，独立工具已在启动前采用相同map schema。原316现已在原UUID经kda_run开始空闲检查，GPU正确性和性能尚未给通过结论。

041原316通过（314numeric+2run-only、158head64，41条监控3before/37running/1after）及tail6通过（10条3/6/1），均exit0/valid且root与独审通过。witness001数值child exit0，但运行期发现foreign，wrapperexit2/invalid；不作为采用证据，保留完整输入/监控并同UUID原参数重试002。见[污染记录](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/witness-001-invalid.json)。

041 witness002已exit0/valid，13条监控7before/5running/1after，无运行期foreign观测，root与独审解码完整Q/KV及5120索引并核原checker通过。90项原协议启动证据冻结后开始comparison001：A036/B041，原6A5B330样本；所有有效/污染历史保留，不从计数或单样本给采用结论。

041 comparison001完成原11轮330样本，但运行期观测到foreign，wrapperexit2/childexit0/valid=false。整次无效，三shape和汇总性能均N/A，不能作采用或拒绝依据；完整原始结果保留。重新核验全部启动pins后，在同UUID以同样036/041包和原5对协议完整重试comparison002，不选择性保留某些轮次。见[污染证据](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/comparison-001-invalid.json)。

041 comparison002同样完成11轮，但85条监控中3个running样本出现非本任务PID3719649（两次）及3723093；wrapperexit2/childexit0/valid=false。root及独审确认整次无效，不计算采用收益，三shape及汇总性能N/A。完整数据和[污染证据](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/comparison-002-invalid.json)保留；已重hash前次92项启动输入，以同UUID、相同包和原5对协议准备comparison003。该重试只由污染触发，不按测量数值选择。


## 2026-11-05T09:50:47.028841+00:00：iter041 原比较无可复现收益，拒绝并恢复036

comparison003完整11轮330样本有效；66条监控3before/62running/1after，运行期无foreign观测。root与独审重算原参数、包身份、330个原始区间及相邻A几何插值一致。comparison001/002污染整组排除且保留；不择优取轮次。轮间SD如下：

|skv|036 A µs ±SD|041 B µs ±SD|配对加速vs036|耗时降低vs036|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|351.640100 ±0.116998|351.752560 ±0.091839|-0.028451%|-0.028459%|14.005283%|976.815588|43.414026%|
|8192|352.438850 ±0.060213|352.406740 ±0.053916|0.008561%|0.008560%|13.801161%|975.002305|43.333436%|
|32768|358.686333 ±0.123753|358.863140 ±0.066598|-0.042702%|-0.042720%|12.446817%|957.460785|42.553813%|

汇总相对036加速−0.020866%、耗时增加0.020871%；直接对初始加速13.415639%、耗时降低11.828738%，后者不能当成本轮收益。五个汇总pair范围−0.055427%至+0.015026%，各shape最大相邻A漂移0.050939%/0.027190%/0.068739%。8192的+0.008561%落在控制漂移内且pair正负混合，不属于已验证局部收益。未达到严格>0.5%的采用条件，不追加择优测量。

原316、tail6和有效focused16query均通过root及独审；污染witness001、comparison001/002及已记录工具审计修订保留。root关闭审计后重hash129项证据，再逐字节恢复036三headers和五包。报告开头保留收益不变，三形状>45%的完整目标仍未达到。

证据：[root复算](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/comparison-003-root-revalidation.json)、[独立复算](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/independent-runtime/comparison-003-audit001/REPORT.md)、[330原始区间](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/comparison-003-raw-interval-audit.json)、[决定](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/decision.json)、[恢复036](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/restoration-036.json)。


## 2026-11-05T10:02:17.343107+00:00：iter042 六路producer计划冻结

唯一父本036，启用原空闲warp10/11，线程384/shared222480保持；16个int4 pack按w+6*r分配，四warp三pack、两warp两pack，330workers/6acks，每half仍32768B。预期缩短最长producer发射序列，全部CTA总传输不减，额外guard/协议与调度竞争可能抵消。计划先冻结并追加draft，主三headers/五包仍036；尚未实现或编译。新增skip分组正确性、60query覆盖和nonfinite差分诊断是后续资格义务，未缩窄API。三负载性能均N/A。见[计划](../../runs/main-clean-series-001/iter-042-six-producer-warps/executable-plan.md)、[研究](../../runs/main-clean-series-001/iter-041-producer-uniform-index-load/post041-next-directions-001.md)。

042隔离源码已按冻结8处literal生成，反向重建等于036，三处guard覆盖第三row全部读取/归约/gather；主三headers/五包仍036。root逐项读diff并核builder仅source_scope标签变化，现启动原NVCC13.1完整TU双架构CPU编译，尚无资源/正确性或性能通过结论。

042原完整TU CPU编译exit0（20.686005s），sm100/sm103分别2624/2688指令位点、24静态gather、REG168/152、零stack/local/spill，3个既有CALL，无新增LDL/STL/SETMAX。这些基础资源符合门槛，实际6路角色/guard/事务与完整成本仍待独立审查和root资格；未正式构建、未运行GPU。主三headers/五包继续保持036，性能N/A。

042独立源审查按独立7处phase+1处config允许清单重建整文件通过；CPU模型核128tuple、64种skip组合、330参与者/6ack、16896种符号组合与401408个valid分量插入、2040组G2/3/5/10及初始ring余数。模型不是真实线程交错或GPU证书。root基础审计原编译argv/资源/主036身份通过。原16query与新增60query harness已CPU --audit通过，分别拒绝6/7种刻意输入损坏；新case输入推导Wfalse1800/TMA1116/skip684/later-valid24，不是实测branchcounter。独立harness审查、完整实际代码资格、正式包、非finite诊断及全部GPU检查仍未关闭。

042四项独立CPU范围已封存：源/整数模型、producer实际guard/传输与persistent状态、issuer完整参数流、其余角色与尾部。root已读全部当前审计脚本、源diff和报告并重核主三headers/五包仍036。两arch各3744 producer核心路径、132 lengths前导、162连续tile；issuer每版本36多query及7种冷等待；尾部224对照，consumer684个关键FP/TMEM/内存/同步位点全128bit相同。6ack/330CLC与实际初始化匹配。原G10成功等待的producer合计减少390/378条、issuer每query减少42条，这些仅是指令成本诊断，不能代替耗时。

审计器历史修订全部保留：producer001–005为UISETP.EX/ULEA/phase/103寄存器适配；route001为过强PC形式；other-role001–003为重复字段与同谓词guard关联；boundaries001为mask同P0链；issuer001为LEA.HI顺序、002为HFMA2低半字负零应为0x8000事务字节。均未改候选或重编，采用最终producer006/route002/other004/boundaries002/issuer003证据，issuer旧002结果明确superseded。

原16query及新增60query独立输入/AST审查通过，原reference/checker/容差和num_runs=0保持；原16的四producer覆盖元数据不当作042六producer动态计数。非finite48case计划已冻结，harness正在实现并将独审；尚未GPU执行。当前正在汇总root CPU资格及准备原setup正式构建，性能N/A。证据：[producer](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-codegen/REPORT.md)、[issuer](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-issuer/REPORT.md)、[其他角色](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-other-roles/REPORT.md)、[有限harness独审](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-source/test-harness-review.md)。

042 root CPU资格已关闭：137项输入重hash，root fresh解码双arch文本和128bit与归档一致，684个consumer关键位点再次逐字核对。root资格仅允许原setup正式构建，不代表数值或性能通过。两formal工具由041适配，仅042标签/资源schema/330与6 metadata/新增独审和focus依赖变化，原flags与checks保留。正式构建session79891已启动，尚未GPU。见[root CPU资格](../../runs/main-clean-series-001/iter-042-six-producer-warps/root-cpu-qualification.json)。

042正式构建exit0（原setup，26s内），DSO `e7a9f16618bf50da56b26beb0fdf229116f0a96d6ae39b589685d75126d1610b`。root与独审fresh提取的双架构全部代码/control/.nv.info/constants与隔离产物相同，REG168/152、0 stack/local/spill，原34/34 exemptions；整cubin差异仅debug/internal symbol ID。137项CPU pins按133immutable+4明确036→042转换关闭，root正式资格再核165项，运行输入46项和启动63项冻结。原316已经原kda_run在固定UUID启动；原tail6/witness16/focus60与nonfinite48差分尚待执行，性能N/A。见[正式资格](../../runs/main-clean-series-001/iter-042-six-producer-warps/root-formal-qualification.json)、[独立正式审计](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-formal/FINAL.md)。

042原316/tail6/原witness16/新focus60均exit0且监控有效，root与独审全部通过。原316保留314numeric+2run-only、158head64，44条监控(3before/40running/1after)；tail/witness各10条(3/6/1)，focus9条(3/5/1)，均无foreign观测。focus完整1966080 Q与266752 KV BF16值、19200 indices独立重构；六组输入推导计数1800 Wfalse/1116 gather/684skip/24 later-valid只作配方覆盖。原reference/checker/容差不变。

非finite48case五源已冻结，纯stdlib --list/--audit退出0，18种输入/分类/metadata/blob损坏拒绝。源生成前的错误路径读取与一次空patch被工具拒绝已如实记录，没有失败的CPU验证轮、没有GPU诊断数据。当前仍须独审与root启动资格，之后分别运行036/042完整48case并核全输入及全部输出分类/有限值；不能跳过后直接benchmark。性能仍N/A。见[非finite实现说明](../../runs/main-clean-series-001/iter-042-six-producer-warps/nonfinite-tests/IMPLEMENTATION.md)、[focus独审](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-runtime/focus-001-audit001.json)。

042非finite harness独审通过并冻结：52项输入/双正式包、48配方完整Q/KV/163840indices和每case25600 skip决策独立重算；BF16全部65536分类及512对BF16/FP32比较边界通过。root读五源与独审后重核211项启动证据，固定UUID分别完成parent036/candidate042独立进程各48case，均exit0/valid，各15条监控(3/11/1)，无foreign观测。原冻结比较器完整读取全部输入/输出blob，48case均逐位相同：out累计805306368元素、max与LSE各1572864元素，无NaN payload或signedzero豁免实际使用。奇数全无效query均独立满足out0/max−Inf/lse+Inf。root比较exit0，独立运行差分审查尚在收尾；未据此声称任意nonfinite输入或sameCTA poison→clean调度已证明。性能尚N/A。[根完整差分](../../runs/main-clean-series-001/iter-042-six-producer-warps/nonfinite-differential-001.json)。

042非finite独立NumPy全量审核通过：48组、96次调用、808452096个对应输出位置；全输入、分类、有限值及奇数all-invalid断言与root一致，NaN payload/±0豁免均未使用。独审首次CPU自测括号语法错误已保留，修正后selftest002通过；没有GPU失败或诊断重跑。root读完整独审源码/分类报告并重hash全部输入后，冻结739项comparison001启动证据。首次准备脚本误用common_subroutine.h目录，写入前失败，纠正既有路径后通过；未改候选。按原036/042、固定UUID、5对交错6A5B共330样本进入性能比较，性能尚N/A。见[独立差分](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-runtime/nonfinite-parent001-candidate001-audit001.md)、[比较启动](../../runs/main-clean-series-001/iter-042-six-producer-warps/comparison-001-prelaunch.json)。


## 2026-11-05T11:08:45.065308+00:00：iter042 六producer原比较负收益，拒绝并恢复036

原comparison001完整11轮330样本有效，66条监控(3before/62running/1after)，无foreign观测。root与独审分别重算原参数、包身份、330原始区间和相邻A几何插值一致。五个汇总pair全负；15个shape-pair范围−0.316965%至−0.064288%。轮间SD如下：

|skv|036 A µs ±SD|042 B µs ±SD|配对加速vs036|耗时降低vs036|加速vs初始|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|351.519583 ±0.107187|352.356340 ±0.097371|-0.230900%|-0.231434%|13.809929%|975.141766|43.339634%|
|8192|352.195833 ±0.087486|353.168900 ±0.133670|-0.277873%|-0.278647%|13.555571%|972.898190|43.239920%|
|32768|358.634883 ±0.147643|359.252620 ±0.221992|-0.168473%|-0.168757%|12.324909%|956.422764|42.507678%|

汇总相对036加速−0.225759%、耗时增加0.226269%；直接对初始加速13.228275%、耗时降低11.682837%，不能当作本轮收益。各shape最大相邻A漂移0.061915%/0.063420%/0.103355%。没有已验证局部正收益；未达到严格>0.5%，不追加择优测量。六路producer虽缩短最长发射序列、减少模型指令，原性能结果未受益；不能从计数推断关键路径时间。

原316、tail6、witness16、focus60与非finite48完整差分均通过root/独审。拒绝042，root关闭全部比较证据后恢复036三headers/五包并核逐字节一致。报告开头已采用收益不变，全部>45%的目标仍未完成。下一方向仅为条件rowmax通信研究，尚未实现。

证据：[root复算](../../runs/main-clean-series-001/iter-042-six-producer-warps/comparison-001-root-revalidation.json)、[独立复算](../../runs/main-clean-series-001/iter-042-six-producer-warps/independent-runtime/comparison-001-audit001/REPORT.md)、[330原始区间](../../runs/main-clean-series-001/iter-042-six-producer-warps/comparison-001-raw-interval-audit.json)、[决定](../../runs/main-clean-series-001/iter-042-six-producer-warps/decision.json)、[恢复036](../../runs/main-clean-series-001/iter-042-six-producer-warps/restoration-036.json)。


## 2026-11-05T11:13:32.719350+00:00：iter043 条件rowmax交换计划冻结

唯一父本036。每tile先做pair64 OR，只有需要缩放的pair交换当前rowmax；real_mi本地累计，query末保留最后slow读退休屏障并复用li128发布后合并。原entry64、全部异步同步、math/checker/参数不变。与001单纯pair64不同；新增reduction/控制/末尾成本可能抵消，计数只作诊断，实际语义/资源通过后按原测试/benchmark决定。计划已先冻结并完整追加draft，主三headers/五包仍036，尚未实现或编译。三负载耗时/波动/父本及初始加速均N/A。见[计划](../../runs/main-clean-series-001/iter-043-conditional-rowmax/executable-plan.md)。

043按冻结4处literal生成隔离source，逆重建逐字等于036；phase SHA23361a1e4cc68ca3c22285ac017db613dc2d478ced1ec2093d848739fd4773dd。root读全部diff后原完整TU双架构CPU构建exit0（17.034247秒），两archREG168/零stack/local/spill。SM103原036为152，现168仍在事前上限内，不冒称资源完全不变。root fresh dump核原argv与两cubin归档一致，实际有一处BAR.RED.OR，仍32gather/3既有CALL，无LDL/STL/SETMAX。首次basic001错误要求4D.GATHER4，原/新实际均2D.GATHER4；保留失败输出，修正审计器后002通过，未改候选或重编。主三headers/五包仍036，源数学/同步/完整机器码审查及额外诊断计划仍待关闭；尚无正式包/GPU数值或性能。见[基础审计](../../runs/main-clean-series-001/iter-043-conditional-rowmax/root-basic-audit-002.json)。

043源级独审通过：四块允许改动独立全文重建/逆变换；精确binary32 RN+FTZ模型核16038阈值组合、19683最大值归约、51200 mi更新；668个四warp生命周期模型/27396读写顺序检查，删末保护、错误条件BAR128、提前local清零均被识别。root已读完整脚本/报告并重核源pins；这只关闭源模型范围，不是实际机器码/线程交错或GPU正确性证明。原16query witness只改三处身份文字，CPU --list/--audit exit0且原6mutation拒绝；新diagnostic配方仍在准备。完整代码/正式包/原验证/性能均未关闭。见[源审查](../../runs/main-clean-series-001/iter-043-conditional-rowmax/independent-source/REPORT.md)。

043补充诊断方案已在实现前冻结：4个finite API配方含64个query模式，24个Q/KV NaN/±Inf差分配方。显式校准scale使内核log2-scale为1，覆盖阈值6上下邻居和等号、两pair不同决策、末tile slow、局部全NaN而peer有限；原316/tail6/witness16不变。root读完原16witness独审脚本并复核全部pins，关闭其CPU保留范围；28配方harness与正式/GPU资格仍待完成。见[冻结诊断计划](../../runs/main-clean-series-001/iter-043-conditional-rowmax/diagnostic-plan.md)。

043完整CPU资格已由root关闭，144项pins一致，见[root资格](../../runs/main-clean-series-001/iter-043-conditional-rowmax/root-cpu-qualification.json)。实际masked-P/softmax272、输出5120及完整成本480实例通过；非consumer1425站点对036100映射、双arch1578站点全128-bit相同，并关闭allocator重排的跨role终态边界。G10/k0-only在SM100每query输出warp增加29 issue sites，只作诊断，不据此拒绝；SM103 REG152→168在上限内。consumer审计器math/output/boundary的首版失败均保留并修正，候选未改。已应用043并启动原setup正式构建，session93308；原GPU数值与性能仍N/A。

043原setup正式构建exit0（26.46秒），正式DSO `62d6eee99cb13d4bd3e8d56f738930100d9fb83e7c650a4e10d7a8615721aa56`。root/独审fresh双arch2792站点的完整code/control/.text/.nv.info/constants与CPU相同，168/168、zero stack/local/spill、原34/34 exemptions通过；140 immutable CPU pins及4显式历史转换核验，root正式资格绑定181项。独审完成后的终态摘要命令一次括号笔误单独保留，只修元数据、未重跑审计。原316/tail6/witness16的运行清单和独立工具已冻结并通过只读preflight；新28配方CPU初版通过，补充poison位置负例后待最终独审，尚无GPU或性能结论。

043原316 attempt001原checker全部返回通过、childexit0，但原监控在运行期观测foreign进程183847（build/address_walks，14MiB），wrapperexit2/valid=false/contaminated。此attempt不作为正确性采用证据；完整原始log/telemetry和[无效记录](../../runs/main-clean-series-001/iter-043-conditional-rowmax/correctness-001-invalid.json)保留。同UUID以完全原参数重跑002，不终止他人进程或换卡。

043原316 retry002有效通过，root与独审均核原316全参数/seed顺序、314numeric+2run-only、158head64，131条监测（82before/48running/1after）；等待期外部任务已在启动前结束，末3条idle成立，运行期无foreign观测。tail001六项也有效通过（24条监测17/6/1），正式DSO进程内绑定核对；witness001正在执行。补充28case的9模块源码与29项负例、独立全输入/边界模型以及父036/候选043正式包绑定均已关闭，root重核88项启动证据，实际GPU诊断和性能尚N/A。见[root诊断启动资格](../../runs/main-clean-series-001/iter-043-conditional-rowmax/root-diagnostic-prelaunch-001.json)、[原316独审](../../runs/main-clean-series-001/iter-043-conditional-rowmax/independent-runtime/original-002-audit001.json)。

043 witness001原checker通过/childexit0，但两条运行期遥测观测foreign PID244557，wrapperexit2/valid=false，完整结果排除且保留。已按原16query配方与同UUID启动retry002，不改变case或候选。tail001独审也已通过，root复核原316/tail全部独审pins一致。

043 witness retry002有效通过（9条遥测3/5/1），root及独审逐值核5120 indices、524288 Q与266752 KV BF16逻辑值及正式包，原checker返回true。原316002、tail001、witness002运行资格均关闭；诊断parent036完整28case已按冻结命令启动，候选043待顺序运行。

043诊断parent036完整28case完成且有效（63条监测30/32/1），原有限配方4次reference/12次checker通过；root已核metadata/调用身份/原始遥测，完整输入与输出差分仍待候选完成。candidate043也已在同UUID启动。独立实际结果审计器与独立配方oracle已完成CPU selftest并由root逐行审读；没有提前写GPU通过结论。另有只读[静态barrier count研究](../../runs/main-clean-series-001/iter-043-conditional-rowmax/research-static-barrier/REPORT.md)，仅为043收尾后的候选假设，未改源码或编译。

043父036与候选各28诊断配方已有效完成；root冻结比较器exit0，全量读取所有实际逻辑输入、三阶段完整backing与三输出，通过28组差分。out对应404750336元素、max和LSE各790528，全部逐位相同，NaN payload/零符号豁免均未使用；原all-invalid约束亦通过。独立实际结果审核仍在执行，尚未进入性能比较。见[完整差分](../../runs/main-clean-series-001/iter-043-conditional-rowmax/diagnostic-differential-001.json)。

043诊断独审exit0（session35031），56份完整档案和28对共406331392输出位置全部逐位相同；root逐项对齐84项输出汇总、重核350项独审pins后关闭运行资格。父/候选监测分别63条(30/32/1)、67条(34/32/1)，运行期均无foreign观测。随后冻结全部comparison001启动证据并在同UUID启动原5pair/6A5B/330sample比较；性能尚N/A。只读摘要显示脚本曾把summary的整数cases当列表而报错，已纠正显示，不涉及测试/审计重跑或数据修改。见[独立诊断](../../runs/main-clean-series-001/iter-043-conditional-rowmax/independent-runtime/diagnostic-parent001-candidate001-audit001.json)、[比较启动证据](../../runs/main-clean-series-001/iter-043-conditional-rowmax/comparison-001-prelaunch.json)。


## 2026-11-05T12:29:03.716968+00:00：iter043 首次原比较有效，进入边界确认

comparison001完整11轮330样本有效，88条遥测(22before/65running/1after)，无运行期foreign观测。root与独审原参数、包身份、区间和统计一致。

|skv|036 A µs ±SD|043 B µs ±SD|配对加速vs036|耗时降低vs036|加速vs初始|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|
|4096|351.852233 ±0.101268|350.083280 ±0.065774|0.500696%|0.498201%|14.548887%|43.621034%|
|8192|352.569967 ±0.064433|350.953780 ±0.375543|0.458489%|0.456397%|14.272301%|43.512838%|
|32768|358.909617 ±0.212724|356.502120 ±0.102145|0.669527%|0.665074%|13.191523%|42.835635%|

汇总加速+0.542862725%、耗时降低0.539931638%，直接相对初始加速14.002729615%。全部15对正收益，但范围0.261744%–0.699442%，且一组aggregate pair为0.478721%。结果接近门槛，尚不采用。依据原计划边界确认规则，在第二次数据产生前冻结[确认计划](../../runs/main-clean-series-001/iter-043-conditional-rowmax/confirmation-plan.md)：只追加一次完整有效比较，两批各自汇总均严格>0.5%才可采用，所有30shape-pair和660样本共同汇总；第二批若未达阈值则拒绝，不追加第三批有效测量择优。污染整批保留排除后可同协议新编号重试。当前已启动comparison002，源码/包与原协议不变，036仍为采用版本。


## 2026-11-05T12:39:39.039860+00:00：iter043 两次完整确认通过，采用

comparison002有效11轮330样本，70条遥测(3/66/1)，无运行期foreign观测。root与独审两批及660原始区间、30对比率、12A/10B轮均值全部复算一致。002汇总+0.545162159%，001为+0.542862725%；严格满足事前两批各自>0.5%条件。

|skv|036 A µs ±SD|043 B µs ±SD|配对加速vs036|耗时降低vs036|直接初始加速|TFLOPS|TFLOPS/2250|
|---|---:|---:|---:|---:|---:|---:|---:|
|4096|351.847383 ±0.101626|350.107460 ±0.074956|0.492276%|0.489864%|14.540976%|981.405491|43.618022%|
|8192|352.576042 ±0.083135|350.872200 ±0.270487|0.486185%|0.483833%|14.298870%|979.266478|43.522955%|
|32768|358.901917 ±0.176397|356.562310 ±0.139246|0.653666%|0.649421%|13.172416%|963.639100|42.828404%|

合并加速+0.544012436%、耗时降低0.541068953%，直接相对初始加速14.002524096%、耗时降低12.282643921%。全部30pair正收益，范围0.261744%–0.724512%，没有形状回退。4096/8192 pooled shape本身约0.49%，未把它们描述为各自>0.5%；采用依据是原汇总门槛和两批可复现性。主三headers/五包逐字核043归档并保留。独立pooled v1仅因prelaunch路径键absolute/relative不匹配在统计前失败，v2修复该key及新输出目录后通过，失败全部保留。完整45%目标仍未完成。

证据：[采用决定](../../runs/main-clean-series-001/iter-043-conditional-rowmax/decision.json)、[root汇总](../../runs/main-clean-series-001/iter-043-conditional-rowmax/combined-valid-results.json)、[独立660样本汇总](../../runs/main-clean-series-001/iter-043-conditional-rowmax/independent-runtime/confirmation-audit002/REPORT.md)。


## 2026-11-05T12:41:56.335733+00:00：iter044 固定count的pair sync计划冻结

唯一父本已采用043。只在两个原unaligned同步位置用本地helper把恒定count64直接写入PTX，ID/参与者/位置/内存排序/synclog保留；其余源逐字不变。实际collective是否由寄存器count触发尚未证实，先用完整双架构TU验证；若全部可执行代码/数据/资源相同则CPU拒绝。计划已先追加draft，尚未生成源码或编译，主源码/包仍043，性能N/A。见[可执行计划](../../runs/main-clean-series-001/iter-044-static-pair-sync64/executable-plan.md)。

044最终隔离源仅本地helper与两调用替换，phase SHA865fd08d3647edb71c884428f06b0c100eb7f3e938464355f19aec4aac359004，逆变换逐字等于043。首版生成器在写snapshot前因12空格模式也是20空格调用的子串而被逆匹配断言拒绝，完整脚本/失败记录已保留；仅给匹配加换行锚定后通过，未改变冻结计划。原flags完整TU双架构CPU编译已启动，主三headers/五包仍043；无新GPU或性能结论。


## 2026-11-05T12:54:17.696464+00:00：iter044 完整机器码相同，CPU拒绝

原flags完整TU双架构编译exit0（session2201，15.578秒），SM100a/SM103a均168 registers、zero stack/local/spill。root与独审fresh实际产物核对：每架构2792条PC/文本/完整128位编码及44672字节native text全部等于采用父043；42个ELF段中的非debug代码、数据、常量、重定位及Mercury相关段也相同。差异仅8个debug段及严格生成internal-ID的.strtab。实际PTX的两条sync确已改为literal64，但collective lowering未变，固定count假设被此次编译证据否定。

依事前identity gate拒绝044，无正式构建或GPU数值/性能测量，各shape耗时/波动及相对初始/父本收益均N/A；不把相同机器码宣称为实测0%收益。主三headers/五package继续保留043，完整45%目标未达成。root关闭脚本exit0、重核81项证据，独审实际session76017 exit0。首轮生成器写入前失败记录仍保留。

证据：[拒绝决定](../../runs/main-clean-series-001/iter-044-static-pair-sync64/decision.json)、[root完整核验](../../runs/main-clean-series-001/iter-044-static-pair-sync64/root-cpu-qualification.json)、[独立actual code审计](../../runs/main-clean-series-001/iter-044-static-pair-sync64/independent-codegen/report.json)。


## 2026-11-05T13:00:21.528710+00:00：iter045 删除已被OR覆盖的entry pair同步计划冻结

唯一父本为采用043，044不继承。仅拟删consumer循环入口pair64，保留043每tile必经OR64、条件publish64、query尾部64和最终128；利用OR位于旧peer读之后、下一覆盖之前的同步关系。007恢复入口时尚无此OR，因此不是对旧同步需求的忽略；也不引入008的双槽寻址。root与独审正在封存包含异步lifetimes/mbarrier observer和跨query的有界证明，未生成候选或编译。准确方案与验证/采用协议已先追加draft；性能N/A、主043保持。见[045可执行计划](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/executable-plan.md)。

045两份源同步研究已封存并经root逐项审读，36项输入重核；唯一实际diff为entry64及旧注释替换，整phase逆变换逐字等043，phase `bf5bd93e64eb247c7010739315db81dcb21828a4101704842419679a0a082d72`。源生成exit0（chunk118b29），原flags完整双架构隔离CPU编译session55607已启动；主三headers/五包保持043，尚无045机器码或GPU资格。

045隔离完整TU CPU session55607实际exit0（16.889秒，terminal b36853）。双架构均168 registers、zero stack/local/spill，静态指令2792→2784：入口BAR与关联WARPSYNC各少1、末尾padding NOP少6，同时初始化一处predicate分支变为uniform形式。存在consumer寄存器重分配/少量调度变化，不能只凭数量判资格。root已读完整双arch文本差分、67项基本构建/资源/编码pins通过；独立实际单删源码审查49pins通过。完整受影响CFG/内存/异步边界与first/steady/cold路径核验继续，尚未正式apply或GPU验证。见[root基本检查](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/root-basic-audit-001.json)。


### 045 CPU资格与正式构建（2026-11-05）

独立完整source/native审查、root common/其他角色审查与480条成本路径已通过；最终root CPU资格 `7020dd2d…c007`，143 pins。源仅删除入口pair同步；两架构REG168、零stack/local/spill。实际删除2条同步与6条对齐NOP，完整consumer G10每query减少11条issued sites，不能据此推断实测收益。consumer审计器三次失败为PTX虚拟寄存器与SM103 PC断言错误，原失败版本/日志/diff保留；候选未变。

原setup正式构建session89205真实exit0（499921），DSO `13a6c6637a52bdcbdbb9bf4d475c2842f7a91af63d45ab3d88706cd7fb4f2893`。root actual审计72157/d25839与独立51065/51bfea均exit0：双架构完整机器码/control及全部非debug段匹配隔离045，34/34原exemptions不变。正式资格 `fdc64d13…702b`。主源码/包现为实验045，已采用最佳仍043；性能N/A，等待原316/tail6/witness16、双角色28诊断和原配对测量。新建clean12未改动。


### 045 全部正确性闭环，原配对性能运行中

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`：原316（33361/972210）、tail6（24452/3ed223）、witness16（16027/c248df）全部真实exit0且monitor valid；root与独立审查均通过，参数、seed和原检查器保持。28诊断父043（9030/66d3f5）与候选045（79826/a4826f）也有效结束；root差分65636/10415c及独审37614/cc492b均exit0。84个输出共406331392个对应元素全bitwiseequal，未使用NaN payload/zero sign豁免；原始完整输入及三个阶段backing均验证。详见 [045差分](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/diagnostic-differential-001.json) 和 [独审](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/independent-runtime/diagnostic-parent001-candidate001-audit001.json)。

性能reader准备首版因已存在common的一条注释变化而失败（58cab3/exit1），失败脚本/部分输出/日志保留；v2仅接受记录该注释、确认AST与原043相同，并复用已生成文件，66f32f/exit0。没有改变协议或测量。原5pairs/6A5B/330samples比较001已在469pins冻结后启动；收益/理论利用率仍N/A，不能据正确性采用。


### 045 决定：拒绝，完整恢复043（2026-11-05T13:56:19.679005+00:00 UTC）

删除入口pair同步的候选正确性通过，但原五对交错比较001不满足采用门槛。真实wrapper70493/176f73退出0、valid=true；GPU启动前等待外部任务结束，最后3个idle样本通过；17 before、60 running、1 after共78条记录，运行期间无foreign/unowned或telemetry错误。root复算dc9d9f、原始区间审查cea8af和独立30854/f6855d均真实exit0，完整11reports/330samples一致。

| s_kv | 父043 μs ±轮间SD | 045 μs ±轮间SD | 对父配对加速 | 对初始加速 / 耗时降低 | TFLOPS / 理论占比 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4096 | 350.105283 ± 0.149868 | 350.292220 ± 0.133817 | -0.054100% | 14.480561% / 12.648926% | 980.887853 / 43.595016% |
| 8192 | 350.679367 ± 0.129740 | 351.028040 ± 0.117095 | -0.101159% | 14.248127% / 12.471213% | 978.831730 / 43.503632% |
| 32768 | 356.512583 ± 0.161043 | 356.915340 ± 0.205639 | -0.112140% | 13.060475% / 11.551761% | 962.685951 / 42.786042% |

汇总对043加速 **-0.089136107%**，耗时降低 -0.089215630%（即耗时增加约0.089216%）；对初始直接加速 13.928019689%、耗时降低 12.225280249%，未叠加历史收益。15个shape-pair全部负值，无已验证局部收益。无需追加有效批次；拒绝045并逐字恢复043三headers和五包文件，保留全部045源码、DSO、测试和测量。

[采用门槛决定](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/decision.json)、[原始比较](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/comparison-001/summary.json)、[独立复算](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/independent-runtime/comparison-001-audit001/report.json)、[恢复证明](../../runs/main-clean-series-001/iter-045-remove-entry-pair-sync/restoration.json)。入口同步删除没有带来可采用收益；没有据此猜测硬件原因。当前最佳仍043，全部45%的目标未达到；下一步是采保留043的当前full/source证据。


### 043 当前版本 profile 首次采集污染，保留并重试（2026-11-06T01:32:30.562576+00:00）

原8192/seed311、043正式包、固定GPU的full采集真实结束：session25510/terminal518e9b，wrapper exit2、child exit0、valid=false。37条遥测中5 before/31 running/1 after；运行期发现不属于采集进程树的PID2970970（build/address_walks），整次排除，不能用其指标作瓶颈或收益结论。保留全部原始报告与日志；该目录不再启动source，新目录r2按同协议重采full/source。源码及最佳版本仍043，性能/理论利用率新增结果均N/A。见[失败报告](../../profile/head64-iter043-kv8192/REPORT.md)。


### 043 当前有效 full/source profile 完成（2026-11-06T01:45:19.056324+00:00）

首轮污染完整保留排除后，r2在相同UUID、原8192/seed311、043正式DSO完成串行full/source：session99181/b14b5f与46853/b29773均exit0、validtrue，遥测分别37(3/33/1)与15(3/11/1)。root与独立直接API/全部遥测/加载包核验通过。两份2791个inst域PC均匹配当前正式043 SASS（另1个padding地址未采到），不是旧036 PC平移。原parser两处WARPSYNC绝对地址归一失败已保留；精确opcode修正版和独审均通过。

六维结果：occupancy15.553%（理论18.75%，register/shared各限1CTA），eligible0.616729，SM active分布相对均值−2.525%/+2.126%；tensor active/elapsed47.400%，DRAM read/write peak10.345%/7.830%，L2 hit76.002%，local load/store0。显式shared actual=ideal5101000，不能把aggregate bank-conflict规则归因到rowmax。PM14指标全0实例，时间线不可用，不能声称无尾波。以上NCU百分比和362.112µs采集耗时都不是原TFLOPS/2250目标或采用计时。

source实际QK首次未就绪147573/163840 consumer warp-visits（约90.07%）；MMA KV0为27198/40960（66.40%）、KV1为0。OR仍每tile执行；条件rowmax publish/peer LDS仅16384/163840 visits（10%）。mask-ready在原QK后首次未就绪为0，但LDS后R2P有210 short-scoreboard samples。下一窄实验方向是把mask-ready和mask LDS提前到QK wait前，先核generation/死锁/实际调度；不删wait，不修改数学，不将samples换算为可回收微秒。尚未修改kernel或采新候选性能。

当前最佳仍043，三个原shape理论占比43.618022%/43.522955%/42.828404%，全部45%目标未达成；本次相对父本/初始新增性能收益均N/A。见[完整六维报告](../../profile/head64-iter043-kv8192-r2/REPORT.md)、[root原始证据核验](../../profile/head64-iter043-kv8192-r2/analysis/root-profile-evidence.json)、[独立采集核验](../../profile/head64-iter043-kv8192-r2/analysis/independent-capture-terminal-001.json)。


### 046 mask-ready/LDS前移计划及隔离构建（2026-11-06T01:49:15.643078+00:00）

依据043有效r2当前PC证据，唯一改动是将原mask-ready wait与原32bit shared mask load移到QK wait之前；保留mask-free、Pfree、所有数学与043同步/producer/MMA/CLC。root与独立研究确认同槽ready→read→free及跨query ring关系，没有发现新增等待环；收益未知，可能暴露mask等待或增加寄存器存活。计划先逐字追加draft再生成源，整phase逆变换等043。phase e60cc0335bf5f43453bc23e1aed29512e121ae6ce617aabf4ab259ce37de8b1b，源生成2009ae/exit0。原flags完整TU双arch隔离CPU session5673/start290733已启动，主源码及五包仍043；当前正确性/性能N/A。见[046计划](../../runs/main-clean-series-001/iter-046-mask-before-qk/executable-plan.md)。

046完整TU CPU真实结束（5673/cf7d33，exit0，19.863秒）：SM100a/SM103a均REG168、零stack/local/spill，2792静态sites保持。root逐位核完整128位SASS/control，每架构只23个sites变化，集中e80–fa0与a4e0–a570；其余2769sites完全相同。实际mask-acquire e80→LDS ec0→QK-acquire ed0→R2P f30→TMEM f40，未被compiler沉回原位置；冷QK路径保留R0。独立完整ELF/资格审查继续；没有正式apply或GPU验证，主043仍逐字一致。见[root实际窗口检查](../../runs/main-clean-series-001/iter-046-mask-before-qk/root-cpu-window-review.json)。


### 046：mask 提前读取，正式构建完成（2026-11-06）

以已采纳043为父版本，只把 consumer 的 mask-ready wait 与原 shared mask load 移至 QK-done wait 前；所有释放、entry/OR/tail/final同步、producer/MMA及config/common保持。依据有效043 kv8192 r2剖析：QK首次失败147573/163840，而原较晚mask首次失败0；该证据支持尝试重叠，不代表可回收时间或预计收益。

隔离双架构编译真实5673/cf7d33 exit0；root及独立完整native/ELF审查通过。每架构2792站点中仅23处编码变化，其余2769处128bit完全相同；实际mask LDS0xec0在QKwait0xed0前，QK冷路径保活R0。REG168、零stack/local/spill。独立ELF inventory明确保留Mercury464字节差异及未解码边界，不作全ELF等同声明。CPU资格7b6baf917a7df94b06965219c4a15b9de00fb3e61f739d5f85a99827f96a5d43。

原setup正式构建40235/e05341→f040fc exit0，DSO3f37b99d2e5648a08a586be84508835339fcb8290266c0c33ad92575731ec001。root实际包审查29397/79a0cb→6795b9 exit0：两架构全部native文本/编码/control及所有非debug sections（含Mercury）与隔离046一致；原34/34 CUTLASS exemption未改。独立正式包审查及新316/tail6/witness16/28双角色诊断、原交错330样本比较仍待完成；性能N/A，verified best仍043，尚未采纳046。


046运行验证进展：原316（40320/94b8a4）、tail6（26433/3536a3）、witness16（58224/84e2e5）均真实exit0且监控valid；分别52/10/9条遥测，无观测到foreign进程。root读原参数/314numeric+2runonly/158head64、进程内tail/witness DSO与完整witness输入；独审原316 7e932f、tail89c8fb、witness v3 c6c86b均exit0。witness原v2 auditor897d0f exit2只因CPU证据旧路径缺失，未读到GPU结果；失败保存，v3只改实际已冻结CPU输出路径及新输出编号，原门槛/同一GPU结果不变。

诊断工具按显式补充计划保留source001，修复候选独立审查终态的嵌套字段读取，所有formal/runtime旧记录不改。新source002、63594/942c25 CPU检查28case/90blob/29负例及独立ddfefe审查通过；数据/预测/负例与001完全相同。runtime绑定74e3fdf156f9566906b8aa7c839d77079fecc5f7d2049f1bf44389f5b5ea2ab1，prelaunch e5f13ded9d1424b2cce564ebcf246e2b4cb79c87f956e8cf17f07f62e98c4b1a。独立诊断reader另发现模型provenance旧路径缺失，正在用明确043历史模型路径/SHA准备独立v2；所有数值和完整backing/输出比较规则不变。尚未启动28case双角色GPU诊断或046性能比较，不作收益声明。


046完整正确性关闭（2026-11-06）：source002的fresh父/候选28case GPU分别38192/39419d与36251/730bd6，均exit0且monitor valid（37与30条遥测）。root全输出差分39990/58dacc exit0；独立v2完整审计38080/d5fc75 exit0、501pins重核。28case/56完整archives/84对应输出共406331392元素全部bitwise相同，logical输入相同，全部backing/padding约束及原4reference/12checker每role通过，所有NaN-payload/zero-sign宽免和mismatch计数均0。root差分SHA2b0e9a151a9988d62862ae54ab22c722cc7e98e02abce69a675c6043faef7b28；独审f28c5f16ff61f7aafc68455e8997e9bf7cb6c91a82114fa0b11d7788d3b47462。

reader v2只修正selftest到明确043历史recipe模型路径并pin SHA；仍对全部28模型重算，不继承旧GPU结果。原reader与静态首轮注释等同断言失败保留，新静态审查5e1fe9 exit0；唯一fresh selftest10125/768358 exit0，28recipes/64finite trajectories/11synthetic负例通过，244pins。原prelaunch及所有formal/runtime记录不变。

原性能comparison001已在所有正确性门槛通过后启动2493/f06375，521输入冻结prelaunch SHA0e03e4e1f8d34a68be9074b0713ceb10a8c44bc9cffa8410e735bbed7a8f6822；严格使用5pairs/330samples、原三shape和seed、原UUID/environment。需完整终态与root+独立原始时间重算后再作决定，不能以中途round选择结果。当前verified best仍043，046仅实验源。


## 2026-11-06 10:45：iter046采用，完整目标继续

只改变consumer原mask-ready等待和共享mask加载顺序；其余计算、mask表达式、release、producer/MMA及布局保持原样。正式构建及双架构实际代码核对通过，168 registers、0 stack/local spill。原316 cases（314数值比较、2按原脚本仅运行）、tail6、16query witness和两版本各28诊断通过；56份完整归档、84输出共406,331,392元素逐位相同。

| s_kv | 043均值 ± 轮间SD μs | 046均值 ± 轮间SD μs | 相对043加速 | 相对初始加速 | TFLOPS | TFLOPS/2250 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 350.023050 ± 0.123101 | 346.388580 ± 0.193075 | 1.050524% | 15.770705% | 991.942008 | 44.086311% |
| 8192 | 350.584300 ± 0.141076 | 347.092900 ± 0.095295 | 1.001062% | 15.543406% | 989.929162 | 43.996852% |
| 32768 | 356.503283 ± 0.131412 | 353.559660 ± 0.117089 | 0.835285% | 14.133547% | 971.822927 | 43.192130% |

原协议11轮/330样本完整有效，GPU实际session2493、terminal f54521退出0；独审session90821、terminal37862d退出0。五个汇总配对收益0.942910%–0.997593%，15个逐形状配对0.803675%–1.153267%，最大相邻A漂移0.115754%。汇总加速0.962249%、耗时降低0.953078%，直接相对初始加速15.146936%、耗时降低13.154441%。结果不属冻结计划要求额外确认的边界情形，全部有效数据均纳入。

Root最终重新核对564个唯一输入pin及当前源码/五文件package；独立最终只读核对3b869d退出0。采用046为当前最佳，未进行新的源码改动。三形状仍均未达严格>45%；下一步采集046最大原形状32768/seed312的full/source NCU，定位当前瓶颈。旧043 profile仅保留为历史证据。

证据：[采用决定](../../runs/main-clean-series-001/iter-046-mask-before-qk/decision.json)、[root重算](../../runs/main-clean-series-001/iter-046-mask-before-qk/comparison-001-root-revalidation.json)、[独审报告](../../runs/main-clean-series-001/iter-046-mask-before-qk/independent-runtime/comparison-001-audit001/REPORT.md)、[实际终态](../../runs/main-clean-series-001/iter-046-mask-before-qk/comparison-001-terminal.json)。监控为采样观察，不能排除采样间隔内的外来活动。


## 2026-11-06 11:06：046最大原形状full/source剖析有效

当前046的32768/seed312 full（41619/c4dd7c）和source（94029/45f5f8）均exit0、monitor valid，root与独审核对全部实际PC/加载包/输入通过。QK首次未就绪约89.7%、KV0约66%、KV1为0；mask R2P短依赖采样full1/source0。DRAM read/write峰值占比12.13%/8.53%，显式shared59处actual=ideal。NCU tensor47.39%不是理论目标，原benchmark32768仍43.192130%。

完整PM metadata额外找到了同pass0 CTA/SM/tensor时间序列，观察到末尾约13µs退场；不能推定可回收同等时间。旧generic图截尾缺陷已记载，原图和工具均保留。下一轮优先CPU验证首3块无用invalid判定短路，保持全部原TMA和数学语义；不是预期收益承诺。完整数据、六维分析和限制见[046当前剖析报告](../../profile/head64-iter046-kv32768/REPORT.md)。


## 2026-11-06T03:21:50.447987+00:00：iter047 CPU拒绝，保留046

只为producer原invalid判定增加 `k >= NUM_BUFS` 前置条件，未改索引读取、TMA、同步或数学。计划先冻结，隔离source逆变换逐字等于046。原flags完整TU双架构编译session86650/terminal9ec38b退出0（19.260893秒），两架构REG168、zero stack/local；源级等价与基本构建检查通过。

实际机器码在loop entry到首分支间仍无条件执行0x84d0/0x8500范围比较，直到0x8560才合入k<3，因此没有实现事前要求的前3块真实绕过。独立完整producer CFG计数也否定净收益门槛：

| tile数G | steady完整query发射slot变化 | first完整query变化 |
| --- | ---: | ---: |
| 2 | +31 | +32 |
| 3 | +46 | +47 |
| 5 | +76 | +77 |
| 10 | +151 | +152 |

两架构结果相同；G10 steady4652→4803、first4660→4812，gather准备/发行窗口383→398。计数包含遇到但谓词关闭的指令位置，采用指定的等待结果，不能换算成实测延迟。whole-function MOV.SPILL/R2UR.FILL各45→53属于UR/GPR搬运，并非local-memory spill。

root与独立源/必要门槛审查、独立成本审查一致，root关闭时重核65个唯一输入pin及主三headers/五package。独立源审实际eff274退出0，成本session11403/4875a0退出0；成本首版stdout括号错误99000a退出1已保留，v2仅补缺失括号。充分拒绝后未扩展完整native operand/其他角色资格，不把源级等价当作全kernel机器码证明。

未正式构建或运行047 GPU正确性/性能；三个shape耗时/波动、对父046及初始收益均N/A。按事前两个必要条件拒绝047，不扩展该guard强行获取结果。主源码和包始终为采用046，无需恢复；其三个原shape理论占比仍44.086311%/43.996852%/43.192130%，完整45%目标未达成。046剖析报告中的首3块建议为本轮实施前的历史假设，现已由此结果关闭。

证据：[拒绝决定](../../runs/main-clean-series-001/iter-047-producer-prologue-skip-check/decision.json)、[root终审](../../runs/main-clean-series-001/iter-047-producer-prologue-skip-check/root-final-reconciliation001.json)、[独立源/必要门槛](../../runs/main-clean-series-001/iter-047-producer-prologue-skip-check/independent-cpu-review/REPORT.md)、[独立完整成本](../../runs/main-clean-series-001/iter-047-producer-prologue-skip-check/independent-cost/cost-report.json)。


## 2026-11-06T03:36:05.713194+00:00：iter048 双P隔离CPU实验

以采用046为父本，把原单P32列改为P448/P480两个完整tile槽，并用两只Pfree[2]各init128匹配原连续global rs的slot/phase；TMEM分配仍512。单consumer、单issuer、原QK[k]→PV[k−1]顺序、三KV、S单槽和全部数学保持。仅放松相邻tile的P复用依赖，不声称消除KV0供数等待或达到目标。当前Pfree首次未就绪3948/40960，访问归属和等待时长未知，新增地址选择成本可能抵消收益。

[完整计划](../../runs/main-clean-series-001/iter-048-double-p-buffer/executable-plan.md)先冻结并逐字追加draft（e5b7f6，SHA677fb0ddf2cd326f346362dbde472b96e5433ab25cb3f986fc7605c411917fa4），之后生成源127e29退出0；config/phase逆变换逐字等046。source phase4d7a97c701001a3e499fc2813b6d1258d8660856cae93718675340bdfc9e2eaa、config65aa3231a997c8169dfe6e6d131cd3d4c4478c36f013f173984154e7a9613693。root已读完整diff，builder只改4处父本/说明身份，原flags不变。当前完整TU双架构CPU编译57009/c46ed1运行；同步代际模型和独立源审并行。主046三headers/五包均未改，尚无048实际代码资格或GPU结果，性能N/A。


### 048：隔离编译与逐角色CPU检查进展（2026-11-06T04:06:31.155805+00:00）

完整TU编译57009/2d81aa退出0，用时18.556551秒；两架构均REG168、零stack/local/spill。host对象实测shared仍222480字节：新8字节Pfree占用旧padding，后续SO至CLC屏障偏移+8，tmem_start/rowmax/rowli/CLCresponse保持。真实CuTe两P槽8192坐标验证，TMEM仍512列，原launch384线程/266workers/4acks保持。

Root basic实际5731a9退出0，全部native逐128位匹配ELF。独立源逆变换、99例同步图和原计数器边界分析已封；两架构2760个实际站点已全部分配审查范围（950公共及其他角色、1205consumer、585issuer、7role election、13不可达padding）。consumer实际Pfree/maskfree被编译器延后到local max之后，但仍在任何后续阻塞等待和SO之前；相应R100读依赖保留。Qcopy双架构各208组实际操作数检查包含全部8个TMA、48个copy、末commit、两phase和地址进位。

相同分支/重试条件下，issuer每tile少41个issued slot，四consumer warp合计每tile多24个；G10持续query合计净少170个。issuer首次启动额外1个，CTA初始化额外1个；Pfree/QT首次进入冷路径各额外1个。计数包含谓词关闭的遇到指令，不代表周期或收益。两架构分别检查，未假设整体机器码相同。

历史工具失败均保留：源段边界/依赖路径、host探针链接与constexpr复杂度、Mercury relocation假设、consumer冷返回映射、root冷热分支间一条setup以及CLC调度mask差异。修订只修正审查工具，未改048源码或数值门槛。Mercury仅清点与relocation边界，未独立解码其ISA；正式包仍必须逐字匹配隔离产物所有非debug sections。

原28诊断缺少受控混合G2/3/5/10的大query输入，已先冻结唯一追加P00配方；原28与316/tail6/witness16保持。新的混合输入仅提供运行压力，不冒称已观察同CTA query顺序。当前正式CPU综合资格待最后独立工具封存；主源/包仍046，没有048 GPU正确性或性能结果，三shape对父/初始收益均N/A。证据：[CPU基本检查](../../runs/main-clean-series-001/iter-048-double-p-buffer/root-basic-audit-001.json)、[完整PC覆盖](../../runs/main-clean-series-001/iter-048-double-p-buffer/root-native/complete-coverage.json)、[consumer](../../runs/main-clean-series-001/iter-048-double-p-buffer/independent-consumer/REPORT.md)、[issuer成本](../../runs/main-clean-series-001/iter-048-double-p-buffer/independent-issuer-cost/REPORT.md)、[补充配方](../../runs/main-clean-series-001/iter-048-double-p-buffer/additional-p-lifetime-plan.md)。


048 CPU综合资格已关闭：root d45e30退出0，364个规范化唯一输入重新核对，资格SHA632d0c6866a05594eb9efacf3ca8d0fcfee1ae9fb404fe808c1e08bac202aef8。最后CLC冷等待仅为依赖编号2/4互换，实际生产/等待位配套，无新增协议问题；正式工具完整diff/剩余AST独审通过。首次collector 90ad72失败因将独立源终态的本目录basename误解为仓库相对路径，保留失败；修复仅明确该字段路径基准，未改变SHA核验或候选。随后正式prepare真实54574/b1bb0e启动；已应用048冻结source，当前最佳仍046，GPU和性能资格尚未开始。


048原setup正式构建54574/1b1ccd退出0，DSO97974ba85a1d13e9163cee2866ab5f68285b6801acb38f5f696658256b0fdfc2。root实际包80231/9712a0与独立57447/d6cf4b均exit0；每架构2760站点的完整PC/文本/128bit及全部非debug（包括Mercury）与隔离产物相同，差异仅debug/内部symbol ID。168 registers、零stack/local/spill、原34/34 exemptions保持。root正式资格4aeb37退出0重核390pins，SHA712d3e3c3b40689018d9f0c88b3cebe8af54df4e671eea99302f74a94869e8d3；其中三个终态记录为实际flat exit_code并另pin独立完整terminal，不需修改冻结diagnostic schema。

403个真实运行输入和原316/tail6/witness16具体argv/env已冻结，prelaunch c1eae381bd7cecf6d6032525fabccc177be7142ba7d778ac176cc4e4b575a8c1。原316 GPU实际66239/2686c1启动，等待选定UUID锁/idle后运行；tail/witness/29双角色及性能尚未运行。当前源与包为048实验版本，最佳仍046；性能N/A。


### 048：原正确性通过，29case补充诊断待运行（2026-11-06T04:22:48.942409+00:00）

原316实际66239/e1ea06退出0，root4424e2与独立58d14c均通过：314原数值case+2原run-only、158head64，参数和seed完全不改；44遥测3/40/1有效。tail6实际53774/9663d2退出0，root0758c7/独立06d815通过；19遥测12/6/1，foreign仅在before，原handle等待后取得连续3idle，运行中无观测污染。witness实际70480/b49403退出0，root545386/独立1568a3通过；9遥测3/5/1，全部16query Q/KV/index输入及原checker和进程内DSO一致。witness独审前置命令记录遇到root终态文件尚未落盘的元数据竞态；原错误/空记录保留，随后同次reader实际exit0并封command002，没有重跑GPU或挑选结果。

P00严格追加在原28末尾；原28完整recipe字节逆变换、全部inputs/model及原29负例保持。新CPU29/94blob/36负例通过；独立使用另一finite底本核全部输入、512query/2560tile记录及17额外负例。root诊断CPU资格2220a500981a0f1a7d0814205fd4157028eaa494b3840a1fbbd9e534b6d47180，真实runtime binding8720f81d8adec20f0a5856b5a7e7e0758f2717282c954af507990e31a89809e9与550pins的prelaunch29fe5869fcf38f0a30315e6f97af36793e36d6e0e83749bc2f2827397900b090已冻结。新增独立reader原28数值/storage/monitor规则保持，只扩P00；第一次CPU selftest误用venv NumPy2.4.6，在未改donor位掩码逻辑遇OverflowError，失败保留；将用046原python3/NumPy1.26.4再次执行同一源码。尚未运行29case或benchmark，三shape性能及收益仍N/A，不采用048。


048 诊断结果读取器自检002已通过（CPU NumPy1.26.4，29例、576条有限轨迹、27个拒绝负例；实际39452/bc2494 exit0），独立静态审查97a4dc exit0通过。首次NumPy2.4.6环境失败原样保留；读取器源码未改。Root已重新核验所有冻结输入，见 `runs/main-clean-series-001/iter-048-double-p-buffer/root-diagnostic-reader-review-001.json`。两版本诊断尚未运行，性能仍为N/A，最佳版本仍046。


048 新增P00在内的两版本各29诊断已实际有效完成：parent90745/e8d895→71ed10、candidate64965/b39c7f→6f79b3，均exit0/valid。两次均在外部任务退出并获得3次idle后启动；运行期监控有效。Root完整差分32047/5f5326→8684eb exit0：29case、87输出数组、423174144元素逐位相同，NaN payload/零符号例外均0；全量输入、三阶段backing和padding通过。`diagnostic-differential-001.json` SHA ca969616ca16d471f8cb855a6274021323fa58b2824cab2b292ff23a01de5f62。独立完整CPU复核4430/9bdb7a运行中；性能仍N/A，最佳046保持。


048 独立完整诊断审查4430/9bdb7a→67f092 exit0通过（849 pins），root与独审全29例/87数组/423174144元素结果一致，全部bitwise相同。原316、tail6、witness16及两版本diagnostic29全部资格关闭，`comparison-001-prelaunch.json`冻结原5pairs/330样本命令与926个当前输入。性能结果尚未产生，采用门槛与三shape45%目标不变。

## 2026-11-06 12:51：iter-048 单consumer双P缓冲，正确但性能回退，拒绝

父版本046。将TMEM的完整P结果在448与480两组32列之间交替，并为两组各设128-arrival释放屏障；保留原单consumer/单issuer、QK[k]→PV[k−1]顺序、三槽KV/QK/SV、单S、数学和CLC。两架构正式产物与隔离构建完整核对通过，REG168、零stack/local/spill、384threads、512TMEM、动态shared222480B。候选DSO `97974ba85a1d13e9163cee2866ab5f68285b6801acb38f5f696658256b0fdfc2`。

正确性全部通过root和独审：原316（314数值与2原run-only）、tail6、16query见证，以及父/候选各29个完整诊断。新增P00覆盖混合G2/3/5/10、有效/无效与重缩放输入；输入顺序不证明实际同CTA调度。全部87输出数组、423174144元素逐位相同，分类/有限值/Inf符号差异为0，NaN payload与零符号例外为0；完整输入、三阶段backing和padding检查通过。

原comparison001：实际9391/e2449b→6bb34c exit0，valid=true；固定B200 UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。原sq4096、topk640、seed310/311/312及其他参数不变，6A/5B共11轮330样本；监控62条（3 before/58 running/1 after），未观察到外来任务。root完整重算16867/b9abf8→811883 exit0，原始330区间核对7f51b7 exit0；独审62734/81a95f→5e2e8a exit0，结果一致。

以下μs的±为各轮均值的样本标准差；父版本为本次交错重测，初始基线仍用原五轮15条记录。

| s_kv | 046重测 μs | 048 μs | 相对046配对加速 | 相对初始加速 | TFLOPS | 理论占比 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 346.418550 ± 0.143255 | 347.157740 ± 0.198297 | -0.219007% | 15.514204% | 989.744269 | 43.988634% |
| 8192 | 346.894400 ± 0.137264 | 347.695080 ± 0.037074 | -0.228207% | 15.343294% | 988.214684 | 43.920653% |
| 32768 | 353.493183 ± 0.137321 | 354.687540 ± 0.137908 | -0.331450% | 13.770611% | 968.732602 | 43.054782% |

汇总配对速度下降0.259567716%，等价耗时增加0.260243223%；全部15个形状配对速度变化为−0.398532077%至−0.136944650%，相邻control最大漂移0.100428177%。相对初始直接汇总加速14.873347468%、耗时降低12.947605164%，不叠加旧收益。三个形状均未超过45%，本轮没有可收录的正收益。

决定拒绝，不做挑选结果的追加有效批次。静态指令减少与解除单P复用依赖没有转化成原负载实测收益；本轮未采048 NCU，不能将回退归因到某个具体等待或额外寻址。已从归档046恢复三header/五package并逐项校验；实际更改phase1、config和DSO三个文件，另外957项决定输入保持原hash。当前最佳仍046，完整45%目标继续。

准备阶段的失败记录继续保留，包括首次独立读取器NumPy2.4.6环境不兼容（源码不改，使用已验证NumPy1.26.4自检002通过），以及性能建议脚本将原始15条baseline误写成3条的断言失败；它们不作为GPU数值或性能失败，不隐藏任何测量批次。

证据：[决定](../../runs/main-clean-series-001/iter-048-double-p-buffer/decision.json)、[原比较及330样本](../../runs/main-clean-series-001/iter-048-double-p-buffer/comparison-001/summary.json)、[root重算](../../runs/main-clean-series-001/iter-048-double-p-buffer/comparison-001-root-revalidation.json)、[独立性能审计](../../runs/main-clean-series-001/iter-048-double-p-buffer/independent-runtime/comparison-001-audit001/report.json)、[完整诊断差分](../../runs/main-clean-series-001/iter-048-double-p-buffer/diagnostic-differential-001.json)、[独立诊断](../../runs/main-clean-series-001/iter-048-double-p-buffer/independent-runtime/diagnostic-parent001-candidate001-audit001.json)、[恢复046](../../runs/main-clean-series-001/iter-048-double-p-buffer/restoration-001.json)。


049 同query下一tile索引预读的可执行计划已由root全文追加draft并冻结；父本锁定已恢复的046，不继承048双P。只准备四处producer源码改动，目标是跨原等待与gather隐藏索引load延迟。额外live值、phi/guard成本及实际早发/晚消费尚需双架构CPU验证，正确性与性能目前均N/A。计划：`runs/main-clean-series-001/iter-049-producer-index-lookahead/executable-plan.md`。


049隔离源码四literal生成完成（phase `a025669cfac43f9c91b508b59715d9c4c5023310146956e1c4a137bac9229e2d`，实际df40ca exit0），完整逆变换等046，主8文件保持046。首次生成162273 exit1因工具anchor缺少行首约束而拒绝重复命中，在snapshot生成前失败；原script/log保留，仅修复anchor后成功，候选机制未变。root读完整生成器/diff和builder三处身份替换后冻结CPU输入，实际85908/9fb91f开始原NVCC13.1.115 fullTU双架构隔离编译。尚无codegen/资源资格或GPU/性能结论。


049隔离编译85908/9fb91f→6544b9 exit0；双架构均2776 native sites、REG168、零stack/local/spill。source四处改动、producer提前load/晚消费、完整路径成本和root issuer操作数/等待/成本已完成各自范围的CPU审查；Qcopy与其他roles最终封存及全kernel覆盖闭合仍待完成。正式工具仅在冻结适配计划后生成（实际72ce83 exit0），保留原setup/环境/34个exemptions/完整native128与非debug ELF检查。主8文件仍046，尚未应用049、正式构建或GPU运行，性能N/A。


049全CPU资格已关闭：root覆盖b8c0c2 exit0将双arch各2776站点逐点分配，source/producer/issuer/Qcopy/consumer/mask/CLC/common的各范围证据和424pins重核通过（root资格5dc24a0f…83abc6b）。producer多数合法路径静态数目下降，但skip内层+4、phi/prefix增长均记录；不据此预测加速。正式原setup构建94359/eece04→1f28c5 exit0，DSO faedc8d910303787bb3ab1d174fd914677d438254f367a36d357ed94b7db23e5。root审计33649/7b87f0→214980及独审14754/646cbd→fa25d9均exit0：完整native128和所有非debug ELF含Mercury匹配隔离候选，REG168/0stack/0local/0spill与34/34 exemptions保持；debug路径/internalID差异明示。原CPU对父本的Mercury仅inventory、未独立ISA解码这一限制保留。root正式资格01b036c5…0fe56ca、455pins已封；主源码/package为待测049，采用版本仍046。原316/tail6/witness16和29诊断准备中，尚无GPU运行或性能结果。


049原316实际38686/73b00a→904c48 exit0/valid，root ff0a1d与独审0aef1c通过，44telemetry 3/40/1。原tail6实际31002/b78e9c→1c7a52 exit0/valid，root d8ff4b与独审49064c通过，16telemetry11/4/1；外来任务仅before等待，实际运行无污染。witness16实际95477/c132b3由固定monitor等待3idle后开始，尚未终态。29诊断源/CPU已root+独审关闭：5模块byteexact048、4模块仅身份/历史P00路径，原28bits/models与29case/94blob/36negative、576finite/12288nonfinite及独立P00全fixture/17额外负例通过；runtime binding为真实049/046包。诊断命令已冻结但独立reader selftest与witness双方结果未齐，未启动诊断GPU或性能；采用最佳仍046。


049全部正确性资格通过。witness16实际95477/c132b3→cfecc6 exit0/valid，root6cb3ea、独审fded17通过。parent29实际25340/a34d78→82cca6、candidate29实际60005/6abc57→ee4b2a均exit0/valid；监控分别44(14/29/1)、43(12/30/1)，外来任务仅before等待，运行无观察到污染。root全量比较92673/f1d120→3de1c4、独审66534/92ddd5→29d9ed均exit0；29对、58完整档案、87数组/423174144元素全部bitwise相同，分类/finite/Inf与NaN-payload/zero-sign例外全0；188个role-archive backing张量完整三阶段/padding均通过。root父包终态记录首次a8b26c因误把case.status期望为passed而失败，冻结harness实际输出completed；原GPU已成功且未重跑，只修元数据读取预期并保留failure文件。独立reader另有686计数字段与旧map schema的显式适配，保留17函数、oracle和原自测。原comparison001命令与1065输入在c84c8aed…5938faf冻结后实际19916/ac7cca启动，性能尚未产生，采用最佳仍046。


### 049 comparison-001 terminal and root verification

Original 330-sample comparison completed: root session `19916`, start `ac7cca`, terminal `22486c`, exit 0, valid and uncontaminated. Root readers `70ab83` and `d96d4f` both passed: all 11 reports, 330 raw intervals, original protocol and package identities. Paired aggregate speedup vs adopted046 is **+0.8800845043%**; all 15 shape-pairs are positive, minimum +0.7341917131%. Candidate means for skv4096/8192/32768 are 343.25164/343.71856/350.68826 µs; theoretical percentages 44.48921156/44.42877577/43.54578288%. All three remain below the strict45% goal. Independent performance audit remains pending; this paragraph does not adopt049.


### 049 adoption closed

Independent reader session `65201 / 919fe3 → 6d60ad` exited 0 and agreed with all root metrics. Root adoption session `84582 / 6611b4 → 863ebc` exited 0, reconciled 1109 immutable pins and verified the main three headers/five package files against archived049. All 15 shape-pairs exceed0.5%; the measured result is not borderline under the frozen plan, so no additional valid batch was selected. Adopted049 replaces046 as the verified best; decision SHA `a28c49d6c45e9f00f1e06111c45095b401872990034227d81c347f21d9cd42b7`. Allthree strict45% targets remain unmet. Fresh profiling must bind to049 before selecting the next mechanism.

Independent adoption closure also passed (`d82b88`, seal `ac3407`, exit0): all1109 root pins, main3headers/5package and retained046 archives verified. Report SHA `2a7950f308d3b5a4867fc251cfc0d3439915f48da6168b56c57ece31da38e8cf`; no kernel/package changes or GPU execution.


### 049 fresh profile and 050 plan

Fresh049 original32768 full/source captures are complete and independently reviewed, including all six dimensions, actual-PC role counts and same-pass PM samples. [Report](../../profile/head64-iter049-kv32768/REPORT.md) SHA 2907c959165df518df5cad2c78813a9865b774a6d81d9e1132f27487acb96794. Future-index first consumption has only1 long-scoreboard sample in each capture; producer parameter-packet reuse remains an observed hotspot, without a predicted saving. Wider Qcopy feasibility rejected on element mapping. Next isolated050 will exchange only perhalf gather loop nesting; full half order,049 lookahead and synchronization stay fixed. Plan frozen before code; no050 build, correctness or performance result yet (N/A).


050隔离完整TU编译73774/5867db→c00eb9 exit0；双arch均2752sites（049为2776）、REG168、stack/local/spill0。root全128bit/ELF及resource核验bef30a、独立源级966f22均exit0；仅两循环头交换，其余phase/config/common保持。main三headers及五package仍049。producer符号/全query/边界与完整路径成本检查已产生通过结果，最终逐点native覆盖正在关闭；所有计数仅诊断，不预测收益。原正确性和330性能尚未运行，结果N/A。


050完整CPU覆盖已闭合：双arch各2752sites=578 producer+2174其他，无缺漏/重叠；REG168及零local spill。正式原setup构建20909/2edc92→55b54f、root包审计49647/e434ac→d99aa0、独审1991/80c10a→c64f06均exit0；完整native128/nondebug ELF含Mercury与隔离产物匹配，原34/34 exemptions保持。root正式资格c8de85 exit0、1113pins，DSO `1eb0c3d7c9b5d1f7d568e17a8fcae76c05ee508d618cbba1537335ba77762220`。1151输入及原316/tail6/witness16命令已冻结；原316实际30579/eb70a4启动并等待固定UUID空闲。采用最佳仍049，050正确性及性能尚无结论。准备读取器对顶层schema/外部工具路径/terminal文件名的三次元数据失败均保留；未重跑GPU、改阈值或改候选。


050原316、tail6、witness16均通过root与独审：GPU终态分别30579/eb70a4→f6f140、71323/1dde10→409aed、30625/5c45fe→778bae，exit0/valid；监控49(9/39/1)、32(25/6/1)、9(3/5/1)，外来任务只在启动前等待，运行未观察到污染。独审终态分别c7fe94、ce1281、ea2372；参数/seed/原checker与包绑定保持。29诊断reader源静态审及完整CPU自测57477/fb2d29→552abc通过，29case/576finite轨迹/27negative。root完整1201pins资格84988/64c940→219d30已闭合，开始父049的29诊断；性能仍N/A，最佳仍049。


050完整诊断root41816/5ed6fb→472888及独审92910/cbf7f0→f11af3均exit0：父049与候选050各29cases，58完整归档、87数组/423174144元素全部逐位相同；NaN payload/zero-sign例外与所有分类/finite/Inf差异0。parent1708/6b127f→eb7afb、candidate43244/f23956→b600f9均valid，监控34(3/30/1)、36(3/32/1)未观察到foreign/unowned。原始checker、full backing和padding保持。原comparison001的1504输入和准确argv在`3a29a3eabcdd3652ca30c927c42924072b9fcce604014dab2009937361d0d1d9`冻结后，以72766/17bb32启动；原三shape/seed/5pair/330sample不变。性能尚无结论，采用版本仍049。


050 comparison001已结束：实际72766/17bb32→485023，monitor wrapper exit2（内层命令exit0），valid=false、contaminated=true，原因foreign_compute_process_observed。整批结果N/A，不进入收益/采用判断；所有原始数据保留。comparison002仅变更两个输出目录，其余原协议、父049/候选050包、UUID与环境保持，在新prelaunch重新冻结后重试。


### 050 producer列优先gather：拒绝，已恢复049

父版本049。仅交换每半块producer的local_col/local_row展开循环顺序，保留全部gather地址、049索引预读、数学和同步。正式双arch2752 native sites（049为2776），REG168、零stack/local/spill；完整源/native与正式包审核通过。静态指令减少没有转化成可保留的原负载收益。

正确性全部通过root和独审：原316（314数值+2 run-only）、tail6、16query见证，以及两侧各29诊断。58完整归档、87数组/423174144元素逐位相同；分类、有限值、Inf符号差异及NaN payload/零符号忽略均为0，完整backing/padding检查通过。

comparison001因运行期间外来GPU进程整批无效，N/A且保留全部记录。唯一有效comparison002：57405/059055→c23fb7 exit0/valid，监控69条（4 before/64 running/1 after），无观察到foreign/unowned。固定B200 UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原三shape/seed310–312、5pairs、6A/5B、330样本不变。root复算28349/dbb74b→b2d97e、原始区间fe5881、独审38472/39f7fc→d2f15d均exit0且数值一致。

以下μs的±为各轮均值样本标准差；049列为本次交错重测，初始基线保持原始记录。

| s_kv | 049重测 μs | 050 μs | 相对049配对加速 | 相对初始加速 | TFLOPS | 理论占比 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 343.176067 ± 0.117038 | 343.283480 ± 0.222692 | -0.029475% | 16.817885% | 1000.914415 | 44.485085% |
| 8192 | 343.036783 ± 0.494611 | 343.640860 ± 0.497938 | -0.154426% | 16.704096% | 999.873483 | 44.438821% |
| 32768 | 350.483017 ± 0.199790 | 350.098640 ± 0.343922 | +0.117433% | 15.261853% | 981.430215 | 43.619121% |

汇总配对速度变化−0.022217623%，等价耗时增加0.022222560%；相对初始直接汇总加速16.259114763%、耗时降低13.985238746%，不与历史收益相加。32768局部观察为+0.117433%，另两项回退；该变化与本轮波动同量级，不列入已验证收益汇总。15个shape-pair变化为−0.390627466%至+0.231895422%。

采用门槛为相对049可复现汇总严格>0.5%；本轮未达到，决定拒绝，不挑选追加有效批次。三shape仍未严格超过2250 TFLOPS峰值的45%。没有采集050 NCU，不能把变化归因于特定等待消除。恢复前核对全部决定输入；已逐项恢复/验证049三headers和五package，实际仅phase和DSO两个文件内容改变，050归档保持。当前最佳049，完整目标继续。

证据：[决定](../../runs/main-clean-series-001/iter-050-producer-column-major/decision.json)、[有效330样本](../../runs/main-clean-series-001/iter-050-producer-column-major/comparison-002/summary.json)、[root复算](../../runs/main-clean-series-001/iter-050-producer-column-major/comparison-002-root-revalidation.json)、[独立性能审计](../../runs/main-clean-series-001/iter-050-producer-column-major/independent-runtime/comparison-002-audit001/report.json)、[完整诊断差分](../../runs/main-clean-series-001/iter-050-producer-column-major/diagnostic-differential-001.json)、[恢复049](../../runs/main-clean-series-001/iter-050-producer-column-major/restoration-001.json)。


## Iter051 — split Q copy issuers（拒绝，恢复049）

父版本049。将原48次WS UTCCP分成warp8/warp10各24次，完成屏障计数2，CLC参与数267；布局、算术、gather和producer释放保持。正式包SHA `46b7696705128948fc432d242aedbede564769eaff966a76dc34ddd2a971fa55`。CUDA13.1原setup构建通过；168regs、0stack/spill、384threads、222480B动态shared+1024B，512TMEM。正式两个目标cubin的全部指令及128bit编码与隔离构建一致，52个其他cubin与049逐字节相同。

正确性：原316（314数值+2运行）、tail6、witness16全部通过。29组完整对照共87数组、423174144元素全部逐位一致，NaN payload/零符号豁免均0。所有GPU运行固定 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；均有效且未观测外来进程重叠。CPU诊断审计首次因运行绑定过早建立、少执行一个“绑定缺失”负向检查而失败；保留失败记录，按原顺序暂存绑定后以不变审计器重试通过29case/36负向检查。这不是kernel数值失败。

comparison001：固定原3shape/seed、6A5B、330samples，session74264/3ef316→0922c1，exit0有效，70条监测记录。结果由独立于比较脚本的原始时间区间重算核对（根代理执行，未声称独立代理审核）。下表SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 051均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.044383 ± 0.119603 | 342.446900 ± 0.209608 | +0.175426% | +17.103265% | 44.593760% |
| 8192 | 343.562650 ± 0.085625 | 343.065800 ± 0.048991 | +0.150046% | +16.899720% | 44.513312% |
| 32768 | 350.414467 ± 0.103998 | 351.000500 ± 0.146519 | -0.167205% | +14.965699% | 43.507046% |

汇总配对加速 **+0.052633983%**；耗时降低 0.052606294%；相对原始基线直接加速 16.318891155%。15个shape-pair范围 -0.199986% 至 +0.239929%。4096/8192各5对均为小幅正向，32768各5对均为负向；这些是本批观察，未额外复测为可复现收益，不加入报告开头的已收录优化。明确未越过0.5%门槛，拒绝且不再重复同一方案。三个shape均未达到45%。

已从049归档恢复3个header和5个package文件并逐项核对；本轮只实际改回config、phase和DSO，其余相同。未重新编译，051源码/正式包/测试/原始性能数据均保留。当前best仍049。

证据：[执行计划](../../runs/main-clean-series-001/iter-051-split-qcopy-issuers/executable-plan.md)、[正确性](../../runs/main-clean-series-001/iter-051-split-qcopy-issuers/correctness-qualification.json)、[原始330重算](../../runs/main-clean-series-001/iter-051-split-qcopy-issuers/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-051-split-qcopy-issuers/decision.json)、[恢复](../../runs/main-clean-series-001/iter-051-split-qcopy-issuers/restoration.json)。


## Iter052 — PV 前半 KV 提前释放（拒绝，恢复049）

父版本049。将原8条PV从K-major改成N-major，每个256维输出仍按原4个K16累加，在前半4条后额外commit；producer在此完成后加载下一tile的half0，仍等原SV-done才加载half1。消费者的S复用、O rescale/输出、Q/O别名保护及CLC不改。组合假设为提前加载抵消新增同步成本；实测不成立。

CPU与正式构建通过：两架构168regs、0stack/local/spill、2792静态指令，40MMA/48Qcopy/32gather保持，commit3→4，384threads/266CLC workers，动态shared222496B（+16B）+1024Bdriver，512TMEM。host probe覆盖32768个V元素并确认两个32KiB物理区域互斥、O32768地址唯一。probe首次遗漏-arch而被kerutils拒绝，保留失败记录；显式sm100a、相同probe源码重试通过。完整kernel TU两架构初次即成功。正式DSO `50a6d126b5041a60a1e5be0c9b87a66116c64b3912b042550a8ac667d7d18e9c`，两个目标cubin全部指令/128bit编码匹配隔离构建，52个其他cubin逐字节同049。

正确性：原316（314数值+2运行）、tail6、witness16及两版本各29组诊断全部有效通过；87数组/423174144输出元素全部逐位一致，NaN payload/零符号豁免0。诊断CPU29case/36负向检查通过，原参考实现/容差/recipe不变。根代理执行审核，无独立代理审核声明。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison001在运行中观察到foreign GPU process，83465/55a456→4552f3，outer exit2/inner exit0、valid=false；整批性能N/A，未读取其指标用于决定，全部原始数据保留。未变源码/包/参数，comparison002重试25801/41b526→9780ba exit0有效，71条监测、未观察到外来重叠。保留原6A5B/3shape/seed/330samples，由原始时间区间重算核对。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 052均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.110983 ± 0.138629 | 354.511440 ± 0.114954 | -3.214231% | +13.118070% | 43.076169% |
| 8192 | 343.610583 ± 0.136019 | 355.058500 ± 0.106695 | -3.225693% | +12.951235% | 43.009799% |
| 32768 | 350.517617 ± 0.228853 | 361.124380 ± 0.111870 | -2.934601% | +11.742713% | 42.287355% |

汇总配对加速 **-3.124934991%**；耗时降低 -3.225737181%（即增加3.225737181%）；相对原始基线直接加速 12.602334440%。15个shape-pair均回退，范围 -3.261663% 至 -2.909603%。没有局部正收益可收录，明确拒绝，不重复选择性测量。此组合的回退不能在没有额外对照/剖析时单独归因于N-major顺序或新增barrier；不把低寄存器/提前释放直接当作收益。三个shape均未达到45%。

已从049归档恢复并逐项核对3header和5package文件，实际改回config/phase/DSO，未重编译；052所有源码、产物、失败/无效记录和数据保留。当前best仍049。

证据：[计划](../../runs/main-clean-series-001/iter-052-pv-half-release/executable-plan.md)、[CPU布局/资源](../../runs/main-clean-series-001/iter-052-pv-half-release/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-052-pv-half-release/correctness-qualification.json)、[有效330重算](../../runs/main-clean-series-001/iter-052-pv-half-release/performance-audit-002.json)、[决定](../../runs/main-clean-series-001/iter-052-pv-half-release/decision.json)、[恢复](../../runs/main-clean-series-001/iter-052-pv-half-release/restoration.json)。


## Iter053 — warp 协作 cp.async KV 搬运（拒绝，恢复049）

父版本049。将4个elected-lane TMA gather issuer改为原4个producer warp的128线程协作搬运，每lane16B，保留原索引lookahead、精确skip条件、Q/O别名保护和全部consumer/MMA数学顺序。每半块128个cp.async noinc异步到达替代transaction byte-count，MMA等待后增加generic-to-async proxy fence。这个组合没有带来性能收益。

首版revision001双架构编译成功，但完整host布局检查失败49152项，未运行GPU。原因是直接调用带smem_ptr_flag的CuTe layout，忽略typed shared-pointer swizzle转换。先归档失败源码/计划/产物并追加计划，再修正为typed tensor reference物理地址。revision002重新完整编译；65536B布局/16B对齐/唯一覆盖和43,046,721种索引类别模式全部通过。原版skip只接受全负或全超上界，混合非法索引仍清零；实现精确保留这一点。

两架构168regs、0stack/local/spill，2680静态指令；32LDGSTS、2异步到达、40MMA、48Qcopy、3commit，动态shared222480B+1024Bdriver、384线程/266CLC、512TMEM。正式构建保留34/34原CUTLASS豁免。DSO `6cf664421fab1e927b58653ec7a724207175a245c84a642fae1ee6c9551ba9a8`，两个目标cubin全部128bit指令和非debug节匹配隔离attempt002，其余52个cubin逐字节同049。根代理审核，不声明独立代理审核。

正确性：原316（314数值+2运行）、tail6、witness16及两版本各29组诊断全部有效通过；87数组/423174144元素全部逐位一致，NaN payload/零符号豁免0。CPU29case/36负向检查通过，原参考、容差、recipe、存储和数值检查不变。CPU reviewer首次错误沿用052的等待字符串数量，核对049后修正检查器，保留失败记录，kernel不变；运行绑定安装器首次误读witness顶层passed字段，改用实际source_audit.passed，所有CPU审查已经exit0，未降低门槛。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；阶段间出现外来进程时均在启动前等待，5项正确性监测和comparison001全部valid。comparison30141/8dd927→7f1d9d exit0，71条监测无运行中外来重叠。保留原6A5B、3shape、seeds、330samples，从原始时间区间重算；SD为各轮均值样本标准差。

| skv | 同批049均值±SD µs | 053均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.134600 ± 0.111764 | 353.186860 ± 0.096714 | -2.847585% | +13.542304% | 43.237721% |
| 8192 | 343.696100 ± 0.175122 | 353.700060 ± 0.064476 | -2.832057% | +13.385042% | 43.174985% |
| 32768 | 350.457150 ± 0.156439 | 360.997680 ± 0.177111 | -2.917342% | +11.781932% | 42.302197% |

汇总配对加速 **-2.865668692%**；耗时降低 -2.950211993%（即增加2.950211993%）；相对原始基线直接加速 12.900281851%。15对全部回退，范围 -2.986399% 至 -2.774928%，无局部正收益可收录。明确拒绝，不选择性重测。该组合结果不能单独归因于copy engine、cache hint、地址运算或barrier成本。三个shape均未达到45%。

已恢复并核对049的3header和5package文件，实际仅复制phase和DSO，未重编译。全部053源码、正式包、首版失败及原始测量归档保留；当前best仍049，新建clean14仍干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-053-warp-cpasync/executable-plan.md)、[首版失败](../../runs/main-clean-series-001/iter-053-warp-cpasync/revision-001-rejected-layout/decision.json)、[CPU审核](../../runs/main-clean-series-001/iter-053-warp-cpasync/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-053-warp-cpasync/correctness-qualification.json)、[330样本重算](../../runs/main-clean-series-001/iter-053-warp-cpasync/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-053-warp-cpasync/decision.json)、[恢复](../../runs/main-clean-series-001/iter-053-warp-cpasync/restoration.json)。


## Iter054 — 提前计算全有效 mask 选择值（拒绝，恢复049）

父版本049。利用已采用的早读mask，在QK等待前准备full-mask的0/1选择值，随后走024同一逐位精确BRX fallback。数学、同步、producer/MMA/Qcopy/CLC/epilogue与049相同。历史024/025收益不能叠加或替代本轮实测。

初始CPU计划的“选择值在首次TRYWAIT之前”字面门槛失败：两架构实际首次非阻塞TRYWAIT0xeb0，selector0xed0/0xee0及table地址/LDC0xef0/0xf00，进入cold wait的条件分支0xf10，LDTM0xf50。根代理在任何054 GPU运行/性能结果之前明确修正了自己过严的调度判据，改查所有selector/table-load在真正等待分支之前且cold retry不覆盖其值；原计划、冻结和失败记录保留，未宣称原判据通过。源码没有改变，正确性、>0.5%采用及45%目标没有放宽。

正式机器码验证：constant2两目标0xfc0/0x1240，fast跳过40条mask指令；实际slow路径解释器每架构核对67712个任意float-bit值。cold loop仅改predicate，保留mask/target GPR。source逆变换精确恢复049；两架构2784静态指令、168regs/0stack/local/spill，40MMA/48Qcopy/32gather/3commit、384threads/266CLC、222480B动态shared+1024driver、512TMEM不变。正式DSO `948abd403d69f613cb0a75cea9731aa212e25d04ad043584359c3dbdc0e85796` 的两目标cubin全部128bit指令和非debug节（含constant2）匹配隔离构建，52其他cubin逐字节同049。原setup及34/34原CUTLASS豁免；根代理审核，无独立代理审核声明。

正确性：原316（314数值+2运行）、tail6、witness16及两版本各29组诊断全部有效通过；87数组/423174144元素全部逐位一致，NaN payload/零符号豁免0。CPU29case/36负向检查通过，原数值/recipe/存储/容差不变。固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，阶段间按原监测器等待。comparison19145/6a4d18→5aef8f exit0有效，80条遥测无运行中外来重叠。原6A5B/3shape/seeds/330samples全部从原始时间区间重算。SD为各轮均值样本标准差。

| skv | 同批049均值±SD µs | 054均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.133350 ± 0.083340 | 341.719060 ± 0.058543 | +0.414122% | +17.352687% | 44.688742% |
| 8192 | 343.619983 ± 0.104082 | 342.228840 ± 0.165395 | +0.408990% | +17.185612% | 44.622174% |
| 32768 | 350.375317 ± 0.171291 | 349.427560 ± 0.078253 | +0.278376% | +15.483215% | 43.702892% |

汇总配对加速 **+0.367143089%**，耗时降低 0.365800079%；相对初始基线直接加速 16.670770374%。15对全部为正，范围 +0.236344% 至 +0.480501%，且全部低于0.5%。保留本批稳定小幅收益记录并加入开头汇总，明确不采纳，不追加同候选测量挑选结果。三个shape均未超过45%。

已恢复并核对049的3header和5package文件，仅实际复制phase和DSO，未重编译；054全部证据保留。当前best仍049，clean14仍干净。

证据：[执行计划及CPU判据修正](../../runs/main-clean-series-001/iter-054-early-mask-selector/executable-plan.md)、[CPU核验](../../runs/main-clean-series-001/iter-054-early-mask-selector/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-054-early-mask-selector/correctness-qualification.json)、[330样本重算](../../runs/main-clean-series-001/iter-054-early-mask-selector/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-054-early-mask-selector/decision.json)、[恢复](../../runs/main-clean-series-001/iter-054-early-mask-selector/restoration.json)。


## Iter055 — 提前 mask 分支与平衡 rowmax 树组合（拒绝，恢复049）

父版本049。组合054的提前selector/table-load和023的16节点4层FTZ max树，与历史025晚guard组合不同；历史收益没有相加。源码逆变换、实际mask分支与cold-wait保值、32个P和-Inf叶子、最长4层max树均通过CPU审核。10022个边界/随机bit向量通过，其他数学、同步及角色保持049。双架构168regs、0stack/local/spill、2784静态指令，40MMA/48Qcopy/32gather/3commit、384threads/266CLC、222480B动态shared+1024driver、512TMEM保持。

正式DSO `44038e8679f0924a9e32906c9ecc56b9e6534aae18b016ec35d74b6907771881` 的两个目标cubin全部128bit指令和非debug节（含constant2）匹配隔离构建，其他52个cubin逐字节同049，原34/34 CUTLASS豁免保持。根代理审核，无独立代理审核声明。

正确性：原316（314数值+2运行）、tail6、witness16、两版本各29组诊断全部有效通过；87数组/423174144元素逐位一致，NaN payload/零符号豁免0。CPU29case/36负向检查通过；原参考、recipe、容差、存储均保持。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison001曾在启动前等待外来进程离开；同一工具session19620/a7000b最终2a2d6e exit0，监测器finished/valid=true/contaminated=false，共295条遥测，无运行中外来重叠。未重启或换卡。原6A5B/3shape/seeds/330samples已从原始时间区间重算，审核c0ae1b exit0。SD为各轮均值样本标准差。

| skv | 同批049均值±SD µs | 055均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.023750 ± 0.141120 | 341.673280 ± 0.110970 | +0.403679% | +17.368411% | 44.694730% |
| 8192 | 343.477350 ± 0.146412 | 342.164040 ± 0.142912 | +0.392771% | +17.207805% | 44.630625% |
| 32768 | 350.371883 ± 0.157667 | 349.213640 ± 0.134481 | +0.342208% | +15.553957% | 43.729663% |

汇总配对加速 **+0.379549077%**，耗时降低 0.378113949%；相对初始基线直接加速 16.707166921%。15对全部为正，范围 +0.275351% 至 +0.466621%，全部低于0.5%。记录小幅收益，但未满足采用门槛，拒绝且不选择性重测。三个shape均未超过45%。

已恢复并核对049的3header和5package文件，未重编译；055全部源码、产物及原始数据保留。当前best仍049，最新clean15保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/executable-plan.md)、[CPU审核](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/correctness-qualification.json)、[330样本重算](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/decision.json)、[恢复](../../runs/main-clean-series-001/iter-055-early-mask-rowmax/restoration.json)。


## Iter056 — 空闲warp预取KV整行（拒绝，恢复049）

父版本049。warp10/11各一个elected helper沿原实际CLC任务，按奇偶分配完整合法index quartet，通过独立UINT32/256x1/NONE-swizzle描述符发送KV整行L2 gather4 hint。CLC参与者266→268，原384线程、正常TMA与全部数学保持。部分/非法quartet省略hint，scalar index读取受逻辑/物理长度双重约束，query地址乘法使用64bit。该完整组合实测明显回退；结果不能单独归因于hint流量、额外索引/指令或CLC成本。

先导探针双架构编译成功，固定B200上的10组描述符编码/执行与40个quartet通过，93065760哨兵字节不变；先导结果没有被用来推断完整kernel性能。先行完整计划与CLC响应生命周期证明冻结后实现。两架构完整TU通过，168regs/0stack/local/spill、2920静态指令；1处UTMAPF.L2.2D.GATHER4，40MMA/48Qcopy/32正常gather/3commit/3CALL保持，222480B动态shared+1024driver、512TMEM、4produceracks。2867长度分区/2329856地址检查及73205 guard模型通过，源码逆变换精确恢复049。

正式DSO `1436c6e44e4a1769a26c0be468cbf14bf47d4f6e51f0e706fe63109938a1b7cc` 两目标完整128bit指令与非debug节匹配隔离构建，其余52个cubin逐字节同049，原setup及34/34 CUTLASS豁免保持。根代理审核，不声明独立代理审核。

测试准备首轮因遗漏必需计划元数据失败，生成物和错误归档；补齐元数据后用相同脚本重试。witness CPU首次CLI误传仅用于GPU的--output，保留错误日志后按原CLI重定向stdout通过。未修改kernel/数值检查/容差。CPU29case/36负向检查通过后才安装正式包绑定。原316（314数值+2运行）、tail6、witness16及两版本各29组诊断均有效通过；87数组/423174144元素全部逐位一致，NaN payload/零符号豁免0。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison001工具70103/955c1e→4e887c exit0，监测器finished/valid=true/contaminated=false，83条遥测无观察到运行中外来重叠。原6A5B/3shape/seeds/330samples从原始时间区间重算，审核7cae25 exit0。SD为各轮均值样本标准差。

| skv | 同批049均值±SD µs | 056均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.080917 ± 0.078522 | 407.159380 ± 0.104658 | -15.738085% | -1.508716% | 37.506185% |
| 8192 | 343.593350 ± 0.067525 | 408.176920 ± 0.400478 | -15.824901% | -1.747762% | 37.412686% |
| 32768 | 350.455667 ± 0.132841 | 408.375960 ± 0.412656 | -14.180991% | -1.186598% | 37.394451% |

汇总配对加速 **-15.251344283%**；耗时降低 -17.995971917%（即增加17.995971917%）；相对初始基线直接加速 -1.481293507%。15对全部回退，范围 -15.971347% 至 -14.107801%，没有局部正收益可收录。明确拒绝，不重复选择性测量。三个shape均未达到45%。

已恢复并核对049的3header及5package文件，实际复制config/phase/DSO，未重编译；056全部源码、产物、测试失败记录及原始性能数据保留。当前best仍049，clean15保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/executable-plan.md)、[CPU审核](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/root-cpu-qualification.json)、[正式包审核](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/correctness-qualification.json)、[330样本重算](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/decision.json)、[恢复](../../runs/main-clean-series-001/iter-056-kv-gather-prefetch/restoration.json)。

056后续剖析完成，仍拒绝。实际655360次hint/2621440次scalar索引load，helper约2630万warp指令；L2 TEX sector余量83886080与名义hint字节数一致。历史049计数上下文中指令+19.8897%、L2 sector+74.2815%，DRAM读仅-0.3452%，不支持继续全query预取。本次NCU显式clock-control none，与历史默认设置不同，未用profile时长作采用比较。下一方向是只预取首个64-index tile，尚未实现或声称收益。[六维/角色/PM剖析报告](../../profile/head64-iter056-kv32768/REPORT.md)。


## Iter057 — 仅预取首个KV tile（拒绝，恢复049）

采用父版本049，056仅为源码/工具来源。本轮相对056只将helper上限改为min(logical_length,physical_topk,B_TOPK)/4，最多预取首个64-index tile的16quartets；其余scalar读取、非法行省略hint、EVICT_LAST、两个elected helper、CLC268/384线程及完整正常TMA/数学路径保持。名义hint数量在topk640下160→16，仅是请求数减少，不当作性能收益。实测仍相对049回退，按先行计划结束此预取方向，不继续扫描cap/vectorization组合。

先行执行计划、CLC/地址证明冻结后实现，源码删除新增上限精确恢复056，删除全部prefetch新增路径精确恢复049。双架构完整TU及CPU审查通过，168regs/0stack/local/spill、2920静态指令，40MMA/48Qcopy/32正常gather/3commit/3CALL/1prefetch，222480B动态shared+1024driver、512TMEM和4produceracks保持。native0x7910的VIMNMX3实现min(length,64,topk)；相对056有11处指令文本变化，完整128bit共27处编码变化，额外16处为helper与cold-wait附近的调度/控制编码，原正常角色指令区域保持。

正式DSO `d6bffcfdd8ea882359625ebcf22bd4607add6d24ba0d2192f466a470b5f5c877` 两目标完整128bit/非debug ELF匹配隔离构建，52其他cubin逐字节同049；原setup和34/34 CUTLASS豁免保持。根代理审核，无独立代理审核声明。准备必需元数据后测试准备首轮通过；CPU29case/36负向检查通过后才安装运行绑定。

正确性：原316（314数值+2运行）、tail6、witness16、两版本各29诊断均有效通过；87数组/423174144元素逐位一致，NaN payload/零符号豁免0。原数值、recipe、存储、容差均未改变。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison001工具45484/7dbea0→052d88 exit0，监测器finished/valid=true/contaminated=false，89条遥测无观察到运行中外来重叠。原6A5B/3shape/seeds/330samples从原始区间重算，审核304dd6 exit0。SD为各轮均值样本标准差。

| skv | 同批049均值±SD µs | 057均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.193567 ± 0.106365 | 356.358980 ± 0.219225 | -3.694565% | +12.531611% | 42.852841% |
| 8192 | 343.625817 ± 0.162661 | 357.026400 ± 0.084746 | -3.762106% | +12.328657% | 42.772733% |
| 32768 | 350.513867 ± 0.171677 | 362.172720 ± 0.128214 | -3.209091% | +11.419264% | 42.164951% |

汇总配对加速 **-3.555568225%**；耗时降低 -3.686649566%（即增加3.686649566%）；相对初始基线直接加速 12.092131910%。15对全部回退，范围 -3.783145% 至 -3.125950%，无局部正收益可收录。明确拒绝，不选择性重测；三个shape均未达到45%。没有把相对被拒绝056更快替代相对采用父版本049的门槛。

已恢复并核对049的3header及5package文件，实际复制config/phase/DSO，未重编译；057全部源码、构建、正式包及原始数据保留。当前best仍049，clean15保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/executable-plan.md)、[CPU审核](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/root-cpu-qualification.json)、[native差异](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/native-delta-from056.json)、[正确性](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/correctness-qualification.json)、[330样本重算](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/decision.json)、[恢复](../../runs/main-clean-series-001/iter-057-first-tile-kv-prefetch/restoration.json)。


## Post057 feasibility — wider NONE gather layout (not a kernel iteration)

Root-only CPU research rejected direct replacement of the current SW128 KV staging with wider NONE-swizzled gather rows. The real CUTLASS descriptor accepted canonical NONE/SW128 on both architectures, while all six256/512/1024-byte row-pitch probes failed the specific canonical K-major stride check.131072 physical-coordinate checks passed after correcting the probe to evaluate CuTe typed-pointer swizzling; the initial failed probe and logs remain archived. No GPU run, candidate058 or new performance result exists (N/A). This conclusion does not exclude repacking or a different MMA/tensor-map design.

A separate actual049 PC review found16 serial packed sum additions, but only24/25 wait samples on three such PCs across source/full captures; balanced FP32 summation remains deferred rather than claiming a measured bottleneck. Main049's eight files and newly requested clean16 were reverified. See [feasibility report](../../profile/head64-wide-gather-layout-research/REPORT.md), [compiled and enumerated evidence](../../profile/head64-wide-gather-layout-research/result.json), and [sum counters](../../profile/head64-wide-gather-layout-research/softmax-sum-review.json).


## Iter058 — KV 三阶段就绪（拒绝，恢复049）

采用父版本049。将KV的两个就绪阶段256+256维改为128+128+256维，使第一组8条SS QK在前128维完成后即可发射；producer先完成前128维的8笔gather，再完成下一128维的8笔，最后256维16笔。增加每槽一个transaction barrier，保持原数学、32条QK累加顺序、8条PV、全SV释放、Q/O别名保护、CLC266与索引lookahead。这个组合未带来性能收益；没有单独测定新增屏障或发行重排各自的耗时贡献。

先行计划冻结后实现。双架构完整TU31001/55baaf→1573e0退出0；均168regs/零stack/local/spill、2776sites、40MMA/48Qcopy/32gather/3commit。实际shared222496B，较049增加16B（额外24B屏障部分吸收原padding），加1024driver仍符合容量。CPU检查32768物理坐标、128gather元组、360事务事件顺序、3888跨query/22680tile状态通过；机器码确认三个wait依次位于8SS/8TS/16TS之前。首次native检查的排除上界0x7100漏计最后一条MMA，保留失败后按实际QKcommit0x7110修正；候选代码未改。审核是root source/model与native重点检查，不声称完整ISA仿真或独立代理审核。

正式构建85597/fe0eab→2944ea和产物审计2242/3364dd→41a9fa均退出0。DSO `a540135c48551b73c92be1953700c213225a21cf8b46fd2166f918853a76b58b`；两目标完整128bit/非debug ELF匹配隔离构建，52个其他cubin逐字节同049。原setup、spill检查与34/34 CUTLASS豁免保持。

原316cases（314数值+2运行）、tail6、witness16、两版本各29诊断均有效通过。281e55复核87数组/423174144元素逐位一致，NaN payload与零符号豁免0。全部数值recipe、存储及检查器保持原样。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison00119403/f91582→77eff3退出0，监控valid且无观察到的外来进程污染，80条遥测。e5eefc从原始区间复算全部330样本（6A5B/5pairs/三组原形状和seed）；SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 058均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.293983 ± 0.123067 | 347.650240 ± 0.091128 | -1.248974% | +15.350560% | 43.926318% |
| 8192 | 343.584400 ± 0.055795 | 348.197760 ± 0.077251 | -1.323086% | +15.176778% | 43.857246% |
| 32768 | 350.483050 ± 0.118435 | 353.120080 ± 0.080893 | -0.748446% | +14.275625% | 43.245898% |

汇总配对加速 **-1.107164199%**；耗时降低-1.119559562%（即增加1.119559562%）；直接相对初始基线加速14.933353837%。15对均回退，范围-1.351465%至-0.697130%；无局部正收益可收入顶部。拒绝且不选择性重测，三组均未达到45%。

已逐项恢复049的3header及5package文件，未重编译；全部058源码、正式包、失败检查和原始数据保留。采用最佳仍049，新建clean16保持干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/root-cpu-qualification.json)、[同步检查](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/correctness-qualification.json)、[原始性能复算](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/decision.json)、[恢复](../../runs/main-clean-series-001/iter-058-three-stage-kv-ready/restoration.json)。


## Iter059 — 静态持久化 query 调度（拒绝，恢复049）

采用父049。将CLC动态取任务改成min(s_q,num_sm)个CTA按64-bit grid stride分配query；每个query结束后266个原工作线程在复用bar_clc_empty上arrive/wait，原scheduler lane8执行空callback并继续参加quorum。config/common、计算callback、数学与逐tile同步保持。此组合明显回退；本轮不能将回退单独归因于静态分配或新增query同步。

先行计划冻结后实现，四处源码逆变换精确恢复049。双架构完整TU55733/63f5a7→016596退出0，168regs、零stack/local/spill，2784sites（比049增加8）；40MMA/48Qcopy/32gather/3commit保持，UGETNEXTWORKID和response读取消失。shared222480B+1024driver、512TMEM、4produceracks保持。CPU2394分区/722358地址、95整数边界和51072quorum事件检查通过，真实native有五处role query到达/等待和64-bit循环。root source/model与native重点审核，不声称完整ISA仿真或独立代理审核。

正式构建43726/d0ac14→672ed2，产物审计19414/e87203→5214ea均通过。DSO `a7a8c54da3b012edabb3dbbe8916886d5a8caced87949de4df76b88066b9cf59`；两目标完整128bit/非debug ELF匹配隔离构建，52个其他cubin逐字节同049。原setup/spill检查与34/34CUTLASS豁免保持。artifact中的legacy clc_workers266表示复用的query边界屏障参与数，已无CLC请求，语义另存scheduler-metadata.json。

原316（314数值+2运行）、tail6、witness16及两版各29诊断有效通过。b04247检查87数组/423174144元素逐位相等，NaN payload/零符号豁免0；原数值recipe/检查器/容差不变。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison00173935/b04247→014031退出0，valid且无观察到的外来污染，77条遥测。d18346从原始时间区间复算330样本、原6A5B/5pairs/三形状和seeds。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 059均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.323667 ± 0.100660 | 387.805420 ± 0.100326 | -11.472298% | +3.406626% | 39.377982% |
| 8192 | 343.489550 ± 0.310141 | 386.353460 ± 0.695733 | -11.101046% | +3.802088% | 39.525969% |
| 32768 | 350.582567 ± 0.329746 | 394.474100 ± 1.296326 | -11.118885% | +2.295735% | 38.712288% |

汇总配对加速 **-11.230908019%**；耗时降低-12.651822575%（即增加12.651822575%）；直接相对初始基线加速3.166174942%。15对均回退，范围-11.500282%至-10.730398%；无局部正收益可收入顶部。拒绝且不选择性重测，三组均未达到45%。

已逐项恢复049的3header及5package文件，未重编译；全部059源码、正式包、失败检查和原始数据保留。采用最佳仍049，新建clean16保持干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/root-cpu-qualification.json)、[同步检查](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/correctness-qualification.json)、[原始性能复算](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/decision.json)、[恢复](../../runs/main-clean-series-001/iter-059-static-persistent-scheduler/restoration.json)。

## Iter060 — 静态调度下各角色独立推进（拒绝，恢复049）

采用父049。从拒绝的059仅移除新增query全组arrive/wait，保留静态64-bit grid stride及原计算callback、数学、逐buffer同步。全源码逆变换恢复049；相对059的单项删除也已精确检查。059和060分属不同批次，不能把二者时延差当作同批配对收益；060仍须直接对照049。

先冻结计划再实现。CPU跨query依赖DAG涵盖80组G2/3/5/10及混合长序列，检查Q/Q_t/O/KV/mask寿命与屏障防越代；另验证2394分区/722358地址及95整数边界。模型是聚合访问端点，不是CUDA内存模型仿真。源代码审查与完整GPU测试共同提供证据，不宣称独立代理审核。

双架构168regs、零stack/local/spill、2728sites，40MMA/48Qcopy/32gather/3commit保持，无CLC请求或response读取、无query边界arrive/wait。266仅为未使用的保留配置常量；shared222480B+1024driver、512TMEM及4produceracks保持。隔离构建原terminal输出因上下文截断不可用，已核对实际manifest finished/exit0、缺失handle及完整产物，未重建或伪造terminal。正式构建93889/92f7ab→f53214成功，产物审计35342/bf5b7e→fa4c68成功。

正式DSO `661a27d6d3bcf7173b6d8d02d8e6173720c62de81bbdcb3e9657eb639ef32725`；两目标完整128bit/非debug ELF匹配隔离构建，52其他cubin逐字节同049。原setup/spill检查及34/34CUTLASS豁免保持。原316（314数值+2运行）、tail6、witness16及两版各29诊断通过；87数组/423174144元素逐位相同，NaN payload/零符号豁免为0。原数值recipe、容差和benchmark参数未改。原测试32800/b4ccc2→e75262，补充及完整差分47955/007fc9→917043，资格924e03。有限16-query witness本身不覆盖多query/CTA；持久化覆盖来自512-query非有限和可变G诊断及原测试。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison00128286/924e03→4644f4退出0，valid且无观察到的外来污染，80条遥测。2656f0从原始时间区间复算330样本、原6A5B/5pairs/三形状和seeds。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 060均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.246283 ± 0.122724 | 346.876260 ± 0.157980 | -1.045982% | +15.607940% | 44.024330% |
| 8192 | 343.776767 ± 0.130099 | 347.266940 ± 0.109392 | -1.004317% | +15.485499% | 43.974802% |
| 32768 | 350.580250 ± 0.263050 | 353.137840 ± 0.149153 | -0.735728% | +14.269878% | 43.243723% |

汇总配对加速 **-0.928771013%**；耗时降低-0.937478038%（即增加0.937478038%）；直接相对初始基线加速15.119517842%。15对均回退，范围-1.150587%至-0.680577%；无局部正收益可收入顶部。拒绝且不选择性重测，三组均未达到45%。

已逐项恢复049的3header及5package文件，未重编译；全部060源码、正式包、失败检查和原始数据保留。采用最佳仍049，新建clean17保持干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-060-static-independent-roles/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-060-static-independent-roles/root-cpu-qualification.json)、[同步检查](../../runs/main-clean-series-001/iter-060-static-independent-roles/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-060-static-independent-roles/correctness-qualification.json)、[原始性能复算](../../runs/main-clean-series-001/iter-060-static-independent-roles/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-060-static-independent-roles/decision.json)、[恢复](../../runs/main-clean-series-001/iter-060-static-independent-roles/restoration.json)。

## Iter061 — 单独移除被后续 fence 覆盖的 P-free fence（拒绝，恢复049）

采用父049。仅删除MMA issuer的P-free wait后after-thread-sync；后续Qcopy/KV0等待及fence仍在首16条QK前，KV1保留原中途等待，所有其他计算/producer/consumer/CLC保持。源码逆变换精确恢复049。此前026还将KV1提前，不能由它的结果推断这一单项变化的性能。计划先冻结后实现，按官方PTX的after-thread-sync排序规则完成源级审查。

完整TU61260/46dd82→c39143，CPU审核6dd41a均通过。双架构2776站点含padding，168regs、零stack/local/spill；40MMA/48Qcopy/32gather/3commit/1CLC、222480B动态shared+1024driver、512TMEM、266CLC/4acks保持。native相对049仅删除热路径0x6180 NOP、调整0x6170控制字，后续代码重定位并增加末尾padding。全部2631个数据操作数逐项不变，141个控制流/3个return编码按完整PC映射核对，其余128bit/control不变；不宣称删掉一条硬件fence或消除等待周期。

正式构建70113/f66d5f→a12870，实际包审计1241/844365→a59708均通过。DSO `e1fdff032598036ad210b8393cfa8aecec31582669111965744fbef566608cc1`；两个目标完整128bit/非debug ELF匹配隔离构建，52其他cubin逐字节同049。原setup/spill检查及34/34CUTLASS豁免保持。原316（314数值+2运行）、tail6、witness16及两版各29诊断通过；87数组/423174144元素逐位相同，无NaN payload或零符号豁免。原测试42807/ecf4e3→ca3c62，补充及完整差分80102/59dc77→beed19，资格e34dba；数值recipe、检查器、容差及benchmark参数未改变。root-only审核，不声称独立代理审核。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison00197675/e34dba→10936b退出0，valid且无观察到的外来污染，75条遥测。ee9416从原始时间区间复算330样本、原6A5B/5pairs/三形状和seeds。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 061均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.184633 ± 0.083552 | 343.667260 ± 0.131729 | -0.138913% | +16.687432% | 44.435408% |
| 8192 | 343.573967 ± 0.061657 | 344.063800 ± 0.145202 | -0.144290% | +16.560638% | 44.384195% |
| 32768 | 350.494900 ± 0.143490 | 350.816240 ± 0.160197 | -0.099688% | +15.026083% | 43.529897% |

汇总配对加速 **-0.127632257%**；耗时降低-0.127795365%（即增加0.127795365%）；直接相对初始基线加速16.088921450%。15对均回退，范围-0.208307%至-0.031490%；无局部正收益可收入顶部。拒绝且不选择性重测，三组均未达到45%。

已逐项恢复049的3header及5package文件，未重编译；全部061源码、正式包、失败检查和原始数据保留。采用最佳仍049，新建clean17保持干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/root-cpu-qualification.json)、[同步检查](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/correctness-qualification.json)、[原始性能复算](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/decision.json)、[恢复](../../runs/main-clean-series-001/iter-061-qk-pfree-fence/restoration.json)。

## Iter062 — 两阶段128/384维KV就绪（拒绝，恢复049）

采用父049。保留两组bar_kv_ready，将256/256维划分改为128/384维；producer先各quartet两列，再各quartet六列。MMA首阶段SS8，第二阶段TS8+TS16；原32条QK累加顺序、PV、完整slot释放、Q/O别名保护、CLC和索引lookahead不变。配置/common逐字同049，不携带058第三屏障或061 fence删除。058与062不同批次的差异不能当作单独的屏障成本或配对收益，本轮直接对照049仍回退。

先冻结计划后实现，源码逆变换精确恢复049。完整TU87875/5a54ea→de42d5双架构成功，2776sites、168regs、零stack/local/spill，40MMA/48Qcopy/32gather/3commit/1CLC/3CALL保持；shared222480B+1024driver、512TMEM、266CLC/4acks保持。typed-pointer布局probe10741/bb977d→6b453d验证32768BF16坐标完整覆盖，事务总量16384/49152B。CPU检查128tuple、240种transaction事件顺序、3888query/22680tile的ring；实际native验证两组expect/wait、skip4096/12288B、8SS/24TS顺序及32gather的barrier参数8/24分配。模型不是GPU仿真，root-only审核，不声称完整ISA解释或独立代理审核。

正式构建88572/d03763→36fb83，实际包审计41457/c6021e→7bba4e通过。DSO `b468dfbd4024634ba9edbaec17440bb4f64dd5a418cdeb9f2bc47e33265b39d8`；两个目标完整128bit/非debug ELF匹配隔离构建，52其他cubin逐字节同049。原setup/spill检查及34/34CUTLASS豁免保持。原316（314数值+2运行）、tail6、witness16及两版各29诊断有效通过；87数组/423174144元素逐位相同，无NaN payload/零符号豁免。原测试6566/17db46→95501a，补充与完整差分29462/1f823b→bafbb9，资格800380；未改原数值recipe、检查器、容差或benchmark参数。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`。comparison00156043/800380→f9cd9c退出0，valid且无观察到的外来污染，77条遥测。60edfd从原始时间区间复算330样本、原6A5B/5pairs/三形状与seeds。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 062均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.402367 ± 0.110712 | 346.266480 ± 0.182885 | -0.825161% | +15.811528% | 44.101857% |
| 8192 | 343.865017 ± 0.151816 | 346.799840 ± 0.091012 | -0.839559% | +15.641045% | 44.034031% |
| 32768 | 350.911383 ± 0.170033 | 353.840640 ± 0.173206 | -0.819832% | +14.042915% | 43.157832% |

汇总配对加速 **-0.828184645%**；耗时降低-0.835100822%（即增加0.835100822%）；直接相对初始基线加速15.162398833%。15对均回退，范围-0.931778%至-0.729895%；无局部正收益可收入顶部。拒绝且不选择性重测，三组均未达到45%。

已逐项恢复049的3header及5package文件，未重编译；全部062源码、正式包、失败检查和原始数据保留。采用最佳仍049，新建clean17保持干净。

证据：[执行计划](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/root-cpu-qualification.json)、[同步检查](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/correctness-qualification.json)、[原始性能复算](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/decision.json)、[恢复](../../runs/main-clean-series-001/iter-062-asymmetric-kv-ready/restoration.json)。


## 049 流水线诊断：SASS 采集失败，输入与独立加载器验证通过

本轮没有候选优化，收益为N/A，采用最佳仍049。CUDA13.1独立harness的2776条完整128位指令与正式049相同；原seed312/skv32768测试通过，导出原始输入/参考，独立加载器三个输出逐字节相同。固定GPU-847489a9-bc7e-726c-1c64-29c59e330fd8，export001监控有效。

SASS capture001在SDK0.0.35 fresh Cubin.serialize处失败，仅scout执行且输出正确；无traced launch、记录或阶段耗时。保留失败，不作为性能证据。CPU诊断显示未打桩的production和standalone cubin同样无法经此路径序列化；donor dump保留原指令，不能作为有效trace回退。下一步改用隔离PTX采样，继续验证稳态覆盖与扰动。生产八文件仍049，clean18保持干净。

[本轮报告与全部证据](../../profile/head64-iter049-xtrace/REPORT.md)。


## 049 PTX 流水线诊断：采集与降低密度对照通过

固定原seed312/skv32768/GPU，完整密度2048records和低密度992records均通过输出逐位比较、容量、16query/480waitpair覆盖及原monitor。仅profile采样，非新优化采用，收益N/A。后续query首tile QK等待均值约1437/1472ns，两种密度下其余tile约172/170ns；KV0首tile约37/35ns。提示优先拆解Q准备/首QK链路，不把NCU not-ready次数当等待周期，不推断跨角色时间总和为关键路径。

独立A-B-A直接launch envelope中位数372.528/372.944/372.032µs，但SD21–31µs，不能据小差值声称无扰动；原30samples保留。生产049八文件和clean18保持。下一步验证Q就绪/UTCCP/首QK分段，再决定优化；原45%及严格>0.5%门槛不变。

[完整报告、HTML/JSON及验证证据](../../profile/head64-iter049-xtrace/ptx/REPORT.md)。

## 049 Q prologue 诊断：有效采集，存在探针敏感性

固定原seed312/skv32768/UUID。分段1152records和仅新增Q-ready区间1024records都通过输出逐位比较、16query覆盖及监控。Q-ready均值分别1978.67/1546.67ns；consumer首tile QK则1808/1114.67ns（此前低密度1472ns）。绝对耗时受采样/编译影响，不能推断收益；仅支持试验跨query提前Q TMA。无优化采用，性能收益N/A，生产仍049。

[报告及完整原始证据](../../profile/head64-iter049-xtrace/ptx/REPORT.md#q-prologue-分段及单区间复查2026-11-06)。

## Iter063 — 跨query提前Q TMA（采用，第三组仍未达45%）

采用父049。最后一次PV之前，MMA线程等待倒数第二SV完成及当前CLC响应；若下一任务有效，提前提交下一query的Q TMA，UTCCP仍在下一query原位置。倒数第二SV commit同时保护此前最后QK和QT别名槽；CLC响应保留到原empty arrival。数学、producer、consumer、mask、epilogue和所有原同步不变。新增等待与提前搬运的实际净收益由原benchmark证明，不能把Xtrace阶段耗时当作收益估计。

冻结计划后生成源码，逆变换精确恢复049。4086query/26994tile的ring检查、362880事务顺序和27个依赖图通过；这些是模型检查，不是GPU仿真。完整TU双架构168regs/零stack/local/spill，2832sites（父2776）；40MMA/48Qcopy/32gather/3commit/1CLC/3CALL保持。源级两次Qcopy展开为8条native TMA，启动与提前提交路径各8条，动态仍每query65536bytes。共享内存222480+1024driver、512TMEM、384threads、266CLC workers和4produceracks保持。

隔离构建94572/3fbd9c→3bb94e、正式构建51076/569d50→bc7c04、实际包审核12480/644e9b→44d26e均成功。DSO `74402a43e80d991da06cd3257f3a66f039f8e2b644dd95e2b1896048a3824e99`。两个目标完整128bit/非debug ELF匹配隔离产物，其余52cubin逐字节同049。原setup及34CUTLASS豁免保留。原316（314数值+2运行）、tail6、witness16、两版各29诊断和完整差分均通过；87数组/423174144元素逐位相同，无NaNpayload/零符号豁免。原测试74698/1031b3→83c6c1，补充与差分19632/c8af7a→8ba2b1。所有监控有效。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原shape/seed/warmup/flush/cooldown/CUPTI协议不变。comparison00165232/333323→9a0c14有效且未观察到外来竞争，78条遥测。0753b5复算全部330原始样本、原6A5B/5pairs。SD为各轮均值的样本标准差。

| skv | 同批049均值±SD µs | 063均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 343.185733 ± 0.125901 | 334.025120 ± 0.115975 | +2.742242% | +20.055791% | 45.718103% |
| 8192 | 343.777917 ± 0.142985 | 334.773220 ± 0.151092 | +2.683751% | +19.795413% | 45.615939% |
| 32768 | 350.708750 ± 0.106782 | 343.545740 ± 0.133168 | +2.087281% | +17.460394% | 44.451126% |

汇总配对加速 **2.503997016%**，耗时降低2.442828659%；直接相对初始基线加速19.098123321%。全部15对提升2.029101%至2.788889%，明显超过严格0.5%采用门槛且无形状回退，采用063。各轮数据全部保留，无选择性重复。前两组超过45%，32768组44.451126%，仍需从343.545740us降至严格小于339.355441us；目标继续进行。

证据：[执行计划](../../runs/main-clean-series-001/iter-063-early-next-q/executable-plan.md)、[TMA展开澄清](../../runs/main-clean-series-001/iter-063-early-next-q/native-plan-clarification.md)、[同步审核](../../runs/main-clean-series-001/iter-063-early-next-q/synchronization-review.md)、[CPU资格](../../runs/main-clean-series-001/iter-063-early-next-q/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-063-early-next-q/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-063-early-next-q/performance-audit-001.json)、[采用决定](../../runs/main-clean-series-001/iter-063-early-next-q/decision.json)。

## 063 Q-ready诊断：新产物绑定及降低密度复查通过

正式063原输入重新导出，关闭探针2832条完整128bit指令一致；两组单launch阶段采集1024/384records，输出逐位相同，覆盖与固定GPU监控均通过。减少KV0/SV探针后Q-ready仍约1.53µs（完整角色1.568µs），支持试验更早Q缓存预取，但不能量化收益或宣称无探针扰动。未采用新优化，性能收益N/A。下一步冻结CLC producer提前Q L2prefetch方案，原45%/严格0.5%门槛保持。

[报告及原始证据](../../profile/head64-iter063-xtrace/REPORT.md)。

## Iter064 — CLC线程提前Q L2预取（拒绝，恢复063）

采用父063。当前063两种探针密度下Q-ready约1.53–1.57µs，提出由CLC producer在当前响应就绪后预取有效下一query的Q到L2。保留063实际Q加载/UTCCP、所有原同步及数学。该cachehint候选实际回退，不能由Q等待较长推断L2预取必然有益，也不能把回退单独归因于带宽、缓存或CLC开销。

先冻结计划。attempt001通用CuTe动态范围生成56静态预取点/3528sites，违反计划的8点门槛；保留完整源码/产物/资格失败，未进行GPU运行。冻结revision002后改为固定M64/128、M64/384局部tile，双架构2888sites、8预取点、168regs/零stack/local/spill；16实际Qload/40MMA/48Qcopy/32gather/3commit/1CLC/3CALL保持，shared222480+1024driver/512TMEM/384threads/266workers/4acks不变。源逆变换、32768坐标/64head范围、64任务链及nativevalidguard/8坐标包通过。模型不是GPU仿真。

CPU构建34575/a887e6→461ec8（资格失败）及15307/71775f→b10fc9（通过）全部保留。正式构建90358/c0a0b7→133564和实际包审核66165/b954ee→599b13通过。DSO `800b2dc17a7e26df7a99431a39cf80702c3d1cbe06cca572a04b54db39b2ace3`；两个目标完整128bit/非debug ELF同attempt002，其余52cubin逐字节同063。原setup/34CUTLASS豁免保持。原316（314数值+2运行）、tail6、witness16、两版29诊断与完整差分通过；87数组/423174144元素逐位相同，无NaNpayload/零符号豁免。原79888/d60a01→4c9db6，补充40908/5fa5b2→ae6719，所有监控有效。测试数值代码未改，元数据绑定从049改为当前063及root-only正式审核schema，未虚构独审。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原参数/seed/warmup/flush/cooldown/CUPTI协议不变。comparison00139716/246668→b53d36有效，78遥测、无观察到的竞争；c895b4复算330原始样本，原6A5B/5pairs。SD为轮均值样本标准差。

| skv | 同批063均值±SD µs | 064均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.999533 ± 0.180393 | 336.377200 ± 0.190935 | -0.711520% | +19.216314% | 45.398424% |
| 8192 | 334.934133 ± 0.103132 | 337.593880 ± 0.146608 | -0.789238% | +18.794499% | 45.234809% |
| 32768 | 343.457850 ± 0.132055 | 350.029280 ± 0.209349 | -1.876673% | +15.284693% | 43.627764% |

汇总配对加速 **-1.127244190%**，耗时降低-1.140095855%（即增加1.140095855%），直接相对初始基线加速17.751890883%。15对均回退，范围-1.930099%至-0.609836%，没有可收入顶部的局部正收益。拒绝，完整恢复063八文件而不重编译；不选择性重复或盲扫hint位置。当前最佳仍063（45.718103%/45.615939%/44.451126%），45%全形状目标未完成，clean18保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/executable-plan.md)、[CPU修订](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/revision-002-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/performance-audit-001.json)、[拒绝决定](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/decision.json)、[恢复](../../runs/main-clean-series-001/iter-064-clc-q-l2-prefetch/restoration.json)。

## Iter065 — CLC线程提交下一query实际Q加载（正确性拒绝，恢复063）

父063，冻结计划后将实际下一Q加载移到CLC线程，保持每query八次传输。隔离构建73591/1e5f05→b81e02、正式55504/0e2421→24fe63、实际包审核65034/935f34→b16d21均完成；双架构2936sites/168regs/零stack/local/spill，16Qload/40MMA/48UTCCP/32gather/3commit/1CLC，DSO `2da03feb1069b229e35ca2a55b63c444be22a3b7ce0893c99619716f8cf60e5c`。两个目标native128与隔离版本一致，其余52cubin同063。测试准备001因缺少绑定说明文件失败，已保留；补齐元数据后CPU29cases/36负控及witness审核通过，数值代码未改。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8` 原测试22619/bfc21b开始48例，停留在seed47（sq213/topk384/G6），未完成316例。复查发现源码级同步缺陷：CLC可在当前PV尚未完成时等待未来SV代际，例如S0/G6指向slot1/generation1，此时实际仍generation0。PTX parity wait只能用于当前或紧邻前一阶段，不能用单个parity标识任意未来代际。最初4086query/27依赖图模型假定了目标代际完成边，漏掉“过早等待”前置条件；其CPU资格已明确撤销，历史记录保留。新增反例检查覆盖G5..32共28例。此源码反例足以拒绝，但没有指令级trace，因此不把它冒充为seed47停滞的完整运行时根因定位。

确认缺陷后只向经/proc与环境绑定验证的本轮Python PID3015886发送SIGTERM（ae2680）；没有终止其他任务、换卡或重启尝试。真实句柄22619→5d0fd9结束，外层241/子命令-15，监控无外部竞争，退出后GPU进程为空。此轮正确性未通过，性能及相对父/初始收益均N/A，不运行补充GPU测试或330采样。完整恢复063八文件，不重编译；clean18保持干净，原45%全形状目标仍未完成。

后续需要每query独立的就绪握手，不能直接提前等待循环SV parity。可研究由MMA在倒数第二次PV后提交独立Qfree barrier、CLC按outerphase等待；每query只有一次翻转且下一次提交依赖下一Q，避免未来代际混淆。尚未实现，收益未知。

证据：[计划](../../runs/main-clean-series-001/iter-065-clc-actual-q/executable-plan.md)、[资格撤销](../../runs/main-clean-series-001/iter-065-clc-actual-q/qualification-revocation.json)、[反例](../../runs/main-clean-series-001/iter-065-clc-actual-q/phase-counterexample-result.json)、[测试监控](../../runs/main-clean-series-001/iter-065-clc-actual-q/original-001-monitor/manifest.json)、[拒绝决定](../../runs/main-clean-series-001/iter-065-clc-actual-q/decision.json)、[恢复](../../runs/main-clean-series-001/iter-065-clc-actual-q/restoration.json)。语义依据：[PTX13.1.1 mbarrier wait](https://docs.nvidia.com/cuda/archive/13.1.1/parallel-thread-execution/index.html#parallel-synchronization-and-communication-instructions-mbarrier-test-wait-mbarrier-try-wait)。

## Iter066 — 每query独立Q就绪握手与CLC实际加载（拒绝，恢复063）

父063。在065未来SV代际反例基础上，新方案增加每query只完成一次的Qfree barrier，MMA在最后QK/倒数第二PV后commit，CLC按outerphase等待后加载有效下一Q。下一次完成依赖下一Q加载，当前CLC等待不会提前或错过两次翻转。源逆变换精确还原063；新增barrier位于原8字节填充0x360e8，静态断言确认tmem_start0x360f0、CLCresponse0x36500及sizeof222480不变。源码计划先冻结，参数/数学/加载总量不变。1..6query早/晚等待模型共402状态，移除背压或握手能触发负控，拒绝065G6；另检查4086query/26994tiles与362880事务顺序。模型不是GPU仿真。

隔离83364/30e1a0→c0857d、正式64541/632161→9d12c3、实际包84043/e9ab2c→d3256c成功；sm100a/sm103a均2944sites/168regs/零stack/local/spill，40MMA/48UTCCP/32gather/16Qload/4commit/1CLC/3CALL，无cacheprefetch。新增每query一次commit，CLC八个TMA点仍带编译器选举循环。DSO `c381cb534dad880e98673b195731f0c24c1411ccf4a5a1039ea2c63d707b0a2d`；两个目标native128/非debug ELF同隔离，其余52cubin同063；原setup/34CUTLASS豁免不变。

原316（314数值+2运行，70546/f116e3→298ade）、tail6/witness16/两版29诊断及全量差分（58534/5b6b72→d535ac）通过，87数组423174144元素逐位相同，无NaNpayload/零符号豁免，所有监控有效。双方报告明确完成29attention/5finite+reference/15checkers，模块绑定不变。测试只改候选标签/计划hash元数据，原051数值recipe/checker/tolerance/storage未改；CPU29cases/36负控及witness审核通过。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原参数/seed/warmup/flush/cooldown/CUPTI协议不变。comparison00188475/a92e00→5bcf2b有效，82遥测无观察到竞争；989f7a重算原330样本、6A5B/5pairs。SD为轮均值样本标准差。

| skv | 同批063均值±SD µs | 066均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.082617 ± 0.185268 | 353.098920 ± 0.096276 | -5.385275% | +13.570582% | 43.248489% |
| 8192 | 334.884483 ± 0.235212 | 353.906920 ± 0.154655 | -5.368722% | +13.318768% | 43.149749% |
| 32768 | 343.414150 ± 0.232116 | 359.552960 ± 0.114855 | -4.486526% | +12.231083% | 42.472171% |

汇总配对加速 **-5.081100608%**，耗时降低-5.353096844%（即增加5.353096844%），直接相对初始基线加速13.038646677%。15对全部回退，范围-5.440195%至-4.453857%，没有可记入顶部的局部正收益。拒绝并完整恢复063八文件，不重编译、不选择性重复。独立握手通过完整正确性，但性能数据不能把回退单独归因于commit、选举、调度或CLCempty延迟。当前最佳仍063（45.718103%/45.615939%/44.451126%），原45%全形状目标未完成；clean18保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-066-clc-q-handshake/executable-plan.md)、[阶段模型](../../runs/main-clean-series-001/iter-066-clc-q-handshake/lifetime-model-result.json)、[同步/native审核](../../runs/main-clean-series-001/iter-066-clc-q-handshake/synchronization-review.md)、[CPU资格](../../runs/main-clean-series-001/iter-066-clc-q-handshake/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-066-clc-q-handshake/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-066-clc-q-handshake/performance-audit-001.json)、[拒绝决定](../../runs/main-clean-series-001/iter-066-clc-q-handshake/decision.json)、[恢复](../../runs/main-clean-series-001/iter-066-clc-q-handshake/restoration.json)。

## Iter067 — 显式选举CLC实际Q加载线程（CPU同步拒绝）

父063。重用066正确的每query握手，并在CLC分支加 `lane_idx == B_TOPK/8 && elect_one_sync()`。计划先冻结，源码逆变换到063、单项逆变换到066通过；066阶段模型原样复用。隔离43432/f27418→56478c成功，双架构2888sites/168regs/零stack/local/spill，八个逐TMA选举循环确实消失。

但native在lane8分支gate0x7e50/7e60后新增WARPSYNC.ALL 0x7e70和ELECT0x7e80。本地CuTe helper的membermask固定0xffffffff；PTX elect.sync需要掩码内线程参与。仍存活的masklanes0..7在另一分支等待CLCresponse，不能到达选举，而CLCrequest又位于选举之后，存在进度环。CPU同步门槛拒绝，未构建正式包、未启动GPU、正确性/性能及相对初始/父收益均N/A。审核脚本首次JSON序列化set失败，原脚本/失败记录保留，改为list后证据写出；这没有改变kernel或审核断言。063生产源码/包未改，clean18干净，45%全形状目标仍未完成。后续需只含lane8的0x100掩码，不能在此分支直接用全warp helper。

证据：[计划](../../runs/main-clean-series-001/iter-067-elected-clc-q/executable-plan.md)、[CPU拒绝](../../runs/main-clean-series-001/iter-067-elected-clc-q/cpu-rejection.json)、[决定](../../runs/main-clean-series-001/iter-067-elected-clc-q/decision.json)。语义依据：[PTX13.1.1 elect.sync](https://docs.nvidia.com/cuda/archive/13.1.1/parallel-thread-execution/index.html#parallel-synchronization-and-communication-instructions-elect-sync)。

## Iter068 — lane8掩码选举CLC加载线程（拒绝，恢复063）

父063。066正确的每query独立Qfree握手保留，新增局部elect.sync helper使用membermask0x100，只在warp9/lane8分支执行，修复067全warp选举同步问题。源码计划先冻结，逆变换到063、helper+condition逆变换到066通过，066阶段模型原样复用。所有数学、加载总量、barrier参与者及测试协议不变。共享barrier仍使用原8字节padding，sizeof222480及关键offset静态断言通过。

隔离87674/5f4bd1→6e12d9、正式39149/9d16ab→094295、实际包35879/1d4495→04a0b9成功。双架构native在0x7e70生成R2=0x100、0x7e80 WARPSYNC R2、0x7e90ELECT，掩码成员只有lane8，无CLC路径全warp同步。八个逐TMA选举循环消失，2888sites（066为2944），仍168regs/零stack/local/spill、40MMA/48UTCCP/32gather/16Qload/4commit/1CLC/3CALL，无cacheprefetch。DSO `b6c4931d7d40d7fa49d48f2af711be130cabd9ef1db4134af18e5b186eae2b15`；两个目标native128/非debug ELF同隔离、其余52cubin同063；原setup/34CUTLASS豁免不变。

原316（314数值+2运行，13645/a3efea→66aba3）、tail6/witness16/两版29诊断及全量差分（45629/8cfa28→a72783）通过；87数组423174144元素逐位相同，无NaNpayload/零符号豁免。实际报告29attention/5finite+reference/15checkers、wrappers恢复和模块绑定一致，所有监控有效。测试适配仅066→068候选标签/计划hash，数值recipe/checker/tolerance/storage不变，CPU29cases/36负控和witness审核通过。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原参数/seed/warmup/flush/cooldown/CUPTI协议不变。comparison00180037/4ed83b→8f5b1f有效，88遥测无观察到竞争；61d892重算原330样本、6A5B/5pairs。SD为轮均值样本标准差。

| skv | 同批063均值±SD µs | 068均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.079417 ± 0.144087 | 351.498960 ± 0.106974 | -4.958339% | +14.087535% | 43.445349% |
| 8192 | 334.950067 ± 0.171860 | 352.263660 ± 0.141811 | -4.917743% | +13.847384% | 43.351037% |
| 32768 | 343.434050 ± 0.125321 | 358.112460 ± 0.157110 | -4.100820% | +12.682530% | 42.643015% |

汇总配对加速 **-4.659783887%**，耗时降低-4.887532330%（即增加4.887532330%），直接相对初始基线加速13.537487750%。15对全部回退，范围-5.039120%至-4.033971%，没有可记入顶部的局部正收益。拒绝并完整恢复063八文件，不重编译、不选择性重复。独立握手通过完整正确性，但性能数据不能把回退单独归因于commit、选举、调度或CLCempty延迟。当前最佳仍063（45.718103%/45.615939%/44.451126%），原45%全形状目标未完成；clean18保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-068-masked-clc-q/executable-plan.md)、[阶段模型](../../runs/main-clean-series-001/iter-068-masked-clc-q/lifetime-model-result.json)、[同步/native审核](../../runs/main-clean-series-001/iter-068-masked-clc-q/synchronization-review.md)、[CPU资格](../../runs/main-clean-series-001/iter-068-masked-clc-q/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-068-masked-clc-q/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-068-masked-clc-q/performance-audit-001.json)、[拒绝决定](../../runs/main-clean-series-001/iter-068-masked-clc-q/decision.json)、[恢复](../../runs/main-clean-series-001/iter-068-masked-clc-q/restoration.json)。


## Iter069 — 提前读取 CLC 响应（拒绝，恢复063）

父063。仅将原MMA线程对下一query的CLC wait/acquire读取移到最后一次QK提交后、倒数第二次PV前；原尾部SV等待、实际Q TMA发起位置和generic callback末尾CLC握手保持。计划先冻结，三项源变换可精确逆变换回063，config/common完全不变。阶段检查覆盖4086query/26994tiles、362880种Q事务顺序、27个依赖图、108个负控和252个早/晚响应状态；区分QK提交与完成，并能检测错误加入的跨query消费者依赖环。模型不代替GPU测试。

双架构隔离编译和正式构建通过。原生指令2848条（063为2832），168寄存器、零stack/local/spill，40MMA/48UTCCP/32gather/16Qload/3commit/1CLC/3CALL，无额外预取。CLC读取在0x6fc0，valid和x分别缓存于R18/UR12，保留0x7100的SV等待，随后有效分支发起8条Q TMA。实际正式包两个目标kernel的完整128bit native及非debug ELF与隔离结果一致，其余52个cubin与063逐字节相同。DSO `4c82bce71feb764342ff5b8d35f742741d6d7ea93fa410a7f1be20559d38b5b0`。

原316测试（314数值+2运行）、tail6、witness16和两版29诊断全部通过；87数组423174144元素逐位相同，未忽略NaNpayload或零符号差异。实际诊断报告各29attention/5finite+reference/15checkers，wrappers恢复、模块绑定稳定。测试仅改068→069标签和计划hash，原数值recipe/checker/tolerance/storage保持；CPU29cases/36负控及witness源审核通过。所有GPU监控有效。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原参数/seed/warmup/flush/cooldown/CUPTI协议不变。comparison001实际handle82656/ce4df8→128a55退出0，86次遥测未观察到竞争；9635f2从原330个时间区间重算6A5B/5pairs。SD为轮均值样本标准差。

| skv | 同批063均值±SD µs | 069均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.097633 ± 0.044209 | 334.677400 ± 0.146917 | -0.176148% | +19.821805% | 45.628999% |
| 8192 | 335.024483 ± 0.127254 | 335.490040 ± 0.069113 | -0.142614% | +19.539453% | 45.518474% |
| 32768 | 343.523533 ± 0.141871 | 345.481240 ± 0.262266 | -0.565211% | +16.802342% | 44.202096% |

汇总配对加速 **-0.294842213%**，耗时降低-0.295714103%（即耗时增加0.295714103%），直接相对初始基线加速18.713349181%。15对全部回退，范围-0.667351%至-0.093948%，无局部正收益。拒绝并恢复063全部八文件，不重编译，不重复不变候选。不能把回退单独归因于额外比较、缓存寄存器或等待位置。当前最佳仍063（45.718103%/45.615939%/44.451126%），全部原负载超过45%的目标未完成。新建clean19保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-069-early-clc-read/executable-plan.md)、[阶段模型](../../runs/main-clean-series-001/iter-069-early-clc-read/lifetime-model-result.json)、[同步/native审核](../../runs/main-clean-series-001/iter-069-early-clc-read/synchronization-review.md)、[正确性](../../runs/main-clean-series-001/iter-069-early-clc-read/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-069-early-clc-read/performance-audit-001.json)、[拒绝决定](../../runs/main-clean-series-001/iter-069-early-clc-read/decision.json)、[恢复](../../runs/main-clean-series-001/iter-069-early-clc-read/restoration.json)。


## Iter070 — O TMA写回优先淘汰缓存（局部收益，整体拒绝，恢复063）

父063。保持原TMA描述符、共享源地址、三维坐标、写回分块、election/fence/commit/wait，只在输出写回增加EVICT_FIRST缓存提示。Q原本已EVICT_FIRST，KV原本EVICT_LAST；假设输出流可能与重复使用KV竞争缓存。计划先冻结，源逆变换精确还原063，config/common不变；helper静态断言确保原src/dst总大小、mode0和TMAatom均4096元素，坐标rank3。CPU枚举8个8192B不重叠输出块，完整覆盖64×512，并保持hq1..64的同描述符边界裁剪。

隔离25062/8aff03→8bacb2、正式2111/7dac6b→3a1627、实际包91263/41e442→4925fd均成功。两架构2840sites（063为2832）、168寄存器、零stack/local/spill。4条静态UTMASTG保留原地址/坐标/描述符寄存器；只新增8条policy装载及4个hint，伴随4处独立指令局部换序。对这些变化及控制流地址重定位规范化后，全部2832条原指令操作/操作数逐项一致；这不代表调度控制位相同。063实际包的完整native128另经复核，与该参考逐位相同。070实际包native128/非debugELF同隔离，其他52cubin同063。DSO `9928dc9d949ec8543d4620ec9e123af207a2a6ad29b1c77c74ad94570643d996`。

原316（314数值+2运行，49808/1cb5b0→419b7a）、tail6/witness16/两版29诊断及全量差分（71466/3ad81e→0b8d0b）通过，87数组423174144元素逐位一致，无NaNpayload/零符号豁免。实际29attention/5finite+reference/15checkers、wrappers恢复与模块稳定通过；全部监控有效。仅069→070标签/计划hash适配，原数值recipe/checker/tolerance/storage不变；CPU29cases/36负控及witness源检查通过。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原参数/seed/warmup/flush/cooldown/CUPTI协议不变。comparison00148760/a61653→965a52有效，90次遥测未观察到竞争；53ef17从原330样本重算6A5B/5pairs。SD为轮均值样本标准差。

| skv | 同批063均值±SD µs | 070均值±SD µs | 配对加速 | 相对初始基线加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.992333 ± 0.080846 | 334.246320 ± 0.137832 | -0.078605% | +19.976340% | 45.687847% |
| 8192 | 334.899317 ± 0.176840 | 335.152620 ± 0.150397 | -0.079905% | +19.659802% | 45.564301% |
| 32768 | 343.562250 ± 0.216811 | 341.657280 ± 0.120758 | +0.547431% | +18.109639% | 44.696823% |

汇总配对加速 **+0.129205221%**，耗时降低0.129038497%，直接相对初始基线加速19.245795745%。32768组5对均提升0.507390%–0.579299%，是可记录的局部收益；其余两组各5对均负，量级约0.08%。汇总未达到严格>0.5%采用门槛，拒绝并完整恢复063八文件，不重编译、不选择性重复。不能由局部计时结果直接断定L2命中率、带宽或哪种缓存竞争是原因，需要新profile验证。当前最佳仍063（45.718103%/45.615939%/44.451126%）；070第三组也仅44.696823%，目标未完成。clean19保持干净。

证据：[计划](../../runs/main-clean-series-001/iter-070-output-evict-first/executable-plan.md)、[映射模型](../../runs/main-clean-series-001/iter-070-output-evict-first/store-mapping-model-result.json)、[源码/native审核](../../runs/main-clean-series-001/iter-070-output-evict-first/synchronization-review.md)、[父版native绑定](../../runs/main-clean-series-001/iter-070-output-evict-first/parent-native-binding.json)、[正确性](../../runs/main-clean-series-001/iter-070-output-evict-first/correctness-qualification.json)、[330样本复算](../../runs/main-clean-series-001/iter-070-output-evict-first/performance-audit-001.json)、[拒绝决定](../../runs/main-clean-series-001/iter-070-output-evict-first/decision.json)、[恢复](../../runs/main-clean-series-001/iter-070-output-evict-first/restoration.json)。


## 070后续：063 / 070 原32768完整NCU对照

两版各full/source采集有效，保持原包/原负载/固定GPU，clock-control none。070 DRAM读取下降4.3416%，L2命中率提高0.7155个百分点，支持缓存流量发生变化；不代替原330计时结论，070仍因汇总0.129205%低于采用门槛而拒绝。四份capture Q首次等待失败均0，KV/消费者QK等待仍突出；063部分PM组无实例，未填零或推断完整尾部。动态MMA/Qcopy/TMA工作一致，61个显式shared站点actual=ideal。完整指标、scope差异、失败的计数单位断言及修正、下一轮组合假设见[六维对照报告](../../profile/head64-iter063-vs070-cache/REPORT.md)。生产仍063，目标未完成。


## Iter071 — 消费者掩码/rowmax与输出缓存策略组合（拒绝，恢复063）

父063。在063保留提前Q加载的基础上，移植055完整消费者delta（提前全有效mask selector、BRX掩码回退、平衡FTZ rowmax树）及070输出TMA EVICT_FIRST。计划在编辑前冻结，并预声明两次完整原330交错比较，合并所有660样本/30配对；汇总和两次单独结果均须严格>0.5%，各形状不得出现超过0.1%的汇总回退。历史055/070收益不相加。

源变换能精确重建055/070，组合反向还原063。双架构隔离与正式构建成功，2848条指令、168寄存器、零stack/local/spill，共享222480+1024。实际native掩码40指令解释器、BRX表和冷重试、rowmax全部32输入及4级16节点、10022组FTZ/NaN/Inf/零符号bit模型通过。输出/producer/MMA连续代码区1910条指令，逐项操作/操作数同070（地址重定位后）；不声称全kernel调度位相同。CPU审核首次错误重定位未变化的0xc30分支目标，失败脚本与记录保留，修正审核后通过，未改kernel。正式包两个目标native128/非debug ELF同隔离，其余52cubin同063；DSO `86b6409ea0a34e49cb4d9052b4be8ee75637a9420b3e66fd421679678e8e20f9`。

原316（314数值+2运行）、tail6、witness16及两版29诊断均通过。87数组423174144元素逐位一致，无NaNpayload/零符号豁免；实际29attention/5finite+reference/15checkers、wrappers恢复、模块绑定稳定。数值recipe/checker/tolerance保持，CPU29cases/36负控通过。固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，全部监控有效，未观察到外部竞争。fresh clean20及18/19保持干净。证据：[冻结计划](../../runs/main-clean-series-001/iter-071-consumer-output-combined/executable-plan.md)、[源码/native资格](../../runs/main-clean-series-001/iter-071-consumer-output-combined/root-cpu-qualification.json)、[实际包核验](../../runs/main-clean-series-001/iter-071-consumer-output-combined/actual-package-audit.json)。

两次完整原330比较均完成，所有660原始时间区间及30邻接配对重算。每次保持6A5B/5pairs、原shape/seed/warmup/8GBflush/.3s冷却，不依据第一轮结果提前停止。SD为轮均值样本标准差。

| skv | 合并063均值±SD µs | 合并071均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.076242 ± 0.133789 | 334.729220 ± 0.175744 | -0.194422% | +19.803255% | 45.621935% |
| 8192 | 335.078475 ± 0.248541 | 335.642260 ± 0.352513 | -0.161386% | +19.485240% | 45.497831% |
| 32768 | 343.583608 ± 0.341994 | 341.784660 ± 0.560508 | +0.522118% | +18.065621% | 44.680164% |

| 比较 | 汇总配对加速 | 4096/8192/32768 配对加速 | 4096/8192/32768 理论峰值利用率 |
|---|---:|---|---|
| 001 | +0.042013122% | -0.190957% / -0.132582% / +0.450836% | 45.619319% / 45.512581% / 44.656782% |
| 002 | +0.067773699% | -0.197886% / -0.190181% / +0.593450% | 45.624552% / 45.483090% / 44.703571% |

合并汇总加速 **+0.054892581%**，耗时降低0.054862466%，直接相对初始基线加速19.115636879%。未满足预声明采用门槛，拒绝并完整恢复063全部八文件。原负载全部严格超过45%的目标仍未完成。收益为组合实测，不叠加历史055/070结果。无不变候选选择性重复。

证据：[正确性](../../runs/main-clean-series-001/iter-071-consumer-output-combined/correctness-qualification.json)、[第一轮330](../../runs/main-clean-series-001/iter-071-consumer-output-combined/performance-audit-001.json)、[第二轮330](../../runs/main-clean-series-001/iter-071-consumer-output-combined/performance-audit-002.json)、[660样本汇总](../../runs/main-clean-series-001/iter-071-consumer-output-combined/pooled-performance-audit.json)、[决定](../../runs/main-clean-series-001/iter-071-consumer-output-combined/decision.json)、[当前文件](../../runs/main-clean-series-001/iter-071-consumer-output-combined/restoration.json)。


## 071后续：063 KV流水线校准（profile证据，无优化采用）

在原seed312/32768输入、固定GPU上完成off-before、single-launch stagecapture、scout/traced/scout、off-after，四份监控均有效。关闭探针全部2832条native128同正式063；注入版3176条/167regs/零stack/local，capture与计时完整native128相同。三输出逐字节同063，4832records/24线程/16采样query完整，max240<256slots，覆盖四个producer warp。CUPTI设备区间150样本校准显示：traced相对相邻scout+1.618718%，相对off+1.883388%，整体低于2%检查线，但不约束局部probe扰动。独立loader/profile协议不替代原采用benchmark。

后续采样query的KV0/KV1 wait均值58.133/52.800ns，producer SV回收198.333ns，两半提交263.400/225.667ns，consumer QK324.800ns（首tile933.333，其余257.185）。不把并行时间相加，不从短scope推断全网格无访存等待。现有NCU Pfree首次失败3948次恰为4096−148，只是query转换假设，下一步须逐query验证Pfree/SO和消费者发布链路。停止无证据的Q/CLC或KV预取扫描。生产仍063，全部45%目标未完成，fresh clean20保持干净。详见[校准及阶段报告](../../profile/head64-iter063-kv-pipeline/REPORT.md)。


## Iter072 — 320线程保留全部工作角色（拒绝，恢复063）

父063。仅将config中的NUM_THREADS从384改为320；phase1/common逐字节不变。移除warp10/11，它们只参加一次初始CTA同步，随后没有工作；消费者warp0..3、四个producer warp4..7、MMAwarp8和mask/CLCwarp9保持。266CLC参与者、4个producer ack、64/128命名barrier、warp2 TMEM分配/warp3释放全部保留。不是016减少为两个producer的方案。计划在编辑前冻结，预声明两轮完整330比较、合并660样本；采用须汇总及两轮各严格>0.5%，无超过0.1%的汇总形状回退。

源码逆变换和角色模型32个选举lane/96个负控通过。两架构完整2832条native128（含调度控制位）与063相同，仍168regs、零stack/local/spill、共享222480+1024、40MMA/48UTCCP/32gather/16Qload/3commit/1CLC/4Ostore；ELF非debug变化仅两处maxthreads元数据384→320及规范化编译单元ID。因此没有获得预期的寄存器调度变化；实际只检验减少空闲warp的启动/资源效果，不宣称占用率翻倍。初次只读ELF辅助检查漏import hashlib，修正后通过，失败记录保留，未改kernel。

正式包DSO `24d63233af75c364f88d11bf7c818fffbdca472b9b09a09def936e7a339544b2`。实际包两个目标cubin完整native/非debugELF同隔离，其余52cubin同063；直接对实际父/候选cubin重验，全部.text字节相同、maxthreads元数据384→320。[实际父子绑定](../../runs/main-clean-series-001/iter-072-cta320/actual-parent-native-binding.json)。

原316（314数值+2运行）、tail6、witness16及两版29诊断均通过。87数组423174144元素逐位一致，无NaNpayload/零符号豁免；实际29attention/5finite+reference/15checkers、wrappers恢复、模块绑定稳定。数值recipe/checker/tolerance保持，CPU29cases/36负控通过。固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，全部监控有效，未观察到外部竞争。fresh clean20及18/19保持干净。证据：[冻结计划](../../runs/main-clean-series-001/iter-072-cta320/executable-plan.md)、[角色模型](../../runs/main-clean-series-001/iter-072-cta320/role-model-result.json)、[同步检查](../../runs/main-clean-series-001/iter-072-cta320/synchronization-review.md)、[CPU完整native资格](../../runs/main-clean-series-001/iter-072-cta320/root-cpu-qualification.json)。

两次完整原330比较均完成，所有660原始时间区间及30邻接配对重算。每次保持6A5B/5pairs、原shape/seed/warmup/8GBflush/.3s冷却，不依据第一轮结果提前停止。SD为轮均值样本标准差。

| skv | 合并063均值±SD µs | 合并072均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.059867 ± 0.145854 | 334.045030 ± 0.155332 | +0.004452% | +20.048635% | 45.715378% |
| 8192 | 334.908975 ± 0.125225 | 334.910890 ± 0.134541 | -0.001289% | +19.746169% | 45.597188% |
| 32768 | 343.392242 ± 0.152501 | 343.397620 ± 0.146247 | -0.005378% | +17.511059% | 44.470299% |

| 比较 | 汇总配对加速 | 4096/8192/32768 配对加速 | 4096/8192/32768 理论峰值利用率 |
|---|---:|---|---|
| 001 | +0.009719295% | +0.033341% / +0.020258% / -0.024433% | 45.723094% / 45.598328% / 44.468898% |
| 002 | -0.011194496% | -0.024428% / -0.022831% / +0.013681% | 45.707665% / 45.596049% / 44.471700% |

合并汇总加速 **-0.000738148%**，耗时降低-0.000738153%，直接相对初始基线加速19.096554813%。未满足预声明采用门槛，拒绝并完整恢复063全部八文件。原负载全部严格超过45%的目标仍未完成。本轮只改变CTA线程数量，未改变工作负载、数学或同步计数。无不变候选选择性重复。

证据：[正确性](../../runs/main-clean-series-001/iter-072-cta320/correctness-qualification.json)、[第一轮330](../../runs/main-clean-series-001/iter-072-cta320/performance-audit-001.json)、[第二轮330](../../runs/main-clean-series-001/iter-072-cta320/performance-audit-002.json)、[660样本汇总](../../runs/main-clean-series-001/iter-072-cta320/pooled-performance-audit.json)、[决定](../../runs/main-clean-series-001/iter-072-cta320/decision.json)、[当前文件](../../runs/main-clean-series-001/iter-072-cta320/restoration.json)。


## Profile063 Pfree/SO: 992记录完整，扰动2.529103%超过检查线

本轮采集和数值验证通过，阶段归因资格受限：打桩版本相对前后off增加2.529103%，超过预声明2%检查线。不能把观察到的短Pfree/SO等待当作生产kernel不存在等待的证明，也不能据此采用双P缓冲。下一步删除querybody探针，仅保留consumerQK/Pfree/SO，在新的冻结计划下重新校准。

生产仍为063，原benchmark32768理论利用率44.451126%，全部三组超过45%的目标未完成。这里的独立CUPTI计时不是采用benchmark，不换算目标利用率。

## 身份、正确性和覆盖

原seed312/sq4096/skv32768/topk640/hq64/hkv1/d512BF16/sinktrue/lengthfalse，固定GPU-847489a9-bc7e-726c-1c64-29c59e330fd8，物理7/逻辑0。原导出tensor哈希、三个输出均复核；成功采集scout/traced两次回调各仅launch一次，输出逐字节同正式063。四次有效GPU运行均经原kda_run三次空闲检查和持续进程监控，未观察到外部竞争。

关闭探针的2832条完整128bit机器指令逐项相同正式063；源变换精确可逆；scout168寄存器、零stack/local，注入版3136条、167寄存器、零stack/local；动态共享222480、驱动共享1024。单次capture与重复计时注入版完整native128相同。16个显式PTX分支守卫保护32个记录store，192槽环步长3072字节。

实际执行4096query；只采CTA0..3各前4逻辑query，每query10tile，8实际线程，992记录。每CTA消费者thread0有88记录，MMA warp8实际elected线程160记录，均未满192槽；本次实际elected线程恰为256，契约没有强制lane0。source推导的MMA结束顺序[10]+[10,11]*9+[11]逐query匹配。Pfree scope10对应QK k=0..9；SO scope11对应PV k-1=0..9，不能直接使用相同循环k作tile标签。buffer总4831838208字节，预算是共享ring，不是过滤器。

## 设备时间校准

沿用已验证CUPTI12.8 concurrent kernel activity采集器。每阶段3批、每批10warmup/10samples、8e9字节flush、0.3秒冷却；150样本，逐批10目标kernel记录、正start/end、零丢失、grid4096/block384/shared222480。Python3.12/CuPy独立loader及显式同步与原Python3.11/kernelkit不同，属于profile校准。重复计时trace不用于阶段分析。

| 阶段 | 均值 µs | 单样本SD µs |
|---|---:|---:|
| off-before | 339.946933 | 1.508585 |
| scout-before | 339.795800 | 1.189184 |
| traced | 348.603167 | 1.403654 |
| scout-after | 339.937800 | 1.595995 |
| off-after | 340.061300 | 1.513289 |

traced/scout增加2.570529%，traced/off增加2.529103%；off漂移+0.033643%，scout漂移+0.041790%。整体扰动超过2%检查线；局部探针可延迟到达wait而隐藏原有等待，不能统一减去全局开销修正scope。

## 打桩后的等待分布，仅作后续设计依据

以下为官方SDK预计算gpu ns统计，后续指采样query1..3，并非全网格稳态。原始timestamp只用于顺序验证，未手算跨线程duration。并行角色不可相加为关键路径。

| scope | 后续全tile均值 ns | p50 | p95 | tile0均值 | tile1均值 | tile2..9均值 |
|---|---:|---:|---:|---:|---:|---:|
| MMA P free | 65.600 | 64.000 | 128.000 | 40.000 | 138.667 | 59.667 |
| MMA SO ready | 56.533 | 64.000 | 64.000 | 77.333 | 48.000 | 55.000 |
| consumer QK ready | 300.533 | 256.000 | 832.000 | 845.333 | 290.667 | 233.667 |

观察到Pfree tile1较长，而非tile0；这与query切换假设相容，但不能把16query的打桩样本映射为NCU全部3948次事件。Pfree/SO多数短等待不构成新增双缓冲的充分依据。历史048双P在046上回退0.259568%，不直接移植。

## 失败记录与下一步

capture-001在JIT之前的CPU断言失败：检查脚本沿用256槽的4096字节步长，而本次192槽正确步长为3072。实际注入PTX本来正确；仅执行scout，输出正确，没有traced结果。该次monitor为command_failed，不能作为有效stage样本。原文件、日志、prelaunch哈希全部保留于[失败归档](../../profile/head64-iter063-pfree-so/analysis/capture-001-failure.json)。新capture-v2/calibrate-v2/run-profile-v2只修正审核步长并使用capture-002独立目录，kernel/source/构建/采样预算不变；capture-002有效。

下一步在新计划下删除5个内联角色的querybody START/END共10处静态探针，只保留6处QK/Pfree/SO markers。保留query计数和原采样窗口，消费者按每10次QK推导query，独立契约960记录。重新证明off-native相同，重新测150样本扰动，不能从“探针更少”假定开销下降。若仍高扰动，停止扩大该trace归因并转向原生SASS/NCU证据。

[交互HTML](../../profile/head64-iter063-pfree-so/reports/capture-002/trace.html) · [JSON](../../profile/head64-iter063-pfree-so/reports/capture-002/trace.json) · [完整验证](../../profile/head64-iter063-pfree-so/analysis/verified-results.json) · [冻结计划](../../profile/head64-iter063-pfree-so/harness/executable-plan.md) · [覆盖](../../profile/head64-iter063-pfree-so/analysis/coverage-001/result.json)。生产063八文件和main-clean-18/19/20/21均复核未改；无优化采用或提交。


## Profile063 minimal Pfree/SO: 960记录完整，扰动2.969399%，停止密度扫描

本轮有效采集960条记录，数值、身份、覆盖与GPU监控均通过；150个设备时间样本显示traced/off增加2.969399%，仍高于预声明2%检查线。删除querybody标记没有带来足够低扰动的测量。按冻结计划停止这条探针密度扫描；这不是kernel优化失败，也不是Pfree/SO无瓶颈的证明。当前不依据这些trace采用双P缓冲或删同步。

当前最佳仍063，原benchmark32768理论利用率44.451126%，全部三组严格超过45%的目标未完成。两个Pfree/SO profile合计300个设备时间样本，均属于独立Python3.12/CuPy/CUPTI校准，不代替原Python3.11/kernelkit采用协议，不据此换算目标利用率。

## 变更、身份和验证

相比上一份profile，仅删除querybody START/END的10处内联静态标记，保留query计数和CTA0..3/各前4query窗口。只留下consumerthread0 QKwait、MMAwarp8实际elected线程Pfree/SO。原所有barrier、phase、算术、地址、source生产文件均不改。关闭探针的2832条完整native128指令同正式063，源码逆变换字节精确；scout168寄存器、零stack/local；注入版2968条、168寄存器、零stack/local，capture和timing完整native128相同。6个显式PTX分支守卫保护12个SDK记录store，192槽ring，wrap3072字节，总buffer4831838208字节。

原seed312/sq4096/skv32768/topk640/hq64/hkv1/d512BF16/sinktrue/lengthfalse，固定B200 GPU-847489a9-bc7e-726c-1c64-29c59e330fd8（物理7/逻辑0）。四次GPU任务均由原kda_run执行，三次空闲检查和全程进程监控有效，未观察到外部竞争；所有原tensor哈希及三输出逐字节同正式063。

阶段来自独立单次traced launch，SDK两次回调scout/traced各只launch一次。全4096query执行，采样16query、8线程、960记录。每CTA消费者80记录，MMA160，最大160<192；consumer每10次QK推导query，MMA每query严格[10]+[10,11]*9+[11]。Pfree对应QK k=0..9，SO对应PV k-1=0..9。逻辑query序号不等于CLC实际s_q_idx；两次profile没有记录并配对各CTA的具体query ID，不能把两份逐tile均值之差完全归因于探针变化。

## 150样本纯设备计时

已验证CUPTI12.8 concurrent kernel start/end采集器，零丢失，每批恰好10个目标kernel，grid4096/block384/dynamicshared222480。每阶段3批，每批10warmup/10samples、8e9字节flush、0.3秒冷却；前后off与scout对照。下面SD是30个单样本的标准差。重复计时产生的trace明确不用于stage证据。

| 阶段 | mean µs | median µs | SD µs | min µs | max µs |
|---|---:|---:|---:|---:|---:|
| off-before | 339.781600 | 339.439000 | 1.539555 | 337.247000 | 344.223000 |
| scout-before | 339.777767 | 339.423500 | 1.196726 | 338.399000 | 343.519000 |
| traced | 349.887667 | 348.767500 | 3.630572 | 346.495000 | 367.104000 |
| scout-after | 339.719000 | 339.344000 | 1.342686 | 338.272000 | 343.647000 |
| off-after | 339.813833 | 339.631000 | 1.480702 | 337.440000 | 343.711000 |

traced/scout增加2.984351%，traced/off增加2.969399%；off漂移+0.009486%，scout漂移-0.017296%。traced样本含367.104µs高值，监控未发现外部竞争，全部保留；未剔除离群点或选择性重测。全局平均超线，局部扰动也未被约束，等待scope不能等同可节省时间。

## 打桩后的阶段统计

官方SDK预计算gpu ns，后续仅指query ordinal1..3；每个tile12次等待。不手算rawtimestamp duration，不相加不同角色scope为关键路径。范围不覆盖晚期query或全网格尾部。

| scope | 后续全tile mean ns | p50 | p95 | tile0 mean | tile1 mean | tile2..9 mean |
|---|---:|---:|---:|---:|---:|---:|
| MMA P free | 69.867 | 64.000 | 128.000 | 48.000 | 208.000 | 55.333 |
| MMA SO ready | 59.733 | 64.000 | 64.000 | 56.000 | 56.000 | 60.667 |
| consumer QK ready | 276.800 | 256.000 | 576.000 | 637.333 | 162.667 | 246.000 |

| logical tile | Pfree mean / p95 ns | SO mean / p95 ns | QKwait mean / p95 ns |
|---:|---:|---:|---:|
| 0 | 48.000 / 64 | 56.000 / 64 | 637.333 / 1120 |
| 1 | 208.000 / 320 | 56.000 / 64 | 162.667 / 416 |
| 2 | 45.333 / 64 | 56.000 / 64 | 218.667 / 320 |
| 3 | 53.333 / 64 | 58.667 / 64 | 226.667 / 256 |
| 4 | 58.667 / 64 | 58.667 / 64 | 250.667 / 288 |
| 5 | 53.333 / 64 | 66.667 / 64 | 253.333 / 288 |
| 6 | 56.000 / 64 | 61.333 / 64 | 248.000 / 288 |
| 7 | 56.000 / 64 | 64.000 / 64 | 245.333 / 288 |
| 8 | 61.333 / 64 | 61.333 / 64 | 261.333 / 288 |
| 9 | 58.667 / 64 | 58.667 / 64 | 264.000 / 288 |

两种采样都出现Pfree tile1较长、tile0较短，但均不足以将NCU3948次首次未就绪一一映射到生产query转换。SO和大多数Pfree落在短区间，意味着当前数据没有支持“普遍长时间等待S发布/单P释放”的证据；它们也不能排除探针延迟到达wait而隐藏真实等待。历史048双P在046上回退0.259568%，当前没有足够的新证据直接移植。

## 决定与下一步

停止继续调整同一SDK的探针密度，保留本轮完整结果及上一轮首次capture审核失败。SASS tracing旧049已有SDK序列化失败，不在未改变工具或路径的情况下盲目重试。没有新增优化采用、原benchmark或正确性测试修改。

下一步先做只读CPU原生指令成本审查：从正式063的MMA循环与consumer QK路径出发，按实际分支恢复k0、k1..9、k10及query边界的地址/descriptor构造、同步和MMA发射顺序；结合已有063有效NCU各PC动态访问次数核算。检查是否存在无需改变数学和生命周期的重复地址计算或发射依赖，再决定单一候选。这个方向目前是待验证假设，不承诺收益；不能仅由scope较大或静态指令较多推出瓶颈。排除已拒绝的037/038 producer状态缓存、048双P、064–069 Q/CLC迁移和072线程数量扫描的重复设计。任何候选仍需独立冻结计划、双架构native/生命周期证明、全正确性与原330严格>0.5%采用门槛。

[交互HTML](../../profile/head64-iter063-pfree-so-minimal/reports/capture-001/trace.html) · [trace JSON](../../profile/head64-iter063-pfree-so-minimal/reports/capture-001/trace.json) · [完整验证](../../profile/head64-iter063-pfree-so-minimal/analysis/verified-results.json) · [覆盖](../../profile/head64-iter063-pfree-so-minimal/analysis/coverage-001/result.json) · [冻结计划](../../profile/head64-iter063-pfree-so-minimal/harness/executable-plan.md) · [上一份有限归因报告](../../profile/head64-iter063-pfree-so/REPORT.md)。生产063八文件与main-clean-18/19/20/21保持原状。


## 073：MMA 前一 KV 槽缓存（回退，拒绝，恢复063）

父063。只在MMA线程缓存前一KV槽，原全局ring、数学、同步和调度保持。源码逆变换精确，隔离及正式包双架构通过；2824静态指令槽（父2832）、168寄存器、零stack/local/spill，384线程/266CLC workers/4 producer acks不变。完整G10稳态路径2910→2869、首次含启动3003→2983；静态成本下降仅为CPU资格门槛，实测显示不能据此预测收益。

原316（314数值+2运行）、tail6、witness16及两版各29诊断通过，87数组423174144元素逐位一致，无NaN payload/零符号豁免。原checker/tolerance/seed/recipe不变。073正式DSO `d40f165a735326438fa0a210191de8161ad70a1141902ca883991690fdaefd8b`，两个目标cubin同隔离完整native128/非debug ELF，其他52cubin同063。

固定B200 `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原三负载、6A5B/5邻接配对/330样本，warmup/8e9字节flush/0.3秒冷却不变。六次GPU任务监控全部有效，无外部竞争；性能监控89次遥测。SD为轮均值的样本标准差。

| skv | 同批063均值±SD µs | 073均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.128183 ± 0.057289 | 340.844540 ± 0.077868 | -1.969906% | +17.653784% | 44.803402% |
| 8192 | 335.056950 ± 0.124075 | 341.685900 ± 0.157377 | -1.939698% | +17.371820% | 44.693079% |
| 32768 | 343.498150 ± 0.089030 | 350.620740 ± 0.225113 | -2.029883% | +15.090220% | 43.554169% |

汇总配对加速 **-1.979836086%**，耗时降低-2.019825317%（即耗时增加2.019825%），直接相对初始基线加速16.699605107%。全部15对回退，范围-2.121055%至-1.877465%。拒绝073并从归档精确恢复063八文件，无重编译、无选择性重复。没有新增可收录的局部收益。最佳仍063，32768形状44.451126%，全目标未完成。main-clean-18/19/20/21/22含忽略文件均保持干净。

CPU审计共覆盖2176个MMA操作数路径、1152个等待地址/phase路径、896个Q拷贝路径和1024个query尾部路径；其他角色2147条/架构的high64一致，low64变化仅控制流重定位。所有工具解析失败及修订均存档：父cubin子目录、MOV R2常量分类、WARPSYNC continuation、RET相对重定位，详见本轮报告；均不改变候选或原协议。更正此前分类：037/038为consumer previous-SV缓存，并非producer；本轮为MMA issuer缓存。

下一步先以既有正式063 full/source报告为对照，审核073真实MMA循环的数据依赖和发射/等待证据，解释为何较少指令却更慢。需要新profile时先冻结实际包/原负载/固定GPU的采集计划；不直接再扫描缓存写法、Q/CLC位置或探针密度，不把本轮回退直接归因于某个未经测量的stall。

证据：[本轮报告](../../runs/main-clean-series-001/iter-073-mma-prev-slot/REPORT.md)、[完整CPU资格](../../runs/main-clean-series-001/iter-073-mma-prev-slot/root-cpu-qualification.json)、[正式包](../../runs/main-clean-series-001/iter-073-mma-prev-slot/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-073-mma-prev-slot/correctness-qualification.json)、[330复算](../../runs/main-clean-series-001/iter-073-mma-prev-slot/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-073-mma-prev-slot/decision.json)、[恢复](../../runs/main-clean-series-001/iter-073-mma-prev-slot/restoration.json)。


## 073回退诊断：循环尾部新增计算与发射依赖（无新优化采用）

原073正式包完成full47/source5 NCU采集，对照已有有效063同负载报告，固定UUID、原seed312和32768负载。两个监控有效，2823个可用PC逐项匹配实际073 SASS。生产063和干净worktree未变。

资源、occupancy、内存流量和L2hit基本不变；eligible从0.564492降至0.537458、issue从41.760654%降至40.605438%。073在最后PV之后重新计算缓存槽，循环尾部动态指令495616→675840；新0x7570在full/source有193/196个short-scoreboard样本，父版尾部0/0。父版QK入口也有126/135个该类样本，不能把新热点全部当作额外延迟；MMA总量368/363→433/434。KV1首次未就绪7584/8418→12282/12809，是事件次数而非等待时长。未证明具体硬件hazard或全部2%损失归因。

PM triage两版均缺失，073 long-scoreboard时间轴缺失，不比较完整尾部。NCU时间不用于采用门槛。下一项仅考虑CPU审核的QK分支内缓存更新，避免PV后新增除3链；另行冻结计划，实际代码不满足门槛则CPU拒绝。没有新收益、没有改变benchmark或正确性要求。

[完整对照报告](../../profile/head64-iter073-vs063-mma-dependency/REPORT.md) · [原始073报告](../../profile/head64-iter073-mma-dependency/REPORT.md) · [逐PC/API比较](../../profile/head64-iter073-vs063-mma-dependency/analysis/comparison.json)


## 074：QK分支内保存前一槽缓存（有小幅收益，未达采用门槛，恢复063）

父063。根据073已归档的PV后槽号重算及short-scoreboard热点证据，将缓存更新限定在原QK分支内，PV使用进入本轮时的旧槽快照。原global ring、数学、同步/CLC和所有其他角色保持；source逆变换精确。两架构2816静态槽（父2832）、168寄存器、零stack/local/spill。完整G10稳态2910→2837、首次含启动3003→2951，PV后的新增除3链消失；指令数减少本身不证明周期收益。

源模型4352例、原生操作数2176例及实际缓存10880次检查、同步地址/phase1152例、Q搬运896例、query尾部1024例全部通过。其他角色2147条/架构的128位编码仅40处控制转移low64因重定位变化，high64全部一致。384线程/266 CLC workers/4 producer acknowledgements、222480动态shared+1024驱动shared及512 TMEM列保持。

正式构建成功，两个目标cubin完整native128/非debug ELF同隔离构建，其他52cubin同063。原316（314数值+2运行）、tail6、witness16及两版各29诊断通过；87数组423174144元素逐位相同，无NaN payload/零符号豁免。原checker/tolerance/recipe不变。

固定B200 UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；原sq4096/topk640/hq64/hkv1/d512 BF16、skv4096/8192/32768、seed310/311/312、sink启用/length关闭。原6A5B、5邻接配对、330样本，10warmup、8e9字节flush、0.3秒冷却均不变。六次GPU任务监控全部有效，无外部竞争；遥测22/10/10/65/69/91条。SD为轮均值的样本标准差。

| skv | 同批063均值±SD µs | 074均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.971833 ± 0.096234 | 332.516260 ± 0.086631 | +0.437365% | +20.600569% | 45.925558% |
| 8192 | 334.848300 ± 0.127855 | 333.513660 ± 0.123940 | +0.399205% | +20.247836% | 45.788214% |
| 32768 | 343.295550 ± 0.227168 | 342.893520 ± 0.122828 | +0.113829% | +17.683816% | 44.535676% |

汇总配对加速 **+0.316695975%**，耗时降低0.315696178%，直接相对初始基线加速19.503637029%。15个配对均为正，范围0.023017%至0.484881%；这些是本次完整五对交错比较的观测，未将小幅变化提升为跨会话复现声明。汇总低于严格>0.5%采用门槛，32768利用率仍低于45%，拒绝074。记录小幅收益但不采用，不选择性重复，不叠加其他候选的收益。

已从063归档精确恢复源码和包共八文件，无重编译；074全部源码、工具、日志和实际产物保留。main-clean-18至23含忽略文件保持干净。当前最佳仍063，采用时三形状利用率45.718103%/45.615939%/44.451126%，全目标未完成。

本轮说明：消除073的PV后新增槽号计算避免了该候选的明显回退，但跨批次比较不能证明全部差异都由该指令链造成。074的最大形状收益仅0.113829%，指令减少未转化为足够的目标负载加速。下一步先审查063生产者的实际地址/描述符计算和已有PC动态计数，排除049已前移索引和017/039已试循环方案；只在找到具体重复依赖及完整成本收益时冻结新候选。037/038是consumer前一SV槽缓存，不据此误排除producer；不直接再次扫描MMA缓存写法、Q/CLC位置或探针密度。当前没有075候选或新GPU任务。

正式DSO `c420be74e3d01ea16e5d4ec252a6df48307931c818b1c67ca08882ab1869285a`。证据：[冻结计划](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/root-cpu-qualification.json)、[正式包](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/correctness-qualification.json)、[330复算](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/decision.json)、[恢复](../../runs/main-clean-series-001/iter-074-qk-scoped-prev-slot/restoration.json)。

## 075：生产者最终tile在索引交接前退出（CPU成本门槛失败，拒绝）

父063，生产八文件全程未改。根据真实063尾部索引合并及既有PC数据，先冻结计划，再只将producer尾部改为rs.update后!have_next直接break，其余轮无条件交接next_indices。原gather顺序、049预加载、skip、alias/SV/Odone/CLC同步及所有其他角色源码保持。源码逆变换字节精确。

6120源模型案例覆盖13600 query、68000 tile，包含G2/3/5/10连续query组合、17ring起点、4producer warp和五种有效性模式，四负控均检出。NVCC13.1完整TU两架构编译通过，2832静态槽、168寄存器、零stack/local/spill。编译器确实消除了15组旧值合并，但索引寄存器分配使gather参数准备增长，未通过冻结的完整CPU成本门槛。

| 路径/区域 | 063 | 075 | 差值 |
|---|---:|---:|---:|
| gather准备/发射含退出分支，每tile | 338 | 370 | +32 |
| 索引交接含回边，每tile | 50 | 27 | -23 |
| G2完整稳态query | 918 | 929 | +11 |
| G3完整稳态query | 1340 | 1360 | +20 |
| G5完整稳态query | 2182 | 2220 | +38 |
| G10完整稳态query | 4287 | 4370 | +83 |
| G10首次query含启动 | 4295 | 4378 | +83 |

两架构一致。表中有效首索引、无长度指针、继续query、wait首次成功；长度指针有无及终止/继续的四种G10组合全部+83。完整记录同时包含fallback-gather/skip、k1/k2 alias、SV、短query Odone及CLC的显式cold路由。计数为遇到的原生指令槽，含predicate关闭的指令，不是周期预测或运行变慢的证据。

gather中的MOV.SPILL/R2UR.FILL各22→48，增加26对；这是uniform寄存器与通用寄存器间搬运，不能称为local-memory spill，资源报告仍为零stack/local。其他opcode变化也已纳入完整338→370的成本，未仅以这一局部变化代替全路径分析。尾部虽然没有条件合并，编译器仍把对最终轮已无用的寄存器交接排在退出测试附近，源码break不等于原生指令必定被跳过。

按冻结停止条件，拒绝075，不继续修改同一候选，不运行正式构建和GPU。完整新gather操作数/同步/其他角色native128资格没有继续执行，不能记作通过。三原负载的耗时、波动、对父/初始收益及理论利用率全部N/A。未新增已验证收益；当前最佳仍063，32768采用时44.451126%，全目标未完成。main-clean18至23含忽略文件均干净。

本轮审计失败已归档：只读研究的AST字面量提取和15R2UR+1MOV分类修正；075成本审计首次使用了错误的063冷路径重定位，实际retry分支为aec0/af10/af60/afb0，已在新版本修正并跑通所有显式cold路由。早期只读研究的热路径成本和PC聚合不受此冷路径标注错误影响，冻结证据保留原样并附更正。

下一步先对063/075实际gather参数包的定义、最后使用及MOV.SPILL/R2UR.FILL位置作只读生命周期对照，确定为何减少loop-exit合并反而增加参数包保存。未提出076源码方案，不直接扫描unroll、gather顺序或MMA缓存写法；后续实现必须由具体依赖及完整成本门槛支持。

证据：[计划](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/executable-plan.md)、[源码差异](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/source-edit.diff)、[模型](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/lifetime-model-result.json)、[完整成本](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/native-cost.json)、[CPU资格结论](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/root-cpu-qualification.json)、[成本审计首次失败](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/native-cost-attempt001-failure.json)、[决定](../../runs/main-clean-series-001/iter-075-producer-terminal-before-handoff/decision.json)。

## 076：连续四列静态gather参数块（机器码完全相同，CPU拒绝）

父063，主八文件全程未改。先完成063/075 gather值生命周期对照：两架构48条32-gather路径的实际参数传播通过；075有8个当前索引字驻留UR，保存的后续row值由17对增至36对、列值4对增至8对，其余无后续gather用途1对增至4对，总22→48。这里是uniform/general寄存器搬运，资源中local/stack仍为零；没有证明分配器内部决策或硬件stall因果。

076单独从063将每组同一行索引的连续四列gather写成一个静态inline PTX块，局部目的地址每步+8192字节、列+64，保持原32条gather、行/half顺序、descriptor/barrier/policy、049lookahead和条件索引handoff。没有带入075终止分支，没有运行时列循环。计划先冻结，源逆变换精确；实际生成PTX解析模型96序列/3072gather事件与原公式一致，dst/col/rows/barrier四负控均检出。

NVCC13.1原完整TU两架构编译成功。对实际cubin重新cuobjdump，并逐PC核对完整128位编码：SM100a和SM103a各2832个槽全部与063相同，包括指令调度控制位和其他角色。REG168、STACK0、LOCAL0、drivershared1024；原40MMA/48UTCCP/32gather/3commit/3CALL/16Qload/1CLC/4Ostore不变。相同机器码使已验证063的所有CFG路径（含cold retry）成本相同，无需把同一代码重新放上GPU评测。

| 完整producer路径 | 063 | 076 | 差值 |
|---|---:|---:|---:|
| G2稳态 | 918 | 918 | 0 |
| G3稳态 | 1340 | 1340 | 0 |
| G5稳态 | 2182 | 2182 | 0 |
| G10稳态 | 4287 | 4287 | 0 |
| G10首次含启动 | 4295 | 4295 | 0 |

表为valid-first、无长度指针、继续query、wait首次成功的遇到指令槽。完整48种query组合继承已验证063路径，并由全体机器码相同证明同成本；不是076新运行时间。gather338、handoff50也不变。编译器把新的源码表达归一化为既有实现，严格更低成本门槛未通过，拒绝076。

正式构建、GPU正确性及三负载耗时/波动/父版与初始收益/理论峰值利用率全部N/A；无新增已验证收益。源代码、产物和全部证据保留，生产063八文件与main-clean18..23含忽略文件均保持原状，32768目标仍未达到45%。075研究工具两次失败（缺0x398常量绑定、入口未定义UR31）保留并以显式输入/unknown传播修正；076自身模型和构建无失败。

本轮已排除仅靠静态PTX参数表达改变机器码的方向。下一步先只读核对当前KV tensor-map的L2 promotion设置及既有full/source中的请求、sector和DRAM流量，判断访存粒度是否还有具体机会；没有提出077，没有改变缓存设置。不会继续重复075退出写法、076等价PTX写法或既有gather循环/顺序扫描。

证据：[冻结计划](../../runs/main-clean-series-001/iter-076-producer-gather-quad/executable-plan.md)、[源差异](../../runs/main-clean-series-001/iter-076-producer-gather-quad/source-edit.diff)、[模型](../../runs/main-clean-series-001/iter-076-producer-gather-quad/packet-model-result.json)、[全机器码/成本](../../runs/main-clean-series-001/iter-076-producer-gather-quad/native-cost.json)、[CPU结论](../../runs/main-clean-series-001/iter-076-producer-gather-quad/root-cpu-qualification.json)、[决定](../../runs/main-clean-series-001/iter-076-producer-gather-quad/decision.json)。

## 063补充：KV tensor-map填充粒度证据（CPU只读重分析）

既有正式32768 full报告经ncu_report API重读，TMA L2→L1TEX bytes2,952,790,016恰等于Q+KV逻辑载荷。DRAM读335,233,792B，L2 throughput36.494762%；不支持大量重复传输或DRAM带宽饱和诊断。promoted-data miss678不是总overfetch字节。256B promotion虽大于单个128B行片段，所有八片段最终消费整行，因此有空间复用，不能直接断言128B更快。仅冻结一次128B单参数对照077，避免NONE/64B扫描。063生产八文件在研究阶段精确，main-clean18..24含忽略文件干净，无新增收益。

[审查报告](../../profile/head64-iter063-kv-promotion-audit/REPORT.md) · [实际API结果](../../profile/head64-iter063-kv-promotion-audit/analysis/result.json)。

## 077：KV tensor-map L2 promotion128B（未达采用门槛，恢复063）

父063。基于既有32768 NCU流量审查，仅把host KV descriptor的promotion256B改为128B，匹配实际gather行片段。没有把TMA逻辑载荷或678 promoted-data miss sectors误当DRAM过量读取证据；全部八列片段最终消费完整行，256B本身可能有空间复用。此次检验填充粒度/延迟假设，不改swizzle、eviction、tile、math、gather顺序或同步。

先冻结计划，再生成隔离源码；逆变换精确。NVCC13.1两架构各2832条完整128位机器码与063一致，168寄存器、零stack/local/spill。host主.text13625字节只在0xa3d有一字节3→2，完整重定位相同；这是实际编码调用第11参数。正式包目标device完整native/nondebug同隔离产物，其他52cubin精确同063；实际linked host参数片段确认128B。384线程、266CLC workers、4producer acknowledgements、222480动态+1024driver shared及512TMEM保持。

原316（314数值+2运行）、tail6、witness16和两版各29诊断通过；87数组423174144元素逐位相同，无NaN payload/零符号豁免。原checker/tolerance/recipe和benchmark参数未改。

固定B200 UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512 BF16、seed310/311/312、sinktrue/lengthfalse。原6A5B/5邻接配对、330样本、10warmup、8e9flush和0.3秒冷却。监控均有效，无外部竞争。SD是轮均值样本标准差。

| skv | 同批063均值±SD µs | 077均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.831483 ± 0.102056 | 333.924560 ± 0.128228 | -0.028355% | +20.091945% | 45.731871% |
| 8192 | 334.772000 ± 0.126175 | 334.708320 ± 0.060428 | +0.018166% | +19.818641% | 45.624784% |
| 32768 | 343.190050 ± 0.180559 | 343.153620 ± 0.205000 | -0.001012% | +17.594615% | 44.501920% |

汇总配对加速 **-0.003735654%**；耗时降低-0.003735794%；直接相对初始加速+19.163129913%。15个配对范围-0.083798%至+0.078911%。三形状全部超过45%：False。汇总未超过严格0.5%采用门槛，拒绝077；无选择性重复，不将小幅或符号不一致变化声明为可复现收益。

两次CPU工具输出用法问题及一次绑定文件缺失均归档：witness拒绝--output、diagnostic只写stdout；原审计改用stdout重定向后通过。第一次诊断CPU stdout已通过后，缺失保存文件使绑定准备报错，shell随后启动原316测试；formal资格此前已完成，实际runtime bindings在诊断GPU前安装。没有修改checker或隐藏失败，所有GPU阶段有效。

已精确恢复063源/包八文件，无重编译；候选源码、实际产物和全部日志保留。main-clean18..24含忽略文件干净。当前最佳仍063，采用时45.718103%/45.615939%/44.451126%，目标未完成。此次结果只判定128B单参数候选，不证明填充粒度完全无影响。下一步先核对既有不同skv下的缓存驻留和等待证据是否能定位最大形状额外耗时；不继续扫描NONE/64B或重复既有cache-hint方向。

正式DSO `8c81749375952cc2e1b50c787bde394d820be860d9284ef68797d2528f490518`。证据：[计划](../../runs/main-clean-series-001/iter-077-kv-promotion128/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-077-kv-promotion128/root-cpu-qualification.json)、[实际正式包](../../runs/main-clean-series-001/iter-077-kv-promotion128/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-077-kv-promotion128/correctness-qualification.json)、[330复算](../../runs/main-clean-series-001/iter-077-kv-promotion128/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-077-kv-promotion128/decision.json)、[恢复](../../runs/main-clean-series-001/iter-077-kv-promotion128/restoration.json)。

## 063补充：原8192与32768形状对照（诊断完成）

新增同正式063的原8192/seed311 full/source NCU，固定UUID、原runner和clock-control none，监控有效。两形状关键MMA/Qcopy/gather/Qload/Ostore次数及TMA载荷相同；32768 DRAM读多47,861,248B，evict_last read miss398512→3146648 sectors，但带宽未饱和。19类等待的first-fail/冷循环实际计数不支持把额外耗时直接归因到KV等待变长，旧32768 PM triage缺失也限制尾部解释。两个case使用不同原seed，保留这一限制。

两形状共有约41万次MMA KV0冷try检查，下一项限定评估单elected线程在该位置的acquire test_wait轮询；不是把sleep事件换算为周期，不继续缓存参数扫描。生产仍063，无新增收益；冷循环解析初次producer Qcopy内联路径假设错误已归档并修正，四capture×19类计数守恒全部通过。

[完整六维报告](../../profile/head64-iter063-kv8192-shape-control/REPORT.md) · [逐PC/流量](../../profile/head64-iter063-kv8192-shape-control/analysis/shape-comparison.json) · [冷路径事件](../../profile/head64-iter063-kv8192-shape-control/analysis/cold-retries.json)。

## 078：MMA KV0 acquire test-wait（热路径数据指令增加，CPU拒绝）

父063。基于原8192/32768同正式包的cold-loop证据，限定替换MMA warp8单elected线程在KV第一半段的wait为非阻塞acquire test_wait轮询。原barrier地址/phase、arrive/transaction字节、后续tcgen05 fence、KV1及全部其他同步保持。没有带入077的128B promotion。该方向旨在检验等待实现开销，busy polling可能增加issue争用，不能用旧sleep事件数预测收益。

计划先冻结，源逆变换精确。初次隔离构建40134/ced47d→18c58a退出255：bar_phase为bool，PTX r约束需要32位；原CUTLASS wait(uint32_t)会隐式扩宽。已归档原源码/生成器/日志，冻结仅加uint32_t(bar_phase)的类型修复说明后重编译，未改变0/1值、同步位置或候选算法。

attempt002由原NVCC13.1完整TU两架构编译84380/72b908→1027e3退出0。初步codegen审核910145/0：两架构2840静态槽（063为2832）、168REG、STACK/LOCAL0、driver shared1024；40MMA/48UTCCP/32gather/3commit/3CALL/16Qload/1CLC/4Ostore保持。实际0x62b0为SYNCS.PHASECHK.TRANS64，0x62c0未就绪跳回0x62b0，前0x6290保持同KV0地址的arrive；该循环无NANOSLEEP。

完整热路径审计已核实两个实际cubin与编译清单及cuobjdump输出。每版本/架构覆盖G=2/3/5/10、首次/稳态、继续/终止共16种query组合，校验query范围全部分支以及8条原cold wait路由和新KV0两指令poll。

| G10路径 | 063指令槽 | 078指令槽 | 增量 |
|---|---:|---:|---:|
| 稳态、终止 | 2866 | 3134 | +268 |
| 稳态、继续 | 2910 | 3189 | +279 |
| 首次含启动、终止 | 2959 | 3238 | +279 |
| 首次含启动、继续 | 3003 | 3293 | +290 |

两架构一致。稳态继续路径的数据槽2676→2955；主要opcode变化为R2UR +150、IMAD.MOV.U32 +100、UMOV +76、MOV +21，另有UIADD3等减少，净增279。wait首次成功时TRYWAIT −10、PHASECHK +10，不能解释等待之外的数据指令增长。计数包含predicate关闭的遇到槽，不是周期或运行变慢的实测证据；没有推断编译器分配器内部原因。

冻结计划要求完整原热路径不增加等待之外的数据指令，该门槛失败，拒绝078。完整操作数/同步/其他角色资格未继续完成；正式构建、GPU数值正确性、三原负载耗时与波动、相对父/初始收益、理论利用率全部N/A。此结论只拒绝当前实现，不证明所有test_wait方案无效。

生产063源/包八文件全程保持，main-clean18..25含忽略文件均干净。没有新增已验证收益，当前采用版第三形状仍44.451126%，三形状均超过45%的目标未完成。下一步先只读分析063/078实际MMA寄存器搬运及依赖变化，再决定是否存在有证据支持的新方案；不直接扫描等待语法或hint。

证据：[冻结计划](../../runs/main-clean-series-001/iter-078-kv0-test-wait/executable-plan.md)、[源差异](../../runs/main-clean-series-001/iter-078-kv0-test-wait/source-edit.diff)、[类型修复记录](../../runs/main-clean-series-001/iter-078-kv0-test-wait/compile-type-fix-plan.json)、[实际编译](../../runs/main-clean-series-001/iter-078-kv0-test-wait/cpu-build/attempt-002/manifest.json)、[初筛](../../runs/main-clean-series-001/iter-078-kv0-test-wait/codegen-screen.json)、[完整路径成本](../../runs/main-clean-series-001/iter-078-kv0-test-wait/native-cost.json)、[CPU资格结论](../../runs/main-clean-series-001/iter-078-kv0-test-wait/root-cpu-qualification.json)、[决定](../../runs/main-clean-series-001/iter-078-kv0-test-wait/decision.json)。

## 063/078补充：MMA地址参数搬运来源（只读）

对实际两架构SASS及完整CFG的定义/使用追踪，G10首次继续query的R2UR由540增至690：固定P地址0x1c0搬运210→320（+110），另有两个Q A-descriptor每轮四字从通用寄存器装回uniform寄存器（+40）。其余分类净变化为零；400次MMA的目标地址来源均为原448/0/128，MMA工作未增加。此为原生定义追踪，不是编译器内部因果、完整操作数资格或运行时间测量。没有新候选与GPU数据，没有新增收益；生产063及main-clean18..25保持。下一步只读核查063固定P目标地址的复用/最后使用，再决定是否冻结独立实现计划。

[研究报告](../../profile/head64-iter078-mma-transfers/REPORT.md) · [完整结果](../../profile/head64-iter078-mma-transfers/result.json)。

## 079：使用TMEM分配结果计算P地址（全部正确性通过，性能回退，恢复063）

父063。基于实际063每组32个QK MMA存在21个P地址装入的证据，仅把MMA角色的`tP=448`改为`plan.tmem_start_addr[0]+448`。原512列分配、base0检查、CTA同步、所有数学/等待/搬运顺序均保留。计划先冻结；源逆变换逐字恢复063，config/common不变。没有带入078 test_wait。

NVCC13.1两架构隔离完整TU成功（77950，ee1f77→5d4ec3，退出0）。每架构2800静态槽，REG168、STACK/LOCAL0、driver shared1024，MMA40/UTCCP48/gather32/Qload16/commit3/CLC1/CALL3/Ostore4保持。新增共享读取只在MMA初始化0x52d0，读取原分配结果字段0x360f0，经R2UR和+448形成P地址；不存在新增热循环共享读取。

| 完整G10路径 | 063指令槽 | 079指令槽 | 差值 |
|---|---:|---:|---:|
| 稳态、终止 | 2866 | 2596 | -270 |
| 稳态、继续 | 2910 | 2640 | -270 |
| 首次含启动、终止 | 2959 | 2692 | -267 |
| 首次含启动、继续 | 3003 | 2736 | -267 |

两架构一致，G2/3/5路径也减少。计数包含predicate关闭槽和新增启动读取，不是周期或实测收益。实际MMA操作数冷热2176案例、wait/commit地址及phase1152案例、Q TMA/UTCCP896案例、query尾部1024案例通过。其他角色2147站点的high64（含调度控制）完全相同；low64差别仅为24个控制流重定位及15处显式UR29/UR30交换。交换边界的4处gather参数读取均由原定义覆盖。最后PV之后到循环回边前12条指令与063相同。

原其他角色文本严格相同检查首次因UR30→UR29失败，已归档；随后显式证明双向重命名和隐式参数组使用边界，没有跳过差异。CPU资格6701ec通过。

正式setup.py原spill检查成功（78532，927f5c→bb83e0）。正式DSO SHA256 `ab83b3903e07d649f351934c2cbe90456c887611a7ad962709bebb8cd634fa43`。实际正式两目标cubin完整128位native/nondebug与隔离产物一致，另外52个cubin与063精确相同（27547，312c5b→d547b6）。原始316（314数值+2运行）、tail6、witness16及两版各29诊断全部通过；87数组423174144元素逐位相同，无NaN payload或零符号豁免。原330配对性能已完成，所有GPU阶段监控有效。

测试准备首次缺少cpu-test-preparation-plan.md元数据而停止，未启动GPU；生成文件与失败记录归档，补齐冻结元数据后重新生成相同数值harness成功。两份完整CPU harness审核通过并安装正式包runtime绑定后，才启动全部GPU阶段。

固定GPU UUID GPU-847489a9-bc7e-726c-1c64-29c59e330fd8；sq4096、skv4096/8192/32768、topk640、hq64、d512BF16及原seed310/311/312。评测协议、原checker和容差不变。已精确恢复063的八个源/包文件，无重编译；候选源码和正式包保留。采用最佳仍063；三形状均超过45%的目标未完成。main-clean18..25含忽略文件保持干净。

证据：[冻结计划](../../runs/main-clean-series-001/iter-079-runtime-p-address/executable-plan.md)、[源差异](../../runs/main-clean-series-001/iter-079-runtime-p-address/source-edit.diff)、[路径成本](../../runs/main-clean-series-001/iter-079-runtime-p-address/native-cost.json)、[MMA操作数](../../runs/main-clean-series-001/iter-079-runtime-p-address/native-operands.json)、[重命名与初始化边界](../../runs/main-clean-series-001/iter-079-runtime-p-address/native-boundaries.json)、[CPU资格](../../runs/main-clean-series-001/iter-079-runtime-p-address/root-cpu-qualification.json)、[正式包](../../runs/main-clean-series-001/iter-079-runtime-p-address/actual-package-audit.json)。

原6A5B/5邻接配对，共330样本，10warmup、8e9flush、0.3秒冷却。SD为各轮均值的样本标准差；相对初始列为直接均值比，未叠加历史收益。

| skv | 同批063均值±SD µs | 079均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.860200 ± 0.161868 | 335.640400 ± 0.101623 | -0.537826% | +19.478019% | 45.498083% |
| 8192 | 334.827683 ± 0.113294 | 336.617300 ± 0.110644 | -0.532017% | +19.139141% | 45.366043% |
| 32768 | 343.288167 ± 0.298674 | 344.794700 ± 0.066112 | -0.437218% | +17.034914% | 44.290109% |

汇总配对加速 **-0.502364473%**，耗时降低-0.504900916%，直接相对初始加速+18.545745525%。15对全部回退，范围-0.578518%至-0.344398%。三形状均超过45%为False。未达到严格>0.5%采用门槛，拒绝079；不选择性重复测量。

实际两架构32个QK目标均使用UR21，初始化阶段R2UR和UIADD3形成地址，完整MMA路径无其他显式UR21写入。代码生成假设实现了，但静态成本减少没有转化为性能收益。没有将此结果归因于某种具体scoreboard/寄存器hazard；下一步对实际063/079包做固定原负载的full/source诊断，核对MMA发射及等待PC分布，再考虑后续方案。当前不扫描P地址表达式或PTX分组写法。

[实际P寄存器复用](../../runs/main-clean-series-001/iter-079-runtime-p-address/p-register-reuse.json)、[正确性](../../runs/main-clean-series-001/iter-079-runtime-p-address/correctness-qualification.json)、[330原样本复算](../../runs/main-clean-series-001/iter-079-runtime-p-address/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-079-runtime-p-address/decision.json)、[恢复](../../runs/main-clean-series-001/iter-079-runtime-p-address/restoration.json)。


## 079 后续诊断：MMA 指令减少，等待重试增加（2026-11-06）

[六维报告](../../profile/head64-iter079-mma-dependency/REPORT.md)、[实际PC对比](../../profile/head64-iter079-vs063-mma-dependency/REPORT.md)。使用归档079正式包，无重编译；原32768/seed312、固定UUID，full/source串行采集均有效，53个冻结输入和实际SASS匹配通过，监测35/17条无外部竞争。历史063/current079 unlocked-clock NCU只作诊断，原330样本-0.502364473%拒绝结论不变。

QK/PV热指令分别7,856,128→6,914,048和2,342,912→2,220,032；包含冷等待的MMA总指令仍下降。19类等待×4capture已核tries=entries+retry、exits=entries及sleep/phasecheck守恒。KV1冷检查full/source7,700/8,546→32,276/32,174，重试回边116/128→5,288/5,060；KV0冷检查410,515/417,242→463,939/462,407。MMA short-scoreboard368/363→370/363，尾部均0，没有073式新尾部热点。等待事件增加与更早到达数据等待点相容，不能转化成微秒或指定硬件hazard因果。

四份报告MMA/UTCCP/gather/Qload/Ostore工作量一致。新增startup LDS只执行148次actual=ideal，无该PC记录的stall样本。eligible0.56449→0.55180、issue41.7607%→41.1550%；DRAM read约335MB且仅+0.061%，不支持流量激增。TC/CTA PM两版均缺失；保留其他pass真实时间窗口，不补零或跨pass拼接。NCU tensor48.6114%不是理论目标。

当前源码和包保持采用063，三个原负载理论利用率45.7181%/45.6159%/44.4511%，目标仍未达成。下一只读研究：KV1只提前arrive-and-expect-tx、保留第16/17条QK之间原wait/fence的位置；先核phase生命周期及026等待整体提前的差异。尚未实现080，不预测收益，不扫描P地址或cache hint。


## 063 只读研究：KV1 expect与wait分离（2026-11-06）

[生命周期检查](../../profile/head64-iter063-kv1-expect-order/REPORT.md)确认原实际0x6930第16条QK后，0x6940 KV1 arrive紧接0x6950 trywait。下一方向只提前事务计数提交，保持原第二半wait/fence，区别于已拒绝026的等待整体前移。结合原源码、CUTLASS实现和官方PTX规则，核对32768B总计数、四producer正常/skip完成、三槽phase与跨query G>=2进度；CPU模型1680种计数安排、1536个query序列/30720tile通过。有限模型不是GPU验证，也不证明提速。

尚未实现或编译080，所有性能N/A。下一步冻结单项计划并验证实际双架构代码生成是否形成预期顺序、完整热路径和资源不恶化；不复用079源代码。采用063保持不变。


## 080：提前KV1事务计数，全部正确性通过，性能回退后恢复063

**拒绝080。原330样本15对全部回退，汇总配对加速-0.187818319%，未达到严格>0.5%采用门槛。**

采用父063；目标仍原三个负载理论利用率>45%，采用需可复现汇总配对>0.5%。[冻结计划](../../runs/main-clean-series-001/iter-080-early-kv1-expect/executable-plan.md)及[源差异](../../runs/main-clean-series-001/iter-080-early-kv1-expect/source-edit.diff)：只移动KV1 arrive_and_expect_tx到KV0 arrive后/等待前，保留全部wait/fence、32QK顺序、P448常量和其他角色。phase SHA `7d19869ea399730ca67bf518b14ac83924dd50205c745ae2f70f4401dc81ed38`，plan SHA `2e7f4d286554a6b0cd5bf8d129aa12cbe77b469bd99aa8c5de72265c568cc07b`。

隔离完整TU NVCC13.1双架构编译85205/b107b2→578c7c成功，17.51秒。两版2832静态槽（含alignment padding），168REG，零stack/local/spill；384线程、266CLC、4produceracks、222480动态+1024driver shared、512TMEM保持。40MMA/48UTCCP/32gather4/16Qload/3commit/1CLC/3CALL/4Ostore不变。

实际080 KV0 arrive0x6420，KV1 arrive0x6440，KV0 TRYWAIT0x6450；16thQK0x6910、KV1 TRYWAIT0x6920、17thQK0x6a30。实际到达地址为原三槽对应half，32768B。全G2/3/5/10、first/steady、next/terminal的热查询成本均下降：steady -1槽、first含startup -3槽；G10 steady-next2910→2909、first-next3003→3000。不将静态计数当性能预测。

[操作数](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-operands.json)2176查询、[等待/commit](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-waits.json)1152、[到达字节与顺序](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-arrivals.json)1152、[Q复制](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-query-copy.json)896、[query尾部](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-final.json)1024案例通过。两架构每份2147个非MMA位点的high64全部相同，low64仅40个控制跳转重定位。无prefix寄存器重命名。最后PV之后仍12条操作，计数寄存器R14→R13，独立UR40/UR5更新互换次序，无额外算术链或新shared load。[边界审查](../../runs/main-clean-series-001/iter-080-early-kv1-expect/native-boundaries.json)、[CPU资格](../../runs/main-clean-series-001/iter-080-early-kv1-expect/root-cpu-qualification.json)。有限标量模型不模拟GPU异步完成，不能代替GPU验证。

审计工具首次native-cost于9122ea退出1：旧Q-copy validator只向前查1/2槽，080实际TRYWAIT在分支前3槽，中间两条是原descriptor/CTA准备。失败脚本/事实保存在native-cost-attempt001.py和failure.json；候选validator仅扩展一槽，全部控制流/冷返回检查保留，dc9d78通过。没有改kernel重试或隐去失败。

正式构建52661/04b4a6→bbeb70退出0，原setupspill检查保留。DSO `bdeefb65febe29921f3224f5278712ace7d4cebe84d7bb2fb39ab88095d17eb7`。实际链接包审计20361/d20834→8f0cbe通过：两个目标cubin全部native128和非debug段与隔离产物匹配，其他52cubin精确等同063。

原316（314数值+2运行）、tail6、witness16、两版各29诊断全部通过；87数组423174144元素逐位相同，无NaN payload或零符号豁免。原316会话57118/442619→695714；其余串行验证77068/cd364b→a885aa。五阶段monitor有效，遥测23/11/10/68/68条，3idle检查及持续foreign监测均通过。补充Qready首次冷等待路径896查询通过，未改动此前冻结审计文件。

固定GPU GPU-847489a9-bc7e-726c-1c64-29c59e330fd8；原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16，sinktrue/lengthfalse、seed310/311/312。原checker/容差/基准脚本和评测参数不变。比较27363/4f8476→39567c成功，87条遥测有效，无外部竞争。根复算b49535/0核对11轮330个原时间区间、输入/包绑定及5邻接配对。

原6A5B/5邻接配对，10warmup、8e9flush、0.3秒冷却、每case10样本。SD为各轮均值的样本标准差；相对初始列为直接均值比，未叠加历史收益。

| skv | 同批063均值±SD µs | 080均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.008017 ± 0.067274 | 334.589980 ± 0.214727 | -0.171497% | +19.853111% | 45.640921% |
| 8192 | 334.799817 ± 0.225498 | 335.426740 ± 0.465767 | -0.193011% | +19.562012% | 45.527065% |
| 32768 | 343.145300 ± 0.129110 | 343.824920 ± 0.098495 | -0.198945% | +17.365018% | 44.415032% |

汇总配对加速 **-0.187818319%**，耗时降低-0.188171740%，直接相对初始加速+18.921505664%。15对全部负值，范围-0.420263%至-0.037874%；没有可保留或汇总表应新增的正向局部收益。三形状均>45%为False。

已无需重编译地精确恢复063的8个源/包文件；候选源码、正式包及全部证据保留。main-clean18..26包含忽略文件均干净。采用最佳仍063，理论利用率45.718103%/45.615939%/44.451126%，原目标尚未完成。

实际代码生成实现了预期顺序，完整热路径没有增加，数学正确性也保持；实测结果仍不支持采用。当前没有080 NCU，不能声称KV1重试已经下降，也不能归因于额外KV0到达延迟或具体寄存器hazard。下一步冻结原32768 full/source诊断计划，核对是否减少KV1首次失败/冷重试、是否把等待移到KV0或其他角色，再决定下一方案。不在此结果上选择性重测或扫描到达位置。

证据：[正式包](../../runs/main-clean-series-001/iter-080-early-kv1-expect/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-080-early-kv1-expect/correctness-qualification.json)、[Qready冷路径补充](../../runs/main-clean-series-001/iter-080-early-kv1-expect/supplement-qready-cold.json)、[原330复算](../../runs/main-clean-series-001/iter-080-early-kv1-expect/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-080-early-kv1-expect/decision.json)、[精确恢复](../../runs/main-clean-series-001/iter-080-early-kv1-expect/restoration.json)。


## 080 后续诊断：提前expect未改善KV1等待（2026-11-06）

[六维报告](../../profile/head64-iter080-kv1-expect/REPORT.md)、[语义PC与等待对比](../../profile/head64-iter080-vs063-expect/REPORT.md)。归档正式080包、原32768/seed312、固定UUID，full/source采集有效，监测37/17条、53冻结输入验证通过；无重编译。此前“没有080 NCU”的状态已由本诊断更新，原330样本汇总-0.187818319%及拒绝决定不变。

KV1首次未就绪full/source7584/8418→13635/12726，冷重试116/128→245/189；KV0 cold tries410515/417242→408908/406455。19等待×4capture事件守恒、正式SASS匹配、MMA/UTCCP/gather/Qload/Ostore工作量一致。MMA short368/363→356/358，尾部short均0；显式shared60位点actual=ideal=5105096，无新增shared load。eligible0.56449→0.56398，DRAM read约335MB仅+0.121%。事件数不是延迟，不能唯一解释回退或命名具体hardware hazard。

TC/CTA PM两版为空，080 long与063 wait也缺失，保留各pass原始覆盖，不补造尾部比较。NCU tensor48.7195%不是理论目标。后续不扫描expect位置；先只读归属063 producer索引/地址准备、TMA发射与等待的原生依赖，复用已有8192/32768报告并对照042/050/058/075/076/078排除重复方案。采用最佳仍063，三个原负载45.718103%/45.615939%/44.451126%，目标未完成。


## 063 只读producer依赖归属（2026-11-06）

[报告](../../profile/head64-iter063-producer-issue-dependencies/REPORT.md)。复用原8192/32768 full/source，报告/包/源码/实际SASS哈希匹配，12区域逐metric守恒。32gather合计5242880、int4索引load655360，四capture均相同。首次显式重写此前gather参数的167个PC集中了producer long-scoreboard的930/893与881/845样本，约52%–55%；producer mio-throttle724/675与703/647全部落在TMA发射。该复用关系不是WAR或延迟因果证明。

lookahead区域long样本0不能排除后续消费者等待索引，但尚无优先加深索引预取的支持。WARPSYNC sleeping不能直接当作elected producer搬运延迟。nvdisasm静态生命周期和2823条原生128位编码核对通过，9条尾部NOP差异、1个null计数明确保留。下一步先对照017/039/076失败原生代码，检查是否存在不同的参数生命周期机制，尚无081实现。事件汇总生成器耗尽错误及两次生命周期解析假设错误均归档并修正；无GPU重采集、无新收益，采用063与原目标不变。


## 081：静态 gather half 设备函数，正确性通过，收益未达门槛

父版为采用063。将每半段16次gather放入禁止内联的设备函数，形成两个真实调用；原32笔操作顺序、barrier、字节数、索引lookahead及数学源码保持。**拒绝081：有效原330样本汇总加速0.286320739%，未达到严格>0.5%门槛。** 两架构资源及完整正确性通过，4096/8192出现一致小幅收益，32768无明确收益。

## 与已有实验的区别

017每行四列runtime loop原比较-6.975282%；039两个half runtime loop完整路径增加57/62槽；076将四个gather写进静态inline PTX块，双架构完整机器码与063相同。本次用真实设备函数边界改变参数分配范围，无新增runtime part/row/column循环。依据是[063 producer归属](../../profile/head64-iter063-producer-issue-dependencies/REPORT.md)的gather参数复用样本及较多uniform/general搬运；它不证明WAR或可实现收益。

[冻结计划](../../runs/main-clean-series-001/iter-081-outlined-gather-half/executable-plan.md)，SHA256 `125b2deffe495b1348eaafe0fd53d8d626e311d6bf4cd88859df009c782e0613`。源码逆变换精确回到063，仅phase1.cuh增加两个模板callee并替换成功TMA分支；config/common逐字节不变。候选phase SHA256 `78e21d9b9761799bc3aa2ffb99ad6f8e6e757a7a771146d8487c1166031504cc`。正式构建时切换至081；完成测试后已精确恢复采用063。

## 已完成的CPU证据

- 原完整TU、原NVCC13.1参数，sm100a/sm103a隔离编译18.111秒，session70356从f53a2f启动，以8f650e退出0。两个callee与入口ptxas均0 stack/spill；实际资源REG168、STACK0、LOCAL0、driver shared1024，无LDL/STL。原动态shared222480、384线程及布局源配置未改。
- 两架构静态2672槽（含padding）；40MMA、48UTCCP、32gather，CALL/RET各5（原3个guardrail调用+新增2个gather调用）。callee0为0x96c0..0x9e50共122槽，callee1为0x9e60..0xa5d0共120槽，均含RET；没有内部控制循环。uniform/general保存恢复由原gather的22对降为两个callee合计1对。
- 源级60个有序tuple case、1920笔gather、640个每half完成计数安排通过；destination/column/row/barrier四负控检出。这是源码映射检查，不代替实际包正确性。
- 实际caller+callee标量解释每架构72case，共144case/4608笔gather：三槽、四producer warp、不同及非法索引、descriptor低字进位均与原地址公式一致。两个实际返回寄存器值均回到正确caller PC；16个当前索引与16个未来索引，以及声明保持的outer state未被破坏。
- 进一步1440个actual call+handoff case确认callee将R43作为scratch后，handoff正确写回k+1；ring cursor更新为query_base+k+1；非末轮复制未来16索引，末轮保留当前索引，不消费未来数据。
- 双架构分别2219个非producer位点（init/consumer/dispatch/MMA/mask/guardrail）按每角色一一寄存器映射及明确cold/callee地址重定位后，opcode、predicate、modifier、immediate、操作数关系和跳转目标相同。未宣称128位调度控制字段完全相同，也未用角色内映射代替跨角色入口活跃值证明。

## 完整路径成本

计数为实际遇到的SASS槽，包括predicate为false的槽、传参、CALL、两个callee全部指令、RET、query prefix/tail和索引交接。两个架构结果相同。固定同一等待成功/重试历史；不是周期、延迟或吞吐量预测。

| valid-first、无length pointer、继续query | 063稳态 | 081稳态 | 差值 | 首次query差值 |
|---|---:|---:|---:|---:|
| G2 | 918 | 673 | -245 | -243 |
| G3 | 1340 | 980 | -360 | -358 |
| G5 | 2182 | 1598 | -584 | -582 |
| G10 | 4287 | 3143 | -1144 | -1142 |

首次G10为4295→3153。gather窗口338→254，handoff50→21。每版本/架构48种query组合覆盖G2/3/5/10、valid-first/fallback-gather/fallback-skip、length-pointer与continue/terminal；所有valid-first完整路径严格减少。query总int4 load始终4G，正常gather32G；skip路径检查两笔complete_tx。非elected路径、指定1/3次cold retry亦有完整记录。减少指令不是采用证据，079/080的反例仍适用。

[资源与静态形状](../../runs/main-clean-series-001/iter-081-outlined-gather-half/codegen-screen.json) · [完整路径](../../runs/main-clean-series-001/iter-081-outlined-gather-half/native-cost.json) · [SM100完整trace](../../runs/main-clean-series-001/iter-081-outlined-gather-half/sm_100a.cost-traces.json) · [SM103完整trace](../../runs/main-clean-series-001/iter-081-outlined-gather-half/sm_103a.cost-traces.json) · [实际包参数与返回地址](../../runs/main-clean-series-001/iter-081-outlined-gather-half/native-packets.json) · [索引交接](../../runs/main-clean-series-001/iter-081-outlined-gather-half/native-handoff.json) · [其他角色对应](../../runs/main-clean-series-001/iter-081-outlined-gather-half/non-producer.json)。

## 完整 CPU 资格与正式包

完整 producer 数值解释在每个架构覆盖 880 个查询案例，包括不同 query 长度、非法索引、skip、跨槽 ring/phase、elected/nonelected 及 CLC 退出。五类冷等待模板确认只写谓词，保持载荷状态。模型覆盖有界实际 SASS 状态转换，不宣称证明硬件异步完成时序。[完整 producer](../../runs/main-clean-series-001/iter-081-outlined-gather-half/native-producer.json) 与 [CPU 资格](../../runs/main-clean-series-001/iter-081-outlined-gather-half/root-cpu-qualification.json) 已通过。

原始 setup 正式构建退出 0；正式包 SHA256 `fcc0619480ee949d9efa55779a407bb8c18a833bbc73059562c3b586c4e13f54`。两架构目标 cubin 的完整 native128 与隔离构建一致，无未解释的非 debug 段变化；其余 52 个 cubin 与 063 完全相同。两架构均为 168 REG、0 STACK/LOCAL。[正式包审计](../../runs/main-clean-series-001/iter-081-outlined-gather-half/actual-package-audit.json) 与 [正式资格](../../runs/main-clean-series-001/iter-081-outlined-gather-half/root-formal-qualification.json) 已通过。

测试工具仅改变候选标签与路径/计划绑定，原始数值配方和 checker 保持。witness CPU 审计及 29 个诊断案例、36 个负控通过；正式运行绑定已安装。[工具资格](../../runs/main-clean-series-001/iter-081-outlined-gather-half/harness-qualification.json)。

## 正确性与固定协议性能结果

原316（314数值+2运行）、tail6、witness16和父/候选各29诊断全部通过。87个输出数组共423,174,144个元素逐位相同，无NaN payload或零符号豁免。五阶段监控有效，遥测21/10/10/69/68条；三次idle检查及持续外部进程监控通过。[完整正确性资格](../../runs/main-clean-series-001/iter-081-outlined-gather-half/correctness-qualification.json)。

固定GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16、sinktrue/lengthfalse、seed310/311/312。原6A5B/5邻接配对、10warmup、8e9flush、0.3秒冷却、每case10样本。比较会话3212/1aca87→a73e25退出0；89条遥测有效，无外部竞争。复算9a0e8b/0核对11轮330个原时间区间、完整参数、checker和实际包绑定。

SD为各轮均值的样本标准差；相对初始列使用直接均值比，没有叠加历史收益。

| skv | 同批063均值±SD µs | 081均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 333.962600 ± 0.157108 | 332.478820 ± 0.147622 | +0.442612% | +20.614149% | 45.930730% |
| 8192 | 334.851283 ± 0.084418 | 333.394200 ± 0.103437 | +0.437478% | +20.290923% | 45.804621% |
| 32768 | 343.408250 ± 0.109408 | 343.456740 ± 0.165182 | -0.020422% | +17.490832% | 44.462644% |

汇总配对加速 **+0.286320739%**，耗时降低+0.285503284%，直接相对初始加速+19.457025742%。4096五对均为+0.383212%至+0.520408%，8192五对均为+0.384801%至+0.477778%，记录为局部小幅收益；32768五对跨零（-0.085256%至+0.029657%），不宣称收益或确定性回退。

采用门槛未通过，不选择性重测。8个源/包文件已无需重编译地精确恢复063；候选源码、正式包及全部证据保留。main-clean18..28（含忽略文件）仍干净。当前最佳063的理论利用率45.718103%/45.615939%/44.451126%，原三形状均>45%目标未完成。

指令槽减少、uniform寄存器搬运减少已经由实际产物证明，但不能据此断言硬件等待减少。当前还没有081的NCU证据；下一步对原32768形状采集full/source诊断，核对producer gather参数复用、MIO/long scoreboard、CALL/RET以及consumer等待是否转移，再决定新候选。不扫描callee划分或在无证据下组合历史优化。

证据：[原330复算](../../runs/main-clean-series-001/iter-081-outlined-gather-half/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-081-outlined-gather-half/decision.json)、[精确恢复](../../runs/main-clean-series-001/iter-081-outlined-gather-half/restoration.json)。

## 审计失败保留

native-cost首次沿用旧只读063工具的cold retry地址，其中四项指向TRYWAIT而非回边；新增cold覆盖触发unclassified branch。已保留失败脚本/日志/JSON，新081工具按实际SASS显式绑定0xaec0/0xaf10/0xaf60/0xafb0并验证preceding phasecheck后通过，未修改旧工具或kernel。其他角色比较首次漏识别WARPSYNC.COLLECTIVE、第二次漏识别BSSY的cold重汇合目标，均归档；按同一明确PC重定位修正后通过。无编译或GPU失败，无选择性性能重测。

## 081 full/source诊断：producer减指令，KV0/KV1等待分布改变（2026-11-06）

两次固定32768采集有效，2671个可用PC均匹配正式候选SASS，角色指标与19类冷等待事件通过守恒。producer动态指令约70.66M→51.89M，gather窗口55.38M→41.62M；新CALL/RET出现611/503个long样本，两个RET占527/501，gather MIO样本703/647→1196/1243。KV0 retry380670/387212→6232/6605，KV1 retry116/128→25086/26252；次数不代表时间，尚不能证明具体依赖原因。PM triage为空，未推断tensor尾部。原330结果仍+0.286321%、未采用；源码/包保持063。[完整诊断](../../profile/head64-iter081-outlined-gather/REPORT.md)、[对比](../../profile/head64-iter081-vs063-producer/REPORT.md)。下一步只读检查RET与最后gather的真实寄存器及依赖关系，不立即扫描函数边界。

## 081 返回边界只读检查（2026-11-06）

双架构2664个native128位点经官方nvdisasm对应检查。第16→17笔gather沿实际执行路径距离063为8槽、081为42槽；RET的返回GPR在55–127槽前已定义。沿既有控制位解释，两个RET都等待紧邻最后gather的read-id1；这是有条件编码解释，不是TMA完成时延证明。支持冻结单个32笔gather whole-tile callee实验，以消除中间返回/重复参数准备，但需资源、完整路径及原运行协议重新验证。[研究报告](../../profile/head64-iter081-return-dependencies/REPORT.md)。

## 082：单个32笔gather设备函数，全部验证通过，采用为新最佳

**采用082：原330样本汇总配对加速+0.735148478%，全部15对提升超过0.547949%，三组无回退。** 原三形状均>45%目标尚未完成。

父版为063。081两个half函数在16→17笔gather之间产生RET、再次CALL及参数重建，真实路径间隔42槽；返回点出现long样本。依据[返回边界研究](../../profile/head64-iter081-return-dependencies/REPORT.md)，本轮只实现一个whole-tile禁止内联函数，连续提交原32笔gather后返回，消除中间返回，同时保留caller之外的参数分配范围。全部part/row/column循环必须编译期展开；没有扫描分段尺寸，未修改SASS控制位。

[冻结计划](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/executable-plan.md) SHA256 `7a401401adcfc84f3e45e1b9697f9eeceacdf6c10541ce90fabd3c93dddd7027`。候选phase SHA256 `7b00ae2fb8de7401150ec5e14eea9543430bfac733242de56dbae1030948f958`。源码逆变换精确恢复063；config/common保持原063。原索引lookahead、valid-first/fallback/skip、所有barrier/phase/CLC、数学和其他角色源码不变。

## CPU结果

原完整TU/NVCC13.1原flags，SM100a/SM103a均构建成功，会话94121/14d6ad→c76e3e退出0。每架构168REG、0STACK/LOCAL/spill、1024driver shared，源配置384threads/222480dynamic shared/512TMEM/266CLCworkers/4produceracks。2696静态槽包含padding；40MMA、48UTCCP、32gather、4CALL/4RET（含原3个guardrail）。唯一gather callee 0x96a0..0xa710共264槽含RET，无内部BRA/CALL。第16→17笔gather为0xa080→0xa0e0，间隔6槽；uniform/general保存恢复9对，低于063的22对，高于081的1对。该变化不能直接证明更快。

源码有序tuple模型60案例、1920笔gather、640种半段完成计数安排通过，destination/column/row/barrier四类负控检出。实际caller+callee数值解释双架构共144案例/4608笔gather，包含descriptor低字进位、三槽四warp、不同/非法索引；完整64位返回地址正确，当前/未来索引及外层状态保持。1440个实际call+handoff案例核对nextk、ring cursor、非末轮复制future payload及末轮不消费future。完整producer模型每架构880查询覆盖长度0..640、skip、非法索引、跨槽phase、elected/nonelected及CLC退出，五类cold模板仅写谓词，模型通过。其他角色每架构2219位点在角色内寄存器一一映射与明确冷块重定位后对应。

[CPU资格](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/root-cpu-qualification.json)通过，49个输入hash已固定。模型为有界SASS状态解释，未声称覆盖所有硬件异步时序或替代GPU正确性。

## 完整路径成本

计数包括传参、CALL、callee全部指令、RET、prefix/tail及handoff，含predicated-off槽；固定相同等待历史。不是周期或耗时预测。

| valid-first、无length pointer、继续query | 063稳态 | 082稳态 | 差值 | 首次query差值 |
|---|---:|---:|---:|---:|
| G2 | 918 | 713 | -205 | -203 |
| G3 | 1340 | 1040 | -300 | -298 |
| G5 | 2182 | 1698 | -484 | -482 |
| G10 | 4287 | 3343 | -944 | -942 |

两个架构结果相同；48种query组合/版本/架构及指定冷重试、nonelected路径已检查。gather窗口338→274槽，handoff50→21。G10比081多200槽，但消除了half边界的返回与重新准备；实际性能必须按固定协议验证。

## 正式包与完整正确性

原setup构建42006/9392c4→7336f7退出0，原spillchecker保留。DSO `c5ff44db0a9cb55a71ea678063731538b38510acefb7f2798f5f4984d106ab61`。实际包审计77045/d8a915→01abc3通过：两目标cubin全部native128/nondebug及资源等同隔离产物，52其他cubin不变。测试工具29案例/36负控CPU审计通过，数值配方及checker未变。

原316（314数值+2运行）、tail6、witness16和两版各29诊断全部通过；87数组共423,174,144元素逐位一致，无NaN payload或零符号豁免。原316会话42876/5c2c3f→a891a8；其余串行验证98604/78af27→350135；五阶段monitor均有效，遥测37/11/11/67/68条。正确性资格3a5d74/0通过。

## 固定协议性能

GPU `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16、sinktrue/lengthfalse、seed310/311/312。原6A5B/5邻接配对，10warmup、8e9flush、0.3秒冷却、每case10样本；原checker/容差/参数不变。比较34185/dd7386→fdd4b9退出0，92条遥测有效，三次idle及持续外部进程监控通过。473d32/0复算全部11轮330个原始时间区间、实际包绑定与5邻接配对。

SD为各轮均值的样本标准差；相对初始列使用直接均值比，不叠加历史收益。

| skv | 同批063均值±SD µs | 082均值±SD µs | 配对加速 | 相对初始加速 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 334.028033 ± 0.117180 | 331.308140 ± 0.134018 | +0.817187% | +21.040340% | 46.093026% |
| 8192 | 334.888467 ± 0.201926 | 332.142260 ± 0.125469 | +0.823722% | +20.744334% | 45.977271% |
| 32768 | 343.374483 ± 0.243043 | 341.425640 ± 0.141495 | +0.564753% | +18.189770% | 44.727147% |

汇总配对加速 **+0.735148478%**，耗时降低+0.729783486%，直接相对初始加速+19.984624079%。15对范围+0.547950%至+0.852833%，全部超过0.5%，支持采用；无选择性重测。

当前源/包8文件已经核对为082，不需要再重编译或回拷。main-clean18..28含忽略文件仍干净。32768均值341.425640µs，要严格超过45%还需低于339.355440672µs，差2.070199µs；不能将本候选采用视为原目标完成。

下一步在原32768形状采集082 full/source，使用与063/081相同协议核对KV1等待是否下降、中间返回消失后的producer MIO/long样本、最终RET及consumer/MMA等待分布。当前尚无082 NCU，因此不把实际性能收益归因于某个已证明硬件hazard。先补证据，再决定下一单候选，不扫描callee分段。

证据：[正式包](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/actual-package-audit.json)、[CPU资格](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/root-cpu-qualification.json)、[正确性](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/correctness-qualification.json)、[原330复算](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/performance-audit-001.json)、[采用决定](../../runs/main-clean-series-001/iter-082-outlined-gather-tile/decision.json)。本候选无构建、正确性或性能测量失败；返回边界研究的脚本SyntaxError另有完整记录。


## 2026-11-06：082 原32768 profiling 完成

082正式包原32768/seed312 full/source采集有效，40/18条遥测通过，八步API/PM分析全部结束。两个报告2695个native PC各自匹配；缺失0xa7b0及未知sample PC 19/30均保留。063/081/082完整角色、gather分类与19类冷等待守恒通过。

082 producer动态指令full/source为55,134,386/55,127,716；gather窗口44,892,160，介于063与081。相对081，KV1冷重试25,086/26,252→9,793/9,214，但KV0重试6,232/6,605→50,073/47,446。最终RET仍有279/235个long样本，uniform/general保存恢复有310/304，需继续核对具体依赖；这些计数不代表周期或可获得的加速。

082首次取得该比较中的有效triage pass0：346,880ns窗口，tensor及CTA最后十分之一均值下降。063/081相应pass为空，不能推断跨版本尾部变化。原benchmark仍是性能权威，32768理论峰值44.727147%未过45%，没有新性能采用结论。[六维完整报告](../../profile/head64-iter082-outlined-tile/REPORT.md)、[三版本守恒比较](../../profile/head64-iter082-vs063081-producer/REPORT.md)。


## 2026-11-06：082 packet/返回依赖只读核验

双架构各2684 native128一致；9组uniform/general保存恢复实际为4个row1坐标和5个列常数。146个首次覆盖旧gather输入PC的long样本898/943，其中部分恢复常数PC也覆盖刚被TMA读取的参数寄存器，因此不能把简单常数重物化当作消除等待。最终RET仍带上一笔gather的已分配read-dependency等待（沿用非官方编码解释）。详见[完整证据与工具失败记录](../../profile/head64-iter082-packet-dependencies/REPORT.md)。下一步仅测试按query生命周期外移函数边界的单项隔离编译方案；082保持采用，原目标未达成。


## 2026-11-06：iter083 producer query函数边界（CPU拒绝）

父版本082。将完整producer query循环放进单个禁止内联函数并在其中内联原32gather，尝试移除每tile返回。attempt001因KernelTemplate成员作用域未限定而编译失败（255，未进入ptxas），保留完整材料后按补充计划作纯作用域修正；attempt002双架构编译通过，REG168、零stack/local/spill。源码和移动body逆变换通过，数学、索引、同步逻辑保持原文本。

原生gather区增至378槽、uniform/general保存恢复各51条（082各9）。G2/3/5/10仅gather区下界756/1134/1890/3780，已分别超过082完整steady路径713/1040/1698/3343，故足够证明未通过完整路径成本降低门槛，拒绝083。未运行正式正确性或GPU benchmark，耗时/性能/理论峰值均N/A，不能称为测得回退。当前源码与包8文件保持082，clean18..29干净。

[完整报告含失败记录](../../runs/main-clean-series-001/iter-083-outlined-producer-query/REPORT.md)、[实际路径下界](../../runs/main-clean-series-001/iter-083-outlined-producer-query/native-cost-lower-bound.json)。原目标仍为三形状均严格>45%，当前32768仍44.727147%。


## 2026-11-06：iter084 两个64列子块合并O发布（CPU机制拒绝）

父082；保留64元素临时数组、全部TMEM64/计算/共享写入，仅把发布配对并指定128列CuTe tile。双架构编译通过，REG168、零stack/local/spill；但实际仍为4个UTMASTG.3D，每query8次O写回，未实现预声明的4→2静态TMA减少。fence/barrier虽4→2，不能替代该机制门槛，故CPU拒绝。没有正式构建/GPU测试/性能样本，均N/A；当前0828文件保持一致。后续先验证真实16KiB输出tensor-map box的维度和共享布局可行性。[完整记录](../../runs/main-clean-series-001/iter-084-paired-o-tma/REPORT.md)。


## 2026-11-06：16KiB O box的4D表示可行性

084失败后的独立研究确认，显式4D O map dims[64,hq,8,sq]/strides[1024,128,hq×1024]/box[64,64,2,1]被当前driver在192组hq/sq组合全部接受，原3D对照通过、三个非法参数负控拒绝。实际CuTe物理地址98,304点及5,324,800有效全局坐标一致，能保留原共享布局；双架构编译探针各产生一条UTMASTG.4D。未运行任何kernel，不提供性能结论。首次缺context的无效probe及修正全部保留。[完整可行性报告](../../profile/head64-output-box4d-feasibility/REPORT.md)。

### Output 4D feasibility: parent L2 promotion128B revalidation

579 metadata cases checked under fixed GPU monitor: 576 legal successes, 3 expected invalid-value failures, exit0/valid=true/7 telemetry records. Includes 192 target blocked4D configurations preserving old shared layout. No kernel or timing; performance N/A; current best remains082. [Audit](../../profile/head64-output-box4d-feasibility/analysis/promotion128-result.json).

### Iter085 — explicit 4D output TMA (rejected)

Status: rejected after complete correctness and valid original330 performance. Parent/adopted best082 restored byte-for-byte. Aggregate paired speedup -0.786880794%; all15 pairs regress. Goal remains active. Fixed GPU GPU-847489a9-bc7e-726c-1c64-29c59e330fd8.

The candidate combines two old64-column shared blocks in one16KiB output TMA through a4D tensor map, retaining the64-element register temporary, original shared layout, arithmetic and TMEM reads. Parent O L2promotion128B preserved. Final store commit and next-query wait/Ofree unchanged. Old typed O descriptor retained as an unused field; the explicit map appends128B of kernel parameters.

Both complete SM100a/SM103a TU builds:168 registers,zero stack/local/spills,1024 static shared;2672 static SASS slots vs0822696. Two static UTMASTG.4D vsfour3D, four LDTM.x64,40MMA,48UTCCP,32gather,9uniformspill/fill pairs. Mechanism/resource gates pass.

Actual native epilogue model:9216 thread cases perarchitecture,72 complete128-thread groups,2359296 BF16 writes perarchitecture. Checks every output provenance (TMEM coordinate→FMUL2→BF16→shared), three slots,two cluster bases,three query indices,two descriptor bases including64bit carry, valid and zero output. All elected-lane packet values agree within each warp. Publication follows128/256 per-thread writes. Wrong descriptor carry,head coordinate and source slice controls rejected. Actual CuTe physical layout model98304 shared coordinates and5324800 valid global coordinates revalidated, including hq1..64. CPU models do not replace GPU rounding/OOB/TMA correctness.

All non-consumer decoded instructions qualified after relocation and bounded register renaming, including464 producer/callee sites,675MMA,182mask,152init,7dispatch,9guardrails perarchitecture. Init only changes intended O descriptor prefetch; MMA zero/64 constants swap registers within a bounded lifetime, both redefined before subsequent uses. CPU root audit verifies ELF TmaParams size1280→1408,thread384,actual operand seeds,source inverse and preserved parent8files/clean18..30.

Checker failures retained: non-consumer001 assumed a permanent whole-role register bijection; output001 incorrectly applied integer addition to symbolic MOV; output002 negative mutation removed a needed register definition; rootCPU001 mixed parent and candidate PC for one redefinition. Minimal frozen corrections changed checks only; kernel source/build unchanged. Final non-consumer002/output003/rootCPU002 pass.

Evidence: [plan](../../runs/main-clean-series-001/iter-085-output-tma4d/executable-plan.md), [source diff](../../runs/main-clean-series-001/iter-085-output-tma4d/source-edit.diff), [codegen](../../runs/main-clean-series-001/iter-085-output-tma4d/codegen-screen.json), [native output](../../runs/main-clean-series-001/iter-085-output-tma4d/native-output.json), [other roles](../../runs/main-clean-series-001/iter-085-output-tma4d/non-consumer.json), [CPU qualification](../../runs/main-clean-series-001/iter-085-output-tma4d/root-cpu-qualification.json). No speedup or adoption claim yet.

Formal package audit passed: actual linked target native128 and all nondebug sections equal qualified isolated085;52 other cubins unchanged082. DSO `5422be98fb2ea0495035c191829e8589b97e9190efe42fb97e453b71c4204dc6`. Original316,tail6,witness16 passed on fixed monitored GPU. Diagnostic CPU29cases/36negativecontrols passed; source manifests frozen and parent082/candidate085 exact formal bindings installed. One orchestration aggregation expected --audit --output to write a file; actual successful JSON was printed to stdout and preserved then copied unchanged. Original diagnostic source/numeric tests unchanged. Diagnostics and performance remain pending.

## Full correctness completed

Original316 (314 numeric,2 run-only),tail6,witness16 and both29case diagnostics passed. All87arrays423174144elements bitwise equal082,zero ignored NaN payloads/zero signs. Five monitors valid with24/11/11/70/70 telemetry records. Remaining-correctness session67845/935eb2→92d655 exit0; rootqualification b367be/0. Original330 completed in session64738/670ab7→0c7b9b,exit0; raw audit760fd7/0 passed. [Correctness qualification](../../runs/main-clean-series-001/iter-085-output-tma4d/correctness-qualification.json).

## Fixed-protocol performance and decision

sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16,sinktrue,lengthfalse,seeds310/311/312. Fixed GPU UUID above,6A5B/5 adjacent pairs,10warmup8e9flush/0.3s cooldown/10samples percase;11runs330samples. Original scripts, checkers and parameters unchanged.93 telemetry records,valid=true,no foreign processes; no clocks changed. SD below is sample standard deviation of round means. Initial baseline comparison is direct, not a sum of historical gains.

| skv | Same-run082 mean±SD µs | 085 mean±SD µs | Paired speedup | Direct vsinitial | Theoretical peak utilization |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.226100 ± 0.128966 | 334.007780 ± 0.143694 | -0.833996% | +20.062024% | 45.720476% |
| 8192 | 332.235883 ± 0.097542 | 334.927140 ± 0.041283 | -0.801822% | +19.740359% | 45.594976% |
| 32768 | 341.523283 ± 0.161948 | 344.021060 ± 0.189531 | -0.724792% | +17.298104% | 44.389709% |

Aggregate paired speedup **-0.786880794%**; elapsed-time reduction-0.793121717% (time increased). Direct initial aggregate speedup+19.027067971%.15pair range-0.857790%..-0.652157%,all negative. Reject; no local performance gains. No selective repeat.

Both source and package restored to exact adopted082 eight-file hashes without rebuilding; clean18..30 remain clean including ignored files. Best082 theoretical utilization remains46.093026%/45.977271%/44.727147% from its adoption measurement; the32768 target remains unmet. This candidate proves true larger4D output transactions are correct and reduce static store count, but this grouping is slower. Reduced store count is not evidence of shorter kernel time. Delayed output publication and changed consumer scheduling are hypotheses, not established hardware causes.

Next evidence: compare original32768 archived085 full/source profile against adopted082, map changed consumer output PCs/publication and MMA/producer waits, and inspect overlap/cold waits before another output grouping change. Do not repeat mere fence grouping or blindly vary4D dimensions. Current production is082.

Evidence: [formal package](../../runs/main-clean-series-001/iter-085-output-tma4d/actual-package-audit.json), [correctness](../../runs/main-clean-series-001/iter-085-output-tma4d/correctness-qualification.json), [raw330 audit](../../runs/main-clean-series-001/iter-085-output-tma4d/performance-audit-001.json), [decision](../../runs/main-clean-series-001/iter-085-output-tma4d/decision.json), [restoration](../../runs/main-clean-series-001/iter-085-output-tma4d/restoration.json). No kernel build/correctness/GPU measurement failures; checker/orchestration failures above retained with minimal corrections.


### 085拒绝方案的原32768 NCU诊断（2026-11-06）

归档085 full/source采集有效，原始2671PC匹配。O TMA动态32768→16384，输出指令减少，scale/转换/shared/TMEM计数不变；producer输出缓冲wait重试27005/26996→28037/28356，consumer循环入口barrier样本236/197→394/332。MMA部分等待下降，不能由某一计数决定因果。085的CTA/tensor等pass0时间序列为空，未声称尾部瓶颈。原330汇总−0.786881%拒绝决定不变，当前082保持。详见[六维诊断](../../profile/head64-iter085-output-tma4d/REPORT.md)和[完整角色/22等待/输出对照](../../profile/head64-iter085-vs082-output/REPORT.md)。


### Iter086 — 输出发射者集中到 consumer row pair（拒绝）

状态：完整正确性通过，原330有效配对提升仅+0.014089954%，未达严格>0.5%门槛，已拒绝并恢复082的八个源码/运行包文件。新建clean31及clean18..30保持干净。目标继续：原三负载理论峰值利用率全部>45%，候选相对082汇总配对提升须严格>0.5%。

只改输出两行：发射warp0/1改0/2，chunk索引使用warp_idx/2。原四次早期发布、八笔8KiB输出、descriptor/布局、计算、commit/wait和128线程Ofree保护均保留。Consumer按0/2及1/3成对同步，假设让一组无需等待本组的输出TMA，有机会提前下一query的P/softmax；没有现有计时证据证明收益，也不把085的barrier样本当作因果证明。014改变的是QK/PV的MMA角色，并未测试本机制。历史81份归档source检查已保留，018/019/020直接存储没有旧TMA片段，未把缺匹配解释为完整排除证据。

## 构建和CPU证据

NVCC13.1完整TU隔离编译18.109s，双架构168REG、零stack/local/spill，2696静态槽，与082总数相同。仅比较opcode从一条ISETP.GT变一条ISETP.NE；40MMA、48UTCCP、32gather、9对寄存器保存恢复、4个O TMA和4个LDTM.x64保留。四个publication PC3850/3f30/4630/4d40，TMA PC38c0/3fc0/46c0/4dd0。外部角色及初始化1502槽native128相同；完整输出区外仅7个setup寄存器/坐标改动和5个等价lastSV冷路径谓词/返回地址改动，逐条核验。

实际SASS符号执行每架构9216线程场景、72组128线程、2359296个BF16 shared写，涵盖3槽、2cluster、3query、2descriptor基址及进位、有效/零输出。每组32768个元素唯一完整，所有可能elected lane的输出包相同。每架构另核验3194880个head1..64裁剪坐标。descriptor进位、issuer奇偶和shared源偏移三个负控都执行到语义不匹配而被拒绝。这里只证明计算来源和地址映射，不能替代GPU浮点/实际TMA测试。

正式包两个head64 native128和非debug ELF均等于隔离结果，52其他cubins仍等于082。资源384threads、222480动态+1024driver共享、512TMEM、266CLCworkers、4produceracks；参数大小1280不变。

## 检查工具问题与更正

codegen-screen attempt001错误要求全部opcode计数相等，而本候选确实把GT比较改NE；attempt002只允许这一个替换并通过。CPU-review attempt001沿用了085两处地址，实际086与082为27f0/2820；attempt002将SM100a reciprocal寄存器强加于SM103a；attempt003分别核验两架构原版/候选的完全一致序列后通过。所有失败脚本、日志和最小更正计划均保留。CPU测试命令在执行前纠正为stdout JSON重定向，原harness/数值检查未改变。没有内核编译、GPU正确性或测量失败；完整GPU验证结果如下。

固定GPU UUID GPU-847489a9-bc7e-726c-1c64-29c59e330fd8。原316、tail6、witness16、两版29诊断及87数组423174144元素逐位比较全部必须通过，之后原330/6A5B/5邻接对评测。性能只使用下方完整原330结果，不将指令变化当作收益。

证据：[冻结计划](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/executable-plan.md)、[两行差异](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/source-edit.diff)、[资源与发射机制](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/codegen-screen.json)、[实际输出符号执行](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/native-output.json)、[CPU审核](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/root-cpu-qualification.json)、[实际正式包](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/actual-package-audit.json)。

正式DSO SHA256：`cbb52fce9f3702608e855a9fcdc5d5dfc21c709799f06cd71753396efe3f74b5`。CPU核验固定50项输入。

## GPU正确性

原316(314数值+2run-only)、tail6、witness16、两版29诊断均通过。完整87数组423174144元素逐位相同，NaN payload/zero sign例外均0。五阶段监控有效，无外部进程干扰；遥测条数为{'original': 21, 'tail': 10, 'witness': 10, 'diagnostic-parent': 69, 'diagnostic-candidate': 68}。原330配对性能已完成且有效，结果如下。

## 固定协议性能与决定

sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16,sinktrue,lengthfalse,seeds310/311/312。固定原GPU UUID、6A5B/5邻接对、10warmup、8e9flush、0.3s cooldown、每shape10samples，共330样本。原脚本/参数/检查器未变。88条遥测有效、无外部进程干扰。SD为round mean的样本标准差；相对初始为直接比较，没有叠加历史收益。

| skv | 同轮082 mean±SD µs | 086 mean±SD µs | 配对加速 | 直接相对初始 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.252500 ± 0.197409 | 331.209220 ± 0.154919 | +0.010072% | +21.076491% | 46.106793% |
| 8192 | 332.202617 ± 0.159561 | 332.224800 ± 0.157551 | -0.006183% | +20.714336% | 45.965849% |
| 32768 | 341.550167 ± 0.107855 | 341.445800 ± 0.178493 | +0.038386% | +18.182792% | 44.724506% |

汇总配对加速 **+0.014089954%**；耗时降低+0.014087969%；直接相对初始汇总加速+19.984267993%。15对范围-0.088785%..+0.100852%。4096/8192配对正负混杂，32768五对均正但幅度仅+0.004742%..+0.100852%，平均差小于各版round波动，未作为可复现局部收益收录到开头收益表。未达到采用门槛，不做选择性重测。

已从归档逐字节恢复082八个文件，无重建；clean18..31连忽略文件也保持干净。最佳082采用测量的理论利用率仍46.093026%/45.977271%/44.727147%，目标未完成。本实验只证明发射者改为0/2仍正确且不会增加资源，未证明关键路径改善；同步/队列时间不能由静态机器码推算。

下一步回到082已有producer packet依赖证据，审查能够减少实际uniform寄存器覆盖等待的机制；不继续做输出warp排列扫描，不把本次噪声提升当作采用依据。083整query外提与085延迟配对发布均已排除，任何新方案仍须先冻结独立计划。

完整证据：[正确性](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/correctness-qualification.json)、[330原始重算](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/decision.json)、[恢复](../../runs/main-clean-series-001/iter-086-output-rowpair-issuers/restoration.json)。

## 082 P/S pipeline full-density Xtrace qualification

Original32768/seed312 diagnostic only: full4192record coverage and byte-exact outputs passed; actual JIT STACK8 plus STL/LDL and150sample traced/off +3.353519% exceed the frozen zero-stack/2% requirements. Stage durations remain instrumented-only; no production gain is claimed. Original strict failure and full factual audit preserved. Best082 and clean18..32 unchanged. [Report](../../profile/head64-iter082-ps-pipeline/REPORT.md).

## 082 reduced P/S pipeline Xtrace qualification

Original32768/seed312 diagnostic: reduced2560record coverage and bit-exact outputs passed; all150 rawCUPTI intervals/monitors audited. ActualJIT stillSTACK8 withSTL/LDL andtraced/off +2.023312%, so both original qualification gates fail. Full density was+3.353519%; this is a measured reduction in tracing overhead, not production speedup. Both runs preserved as instrumented-only; no further density sweep. Best082 andclean18..32 unchanged, goal unmet. [Report](../../profile/head64-iter082-ps-pipeline-reduced/REPORT.md).

## Iter087 — derive redundant second KV barrier (CPU rejected)

Parent082; isolatedsource removesbarrier1 ABIargument and derives+8 inhelper. FullTUdualarch compile passes168REG/zeroSTACK/LOCAL/spill, but actualcaller+callee274→283slots anduniform/GPRsavepairs9→10 on botharchitectures. FrozenCPUmechanismgate rejects; noformal/GPU/original316/original330 run, performanceN/A and no runtime regression claim. Current082 eightfiles andclean18..32 unchanged. [Report](../../runs/main-clean-series-001/iter-087-derived-kv-barrier/REPORT.md) · [Decision](../../runs/main-clean-series-001/iter-087-derived-kv-barrier/decision.json).

## Iter088 — KV 两个半宽描述符（拒绝）

完整正确性通过，原330有效配对汇总加速 -0.109795499%，全部15对回退，未达严格>0.5%采用门槛。已从归档恢复082八个源码/运行包文件，无重建。当前最佳仍为082；clean18..33含忽略文件均保持干净。目标仍要求原三负载全部超过B200 dense BF16额定2250TFLOPS的45%。

## 改动和机制

从082出发，将单个512宽KV tensor map变成两个256宽视图，实际数据基址为KV和KV+256BF16，物理row stride不变。两半均使用0/64/128/192列坐标。保持32笔gather顺序、shared目的地址、transaction bytes、barrier、索引lookahead与数学逻辑。新增128B kernel参数和一次descriptor prefetch；未引入087的barrier参数推导。

实际caller+callee指令槽274→267；9对uniform/GPR保存恢复不变。完整有效G2/G3/G5/G10 producer路径分别减少14/21/35/70条指令；额外3条一次性初始化指令单独计入。该静态收益未转化为kernel性能收益。双架构168REG、零stack/local/spill，384threads、222480动态+1024driver shared、512TMEM、266CLC workers、4producer acknowledgements保持。

## CPU与正式构建

完整TU隔离编译17.100s，SM100a/SM103a实际源地址/OOB、32笔gather包、64位descriptor进位、current/future索引交接、cold路径、完整producer和其余数学/同步核验通过。源码模型26,542,080个BF16地址/OOB比较；实际机器码模型两架构共15,925,248个地址/OOB比较，1,760个完整producer案例、1,440个handoff案例。150个编译树文件仅config.h和phase1.cuh有变化。元数据驱动编码162个正例与4个负控通过；没有把驱动接受描述符当作GPU正确性证明。

正式构建session47808/afefa3→5d3c35退出0，原setup.py与spill检查未修改；正式构建记录00:32:08.382812至00:32:40.241358UTC。实际包审计session38235/97ebb6→9b0b98退出0：两个head64 cubin完整native128和非debug ELF与隔离编译一致，52个其他cubins与082相同；877个CPU输入hash复核通过。原NVCC13.1/NVCC_THREADS2/MAX_JOBS8；运行CUDA13.2，Python /home/liuyong/FlashMLA/.venv/bin/python。

正式DSO SHA256：`37e9b2c5d023b9a286c78f855443a1b403e1219b0ecd6fa9d485781cfea1a85e`。

## 核验与编排错误

native-outside attempt001对三个搬移的guard-helper RET错误要求完整编码相同；冻结更正后，六条其他helper指令仍要求native128完全相同，三条RET检查官方解码的opcode/R2/offset与high64控制相同，并保留变化的low64和PC。不推断未公开编码含义，不声称九条指令全部native128相同；候选源码没有改变。更正后核验通过。

测试适配初次因缺cpu-test-preparation-plan.md停止；第一次恢复脚本缺dst变量也停止。保留失败和原脚本，补齐计划/元数据并修正恢复变量，未改变数值检查。诊断CPU审计命令改为harness.py --audit，因cpu_audit.py只有函数定义；witness审计从stdout保存，不使用不支持的--output。全部发生在GPU测试前。源适配逐项重算，只有候选标签、计划hash和父包绑定变化。无内核编译、GPU正确性或GPU性能测量失败。

## 正确性

原316用例（314数值+2run-only）、tail6、witness16、两版29诊断全部通过。87数组共423,174,144个元素逐位相同，忽略NaN payload与zero sign数量均0。五阶段监控有效、无外部进程干扰；遥测条数23/10/10/67/68。原始checker、阈值、测试参数均未改变。

原316session27627/e3883f→634cd4退出0；剩余正确性与完整CPU差分session83795/062d07→ab80b9退出0；最终正确性审计1e1e24退出0。随后才启动性能比较。

## 固定协议性能

原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16/sinktrue/lengthfalse/seeds310,311,312。固定GPU UUID GPU-847489a9-bc7e-726c-1c64-29c59e330fd8；原kda_run三次idle检查、持续foreign监控，无修改时钟或更换设备。6A5B、5组相邻对照、每case10warmup/10samples、8e9flush、0.3s cooldown，共330样本。性能session38781/a60c32→21fbdd退出0；原始区间重算66dedc退出0，90条遥测有效。SD为round mean样本标准差。

| skv | 同轮082 mean±SD µs | 088 mean±SD µs | 配对加速 | 直接相对初始 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.265783 ± 0.112384 | 331.711680 ± 0.048367 | -0.133238% | +20.893090% | 46.036952% |
| 8192 | 332.291733 ± 0.153771 | 332.629600 ± 0.060997 | -0.103746% | +20.567430% | 45.909909% |
| 32768 | 341.769050 ± 0.191602 | 342.051780 ± 0.141152 | -0.092398% | +17.973419% | 44.645272% |

汇总配对加速 **-0.109795499%**；耗时降低-0.109916182%（实际耗时增加）。直接相对初始汇总加速+19.804155660%，没有叠加历史收益。15对范围-0.150545%..-0.030305%，全部负值；没有可收录的局部收益，不选择性重测。

## 决定与下一步

拒绝088，逐字节恢复082八个文件。当前082采用测量的理论峰值利用率仍46.093026%/45.977271%/44.727147%；32768尚未达45%，目标未完成。新建clean33和clean18..32均未修改。

本实验确认半宽描述符能正确复用列坐标并减少指令，但没有改善端到端延迟。额外descriptor prefetch、参数和地址计算的影响尚未单独归因，不把静态计数当作关键路径证明。下一步应回到082原producer等待/依赖证据，先识别可改变实际依赖的独立机制；不重复描述符拆分、参数排列或既有输出发射者扫描。任何新候选须另行冻结计划。

证据：[冻结计划](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/executable-plan.md)、[CPU资格](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/root-cpu-qualification.json)、[实际包](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/actual-package-audit.json)、[正确性](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/correctness-qualification.json)、[330原始重算](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/performance-audit-001.json)、[决定](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/decision.json)、[恢复](../../runs/main-clean-series-001/iter-088-kv-half-descriptors/restoration.json)。

## Iter089 — 四层softmax求和树（拒绝）

父版本082。只把32值局部normalizer的16次顺序packed加法改成15次、4层平衡树；exp/BF16 S/其他源逻辑保持，明确允许正常浮点舍入差异，不声称LSE或out逐位等价。原316/reference/tolerances不改变。完整正确性通过，但原330样本汇总加速-0.061010908%，未达严格>0.5%门槛，拒绝089。已恢复082八个源码/运行包文件，最佳仍082。

依据原082/32768 NCU full/source直接重读：16FADD2链wait样本17/24，末尾scalar+li为32/27。source行103较大wait属于exp2而非sum，初步按行的归因已纠正；低计数不证明主要瓶颈或>0.5%收益。

隔离完整TU NVCC13.1编译19.220s，session65206/c6921f→c67290退出0。双架构168REG/零STACK/LOCAL/spill，2696含padding指令槽，15FADD2/4层；40MMA、48UTCCP、32gather、4Ostores和原调用结构保持。实际math DAG核验两架构各4种poly/fallback组合：32exp输入与16BF16 pack/4Sstore相同，确切树使用每个原值一次；8个破坏性负控全部拒绝。完整外部opcode/操作数在地址搬移后相同；native128相同2338/2319处，另外49/68处只有high64不同，155个控制/返回地址位点单列，不声称全部机器码一致。

CPU近零log(sum)补充50,128向量：树最大绝对误差1.474891e-7，原链8.940684e-7；97个NaN/+Inf/全零分类案例一致。仅为输入FP32指数值的求和模型，没有模拟QK/MUFU/CUDAfastlog/完整kernel，不替代原GPU正确性。

核验工具失败均保留：outside初次未映射变化区域内的SV冷路径返回BSYNC目标，按双架构实际目标单点修正；math初次将原首项d0+0写成0+d0，按真实父机器码修正模型。候选源与数值门槛未变。最终CPU资格839pins、150编译树文件仅phase1变化。

正式原setup构建session3999/bbd194→5d7ea0退出0；实际包审计72062/a40e62→a5321e通过：两个head64完整native128/非debugELF与隔离编译一致，52其他cubins与082相同。DSO013147e7cbae29eae12932a049d6d358655ce805db7c34091718e7025be237d2。验证期间安装候选；测量后已从完整082归档恢复，不重建。

测试适配已在GPU前冻结：原316、tail6、witness16、29诊断输入/backing/canary/reference流程不变；max_logits exactbytes，out/LSE从原run_test AST提取容差并调用原check_is_allclose的CPU路径作额外父版比较。完整87数组已检查；比较器负控及标准CPUfixture审计完成后才发布runtimebindings。所有GPU仍使用原固定UUID/idle/foreign协议。GPU验证结果见下文；clean18..34保留。

证据：[计划](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/executable-plan.md)、[机器码筛查](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/codegen-screen.json)、[mathDAG](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/native-math.json)、[外部路径](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/native-outside.json)、[CPU资格](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/root-cpu-qualification.json)、[正式包](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/actual-package-audit.json)、[测试适配计划](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/formal-test-adaptation-plan.md)。

标准CPUfixture审计和math比较器审计均通过（5个正例、7个负控含cosine门槛），runtimebindings已发布。原316用例session52019/191f9b→449c0d有效通过，监控无污染；剩余正确性session3106/d65da4→6b593b退出0，最终资格审计2b1d5c退出0。原316（314数值+2run-only）、tail6、witness16、两版29诊断均通过。完整87数组共423,174,144元素核对；只有F00/F03的LSE各64元素变化，最大绝对差9.5367431640625e-7，原check_is_allclose均通过。所有out/max_logits逐位相同，NaN payload和zero sign忽略数均0。五阶段遥测21/10/10/70/69条有效，无外部干扰。正确性完成后才启动原330样本交错比较session2292/e08fae→668e87退出0；原始区间重算a7644d退出0。

## 固定协议性能

原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16/sinktrue/lengthfalse/seeds310,311,312，参数与原benchmark一致。固定GPU UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`；原kda_run三次idle检查、持续foreign监控，无修改时钟或更换设备。6A5B、5组相邻对照、每case10warmup/10samples、8e9flush、0.3s cooldown，共330样本。86条遥测有效，无外部干扰。运行CUDA13.2、Python `/home/liuyong/FlashMLA/.venv/bin/python`。SD为round mean样本标准差。

| skv | 同轮082 mean±SD µs | 089 mean±SD µs | 配对加速 | 直接相对初始 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.334200 ± 0.160005 | 331.395740 ± 0.115301 | -0.019985% | +21.008345% | 46.080842% |
| 8192 | 332.181433 ± 0.112026 | 332.342660 ± 0.062060 | -0.046873% | +20.671526% | 45.949547% |
| 32768 | 341.696533 ± 0.182563 | 342.079540 ± 0.230178 | -0.116149% | +17.963845% | 44.641649% |

汇总配对加速 **-0.061010908%**；耗时降低-0.061048154%（实际耗时增加）。直接相对初始汇总加速+19.873453126%，没有叠加历史收益。全部15对为负，范围-0.208553%至-0.004320%；小幅变化不单独证明稳定回退机制，也不构成可收录收益。没有选择性重测。

## 决定与下一步

拒绝089，从082归档逐字节恢复3个源码文件和5个运行包文件。clean18..34包含忽略文件均保持干净，无运行任务遗留。当前082采用测量的理论峰值利用率仍为46.093026%/45.977271%/44.727147%；最大负载未超过45%，整体目标未完成。

本轮缩短了实际局部求和依赖，并通过了原数值检查，但没有获得端到端收益。原NCU求和等待计数较低；目前证据不能区分调度变化、其他流水线瓶颈和测量波动的贡献。下一步回到082实际依赖与等待证据，优先检查尚未验证的指数路径指令机会；不重复sum树排列或把减少静态指令直接当作加速。任何新实现须重新冻结计划并通过完整验证。

证据：[正确性资格](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/correctness-qualification.json)、[完整数组比较](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/diagnostic-differential-001.json)、[330原始重算](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/performance-audit-001.json)、[比较环境与命令](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/comparison-001-prelaunch.json)、[监控与硬件遥测](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/comparison-001-monitor/manifest.json)、[决定](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/decision.json)、[恢复](../../runs/main-clean-series-001/iter-089-softmax-sum-tree/restoration.json)。

## Iter090 — poly5两层RN-FTZ减法打包（拒绝）

父082；仅把8scalar RN-FTZ减法打包为4FADD2.FTZ，保持RD/guard/Horner/指数重构/求和次序/BF16pack与同步。双架构实际数学区域142→138槽，padding另少4；168REG/零STACK/LOCAL/spill，4CALL/RET保持。完整数学DAG、区域外机器码、14条SVwait/control、55112整数模型pairs与1122输入pins通过。该静态指令节省没有转化为端到端收益。

正式DSO `46144ffd6c53f0a26ec532e2a4ab16adae996c827ef07cfc4e26bc8a93cf5c39`。目标head64正式机器码与隔离产物一致；52非目标中10文件byteexact、42仅debug/internalnamespace十进制标识/ELF布局变化，经完整ELF/符号/segment核验和6个负控确认可执行资源身份保持。原全文件SHA审计失败及两次layout检查失败均保留，修订在GPU前冻结；未改变源码或数值/性能门槛。CPU工具分类/计数错误也保留并说明，见[完整记录](../../runs/main-clean-series-001/iter-090-poly5-packed-sub/REPORT.md)。

原316（314数值+2run-only）、tail6、witness16、两版29诊断全部有效通过；87数组423,174,144元素逐位相同，忽略NaN payload/zero sign均0。五阶段监控24/10/10/64/68条有效。原GPU UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`、原三负载与种子、6A5B五组配对、10warmup/10samples、8e9flush/.3cooldown均未变。性能330样本，90条遥测无外部干扰；session85444/018b03→aedd32和原始区间复算cdcdd7均退出0。SD为round mean样本标准差。

| skv | 同轮082 mean±SD µs | 090 mean±SD µs | 配对加速 | 直接相对初始 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.309217 ± 0.056153 | 331.675540 ± 0.174924 | -0.106709% | +20.906263% | 46.041969% |
| 8192 | 332.126033 ± 0.134418 | 332.548140 ± 0.154744 | -0.121316% | +20.596964% | 45.921155% |
| 32768 | 341.683350 ± 0.242786 | 342.206880 ± 0.140540 | -0.149972% | +17.919949% | 44.625037% |

汇总配对加速 **-0.126000550%**；耗时降低-0.126159512%，实际变慢。直接相对初始汇总加速+19.800184044%，没有叠加历史收益。全部15配对为负(-0.230417%..-0.024537%)，无可收录局部收益。拒绝090，不选择性重测；已恢复082并核对全部8文件，clean18..34保持干净。目标最大负载仍44.727147%，未完成。

[正确性](../../runs/main-clean-series-001/iter-090-poly5-packed-sub/correctness-qualification.json) · [330重算](../../runs/main-clean-series-001/iter-090-poly5-packed-sub/performance-audit-001.json) · [决定](../../runs/main-clean-series-001/iter-090-poly5-packed-sub/decision.json) · [恢复](../../runs/main-clean-series-001/iter-090-poly5-packed-sub/restoration.json)。下一步回到082实际流水线依赖证据，避免重复sum树/packed同义改写扫描。

## Iter091 — O提交后计算/写回LSE与max_logits（拒绝）

父082。只把完整元数据计算/写回移到O的TMA commit之后，保持数学、同步、布局和工作负载。完整正确性通过，原330样本汇总配对加速 **+0.114342207%**，低于严格>0.5%的采用门槛，拒绝091；已恢复082并核验全部8个源码/包文件。只复制实际变化的phase1与DSO两个文件，没有重建。clean18..35保持干净。

原082/32768 NCU full/source直接重读：metadata14条native指令的wait样本5/3，O source-read wait没有非selected stall采样。producer Odone等待存在，但不能由此归因于O store延迟。本轮只验证了调度变更的端到端结果，不把样本计数当作关键路径时间。

完整TU NVCC13.1隔离编译20.459s通过，双架构168REG、零STACK/LOCAL/spill；2696含padding指令槽保持，新增1BRA与少1NOP。实际LG2位于4d00，两次STG位于4de0/4df0，均晚于4cd0 Ocommit且早于4e10 CLCwait。head/padding guard拆分，未增加global store范围。原40MMA/48UTCCP/32gather/4Ostore/4CALL与RET保持。O epilogue寄存器分配/调度确有变化，不能仅称源代码搬移。

native输出检查对父/候选、两个架构分别执行9216线程场景、2359296次BF16写入，覆盖128线程、三ring位置、有效/全无效分支及descriptor carry。输出地址、转换来源、四次TMA参数和元数据存活通过；12个语义负控拒绝。query末尾之外1934/1931处native128相同、144个控制/返回地址位点搬移、7/10处相同解码操作但编码/调度hint变化均记录。源代码逆向搬移逐字节等于082；query尾数学与控制已审查。

正式构建session55477/f52fa7→57c602退出0；DSO `509c9043dbb4892188d6aec9ec671c6eb5779ce8bd9687b1a4f375b9a82c2c28`。实际包审计session90348/550aac→20e9f8通过，两个目标cubin的native128/非debug资源与隔离编译一致；52非目标中10byteexact、42仅历史debug/localPID/layout元数据差异，完整ELF/符号/segment检查和6个负控通过。

原316（314数值+2run-only）session14342/b4632f→9ae7da有效通过；tail6、witness16和父/候选29诊断、全量比较session46225/b0454d→85e794通过。87数组423,174,144元素逐位相同，无NaN payload或zero sign豁免。正确性资格be07b3通过；五阶段遥测23/10/10/66/70条均有效。

固定GPU UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`（物理7/逻辑0）、原sq4096/skv4096,8192,32768/topk640/hq64/hkv1/d512BF16/sinktrue/lengthfalse/seeds310,311,312、6A5B五组相邻配对、10warmup/10samples/8e9flush/.3cooldown保持。性能session80069/38f1a7→cbe75f退出0；原始计时间隔复算1f6620通过，330样本及88条遥测无外部干扰。SD为round mean的样本标准差。

| skv | 同轮082 mean±SD µs | 091 mean±SD µs | 配对加速 | 直接相对初始 | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|
| 4096 | 331.303900 ± 0.076700 | 330.842900 ± 0.102124 | +0.139466% | +21.210550% | 46.157844% |
| 8192 | 332.390233 ± 0.083743 | 331.801060 ± 0.075860 | +0.174993% | +20.868499% | 46.024551% |
| 32768 | 341.770433 ± 0.139040 | 341.658100 ± 0.119001 | +0.028625% | +18.109356% | 44.696715% |

汇总配对加速+0.114342207%，耗时降低+0.114211615%；直接相对初始汇总加速+20.054732285%，没有叠加历史收益。4096/8192各五组配对均为正（+0.106473%..+0.190612%、+0.147313%..+0.200104%），在本次固定协议内验证了小幅局部收益；未达总体采用门槛。32768配对-0.006539%..+0.085846%，有正有负，+0.028625%的均值不作为稳定收益收录。没有选择性重测。

工具问题全部保留：native-output负控替换两次未正确匹配`.reuse`位置；test preparation遗漏必需计划文件，续跑适配遗漏dst变量；流水线状态更新一次误判路径层级。均修正后核验，没有GPU/候选数值失败，也没有修改门槛。另以dependency-proof-erratum001纠正“host API return等待kernel”的措辞：实际合同是CUDA stream依赖下kernel完成后的输出可用性，不是同步host返回；无代码/同步变更。冻结原证据保留。

决定：拒绝091、当前最佳仍082，采用时理论利用率46.093026%/45.977271%/44.727147%，目标未完成。下一步继续查082最大负载实际依赖与等待证据；不重复本轮metadata移动排列，也不将本轮小负载收益推断为最大负载关键路径改善。

[计划](../../runs/main-clean-series-001/iter-091-late-metadata/executable-plan.md) · [CPU资格](../../runs/main-clean-series-001/iter-091-late-metadata/root-cpu-qualification.json) · [输出SASS检查](../../runs/main-clean-series-001/iter-091-late-metadata/native-output.json) · [区域外检查](../../runs/main-clean-series-001/iter-091-late-metadata/native-outside.json) · [正式包](../../runs/main-clean-series-001/iter-091-late-metadata/actual-package-audit.json) · [正确性](../../runs/main-clean-series-001/iter-091-late-metadata/correctness-qualification.json) · [330重算](../../runs/main-clean-series-001/iter-091-late-metadata/performance-audit-001.json) · [决定](../../runs/main-clean-series-001/iter-091-late-metadata/decision.json) · [恢复](../../runs/main-clean-series-001/iter-091-late-metadata/restoration.json) · [依赖说明勘误](../../runs/main-clean-series-001/iter-091-late-metadata/dependency-proof-erratum001.md)。

## Iter092 — early mask / previous slot / O cache组合（采用，目标v2达标）

父082；组合054的全有效mask旁路、074的QK范围previous KV slot维护、070的O TMA evict-first，保留082的32笔gather设备函数，不包含055的rowmax tree。历史单项收益不相加；071组合失败作为反证保留。两轮完整原协议各330样本均完成，所有有效结果都计入；无选择性停止或挑选有利重测。

完整正确性通过：原316（314数值+2run-only）、tail6、witness16、父/候选各29诊断。87数组、423,174,144元素逐位一致，无NaN payload或符号零豁免。五阶段监控26/11/11/63/67条均有效。固定UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8`，NVIDIA B200，物理7/逻辑0。

原sq4096、skv4096/8192/32768、topk640、hq64/hkv1、d512、BF16、sinktrue/lengthfalse、seeds310/311/312保持。每轮6A5B、五组相邻A几何均值/B配对，10warmup/10samples、8e9flush、.3s cooldown保持。合并30个配对GM加速 **+0.677353666%**，耗时降低 **0.672796455%**；直接相对初始汇总加速 **+20.747824068%**。全部30对为正，无逐负载回退。SD为round mean的样本标准差；合并12个父版round和10个候选round。

| skv | 同轮082 mean±SD µs | 092 mean±SD µs | 配对加速 | 直接相对初始 | 实测TFLOPS | 理论峰值利用率 |
|---:|---:|---:|---:|---:|---:|---:|
| 4096 | 331.333642 ± 0.097535 | 329.667310 ± 0.100814 | +0.505191% | +21.642786% | 1042.254944 | 46.322442% |
| 8192 | 332.220150 ± 0.099693 | 330.559550 ± 0.079869 | +0.504860% | +21.322455% | 1039.441709 | 46.197409% |
| 32768 | 341.706167 ± 0.183062 | 338.271670 ± 0.130146 | +1.022897% | +19.291746% | 1015.743895 | 45.144173% |

两轮分别检验，不能仅凭合并平均宣布达标：

| 完整比较 | 汇总配对加速 | 4096理论利用率 | 8192理论利用率 | 32768理论利用率 | 有效遥测条数 |
|---:|---:|---:|---:|---:|---:|
| 001 | +0.685370554% | 46.324888405% | 46.195381544% | 45.151763998% | 85 |
| 002 | +0.669337416% | 46.319995753% | 46.199437239% | 45.136584783% | 88 |

采用门槛要求两轮各自和合并GM均严格>0.5%，逐负载合并回退不超过0.1%；全部通过。目标按343,597,383,680 FLOPs / 实测耗时 / 2250e12计算，三组在两轮均严格>45%，不是NCU tensor活动率。最大负载两轮338.214800/338.328540µs，均低于339.355440672µs目标上限。

源码仅phase1.cuh相对082发生7处替换，逆变换逐字节恢复父版。103个项目源码、vendor依赖以及config/common身份核对通过。双架构168REG、零STACK/LOCAL/spill，2696槽、40MMA/48UTCCP/32gather/4Ostore/4CALL/RET保持；384线程、222480动态共享、1024driver共享、512TMEM、266CLCworkers、4producer ACK不变。

实际消费者1363、MMA659、其它655处按显式地址映射核对，含冷等待和callee；并集2684处，未覆盖仅12个尾部padding NOP。8个policy UMOV及4个store hint核验，4个descriptor-high加法仅跨越无依赖坐标操作。编码和调度变化完整记录，未宣称机器码或性能恒等。每架构mask67712逐位检查，6个实际mask负例和6个consumer/MMA/返回地址负例均拒绝。previous-slot模型4352场景、17408query、87040QK/PV读取和4类负控；历史MMA模型桥接每架构675处。O映射8个8192byte块、hq1..64裁剪通过。CPU模型不作为硬件时序证据。

正式DSO `078f7c61d6c1aa9b37c9d6452e64d0fa87c0cfd9a59c9ad672f893c1626de0db`。构建session35811/45025f→e30012和审计session54144/57266b→fbdba8均退出0。目标两个cubin的native128与非debug部分等于隔离编译；52非目标10byteexact、42仅debug/localPID/layout元数据差异，完整ELF/符号/segment身份及6负控通过。NVCC13.1.115，运行CUDA_HOME13.2，Python3.11.7/Torch2.10.0+cu130，driver595.71.05。温度、功率、SM/显存频率逐样本保留在两份telemetry.jsonl，范围见final-environment.json；没有调频或换卡。

原316 session62347/f6ee21→63d1ca退出0；其余正确性session32707/476b1e→5c7623和资格cd6be2通过。性能001 session14674/e8ffc9→dff9eb、002 session10119/9ad20d→eb4117均退出0；原始时间区间复算1f927c/27fb4e及660合并审核通过。不存在GPU数值失败或无效测量。

工具失败全部保留：native composition四次边界/返回地址/尾部覆盖适配错误；native-controls把UR当R查找；CPU资格误以为kerutils是symlink，改为完整文件名和内容核验；formal资格误把list当dict，shell后续prepare虽生成测试文件但formal binding正确拒绝。修订后逆向验证全部生成文件、完成正式资格和CPU审计，再发布runtime绑定；没有提前启动GPU、修改候选源码或降低门槛。每次失败、修订和原脚本保存在本目录。

决定：采用092，当前源码与运行包的8个文件逐一核对并绑定decision.json；保留所有082父版归档。clean18..36全部保持main的395cb3a且无修改/未跟踪/忽略文件。没有提交、PR或改动用户主工作区。冻结docs/draft.md与executable-plan.md保持一致。本报告仅证明约定工作负载/设备/协议的目标达成，不声称所有可能形状都具有相同收益。

[完整报告与全部证据](../../runs/main-clean-series-001/iter-092-mask-slot-output-combination/REPORT.md) · [完成审计](../../runs/main-clean-series-001/iter-092-mask-slot-output-combination/completion-audit.md)。
