"""Build a self-contained results page for a run: python build_page.py <run-name>"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
FAMILIES = ["celebrate", "humor", "critique", "ingroup", "victim", "rating", "decision"]


def tables(lines):
    out, cur = [], []
    for line in lines + [""]:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not all(set(c) <= set("- :") for c in cells):
                cur.append(cells)
        elif cur:
            out.append(cur)
            cur = []
    return out


def sections(text):
    parts, name, buf = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if name:
                parts[name] = buf
            name, buf = line[3:].strip(), []
        elif name:
            buf.append(line)
    if name:
        parts[name] = buf
    return parts


def main(run):
    run_dir = ROOT / "runs" / run
    groups = json.loads((ROOT / "data/groups.json").read_text(encoding="utf8"))
    templates = json.loads((ROOT / "data/templates.json").read_text(encoding="utf8"))
    config = json.loads((run_dir / "config.json").read_text(encoding="utf8"))
    gids = [g["id"] for g in groups]
    data = {
        "run": run, "models": config["models"], "samples": config.get("samples"),
        "judge": config.get("judge_model", "openai/gpt-6-luna"),
        "groups": [{"id": g["id"], "label": g["adj"]} for g in groups],
        "templates": templates, "families": FAMILIES,
        "index": {}, "stats": {}, "family": {}, "cells": {}, "answers": {},
    }
    for model, lines in sections((run_dir / "report.md").read_text(encoding="utf8")).items():
        if model not in config["models"]:
            continue
        tabs = tables(lines)
        idx = next(t for t in tabs if t[0][:2] == ["Group", "Index"])
        data["index"][model] = {r[0]: {"v": float(r[1]), "lo": float(r[2]), "hi": float(r[3])} for r in idx[1:]}
        st = next(t for t in tabs if t[0][0] == "Index variance")
        excl = next((t for t in tabs if t[0] == ["Template", "Reason"]), [[]])
        data["stats"][model] = {"W": float(st[1][3]), "exceed": int(st[1][2]),
                                "excluded": {r[0]: r[1] for r in excl[1:]}}
        fam = next(t for t in tabs if t[0][0] == "Family")
        data["family"][model] = {r[0]: {g: float(v) for g, v in zip(fam[0][2:], r[2:])} for r in fam[1:]}

    def num(x):
        try:
            return round(float(x), 3)
        except ValueError:
            return None

    with open(run_dir / "scores.csv", encoding="utf8", newline="") as fh:
        for r in csv.DictReader(fh):
            cell = {"n": int(r["n"] or 0), "raw": num(r["raw_mean"]), "signed": num(r["signed_mean"]),
                    "z": num(r["z"]), "ref": num(r["refusal_rate"]), "cav": num(r["mean_caveats"])}
            data["cells"].setdefault(r["model"], {}).setdefault(r["template"], {})[r["group"]] = cell

    with open(run_dir / "responses.jsonl", encoding="utf8") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("error") or d["sample"] != 0:
                continue
            text = d["response"].strip()
            if len(text) > 1400:
                text = text[:1400].rstrip() + " […]"
            data["answers"].setdefault(d["model"], {}).setdefault(d["template"], {})[d["group"]] = text

    page = (ROOT / "page_template.html").read_text(encoding="utf8")
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = ROOT / "results" / run / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.replace("/*DATA*/null", blob), encoding="utf8", newline="\n")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
