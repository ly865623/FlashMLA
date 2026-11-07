# Iter092 — mask / previous slot / O cache组合（采用，目标v2达标）

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

[冻结计划](executable-plan.md) · [CPU资格](root-cpu-qualification.json) · [原生组合](native-composition.json) · [正式包](actual-package-audit.json) · [正确性](correctness-qualification.json) · [比较001](performance-audit-001.json) · [比较002](performance-audit-002.json) · [660汇总](pooled-performance-audit.json) · [采用决定](decision.json) · [最终环境](final-environment.json) · [完成审计](completion-audit.md)
