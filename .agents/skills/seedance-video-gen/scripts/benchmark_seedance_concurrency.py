#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28.0",
# ]
# ///

"""Seedance 2.0 concurrent running capacity benchmark.

Adaptive stepped ramp: submit batches of N tasks, observe running count, double N
on each step until saturation is reached or the cap is hit. Also measures whether
submit itself is rate-limited (429s).

Unlike the production generate_seedance_video.py, this script intentionally does
NOT retry submits. We want to OBSERVE 429s as a measurement of submit throttling,
not mask them. The list endpoint (used for observation) does silently retry to
keep the measurement window clean.

Output: a timestamped directory under --output-dir (default: SEEDANCE_OUTPUT_DIR env var or output/benchmarks)
  - summary.json          headlined numbers: ceiling, submit success rate, etc.
  - timeseries.csv        per-poll samples: t, running, queued, succeeded counts
  - submit_log.jsonl      per-submit POST: status_code, latency_ms, task_id, error
  - manifest.json         test parameters, model, account key prefix, base URL
  - ramp_summary.txt      human-readable per-batch table

Usage:
  uv run scripts/benchmark_seedance_concurrency.py
  uv run scripts/benchmark_seedance_concurrency.py --first-batch 20 --max-batch 100
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_PROMPT = "一只橘猫在阳光下缓慢眨眼"
DEFAULT_OUTPUT_ROOT = os.environ.get("SEEDANCE_OUTPUT_DIR", "output") + "/benchmarks"
# Default to FAST model: standard 5s 720p actually takes 5-10 min per task on the
# server, which makes a stepped ramp impractical. Fast 4s 480p completes in
# ~30-60s, which gives clean signal within 60s observation windows.
DEFAULT_MODEL = "doubao-seedance-2-0-fast-260128"
DEFAULT_RESOLUTION = "480p"
DEFAULT_DURATION = 4

# Saturation: peak_running_in_window < batch_size * SATURATION_RATIO AND
# final_queued > 0  =>  we have a queue, the server is at capacity.
DEFAULT_SATURATION_RATIO = 0.5
# List endpoint silent retry config (3 attempts, exp backoff)
LIST_MAX_ATTEMPTS = 3
LIST_BACKOFF_S = 1.5


def _load_dotenv() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and k not in os.environ:
            os.environ[k] = v


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def now_epoch() -> float:
    return time.time()


def get_auth() -> tuple[str, str]:
    api_key = os.environ.get("ARK_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "Error: ARK_API_KEY not found. Set it in your shell or .env file."
        )
    base_url = os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    return api_key, base_url


def build_payload(
    model: str, prompt: str, duration: int, ratio: str, resolution: str, audio: bool
) -> dict[str, Any]:
    return {
        "model": model,
        "content": [{"type": "text", "text": prompt}],
        "duration": duration,
        "ratio": ratio,
        "resolution": resolution,
        "generate_audio": audio,
    }


async def submit_one(
    client: httpx.AsyncClient,
    api_key: str,
    base_url: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Submit a single task. NO retry - we want to see 429s as data points."""
    t0 = time.monotonic()
    try:
        r = await client.post(
            f"{base_url}/contents/generations/tasks",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=60,
        )
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        ct = r.headers.get("content-type", "")
        body = r.json() if ct.startswith("application/json") else {"raw": r.text[:300]}
        return {
            "status_code": r.status_code,
            "latency_ms": latency_ms,
            "task_id": body.get("id") if isinstance(body, dict) else None,
            "error": body.get("error") if isinstance(body, dict) and r.status_code >= 400 else None,
            "retry_after_header": r.headers.get("Retry-After"),
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return {
            "status_code": -1,
            "latency_ms": latency_ms,
            "task_id": None,
            "error": {"code": "EXCEPTION", "message": f"{type(e).__name__}: {e}"},
            "retry_after_header": None,
        }


async def list_count(
    client: httpx.AsyncClient, api_key: str, base_url: str, status: str
) -> int:
    """List tasks in given status, return total count. Silent retry on 429/5xx."""
    url = f"{base_url}/contents/generations/tasks"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    last_err: str = ""
    for attempt in range(LIST_MAX_ATTEMPTS):
        try:
            r = await client.get(
                url,
                params={"filter.status": status, "page_size": 500},
                headers=headers,
                timeout=30,
            )
            if r.status_code == 200:
                return r.json().get("total", 0)
            if r.status_code in {429, 500, 502, 503, 504}:
                last_err = f"HTTP {r.status_code}"
                await asyncio.sleep(LIST_BACKOFF_S * (2 ** attempt))
                continue
            return -1  # permanent error
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            await asyncio.sleep(LIST_BACKOFF_S * (2 ** attempt))
    print(f"  WARN list {status} failed after {LIST_MAX_ATTEMPTS} attempts: {last_err}", file=sys.stderr)
    return -1


async def submit_batch(
    client: httpx.AsyncClient, api_key: str, base_url: str, payload: dict[str, Any], n: int
) -> list[dict[str, Any]]:
    tasks = [submit_one(client, api_key, base_url, payload) for _ in range(n)]
    return await asyncio.gather(*tasks)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p.add_argument("--prompt", default=DEFAULT_PROMPT, help="Prompt text (kept identical across batches for clean signal)")
    p.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    p.add_argument("--ratio", default="16:9")
    p.add_argument("--resolution", default=DEFAULT_RESOLUTION)
    p.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--first-batch", type=int, default=10, help="First batch size (default 10)")
    p.add_argument("--max-batch", type=int, default=200, help="Cap on any single batch (default 200)")
    p.add_argument("--step-multiplier", type=float, default=2.0, help="Multiply batch size by this each step (default 2.0)")
    p.add_argument("--observe-seconds", type=int, default=90, help="Observation window per batch (default 90s)")
    p.add_argument("--poll-interval", type=int, default=5, help="Poll interval in seconds (default 5s)")
    p.add_argument("--cooldown-timeout", type=int, default=30 * 60, help="Max wait for tasks to finish after ramp (default 30min)")
    p.add_argument("--saturation-ratio", type=float, default=DEFAULT_SATURATION_RATIO, help="peak/batch ratio below which we call it saturated (default 0.5)")
    p.add_argument("--include-cooldown-peak", action=argparse.BooleanOptionalAction, default=True, help="Track running peak during cooldown and include in summary (default True)")
    p.add_argument("--baseline-threshold", type=int, default=2, help="Wait until running count drops below this before starting (default 2)")
    p.add_argument("--baseline-wait-timeout", type=int, default=15 * 60, help="Max seconds to wait for baseline to clear (default 15min)")
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT_ROOT, help="Output root (default: SEEDANCE_OUTPUT_DIR env var or output/benchmarks)")
    p.add_argument("--dry-run", action="store_true", help="Just print the plan, don't hit the API")
    return p.parse_args()


