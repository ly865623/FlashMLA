#!/usr/bin/env python3
"""Run the original head64 workloads with reproducible seeds and raw timing.

Example (the package root contains a built ``flash_mla`` directory)::

    CUDA_VISIBLE_DEVICES=GPU-... python scripts/kda_bench.py \
        --package-root runs/baseline/package --output runs/baseline/timing.json

``--profile-s-kv 4096`` generates the same input and launches attention once,
without invoking the CUPTI benchmark. Run that mode under Nsight Compute.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import statistics
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = REPO_ROOT / "tests/test-sparse-prefill.py"
WORKLOADS = (4096, 8192, 32768)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def instrument_source(source: str, *, profile: bool) -> str:
    """Keep run_test and its parameters intact; select after original seeding."""
    anchor = "    testcases = filtered_testcases\n"
    if source.count(anchor) != 1:
        raise RuntimeError("Original testcase selection changed; review the runner")
    injected = anchor + """
    if len(testcases) != 316:
        raise RuntimeError(f"Expected 316 original CUDA cases, got {len(testcases)}")
    for _kda_case in testcases:
        if _kda_case.seed == -1:
            _kda_case.seed = _counter.next()
    testcases = [p for p in testcases if p.h_q == 64 and p.num_runs > 0]
    _kda_validate_cases(testcases)
