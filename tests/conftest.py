"""
Shared test configuration and fixtures for the Phorager summarize toolkit.

Sets up sys.path so that all test files can import from lib/ without
needing the phorager CLI entry point.
"""

import sys
from pathlib import Path
import pytest

# Mirror the path setup from the phorager CLI entry point
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


# ---------------------------------------------------------------------------
# Minimal valid file content constants
# ---------------------------------------------------------------------------

CHECKM2_HEADER = (
    "Name\tCompleteness\tContamination\tCompleteness_Model_Used\t"
    "Translation_Table_Used\tCoding_Density\tContig_N50\t"
    "Average_Gene_Length\tGenome_Size\tGC_Content\t"
    "Total_Coding_Sequences\tAdditional_Notes"
)

CHECKM2_ROW_A = "genome_A\t100.0\t0.23\tNeural Network\t11\t0.891\t1139944\t321.4\t4802857\t0.56\t4448\tNone"
CHECKM2_ROW_B = "genome_B\t82.67\t1.39\tNeural Network\t11\t0.888\t7844\t263.6\t4319616\t0.55\t4863\tNone"

CHECKV_HEADER = (
    "contig_id\tcontig_length\tgenome_copies\tgene_count\tviral_genes\t"
    "host_genes\tcheckv_quality\tmiuvig_quality\tcompleteness\t"
    "completeness_method\tcontamination\tproviral_length\twarnings"
)
# proviral_length set for first entry, empty for others
CHECKV_ROW_A1 = "genome_A_ctg001_1000_5000\t4000\t1\t5\t4\t1\tHigh-quality\tHigh-quality\t95.0\tDTR\t0.1\t3800\t"
CHECKV_ROW_A2 = "genome_A_ctg002_complete\t5000\t1\t7\t6\t1\tComplete\tComplete\t100.0\tDTR\t0.0\t\t"
CHECKV_ROW_B1 = "genome_B_ctg001_2000_8000\t6000\t1\t8\t7\t1\tMedium-quality\tMedium-quality\t70.0\tHMM\t0.5\t\t"

# Cluster_information.tsv is headerless: col0=rep, col1=comma-sep members
CLUSTER_ROWS = (
    "genome_A_ctg001_1000_5000\tgenome_A_ctg001_1000_5000,genome_B_ctg001_2000_8000\n"
    "genome_A_ctg002_complete\tgenome_A_ctg002_complete\n"
)

# Parent uses _pharokka / _1_pharokka suffixes; Sequence is the clean name
ANNOTATION_HEADER = "Parent\tSequence\tCDS\tconnector\thead and packaging\ttail\tTotal Structural Genes\t% Structural Genes"
ANNOTATION_ROW_A1 = "genome_A_ctg001_1000_5000_pharokka\tgenome_A_ctg001_1000_5000\t45\t2\t5\t4\t11\t24.4"
ANNOTATION_ROW_A2 = "genome_A_ctg002_complete_1_pharokka\tgenome_A_ctg002_complete\t62\t3\t8\t6\t17\t27.4"
ANNOTATION_ROW_B1 = "genome_B_ctg001_2000_8000_pharokka\tgenome_B_ctg001_2000_8000\t78\t4\t9\t7\t20\t25.6"

PHAGE_FASTA = (
    ">genome_A_ctg001_1000_5000\nATCGATCGATCG\n"
    ">genome_A_ctg002_complete\nGCTAGCTAGCTA\n"
    ">genome_B_ctg001_2000_8000\nTTAACCGGTTAA\n"
)


# ---------------------------------------------------------------------------
# Fixtures: build the expected output directory tree in tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture
def bacterial_outdir(tmp_path):
    """Create a minimal bacterial workflow output tree."""
    checkm2_dir = tmp_path / "1.Genome_preprocessing" / "Bact1_CheckM2"
    checkm2_dir.mkdir(parents=True)
    (checkm2_dir / "quality_report.tsv").write_text(
        "\n".join([CHECKM2_HEADER, CHECKM2_ROW_A, CHECKM2_ROW_B])
    )
    return tmp_path


@pytest.fixture
def annotation_outdir(tmp_path):
    """Create a minimal annotation workflow output tree with all files."""
    base = tmp_path

    # Anno1_CheckV
    checkv_dir = base / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
    checkv_dir.mkdir(parents=True)
    (checkv_dir / "quality_summary.tsv").write_text(
        "\n".join([CHECKV_HEADER, CHECKV_ROW_A1, CHECKV_ROW_A2, CHECKV_ROW_B1])
    )

    # Anno5_FilteredResults
    anno5_dir = base / "3.Annotation" / "Anno5_FilteredResults"
    fasta_dir = anno5_dir / "annotation_filtered_sequences"
    fasta_dir.mkdir(parents=True)
    (anno5_dir / "filtered_annotation_output.tsv").write_text(
        "\n".join([ANNOTATION_HEADER, ANNOTATION_ROW_A1, ANNOTATION_ROW_A2, ANNOTATION_ROW_B1])
    )
    (fasta_dir / "filtered_phage_set.fasta").write_text(PHAGE_FASTA)

    # Anno6_Clustering
    anno6_dir = base / "3.Annotation" / "Anno6_Clustering"
    anno6_dir.mkdir(parents=True)

    # Cluster_information.tsv
    (base / "3.Annotation" / "Cluster_information.tsv").write_text(CLUSTER_ROWS)

    return base


@pytest.fixture
def shared_outdir(tmp_path):
    """
    Single directory that contains BOTH bacterial and annotation outputs —
    simulates the common case where all workflows share --outdir.
    """
    # Bacterial
    checkm2_dir = tmp_path / "1.Genome_preprocessing" / "Bact1_CheckM2"
    checkm2_dir.mkdir(parents=True)
    (checkm2_dir / "quality_report.tsv").write_text(
        "\n".join([CHECKM2_HEADER, CHECKM2_ROW_A, CHECKM2_ROW_B])
    )

    # Annotation
    checkv_dir = tmp_path / "3.Annotation" / "Anno1_CheckV" / "checkv_output"
    checkv_dir.mkdir(parents=True)
    (checkv_dir / "quality_summary.tsv").write_text(
        "\n".join([CHECKV_HEADER, CHECKV_ROW_A1, CHECKV_ROW_A2, CHECKV_ROW_B1])
    )

    anno5_dir = tmp_path / "3.Annotation" / "Anno5_FilteredResults"
    fasta_dir = anno5_dir / "annotation_filtered_sequences"
    fasta_dir.mkdir(parents=True)
    (anno5_dir / "filtered_annotation_output.tsv").write_text(
        "\n".join([ANNOTATION_HEADER, ANNOTATION_ROW_A1, ANNOTATION_ROW_A2, ANNOTATION_ROW_B1])
    )
    (fasta_dir / "filtered_phage_set.fasta").write_text(PHAGE_FASTA)

    anno6_dir = tmp_path / "3.Annotation" / "Anno6_Clustering"
    anno6_dir.mkdir(parents=True)

    (tmp_path / "3.Annotation" / "Cluster_information.tsv").write_text(CLUSTER_ROWS)

    return tmp_path
