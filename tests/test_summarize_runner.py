"""
Tests for lib/summarize_runner.py

This script is what the SUMMARIZE Nextflow process actually calls inside
the container/conda environment. These tests replace the generation-logic
tests that previously lived in test_summarize_command.py.

Covers:
  - main() happy path: TSV and CSV output written correctly
  - main() with unknown --type exits non-zero
  - main() with missing required file exits non-zero
  - main() with optional file absent still succeeds (warning only)
  - output file contains correct rows and columns
  - --bacterial-outdir and --annotation-outdir independently
"""

import sys
import subprocess
from pathlib import Path

import pandas as pd
import pytest

# summarize_runner.py lives in lib/, which is this file's grandparent
RUNNER = Path(__file__).parent.parent / "lib" / "summarize_runner.py"


def _run(args: list, expect_success: bool = True):
    """Call summarize_runner.py as a subprocess and return CompletedProcess."""
    result = subprocess.run(
        [sys.executable, str(RUNNER)] + args,
        capture_output=True,
        text=True,
    )
    if expect_success:
        assert result.returncode == 0, (
            f"Runner exited {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


# ---------------------------------------------------------------------------
# bacterial_genome summary via runner
# ---------------------------------------------------------------------------

class TestRunnerBacterialGenome:

    def test_tsv_written(self, shared_outdir, tmp_path):
        out = tmp_path / "bacterial.tsv"
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir",  str(shared_outdir),
            "--annotation-outdir", str(shared_outdir),
            "--output", str(out),
            "--format", "tsv",
        ])
        assert out.exists()

    def test_tsv_has_correct_columns(self, shared_outdir, tmp_path):
        out = tmp_path / "bacterial.tsv"
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir",  str(shared_outdir),
            "--annotation-outdir", str(shared_outdir),
            "--output", str(out),
        ])
        df = pd.read_csv(out, sep="\t")
        expected = {
            "Genome_name", "Completeness", "Contamination", "Genome_size",
            "GC_content", "Contig_N50", "Coding_sequences", "Prophage_count",
        }
        assert expected.issubset(set(df.columns))

    def test_tsv_has_correct_row_count(self, shared_outdir, tmp_path):
        out = tmp_path / "bacterial.tsv"
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir",  str(shared_outdir),
            "--annotation-outdir", str(shared_outdir),
            "--output", str(out),
        ])
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 2  # shared_outdir fixture has genome_A and genome_B

    def test_csv_output(self, shared_outdir, tmp_path):
        out = tmp_path / "bacterial.csv"
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir",  str(shared_outdir),
            "--annotation-outdir", str(shared_outdir),
            "--output", str(out),
            "--format", "csv",
        ])
        df = pd.read_csv(out)
        assert "Genome_name" in df.columns

    def test_without_annotation_outdir(self, bacterial_outdir, tmp_path):
        """bacterial_genome works with only --bacterial-outdir (prophage count = 0)."""
        out = tmp_path / "bacterial.tsv"
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir", str(bacterial_outdir),
            "--output", str(out),
        ])
        df = pd.read_csv(out, sep="\t")
        assert (df["Prophage_count"] == 0).all()


# ---------------------------------------------------------------------------
# prophage_table summary via runner
# ---------------------------------------------------------------------------

class TestRunnerProphageTable:

    def test_tsv_written(self, annotation_outdir, tmp_path):
        out = tmp_path / "prophage.tsv"
        _run([
            "--type", "prophage_table",
            "--annotation-outdir", str(annotation_outdir),
            "--output", str(out),
        ])
        assert out.exists()

    def test_tsv_has_correct_columns(self, annotation_outdir, tmp_path):
        out = tmp_path / "prophage.tsv"
        _run([
            "--type", "prophage_table",
            "--annotation-outdir", str(annotation_outdir),
            "--output", str(out),
        ])
        df = pd.read_csv(out, sep="\t")
        expected = {
            "Prophage_name", "Bacterial_host", "Cluster_representative",
            "CheckV_quality", "Phage_length", "CDS_number",
        }
        assert expected.issubset(set(df.columns))

    def test_tsv_has_correct_row_count(self, annotation_outdir, tmp_path):
        out = tmp_path / "prophage.tsv"
        _run([
            "--type", "prophage_table",
            "--annotation-outdir", str(annotation_outdir),
            "--output", str(out),
        ])
        df = pd.read_csv(out, sep="\t")
        assert len(df) == 3  # annotation_outdir fixture has 3 prophage sequences

    def test_optional_annotation_absent_still_succeeds(
        self, annotation_outdir, tmp_path
    ):
        """Remove the optional annotation file — runner should succeed with NA CDS."""
        (annotation_outdir / "3.Annotation" / "Anno5_FilteredResults"
         / "filtered_annotation_output.tsv").unlink()

        out = tmp_path / "prophage.tsv"
        result = _run([
            "--type", "prophage_table",
            "--annotation-outdir", str(annotation_outdir),
            "--output", str(out),
        ], expect_success=True)

        assert "Warning" in result.stdout
        df = pd.read_csv(out, sep="\t", keep_default_na=False)
        assert (df["CDS_number"] == "NA").all()


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestRunnerErrors:

    def test_unknown_type_exits_nonzero(self, shared_outdir, tmp_path):
        result = _run([
            "--type", "nonexistent_summary",
            "--bacterial-outdir", str(shared_outdir),
            "--output", str(tmp_path / "out.tsv"),
        ], expect_success=False)
        assert result.returncode != 0
        assert "Unknown" in result.stdout or "Unknown" in result.stderr

    def test_missing_required_file_exits_nonzero(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = _run([
            "--type", "prophage_table",
            "--annotation-outdir", str(empty),
            "--output", str(tmp_path / "out.tsv"),
        ], expect_success=False)
        assert result.returncode != 0

    def test_output_parent_directory_created(self, shared_outdir, tmp_path):
        nested = tmp_path / "deep" / "nested" / "out.tsv"
        assert not nested.parent.exists()
        _run([
            "--type", "bacterial_genome",
            "--bacterial-outdir",  str(shared_outdir),
            "--annotation-outdir", str(shared_outdir),
            "--output", str(nested),
        ])
        assert nested.exists()
