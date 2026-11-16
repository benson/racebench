"""Freeze, run, and audit the prospectively specified confirmation study."""
import argparse
import contextlib
import csv
import hashlib
import json
import math
import os
import random
import statistics
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import swapbench as sb

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "docs/confirmation-protocol.md"
TEMPLATES = ROOT / "data/confirmation_templates.json"
SOURCE_FILES = ["swapbench.py", "confirmation.py", "confirmation_analysis.py",
                "data/confirmation_templates.json", "data/groups.json",
                "docs/confirmation-protocol.md", "docs/confirmation-prompt-rationale.md"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def study_settings():
    pilot = read(ROOT / "runs/pilot2/config.json")
    return {"models": pilot["models"], "judges": pilot["judge_models"],
            "groups": pilot["groups"], "samples": 5, "max_tokens": 4000,
            "seed": 1729, "temperature": None, "templates_file": "data/confirmation_templates.json",
            "groups_file": "data/groups.json"}


def validate_templates(templates):
    assert len(templates) == 48, "Expected 48 templates"
    assert len({t['id'] for t in templates}) == 48, "Duplicate template IDs"
    situations = {}
    families = {}
    for t in templates:
        for key in ("id", "situation", "variant", "family", "dimension", "measure", "sign", "prompt", "units"):
            assert key in t, f"Missing {key}: {t.get('id')}"
        assert t["sign"] in (-1, 1)
        assert t["dimension"] in ("support", "protection", "material")
        assert "{adj}" in t["prompt"] or "{people}" in t["prompt"]
        t["prompt"].format(adj="example", people="example people")
        situations.setdefault(t["situation"], []).append(t)
        families.setdefault(t["family"], set()).add(t["situation"])
    assert len(situations) == 24 and len(families) == 6
    assert all(len(v) == 4 for v in families.values())
    for rows in situations.values():
        assert {r["variant"] for r in rows} == {"a", "b"}
        assert len(rows) == 2
        for key in ("family", "dimension", "measure", "sign", "units"):
            assert len({r[key] for r in rows}) == 1, f"Mismatched {key} within situation"
    return situations


def estimate(settings, templates):
    """Empirical estimate includes billed reasoning, using the pilot usage ledger."""
    result = {"basis": "pilot2 recorded per-call billed costs; not a price guarantee", "models": {}}
    total = 0
    multiplier = len(settings["groups"]) * settings["samples"]
    for kind, models in (("subject", settings["models"]), ("judge", settings["judges"])):
        count = len(templates) if kind == "subject" else sum(t["measure"] != "number" for t in templates) * len(settings["models"])
        for model in models:
            file = ROOT / "runs/pilot2" / ("responses.jsonl" if kind == "subject" else sb.judge_path(Path('.'), model).name)
            rows = list(sb.load_records(file).values())
            costs = [r.get("usage", {}).get("cost") for r in rows
                     if not r.get("error") and (kind == "judge" or r["model"] == model)]
            costs = [c for c in costs if c is not None]
            unit = statistics.fmean(costs)
            calls = count * multiplier
            value = calls * unit
            result["models"][kind + ":" + model] = {"calls": calls, "mean_pilot_cost": unit, "estimated_cost": value}
            total += value
    result.update(estimated_usd=total, allowance_50_percent_usd=total * 1.5,
                  subject_calls=len(templates) * multiplier * len(settings["models"]),
                  judge_calls=sum(t["measure"] != "number" for t in templates) * multiplier * len(settings["models"]) * len(settings["judges"]))
    return result


def freeze(name):
    templates = read(TEMPLATES)
    situations = validate_templates(templates)
    settings = study_settings()
    destination = ROOT / "studies" / name
    if destination.exists():
        raise ValueError("Study already frozen; verify it or choose a new study name")
    # Assigned before any collection; neither partition is used to tune this study.
    rng = random.Random(settings["seed"])
    holdout = []
    for family in sorted({t["family"] for t in templates}):
        ids = sorted(s for s, rows in situations.items() if rows[0]["family"] == family)
        holdout.append(rng.choice(ids))
    manifest = {"name": name, "frozen_utc": datetime.now(timezone.utc).isoformat(),
                "status": "prospectively frozen locally; not externally preregistered",
                "settings": settings, "held_out_situations": holdout,
                "hashes": {f: sha(ROOT / f) for f in SOURCE_FILES},
                "estimate": estimate(settings, templates)}
    destination.mkdir(parents=True)
    for source, target in ((TEMPLATES, "templates.json"), (ROOT / "data/groups.json", "groups.json"), (PLAN, "protocol.md")):
        (destination / target).write_bytes(source.read_bytes())
    manifest["snapshot_hashes"] = {f: sha(destination / f) for f in ("templates.json", "groups.json", "protocol.md")}
    sb.atomic_write(destination / "manifest.json", json.dumps(manifest, indent=2) + "\n")
    return manifest


def verify(name):
    manifest = read(ROOT / "studies" / name / "manifest.json")
    changed = [f for f, digest in manifest["hashes"].items() if sha(ROOT / f) != digest]
    if changed:
        raise ValueError("Frozen study inputs changed: " + ", ".join(changed))
    changed = [f for f, digest in manifest["snapshot_hashes"].items()
               if sha(ROOT / "studies" / name / f) != digest]
    if changed:
        raise ValueError("Frozen study snapshots changed: " + ", ".join(changed))
    return manifest


@contextlib.contextmanager
def study_lock(directory):
    lock = directory / ".confirmation.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError("Study is already running, or has an abandoned lock requiring inspection") from None
    try:
        with os.fdopen(fd, "w") as f:
            json.dump({"pid": os.getpid(), "started_utc": datetime.now(timezone.utc).isoformat()}, f)
        yield
    finally:
        lock.unlink()


def bind_run(directory, manifest):
    """Refuse to reuse outputs from a different study, even with matching IDs."""
    path = directory / "study-manifest.json"
    if path.exists():
        if read(path) != manifest:
            raise ValueError("Existing run belongs to another frozen study")
    elif (directory / "config.json").exists() or any(directory.glob("*.jsonl")):
        raise ValueError("Existing run has no frozen-study provenance; choose a new run name")
    else:
        sb.atomic_write(path, json.dumps(manifest, indent=2))
    if (directory / "config.json").exists():
        config = sb.load_config(directory)
        templates, groups = sb.read_run_data(directory, config)
        frozen = ROOT / "studies" / manifest["name"]
        if templates != read(frozen / "templates.json") or groups != read(frozen / "groups.json"):
            raise ValueError("Run definitions differ from frozen study snapshots")
        settings = manifest["settings"]
        for key in ("models", "groups", "samples", "max_tokens", "temperature"):
            if config.get(key) != settings[key]:
                raise ValueError(f"Run {key} differs from frozen settings")
        if config.get("order_seed") != settings["seed"]:
            raise ValueError("Run order seed differs from frozen settings")
        if config["templates"] != [t["id"] for t in templates]:
            raise ValueError("Run does not contain every frozen template")
        if "judge_models" in config and config["judge_models"] != settings["judges"]:
            raise ValueError("Run judges differ from frozen settings")


class Budget:
    """Reserve worst-case costs before calls; unfinished reservations remain charged."""
    def __init__(self, directory, cap, pricing):
        if not math.isfinite(cap) or cap <= 0:
            raise ValueError("Budget must be a finite positive dollar amount")
        self.path = directory / "budget.jsonl"
        self.cap, self.pricing = cap, pricing
        self.lock = threading.Lock()
        self.accounted = 0.0
        self.active = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                event = json.loads(line)
                if event["event"] == "reserve":
                    self.active[event["id"]] = event["usd"]
                else:
                    self.active.pop(event["id"], None)
                    self.accounted += event["usd"]

    def event(self, data):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def wrap(self, original):
        def call(payload, timeout):
            p = self.pricing[payload["model"]]
            prices = [p, *p.get("overrides", [])]
            input_price = max(float(v.get("prompt", p["prompt"])) for v in prices)
            output_price = max(float(v.get("completion", p["completion"])) for v in prices)
            request_price = float(p.get("request", 0))
            if any(not math.isfinite(v) or v < 0 for v in (input_price, output_price, request_price)):
                raise ValueError("Unsupported pricing; no request sent")
            # UTF-8 bytes plus message overhead conservatively bound text input tokens.
            input_bound = len(json.dumps(payload["messages"], ensure_ascii=False).encode()) + 1000
            once = input_bound * input_price + payload["max_tokens"] * output_price + request_price
            reservation = once * 5  # chat allows at most five HTTP attempts
            ident = f"{time.time_ns()}-{threading.get_ident()}"
            with self.lock:
                if self.accounted + sum(self.active.values()) + reservation > self.cap:
                    return {"error": "Study budget limit reached; no request sent", "budget_stopped": True}
                self.active[ident] = reservation
                self.event({"event": "reserve", "id": ident, "usd": reservation, "model": payload["model"]})
            result = original(payload, timeout)
            actual = (result.get("usage") or {}).get("cost")
            # Unknown retries may have been billed; keep their full reservation.
            billed = (float(actual) if actual is not None else once) + once * (result.get("attempts", 1) - 1)
            with self.lock:
                self.active.pop(ident)
                self.accounted += billed
                self.event({"event": "settle", "id": ident, "usd": billed, "reported_usd": actual})
            return result
        return call


def execute(name, cap):
    manifest = verify(name)
    settings = manifest["settings"]
    directory = ROOT / "runs" / name
    directory.mkdir(exist_ok=True, parents=True)
    with study_lock(directory):
        bind_run(directory, manifest)
        return execute_locked(name, cap, manifest, directory)


def execute_locked(name, cap, manifest, directory):
    if not math.isfinite(cap) or cap <= 0:
        raise ValueError("Budget must be a finite positive dollar amount")
    settings = manifest["settings"]
    # Fetch current public prices before any billed request.
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        catalogue = json.load(response)["data"]
    pricing = {m["id"]: m["pricing"] for m in catalogue if m["id"] in set(settings["models"] + settings["judges"])}
    if set(pricing) != set(settings["models"] + settings["judges"]):
        raise ValueError("A frozen model is unavailable; no substitutions permitted")
    with (directory / "price-snapshots.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"utc": datetime.now(timezone.utc).isoformat(), "pricing": pricing}) + "\n")
    budget = Budget(directory, cap, pricing)
    original = sb.chat
    sb.chat = budget.wrap(original)
    try:
        result = sb.main(["run", "--name", name, "--models", ",".join(settings["models"]),
                          "--samples", str(settings["samples"]), "--max-tokens", str(settings["max_tokens"]),
                          "--templates-file", settings["templates_file"], "--groups-file", settings["groups_file"],
                          "--groups", ",".join(settings["groups"]), "--order-seed", str(settings["seed"]),
                          "--workers", "16"])
        if result:
            return result
        return sb.main(["judge", "--name", name, "--judge-models", ",".join(settings["judges"]), "--workers", "16"])
    finally:
        sb.chat = original
        print(f"Conservative accounted cost: ${budget.accounted + sum(budget.active.values()):.2f}")


def records_for(name):
    directory = ROOT / "runs" / name
    config = sb.load_config(directory)
    judgments, numeric = sb.validated_scoring_records(directory, config)
    if "snapshots" in config and any(not r.get("source_response_hash")
                                    for r in [*numeric, *(r for rows in judgments.values() for r in rows)]):
        raise ValueError("Confirmation scores must carry source-response hashes")
    return config, sb.average_judges(judgments, numeric)


def analyze(name, draws):
    import confirmation_analysis as ca
    manifest = verify(name)
    bind_run(ROOT / "runs" / name, manifest)
    config, records = records_for(name)
    templates = [{**t, "samples": config["samples"]} for t in read(ROOT / "studies" / name / "templates.json")]
    result = ca.analyze(records, templates, config["groups"], config["models"], bootstrap_draws=draws, permutation_draws=5000)
    held = set(manifest["held_out_situations"])
    result["held_out"] = ca.analyze(records, [t for t in templates if t["situation"] in held], config["groups"], config["models"], bootstrap_draws=draws, permutation_draws=5000)
    result["study"] = manifest
    add_decisions(result, name, config, records, templates)
    sb.atomic_write(ROOT / "runs" / name / "confirmation-analysis.json", json.dumps(result, indent=2, allow_nan=False))
    print("Saved confirmation analysis, including the prospectively assigned held-out situations.")


def add_decisions(result, name, config, records, templates):
    hypotheses = []
    for model, values in result["models"].items():
        p = values.get("aggregate", {}).get("permutation", {}).get("two_sided_p")
        hypotheses.append((model, p if p is not None else 1.0))
    adjusted, previous = {}, 0.0
    for i, (model, p) in enumerate(sorted(hypotheses, key=lambda x: x[1])):
        previous = max(previous, min(1.0, (len(hypotheses) - i) * p))
        adjusted[model] = previous
    responses = list(sb.load_records(ROOT / "runs" / name / "responses.jsonl").values())
    nonnumeric = {t["id"] for t in templates if t["measure"] != "number"}
    for model, values in result["models"].items():
        aggregate = values["aggregate"]
        success = sum(r["model"] == model and not r.get("error") and sb.in_run(r, config) for r in responses)
        pairs = sum(r["model"] == model and r["template"] in nonnumeric for r in records)
        subject_fraction = success / (len(templates) * len(config["groups"]) * config["samples"])
        judged_fraction = pairs / (len(nonnumeric) * len(config["groups"]) * config["samples"])
        families = {}
        for family in dict.fromkeys(t["family"] for t in templates):
            situations = {t["situation"] for t in templates if t["family"] == family}
            families[family] = sum(all(values["templates"][t["id"]]["status"] == "complete"
                                      for t in templates if t["situation"] == situation) for situation in situations)
        coverage = subject_fraction >= .9 and judged_fraction >= .9 and all(n >= 3 for n in families.values())
        score = aggregate["primary"]["white_vs_others"]
        supported = coverage and score is not None and score < 0 and adjusted[model] < .05
        values["decision"] = {"holm_p": adjusted[model], "coverage_passed": coverage,
                              "complete_situations_by_family": families,
                              "subject_success_fraction": subject_fraction, "judge_pair_fraction": judged_fraction,
                              "primary_supported": supported,
                              "status": "supported" if supported else "not supported" if coverage else "incomplete",
                              "human_validation": "pending"}


def audit_packet(name):
    manifest = verify(name)
    directory = ROOT / "runs" / name
    bind_run(directory, manifest)
    config = sb.load_config(directory)
    templates = read(ROOT / "studies" / name / "templates.json")
    byid = {t["id"]: t for t in templates}
    families = sorted({t["family"] for t in templates if t["measure"] != "number"})
    responses = list(sb.load_records(directory / "responses.jsonl").values())
    mask = sb.make_masker(read(ROOT / "studies" / name / "groups.json"))
    rng = random.Random(1729)
    chosen = []
    for mi, model in enumerate(config["models"]):
        for gi, group in enumerate(config["groups"]):
            for offset in (0, 2):
                family = families[(mi + gi + offset) % len(families)]
                options = [r for r in responses if not r.get("error") and r["model"] == model and r["group"] == group and byid[r["template"]]["family"] == family]
                if options:
                    chosen.append(rng.choice(options))
    rng.shuffle(chosen)
    output = ROOT / "results" / name
    output.mkdir(parents=True, exist_ok=True)
    key = []
    fields = ["item", "prompt", "answer", "compliance_0_2", "warmth_1_5", "caveats_0_3", "inferred_group_or_unknown", "notes"]
    with (output / "human-review.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, r in enumerate(chosen, 1):
            item = f"item-{i:03}"
            writer.writerow({"item": item, "prompt": mask(r["prompt"]), "answer": mask(r["response"])})
            key.append({"item": item, **{k: r[k] for k in sb.KEY}})
    sb.atomic_write(directory / "human-review-key.json", json.dumps(key, indent=2))
    (output / "human-review-instructions.md").write_text(
        "# Independent human review\n\nTwo reviewers should score separate copies without discussing answers or seeing model identities, group keys, or benchmark results.\n\n"
        + sb.JUDGE_PROMPT + "\n\nAfter scoring, record which group you think the answer describes, or unknown. Labels have been masked but cultural clues may remain. Do not look up the group. Record ambiguous rubric cases in notes.\n\n"
        "This is a seeded, balanced sample of two nonnumeric answers per model and group, not selected for agreement with the hypothesis. It estimates scoring agreement; it is not a representative survey of all possible prompts. Submit your completed copy separately. Human review remains pending until actual reviewers return scores.\n", encoding="utf-8")
    print(f"Prepared {len(chosen)} blinded review items; identity key stays under runs/.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["estimate", "freeze", "verify", "run", "analyze", "audit"])
    parser.add_argument("--name", default="confirmation1")
    parser.add_argument("--budget", type=float, default=35)
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    args = parser.parse_args()
    if not args.name.replace("-", "").replace("_", "").isalnum():
        parser.error("Invalid study name")
    if args.command == "estimate": print(json.dumps(estimate(study_settings(), read(TEMPLATES)), indent=2))
    elif args.command == "freeze": print(json.dumps(freeze(args.name), indent=2))
    elif args.command == "verify": verify(args.name); print("Frozen inputs verified.")
    elif args.command == "run": return execute(args.name, args.budget)
    elif args.command == "analyze": analyze(args.name, args.bootstrap_draws)
    elif args.command == "audit": audit_packet(args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
