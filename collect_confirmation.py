"""Operational concurrency override; frozen prompts, scoring, and budget stay intact."""
import argparse
import json
import os
import threading
import urllib.request
from datetime import datetime, timezone

import confirmation


def key_state():
    request = urllib.request.Request("https://openrouter.ai/api/v1/key",
                                     headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)["data"]
    return {k: data.get(k) for k in ("usage", "limit", "limit_remaining")}


def collect(name, budget=35, workers=64, judge_only=False):
    if not 1 <= workers <= 64:
        raise ValueError("Workers must be between 1 and 64")
    confirmation.verify(name)
    account = key_state()
    if account["limit_remaining"] is not None and account["limit_remaining"] <= 0:
        raise ValueError("OpenRouter key limit exhausted; collection remains stopped")
    original = confirmation.sb.main
    blocked, installed = threading.Event(), False

    def with_workers(argv):
        nonlocal installed
        argv = list(argv)
        if judge_only and argv[0] == "run":
            return 0
        if argv[0] in ("run", "judge"):
            argv[argv.index("--workers") + 1] = str(workers)
        if not installed:
            # Install outside the frozen budget wrapper: skipped queued work
            # neither sends a request nor consumes a new reservation.
            guarded_chat = confirmation.sb.chat
            def stop_on_account_error(payload, timeout):
                if blocked.is_set():
                    return {"error": "Collection stopped after account rejection; no request sent", "not_sent": True}
                result = guarded_chat(payload, timeout)
                error = str(result.get("error", ""))
                if error.startswith(("HTTP 401:", "HTTP 402:", "HTTP 403:", "API 401:", "API 402:", "API 403:")) or result.get("budget_stopped"):
                    blocked.set()
                return result
            confirmation.sb.chat = stop_on_account_error
            installed = True
        return original(argv)

    directory = confirmation.ROOT / "runs" / name
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "collection-operations.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"requested_utc": datetime.now(timezone.utc).isoformat(),
                            "workers": workers, "budget": budget,
                            "phase": "judge" if judge_only else "collect-and-judge",
                            "account_before": account,
                            "amendment": "studies/confirmation1/operational-amendment-1.md"}) + "\n")
    confirmation.sb.main = with_workers
    try:
        return confirmation.execute(name, budget)
    finally:
        confirmation.sb.main = original


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="confirmation1")
    parser.add_argument("--budget", type=float, default=35)
    parser.add_argument("--workers", type=int, default=64)
    parser.add_argument("--judge-only", action="store_true",
                        help="Score saved answers after bounded collection retries; retain missing slots")
    args = parser.parse_args()
    raise SystemExit(collect(args.name, args.budget, args.workers, args.judge_only))
