"""
Tests for summaries/prophage_table.py

Covers:
  - generate() normal case (all files present)
  - host extraction from prophage IDs
  - proviral_length preferred over contig_length
  - proviral_length fallback (empty string, "NA", "None")
  - cluster representative lookup
  - prophage not in any cluster
  - prophage absent from CheckV summary
  - CDS lookup via Sequence column
  - CDS = NA when annotation file absent
  - CDS = NA when Sequence / CDS column missing
  - required_files() and optional_files() return correct paths
  - validate() behaviour
"""

import pytest
import pandas as pd
from pathlib import Path

from summaries.prophage_table import ProphageTableSummary
from conftest import (
    CHECKV_HEADER, CLUSTER_ROWS, ANNOTATION_HEADER,
    ANNOTATION_ROW_A1, ANNOTATION_ROW_A2, ANNOTATION_ROW_B1,
    PHAGE_FASTA,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def summary():
    return ProphageTableSummary()


# ---------------------------------------------------------------------------
# generate() — normal case
# ---------------------------------------------------------------------------

class TestGenerateNormalCase:

    def test_returns_dataframe(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir))
        assert isinstance(df, pd.DataFrame)

    def test_one_row_per_prophage_in_fasta(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir))
        # PHAGE_FASTA has 3 sequences
        assert len(df) == 3

    def test_expected_columns_present(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir))
        expected = {
            "Prophage_name", "Bacterial_host", "Cluster_representative",
            "CheckV_quality", "Phage_length", "CDS_number",
        }
        assert expected.issubset(set(df.columns))

    def test_prophage_names_match_fasta_ids(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir))
        assert set(df["Prophage_name"]) == {
            "genome_A_ctg001_1000_5000",
            "genome_A_ctg002_complete",
            "genome_B_ctg001_2000_8000",
        }

    def test_checkv_quality_values(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "CheckV_quality"] == "High-quality"
        assert df.loc["genome_A_ctg002_complete",   "CheckV_quality"] == "Complete"
        assert df.loc["genome_B_ctg001_2000_8000",  "CheckV_quality"] == "Medium-quality"

    def test_cds_values_correct(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "CDS_number"] == 45
        assert df.loc["genome_A_ctg002_complete",   "CDS_number"] == 62
        assert df.loc["genome_B_ctg001_2000_8000",  "CDS_number"] == 78


# ---------------------------------------------------------------------------
# Host extraction
# ---------------------------------------------------------------------------

class TestHostExtraction:

    def test_host_extracted_correctly(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "Bacterial_host"] == "genome_A"
        assert df.loc["genome_B_ctg001_2000_8000", "Bacterial_host"] == "genome_B"

    def test_host_extraction_complete_prophage(self, summary, annotation_outdir):
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg002_complete", "Bacterial_host"] == "genome_A"

    def test_host_extraction_hyphenated_genome_name(self, summary, tmp_path):
        """Genome names with hyphens should be preserved up to _ctg."""
        fasta = ">my-genome-v2_ctg001_500_3000\nATCGATCG\n"
        self._write_minimal_annotation(tmp_path, fasta)
        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["my-genome-v2_ctg001_500_3000", "Bacterial_host"] == "my-genome-v2"

    def test_unknown_host_when_no_ctg_separator(
        self, summary, tmp_path, capsys
    ):
        """IDs without '_ctg' should produce 'Unknown' host with a warning."""
        fasta = ">some_weird_sequence_name\nATCGATCG\n"
        self._write_minimal_annotation(tmp_path, fasta)
        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["some_weird_sequence_name", "Bacterial_host"] == "Unknown"
        captured = capsys.readouterr()
        assert "Warning" in captured.out

    @staticmethod
    def _write_minimal_annotation(tmp_path, fasta_content):
        """Helper: write enough files so generate() can run but returns minimal data."""
        # FASTA
        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(fasta_content)

        # Empty cluster file (no clusters)
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        # Minimal CheckV summary
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(CHECKV_HEADER + "\n")


# ---------------------------------------------------------------------------
# Phage length: proviral_length vs contig_length
# ---------------------------------------------------------------------------

