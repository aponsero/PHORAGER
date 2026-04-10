"""
Prophage table summary.

Reads:
  REQUIRED
    {annotation_outdir}/3.Annotation/Anno6_Clustering/filtered_phage_set.fasta
    {annotation_outdir}/3.Annotation/Cluster_information.tsv
    {annotation_outdir}/3.Annotation/Anno1_CheckV/checkv_output/quality_summary.tsv
  OPTIONAL
    {annotation_outdir}/3.Annotation/Anno5_FilteredResults/filtered_annotation_output.tsv
    (absent when --skip_detailed_annotation was used)

Output columns:
  Prophage_name          - sequence ID from filtered_phage_set.fasta
  Bacterial_host         - genome basename extracted from the prophage name
                           (everything before the first '_ctg')
  Cluster_representative - representative sequence for this prophage's cluster
                           (from Cluster_information.tsv col 0)
  CheckV_quality         - quality tier from CheckV quality_summary.tsv
  Phage_length           - proviral_length when available, else contig_length
  CDS_number             - CDS count from filtered_annotation_output.tsv;
                           NA if annotation was skipped
"""

from pathlib import Path

import pandas as pd
from Bio import SeqIO

from summaries.base import BaseSummary
from summaries.registry import registry

# Path fragments relative to annotation_outdir
_FASTA_REL       = "3.Annotation/Anno5_FilteredResults/annotation_filtered_sequences/filtered_phage_set.fasta"
_CLUSTER_REL     = "3.Annotation/Cluster_information.tsv"
_CHECKV_REL      = "3.Annotation/Anno1_CheckV/checkv_output/quality_summary.tsv"
_ANNOTATION_REL  = "3.Annotation/Anno5_FilteredResults/filtered_annotation_output.tsv"


