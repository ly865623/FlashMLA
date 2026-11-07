B200 理论 Tensor Core 利用率口径（goal v2，2026-11-04）

本系列固定使用 **单卡 B200 BF16 dense Tensor Core 2250 TFLOPS** 作为理论峰值分母。按原测试 FLOPs 和 iter007 五轮 B 原始时间重算，三组利用率为 **42.645470%、42.573352%、41.943027%**，均未达到 45%。旧 NCU tensor-cycle 百分比保留为诊断证据，不能代替这一目标。

NVIDIA 官方 Blackwell 数据表（Oct25，第 8 页）在 HGX B200 的单卡规格列给出 BF16/FP16 Tensor Core **4.5 PFLOPS**，脚注 2 明确这是 sparse 规格，dense 为其一半。因此 4.5 ÷ 2 = **2.25 PFLOPS = 2250 TFLOPS**。该 PDF 由 NVIDIA HGX 官方页面的 Blackwell Datasheet 链接提供。[NVIDIA Blackwell Datasheet](https://dam-cdn.nvd.orangelogic.com/AssetLink/y441155802qub41q118b2852i557jem5.pdf)

独立交叉核对：HGX B200 官方规格为 8 张 GPU、合计 BF16/FP16 36 PFLOPS，同一脚注说明 dense 为 sparse 的一半；36 ÷ 8 ÷ 2 同样得到 2.25 PFLOPS。[NVIDIA HGX Specifications](https://www.nvidia.com/en-au/data-center/hgx/) 官方 PCF 数据表也确认 8 张 B200、36 PFLOPS sparse，以及每卡可配置至 1000 W。[NVIDIA HGX B200 PCF Summary，第 1 页](https://images.nvidia.com/aem-dam/Solutions/documents/HGX-B200-PCF-Summary.pdf)

本 kernel 对选择出的 top-k 元素执行 BF16 矩阵乘法；attention 的稀疏索引不等于 Tensor Core 的 2:4 结构化稀疏执行。使用 dense 分母，不能用 4500 TFLOPS sparse、其他 Blackwell 产品峰值或不同精度峰值混算。所查网页与 PDF 于 2026-11-04 核实，来源及换算写入 [goal-v2-metric.json](../../runs/main-clean-series-001/goal-v2-metric.json)。

原测试 [tests/test-sparse-prefill.py](../../tests/test-sparse-prefill.py) 第 46–48 行调用 [tests/lib.py](../../tests/lib.py) 第 439–446 行，定义如下：

```text
total_topk = s_q * topk                 # 本三组 topk_length=None
F = 2 * total_topk * h_q * (d_qk + d_v)
  = 2 * 4096 * 640 * 64 * (512 + 512)
  = 343597383680 FLOPs
TFLOPS = F / kernel_time_seconds / 1e12
理论利用率(%) = TFLOPS / 2250 * 100
```

一次乘加按 2 FLOPs 计算，包含 QK 与 PV 两个矩阵乘法，不另加 softmax、指数、gather 或 rescale 的运算。原 helper 在没有 topk_length 时使用 nominal topk；valid-index 数仅用于访存量估算，不能改为按实际 valid-index 数计算 FLOPs。三组 s_kv 虽不同，固定 topk=640，因此 F 相同。原测试入口及 helper 均与仓库 HEAD `395cb3afbb331fef7b1b21e9340861b9436b42d8` 一致，未作修改。

原始时间来自 [iter007 comparison-001](../../runs/main-clean-series-001/iter-007-nondual-qk/comparison-001/summary.json) 的 `B00.json` 至 `B04.json`。每轮为原测试的 10 个 CUPTI kernel samples，主结果先算五轮 mean_s 的算术平均，再用 F/平均时间换算；没有使用最佳轮次、打印后取整时间或 NCU replay duration。± 为五个轮均值的样本标准差。JSON 保留输入的完整十进制时间，并通过 Decimal 计算；与原 comparison summary 的浮点均值差异小于 1e-18 秒。

| s_kv | 平均时间 ± 轮间样本标准差 (µs) | 实测 TFLOPS | 理论利用率 | 达到恰好 45% 所需速度提升 | 达到恰好 45% 所需时间减少 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4096 | 358.091840 ± 0.137347 | 959.523075645 | 42.645470029% | 5.521173% | 5.232289% |
| 8192 | 358.698440 ± 0.183400 | 957.900412614 | 42.573351672% | 5.699923% | 5.392552% |
| 32768 | 364.089000 ± 0.610437 | 943.718112000 | 41.943027200% | 7.288393% | 6.793273% |

45% 对应 **1012.5 TFLOPS**，三组相同的时间界限为：

```text
t_45 = 343597383680 / (2250e12 * 0.45)
     = 339.35544067160493827160493827160493827160493827160 µs
```

按“高于 45%”验收，平均时间必须严格小于上述界限；恰好等于只得到 45%。表中所需提升和时间减少也是到等号的边界值，严格超过目标需要略多的提升。

| s_kv | B 轮次 | 轮均时间 (µs，显示 7 位小数) | TFLOPS | 理论利用率 |
| ---: | :--- | ---: | ---: | ---: |
| 4096 | B00 | 358.0438000 | 959.651818241 | 42.651191922% |
| 4096 | B01 | 357.9414000 | 959.926355767 | 42.663393590% |
| 4096 | B02 | 358.1207000 | 959.445750218 | 42.642033343% |
| 4096 | B03 | 358.0438000 | 959.651818241 | 42.651191922% |
| 4096 | B04 | 358.3095000 | 958.940200246 | 42.619564455% |
| 8192 | B00 | 358.8182000 | 957.580701536 | 42.559142291% |
| 8192 | B01 | 358.3926000 | 958.717852099 | 42.609682315% |
| 8192 | B02 | 358.8600000 | 957.469162570 | 42.554185003% |
| 8192 | B03 | 358.6993000 | 957.898115999 | 42.573249600% |
| 8192 | B04 | 358.7221000 | 957.837233000 | 42.570543689% |
| 32768 | B00 | 363.5890000 | 945.015893440 | 42.000706375% |
| 32768 | B01 | 364.1647000 | 943.521938507 | 41.934308378% |
| 32768 | B02 | 363.4582000 | 945.355982284 | 42.015821435% |
| 32768 | B03 | 364.2422000 | 943.321184860 | 41.925385994% |
| 32768 | B04 | 364.9909000 | 941.386165189 | 41.839385120% |

峰值分母是厂商公布的额定性能，不按本次运行的实际 SM 时钟调整。归档 [environment.json](../../runs/main-clean-series-001/environment.json) 记录该卡功率上限 1000 W、最大 SM 时钟 1965 MHz；最大时钟不是本次 kernel 的平均时钟，也不自行证明官方峰值的参考时钟。若以后分析 `P_clock = P_rated × f_measured / f_reference`，必须另列为时钟归一化诊断，并有可验证的参考时钟，不能替换本目标固定的 2250 TFLOPS 分母来宣布达标。额定峰值也不是 kernel 必然能达到的持续性能。

本次只读取源码、已有 JSON 与 NVIDIA 官方资料，并在 CPU 上重新计算；未启动 GPU。使用固定 UUID `GPU-847489a9-bc7e-726c-1c64-29c59e330fd8` 的已完成、有效且无污染 comparison-001。候选 `.so` SHA-256 为 `365dfcb727cd914ba4d4132bab14dabcb4bbbb039f6e5ee0f62499bb940c03da`，三组保持原参数、种子 310/311/312、BF16 和每轮 10 次采样。逐输入 SHA-256、原测试/runner 哈希、候选源码快照哈希与每轮精确时间见 [goal-v2-metric.json](../../runs/main-clean-series-001/goal-v2-metric.json)。本文件不修改 kernel、主性能报告或优化计划，也不重新解释既有正确性与 A/B 速度提升结论。
