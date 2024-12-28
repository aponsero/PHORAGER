process PARSE_FILTER_ANNOTATIONS {
    publishDir "${params.outdir}/3.Annotation/Anno5_FilteredResults", mode: 'copy'

    input:
    path "pharokka_results/*"  // Changed to use wildcards for multiple directories
    path "phold_results/*"     // Changed to use wildcards for multiple directories
    path "input_sequences/*"   // Changed to use wildcards for multiple directories
    val filter_mode
    val pharokka_perc
    val pharokka_total
    val phold_perc
    val phold_total

    output:
    path "filtered_annotation_output.tsv", emit: summary
    path "annotation_filtered_sequences/filtered_phage_set.fasta", emit: filtered_fasta
    path "annotation_filtered_sequences/*.fasta", emit: individual_fastas

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    import os
    import shutil
    from Bio import SeqIO

    def parse_pharokka_output():
        results = []
        header = ["Parent", "CDS", "connector", "DNA, RNA and nucleotide metabolism", 
                 "head and packaging", "integration and excision", "lysis",
                 "moron, auxiliary metabolic gene and host takeover", "other", "tail",
                 "transcription regulation", "unknown function", "tRNAs", "CRISPRs",
                 "tmRNAs", "VFDB_Virulence_Factors", "CARD_AMR_Genes"]

        for dirname in os.listdir("pharokka_results"):
            if dirname.endswith("_pharokka"):
                cds_file = os.path.join("pharokka_results", dirname, "pharokka_cds_functions.tsv")
                if os.path.isfile(cds_file):
                    counts = {col: 0 for col in header[1:]}
                    counts["Parent"] = dirname
                    
                    df = pd.read_csv(cds_file, sep='\\t')
                    for _, row in df.iterrows():
                        counts[row['Description']] = row['Count']
                    
                    # Calculate structural genes
                    total_structural = (counts.get("head and packaging", 0) + 
                                     counts.get("tail", 0) + counts.get("connector", 0))
                    percent_structural = (total_structural / counts["CDS"] * 100 
                                       if counts["CDS"] > 0 else 0)
                    
                    counts["Total Structural Genes"] = total_structural
                    counts["% Structural Genes"] = percent_structural
                    
                    results.append(counts)
        
        return pd.DataFrame(results) if results else pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    def parse_phold_output():
        results = []
        header = ["Parent", "CDS", "connector", "DNA, RNA and nucleotide metabolism",
                 "head and packaging", "integration and excision", "lysis",
                 "moron, auxiliary metabolic gene and host takeover", "other", "tail",
                 "transcription regulation", "unknown function", "VFDB_Virulence_Factors",
                 "CARD_AMR", "ACR_anti_crispr", "Defensefinder"]

        for dirname in os.listdir("phold_results"):
            if dirname.endswith("_phold"):
                func_file = os.path.join("phold_results", dirname, "phold_all_cds_functions.tsv")
                if os.path.isfile(func_file):
                    counts = {col: 0 for col in header[1:]}
                    counts["Parent"] = dirname
                    
                    df = pd.read_csv(func_file, sep='\\t')
                    for _, row in df.iterrows():
                        counts[row['Description']] = row['Count']
                    
                    # Calculate structural genes
                    total_structural = (counts.get("head and packaging", 0) + 
                                     counts.get("tail", 0) + counts.get("connector", 0))
                    percent_structural = (total_structural / counts["CDS"] * 100 
                                       if counts["CDS"] > 0 else 0)
                    
                    counts["Total Structural Genes"] = total_structural
                    counts["% Structural Genes"] = percent_structural
                    
                    results.append(counts)
        
        return pd.DataFrame(results) if results else pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    def filter_entries(df, mode, ph_perc, ph_total, pl_perc, pl_total):
        if df.empty:
            return df
            
        if mode == 'pharokka':
            return df[(df['Total Structural Genes'] >= ph_total) & 
                     (df['% Structural Genes'] >= ph_perc)]
        elif mode == 'phold':
            return df[(df['Total Structural Genes'] >= pl_total) & 
                     (df['% Structural Genes'] >= pl_perc)]
        else:  # both
            pharokka_filtered = df[(df['Total Structural Genes'] >= ph_total) & 
                                 (df['% Structural Genes'] >= ph_perc)]
            phold_filtered = df[(df['Total Structural Genes'] >= pl_total) & 
                              (df['% Structural Genes'] >= pl_perc)]
            return pd.concat([pharokka_filtered, phold_filtered]).drop_duplicates()

    # Parse outputs
    pharokka_df = parse_pharokka_output()
    phold_df = parse_phold_output()
    
    # Combine and filter
    combined_df = pd.concat([pharokka_df, phold_df]).drop_duplicates()
    filtered_df = filter_entries(combined_df, "${filter_mode}", 
                               ${pharokka_perc}, ${pharokka_total},
                               ${phold_perc}, ${phold_total})
    
    # Save filtered summary
    filtered_df.to_csv("filtered_annotation_output.tsv", sep='\\t', index=False)

    # Process sequences
    os.makedirs("annotation_filtered_sequences", exist_ok=True)
    filtered_names = [name.replace('_pharokka', '').replace('_phold', '') 
                     for name in filtered_df['Parent']]
    
    with open("annotation_filtered_sequences/filtered_phage_set.fasta", 'w') as combined:
        for seq_file in os.listdir("input_sequences"):
            if seq_file.endswith(('.fasta', '.fa', '.fna')):
                name = os.path.splitext(seq_file)[0]
                if name in filtered_names:
                    src = os.path.join("input_sequences", seq_file)
                    dst = os.path.join("annotation_filtered_sequences", seq_file)
                    shutil.copy(src, dst)
                    
                    # Append to combined file
                    for record in SeqIO.parse(src, "fasta"):
                        SeqIO.write(record, combined, "fasta")
    """
}
