"""
Tests for summaries/bacterial_genome.py

Covers:
  - generate() normal case
  - prophage counting from FASTA (various ID formats)
  - prophage count = 0 when annotation outdir not provided
  - prophage count = 0 when FASTA is absent
  - unexpected FASTA header format (no _ctg) handled gracefully
  - CheckM2 missing column raises ValueError
  - required_files() and optional_files() return correct paths
  - validate() distinguishes required vs optional missing files
"""

import pytest
import pandas as pd
from pathlib import Path

from summaries.bacterial_genome import BacterialGenomeSummary
from conftest import (
    CHECKM2_HEADER, CHECKM2_ROW_A, CHECKM2_ROW_B, PHAGE_FASTA,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def summary():
    return BacterialGenomeSummary()


# ---------------------------------------------------------------------------
# generate() — normal case
# ---------------------------------------------------------------------------

class TestGenerateNormalCase:

    def test_returns_dataframe(self, summary, bacterial_outdir, annotation_outdir):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        )
        assert isinstance(df, pd.DataFrame)

    def test_one_row_per_genome(self, summary, bacterial_outdir, annotation_outdir):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        )
        assert len(df) == 2

    def test_expected_columns_present(self, summary, bacterial_outdir, annotation_outdir):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        )
        expected = {
            "Genome_name", "Completeness", "Contamination", "Genome_size",
            "GC_content", "Contig_N50", "Coding_sequences", "Prophage_count",
        }
        assert expected.issubset(set(df.columns))

    def test_checkm2_values_correct(self, summary, bacterial_outdir, annotation_outdir):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        ).set_index("Genome_name")

        assert df.loc["genome_A", "Completeness"]       == 100.0
        assert df.loc["genome_A", "Contamination"]      == 0.23
        assert df.loc["genome_A", "Genome_size"]        == 4802857
        assert df.loc["genome_A", "GC_content"]         == 0.56
        assert df.loc["genome_A", "Contig_N50"]         == 1139944
        assert df.loc["genome_A", "Coding_sequences"]   == 4448

        assert df.loc["genome_B", "Completeness"]       == 82.67
        assert df.loc["genome_B", "Coding_sequences"]   == 4863

    def test_prophage_counts_correct(self, summary, bacterial_outdir, annotation_outdir):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        ).set_index("Genome_name")

        # PHAGE_FASTA has 2 sequences for genome_A and 1 for genome_B
        assert df.loc["genome_A", "Prophage_count"] == 2
        assert df.loc["genome_B", "Prophage_count"] == 1


# ---------------------------------------------------------------------------
# generate() — prophage count edge cases
# ---------------------------------------------------------------------------

class TestProphageCountEdgeCases:

    def test_count_zero_when_annotation_outdir_is_none(
        self, summary, bacterial_outdir
    ):
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=None,
        ).set_index("Genome_name")
        assert df.loc["genome_A", "Prophage_count"] == 0
        assert df.loc["genome_B", "Prophage_count"] == 0

    def test_count_zero_when_fasta_absent(self, summary, bacterial_outdir, tmp_path):
        # annotation_outdir exists but the FASTA does not
        anno_dir = tmp_path / "annotation_no_fasta"
        anno_dir.mkdir()
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(anno_dir),
        ).set_index("Genome_name")
        assert df.loc["genome_A", "Prophage_count"] == 0

    def test_count_zero_when_fasta_is_empty(self, summary, bacterial_outdir, tmp_path):
        anno_dir = tmp_path / "anno_empty_fasta"
        fasta_dir = anno_dir / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text("")

        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(anno_dir),
        ).set_index("Genome_name")
        assert df.loc["genome_A", "Prophage_count"] == 0

    def test_multiple_prophages_same_genome(self, summary, bacterial_outdir, tmp_path):
        """Five prophages from genome_A and none from genome_B."""
        fasta = "\n".join(
            f">genome_A_ctg{i:03d}_1000_2000\nATCG" for i in range(1, 6)
        )
        anno_dir = tmp_path / "anno_multi"
        fasta_dir = anno_dir / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(fasta)

        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(anno_dir),
        ).set_index("Genome_name")

        assert df.loc["genome_A", "Prophage_count"] == 5
        assert df.loc["genome_B", "Prophage_count"] == 0

    def test_complete_prophage_id_counted(self, summary, bacterial_outdir, tmp_path):
        """IDs ending in _complete should still be counted."""
        fasta = ">genome_A_ctg001_complete\nATCGATCG\n"
        anno_dir = tmp_path / "anno_complete"
        fasta_dir = anno_dir / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(fasta)

        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(anno_dir),
        ).set_index("Genome_name")

        assert df.loc["genome_A", "Prophage_count"] == 1

    def test_unexpected_id_format_does_not_crash(
        self, summary, bacterial_outdir, tmp_path, capsys
    ):
        """Sequences without '_ctg' in the ID should be skipped with a warning."""
        fasta = ">some_weird_id_without_the_separator\nATCG\n"
        anno_dir = tmp_path / "anno_weird"
        fasta_dir = anno_dir / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(fasta)

        # Should not raise
        df = summary.generate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(anno_dir),
        )
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert df["Prophage_count"].sum() == 0


