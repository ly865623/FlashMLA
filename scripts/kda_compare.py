#!/usr/bin/env python3
"""Interleave archived baseline/candidate benchmarks under an outer kda_run lock.

Runs A0 B0 A1 B1 ... A<pairs>, always using kda_bench.py --rounds 1.
Reports ratios and drift; it never automatically accepts an optimization.
GPU isolation must separately pass the enclosing kda_run.py manifest.
"""

import argparse
import ast
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "scripts/kda_bench.py"
SHAPES = ("4096", "8192", "32768")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, data):
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def package_snapshot(root):
    package = root / "flash_mla"
    tree = ast.parse((package / "_build_info.py").read_text())
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("BACKEND", "EXTENSION"):
                    constants[target.id] = ast.literal_eval(node.value)
    if constants.get("BACKEND") != "cuda":
        raise ValueError(f"Expected CUDA package: {root}")
    extension = (package / constants["EXTENSION"]).resolve()
    if not extension.is_relative_to(package.resolve()):
        raise ValueError(f"Extension escapes package: {extension}")
    files = {str(path.relative_to(root)): sha256(path)
             for path in sorted(package.rglob("*.py"))}
    files[str(extension.relative_to(root))] = sha256(extension)
    return {"package_root": str(root), "extension": {
        "path": str(extension), "sha256": sha256(extension)}, "files": files}


def checked_measurements(report, *, one_round=False):
    if report.get("status") != "passed" or report.get("mode") != "benchmark":
        raise ValueError("Benchmark did not pass")
    if one_round and report.get("requested_rounds") != 1:
        raise ValueError("Expected exactly one benchmark round")
    grouped = {shape: [] for shape in SHAPES}
    for item in report["measurements"]:
        shape = str(item["case"]["s_kv"])
        if shape not in grouped or item.get("correctness") != "passed":
            raise ValueError(f"Unexpected workload or correctness: {shape}")
        samples = item["samples_s"]
        if len(samples) != 10 or item["num_tests"] != 10:
            raise ValueError("Original benchmark must retain ten kernel samples")
        if not all(isinstance(value, (int, float)) and math.isfinite(value) and value > 0
                   for value in samples):
            raise ValueError("Kernel times must be finite and positive")
        if not math.isclose(item["mean_s"], statistics.mean(samples), rel_tol=1e-10):
            raise ValueError("Recorded kernel mean differs from raw samples")
        grouped[shape].append(item)
    counts = {len(values) for values in grouped.values()}
    expected = 1 if one_round else report["requested_rounds"]
    if counts != {expected}:
        raise ValueError(f"Missing/duplicate workload measurements: counts={counts}")
    for shape, items in grouped.items():
        case = items[0]["case"]
        if any(item["case"] != case for item in items):
            raise ValueError(f"Workload parameters changed across rounds: {shape}")
    return grouped


def validate_report(report, snapshot, initial, initial_grouped):
    grouped = checked_measurements(report, one_round=True)
    if Path(report["package_root"]).resolve() != Path(snapshot["package_root"]):
        raise ValueError("Benchmark loaded a different package root")
    if report["extension"] != snapshot["extension"]:
        raise ValueError("Benchmark extension path/hash differs from pinned artifact")
    for module in report["modules"].values():
        path = Path(module["path"]).resolve()
        relative = str(path.relative_to(snapshot["package_root"]))
        if snapshot["files"].get(relative) != module["sha256"]:
            raise ValueError(f"Loaded Python module changed: {path}")
    for key in ("executed_source_sha256", "environment", "device"):
        if report[key] != initial[key]:
            raise ValueError(f"Comparison protocol differs from initial baseline: {key}")
    for key in ("test_source", "runner"):
        if report[key]["sha256"] != initial[key]["sha256"]:
            raise ValueError(f"Comparison source differs from initial baseline: {key}")
    for shape in SHAPES:
        if grouped[shape][0]["case"] != initial_grouped[shape][0]["case"]:
            raise ValueError(f"Comparison parameters differ from initial baseline: {shape}")
    return grouped


