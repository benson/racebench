"""Import two completed independent human audit copies without making model calls."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

import swapbench as sb


RUBRIC = {"compliance": (0, 2), "warmth": (1, 5), "caveats": (0, 3)}
SCORE_COLUMNS = {"compliance": "compliance_0_2", "warmth": "warmth_1_5", "caveats": "caveats_0_3"}
REQUIRED_COLUMNS = {"item", "prompt", "answer", "inferred_group_or_unknown", *SCORE_COLUMNS.values()}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_aliases(groups):
    aliases = {}
    for group in groups:
        for label in (group["id"], group.get("adj"), group.get("people"), group.get("label"), *group.get("mask", [])):
            if label:
                normalized = label.strip().casefold()
                if normalized in aliases and aliases[normalized] != group["id"]:
                    raise ValueError(f"Ambiguous group alias: {label}")
                aliases[normalized] = group["id"]
    return aliases


def read_key(directory, config, templates, responses):
    key = json.loads((directory / "human-review-key.json").read_text(encoding="utf-8"))
    if not isinstance(key, list) or not key:
        raise ValueError("Human review key must contain at least one item")
    by_id = {template["id"]: template for template in templates}
    items, seen_sources = {}, set()
    for row in key:
        if not isinstance(row, dict) or not isinstance(row.get("item"), str) or not row["item"].strip():
            raise ValueError("Human review key contains an invalid item ID")
        item = row["item"]
        if not all(field in row for field in sb.KEY) or not sb.in_run(row, config):
            raise ValueError(f"Human review item is outside the saved run: {item}")
        source_key = sb.record_key(row)
        if item in items or source_key in seen_sources:
            raise ValueError(f"Human review key contains a duplicate item or answer: {item}")
        if source_key not in responses or by_id[row["template"]]["measure"] == "number":
            raise ValueError(f"Human review item has no successful nonnumeric source: {item}")
        items[item] = row
        seen_sources.add(source_key)
    return items


def read_review(path, reviewer, items, responses, mask, aliases):
    rows = {}
    with Path(path).open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"{reviewer}: missing or duplicate CSV headers")
        if REQUIRED_COLUMNS - set(reader.fieldnames):
            raise ValueError(f"{reviewer}: missing columns: {', '.join(sorted(REQUIRED_COLUMNS - set(reader.fieldnames)))}")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(raw.get(field) is None for field in REQUIRED_COLUMNS):
                raise ValueError(f"{reviewer}: malformed CSV row {line}")
            item = raw["item"].strip()
            if item not in items:
                raise ValueError(f"{reviewer}: unknown item ID {item!r} on row {line}")
            if item in rows:
                raise ValueError(f"{reviewer}: duplicate item ID {item}")
            source = responses[sb.record_key(items[item])]
            if raw["prompt"] != mask(source["prompt"]) or raw["answer"] != mask(source["response"]):
                raise ValueError(f"{reviewer}: prompt or answer differs from the saved audit item: {item}")
            scores = {}
            for field, (low, high) in RUBRIC.items():
                value = raw[SCORE_COLUMNS[field]].strip()
                if not re.fullmatch(r"\d+", value) or not low <= int(value) <= high:
                    raise ValueError(f"{reviewer}: {item} needs an integer {field} score from {low} to {high}")
                scores[field] = int(value)
            guess = raw["inferred_group_or_unknown"].strip()
            if not guess:
                raise ValueError(f"{reviewer}: {item} needs a group guess or explicit 'unknown'")
            unknown = guess.casefold() == "unknown"
            guessed_group = None if unknown else aliases.get(guess.casefold())
            rows[item] = {"scores": scores, "group_guess": guess, "unknown": unknown,
                          "guessed_group": guessed_group, "correct_group_guess": not unknown and guessed_group == items[item]["group"],
                          "raw_csv_row": raw}
    missing = set(items) - set(rows)
    if missing:
        raise ValueError(f"{reviewer}: incomplete review; missing {len(missing)} items: {', '.join(sorted(missing))}")
    return rows


def compare(left, right):
    if not left or set(left) != set(right):
        raise ValueError("Agreement comparisons require the same nonempty item set")
    fields = {}
    for field in RUBRIC:
        differences = [abs(left[item][field] - right[item][field]) for item in left]
        exact = sum(value == 0 for value in differences)
        fields[field] = {"n": len(differences), "exact_count": exact,
                         "exact_agreement": exact / len(differences),
                         "mean_absolute_difference": statistics.fmean(differences)}
    disagreements = [{"item": item, "left": left[item], "right": right[item],
                      "absolute_differences": {field: abs(left[item][field] - right[item][field]) for field in RUBRIC}}
                     for item in sorted(left) if any(left[item][field] != right[item][field] for field in RUBRIC)]
    return {"n": len(left), "fields": fields, "disagreement_count": len(disagreements), "disagreements": disagreements}


def group_guess_summary(rows):
    total = len(rows)
    unknown = sum(row["unknown"] for row in rows.values())
    guessed = total - unknown
    correct = sum(row["correct_group_guess"] for row in rows.values())
    return {"n": total, "unknown_count": unknown, "guessed_count": guessed,
            "unrecognized_guess_count": sum(not row["unknown"] and row["guessed_group"] is None for row in rows.values()),
            "correct_count": correct, "accuracy_all_items": correct / total,
            "accuracy_among_guesses": correct / guessed if guessed else None}


def status(name):
    directory = sb.run_directory(name)
    result_path = directory / "human-review-results.json"
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        return {"status": result["status"], "reviewers": [review["name"] for review in result["reviews"]],
                "items": len(result["items"]), "results": str(result_path)}
    key_path = directory / "human-review-key.json"
    return {"status": "pending", "reason": "completed human reviews have not been imported" if key_path.exists()
            else "human audit packet has not been generated", "required_reviewers": 2}


def report_text(result):
    lines = [f"# Human audit: {result['run']}", "", f"Imported two completed reviews covering {len(result['items'])} answers.",
             "Reviewer names are supplied by the importer. This utility cannot verify that the reviewers are different people or worked independently.",
             "These audit scores assess scoring agreement and masking; they do not rerank models or replace the primary study results.", "",
             "| Comparison | Measure | Exact agreement | Mean absolute difference |", "| --- | --- | --- | --- |"]
    for comparison in result["comparisons"]:
        for field, values in comparison["statistics"]["fields"].items():
            label = (comparison["left"] + " / " + comparison["right"]).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {label} | {field} | {values['exact_count']}/{values['n']} ({values['exact_agreement']:.1%}) | {values['mean_absolute_difference']:.3f} |")
    lines += ["", "Group-identification results:", ""]
    for review in result["reviews"]:
        guesses = review["group_guesses"]
        accuracy = "not applicable" if guesses["accuracy_among_guesses"] is None else f"{guesses['accuracy_among_guesses']:.1%}"
        lines.append(f"- {review['name']}: {guesses['unknown_count']} unknown; {guesses['guessed_count']} guesses; {guesses['correct_count']} correct ({accuracy} of guesses).")
    lines += ["", "Per-item disagreements, original CSV scores, group guesses, source keys, and input fingerprints are retained in human-review-results.json."]
    return "\n".join(lines) + "\n"


def import_reviews(name, reviewers):
    if len(reviewers) != 2:
        raise ValueError("Exactly two completed independent reviewer copies are required")
    reviewers = [(name.strip(), Path(path).resolve()) for name, path in reviewers]
    names = [name.casefold() for name, _ in reviewers]
    if not all(names) or len(set(names)) != 2:
        raise ValueError("Two distinct nonempty reviewer names are required")
    if reviewers[0][1] == reviewers[1][1]:
        raise ValueError("Reviewers must supply separate completed CSV files")
    directory = sb.run_directory(name)
    with sb.run_lock(directory):
        config = sb.load_config(directory)
        templates, groups = sb.read_run_data(directory, config)
        judgments, _ = sb.validated_scoring_records(directory, config)
        if len(judgments) < 1:
            raise ValueError("No LLM judges are configured")
        responses = sb.load_records(directory / "responses.jsonl")
        items = read_key(directory, config, templates, responses)
        mask, aliases = sb.make_masker(groups), group_aliases(groups)
        reviews = []
        for reviewer, path in reviewers:
            rows = read_review(path, reviewer, items, responses, mask, aliases)
            reviews.append({"name": reviewer, "source_file": str(path), "source_sha256": sha(path),
                            "items": rows, "group_guesses": group_guess_summary(rows)})
        llm_scores = {}
        for judge, rows in judgments.items():
            by_key = sb.scored_records(rows)
            scores = {}
            for item, key in items.items():
                source_key = sb.record_key(key)
                if source_key not in by_key:
                    raise ValueError(f"LLM judge {judge} has no complete score for {item}")
                row = by_key[source_key]
                if any(type(row[field]) is not int or not low <= row[field] <= high for field, (low, high) in RUBRIC.items()):
                    raise ValueError(f"LLM judge {judge} has an invalid rubric score for {item}")
                scores[item] = {field: row[field] for field in RUBRIC}
            llm_scores[judge] = scores
        human_scores = [{item: row["scores"] for item, row in review["items"].items()} for review in reviews]
        comparisons = [{"kind": "human_human", "left": reviews[0]["name"], "right": reviews[1]["name"],
                        "statistics": compare(*human_scores)}]
        for review, scores in zip(reviews, human_scores):
            for judge, judged_scores in llm_scores.items():
                comparisons.append({"kind": "human_llm", "left": review["name"], "right": judge,
                                    "statistics": compare(scores, judged_scores)})
        inputs = [directory / "config.json", directory / "responses.jsonl", directory / "human-review-key.json",
                  *sb.definition_paths(directory, config), *(sb.judge_path(directory, judge) for judge in judgments)]
        result = {"version": 1, "run": name, "status": "complete", "imported_at": datetime.now(timezone.utc).isoformat(),
                  "scope": "scoring agreement and group identification on the audit packet only; no primary model reranking",
                  "reviewer_independence": "required by protocol; reviewer identity and independence cannot be verified programmatically",
                  "items": items, "reviews": reviews, "llm_scores": llm_scores, "comparisons": comparisons,
                  "input_sha256": {str(path.relative_to(directory)) if path.is_relative_to(directory) else str(path): sha(path) for path in inputs}}
        sb.atomic_write(directory / "human-review-results.json", json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n")
        sb.atomic_write(directory / "human-review-report.md", report_text(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "import"):
        child = commands.add_parser(command)
        child.add_argument("--name", required=True)
        if command == "import":
            child.add_argument("--reviewer", action="append", nargs=2, metavar=("NAME", "CSV"), required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "import":
            import_reviews(args.name, args.reviewer)
        print(json.dumps(status(args.name), indent=2))
        return 0
    except (ValueError, OSError, KeyError, csv.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