def print_plan(args: argparse.Namespace) -> None:
    print("=== Plan ===")
    print(f"  Model: {args.model}")
    print(f"  Prompt: {args.prompt!r}")
    print(f"  Per-task params: {args.duration}s, {args.ratio}, {args.resolution}, audio={args.generate_audio}")
    print(f"  First batch: {args.first_batch}, step x{args.step_multiplier}, max {args.max_batch}")
    print(f"  Observe window: {args.observe_seconds}s per batch (poll every {args.poll_interval}s)")
    print(f"  Saturation ratio: {args.saturation_ratio}")
    est_batches = 1
    s = args.first_batch
    while s < args.max_batch and s * args.step_multiplier < args.max_batch * 1.1:
        s = int(s * args.step_multiplier)
        if s > args.max_batch:
            break
        est_batches += 1
    est_total = sum(min(int(args.first_batch * (args.step_multiplier ** i)), args.max_batch) for i in range(est_batches))
    print(f"  Estimated: ~{est_batches} batches, ~{est_total} tasks, ~{est_batches * (15 + args.observe_seconds) // 60}min wall time (if no early saturation)")


async def run_benchmark(args: argparse.Namespace) -> int:
    _load_dotenv()
    api_key, base_url = get_auth()

    print_plan(args)
    if args.dry_run:
        return 0

    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")
    out_dir = Path(args.output_dir).expanduser().resolve() / f"seedance-concurrency-{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput dir: {out_dir}\n")

    payload = build_payload(
        args.model, args.prompt, args.duration, args.ratio, args.resolution, args.generate_audio,
    )

    manifest = {
        "started_at": now_iso(),
        "params": {
            "model": args.model,
            "prompt": args.prompt,
            "duration": args.duration,
            "ratio": args.ratio,
            "resolution": args.resolution,
            "generate_audio": args.generate_audio,
        },
        "config": {
            "first_batch": args.first_batch,
            "max_batch": args.max_batch,
            "step_multiplier": args.step_multiplier,
            "observe_seconds": args.observe_seconds,
            "poll_interval": args.poll_interval,
            "saturation_ratio": args.saturation_ratio,
        },
        "api_key_prefix": api_key[:8],
        "base_url": base_url,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    submit_log_f = open(out_dir / "submit_log.jsonl", "w", encoding="utf-8")
    timeseries_f = open(out_dir / "timeseries.csv", "w", encoding="utf-8")
    timeseries_f.write("t_epoch,t_iso,batch_id,phase,elapsed_in_phase_s,total_submitted,running,queued,succeeded,note\n")
    timeseries_f.flush()

    all_submit_results: list[dict[str, Any]] = []
    all_task_ids: list[str] = []
    batch_records: list[dict[str, Any]] = []
    t_start = now_epoch()

    async with httpx.AsyncClient() as client:
        # Baseline: get current running count
        baseline_running = await list_count(client, api_key, base_url, "running")
        baseline_queued = await list_count(client, api_key, base_url, "queued")
        print(f"Baseline (before any submits): running={baseline_running}, queued={baseline_queued}")

        # If baseline has tasks, wait for them to clear so the measurement isn't
        # contaminated. This is important because previous benchmark/test tasks
        # can occupy running slots and make our submits appear "queued forever".
        if baseline_running > args.baseline_threshold or baseline_queued > args.baseline_threshold:
            t_wait_start = now_epoch()
            print(f"\n=== Waiting for baseline to clear (threshold={args.baseline_threshold}, max {args.baseline_wait_timeout}s) ===")
            while now_epoch() - t_wait_start < args.baseline_wait_timeout:
                br = await list_count(client, api_key, base_url, "running")
                bq = await list_count(client, api_key, base_url, "queued")
                t_now = now_epoch()
                elapsed = t_now - t_wait_start
                timeseries_f.write(
                    f"{t_now:.1f},{now_iso()},0,baseline_wait,{elapsed:.1f},0,{br},{bq},0,\n"
                )
                timeseries_f.flush()
                print(f"  baseline wait t+{elapsed:5.0f}s  running={br:>3}  queued={bq:>3}")
                if br <= args.baseline_threshold and bq <= args.baseline_threshold:
                    print(f"  → baseline cleared after {elapsed:.0f}s. Proceeding.")
                    baseline_running = br
                    baseline_queued = bq
                    break
                await asyncio.sleep(args.poll_interval)
            else:
                print(f"  → baseline wait timeout {args.baseline_wait_timeout}s reached. Proceeding anyway with baseline_running={baseline_running}.")
                baseline_running = baseline_running
                baseline_queued = baseline_queued

        batch_size = args.first_batch
        batch_id = 0
        stop_reason = "no_batches"

        # --- Ramp phase ---
        while True:
            batch_id += 1
            print(f"\n=== Batch {batch_id}: submitting {batch_size} tasks ===")
            t_batch_start = now_epoch()

            submit_results = await submit_batch(client, api_key, base_url, payload, batch_size)
            for sr in submit_results:
                sr["batch_id"] = batch_id
                sr["t_iso"] = now_iso()
                sr["t_epoch"] = now_epoch()
                submit_log_f.write(json.dumps(sr, ensure_ascii=False) + "\n")
            submit_log_f.flush()
            all_submit_results.extend(submit_results)

            n_2xx = sum(1 for sr in submit_results if 200 <= sr["status_code"] < 300)
            n_429 = sum(1 for sr in submit_results if sr["status_code"] == 429)
            n_other = sum(1 for sr in submit_results if sr["status_code"] >= 400 and sr["status_code"] != 429) + sum(1 for sr in submit_results if sr["status_code"] < 0)
            submit_elapsed = now_epoch() - t_batch_start
            new_task_ids = [sr["task_id"] for sr in submit_results if sr["task_id"]]
            all_task_ids.extend(new_task_ids)

            print(f"  submit: 2xx={n_2xx} 429={n_429} other_err={n_other} (in {submit_elapsed:.1f}s)")
            if n_429:
                sample = next((sr for sr in submit_results if sr["status_code"] == 429), None)
                print(f"  429 sample: {sample}")

            # Observation window
            print(f"  observing for {args.observe_seconds}s (poll every {args.poll_interval}s)...")
            window_samples: list[dict[str, Any]] = []
            t_obs_start = now_epoch()
            while now_epoch() - t_obs_start < args.observe_seconds:
                running = await list_count(client, api_key, base_url, "running")
                queued = await list_count(client, api_key, base_url, "queued")
                succeeded = await list_count(client, api_key, base_url, "succeeded")
                t_now = now_epoch()
                elapsed = t_now - t_batch_start
                note = ""
                timeseries_f.write(
                    f"{t_now:.1f},{now_iso()},{batch_id},observe,{elapsed:.1f},{len(all_task_ids)},{running},{queued},{succeeded},{note}\n"
                )
                timeseries_f.flush()
                window_samples.append({"t": t_now, "elapsed": elapsed, "running": running, "queued": queued, "succeeded": succeeded})
                print(f"    t+{elapsed:5.0f}s  running={running:>3}  queued={queued:>3}  succeeded={succeeded:>4}")
                await asyncio.sleep(args.poll_interval)

            # Compute batch-level metrics. Subtract baseline so "running" reflects
            # only this benchmark's contribution, not other account activity.
            peak_running = max((s["running"] for s in window_samples), default=0)
            peak_running_minus_baseline = max(0, peak_running - max(0, baseline_running))
            last_queued = window_samples[-1]["queued"] if window_samples else 0
            last_succeeded = window_samples[-1]["succeeded"] if window_samples else 0
            saturated = peak_running_minus_baseline < batch_size * args.saturation_ratio and last_queued > baseline_queued

            batch_records.append({
                "batch_id": batch_id,
                "batch_size": batch_size,
                "submit_2xx": n_2xx,
                "submit_429": n_429,
                "submit_other_err": n_other,
                "submit_elapsed_s": round(submit_elapsed, 2),
                "peak_running_global": peak_running,
                "peak_running_minus_baseline": peak_running_minus_baseline,
                "final_queued": last_queued,
                "final_succeeded": last_succeeded,
                "window_samples": len(window_samples),
                "saturated": saturated,
            })

            print(f"  Batch {batch_id} summary: peak_running={peak_running} (ours={peak_running_minus_baseline}), final_queued={last_queued}, saturated={saturated}")

            if saturated:
                stop_reason = f"saturated at batch {batch_id} (peak_running_ours={peak_running_minus_baseline} < {batch_size}*{args.saturation_ratio}={int(batch_size*args.saturation_ratio)} AND queued={last_queued}>baseline_queued={baseline_queued})"
                print(f"  → {stop_reason}")
                break
            if batch_size >= args.max_batch:
                stop_reason = f"max_batch_reached ({args.max_batch})"
                print(f"  → {stop_reason}")
                break

            batch_size = min(int(batch_size * args.step_multiplier), args.max_batch)

        # --- Cooldown: wait for all submitted tasks to finish ---
        print(f"\n=== Cooldown: waiting for all tasks to finish (timeout {args.cooldown_timeout}s) ===")
        cooldown_peak_running = 0
        cooldown_start = now_epoch()
        last_running = -1
        last_queued = -1
        while now_epoch() - cooldown_start < args.cooldown_timeout:
            running = await list_count(client, api_key, base_url, "running")
            queued = await list_count(client, api_key, base_url, "queued")
            t_now = now_epoch()
            timeseries_f.write(
                f"{t_now:.1f},{now_iso()},{batch_id},cooldown,{t_now-cooldown_start:.1f},{len(all_task_ids)},{running},{queued},0,\n"
            )
            timeseries_f.flush()
            print(f"  cooldown t+{t_now-cooldown_start:5.0f}s  running={running:>3}  queued={queued:>3}")
            last_running = running
            last_queued = queued
            if running <= 0 and queued <= 0:
                print("  → all tasks finished.")
                stop_reason = stop_reason + " + cooldown_clean"
                break
            await asyncio.sleep(args.poll_interval * 2)
        else:
            print(f"  → cooldown timeout {args.cooldown_timeout}s reached with running={last_running}, queued={last_queued}")

    submit_log_f.close()
    timeseries_f.close()
    t_end = now_epoch()

    # --- Summary ---
    total_submits = len(all_submit_results)
    n_2xx_total = sum(1 for sr in all_submit_results if 200 <= sr["status_code"] < 300)
    n_429_total = sum(1 for sr in all_submit_results if sr["status_code"] == 429)
    n_other_total = sum(1 for sr in all_submit_results if sr["status_code"] >= 400 and sr["status_code"] != 429) + sum(1 for sr in all_submit_results if sr["status_code"] < 0)

    saturated_batches = [b for b in batch_records if b["saturated"]]
    ceiling_global = max((b["peak_running_global"] for b in batch_records), default=0)
    ceiling_ours = max((b["peak_running_minus_baseline"] for b in batch_records), default=0)
    effective_ceiling_global = max(ceiling_global, cooldown_peak_running) if args.include_cooldown_peak else ceiling_global
    if saturated_batches:
        ceiling_batch = saturated_batches[0]
        ceiling_at_batch = ceiling_batch["batch_id"]
    else:
        ceiling_at_batch = batch_records[-1]["batch_id"] if batch_records else 0

    summary = {
        "started_at": manifest["started_at"],
        "finished_at": now_iso(),
        "wall_time_s": round(t_end - t_start, 1),
        "baseline_running": baseline_running,
        "baseline_queued": baseline_queued,
        "params": manifest["params"],
        "config": manifest["config"],
        "ramp": {
            "batches": batch_records,
            "stop_reason": stop_reason,
        },
        "totals": {
            "tasks_submitted": total_submits,
            "submit_2xx": n_2xx_total,
            "submit_429": n_429_total,
            "submit_other_err": n_other_total,
            "submit_success_rate": round(n_2xx_total / total_submits, 4) if total_submits else 0.0,
        },
        "ceiling": {
            "peak_running_global_ramp_only": ceiling_global,
            "peak_running_global_cooldown": cooldown_peak_running,
            "peak_running_global_effective": effective_ceiling_global,
            "peak_running_ours_only": ceiling_ours,
            "detected_at_batch": ceiling_at_batch,
            "saturation_reached": bool(saturated_batches),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Human-readable ramp summary
    ramp_txt = ["Ramp summary", "=" * 60]
    ramp_txt.append(f"{'Batch':<7}{'Size':<6}{'2xx':<5}{'429':<5}{'Other':<6}{'peak_R':<8}{'peak_R_ours':<13}{'final_Q':<9}{'sat'}")
    for b in batch_records:
        ramp_txt.append(
            f"{b['batch_id']:<7}{b['batch_size']:<6}{b['submit_2xx']:<5}{b['submit_429']:<5}{b['submit_other_err']:<6}"
            f"{b['peak_running_global']:<8}{b['peak_running_minus_baseline']:<13}{b['final_queued']:<9}{'Y' if b['saturated'] else ''}"
        )
    ramp_txt.append("")
    ramp_txt.append(f"Stop reason: {stop_reason}")
    ramp_txt.append(f"Peak running (global): {ceiling_global}")
    ramp_txt.append(f"Peak running (ours only, baseline subtracted): {ceiling_ours}")
    ramp_txt.append(f"Total submits: {total_submits}  (2xx: {n_2xx_total}, 429: {n_429_total}, other_err: {n_other_total})")
    (out_dir / "ramp_summary.txt").write_text("\n".join(ramp_txt) + "\n", encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"FINAL")
    print(f"  Total submits:    {total_submits} (2xx: {n_2xx_total}, 429: {n_429_total}, other_err: {n_other_total})")
    print(f"  Peak running (ramp):     {ceiling_global}")
    print(f"  Peak running (cooldown): {cooldown_peak_running}")
    print(f"  Effective ceiling:       {effective_ceiling_global} (max of ramp + cooldown)")
    print(f"  Saturation seen (ramp):  {bool(saturated_batches)}")
    print(f"  Stop reason:             {stop_reason}")
    print(f"  Output:           {out_dir}")
    print(f"{'='*60}\n")
    print("\n".join(ramp_txt))
    return 0


def main() -> int:
    args = parse_args()
    return asyncio.run(run_benchmark(args))


if __name__ == "__main__":
    raise SystemExit(main())
