import os
from pathlib import Path
from datetime import datetime
import subprocess

from setuptools import setup, find_packages

from torch.utils.cpp_extension import (
    BuildExtension,
    CUDAExtension,
    IS_WINDOWS,
    CUDA_HOME
)


def is_flag_set(flag: str) -> bool:
    return os.getenv(flag, "FALSE").lower() in ["true", "1", "y", "yes"]

def get_features_args():
    features_args = []
    if is_flag_set("FLASH_MLA_DISABLE_FP16"):
        features_args.append("-DFLASH_MLA_DISABLE_FP16")
    return features_args

def get_prof_args():
    # clock64 instrumentation for fwd_for_small_topk prefill. Off by default.
    # FLASHMLA_PROF_MMA_LAT adds the W8 same-warp single-MMA-latency stamps (QK_SELF/PV_SELF);
    # it implies _SMALL_TOPK and SERIALIZES the sampled block (II/qk_occ/obs not valid then).
    args = []
    if any(is_flag_set(f) for f in ("FLASHMLA_PROF_SMALL_TOPK", "FLASHMLA_PROF_MMA_LAT")):
        args.append("-DFLASHMLA_PROF_SMALL_TOPK")
    if is_flag_set("FLASHMLA_PROF_MMA_LAT"):
        args.append("-DFLASHMLA_PROF_MMA_LAT")
    return args

def get_arch_flags():
    # Check NVCC Version
    # NOTE The "CUDA_HOME" here is not necessarily from the `CUDA_HOME` environment variable. For more details, see `torch/utils/cpp_extension.py`
    assert CUDA_HOME is not None, "PyTorch must be compiled with CUDA support"
    nvcc_version = subprocess.check_output(
        [os.path.join(CUDA_HOME, "bin", "nvcc"), '--version'], stderr=subprocess.STDOUT
    ).decode('utf-8')
    nvcc_version_number = nvcc_version.split('release ')[1].split(',')[0].strip()
    major, minor = map(int, nvcc_version_number.split('.'))
    print(f'Compiling using NVCC {major}.{minor}')

    DISABLE_SM100 = is_flag_set("FLASH_MLA_DISABLE_SM100")
    DISABLE_SM90 = is_flag_set("FLASH_MLA_DISABLE_SM90")
    if major < 12 or (major == 12 and minor <= 8):
        assert DISABLE_SM100, "sm100 compilation for Flash MLA requires NVCC 12.9 or higher. Please set FLASH_MLA_DISABLE_SM100=1 to disable sm100 compilation, or update your environment."    # TODO Implement this

    # The SM100-family target code can be overridden via FLASHMLA_SM100_CODE so the
    # same 2-SM Blackwell kernels can be built for Thor (sm_110a) instead of the
    # datacenter default sm_100f. E.g. FLASHMLA_SM100_CODE=110a for Jetson Thor.
    sm100_code = os.getenv("FLASHMLA_SM100_CODE", "100f")
    sm100_compute = sm100_code if sm100_code.endswith("a") else sm100_code  # compute_<code>
    arch_flags = []
    if not DISABLE_SM100:
        arch_flags.extend(["-gencode", f"arch=compute_{sm100_compute},code=sm_{sm100_code}"])
    if not DISABLE_SM90:
        arch_flags.extend(["-gencode", "arch=compute_90a,code=sm_90a"])
    return arch_flags

def get_nvcc_thread_args():
    nvcc_threads = os.getenv("NVCC_THREADS") or "32"
    return ["--threads", nvcc_threads]

subprocess.run(["git", "submodule", "update", "--init", "csrc/cutlass"])

this_dir = os.path.dirname(os.path.abspath(__file__))

if IS_WINDOWS:
    cxx_args = ["/O2", "/std:c++20", "/DNDEBUG", "/W0"]
else:
    cxx_args = ["-O3", "-std=c++20", "-DNDEBUG", "-Wno-deprecated-declarations"]