@registry.register
class ProphageTableSummary(BaseSummary):

    name        = "prophage_table"
    description = "Per-prophage table: host, cluster, CheckV quality, length, CDS count"

    # ------------------------------------------------------------------ #
    #  File declarations                                                   #
    # ------------------------------------------------------------------ #

    def required_files(self, annotation_outdir=None, **_):
        a = Path(annotation_outdir)
        return {
            "Filtered phage FASTA":   a / _FASTA_REL,
            "Cluster information":    a / _CLUSTER_REL,
            "CheckV quality summary": a / _CHECKV_REL,
        }

    def optional_files(self, annotation_outdir=None, **_):
        return {
            "Filtered annotation output": Path(annotation_outdir) / _ANNOTATION_REL,
        }

    # ------------------------------------------------------------------ #
    #  Core logic                                                          #
    # ------------------------------------------------------------------ #

    def generate(self, annotation_outdir=None, **_):
        """Return a DataFrame with one row per prophage in filtered_phage_set.fasta."""
        a = Path(annotation_outdir)

        fasta_path      = a / _FASTA_REL
        cluster_path    = a / _CLUSTER_REL
        checkv_path     = a / _CHECKV_REL
        annotation_path = a / _ANNOTATION_REL

        # -- Load supporting look-up tables --
        cluster_map  = self._load_cluster_map(cluster_path)
        checkv_index = self._load_checkv_index(checkv_path)
        cds_map      = self._load_cds_map(annotation_path)

        # -- Build output rows --
        rows = []
        for record in SeqIO.parse(str(fasta_path), "fasta"):
            prophage_name = record.id

            host = self._extract_host(prophage_name)
            rep  = cluster_map.get(prophage_name, "Not_in_clusters")

            checkv_quality, phage_length = self._get_checkv_data(
                prophage_name, checkv_index
            )

            cds_number = cds_map.get(prophage_name, "NA")

            rows.append({
                "Prophage_name":        prophage_name,
                "Bacterial_host":       host,
                "Cluster_representative": rep,
                "CheckV_quality":       checkv_quality,
                "Phage_length":         phage_length,
                "CDS_number":           cds_number,
            })

        return pd.DataFrame(rows)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_host(prophage_name: str) -> str:
        """
        Extract the genome basename from a prophage sequence ID.

        Prophage IDs follow the convention produced by RENAME_CONTIGS and
        COMPARE_PROPHAGES:
            {genome_basename}_ctg{NNN}_{start}_{end}
            {genome_basename}_ctg{NNN}_complete

        The genome basename is everything before the first '_ctg'.
        """
        if "_ctg" in prophage_name:
            return prophage_name.split("_ctg")[0]
        print(f"  Warning: Cannot extract host from ID (no '_ctg'): '{prophage_name}'")
        return "Unknown"

    @staticmethod
    def _load_cluster_map(path: Path) -> dict:
        """
        Build {member_name: representative_name} from Cluster_information.tsv.

        The file is headerless (produced by aniclust.py):
          col 0 — representative sequence name
          col 1 — comma-separated string of all cluster members
                  (the representative is included in the member list)

        A prophage that IS the representative will therefore also appear in
        col 1 and map correctly to itself.
        """
        cluster_map = {}
        if not path.exists():
            print(f"  Warning: Cluster information file not found: {path}")
            return cluster_map

        if path.stat().st_size == 0:
            return cluster_map

        df = pd.read_csv(path, sep="\t", header=None, keep_default_na=False)

        for _, row in df.iterrows():
            rep     = str(row.iloc[0]).strip()
            members = [m.strip() for m in str(row.iloc[1]).split(",")]
            for member in members:
                if member:
                    cluster_map[member] = rep

        return cluster_map

    @staticmethod
    def _load_checkv_index(path: Path) -> pd.DataFrame:
        """
        Load quality_summary.tsv and return a DataFrame indexed by contig_id.

        Adds a 'phage_length' column that prefers proviral_length (trimmed
        CheckV estimate) over contig_length (raw input length). This matches
        the downstream pipeline behaviour, which uses CheckV's trimmed FASTA
        output.
        """
        df = pd.read_csv(path, sep="\t", keep_default_na=False)

        def _best_length(row):
            prov = row.get("proviral_length", "")
            # keep_default_na=False means empty cells are "" not NaN
            if prov not in ("", "NA", "None"):
                try:
                    return int(float(prov))
                except (ValueError, TypeError):
                    pass
            return int(row["contig_length"])

        # df.apply() on an empty DataFrame returns a DataFrame instead of
        # a Series in newer pandas versions, causing a ValueError on assignment.
        # Guard explicitly — an empty CheckV summary is a valid pipeline state.
        if df.empty:
            df["phage_length"] = pd.Series(dtype=object)
        else:
            df["phage_length"] = df.apply(_best_length, axis=1)
        return df.set_index("contig_id")

    @staticmethod
    def _get_checkv_data(prophage_name: str, checkv_index: pd.DataFrame) -> tuple:
        """
        Return (checkv_quality, phage_length) for a prophage, or ('NA', 'NA').

        CheckV appends '_1' to proviral sequences in proviruses.fna (its trimmed
        output). PARSE_CHECKV extracts from that file, so filtered_prophages.fasta
        carries the '_1' name. But quality_summary.tsv records the original input
        name without '_1'. Try the exact name first, then strip a trailing '_1'
        and retry before giving up.
        """
        if prophage_name in checkv_index.index:
            row = checkv_index.loc[prophage_name]
            return str(row["checkv_quality"]), row["phage_length"]

        # Provirus case: strip CheckV's trailing '_1' and retry
        if prophage_name.endswith("_1"):
            base_name = prophage_name[:-2]
            if base_name in checkv_index.index:
                row = checkv_index.loc[base_name]
                return str(row["checkv_quality"]), row["phage_length"]

        print(f"  Warning: '{prophage_name}' not found in CheckV quality summary.")
        return "NA", "NA"

    @staticmethod
    def _load_cds_map(path: Path) -> dict:
        """
        Build {sequence_name: cds_count} from filtered_annotation_output.tsv.

        The file contains a 'Sequence' column which is the canonical prophage
        name (Parent with tool suffix stripped — already done by the pipeline
        at parse time). This column is the correct join key for matching
        against FASTA sequence IDs, so no regex stripping is needed here.
        """
        cds_map = {}
        if not path.exists():
            print(
                f"  Warning: Filtered annotation output not found: {path}\n"
                f"  CDS_number will be NA for all prophages.\n"
                f"  (Expected if --skip_detailed_annotation was used.)"
            )
            return cds_map

        df = pd.read_csv(path, sep="\t", keep_default_na=False)

        if "Sequence" not in df.columns:
            print(
                f"  Warning: 'Sequence' column not found in {path.name}.\n"
                f"  CDS_number will be NA for all prophages."
            )
            return cds_map

        if "CDS" not in df.columns:
            print(
                f"  Warning: 'CDS' column not found in {path.name}.\n"
                f"  CDS_number will be NA for all prophages."
            )
            return cds_map

        for _, row in df.iterrows():
            seq_name = str(row["Sequence"]).strip()
            try:
                cds_map[seq_name] = int(row["CDS"])
            except (ValueError, TypeError):
                print(f"  Warning: Non-integer CDS value for '{seq_name}': {row['CDS']}")

        return cds_map
