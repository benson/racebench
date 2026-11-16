"""Offline exploratory checks for the featured examples; no model/API calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from build_page import ROOT, load_run
from racebench import average_judges, validated_scoring_records


def permutation_spread(blocks, draws=200_000, seed=20261116):
    """Each block is one fixed model; each cell contains response-level scores."""
    if draws < 1 or not blocks or len(blocks[0]) < 2:
        raise ValueError("Need positive draws, models, and at least two groups")
    groups = len(blocks[0])
    if any(len(block) != groups or any(not cell for cell in block) for block in blocks):
        raise ValueError("All models need usable scores for every group")
    if any(not math.isfinite(v) for block in blocks for cell in block for v in cell):
        raise ValueError("Scores must be finite")
    means = [statistics.fmean(statistics.fmean(block[g]) for block in blocks)
             for g in range(groups)]
    observed = max(means) - min(means)
    counts = [[len(cell) for cell in block] for block in blocks]
    pools = [[value for cell in block for value in cell] for block in blocks]
    rng = random.Random(seed)
    exceedances = 0
    if observed == 0:
        exceedances = draws
    else:
        tolerance = max(1.0, abs(observed)) * 1e-12
        for _ in range(draws):
            totals = [0.0] * groups
            for pool, sizes in zip(pools, counts):
                rng.shuffle(pool)
                start = 0
                for g, size in enumerate(sizes):
                    totals[g] += sum(pool[start:start + size]) / size
                    start += size
            spread = (max(totals) - min(totals)) / len(blocks)
            exceedances += spread >= observed - tolerance
    return {"means": means, "spread": observed, "counts": counts,
            "draws": draws, "seed": seed, "exceedances": exceedances,
            "p": (exceedances + 1) / (draws + 1)}


def analyze_examples(data, records, draws=200_000, seed=20261116):
    groups = [g["id"] for g in data["groups"]]
    lookup = {(r["model"], r["template"], r["group"], r["sample"]): r
              for r in records if not r.get("error")}
    results = {}
    for tid in data["examples"]:
        t = next(t for t in data["templates"] if t["id"] == tid)
        field = "value" if t["measure"] == "number" else t["measure"]
        matched, blocks = [], []
        for model in data["models"]:
            block = [[lookup.get((model, tid, g, sample), {}).get(field)
                      for sample in range(data["samples"])] for g in groups]
            block = [[v for v in cell if v is not None] for cell in block]
            for g, cell in zip(groups, block):
                saved = data["cells"][model][tid][g]
                mean = statistics.fmean(cell) if cell else None
                if len(cell) != saved["valid"] or (mean is None) != (saved["raw"] is None):
                    raise ValueError(f"Score coverage differs from chart: {model}/{tid}/{g}")
                if mean is not None and not math.isclose(mean, saved["raw"], abs_tol=1e-9):
                    raise ValueError(f"Score mean differs from chart: {model}/{tid}/{g}")
            if all(block):
                matched.append(model)
                blocks.append(block)
        if not blocks:
            results[tid] = {"status": "unavailable", "models": []}
            continue
        item_seed = seed + int.from_bytes(hashlib.sha256(tid.encode()).digest()[:4], "big")
        out = permutation_spread(blocks, draws, item_seed)
        lo, hi = min(range(len(groups)), key=out["means"].__getitem__), max(range(len(groups)), key=out["means"].__getitem__)
        differences = [statistics.fmean(b[hi]) - statistics.fmean(b[lo]) for b in blocks]
        adjusted = min(1.0, len(data["templates"]) * out["p"])
        results[tid] = {**out, "status": "available", "models": matched,
                        "groups": groups, "adjusted_p": adjusted,
                        "significant": adjusted < 0.05,
                        "lowest": groups[lo], "highest": groups[hi],
                        "same_direction": sum(d > 1e-9 for d in differences),
                        "tied": sum(abs(d) <= 1e-9 for d in differences),
                        "opposite_direction": sum(d < -1e-9 for d in differences)}
    return {"version": 1, "run": data["run"], "family_size": len(data["templates"]),
            "alpha": 0.05, "correction": "Bonferroni over all inspected prompts",
            "statistic": "Largest minus smallest equal-model group mean",
            "unit": "One saved response; paired judge scores averaged first",
            "scope": "Exploratory; usable responses in these fixed models and prompts",
            "results": results}


def digest(path):
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def main(run, draws=200_000):
    directory = ROOT / "runs" / run
    data = load_run(run, answers=False, example_checks=False)
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    judgments, numeric = validated_scoring_records(directory, config)
    scores = average_judges(judgments, numeric)
    result = analyze_examples(data, scores, draws)
    paths = [directory / name for name in ("analysis.json", "config.json", "responses.jsonl", "numeric.jsonl")]
    paths += sorted(directory.glob("judged__*.jsonl"))
    paths += [Path(__file__).resolve(), ROOT / "racebench.py"]
    result["source_sha256"] = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    output = ROOT / "results" / run / "example-analysis.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for tid, item in result["results"].items():
        print(tid, item.get("spread"), item.get("p"), item.get("adjusted_p"), item.get("significant"), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--draws", type=int, default=200_000)
    args = parser.parse_args()
    main(args.run, args.draws)