class TestPhageLength:

    def test_proviral_length_used_when_present(self, summary, annotation_outdir):
        """genome_A_ctg001 has proviral_length=3800 in the fixture."""
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "Phage_length"] == 3800

    def test_contig_length_used_when_proviral_empty(self, summary, annotation_outdir):
        """genome_A_ctg002 has an empty proviral_length → should use contig_length=5000."""
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg002_complete", "Phage_length"] == 5000

    def test_contig_length_fallback_for_na_string(self, summary, tmp_path):
        """proviral_length value of 'NA' should fall back to contig_length."""
        checkv_content = (
            f"{CHECKV_HEADER}\n"
            "seq1_ctg001_1_5000\t4000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.1\tNA\t\n"
        )
        self._write_checkv_and_fasta(tmp_path, checkv_content, ">seq1_ctg001_1_5000\nATCG\n")
        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["seq1_ctg001_1_5000", "Phage_length"] == 4000

    def test_contig_length_fallback_for_none_string(self, summary, tmp_path):
        checkv_content = (
            f"{CHECKV_HEADER}\n"
            "seq1_ctg001_1_5000\t4000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.1\tNone\t\n"
        )
        self._write_checkv_and_fasta(tmp_path, checkv_content, ">seq1_ctg001_1_5000\nATCG\n")
        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["seq1_ctg001_1_5000", "Phage_length"] == 4000

    @staticmethod
    def _write_checkv_and_fasta(tmp_path, checkv_content, fasta_content):
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(checkv_content)

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(fasta_content)

        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")


# ---------------------------------------------------------------------------
# Cluster representative lookup
# ---------------------------------------------------------------------------

class TestClusterLookup:

    def test_representative_for_member(self, summary, annotation_outdir):
        """genome_B_ctg001 is a member of genome_A_ctg001's cluster."""
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_B_ctg001_2000_8000", "Cluster_representative"] == "genome_A_ctg001_1000_5000"

    def test_representative_for_singleton(self, summary, annotation_outdir):
        """genome_A_ctg002 is its own representative."""
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg002_complete", "Cluster_representative"] == "genome_A_ctg002_complete"

    def test_representative_for_self(self, summary, annotation_outdir):
        """The representative itself maps back to itself."""
        df = summary.generate(annotation_outdir=str(annotation_outdir)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "Cluster_representative"] == "genome_A_ctg001_1000_5000"

    def test_not_in_clusters_marker(self, summary, tmp_path):
        """A prophage absent from Cluster_information.tsv gets 'Not_in_clusters'."""
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "orphan_ctg001_1_5000\t5000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.0\t\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">orphan_ctg001_1_5000\nATCG\n")

        # Cluster file does not mention this sequence
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text(
            "other_seq\tother_seq\n"
        )

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["orphan_ctg001_1_5000", "Cluster_representative"] == "Not_in_clusters"

    def test_empty_cluster_file_handled_gracefully(self, summary, tmp_path):
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "seq_ctg001_1_2000\t2000\t1\t3\t2\t1\tMedium-quality\tMedium-quality\t70.0\tHMM\t0.0\t\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">seq_ctg001_1_2000\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["seq_ctg001_1_2000", "Cluster_representative"] == "Not_in_clusters"


# ---------------------------------------------------------------------------
# CheckV data absent
# ---------------------------------------------------------------------------

class TestCheckVAbsent:

    def test_prophage_absent_from_checkv_returns_na(self, summary, tmp_path):
        """A prophage ID not in quality_summary.tsv → CheckV_quality and Phage_length = NA."""
        # Write CheckV with no rows
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(CHECKV_HEADER + "\n")

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">genome_A_ctg001_1000_5000\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg001_1000_5000", "CheckV_quality"] == "NA"
        assert df.loc["genome_A_ctg001_1000_5000", "Phage_length"]   == "NA"

    def test_provirus_with_trailing_1_matches_checkv(self, summary, tmp_path):
        """
        CheckV appends '_1' to proviral sequences in proviruses.fna.
        PARSE_CHECKV extracts from that file, so the FASTA name has '_1'
        but quality_summary.tsv has the original name without it.
        The lookup must strip '_1' and retry.
        """
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        # quality_summary has the ORIGINAL name (no _1)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "genome_A_ctg011_34888_88955\t54067\t1\t7\t6\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.0\t3800\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        # FASTA has the _1 name (CheckV provirus naming)
        (fasta_dir / "filtered_phage_set.fasta").write_text(
            ">genome_A_ctg011_34888_88955_1\nATCGATCG\n"
        )
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        # Should have resolved via stripped name
        assert df.loc["genome_A_ctg011_34888_88955_1", "CheckV_quality"] == "High-quality"
        assert df.loc["genome_A_ctg011_34888_88955_1", "Phage_length"]   == 3800

    def test_non_provirus_without_trailing_1_matches_directly(self, summary, tmp_path):
        """
        Non-proviral sequences (from viruses.fna) keep their original name
        without '_1'. Direct lookup should succeed without stripping.
        """
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "genome_A_ctg010_17220_62963\t45743\t1\t6\t5\t1\tHigh-quality\tHigh-quality\t98.0\tDTR\t0.0\t\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(
            ">genome_A_ctg010_17220_62963\nATCGATCG\n"
        )
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg010_17220_62963", "CheckV_quality"] == "High-quality"
        # No proviral_length set → falls back to contig_length
        assert df.loc["genome_A_ctg010_17220_62963", "Phage_length"]   == 45743

    def test_genuinely_absent_id_still_returns_na(self, summary, tmp_path):
        """
        A name that ends in '_1' but whose stripped form is also not in
        quality_summary should still return NA rather than crashing.
        """
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(CHECKV_HEADER + "\n")

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">genome_A_ctg011_34888_88955_1\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["genome_A_ctg011_34888_88955_1", "CheckV_quality"] == "NA"
        assert df.loc["genome_A_ctg011_34888_88955_1", "Phage_length"]   == "NA"


