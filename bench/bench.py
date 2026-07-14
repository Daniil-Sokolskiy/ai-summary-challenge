#!/usr/bin/env python3
"""Измерительный стенд.

Ничего не чинит и ничего не подсказывает — только показывает, чего стоит
одно открытие карточки: сколько времени, сколько запросов в БД, сколько
платных вызовов к LLM.

Запуск:  make bench          (или python3 bench/bench.py)
         make bench INN=5027089703
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "http://localhost:8000"
LLM = "http://localhost:8090"

TIMEOUT = 180  # столько ждать ответа мы не готовы, но хотим увидеть честное число


def _get(url: str) -> tuple[int, float, dict | None]:
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            body = json.loads(response.read().decode())
            return response.status, time.monotonic() - started, body
    except urllib.error.HTTPError as error:
        return error.code, time.monotonic() - started, None
    except Exception:
        return 0, time.monotonic() - started, None


def _post(url: str, payload: dict | None = None) -> None:
    data = json.dumps(payload or {}).encode()
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        urllib.request.urlopen(request, timeout=10).read()
    except Exception as error:
        print(f"  ! не достучались до {url}: {error}")


def _stats(url: str) -> dict:
    _, _, body = _get(url)
    return body or {}


def _reset() -> None:
    _post(f"{LLM}/admin/reset")
    _post(f"{API}/debug/reset")


def _purge(inn: str) -> None:
    """Забыть уже сгенерированное описание, иначе «холодное» открытие холодным не будет."""
    _post(f"{API}/debug/purge/{inn}")


def _fmt(seconds: float) -> str:
    return f"{seconds:6.2f}s"


def cold_open(inn: str, concurrency: int) -> None:
    """Что видит N человек (или N краулеров), одновременно открывших одну карточку."""
    print(f"\n=== ХОЛОДНОЕ ОТКРЫТИЕ: {concurrency} одновременных запросов, ИНН {inn} ===")
    _purge(inn)
    _reset()

    url = f"{API}/v1/company/{inn}/ai-description"
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda _: _get(url), range(concurrency)))

    latencies = [latency for _, latency, _ in results]
    codes = [status if status else "таймаут" for status, _, _ in results]

    print(f"  статусы:        {sorted(codes, key=str)}")
    print(f"  быстрейший:     {_fmt(min(latencies))}")
    print(f"  медиана:        {_fmt(statistics.median(latencies))}")
    print(f"  самый медленный:{_fmt(max(latencies))}")

    llm = _stats(f"{LLM}/admin/stats")
    api = _stats(f"{API}/debug/stats")
    generations = llm.get("generations_by_inn", {}).get(inn, 0)

    print(f"\n  вызовов к LLM:       {llm.get('calls_total', 0)}"
          f"  (ok {llm.get('calls_ok', 0)}, 429 {llm.get('calls_429', 0)})")
    print(f"  из них генераций:    {generations}  — уникальных карточек здесь ОДНА")
    print(f"  секунд в LLM:        {llm.get('llm_seconds_spent', 0)}")
    print(f"  запросов в БД:       {api.get('sql_queries_total', 0)}")


def warm_open(inn: str, repeats: int) -> None:
    """Что стоит повторное открытие уже сгенерированной карточки."""
    print(f"\n=== ПОВТОРНОЕ ОТКРЫТИЕ: {repeats} последовательных запросов, ИНН {inn} ===")

    url = f"{API}/v1/company/{inn}/ai-description"
    _get(url)  # прогреваем, чтобы мерить именно повторное открытие
    _reset()

    latencies = []
    for _ in range(repeats):
        status, latency, _ = _get(url)
        latencies.append(latency)
        if status != 200:
            print(f"  ! статус {status}")

    llm = _stats(f"{LLM}/admin/stats")
    api = _stats(f"{API}/debug/stats")

    print(f"  медиана:             {_fmt(statistics.median(latencies))}")
    print(f"  самый медленный:     {_fmt(max(latencies))}")
    print(f"  вызовов к LLM:       {llm.get('calls_total', 0)}  — карточка уже сгенерирована")
    print(f"  запросов в БД:       {api.get('sql_queries_total', 0)}"
          f"  ({api.get('sql_queries_total', 0) / max(repeats, 1):.0f} на запрос)")


def degraded(inn: str) -> None:
    """Провайдер LLM лежит. Что делает приложение."""
    print(f"\n=== ПРОВАЙДЕР LLM НЕДОСТУПЕН, ИНН {inn} ===")
    _purge(inn)
    _reset()
    _post(f"{LLM}/admin/config", {"fail_mode": True})

    url = f"{API}/v1/company/{inn}/ai-description"
    for attempt in (1, 2):
        status, latency, _ = _get(url)
        print(f"  запрос {attempt}: статус {status}, {_fmt(latency)}")

    llm = _stats(f"{LLM}/admin/stats")
    print(f"  вызовов к LLM за 2 запроса: {llm.get('calls_total', 0)}")

    _post(f"{LLM}/admin/config", {"fail_mode": False})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inn", default="7707410283")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--skip-degraded", action="store_true")
    args = parser.parse_args()

    status, _, _ = _get(f"{LLM}/admin/stats")
    if status != 200:
        print("llm-mock не отвечает на localhost:8090 — поднят ли стенд? (make up)")
        return 1

    cold_open(args.inn, args.concurrency)
    warm_open(args.inn, args.repeats)
    if not args.skip_degraded:
        degraded(args.inn)

    print("\nОриентиры «сделано» — см. TASK.md.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
