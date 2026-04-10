"""
Bacterial genome summary table.

Reads:
  REQUIRED
    {bacterial_outdir}/1.Genome_preprocessing/Bact1_CheckM2/quality_report.tsv
  OPTIONAL
    {annotation_outdir}/3.Annotation/Anno6_Clustering/filtered_phage_set.fasta

Output columns:
  Genome_name            - genome basename (from CheckM2 'Name')
  Completeness           - CheckM2 completeness (%)
  Contamination          - CheckM2 contamination (%)
  Genome_size            - total assembly size (bp)
  GC_content             - GC fraction
  Contig_N50             - contig N50 (bp)
  Coding_sequences       - total predicted CDS count
  Prophage_count         - prophages in filtered_phage_set.fasta attributed to this genome
                           (0 if FASTA is absent or no prophages found for this genome)
"""

from pathlib import Path

import pandas as pd
from Bio import SeqIO

from summaries.base import BaseSummary
from summaries.registry import registry

# CheckM2 column names
_CHECKM2_COLS = {
    "name":   "Name",
    "comp":   "Completeness",
    "cont":   "Contamination",
    "size":   "Genome_Size",
    "gc":     "GC_Content",
    "n50":    "Contig_N50",
    "cds":    "Total_Coding_Sequences",
}

# Path fragments relative to their respective outdirs
_CHECKM2_REL   = "1.Genome_preprocessing/Bact1_CheckM2/quality_report.tsv"
_PHAGE_FASTA_REL = "3.Annotation/Anno5_FilteredResults/annotation_filtered_sequences/filtered_phage_set.fasta"


@registry.register
class BacterialGenomeSummary(BaseSummary):

    name        = "bacterial_genome"
    description = "Per-genome QC metrics (CheckM2) with prophage counts"

    # ------------------------------------------------------------------ #
    #  File declarations                                                   #
    # ------------------------------------------------------------------ #

    def required_files(self, bacterial_outdir=None, **_):
        return {
            "CheckM2 quality report":
                Path(bacterial_outdir) / _CHECKM2_REL,
        }

    def optional_files(self, annotation_outdir=None, **_):
        # The FASTA is optional because:
        #   - annotation may not have been run yet
        #   - no prophages may have passed all filters (empty but valid FASTA)
        # In either case prophage counts default to 0 with a printed warning.
        if annotation_outdir is None:
            return {}
        return {
            "Filtered phage FASTA":
                Path(annotation_outdir) / _PHAGE_FASTA_REL,
        }

    # ------------------------------------------------------------------ #
    #  Core logic                                                          #
    # ------------------------------------------------------------------ #

    def generate(self, bacterial_outdir=None, annotation_outdir=None, **_):
        """Return a DataFrame with one row per genome from the CheckM2 report."""

        checkm2_path = Path(bacterial_outdir) / _CHECKM2_REL

        # -- CheckM2 report --
        checkm2_df = pd.read_csv(checkm2_path, sep="\t", keep_default_na=False)
        self._validate_checkm2_columns(checkm2_df, checkm2_path)

        # -- Prophage counts from FASTA --
        prophage_counts = {}
        if annotation_outdir is not None:
            fasta_path = Path(annotation_outdir) / _PHAGE_FASTA_REL
            prophage_counts = self._count_prophages_per_genome(fasta_path)

        # -- Build output rows --
        rows = []
        for _, row in checkm2_df.iterrows():
            genome_name = row[_CHECKM2_COLS["name"]]
            rows.append({
                "Genome_name":       genome_name,
                "Completeness":      row[_CHECKM2_COLS["comp"]],
                "Contamination":     row[_CHECKM2_COLS["cont"]],
                "Genome_size":       row[_CHECKM2_COLS["size"]],
                "GC_content":        row[_CHECKM2_COLS["gc"]],
                "Contig_N50":        row[_CHECKM2_COLS["n50"]],
                "Coding_sequences":  row[_CHECKM2_COLS["cds"]],
                "Prophage_count":    prophage_counts.get(genome_name, 0),
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_checkm2_columns(df, path):
        """Raise a clear error if expected columns are missing."""
        expected = set(_CHECKM2_COLS.values())
        missing  = expected - set(df.columns)
        if missing:
            raise ValueError(
                f"CheckM2 quality report at '{path}' is missing expected columns: "
                f"{sorted(missing)}. "
                f"Found columns: {list(df.columns)}"
            )

    @staticmethod
    def _count_prophages_per_genome(fasta_path: Path) -> dict:
        """
        Parse filtered_phage_set.fasta and return {genome_basename: count}.

        Prophage sequence IDs follow the naming convention established by
        RENAME_CONTIGS + COMPARE_PROPHAGES:
            {genome_basename}_ctg{NNN}_{start}_{end}
            {genome_basename}_ctg{NNN}_complete

        The genome basename is therefore everything before the first '_ctg'.
        """
        counts = {}

        if not fasta_path.exists():
            print(
                f"  Warning: Filtered phage FASTA not found: {fasta_path}\n"
                f"  Prophage counts will be 0 for all genomes."
            )
            return counts

        for record in SeqIO.parse(str(fasta_path), "fasta"):
            seq_id = record.id
            if "_ctg" in seq_id:
                host = seq_id.split("_ctg")[0]
            else:
                # Unexpected naming; skip and warn rather than crash
                print(f"  Warning: Unexpected prophage ID format (no '_ctg'): '{seq_id}' — skipping.")
                continue
            counts[host] = counts.get(host, 0) + 1

        return counts