def stats(values):
    return {"values": values, "mean": statistics.mean(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values), "max": max(values)}


def ratios(speedup):
    return {"speedup": speedup, "speedup_pct": (speedup - 1) * 100,
            "elapsed_time_reduction_fraction": 1 - 1 / speedup,
            "elapsed_time_reduction_pct": (1 - 1 / speedup) * 100}


def summarize(controls, candidates, initial):
    shapes = {}
    for shape in SHAPES:
        a = [group[shape][0]["mean_s"] for group in controls]
        b = [group[shape][0]["mean_s"] for group in candidates]
        initial_means = [item["mean_s"] for item in initial[shape]]
        pairs = []
        for index, candidate_mean in enumerate(b):
            control_mean = math.sqrt(a[index] * a[index + 1])
            pairs.append({"pair": index, "control_before_mean_s": a[index],
                          "control_after_mean_s": a[index + 1],
                          "interpolated_control_mean_s": control_mean,
                          "candidate_mean_s": candidate_mean,
                          **ratios(control_mean / candidate_mean),
                          "adjacent_control_drift_ratio": a[index + 1] / a[index],
                          "adjacent_control_drift_pct": (a[index + 1] / a[index] - 1) * 100})
        shapes[shape] = {
            "baseline_round_means_s": stats(a), "candidate_round_means_s": stats(b),
            "initial_baseline_round_means_s": stats(initial_means),
            "baseline_round_sample_stdev_s": [statistics.stdev(group[shape][0]["samples_s"])
                                               for group in controls],
            "candidate_round_sample_stdev_s": [statistics.stdev(group[shape][0]["samples_s"])
                                                for group in candidates],
            "pairs": pairs,
            "paired": ratios(statistics.geometric_mean([pair["speedup"] for pair in pairs])),
            "pair_speedup_stats": stats([pair["speedup"] for pair in pairs]),
            "versus_initial_baseline": ratios(statistics.mean(initial_means) / statistics.mean(b)),
            "maximum_absolute_adjacent_control_drift_pct": max(
                abs(pair["adjacent_control_drift_pct"]) for pair in pairs),
        }
    aggregate_pairs = [
        {"pair": index, **ratios(statistics.geometric_mean([
            shapes[shape]["pairs"][index]["speedup"] for shape in SHAPES]))}
        for index in range(len(candidates))
    ]
    return {"shapes": shapes, "aggregate": {
        "weighting": "equal geometric weight across three workloads and pairs",
        "pairs": aggregate_pairs,
        "paired": ratios(statistics.geometric_mean([shapes[s]["paired"]["speedup"] for s in SHAPES])),
        "versus_initial_baseline": ratios(statistics.geometric_mean([
            shapes[s]["versus_initial_baseline"]["speedup"] for s in SHAPES])),
    }}


