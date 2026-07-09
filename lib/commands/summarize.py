"""
Phorager Summarize Command

Generates summary tables from completed Phorager workflow outputs by
delegating to the SUMMARIZE Nextflow process, which runs inside the
parsing_env conda environment or Singularity container.

Summary types are defined in lib/summaries/. See ADDING_NEW_SUMMARIES.md
for instructions on adding new types.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


# Known summary types — used only for --list display and basic validation.
# The authoritative registry lives in lib/summaries/registry.py and is used
# at runtime inside the Nextflow process.
_KNOWN_SUMMARIES = {
    "bacterial_genome": "Per-genome QC metrics (CheckM2) with prophage counts",
    "prophage_table":   "Per-prophage table: host, cluster, CheckV quality, length, CDS count",
}

_FORMATS = ("tsv", "csv")


class SummarizeCommand:

    def __init__(self):
        self.config_dir  = Path.home() / '.phorager'
        self.config_file = self.config_dir / 'config.json'

    # ------------------------------------------------------------------ #
    #  Argument definitions                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_arguments(parser):
        parser.add_argument(
            "--type", "-t",
            metavar="SUMMARY_TYPE",
            help="Summary type to generate. Use --list to see available types.",
        )
        parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="List all available summary types with descriptions.",
        )
        parser.add_argument(
            "--outdir",
            metavar="DIR",
            default="results/",
            help=(
                "Main results directory — the same --outdir used for your "
                "bacterial/prophage/annotation runs (default: results/). "
                "Output is written to {outdir}/4.Summaries/{type}.{format}."
            ),
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
        parser.add_argument(
            "--format", "-f",
            choices=_FORMATS,
            default="tsv",
            help="Output format: tsv (default) or csv.",
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            help="Resume a previous Nextflow run.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the Nextflow command that would be run without executing it.",
        )

    # ------------------------------------------------------------------ #
    #  Entry point                                                         #
    # ------------------------------------------------------------------ #

    def run(self, args) -> bool:
        try:
            if getattr(args, "list", False):
                self._print_list()
                return True

            if not getattr(args, "type", None):
                print("Error: --type is required unless --list is specified.")
                print("       Run 'phorager summarize --list' to see available types.")
                return False

            params = self._validate_parameters(args)
            cmd    = self._build_nextflow_command(params, args)

            if args.dry_run:
                self._show_plan(params, cmd)
                return True

            phorager_dir = Path(sys.argv[0]).resolve().parent
            os.chdir(phorager_dir)
            return self._execute_nextflow(cmd)

        except ValueError as exc:
            print(f"Error: {exc}")
            return False
        except Exception as exc:
            print(f"Unexpected error: {exc}")
            return False

    # ------------------------------------------------------------------ #
    #  Configuration                                                       #
    # ------------------------------------------------------------------ #

    def _load_config(self) -> dict:
        import json
        defaults = {"backend": "singularity", "cache_location": None}
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    cfg = json.load(f)
                defaults["backend"]        = cfg.get("backend", defaults["backend"])
                defaults["cache_location"] = cfg.get("cache_location")
            except Exception as exc:
                print(f"Warning: Could not read phorager config ({exc}). Using defaults.")
        return defaults

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def _validate_parameters(self, args) -> dict:
        summary_type = args.type
        if summary_type not in _KNOWN_SUMMARIES:
            known = ", ".join(sorted(_KNOWN_SUMMARIES))
            raise ValueError(
                f"Unknown summary type '{summary_type}'. "
                f"Known types: {known}. "
                f"Use --list for descriptions."
            )

        outdir = str(Path(args.outdir).resolve())

        bacterial_outdir  = self._resolve_dir(args.bacterial_outdir,  "--bacterial-outdir")
        annotation_outdir = self._resolve_dir(args.annotation_outdir, "--annotation-outdir")

        if bacterial_outdir is None and annotation_outdir is None:
            raise ValueError(
                "At least one of --bacterial-outdir or --annotation-outdir must be provided."
            )

        config = self._load_config()

        return {
            "summary_type":      summary_type,
            "outdir":            outdir,
            "bacterial_outdir":  bacterial_outdir  or "NONE",
            "annotation_outdir": annotation_outdir or "NONE",
            "summary_format":    args.format,
            "backend":           config["backend"],
            "cache_location":    config["cache_location"],
        }

    @staticmethod
    def _resolve_dir(path_str: Optional[str], flag_name: str) -> Optional[str]:
        if not path_str:
            return None
        resolved = Path(path_str).resolve()
        if not resolved.exists():
            raise ValueError(f"{flag_name} path does not exist: {path_str}")
        if not resolved.is_dir():
            raise ValueError(f"{flag_name} path is not a directory: {path_str}")
        return str(resolved)

    # ------------------------------------------------------------------ #
    #  Nextflow command                                                    #
    # ------------------------------------------------------------------ #

    def _build_nextflow_command(self, params: dict, args) -> List[str]:
        cmd = ["nextflow", "run", "main.nf"]

        if args.resume:
            cmd.insert(2, "-resume")

        if params["backend"] == "conda":
            cmd.extend(["-profile", "conda"])
        elif params["backend"] == "singularity":
            cmd.extend(["-profile", "singularity"])
        else:
            raise ValueError(f"Unrecognized backend: {params['backend']!r}. Must be 'conda' or 'singularity'.")

        cmd.extend(["--workflow",          "summarize"])
        cmd.extend(["--summary_type",      params["summary_type"]])
        cmd.extend(["--outdir",            params["outdir"]])
        cmd.extend(["--summary_format",    params["summary_format"]])
        cmd.extend(["--bacterial_outdir",  params["bacterial_outdir"]])
        cmd.extend(["--annotation_outdir", params["annotation_outdir"]])

        cache = params.get("cache_location")
        if cache:
            if params["backend"] == "conda":
                cmd.extend(["--conda_cache_dir",       cache])
            else:
                cmd.extend(["--singularity_cache_dir", cache])

        return cmd

    def _execute_nextflow(self, cmd: List[str]) -> bool:
        try:
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, text=True, cwd=Path.cwd())
            if result.returncode == 0:
                print("Summary generation completed successfully.")
                return True
            else:
                print(f"Summary generation failed with exit code: {result.returncode}")
                return False
        except FileNotFoundError:
            print("Error: Nextflow not found. Please ensure Nextflow is installed and in your PATH.")
            return False
        except Exception as exc:
            print(f"Error executing Nextflow: {exc}")
            return False

    # ------------------------------------------------------------------ #
    #  Display helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _print_list():
        print("\nAvailable summary types:")
        print("-" * 60)
        for name, desc in sorted(_KNOWN_SUMMARIES.items()):
            print(f"  {name:<30} {desc}")
        print()

    @staticmethod
    def _show_plan(params: dict, cmd: List[str]):
        print("Phorager Summarize Plan")
        print("=" * 35)
        print()
        print("Configuration:")
        print(f"  Backend:           {params['backend']}")
        if params["cache_location"]:
            print(f"  Cache location:    {params['cache_location']}")
        print()
        print("Summary parameters:")
        print(f"  Type:              {params['summary_type']}")
        print(f"  Format:            {params['summary_format']}")
        print(f"  Output:            {params['outdir']}/4.Summaries/{params['summary_type']}.{params['summary_format']}")
        if params["bacterial_outdir"] != "NONE":
            print(f"  Bacterial outdir:  {params['bacterial_outdir']}")
        if params["annotation_outdir"] != "NONE":
            print(f"  Annotation outdir: {params['annotation_outdir']}")
        print()
        print("Nextflow command that would be executed:")
        print(f"  {' '.join(cmd)}")
        print()
        print("NOTE: This is a dry-run. Use without --dry-run to execute.")