# ---------------------------------------------------------------------------
# generate() — CheckM2 column validation
# ---------------------------------------------------------------------------

class TestCheckm2ColumnValidation:

    def test_missing_column_raises_value_error(self, summary, tmp_path):
        # Write a CheckM2 report that is missing Total_Coding_Sequences
        bad_header = "Name\tCompleteness\tContamination\tGenome_Size\tGC_Content\tContig_N50"
        bad_row    = "genome_A\t100.0\t0.0\t4000000\t0.5\t50000"
        checkm2_dir = tmp_path / "1.Genome_preprocessing" / "Bact1_CheckM2"
        checkm2_dir.mkdir(parents=True)
        (checkm2_dir / "quality_report.tsv").write_text(f"{bad_header}\n{bad_row}")

        with pytest.raises(ValueError, match="Total_Coding_Sequences"):
            summary.generate(bacterial_outdir=str(tmp_path), annotation_outdir=None)


# ---------------------------------------------------------------------------
# required_files() / optional_files() / validate()
# ---------------------------------------------------------------------------

class TestFileDeclarations:

    def test_required_files_contains_checkm2_report(self, summary, bacterial_outdir):
        req = summary.required_files(bacterial_outdir=str(bacterial_outdir))
        paths = list(req.values())
        assert any("quality_report.tsv" in str(p) for p in paths)

    def test_optional_files_contains_fasta_when_annotation_outdir_given(
        self, summary, annotation_outdir
    ):
        opt = summary.optional_files(annotation_outdir=str(annotation_outdir))
        assert len(opt) > 0
        assert any("filtered_phage_set.fasta" in str(p) for p in opt.values())

    def test_optional_files_empty_when_annotation_outdir_is_none(self, summary):
        assert summary.optional_files(annotation_outdir=None) == {}


class TestValidate:

    def test_validate_passes_when_all_required_files_present(
        self, summary, bacterial_outdir, annotation_outdir
    ):
        ok, msgs = summary.validate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(annotation_outdir),
        )
        required_errors = [m for m in msgs if "[REQUIRED]" in m]
        assert ok is True
        assert required_errors == []

    def test_validate_fails_when_required_file_missing(self, summary, tmp_path):
        # Empty bacterial outdir — CheckM2 report absent
        ok, msgs = summary.validate(
            bacterial_outdir=str(tmp_path),
            annotation_outdir=None,
        )
        assert ok is False
        assert any("[REQUIRED]" in m for m in msgs)

    def test_validate_warns_but_passes_when_optional_file_missing(
        self, summary, bacterial_outdir, tmp_path
    ):
        # annotation_outdir exists but FASTA is not there
        empty_anno = tmp_path / "empty_anno"
        empty_anno.mkdir()

        ok, msgs = summary.validate(
            bacterial_outdir=str(bacterial_outdir),
            annotation_outdir=str(empty_anno),
        )
        assert ok is True
        assert any("[OPTIONAL]" in m for m in msgs)
        assert not any("[REQUIRED]" in m for m in msgs)

    def test_validate_reports_exact_missing_path(self, summary, tmp_path):
        ok, msgs = summary.validate(
            bacterial_outdir=str(tmp_path),
            annotation_outdir=None,
        )
        assert ok is False
        # The message should contain the actual expected file path
        combined = " ".join(msgs)
        assert "quality_report.tsv" in combined
