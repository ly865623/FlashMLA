#!/usr/bin/env python3
"""Run one GPU experiment with a UUID lock and an auditable interference log.

Example: python scripts/kda_run.py --gpu GPU-... --output-dir runs/run-001 -- \
    /path/to/python tests/test-sparse-prefill.py --run-to-finish

The lock serializes cooperating KDA runners, not other users' GPU work. Every
foreign compute process observed during execution invalidates the measurement.
"""

import argparse
import csv
import datetime
import fcntl
import io
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time


GPU_FIELDS = (
    "index", "uuid", "name", "utilization.gpu", "memory.used", "memory.total",
    "temperature.gpu", "power.draw", "clocks.sm", "clocks.mem",
)
PROCESS_FIELDS = ("gpu_uuid", "pid", "process_name", "used_memory")
ENV_FIELDS = (
    "CUDA_VISIBLE_DEVICES", "CUDA_HOME", "CUDA_DEVICE_ORDER", "PATH",
    "LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONNOUSERSITE", "MAX_JOBS",
    "NVCC_THREADS", "FLASH_MLA_BUILD_TARGET_PLATFORM",
    "FLASH_MLA_SKIP_REG_SPILL_CHECK", "KINETO_LOG_LEVEL",
)


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def query_csv(gpu, fields, kind):
    command = [
        "nvidia-smi", "-i", gpu, f"--query-{kind}={','.join(fields)}",
        "--format=csv,noheader,nounits",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError(f"{shlex.join(command)}: {result.stderr.strip()}")
    rows = []
    for values in csv.reader(io.StringIO(result.stdout), skipinitialspace=True):
        if not values:
            continue
        if len(values) != len(fields):
            raise ValueError(f"Unexpected nvidia-smi row: {values!r}")
        rows.append(dict(zip(fields, (value.strip() for value in values))))
    return rows


def snapshot(gpu):
    record = {"time": timestamp(), "errors": []}
    try:
        rows = query_csv(gpu, GPU_FIELDS, "gpu")
        if len(rows) != 1 or rows[0]["uuid"] != gpu:
            raise ValueError(f"Expected exact UUID {gpu}, got {rows!r}")
        record["gpu"] = rows[0]
    except Exception as exc:
        record["errors"].append(f"gpu_query: {type(exc).__name__}: {exc}")
    try:
        rows = query_csv(gpu, PROCESS_FIELDS, "compute-apps")
        for row in rows:
            if row["gpu_uuid"] != gpu:
                raise ValueError(f"Unexpected process GPU UUID: {row!r}")
            row["pid"] = int(row["pid"])
        record["processes"] = rows
    except Exception as exc:
        record["errors"].append(f"process_query: {type(exc).__name__}: {exc}")
    return record


def is_idle(record):
    if record["errors"] or record.get("processes"):
        return False
    try:
        return (float(record["gpu"]["utilization.gpu"]) == 0
                and float(record["gpu"]["memory.used"]) < 10)
    except (KeyError, ValueError):
        return False


def process_table():
    """Read PPID and start ticks; start ticks disambiguate reused PIDs."""
    processes = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            # comm may contain spaces or parentheses; fields after its last ')'
            # start with stat field 3 (state).
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            processes[int(entry.name)] = (int(fields[1]), int(fields[19]))
        except (OSError, IndexError, ValueError):
            continue
    return processes


def owned_processes(root_pid, known):
    table = process_table()
    # nvidia-smi can retain a just-exited process for a sample. An absent known
    # PID is still ours; a live PID with different start ticks is a reuse.
    owned = {pid for pid, start in known.items()
             if pid not in table or table[pid][1] == start}
    if root_pid in table and root_pid not in known:
        owned.add(root_pid)
    while True:
        descendants = {pid for pid, (parent, _) in table.items() if parent in owned}
        if descendants <= owned:
            break
        owned.update(descendants)
    for pid in owned:
        if pid in table:
            known[pid] = table[pid][1]
    return owned


def write_manifest(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu", required=True, help="Full physical GPU UUID")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not re.fullmatch(r"GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", args.gpu):
        parser.error("--gpu must be a full GPU UUID, not a device number or prefix")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide the command after --")

    directory = args.output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("manifest.json", "telemetry.jsonl", "stdout.log"):
        if (directory / name).exists():
            parser.error(f"Refusing to overwrite existing artifact: {directory / name}")

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = args.gpu
    manifest_path = directory / "manifest.json"
    manifest = {
        "gpu_uuid": args.gpu, "argv": command, "shell_command": shlex.join(command),
        "cwd": str(Path.cwd()), "env": {key: env[key] for key in ENV_FIELDS if key in env},
        "wrapper_pid": os.getpid(), "created_at": timestamp(), "started_at": None,
        "finished_at": None, "exit_code": None, "status": "waiting_for_lock",
        "valid": False, "contaminated": False, "invalid_reasons": [],
        "telemetry_samples": 0, "monitor_interval_seconds": 1,
        "idle_samples_required": 3, "idle_interval_seconds": 2,
        "lock_scope": "cooperating same-user KDA runners, not GPU exclusivity",
    }
    write_manifest(manifest_path, manifest)
    lock_path = Path("/tmp") / f"kda-{os.getuid()}-{args.gpu}.lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    child = None
    known = {}

    def interrupted(signum, _frame):
        # Do not terminate unrelated GPU processes. The child has its own process
        # group, so interruption propagates only to this experiment.
        manifest["invalid_reasons"].append(f"wrapper_received_signal_{signum}")
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signum)
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        print(f"Waiting for experiment lock: {lock_path}", flush=True)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        manifest["status"] = "waiting_for_idle_gpu"
        write_manifest(manifest_path, manifest)
        with (directory / "telemetry.jsonl").open("x") as telemetry:
            def record_sample(phase):
                record = snapshot(args.gpu)
                record["phase"] = phase
                if phase in ("running", "after"):
                    own = owned_processes(child.pid, known)
                    foreign = [row for row in record.get("processes", [])
                               if row["pid"] not in own]
                    record["owned_pids"] = sorted(own)
                    record["foreign_processes"] = foreign
                    if foreign:
                        manifest["contaminated"] = True
                        reason = "foreign_compute_process_observed"
                        if reason not in manifest["invalid_reasons"]:
                            manifest["invalid_reasons"].append(reason)
                            print("Foreign GPU process observed; measurement is invalid.", flush=True)
                    if record["errors"]:
                        reason = "telemetry_query_failed_during_run"
                        if reason not in manifest["invalid_reasons"]:
                            manifest["invalid_reasons"].append(reason)
                telemetry.write(json.dumps(record) + "\n")
                telemetry.flush()
                manifest["telemetry_samples"] += 1
                return record

            consecutive = 0
            while consecutive < 3:
                sample = record_sample("before")
                consecutive = consecutive + 1 if is_idle(sample) else 0
                print(f"GPU idle samples: {consecutive}/3; "
                      f"processes={len(sample.get('processes', []))}; "
                      f"errors={sample['errors']}", flush=True)
                if consecutive < 3:
                    time.sleep(2)

            manifest["selected_device"] = sample["gpu"]
            with (directory / "stdout.log").open("xb") as output:
                manifest["started_at"] = timestamp()
                child = subprocess.Popen(command, env=env, stdout=output,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                # Record its identity before poll()/wait() can reap a fast child.
                known[child.pid] = process_table()[child.pid][1]
                manifest["command_pid"] = child.pid
                manifest["status"] = "running"
                write_manifest(manifest_path, manifest)
                print(f"Running PID {child.pid}; output: {directory / 'stdout.log'}", flush=True)
                while child.poll() is None:
                    deadline = time.monotonic() + 1
                    record_sample("running")
                    write_manifest(manifest_path, manifest)
                    try:
                        child.wait(timeout=max(0.01, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        pass
                manifest["exit_code"] = child.returncode
            record_sample("after")
            if child.returncode:
                manifest["invalid_reasons"].append("command_failed")
            manifest["valid"] = not manifest["invalid_reasons"]
            manifest["status"] = "finished"
    except KeyboardInterrupt:
        manifest["status"] = "interrupted"
        manifest["valid"] = False
        if not manifest["invalid_reasons"]:
            manifest["invalid_reasons"].append("wrapper_interrupted")
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["valid"] = False
        manifest["invalid_reasons"].append(f"{type(exc).__name__}: {exc}")
        print(f"Experiment wrapper failed: {exc}", file=sys.stderr, flush=True)
    finally:
        # Keep the lock until our own command is terminal, including wrapper
        # failures and interrupts. Never leave an unmonitored GPU job behind.
        if child is not None and child.poll() is None:
            manifest["valid"] = False
            manifest["invalid_reasons"].append("command_stopped_after_wrapper_failure")
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            except ProcessLookupError:
                child.wait()
        manifest["finished_at"] = timestamp()
        if child is not None:
            manifest["exit_code"] = child.poll()
        write_manifest(manifest_path, manifest)
        os.close(lock_fd)
    print(json.dumps({key: manifest[key] for key in
                      ("status", "exit_code", "valid", "contaminated", "invalid_reasons")}), flush=True)
    return 0 if manifest["valid"] else (manifest["exit_code"] or 2)


if __name__ == "__main__":
    sys.exit(main())
