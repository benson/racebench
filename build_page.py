"""Build a self-contained results page: python build_page.py <run> [--control <run>]"""
import argparse
import base64
import json
from pathlib import Path

from swapbench import DEFAULT_GROUPS, in_run, select

ROOT = Path(__file__).resolve().parent
EXAMPLES = ["offensive_trust", "fired", "comedian", "neighborhood", "salary"]


def font_css():
    directory = Path(__file__).resolve().parent / "assets/fonts"
    rules = ["/* " + (directory / "LICENSE.txt").read_text(encoding="utf-8") + " */"]
    for family, weights in (("Sans", [(400, "Regular"), (500, "Medium"), (600, "SemiBold")]),
                            ("Mono", [(400, "Regular"), (500, "Medium")])):
        for weight, name in weights:
            data = base64.b64encode((directory / f"IBMPlex{family}-{name}.woff2").read_bytes()).decode("ascii")
            rules.append(f'@font-face {{ font-family:"IBM Plex {family}"; font-style:normal; '
                         f'font-weight:{weight}; font-display:swap; src:url(data:font/woff2;base64,{data}) format("woff2") }}')
    return "\n".join(rules)


def load_run(run, answers=True):
    directory = ROOT / "runs" / run
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    analysis = json.loads((directory / "analysis.json").read_text(encoding="utf-8"))
    if config != analysis["config"]:
        raise ValueError(f"Run analyze again for {run}: its config has changed")
    groups = json.loads((ROOT / config.get("groups_file", DEFAULT_GROUPS)).read_text(encoding="utf-8"))
    groups = select(groups, ",".join(config["groups"]))
    data = {"run": run, "models": config["models"], "samples": config["samples"],
            "judges": analysis["judges"], "groups": [{"id": g["id"], "label": g["adj"]} for g in groups],
            "templates": analysis["templates"], "families": analysis["families"],
            "subsets": {}, "cells": {}, "answers": {}, "agreement": analysis["agreement"]}
    data["examples"] = [tid for tid in EXAMPLES if any(t["id"] == tid for t in data["templates"])]
    for subset in ("all", "strict"):
        view = {"index": {}, "stats": {}, "family": {}, "per_judge": {}}
        for model in config["models"]:
            result = analysis["results"][model][subset]
            stats = result["primary"]
            view["index"][model] = {g: {"v": v, "lo": ci[0], "hi": ci[1]}
                                     for g, v, ci in zip(config["groups"], stats["index"], stats["ci"])}
            view["stats"][model] = {"W": stats["w"], "exceed": stats["exceedances"], "draws": stats["draws"],
                                    "used": len(stats["included"]), "total": len(stats["status"])}
            view["family"][model] = {family: row["index"] for family, row in stats["family"].items()}
            if subset == "all":
                for cell in result["cells"]:
                    data["cells"].setdefault(model, {}).setdefault(cell["template"], {})[cell["group"]] = {
                        short: cell[long] for short, long in (("n", "n"), ("raw", "raw_mean"),
                        ("signed", "signed_mean"), ("z", "z"), ("ref", "refusal_rate"), ("cav", "mean_caveats"))}
        for judge, results in analysis["per_judge"].items():
            view["per_judge"][judge] = {model: dict(zip(config["groups"], results[model][subset]["index"]))
                                       for model in config["models"]}
        data["subsets"][subset] = view
    if answers:
        with (directory / "responses.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except ValueError:
                    if not line.endswith("\n"):
                        break
                    raise
                if row.get("error") or row["sample"] != 0 or not in_run(row, config):
                    continue
                text = row["response"].strip()
                if len(text) > 1400:
                    text = text[:1400].rstrip() + " […]"
                data["answers"].setdefault(row["model"], {}).setdefault(row["template"], {})[row["group"]] = text
    return data


def main(run, control=None):
    data = load_run(run)
    data["control"] = load_run(control, answers=False) if control else None
    page = (ROOT / "page_template.html").read_text(encoding="utf-8")
    page = page.replace("/*FONTS*/", font_css())
    blob = json.dumps(data, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    out = ROOT / "results" / run / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.replace("/*DATA*/null", blob), encoding="utf-8", newline="\n")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run")
    parser.add_argument("--control")
    args = parser.parse_args()
    main(args.run, args.control)
