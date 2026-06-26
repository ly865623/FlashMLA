#include "../phase1.h"
#include "../phase1.cuh"

namespace sm100::fwd_for_small_topk::head128 {

template void run_fwd_for_small_topk_phase1_kernel<SparseAttnFwdMode::Prefill, 512>(const SparseAttnFwdParams& params);

}

// Emit host accessors (prof_reset_buffer / prof_copy_buffer) bound to THIS TU's
// g_prof_buf -- the same copy the prefill kernel above writes at runtime.
FLASHMLA_PROF_DEFINE_HOST_ACCESSORS()
