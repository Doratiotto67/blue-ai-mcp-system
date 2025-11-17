import asyncio
import json
import time
import argparse
import statistics
import httpx
from typing import Dict, Any

services = {
    "orchestrator": "http://localhost:9080",
    "architect": "http://localhost:9081",
    "designer": "http://localhost:9082",
    "coder": "http://localhost:9083",
    "auditor": "http://localhost:9084",
    "stack": "http://localhost:9085"
}

async def health_check(client: httpx.AsyncClient, base: str) -> bool:
    try:
        r = await client.get(f"{base}/health", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

async def smoke_suite(host: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        health = {}
        for name, base in services.items():
            health[name] = await health_check(client, base)
        calls = []
        t0 = time.perf_counter()
        r = await client.get(f"{host}/mcp/tools/quick_code?description=hello&language=python&style=minimal&stub=1")
        dt = (time.perf_counter() - t0) * 1000
        calls.append({"status": r.status_code == 200, "ms": dt})
        return {"health": health, "calls": calls}

async def load_suite(host: str, concurrency: int, iterations: int) -> Dict[str, Any]:
    lat = []
    err = 0
    async def one(i: int):
        nonlocal err
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                t0 = time.perf_counter()
                r = await client.get(f"{host}/mcp/tools/quick_code?description=case{i}&language=python&style=modern&stub=1")
                dt = (time.perf_counter() - t0) * 1000
                if r.status_code == 200:
                    lat.append(dt)
                else:
                    err += 1
        except Exception:
            err += 1
    tasks = []
    for i in range(iterations):
        tasks.append(one(i))
        if len(tasks) % concurrency == 0:
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)
    total = iterations
    succ = total - err
    rate = succ / total if total else 0
    p50 = statistics.median(lat) if lat else 0
    p95 = statistics.quantiles(lat, n=100)[94] if len(lat) >= 100 else max(lat) if lat else 0
    p99 = statistics.quantiles(lat, n=100)[98] if len(lat) >= 100 else max(lat) if lat else 0
    return {"total": total, "success": succ, "error": err, "success_rate": rate, "p50_ms": p50, "p95_ms": p95, "p99_ms": p99}

def save_report(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def main_async(host: str, report_path: str, concurrency: int, iterations: int) -> int:
    smoke = await smoke_suite(host)
    load = await load_suite(host, concurrency, iterations)
    report = {"smoke": smoke, "load": load}
    save_report(report_path, report)
    ok_health = all(smoke["health"].values())
    ok_calls = all(c["status"] for c in smoke["calls"]) if smoke["calls"] else False
    ok_load = load["success_rate"] >= 0.98
    return 0 if ok_health and ok_calls else (0 if ok_load else 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://localhost:9080")
    parser.add_argument("--report", default="logs/test-runner-report.json")
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--iterations", type=int, default=200)
    args = parser.parse_args()
    rc = asyncio.run(main_async(args.host, args.report, args.concurrency, args.iterations))
    raise SystemExit(rc)

if __name__ == "__main__":
    main()