def execute(args, report, path):
    initial = json.loads(args.initial_baseline.read_text())
    initial_grouped = checked_measurements(initial)
    uuid = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if not re.fullmatch(r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", uuid):
        raise ValueError("CUDA_VISIBLE_DEVICES must be one full UUID set by outer kda_run")
    if initial["device"]["cuda_visible_devices"] != uuid:
        raise ValueError("GPU differs from initial baseline")
    snapshots = {"A": package_snapshot(args.baseline_package),
                 "B": package_snapshot(args.candidate_package)}
    report.update({"gpu_uuid": uuid, "packages": snapshots,
                   "baseline_matches_initial_artifact": (
                       snapshots["A"]["extension"]["sha256"] == initial["extension"]["sha256"]),
                   "initial_baseline": {"path": str(args.initial_baseline),
                                        "sha256": sha256(args.initial_baseline)},
                   "benchmark_runner": {"path": str(BENCH), "sha256": sha256(BENCH)}})
    write_json(args.output_dir / "initial-baseline.json", initial)
    write_json(path, report)
    controls, candidates = [], []
    sequence = [(label, index) for index in range(args.pairs) for label in ("A", "B")]
    sequence.append(("A", args.pairs))
    for label, index in sequence:
        name = f"{label}{index:02d}"
        timing_path = args.output_dir / f"{name}.json"
        log_path = args.output_dir / f"{name}.stdout.log"
        snapshot = snapshots[label]
        # Detect package mutation before every run, including Python helpers that
        # might not have been imported during the previous run.
        if package_snapshot(Path(snapshot["package_root"])) != snapshot:
            raise ValueError(f"Archived package mutated before {name}")
        if sha256(BENCH) != report["benchmark_runner"]["sha256"]:
            raise ValueError("Benchmark runner mutated during comparison")
        command = [sys.executable, str(BENCH), "--package-root", snapshot["package_root"],
                   "--rounds", "1", "--output", str(timing_path)]
        record = {"name": name, "version": label, "index": index, "argv": command,
                  "shell_command": shlex.join(command), "cwd": str(ROOT),
                  "timing_json": str(timing_path), "stdout_log": str(log_path),
                  "started_at": now(), "status": "running"}
        report["runs"].append(record)
        write_json(path, report)
        print(f"Running {name}: {shlex.join(command)}", flush=True)
        with log_path.open("xb") as output:
            result = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
        record.update({"finished_at": now(), "exit_code": result.returncode})
        if result.returncode:
            record["status"] = "failed"
            raise RuntimeError(f"{name} failed with exit code {result.returncode}; see {log_path}")
        measured = json.loads(timing_path.read_text())
        group = validate_report(measured, snapshot, initial, initial_grouped)
        if package_snapshot(Path(snapshot["package_root"])) != snapshot:
            raise ValueError(f"Archived package mutated during {name}")
        record.update({"status": "passed", "timing_json_sha256": sha256(timing_path),
                       "extension_sha256": measured["extension"]["sha256"],
                       "round_mean_s": {shape: group[shape][0]["mean_s"] for shape in SHAPES},
                       "round_sample_stdev_s": {
                           shape: statistics.stdev(group[shape][0]["samples_s"]) for shape in SHAPES}})
        (controls if label == "A" else candidates).append(group)
        write_json(path, report)
    report.update(summarize(controls, candidates, initial_grouped))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-package", required=True, type=Path)
    parser.add_argument("--candidate-package", required=True, type=Path)
    parser.add_argument("--initial-baseline", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--pairs", type=int, default=5)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    for field in ("baseline_package", "candidate_package", "initial_baseline", "output_dir"):
        setattr(args, field, getattr(args, field).resolve())
    if args.output_dir.exists():
        parser.error("--output-dir must be new; refusing to overwrite experiment data")
    args.output_dir.mkdir(parents=True)
    path = args.output_dir / "summary.json"
    report = {"schema_version": 1, "status": "running", "started_at": now(),
              "pairs_requested": args.pairs, "argv": sys.argv, "cwd": str(Path.cwd()),
              "python_executable": sys.executable, "runs": [],
              "decision": "not_made", "gpu_isolation_validity": "requires_outer_kda_run_manifest",
              "paired_speedup_formula": "sqrt(A_i * A_(i+1)) / B_i",
              "elapsed_time_reduction_formula": "1 - 1/speedup",
              "adjacent_control_drift_formula": "A_(i+1)/A_i - 1"}
    write_json(path, report)
    try:
        execute(args, report, path)
        report["status"] = "completed"
    except BaseException as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        if report["runs"] and report["runs"][-1]["status"] == "running":
            report["runs"][-1].update({"status": "failed", "error": report["error"]})
        raise
    finally:
        report["finished_at"] = now()
        write_json(path, report)
    print(json.dumps(report["aggregate"], indent=2), flush=True)


if __name__ == "__main__":
    main()