"""
    if profile:
        stop = "    failed_cases = []\n"
        if source.count(stop) != 1:
            raise RuntimeError("Original test loop changed; review the runner")
        source = source.split(stop, 1)[0]
    else:
        # The original full suite cools down before its first performance case.
        # Filtering makes that case first, so restore its initial cooldown.
        injected += "    time.sleep(0.3)\n"
    return source.replace(anchor, injected)


def validate_cases(cases: list[Any]) -> None:
    expected = [
        (4096, s_kv, 640, 64, 1, 512, 512, 310 + i, 10, True, False, True)
        for i, s_kv in enumerate(WORKLOADS)
    ]
    actual = [
        (p.s_q, p.s_kv, p.topk, p.h_q, p.h_kv, p.d_qk, p.d_v,
         p.seed, p.num_runs, p.have_attn_sink, p.have_topk_length,
         p.check_correctness)
        for p in cases
    ]
    if actual != expected:
        raise RuntimeError(f"Original benchmark workloads changed: {actual!r}")


def load_package(package_root: Path) -> tuple[Any, dict[str, Any]]:
    expected_init = package_root / "flash_mla/__init__.py"
    if not expected_init.is_file():
        raise ValueError(f"--package-root must contain flash_mla: {package_root}")
    if any(name == "flash_mla" or name.startswith("flash_mla.") for name in sys.modules):
        raise RuntimeError("flash_mla was imported before selecting --package-root")
    # An archived package takes precedence over both the current source tree
    # and editable installations from other worktrees.
    sys.path[:0] = [str(package_root), str(REPO_ROOT / "tests"), str(REPO_ROOT)]
    package = importlib.import_module("flash_mla")
    if Path(package.__file__).resolve() != expected_init.resolve():
        raise RuntimeError(f"Loaded the wrong flash_mla package: {package.__file__}")
    info = importlib.import_module("flash_mla._build_info")
    if info.BACKEND != "cuda":
        raise RuntimeError(f"Expected CUDA package, found {info.BACKEND}")
    extension = (expected_init.parent / info.EXTENSION).resolve()
    import torch

    if str(extension) not in {str(Path(p).resolve()) for p in torch.ops.loaded_libraries}:
        raise RuntimeError(f"Expected extension was not loaded: {extension}")
    modules = {}
    for name, module in sorted(sys.modules.items()):
        if name == "flash_mla" or name.startswith("flash_mla."):
            filename = getattr(module, "__file__", None)
            if filename:
                path = Path(filename).resolve()
                if not path.is_relative_to(expected_init.parent.resolve()):
                    raise RuntimeError(f"Mixed flash_mla package origins: {path}")
                modules[name] = {"path": str(path), "sha256": sha256(path)}
    return torch, {
        "package_root": str(package_root),
        "modules": modules,
        "extension": {"path": str(extension), "sha256": sha256(extension)},
    }


def check_device(torch: Any, expected_uuid: str) -> dict[str, Any]:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != expected_uuid:
        raise RuntimeError("CUDA_VISIBLE_DEVICES changed during this run")
    if torch.cuda.device_count() != 1:
        raise RuntimeError("Exactly one CUDA device must be visible")
    props = torch.cuda.get_device_properties(0)
    actual_uuid = str(getattr(props, "uuid", ""))
    if actual_uuid.removeprefix("GPU-").lower() != expected_uuid[4:].lower():
        raise RuntimeError(f"cuda:0 UUID {actual_uuid!r} differs from {expected_uuid!r}")
    return {
        "cuda_visible_devices": expected_uuid,
        "logical_device": "cuda:0",
        "uuid": actual_uuid,
        "name": props.name,
        "compute_capability": [props.major, props.minor],
        "total_memory_bytes": props.total_memory,
    }


def run(args: argparse.Namespace, report: dict[str, Any]) -> None:
    gpu_uuid = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if not re.fullmatch(r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", gpu_uuid):
        raise ValueError("Set CUDA_VISIBLE_DEVICES to one complete GPU UUID, not an index")
    torch, provenance = load_package(args.package_root.resolve())
    report.update(provenance)
    report["device"] = check_device(torch, gpu_uuid)
    report["environment"] = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": str(torch.__version__),
        "torch_cuda_version": torch.version.cuda,
        "cuda_module_loading": os.environ.get("CUDA_MODULE_LOADING"),
        "cuda_launch_blocking": os.environ.get("CUDA_LAUNCH_BLOCKING"),
    }
    import kernelkit as kk

    if not kk.is_on_cuda_platform():
        raise RuntimeError("The original tests must detect the CUDA platform")
    if args.profile_s_kv is None and kk.is_using_profiling_tools():
        raise RuntimeError("Benchmark mode cannot run under an external profiler; use --profile-s-kv")

    source = TEST_PATH.read_text()
    modified = instrument_source(source, profile=args.profile_s_kv is not None)
    report["test_source"] = {"path": str(TEST_PATH), "sha256": sha256(TEST_PATH)}
    report["executed_source_sha256"] = hashlib.sha256(modified.encode()).hexdigest()
    report["runner"] = {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))}
    code = compile(modified, str(TEST_PATH), "exec")
    original_argv = sys.argv
    original_bench = kk.bench
    namespace: dict[str, Any] = {}
    round_number = 0

    def capture_bench(*bench_args: Any, **bench_kwargs: Any) -> Any:
        # Forward the exact original call, including the original default L2 flush.
        result = original_bench(*bench_args, **bench_kwargs)
        p = namespace["test"]
        matched = [name for name in result.get_kernel_names() if "sparse_attn_fwd" in name]
        if len(matched) != 1:
            raise RuntimeError(f"Expected one sparse attention kernel, got {matched!r}")
        ranges = result.time_ranges[matched[0]]
        if result.num_tests != p.num_runs or len(ranges) != p.num_runs:
            raise RuntimeError(f"Expected {p.num_runs} kernel samples, got {len(ranges)}")
        report["measurements"].append({
            "round": round_number,
            "case": dataclasses.asdict(p),
            "kernel_name": matched[0],
            "num_tests": result.num_tests,
            "time_ranges_s": [list(pair) for pair in ranges],
            "samples_s": [end - start for start, end in ranges],
            "mean_s": result.get_kernel_time("sparse_attn_fwd"),
            "correctness": "pending",
        })
        write_report(args.output, report)
        return result

    try:
        sys.argv = [str(TEST_PATH), "--run-to-finish"]
        if args.profile_s_kv is not None:
            namespace = {"__name__": "__main__", "__file__": str(TEST_PATH),
                         "_kda_validate_cases": validate_cases}
            exec(code, namespace)
            p = next(p for p in namespace["testcases"] if p.s_kv == args.profile_s_kv)
            lib = namespace["lib"]
            with torch.inference_mode():
                testcase = lib.generate_testcase(p)
                lib.device_synchronize()
                torch.cuda.nvtx.range_push("profile_target")
                try:
                    outputs = lib.run_flash_mla_sparse_fwd(p, testcase)
                finally:
                    torch.cuda.nvtx.range_pop()
                lib.device_synchronize()
            report["profile"] = {
                "case": dataclasses.asdict(p),
                "attention_launches": 1,
                "correctness": "not_checked_in_profile_mode",
                "output_shapes": [list(output.shape) for output in outputs],
            }
        else:
            kk.bench = capture_bench
            for round_number in range(1, args.rounds + 1):
                check_device(torch, gpu_uuid)
                print(f"KDA benchmark round {round_number}/{args.rounds}", flush=True)
                # Executing the original module recreates its Counter and all cases.
                namespace = {"__name__": "__main__", "__file__": str(TEST_PATH),
                             "_kda_validate_cases": validate_cases}
                round_completed = False
                try:
                    exec(code, namespace)
                    round_completed = True
                finally:
                    failed_seeds = {p.seed for p in namespace.get("failed_cases", [])}
                    for measurement in report["measurements"]:
                        if measurement["round"] == round_number:
                            measurement["correctness"] = (
                                "failed" if measurement["case"]["seed"] in failed_seeds
                                else "passed" if round_completed else "not_confirmed"
                            )
                    write_report(args.output, report)
            report["summary"] = {}
            for s_kv in WORKLOADS:
                means = [m["mean_s"] for m in report["measurements"] if m["case"]["s_kv"] == s_kv]
                report["summary"][str(s_kv)] = {
                    "round_means_s": means,
                    "mean_s": statistics.mean(means),
                    "median_s": statistics.median(means),
                    "stdev_s": statistics.stdev(means) if len(means) > 1 else 0.0,
                }
        check_device(torch, gpu_uuid)
    finally:
        kk.bench = original_bench
        sys.argv = original_argv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="Destination JSON for provenance and raw samples")
    parser.add_argument("--rounds", type=int, default=5, help="Outer benchmark rounds (default: 5)")
    parser.add_argument("--package-root", type=Path, default=REPO_ROOT,
                        help="Directory containing the exact built flash_mla package to load")
    parser.add_argument("--profile-s-kv", type=int, choices=WORKLOADS,
                        help="Generate one original workload and launch attention once, without CUPTI benchmarking")
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    args.output = args.output.resolve()
    if args.output.exists():
        parser.error(f"--output already exists; choose a new path to preserve raw data: {args.output}")
    report: dict[str, Any] = {
        "schema_version": 1,
        "mode": "profile" if args.profile_s_kv is not None else "benchmark",
        "status": "running",
        "started_at": utc_now(),
        "requested_rounds": args.rounds if args.profile_s_kv is None else None,
        "measurements": [],
    }
    write_report(args.output, report)
    try:
        run(args, report)
        report["status"] = "passed" if args.profile_s_kv is None else "profile_launch_completed"
    except BaseException as error:
        report["status"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report["finished_at"] = utc_now()
        write_report(args.output, report)


if __name__ == "__main__":
    main()