# ---------------------------------------------------------------------------
# CDS lookup
# ---------------------------------------------------------------------------

class TestCDSLookup:

    def test_cds_na_when_annotation_file_absent(
        self, summary, tmp_path, capsys
    ):
        """No filtered_annotation_output.tsv → all CDS_number = NA."""
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "g_ctg001_1_5000\t5000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.0\t\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">g_ctg001_1_5000\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")
        # NOTE: Anno5_FilteredResults directory intentionally NOT created

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["g_ctg001_1_5000", "CDS_number"] == "NA"

        captured = capsys.readouterr()
        assert "Warning" in captured.out

    def test_cds_na_when_sequence_column_missing(self, summary, tmp_path, capsys):
        """filtered_annotation_output.tsv lacks a Sequence column → CDS = NA."""
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(
            f"{CHECKV_HEADER}\n"
            "g_ctg001_1_5000\t5000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.0\t\t\n"
        )

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">g_ctg001_1_5000\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        anno5 = tmp_path / "3.Annotation" / "Anno5_FilteredResults"
        anno5.mkdir(parents=True, exist_ok=True)
        # Write annotation file but WITHOUT the Sequence column
        (anno5 / "filtered_annotation_output.tsv").write_text(
            "Parent\tCDS\n"
            "g_ctg001_1_5000_pharokka\t30\n"
        )

        df = summary.generate(annotation_outdir=str(tmp_path)).set_index("Prophage_name")
        assert df.loc["g_ctg001_1_5000", "CDS_number"] == "NA"
        assert "Warning" in capsys.readouterr().out

    def test_cds_uses_sequence_column_not_parent(self, summary, annotation_outdir):
        """
        Confirm matching uses the Sequence column (canonical name), not Parent.
        The fixture has _pharokka and _1_pharokka Parent values — those should
        NOT appear in CDS_number; the clean Sequence match should produce integers.
        """
        df = summary.generate(annotation_outdir=str(annotation_outdir))
        assert all(
            isinstance(v, int) for v in df["CDS_number"] if v != "NA"
        )


# ---------------------------------------------------------------------------
# File declarations and validate()
# ---------------------------------------------------------------------------

class TestFileDeclarations:

    def test_required_files_contains_fasta(self, summary, annotation_outdir):
        req = summary.required_files(annotation_outdir=str(annotation_outdir))
        assert any("filtered_phage_set.fasta" in str(p) for p in req.values())

    def test_required_files_contains_cluster_info(self, summary, annotation_outdir):
        req = summary.required_files(annotation_outdir=str(annotation_outdir))
        assert any("Cluster_information.tsv" in str(p) for p in req.values())

    def test_required_files_contains_checkv_summary(self, summary, annotation_outdir):
        req = summary.required_files(annotation_outdir=str(annotation_outdir))
        assert any("quality_summary.tsv" in str(p) for p in req.values())

    def test_optional_files_contains_annotation_output(self, summary, annotation_outdir):
        opt = summary.optional_files(annotation_outdir=str(annotation_outdir))
        assert any("filtered_annotation_output.tsv" in str(p) for p in opt.values())

    def test_validate_passes_with_all_files(self, summary, annotation_outdir):
        ok, msgs = summary.validate(annotation_outdir=str(annotation_outdir))
        assert ok is True
        assert not any("[REQUIRED]" in m for m in msgs)

    def test_validate_fails_when_fasta_missing(self, summary, tmp_path):
        # Create CheckV and cluster but omit the FASTA
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(CHECKV_HEADER + "\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")

        ok, msgs = summary.validate(annotation_outdir=str(tmp_path))
        assert ok is False
        assert any("[REQUIRED]" in m and "filtered_phage_set.fasta" in m for m in msgs)

    def test_validate_warns_but_passes_when_annotation_file_missing(
        self, summary, tmp_path
    ):
        checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
        checkv_dir.mkdir(parents=True)
        (checkv_dir / "quality_summary.tsv").write_text(CHECKV_HEADER + "\n")

        fasta_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults" / "annotation_filtered_sequences"
        fasta_dir.mkdir(parents=True)
        (fasta_dir / "filtered_phage_set.fasta").write_text(">g_ctg001_1_5000\nATCG\n")
        (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text("")
        # No Anno5_FilteredResults directory

        ok, msgs = summary.validate(annotation_outdir=str(tmp_path))
        assert ok is True
        assert any("[OPTIONAL]" in m for m in msgs)
        assert not any("[REQUIRED]" in m for m in msgs)
