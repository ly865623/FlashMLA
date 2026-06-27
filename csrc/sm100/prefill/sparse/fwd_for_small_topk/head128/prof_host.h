#pragma once
// Host-safe declarations for the fwd_for_small_topk clock64 profiler.
// Safe to include from plain C++ TUs (api.cpp) -- contains NO __device__ code.
// The device-side storage / stamp helpers live in prof.cuh.
//
// Layout: g_prof_buf[PROF_MAX_ITERS][PROF_NUM_SLOTS], uint64.
// Indexed by inner K-block index k. Each row holds absolute clock64() stamps
// (and one boolean) for the core recurrence edges of block k, recorded only for
// the first cluster's cta0 (blockIdx.x==0), first tile.

namespace sm100::fwd_for_small_topk::head128 {

// topk<=1280 => N_blk = ceil(topk/64) <= 20; 64 is ample headroom for one tile.
static constexpr int PROF_MAX_ITERS = 64;

// Slot indices into a row. Keep in sync with prof.cuh usage.
enum ProfSlot {
    PROF_ISSUE_P     = 0,  // W8 cta0: clock64 right before QK MMA (after P_empty+KV_full waits)
    PROF_ISSUE_O     = 1,  // W8 cta0: clock64 right before PV MMA (after S_O_full wait)
    PROF_QK_DONE     = 2,  // WG3 cta0 lane0: after bar_QK_done.wait returns
    PROF_P_EMPTY     = 3,  // WG3 cta0 lane0: at bar_P_empty.arrive (P-tmem freed -> unlocks QK_{k+1})
    PROF_SV_DONE     = 4,  // WG3 cta0 lane0: after bar_SV_done.wait returns
    PROF_S_O_FULL    = 5,  // WG3 cta0 lane0: at bar_S_O_full.arrive (S/O ready -> unlocks PV_k)
    PROF_DID_RESCALE = 6,  // WG3 cta0 lane0: 1 if rescale_O ran this block, else 0
    PROF_KV_WAIT     = 7,  // W8 cta0: clock64 right before bar_KV_full.wait (after bar_P_empty.wait)
                           //   -> T_KVwait[k] = ISSUE_P[k] - KV_WAIT[k] = pure KV-gather stall (env2)
    PROF_NUM_SLOTS   = 8
};

// Defined in the prefill instantiation TU via FLASHMLA_PROF_DEFINE_HOST_ACCESSORS().
// prof_reset_buffer: zero the device buffer before a profiled launch.
// prof_copy_buffer:  copy device buffer -> host dst (PROF_MAX_ITERS*PROF_NUM_SLOTS u64) and nblk.
void prof_reset_buffer();
void prof_copy_buffer(unsigned long long* dst, unsigned int* nblk);

}
