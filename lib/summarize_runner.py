#!/usr/bin/env python3
"""
Phorager summarize runner — called by the SUMMARIZE Nextflow process.

This script is NOT intended to be called directly by users. It is invoked
by the SUMMARIZE Nextflow process inside the parsing_env conda environment
or Singularity container, with the correct dependencies already present.

The entry point for users is: phorager summarize ...

How it locates lib/summaries/:
    This file lives at lib/summarize_runner.py. It inserts its own parent
    directory (lib/) into sys.path, which makes 'import summaries' work
    regardless of what the Nextflow working directory is.

How to add a new summary type:
    See ADDING_NEW_SUMMARIES.md in the project root.
"""

import argparse
import sys
from pathlib import Path

# lib/ is this file's parent directory. Adding it to sys.path makes the
# summaries package importable from inside a Nextflow work directory, where
# the working directory is a temporary staging area, not the project root.
sys.path.insert(0, str(Path(__file__).parent))

# Importing summaries triggers __init__.py auto-discovery, which registers
# all summary classes via registry.register(). No manual imports needed.
import summaries  # noqa: F401
from summaries.registry import registry

_FORMATS = ("tsv", "csv")


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Phorager summary table (called by Nextflow)."
    )
    parser.add_argument(
        "--type", required=True,
        metavar="SUMMARY_TYPE",
        help="Summary type to generate (e.g. bacterial_genome, prophage_table).",
    )
    parser.add_argument(
        "--output", required=True,
        metavar="FILE",
        help="Output file path.",
    )
    parser.add_argument(
        "--format",
        choices=_FORMATS,
        default="tsv",
        help="Output format: tsv (default) or csv.",
    )
    parser.add_argument(
        "--bacterial-outdir",
        metavar="DIR",
        default=None,
        help="Directory containing bacterial workflow output.",
    )
    parser.add_argument(
        "--annotation-outdir",
        metavar="DIR",
        default=None,
        help="Directory containing annotation workflow output.",
    )
    return parser.parse_args()


def _write(df, path: str, fmt: str):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "tsv":
        df.to_csv(out, sep="\t", index=False)
    else:
        df.to_csv(out, index=False)
    print(f"Summary written to: {out}")
    print(f"  Rows   : {len(df)}")
    print(f"  Columns: {list(df.columns)}")


def main():
    args = _parse_args()

    dirs = dict(
        bacterial_outdir=args.bacterial_outdir,
        annotation_outdir=args.annotation_outdir,
    )

    # -- Retrieve summary instance --
    try:
        summary = registry.get(args.type)
    except KeyError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    # -- Validate input files --
    ok, messages = summary.validate(**dirs)
    for msg in messages:
        prefix = "Error" if "[REQUIRED]" in msg else "Warning"
        print(f"{prefix}: {msg}")
    if not ok:
        print(f"Cannot generate '{args.type}': required input files are missing.")
        sys.exit(1)

    # -- Generate --
    print(f"Generating '{args.type}' summary...")
    try:
        df = summary.generate(**dirs)
    except Exception as exc:
        print(f"Error generating summary: {exc}")
        sys.exit(1)

    if df.empty:
        print("Warning: The generated summary table is empty.")

    # -- Write --
    _write(df, args.output, args.format)


if __name__ == "__main__":
    main()
