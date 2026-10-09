

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings
from .pipeline import run_pipeline
from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen and rank PDF resumes.")
    parser.add_argument("--input", type=Path, required=True, help="Directory containing PDF resumes")
    parser.add_argument("--output", type=Path, required=True, help="Path for results.json")
    args = parser.parse_args()
    if not args.input.is_dir():
        parser.error(f"Input directory does not exist: {args.input}")
    report = run_pipeline(args.input, load_settings())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"Processed {report.summary.total_resumes} resumes. Results written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
