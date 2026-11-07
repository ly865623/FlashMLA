/*
Sparse Attention Forward Pass (Phase 1) — SM100, h_q = 64

Forward attention kernel for 64 query heads.
Uses UTCMMA and TMEM. Single-CTA design with B_TOPK=64.

The MMA head block size is MMA_M = 64, matching h_q.

Grid: [s_q, 1, 1]

I/O: See SparseAttnFwdParams in csrc/params.h
*/
#pragma once
#include "phase1.h"

#include <math_constants.h>
#include <cute/tensor.hpp>
#include <cutlass/arch/reg_reconfig.h>
#include <cutlass/arch/arch.h>
#include <cutlass/cuda_host_adapter.hpp>

#include <kerutils/kerutils.cuh>

#include "params.h"
#include "cuda_kernels/defines.h"
#include "cuda_kernels/utils.h"
#include "cuda_kernels/sm100/helpers.h"
#include "cuda_kernels/sm100/common_subroutine.h"
#include "config.h"

namespace sm100::prefill::sparse_fwd::head64 {

template<class TmaCopy, class TS, class SL, class TD, class DL>
CUTE_DEVICE void store_o_evict_first(
    TmaCopy const& tma, Tensor<TS, SL> const& src, Tensor<TD, DL> const& dst
) {
    static_assert(is_smem<TS>::value);
    static_assert(TmaCopy::NumValSrc == 4096 && TmaCopy::NumValDst == 4096);
    static_assert(decltype(size(src))::value == 4096 && decltype(size(dst))::value == 4096);
    static_assert(decltype(size<0>(src))::value == 4096 && decltype(size<0>(dst))::value == 4096);
    auto coord = dst.data().coord_;
    static_assert(tuple_size<decltype(coord)>::value == 3);
#if defined(CUTE_ARCH_TMA_SM90_ENABLED)
    uint64_t desc = reinterpret_cast<uint64_t>(tma.get_tma_descriptor());
    uint32_t smem = cast_smem_ptr_to_uint(raw_pointer_cast(src.data()));
    cutlass::arch::synclog_emit_tma_store(__LINE__, desc, smem);
    asm volatile(
        "cp.async.bulk.tensor.3d.global.shared::cta.bulk_group.L2::cache_hint "
        "[%0, {%2, %3, %4}], [%1], %5;"
        :
        : "l"(desc), "r"(smem), "r"(int32_t(get<0>(coord))),
          "r"(int32_t(get<1>(coord))), "r"(int32_t(get<2>(coord))),
          "l"(uint64_t(TMA::CacheHintSm90::EVICT_FIRST))
        : "memory");
#else
    CUTE_INVALID_CONTROL_PATH("Trying to use tma without CUTE_ARCH_TMA_SM90_ENABLED.");
#endif
}

using namespace cute;

// Isolate packet allocation from the caller without a return between KV halves.
static __device__ __noinline__ void issue_kv_tile(
    const void* descriptor, uint32_t destination_base,
    uint32_t barrier0, uint32_t barrier1,
    int4 rows0, int4 rows1, int4 rows2, int4 rows3
) {
    int4 rows[4] = {rows0, rows1, rows2, rows3};
    CUTE_UNROLL
    for (int part = 0; part < 2; ++part) {
        uint32_t barrier = part == 0 ? barrier0 : barrier1;
        CUTE_UNROLL
        for (int row = 0; row < 4; ++row) {
            CUTE_UNROLL
            for (int j = 0; j < 4; ++j) {
                uint32_t destination = destination_base + row*2048 + (part*4+j)*8192;
                int column = (part*4+j)*64;
                asm volatile(
                    "cp.async.bulk.tensor.2d.shared::cta.global.tile::gather4.mbarrier::complete_tx::bytes.cta_group::1.L2::cache_hint [%0], [%1, {%2, %3, %4, %5, %6}], [%7], %8;\n"
                    :
                    : "r"(destination), "l"(descriptor), "r"(column),
                      "r"(rows[row].x), "r"(rows[row].y), "r"(rows[row].z), "r"(rows[row].w),
                      "r"(barrier), "l"((int64_t)TMA::CacheHintSm90::EVICT_LAST)
                    : "memory"
                );
            }
        }
    }
}

// Apply the original runtime mask, with a uniform all-valid bypass.
CUTE_DEVICE
void mask32_if_needed(float (&p)[32], uint32_t valid_mask, uint32_t branch_selector) {
    asm(
        "{\n"
        ".reg .u32 mask_bits, bit, branch_index;\n"
        ".reg .pred invalid;\n"
        "mov.u32 mask_bits, %32;\n"
        "mov.u32 branch_index, %33;\n"
        "MASK_TARGETS: .branchtargets MASK_SLOW, MASK_DONE;\n"
        "brx.idx.uni branch_index, MASK_TARGETS;\n"
        "MASK_SLOW:\n"
        "and.b32 bit, mask_bits, 0x00000001;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %0, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000002;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %1, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000004;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %2, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000008;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %3, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000010;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %4, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000020;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %5, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000040;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %6, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000080;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %7, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000100;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %8, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000200;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %9, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000400;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %10, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00000800;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %11, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00001000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %12, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00002000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %13, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00004000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %14, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00008000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %15, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00010000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %16, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00020000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %17, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00040000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %18, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00080000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %19, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00100000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %20, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00200000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %21, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00400000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %22, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x00800000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %23, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x01000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %24, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x02000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %25, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x04000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %26, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x08000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %27, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x10000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %28, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x20000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %29, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x40000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %30, 0fFF800000;\n"
        "and.b32 bit, mask_bits, 0x80000000;\n"
        "setp.eq.u32 invalid, bit, 0;\n"
        "@invalid mov.f32 %31, 0fFF800000;\n"
        "MASK_DONE:\n"
        "}\n"
        : "+f"(p[0]), "+f"(p[1]), "+f"(p[2]), "+f"(p[3]), "+f"(p[4]), "+f"(p[5]), "+f"(p[6]), "+f"(p[7]), "+f"(p[8]), "+f"(p[9]), "+f"(p[10]), "+f"(p[11]), "+f"(p[12]), "+f"(p[13]), "+f"(p[14]), "+f"(p[15]), "+f"(p[16]), "+f"(p[17]), "+f"(p[18]), "+f"(p[19]), "+f"(p[20]), "+f"(p[21]), "+f"(p[22]), "+f"(p[23]), "+f"(p[24]), "+f"(p[25]), "+f"(p[26]), "+f"(p[27]), "+f"(p[28]), "+f"(p[29]), "+f"(p[30]), "+f"(p[31])
        : "r"(valid_mask), "r"(branch_selector)
    );
}

// Degree-5 exp2 on [0, 1), mixed with MUFU for a small part of softmax.
// Keep exceptional and subnormal results on the original hardware path.
CUTE_DEVICE
float2 exp2_poly5_pair(float2 x) {
    if (!(x.x >= -126.0f && x.x <= 127.0f &&
          x.y >= -126.0f && x.y <= 127.0f)) {
        return float2{exp2f(x.x), exp2f(x.y)};
    }
    constexpr float magic = 12582912.0f;
    float2 z = {__fadd_rd(x.x, magic), __fadd_rd(x.y, magic)};
    float2 r = {__fsub_rn(x.x, __fsub_rn(z.x, magic)),
                __fsub_rn(x.y, __fsub_rn(z.y, magic))};
    float2 y = {0x1.e9b62cp-10f, 0x1.e9b62cp-10f};
    y = ku::float2_fma(y, r, float2{0x1.27634cp-7f, 0x1.27634cp-7f});
    y = ku::float2_fma(y, r, float2{0x1.c921acp-5f, 0x1.c921acp-5f});
    y = ku::float2_fma(y, r, float2{0x1.ebdae6p-3f, 0x1.ebdae6p-3f});
    y = ku::float2_fma(y, r, float2{0x1.62e4bep-1f, 0x1.62e4bep-1f});
    y = ku::float2_fma(y, r, float2{1.0f, 1.0f});
    return float2{
        __uint_as_float((__float_as_uint(z.x) << 23) + __float_as_uint(y.x)),
        __uint_as_float((__float_as_uint(z.y) << 23) + __float_as_uint(y.y))};
}

template<int NUM_ELEMS_PER_THREAD>
CUTE_DEVICE
float get_s_from_p_mixed_exp(
    nv_bfloat162 s[NUM_ELEMS_PER_THREAD/2],
    float p[NUM_ELEMS_PER_THREAD], float scale, float new_max
) {
    float2 cur_sum = {0.0f, 0.0f};
    float2 scale2 = {scale, scale};
    float2 neg_max2 = {-new_max, -new_max};
    CUTE_UNROLL
    for (int i = 0; i < NUM_ELEMS_PER_THREAD/2; ++i) {
        float2 d = ku::float2_fma(float2{p[i*2], p[i*2+1]}, scale2, neg_max2);
        if ((i & 7) == 7) {
            d = exp2_poly5_pair(d);
        } else {
            d.x = exp2f(d.x);
            d.y = exp2f(d.y);
        }
        cur_sum = ku::float2_add(cur_sum, d);
        s[i] = __float22bfloat162_rn(d);
    }
    return cur_sum.x + cur_sum.y;
}

// OR over the two consumer warps that own the halves of the same rows.
// The explicit count and unaligned form permit the two row pairs to diverge.
CUTE_DEVICE
bool row_pair_any(bool predicate, uint32_t user_barrier_id) {
    uint32_t result;
    uint32_t barrier_id = user_barrier_id + NamedBarrier::ReservedNamedBarrierCount;
    asm volatile(
        "{ .reg .pred input_pred, output_pred;\n"
        "  setp.ne.u32 input_pred, %1, 0;\n"
        "  barrier.red.or.pred output_pred, %2, 64, input_pred;\n"
        "  selp.u32 %0, 1, 0, output_pred; }\n"
        : "=r"(result) : "r"(uint32_t(predicate)), "r"(barrier_id) : "memory");
    return result != 0;
}

/*
Pipeline Overview:

| Copy |    MMA    |   Scale & Exp   |

KV0
KV1
KV2
        P0 = QK0^T
                    S0 = exp(P0)
                    scale(O) w.r.t P0
        P1 = QK1^T
                    S1 = exp(P1)
        O += S0V0
KV3                 scale(O) w.r.t P1
        P2 = QK2^T
                    S2 = exp(P2)
        O += S1V1
KV4                 scale(O) w.r.t P2
        P3 = QK3^T
                    S3 = exp(P3)
        O += S2V2
KV5                 scale(O) w.r.t P3

...

        O += S(n-3)V(n-3)
                    scale(O) w.r.t P(n-2)
        P(n-1) = QK(n-1)^T
                   S(n-1) = exp(P(n-1))
        O += S(n-2)V(n-2)
                   scale(O) w.r.t P(n-1)
        O += S(n-1)V(n-1)
*/

template<typename TmaParam>
__device__ void
KernelTemplate::sparse_attn_fwd_kernel_devfunc(const SparseAttnFwdParams &params, const TmaParam &tma_params) {
#if (defined(__CUDA_ARCH__) && (__CUDA_ARCH__ >= 1000 && __CUDA_ARCH__ < 1200)) || (defined(__CLION_IDE__) || defined(__VSCODE_IDE__))
    // Grid shape: [s_q, 1, 1]

    const int warp_idx = cutlass::canonical_warp_idx_sync();
    const int lane_idx = threadIdx.x % 32;
    const int warpgroup_idx = __shfl_sync(0xffffffff, threadIdx.x / 128, 0);
    const int idx_in_warpgroup = threadIdx.x % 128;

    // Define shared tensors
    extern __shared__ char wksp_buf[];
    SharedMemoryPlan &plan = *reinterpret_cast<SharedMemoryPlan*>(wksp_buf);

    if (warp_idx == 0 && elect_one_sync()) {
        cute::prefetch_tma_descriptor(tma_params.tma_QS.get_tma_descriptor());
        cute::prefetch_tma_descriptor(tma_params.tma_QT.get_tma_descriptor());
        cute::prefetch_tma_descriptor(tma_params.tma_O.get_tma_descriptor());
        cute::prefetch_tma_descriptor(&(tma_params.tensor_map_kv));

        plan.bar_prologue_q.init(1);
        plan.bar_prologue_utccp.init(1);
        plan.bar_clc_full.init(1);
        plan.bar_clc_empty.init(NUM_WORKER_THREADS);
        fence_barrier_init();
    } else if (warp_idx == 1 && elect_one_sync()) {
        // Initialize other barriers
        CUTE_UNROLL
        for (int i = 0; i < NUM_BUFS; ++i) {
            plan.bar_qk_done[i].init(1);
            plan.bar_sv_done[i].init(1);
            plan.bar_kv_ready[i][0].init(1);
            plan.bar_kv_ready[i][1].init(1);
            plan.bar_k_valid_ready[i].init(B_TOPK/8);
            plan.bar_k_valid_free[i].init(128);
        }
        plan.bar_p_free.init(128);
        plan.bar_so_ready.init(128);
        plan.bar_o_write_back_done.init(128);
        plan.bar_o_write_back_done_waited.init(4);
        fence_barrier_init();
    } else if (warp_idx == 2) {
        // Initialize TMEM
        cute::TMEM::Allocator1Sm().allocate(512, plan.tmem_start_addr.data());
        TRAP_ONLY_DEVICE_ASSERT(plan.tmem_start_addr.data()[0] == 0);
        cute::TMEM::Allocator1Sm().release_allocation_lock();
    }

    __syncthreads();

    struct OuterloopArgs {
        bool outer_loop_phase;
        int s_q_idx;
        int num_k_blocks;
        int topk_length;
    };

    auto issue_q_tma = [&](int s_q_idx, int qko_slot_idx) {
        Tensor gQS = tma_params.tma_QS.get_tma_tensor(tma_params.shape_QS)(_, _, s_q_idx);
        Tensor gQT = tma_params.tma_QT.get_tma_tensor(tma_params.shape_QT)(_, _, s_q_idx);
        Tensor sQS = make_tensor(make_smem_ptr(plan.q_shared.data()), SmemLayoutQTiles<D_sQ/64>{});
        Tensor sQT = make_tensor(make_smem_ptr(plan.u.qko_slots[qko_slot_idx].data()), SmemLayoutQTiles<D_tQ/64>{});
        ku::launch_tma_copy(tma_params.tma_QS, gQS, sQS, plan.bar_prologue_q, TMA::CacheHintSm90::EVICT_FIRST);
        ku::launch_tma_copy(tma_params.tma_QT, gQT, sQT, plan.bar_prologue_q, TMA::CacheHintSm90::EVICT_FIRST);
    };

    auto issue_q_utccp = [&](bool outer_loop_phase, int qko_slot_idx) {
        plan.bar_prologue_q.arrive_and_expect_tx(MMA_M*D_V*sizeof(bf16));
        plan.bar_prologue_q.wait(outer_loop_phase);
        ku::tcgen05_after_thread_sync();
        UMMA::SmemDescriptor sQ_desc = UMMA::make_umma_desc<UMMA::Major::K>(
            make_tensor(
                make_smem_ptr(plan.u.qko_slots[qko_slot_idx].data()),
                tile_to_shape(
                    UMMA::Layout_K_SW128_Atom<bf16>{},
                    Shape<Int<MMA_M>, Int<64>>{}
                )
            )
        );
        
        CUTE_UNROLL
        for (int tile_idx = 0; tile_idx < D_tQ/64; ++tile_idx) {
            // Duplicate the 64 Q rows into both halves of TMEM for normal M64 QK.
            CUTE_UNROLL
            for (int subtile_idx = 0; subtile_idx < 8; ++subtile_idx) {
                SM100_UTCCP_2x64dp128bitlw0213_1cta::copy(
                    sQ_desc + tile_idx*(MMA_M*128/16) + subtile_idx,
                    tmem_cols::Q + tile_idx*32 + subtile_idx*4
                );
            }
        }
        ku::umma_arrive_noelect(plan.bar_prologue_utccp);
    };

    auto run_outer_loop = [&](auto loop_body) {
        int outer_loop_phase = false;
        ku::CLCResult next_job = {true, (int)blockIdx.x, 0, 0};
        CUTE_NO_UNROLL
        while (next_job.is_valid) {
            int s_q_idx = next_job.x;
            int topk_length = params.topk_length != nullptr ? __ldg(params.topk_length + s_q_idx) : params.topk;
            int num_k_blocks = max(cute::ceil_div(topk_length, (int)B_TOPK), 2);  // num_k_blocks always >= 2 to simplify synchronizations across outer loop boundries
            OuterloopArgs args = {
                (bool)outer_loop_phase,
                s_q_idx,
                num_k_blocks,
                topk_length
            };
            loop_body(args);

            plan.bar_clc_full.wait(outer_loop_phase);
            next_job = ku::get_clc_query_response<true>(plan.clc_response_obj);
            outer_loop_phase ^= 1;

            plan.bar_clc_empty.arrive();
        }
    };

    RingBufferState rs;

    if (warpgroup_idx == 0) {
        // Scale & Exp warps
        bf16* sS_base;
        sS_base = plan.s + lane_idx*8 + (warp_idx&1)*(MMA_M/2)*8 + (warp_idx/2)*MMA_M*(B_TOPK/2);
        static constexpr int NUM_ELEMS_PER_THREAD = B_TOPK / (128/MMA_M);

        run_outer_loop([&](const OuterloopArgs &args) {
            // The following three numbers are 
            // - mi: max_logits used to scale Pi (i.e. O := exp2(Pi*scale - mi) @ V)
            // - li: sumexp, i.e. li := sum(exp(Pi*scale - mi))
            // - real_mi: local max logits, merged with the other half at query end
            // where Pi is the i-th row of P, P := QK^T
            // mi is consistent between the two threads controlling one row
            // (thread 0+64, 1+65, ...); real_mi is local until the final exchange.
            float mi = MAX_INIT_VAL;
            float li = 0.0f;
            float real_mi = -CUDART_INF_F;

            cute::tma_store_wait<0>();
            plan.bar_o_write_back_done.arrive();
    
            CUTE_NO_UNROLL
            for (int k = 0; k < args.num_k_blocks; ++k) {
                // Wait for P
                // Without P exchange, this also protects the previous rowmax peer read.
                NamedBarrier::arrive_and_wait(64, NamedBarriers::wg0_warp02_sync+(warp_idx&1));
                auto [buf_idx, bar_phase] = rs.get<NUM_BUFS>();
                // Acquire and load the mask before waiting for QK completion.
                plan.bar_k_valid_ready[buf_idx].wait(bar_phase);
                // WS M64N64 folds the two top-k halves into the lower/upper DP rows.
                uint32_t valid_mask = *(uint32_t*)(plan.is_k_valid[buf_idx] + (warp_idx >= 2 ? 4 : 0));
                uint32_t mask_branch_selector;
                asm volatile(
                    "{ .reg .pred full;\n"
                    "  setp.eq.u32 full, %1, 0xffffffff;\n"
                    "  selp.u32 %0, 1, 0, full; }\n"
                    : "=r"(mask_branch_selector) : "r"(valid_mask));
                plan.bar_qk_done[buf_idx].wait(bar_phase);
                ku::tcgen05_after_thread_sync();
                
                // Load P
                float p[NUM_ELEMS_PER_THREAD];
                ku::tmem_ld_32dp32bNx<NUM_ELEMS_PER_THREAD>(tmem_cols::P, p);
                cutlass::arch::fence_view_async_tmem_load();
                ku::tcgen05_before_thread_sync();
                plan.bar_p_free.arrive();

                static_assert(NUM_ELEMS_PER_THREAD == 32);
                mask32_if_needed(p, valid_mask, mask_branch_selector);
                plan.bar_k_valid_free[buf_idx].arrive();
                
                // Get rowwise max of Pi
                float cur_pi_max = get_max<NUM_ELEMS_PER_THREAD>(p);
                cur_pi_max *= params.sm_scale_div_log2;
    
                real_mi = max(real_mi, cur_pi_max);
                bool should_scale_o = row_pair_any(
                    cur_pi_max - mi > 6.0f,
                    NamedBarriers::wg0_warp02_sync + (warp_idx&1));
                if (should_scale_o) {
                    plan.rowwise_max_buf[idx_in_warpgroup] = cur_pi_max;
                    NamedBarrier(64, NamedBarriers::wg0_warp02_sync + (warp_idx&1))
                        .arrive_and_wait_unaligned();
                    cur_pi_max = max(cur_pi_max, plan.rowwise_max_buf[idx_in_warpgroup^64]);
                }
                // The decision is uniform within each pair of consumer warps.
                // Only the scaling path needs the peer's current maximum.
    
                // Calc scale factor, and scale li
                float new_max, scale_for_old;
                if (!should_scale_o) {
                    // Don't scale O
                    scale_for_old = 1.0f;
                    new_max = mi;
                } else {
                    new_max = max(cur_pi_max, mi);
                    scale_for_old = exp2f(mi - new_max);
                }
                mi = new_max;   // mi is still identical within each row
    
                // Calculate S
                nv_bfloat162 s[NUM_ELEMS_PER_THREAD/2];
                float cur_sum = get_s_from_p_mixed_exp<NUM_ELEMS_PER_THREAD>(s, p, params.sm_scale_div_log2, new_max);
                li = fma(li, scale_for_old, cur_sum);
    
                // Wait for last SV gemm, write S
                if (k > 0) {
                    auto [last_sv_buf_idx, last_sv_bar_phase] = rs.offset_by(-1).get<NUM_BUFS>();
                    plan.bar_sv_done[last_sv_buf_idx].wait(last_sv_bar_phase);
                }
                CUTE_UNROLL
                for (int i = 0; i < NUM_ELEMS_PER_THREAD/8; i += 1) {
                    *(uint128_t*)(sS_base + MMA_M*8*i) = *(uint128_t*)(s + i*4);
                }
    
                // Scale O
                if (k > 0 && should_scale_o) {
                    // plan.bar_sv_done[(k-1)%NUM_BUFS].wait(((k-1)/NUM_BUFS)&1);   // NOTE We have waited for last SV gemm before
                    ku::tcgen05_after_thread_sync();
                    rescale_O<D_V/(128/MMA_M), 32, tmem_cols::O>(scale_for_old);
                    ku::tcgen05_before_thread_sync();
                }
                
                fence_view_async_shared();
                plan.bar_so_ready.arrive();

                rs.update();
            }

            plan.bar_o_write_back_done_waited.wait(args.outer_loop_phase);
    
            // Retire the final conditional rowmax peer read before reusing its buffer.
            NamedBarrier(64, NamedBarriers::wg0_warp02_sync + (warp_idx&1))
                .arrive_and_wait_unaligned();

            // Publish the local maximum and unmodified li using the original li barrier.
            plan.rowwise_max_buf[idx_in_warpgroup] = real_mi;
            plan.rowwise_li_buf[idx_in_warpgroup] = li;
            NamedBarrier::arrive_and_wait(128, NamedBarriers::wg0_sync);
            real_mi = max(real_mi, plan.rowwise_max_buf[idx_in_warpgroup^64]);
            li += plan.rowwise_li_buf[idx_in_warpgroup^64];

            // Only the merged maximum can establish that the entire row is invalid.
            if (real_mi == -CUDART_INF_F) {
                li = 0.0f;
                mi = -CUDART_INF_F;
            }
    
            // Store mi and li
            if (idx_in_warpgroup < MMA_M) {
                bool is_padding_row = idx_in_warpgroup >= params.h_q;
                float cur_lse = fmaf(mi, CUDART_LN2_F, logf(li));
                cur_lse = cur_lse == -CUDART_INF_F ? +CUDART_INF_F : cur_lse;
                if (!is_padding_row) {
                    int global_index = args.s_q_idx*params.h_q + idx_in_warpgroup;
                    params.max_logits[global_index] = real_mi*CUDART_LN2_F;
                    params.lse[global_index] = cur_lse;
                }
            }
            
            auto [o_slot_idx, __] = rs.offset_by(+2).get<NUM_BUFS>();
    
            // Store O
            float attn_sink = (params.attn_sink == nullptr || idx_in_warpgroup%MMA_M >= params.h_q)
                ? -CUDART_INF_F : __ldg(params.attn_sink + (idx_in_warpgroup%MMA_M))*CUDART_L2E_F;
            float output_scale = __fdividef(1.0f, li + exp2f(attn_sink - mi));
            Tensor sO = make_tensor(make_smem_ptr(plan.u.qko_slots[o_slot_idx].data()), SmemLayoutO{});
            Tensor tma_gO = flat_divide(
                tma_params.tma_O.get_tma_tensor(tma_params.shape_O)(_, _, args.s_q_idx),
                Shape<Int<MMA_M>, Int<B_EPI>>{}
            )(_, _, _0{}, _);
            Tensor sO_divided = flat_divide(
                sO,
                Shape<Int<MMA_M>, Int<B_EPI>>{}
            )(_, _, _0{}, _);
            auto thr_tma = tma_params.tma_O.get_slice(_0{});
    
            float2 o[B_EPI/2];
            bool have_valid_indices = __any_sync(0xffffffff, li != 0);  // Prevent some threads' li == 0 and some threads' li != 0 which lead to deadlock during ku::tmem_ld
            if (!have_valid_indices) {
                // If there are no valid indices, we set o[i] to 0 and don't load from TMEM
                CUTE_UNROLL
                for (int i = 0; i < B_EPI/2; ++i)
                    o[i].x = o[i].y = 0.0f;
                output_scale = 1.0f;
            }
    
            float2 output_scale_float2 = make_float2(output_scale, output_scale);
    
            bf16* sO_addrs[8];
            CUTE_UNROLL
            for (int i = 0; i < B_EPI/8; ++i) {
                sO_addrs[i] = &sO(idx_in_warpgroup%MMA_M, i*8);
            }
    
            // Wait for the last GEMM
            {
                auto [last_sv_buf_idx, last_sv_bar_phase] = rs.offset_by(-1).get<NUM_BUFS>();
                plan.bar_sv_done[last_sv_buf_idx].wait(last_sv_bar_phase);
                ku::tcgen05_after_thread_sync();
            }
    
            static constexpr int NUM_EPI_SB = D_V/B_EPI_SB;
            static constexpr int NUM_TMA_PARTS = 128 / MMA_M;
            CUTE_UNROLL
            for (int c = 0; c < NUM_EPI_SB; ++c) {
                // Each tile: MMA_M x B_EPI_SB
                CUTE_UNROLL
                for (int k = 0; k < B_EPI_SB/B_EPI/NUM_TMA_PARTS; ++k) {
                    // Load O from tO
                    if (have_valid_indices) {
                        ku::tmem_ld_32dp32bNx<B_EPI>(tmem_cols::O + c*(B_EPI_SB/NUM_TMA_PARTS) + k*B_EPI, o);
                        cutlass::arch::fence_view_async_tmem_load();
                    }
                    // NOTE. We neither signal any barrier after tmem_O is free, nor do we wait for any barrier in the UTCMMA warp, since the first O gemm in the next round depends on S, which depends on this warpgroup

                    // Convert and store
                    CUTE_UNROLL
                    for (int i = 0; i < B_EPI/8; ++i) {
                        nv_bfloat162 o_bf16[4];
                        CUTE_UNROLL
                        for (int j = 0; j < 4; ++j) {
                            o[i*4+j] = ku::float2_mul(o[i*4+j], output_scale_float2);
                            o_bf16[j] = __float22bfloat162_rn(o[i*4+j]);
                        }
                        bf16* sO_ptr = sO_addrs[i] + (c*B_EPI_SB + (idx_in_warpgroup/MMA_M)*(B_EPI_SB/(128/MMA_M)) + k*B_EPI)*MMA_M;
                        ku::st_shared(sO_ptr, *(__int128_t*)(o_bf16));
                    }
    
                    // Sync
                    fence_view_async_shared();
                    NamedBarrier::arrive_and_wait(128, NamedBarriers::wg0_sync);
                    
                    // Store into global memory
                    if (warp_idx < NUM_TMA_PARTS && elect_one_sync()) {
                        int epi_chunk_idx = c*(B_EPI_SB/B_EPI) + ((B_EPI_SB/B_EPI)/NUM_TMA_PARTS)*warp_idx + k;
                        store_o_evict_first(
                            tma_params.tma_O,
                            thr_tma.partition_S(sO_divided(_, _, epi_chunk_idx)),
                            thr_tma.partition_D(tma_gO(_, _, epi_chunk_idx))
                        );
                    }
                }
            }
            cute::tma_store_arrive();
        });

        if (warp_idx == 3) {
            cute::TMEM::Allocator1Sm().free(0, 512);
        }
    } else if (warpgroup_idx == 1) {
        // Producer warp for KV
        int warp_idx = cutlass::canonical_warp_idx_sync() - 4;
        constexpr int NUM_WARPS = 4, NUM_LOCAL_ROWS_PER_WARP = (B_TOPK/4)/NUM_WARPS;
        run_outer_loop([&](const OuterloopArgs &args) {
            if (elect_one_sync()) {
                int* gIndices = params.indices + args.s_q_idx*params.stride_indices_s_q; // [topk]
                int4 indices[NUM_LOCAL_ROWS_PER_WARP];
                CUTE_UNROLL
                for (int local_row = 0; local_row < NUM_LOCAL_ROWS_PER_WARP; ++local_row) {
                    indices[local_row] = __ldg((int4*)gIndices + local_row*NUM_WARPS + warp_idx);
                }
                CUTE_NO_UNROLL
                for (int k = 0; k < args.num_k_blocks; ++k) {
                    int4 next_indices[NUM_LOCAL_ROWS_PER_WARP];
                    const bool have_next = k + 1 < args.num_k_blocks;
                    bool is_all_rows_invalid = false;
                    if (!(0 <= indices[0].x && indices[0].x < params.s_kv)) {
                        uint32_t negative_sign = 0x80000000u;
                        int min_indices = params.s_kv;
                        CUTE_UNROLL
                        for (int local_row = 0; local_row < NUM_LOCAL_ROWS_PER_WARP; ++local_row) {
                            negative_sign &= uint32_t(indices[local_row].x)
                                           & uint32_t(indices[local_row].y)
                                           & uint32_t(indices[local_row].z)
                                           & uint32_t(indices[local_row].w);
                            min_indices = min(min_indices, int4_min(indices[local_row]));
                        }
                        is_all_rows_invalid = min_indices == params.s_kv || negative_sign != 0;
                    }
                    bool should_skip_tma = is_all_rows_invalid && k >= NUM_BUFS;    // Don't skip TMA for the first NUM_BUFS turns to swipe out invalid values in kv buffer
                    if (have_next) {
                        CUTE_UNROLL
                        for (int local_row = 0; local_row < NUM_LOCAL_ROWS_PER_WARP; ++local_row) {
                            next_indices[local_row] = __ldg((int4*)(gIndices + (k+1)*B_TOPK) + local_row*NUM_WARPS + warp_idx);
                        }
                    }
                    
                    if (k == 1) {
                        // Since Q shares its smem slot with k["buffer idx of the 1st block"]
                        plan.bar_prologue_utccp.wait(args.outer_loop_phase);
                    } else if (k == 2) {
                        // Since o_buf coincidences with k["buffer idx of the 2nd block"]
                        plan.bar_o_write_back_done.wait(args.outer_loop_phase);
                    }
                    
                    // Copy K
                    auto [buf_idx, bar_phase] = rs.get<NUM_BUFS>();
                    plan.bar_sv_done[buf_idx].wait(bar_phase^1);
                    bf16* sK_base = plan.u.qko_slots[buf_idx].data() + warp_idx*4*64;
    
                    if (!should_skip_tma) {
                        static_assert(NUM_LOCAL_ROWS_PER_WARP == 4 && B_TOPK == 64 && D_V == 512);
                        uint32_t destination_base = cute::cast_smem_ptr_to_uint(sK_base);
                        issue_kv_tile(
                            &(tma_params.tensor_map_kv), destination_base,
                            cute::cast_smem_ptr_to_uint(&plan.bar_kv_ready[buf_idx][0]),
                            cute::cast_smem_ptr_to_uint(&plan.bar_kv_ready[buf_idx][1]),
                            indices[0], indices[1], indices[2], indices[3]
                        );
                    } else {
                        // NOTE See head128/phase1.cuh for this TMA skipping technique
                        CUTE_UNROLL
                        for (int part_idx = 0; part_idx < 2; ++part_idx)
                            plan.bar_kv_ready[buf_idx][part_idx].complete_transaction(NUM_LOCAL_ROWS_PER_WARP*4*D_V/2*sizeof(bf16));
                    }

                    if (have_next) {
                        CUTE_UNROLL
                        for (int local_row = 0; local_row < NUM_LOCAL_ROWS_PER_WARP; ++local_row) {
                            indices[local_row] = next_indices[local_row];
                        }
                    }
                    rs.update();
                }
                if (args.num_k_blocks <= 2) {
                    plan.bar_o_write_back_done.wait(args.outer_loop_phase);
                }
                plan.bar_o_write_back_done_waited.arrive();
            }
            __syncwarp();
        });
    } else {
        // MMA warp
        if (warp_idx == 8 && elect_one_sync()) {
            // Allocate tmem tensors
            TiledMMA tiled_mma_P_sQ = TiledMMA_P_sQ{};
            TiledMMA tiled_mma_P_tQ = TiledMMA_P_tQ{};
            TiledMMA tiled_mma_O = TiledMMA_O{};
            // NOTE These tXXX tensors are only for a forged layout (so that CuTe is able to generate correct address in cute::gemm)
            Tensor tP = partition_fragment_C(tiled_mma_P_tQ, Shape<Int<MMA_M>, Int<B_TOPK>>{});
            Tensor tQ_part0 = tiled_mma_P_tQ.get_slice(_0{}).make_fragment_A(
                partition_shape_A(tiled_mma_P_tQ, Shape<Int<MMA_M>, Int<D_V/2-D_sQ>>{})
            );
            Tensor tQ_part1 = tiled_mma_P_tQ.get_slice(_0{}).make_fragment_A(
                partition_shape_A(tiled_mma_P_tQ, Shape<Int<MMA_M>, Int<D_V/2>>{})
            );
            Tensor tO = partition_fragment_C(tiled_mma_O, Shape<Int<MMA_M>, Int<D_V>>{});
            tP.data().get() = tmem_cols::P;
            tQ_part0.data().get() = tmem_cols::Q;
            tQ_part1.data().get() = tmem_cols::Q + (D_V/2-D_sQ)/2;
            tO.data().get() = tmem_cols::O;
            static_assert(NUM_BUFS == 3);
            bool have_prefetched_q = false;
            
            run_outer_loop([&](const OuterloopArgs &args) {
                // Copy Q into k["buffer idx of the 1st block"+1]
                // NOTE. As we reach here, we must have already issued the last O gemm of the last round, which means that the penultimate O gemm must be finished (since the last O gemm |-> bar_so_ready (the last S is ready) |-> the penultimate O gemm must be finished). So the corresponding K buffer must be free.
                int q_slot_idx = rs.offset_by(+1).get<NUM_BUFS>().first;
                if (!have_prefetched_q) {
                    issue_q_tma(args.s_q_idx, q_slot_idx);
                }
                issue_q_utccp(args.outer_loop_phase, q_slot_idx);

                uint32_t previous_kv_buf_idx;
                CUTE_NO_UNROLL
                for (int k = 0; k < args.num_k_blocks+1; ++k) {
                    uint32_t pv_buf_idx;
                    if (k > 0) {
                        pv_buf_idx = previous_kv_buf_idx;
                    }
                    if (k < args.num_k_blocks) {
                        // Pi = QKi^T
                        auto [buf_idx, bar_phase] = rs.get<NUM_BUFS>();
                        previous_kv_buf_idx = buf_idx;
                        bf16* sK_base = plan.u.qko_slots[buf_idx].data();
                        Tensor sQ = make_tensor(make_smem_ptr(plan.q_shared.data()), SmemLayoutQTiles<D_sQ/64>{});
                        Tensor sK_sQ = make_tensor(make_smem_ptr(sK_base), SmemLayoutKTiles<D_sQ/64>{});
                        Tensor sK_tQ0 = make_tensor(make_smem_ptr(sK_base + B_TOPK*D_sQ), SmemLayoutKTiles<(D_V/2-D_sQ)/64>{});
                        Tensor sK_tQ1 = make_tensor(make_smem_ptr(sK_base + B_TOPK*(D_V/2)), SmemLayoutKTiles<D_V/2/64>{});
    
                        auto [__, binary_bar_phase] = rs.get<1>();
                        plan.bar_p_free.wait(binary_bar_phase^1);
                        ku::tcgen05_after_thread_sync();
                        
                        // Wait for K
                        if (k == 0) {
                            plan.bar_prologue_utccp.wait(args.outer_loop_phase);
                        }
                        plan.bar_kv_ready[buf_idx][0].arrive_and_expect_tx(B_TOPK*D_V/2*sizeof(bf16));
                        plan.bar_kv_ready[buf_idx][0].wait(bar_phase);
                        ku::tcgen05_after_thread_sync();
                        // First half: shared Q[0:128], then TMEM Q[128:256].
                        ku::utcmma_ss(tiled_mma_P_sQ, sQ, sK_sQ, tP, true);
                        ku::utcmma_ts(tiled_mma_P_tQ, tQ_part0, sK_tQ0, tP, false);

                        plan.bar_kv_ready[buf_idx][1].arrive_and_expect_tx(B_TOPK*D_V/2*sizeof(bf16));
                        plan.bar_kv_ready[buf_idx][1].wait(bar_phase);
                        ku::tcgen05_after_thread_sync();
                        ku::utcmma_ts(tiled_mma_P_tQ, tQ_part1, sK_tQ1, tP, false);
                        ku::umma_arrive_noelect(plan.bar_qk_done[buf_idx]);
                    }
                    if (k == args.num_k_blocks) {
                        // This commit follows the last QK and penultimate PV.
                        // Both Qshared and next query's temporary Q slot are free.
                        auto [q_free_slot, q_free_phase] = rs.offset_by(-2).get<NUM_BUFS>();
                        plan.bar_sv_done[q_free_slot].wait(q_free_phase);
                        plan.bar_clc_full.wait(args.outer_loop_phase);
                        auto next_query = ku::get_clc_query_response<true>(plan.clc_response_obj);
                        if (next_query.is_valid) {
                            int next_q_slot = rs.offset_by(+1).get<NUM_BUFS>().first;
                            issue_q_tma(next_query.x, next_q_slot);
                            have_prefetched_q = true;
                        }
                    }
                    if (k > 0) {
                        // O += S(i-1)V(i-1)
                        const auto buf_idx = pv_buf_idx;
    
                        Tensor sS = make_tensor(make_smem_ptr(plan.s), SmemLayoutS{});
                        Tensor sV = make_tensor(make_smem_ptr(plan.u.qko_slots[buf_idx].data()), SmemLayoutV{});
    
                        // Wait for S(i-1) and O to be scaled
                        auto [__, binary_bar_phase] = rs.offset_by(-1).get<1>();
                        plan.bar_so_ready.wait(binary_bar_phase);
                        ku::tcgen05_after_thread_sync();
    
                        // O += sS @ sV
                        ku::utcmma_ss(tiled_mma_O, sS, sV, tO, k == 1);
                        ku::umma_arrive_noelect(plan.bar_sv_done[buf_idx]);
                    }

                    rs.update();
                }
                rs = rs.offset_by(-1);
            });
        } else if (warp_idx == 9) {
            // KV valid loading + CLC producer warp
            if (lane_idx < B_TOPK/8) {
                run_outer_loop([&](const OuterloopArgs &args) {
                    int* gIndices = params.indices + args.s_q_idx*params.stride_indices_s_q; // [topk]
                    CUTE_NO_UNROLL
                    for (int k = 0; k < args.num_k_blocks; ++k) {
                        char k_validness_mask = load_indices_and_generate_mask(
                            lane_idx,
                            gIndices + k*B_TOPK,
                            params.s_kv,
                            k*B_TOPK,
                            args.topk_length
                        );
    
                        auto [buf_idx, bar_phase] = rs.get<NUM_BUFS>();
                        plan.bar_k_valid_free[buf_idx].wait(bar_phase^1);
                        plan.is_k_valid[buf_idx][lane_idx] = k_validness_mask;
                        plan.bar_k_valid_ready[buf_idx].arrive();

                        rs.update();
                    }
                });
            } else if (lane_idx == B_TOPK/8) {
                run_outer_loop([&](const OuterloopArgs &args) {
                    plan.bar_clc_empty.wait(args.outer_loop_phase^1);
                    ku::issue_clc_query(plan.bar_clc_full, plan.clc_response_obj);
                    plan.bar_clc_full.arrive_and_expect_tx(sizeof(plan.clc_response_obj));
                });
            }
        }
    }

#else
    if (cute::thread0()) {
        CUTE_INVALID_CONTROL_PATH("This kernel only supports sm100");
    }
#endif
}

template<typename Kernel, typename TmaParams>
__global__ void __launch_bounds__(Kernel::NUM_THREADS, 1, 1)
sparse_attn_fwd_kernel(__grid_constant__ const SparseAttnFwdParams params, __grid_constant__ const TmaParams tma_params) {
    Kernel::sparse_attn_fwd_kernel_devfunc(params, tma_params);
}

void KernelTemplate::run(const SparseAttnFwdParams& params) {
    KU_ASSERT(params.h_kv == 1);
    KU_ASSERT(params.topk % B_TOPK == 0);   // To save some boundry checkings
    KU_ASSERT(params.topk >= 128);  // To simplify synchronizations between outer loop boundries
    KU_ASSERT(params.h_q >= 1 && params.h_q <= MMA_M);  // Q rows beyond h_q are zero-filled padding rows
    KU_ASSERT(params.d_qk == D_QK);

    auto shape_QS = make_shape(params.h_q, D_sQ, params.s_q);
    auto tma_QS = cute::make_tma_copy(
        SM90_TMA_LOAD{},
        make_tensor(
            make_gmem_ptr((bf16*)params.q),
            make_layout(
                shape_QS,
                make_stride(params.stride_q_h_q, _1{}, params.stride_q_s_q)
            )
        ),
        SmemLayoutQTiles<D_sQ/64>{}
    );
    auto shape_QT = make_shape(params.h_q, D_tQ, params.s_q);
    auto tma_QT = cute::make_tma_copy(
        SM90_TMA_LOAD{},
        make_tensor(
            make_gmem_ptr((bf16*)params.q + D_sQ),
            make_layout(
                shape_QT,
                make_stride(params.stride_q_h_q, _1{}, params.stride_q_s_q)
            )
        ),
        SmemLayoutQTiles<D_tQ/64>{}
    );

    auto shape_O = make_shape(params.h_q, params.d_v, params.s_q);
    auto tma_O = cute::make_tma_copy(
        SM90_TMA_STORE{},
        make_tensor(
            make_gmem_ptr((bf16*)params.out),
            make_layout(
                shape_O,
                make_stride(params.d_v, _1{}, params.h_q*params.d_v)
            )
        ),
        SmemLayoutOTiles<1>{}
    );

    CUtensorMap tensor_map_kv;
    {
        uint64_t size[2] = {D_V, (unsigned long)params.s_kv};
        uint64_t stride[1] = {params.stride_kv_s_kv*sizeof(bf16)};
        uint32_t box_size[2] = {64, 1};
        uint32_t elem_stride[2] = {1, 1};
        CUresult res = CUTLASS_CUDA_DRIVER_WRAPPER_CALL(cuTensorMapEncodeTiled)(
            &tensor_map_kv,
            CUtensorMapDataType::CU_TENSOR_MAP_DATA_TYPE_BFLOAT16,
            2,
            params.kv,
            size,
            stride,
            box_size,
            elem_stride,
            CUtensorMapInterleave::CU_TENSOR_MAP_INTERLEAVE_NONE,
            CUtensorMapSwizzle::CU_TENSOR_MAP_SWIZZLE_128B,
            CUtensorMapL2promotion::CU_TENSOR_MAP_L2_PROMOTION_L2_256B,
            CUtensorMapFloatOOBfill::CU_TENSOR_MAP_FLOAT_OOB_FILL_NONE
        );
        KU_ASSERT(res == CUresult::CUDA_SUCCESS);
    }

    TmaParams<
        decltype(shape_QS), decltype(tma_QS),
        decltype(shape_QT), decltype(tma_QT),
        decltype(shape_O), decltype(tma_O)
    > tma_params = {
        shape_QS, tma_QS,
        shape_QT, tma_QT,
        shape_O, tma_O,
        tensor_map_kv
    };
    auto kernel = &sparse_attn_fwd_kernel<KernelTemplate, decltype(tma_params)>;

    constexpr size_t smem_size = sizeof(SharedMemoryPlan);
    KU_CUDA_CHECK(cudaFuncSetAttribute(kernel, cudaFuncAttributeMaxDynamicSharedMemorySize, smem_size));

    kernel<<<params.s_q, NUM_THREADS, smem_size, params.stream>>>(params, tma_params);
    KU_CHECK_KERNEL_LAUNCH();
}

}

