#include <pybind11/pybind11.h>
#include <torch/extension.h>
#include <tuple>

#include "sparse_fwd.h"
#include "sparse_decode.h"
#include "dense_decode.h"
#include "dense_fwd.h"
#include "sm100/prefill/sparse/fwd_for_small_topk/head128/prof_host.h"

// clock64 profiler for fwd_for_small_topk prefill (active only when the kernel was
// built with FLASHMLA_PROF_SMALL_TOPK; otherwise returns a zeroed buffer).
static void small_topk_prof_reset() {
    sm100::fwd_for_small_topk::head128::prof_reset_buffer();
}
static std::tuple<at::Tensor, int64_t> small_topk_prof_get() {
    using namespace sm100::fwd_for_small_topk::head128;
    at::Tensor buf = torch::zeros(
        {(long)PROF_MAX_ITERS, (long)PROF_NUM_SLOTS},
        torch::dtype(torch::kInt64).device(torch::kCPU)
    );
    unsigned int nblk = 0;
    prof_copy_buffer((unsigned long long*)buf.data_ptr<int64_t>(), &nblk);
    return std::make_tuple(buf, (int64_t)nblk);
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.doc() = "FlashMLA";
    m.def("sparse_decode_fwd", &sparse_attn_decode_interface);
    m.def("dense_decode_fwd", &dense_attn_decode_interface);
    m.def("sparse_prefill_fwd", &sparse_attn_prefill_interface);
    m.def("dense_prefill_fwd", &FMHACutlassSM100FwdRun);
    m.def("dense_prefill_bwd", &FMHACutlassSM100BwdRun);
    m.def("small_topk_prof_reset", &small_topk_prof_reset, "Zero the fwd_for_small_topk clock64 profiler buffer");
    m.def("small_topk_prof_get", &small_topk_prof_get, "Fetch (buf[PROF_MAX_ITERS,PROF_NUM_SLOTS] int64, nblk) from the profiler");
}
