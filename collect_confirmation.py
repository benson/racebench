"""Operational concurrency override; frozen prompts, scoring, and budget stay intact."""
import argparse
import json
from datetime import datetime, timezone

import confirmation


def collect(name, budget=35, workers=64):
    if not 1 <= workers <= 64:
        raise ValueError("Workers must be between 1 and 64")
    confirmation.verify(name)
    original = confirmation.sb.main

    def with_workers(argv):
        argv = list(argv)
        if argv[0] in ("run", "judge"):
            argv[argv.index("--workers") + 1] = str(workers)
        return original(argv)

    directory = confirmation.ROOT / "runs" / name
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "collection-operations.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"requested_utc": datetime.now(timezone.utc).isoformat(),
                            "workers": workers, "budget": budget,
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
    args = parser.parse_args()
    raise SystemExit(collect(args.name, args.budget, args.workers))
