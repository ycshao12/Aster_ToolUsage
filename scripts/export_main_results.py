"""Export the non-ablation main table from the paper's final summary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

OUTPUT = Path(__file__).parents[1] / "results"

FIELDS = [
    "benchmark",
    "model",
    "method",
    "n",
    "task_similarity",
    "ts",
    "proper",
    "under",
    "over",
    "ster",
    "spr",
    "tool_calls",
    "model_calls",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    data = json.loads(args.source.read_text())
    rows = []
    for source_row in data["rows"]:
        row = {field: source_row.get(field) for field in FIELDS}
        row["method"] = "Aster" if row["method"] == "Aster r108" else row["method"]
        rows.append(row)

    args.output.mkdir(exist_ok=True)
    (args.output / "main_results.json").write_text(
        json.dumps(
            {
                "artifact": "Aster main evaluation",
                "version": data["aster_version"],
                "judge_version": data["judge_version"],
                "source_sha256": data["source_sha256"],
                "ablation_included": False,
                "fields": FIELDS,
                "rows": rows,
            },
            indent=2,
        )
        + "\n"
    )
    with (OUTPUT / "main_results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
