#pragma once
// Device-side clock64 profiler storage + stamp helpers for fwd_for_small_topk.
//
// This project builds WITHOUT -rdc (relocatable device code), so a __device__
// symbol cannot be shared across translation units. We therefore declare the
// buffer `static __device__` (internal linkage): every TU that includes this
// header gets its OWN private copy. The host accessors emitted by
// FLASHMLA_PROF_DEFINE_HOST_ACCESSORS() read the copy of the SAME TU they are
// instantiated in -- so we emit them in the prefill instantiation TU, which is
// exactly the TU whose kernel writes the buffer at runtime.
//
// The storage exists unconditionally (a few KB of device .bss, unused when the
// macro is off). Only the stamp call sites in phase1.cuh are guarded by
// FLASHMLA_PROF_SMALL_TOPK, so the kernel hot path is byte-identical when off.

#include <cstdint>
#include <cuda_runtime.h>

#include "prof_host.h"

namespace sm100::fwd_for_small_topk::head128 {

static __device__ unsigned long long g_prof_buf[PROF_MAX_ITERS][PROF_NUM_SLOTS];
static __device__ unsigned int       g_prof_nblk;

#ifdef FLASHMLA_PROF_SMALL_TOPK
// Sample only the first cluster's cta0 (blockIdx.x==0) and only its first tile.
__device__ __forceinline__ bool prof_active(int prof_tile) {
    return blockIdx.x == 0 && prof_tile == 0;
}
__device__ __forceinline__ void prof_stamp(int k, int slot, unsigned long long v) {
    if ((unsigned)k < (unsigned)PROF_MAX_ITERS) g_prof_buf[k][slot] = v;
}
#endif

}

// Emit host accessors bound to the g_prof_buf of the TU that invokes this macro.
// Invoke exactly once, in the prefill instantiation TU.
#define FLASHMLA_PROF_DEFINE_HOST_ACCESSORS()                                       \
namespace sm100::fwd_for_small_topk::head128 {                                       \
    void prof_reset_buffer() {                                                       \
        static unsigned long long zero[PROF_MAX_ITERS][PROF_NUM_SLOTS] = {};         \
        cudaMemcpyToSymbol(g_prof_buf, zero, sizeof(g_prof_buf));                    \
        unsigned int z = 0;                                                          \
        cudaMemcpyToSymbol(g_prof_nblk, &z, sizeof(z));                              \
    }                                                                               \
    void prof_copy_buffer(unsigned long long* dst, unsigned int* nblk) {            \
        cudaMemcpyFromSymbol(dst, g_prof_buf, sizeof(g_prof_buf));                   \
        cudaMemcpyFromSymbol(nblk, g_prof_nblk, sizeof(*nblk));                      \
    }                                                                               \
}