ext_modules = []
ext_modules.append(
    CUDAExtension(
        name="flash_mla.cuda",
        sources=[
            # API
            "csrc/api/api.cpp",

            # Misc kernels for decoding
            "csrc/smxx/decode/get_decoding_sched_meta/get_decoding_sched_meta.cu",
            "csrc/smxx/decode/combine/combine.cu",

            # sm90 dense decode
            "csrc/sm90/decode/dense/instantiations/fp16.cu",
            "csrc/sm90/decode/dense/instantiations/bf16.cu",

            # sm90 sparse decode
            "csrc/sm90/decode/sparse_fp8/instantiations/model1_persistent_h64.cu",
            "csrc/sm90/decode/sparse_fp8/instantiations/model1_persistent_h128.cu",
            "csrc/sm90/decode/sparse_fp8/instantiations/v32_persistent_h64.cu",
            "csrc/sm90/decode/sparse_fp8/instantiations/v32_persistent_h128.cu",

            # sm90 sparse prefill
            "csrc/sm90/prefill/sparse/fwd.cu",
            "csrc/sm90/prefill/sparse/instantiations/phase1_k512.cu",
            "csrc/sm90/prefill/sparse/instantiations/phase1_k512_topklen.cu",
            "csrc/sm90/prefill/sparse/instantiations/phase1_k576.cu",
            "csrc/sm90/prefill/sparse/instantiations/phase1_k576_topklen.cu",

            # sm100 dense prefill & backward
            "csrc/sm100/prefill/dense/fmha_cutlass_fwd_sm100.cu",
            "csrc/sm100/prefill/dense/fmha_cutlass_bwd_sm100.cu",

            # sm100 sparse prefill
            "csrc/sm100/prefill/sparse/fwd/head64/instantiations/phase1_k512.cu",
            "csrc/sm100/prefill/sparse/fwd/head64/instantiations/phase1_k576.cu",
            "csrc/sm100/prefill/sparse/fwd/head128/instantiations/phase1_k512.cu",
            "csrc/sm100/prefill/sparse/fwd/head128/instantiations/phase1_k576.cu",
            "csrc/sm100/prefill/sparse/fwd_for_small_topk/head128/instantiations/phase1_prefill_k512.cu",

            # sm100 sparse decode
            "csrc/sm100/decode/head64/instantiations/v32.cu",
            "csrc/sm100/decode/head64/instantiations/model1.cu",
            "csrc/sm100/prefill/sparse/fwd_for_small_topk/head128/instantiations/phase1_decode_k512.cu",
        ],
        extra_compile_args={
            "cxx": cxx_args + get_features_args(),
            "nvcc": [
                "-O3",
                "-std=c++20",
                "-DNDEBUG",
                "-D_USE_MATH_DEFINES",
                "-Wno-deprecated-declarations",
                "-U__CUDA_NO_HALF_OPERATORS__",
                "-U__CUDA_NO_HALF_CONVERSIONS__",
                "-U__CUDA_NO_HALF2_OPERATORS__",
                "-U__CUDA_NO_BFLOAT16_CONVERSIONS__",
                "--expt-relaxed-constexpr",
                "--expt-extended-lambda",
                "--use_fast_math",
                "--ptxas-options=-v,--register-usage-level=10,--warn-on-spills,--warn-on-local-memory-usage,--warn-on-double-precision-use",
                "-lineinfo",
                "--source-in-ptx",
            ] + get_features_args() + get_prof_args() + get_arch_flags() + get_nvcc_thread_args(),
        },
        include_dirs=[
            Path(this_dir) / "csrc",
            Path(this_dir) / "csrc" / "kerutils" / "include",   # TODO Remove me
            Path(this_dir) / "csrc" / "sm90",
            Path(this_dir) / "csrc" / "cutlass" / "include",
            Path(this_dir) / "csrc" / "cutlass" / "tools" / "util" / "include",
            # CUDA 13.x ships libcu++ (cuda/std/*) under include/cccl. nvcc finds it
            # automatically, but the host (g++) compile of api.cpp -- which pulls
            # cutlass.h -- needs it on the include path explicitly.
            Path(CUDA_HOME) / "include" / "cccl",
        ],
    )
)

try:
    cmd = ['git', 'rev-parse', '--short', 'HEAD']
    rev = '+' + subprocess.check_output(cmd).decode('ascii').rstrip()
except Exception as _:
    now = datetime.now()
    date_time_str = now.strftime("%Y-%m-%d-%H-%M-%S")
    rev = '+' + date_time_str


setup(
    name="flash_mla",
    version="1.0.0" + rev,
    packages=find_packages(include=['flash_mla']),
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExtension},
)
