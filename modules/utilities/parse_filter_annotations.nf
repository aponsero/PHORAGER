process PARSE_FILTER_ANNOTATIONS {
    tag "Parsing and filtering annotation results"
    publishDir "${params.outdir}/3.Annotation/Anno5_FilteredResults", mode: 'copy'

    input:
    path "pharokka_results/*"  // Multiple pharokka directories
    path "phold_results/*"     // Multiple phold directories
    path "input_sequences/*"   // Multiple input sequence files
    val filter_mode
    val pharokka_perc
    val pharokka_total
    val phold_perc
    val phold_total

    output:
    path "filtered_annotation_output.tsv", emit: summary
    path "annotation_filtered_sequences/filtered_phage_set.fasta", emit: filtered_fasta
    path "annotation_filtered_sequences/*.fasta", emit: individual_fastas
    path "annotation_count.txt", emit: count

    script:
    // This process uses the parsing_env (Python + pandas + BioPython)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for parsing_env"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Parse Filter Annotations via Singularity container..."
        echo "Filter mode: ${filter_mode}"
        echo "Pharokka thresholds: ${pharokka_perc}% / ${pharokka_total} genes"
        echo "PHOLD thresholds: ${phold_perc}% / ${phold_total} genes"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling parsing environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing environment container already exists, using cached version."
        fi
        
        # Create the Python script
        cat > parse_filter_annotations.py << 'EOF'
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

    pharokka_dir = "pharokka_results"
    if not os.path.exists(pharokka_dir):
        print(f"Warning: Pharokka results directory not found: {pharokka_dir}")
        return pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    for dirname in os.listdir(pharokka_dir):
        if dirname.endswith("_pharokka"):
            cds_file = os.path.join(pharokka_dir, dirname, "pharokka_cds_functions.tsv")
            if os.path.isfile(cds_file):
                print(f"Processing Pharokka output: {dirname}")
                counts = {col: 0 for col in header[1:]}
                counts["Parent"] = dirname
                
                try:
                    df = pd.read_csv(cds_file, sep='\\t')
                    for _, row in df.iterrows():
                        if 'Description' in row and 'Count' in row:
                            desc = row['Description']
                            if desc in counts:
                                counts[desc] = row['Count']
                except Exception as e:
                    print(f"Error processing {cds_file}: {e}")
                    continue
                
                # Calculate structural genes
                total_structural = (counts.get("head and packaging", 0) + 
                                 counts.get("tail", 0) + counts.get("connector", 0))
                percent_structural = (total_structural / counts["CDS"] * 100 
                                   if counts["CDS"] > 0 else 0)
                
                counts["Total Structural Genes"] = total_structural
                counts["% Structural Genes"] = percent_structural
                
                results.append(counts)
            else:
                print(f"Warning: CDS functions file not found: {cds_file}")
    
    return pd.DataFrame(results) if results else pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

def parse_phold_output():
    results = []
    header = ["Parent", "CDS", "connector", "DNA, RNA and nucleotide metabolism",
             "head and packaging", "integration and excision", "lysis",
             "moron, auxiliary metabolic gene and host takeover", "other", "tail",
             "transcription regulation", "unknown function", "VFDB_Virulence_Factors",
             "CARD_AMR", "ACR_anti_crispr", "Defensefinder"]

    phold_dir = "phold_results"
    if not os.path.exists(phold_dir):
        print(f"Warning: PHOLD results directory not found: {phold_dir}")
        return pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    for dirname in os.listdir(phold_dir):
        if dirname.endswith("_phold"):
            func_file = os.path.join(phold_dir, dirname, "phold_all_cds_functions.tsv")
            if os.path.isfile(func_file):
                print(f"Processing PHOLD output: {dirname}")
                counts = {col: 0 for col in header[1:]}
                counts["Parent"] = dirname
                
                try:
                    df = pd.read_csv(func_file, sep='\\t')
                    for _, row in df.iterrows():
                        if 'Description' in row and 'Count' in row:
                            desc = row['Description']
                            if desc in counts:
                                counts[desc] = row['Count']
                except Exception as e:
                    print(f"Error processing {func_file}: {e}")
                    continue
                
                # Calculate structural genes
                total_structural = (counts.get("head and packaging", 0) + 
                                 counts.get("tail", 0) + counts.get("connector", 0))
                percent_structural = (total_structural / counts["CDS"] * 100 
                                   if counts["CDS"] > 0 else 0)
                
                counts["Total Structural Genes"] = total_structural
                counts["% Structural Genes"] = percent_structural
                
                results.append(counts)
            else:
                print(f"Warning: CDS functions file not found: {func_file}")
    
    return pd.DataFrame(results) if results else pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

def filter_entries(df, mode, ph_perc, ph_total, pl_perc, pl_total):
    if df.empty:
        print("Warning: DataFrame is empty, no filtering applied")
        return df
        
    if mode == 'pharokka':
        filtered = df[(df['Total Structural Genes'] >= ph_total) & 
                     (df['% Structural Genes'] >= ph_perc)]
        print(f"Pharokka filtering: {len(filtered)} sequences passed out of {len(df)}")
        return filtered
    elif mode == 'phold':
        filtered = df[(df['Total Structural Genes'] >= pl_total) & 
                     (df['% Structural Genes'] >= pl_perc)]
        print(f"PHOLD filtering: {len(filtered)} sequences passed out of {len(df)}")
        return filtered
    else:  # both
        pharokka_filtered = df[(df['Total Structural Genes'] >= ph_total) & 
                             (df['% Structural Genes'] >= ph_perc)]
        phold_filtered = df[(df['Total Structural Genes'] >= pl_total) & 
                          (df['% Structural Genes'] >= pl_perc)]
        combined = pd.concat([pharokka_filtered, phold_filtered]).drop_duplicates()
        print(f"Combined filtering: {len(combined)} sequences passed out of {len(df)}")
        return combined

# Main processing
print("Starting annotation parsing and filtering...")

# Parse outputs
print("Parsing Pharokka outputs...")
pharokka_df = parse_pharokka_output()
print(f"Pharokka results: {len(pharokka_df)} sequences")

print("Parsing PHOLD outputs...")
phold_df = parse_phold_output()
print(f"PHOLD results: {len(phold_df)} sequences")

# Combine and filter
combined_df = pd.concat([pharokka_df, phold_df]).drop_duplicates()
print(f"Combined results: {len(combined_df)} sequences")

filtered_df = filter_entries(combined_df, "${filter_mode}", 
                           ${pharokka_perc}, ${pharokka_total},
                           ${phold_perc}, ${phold_total})

print(f"Final filtered results: {len(filtered_df)} sequences")

# Write count to file
with open("annotation_count.txt", "w") as count_f:
    count_f.write(str(len(filtered_df)))

# Save filtered summary
filtered_df.to_csv("filtered_annotation_output.tsv", sep='\\t', index=False)
print("Saved filtered annotation summary")

# Process sequences
os.makedirs("annotation_filtered_sequences", exist_ok=True)

# Check if we have any filtered results
if len(filtered_df) == 0:
    print("")
    print("WARNING: No sequences passed annotation filtering!")
    print(f"  Pharokka thresholds: ${pharokka_perc}% / ${pharokka_total} genes")
    print(f"  PHOLD thresholds: ${phold_perc}% / ${phold_total} genes")
    print("")
    # Create empty combined FASTA file
    with open("annotation_filtered_sequences/filtered_phage_set.fasta", 'w') as f:
        pass
    print("Created empty output files")
else:
    filtered_names = [name.replace('_pharokka', '').replace('_phold', '') 
                     for name in filtered_df['Parent']]
    
    print(f"Looking for sequences with names: {filtered_names}")
    
    sequences_found = 0
    with open("annotation_filtered_sequences/filtered_phage_set.fasta", 'w') as combined:
        input_dir = "input_sequences"
        if os.path.exists(input_dir):
            for seq_file in os.listdir(input_dir):
                if seq_file.endswith(('.fasta', '.fa', '.fna')):
                    name = os.path.splitext(seq_file)[0]
                    if name in filtered_names:
                        src = os.path.join(input_dir, seq_file)
                        dst = os.path.join("annotation_filtered_sequences", seq_file)
                        shutil.copy(src, dst)
                        sequences_found += 1
                        
                        # Append to combined file
                        for record in SeqIO.parse(src, "fasta"):
                            SeqIO.write(record, combined, "fasta")
        else:
            print(f"Warning: Input sequences directory not found: {input_dir}")
    
    print(f"Successfully processed {sequences_found} filtered sequences")

print("Annotation parsing and filtering completed")
EOF
        
        # Run the Python script using the container
        singularity exec ${container_path} python3 parse_filter_annotations.py
        
        # Verify output files were created
        if [ ! -f "filtered_annotation_output.tsv" ]; then
            echo "ERROR: Filtered annotation output file not created"
            exit 1
        fi
        
        if [ ! -f "annotation_filtered_sequences/filtered_phage_set.fasta" ]; then
            echo "ERROR: Filtered phage set FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "annotation_count.txt" ]; then
            echo "ERROR: Annotation count file not created"
            exit 1
        fi
        
        echo "Parse Filter Annotations completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Parse Filter Annotations via Conda environment..."
        echo "Filter mode: ${filter_mode}"
        echo "Pharokka thresholds: ${pharokka_perc}% / ${pharokka_total} genes"
        echo "PHOLD thresholds: ${phold_perc}% / ${phold_total} genes"
        
        # Create the Python script
        cat > parse_filter_annotations.py << 'EOF'
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

    pharokka_dir = "pharokka_results"
    if not os.path.exists(pharokka_dir):
        print(f"Warning: Pharokka results directory not found: {pharokka_dir}")
        return pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    for dirname in os.listdir(pharokka_dir):
        if dirname.endswith("_pharokka"):
            cds_file = os.path.join(pharokka_dir, dirname, "pharokka_cds_functions.tsv")
            if os.path.isfile(cds_file):
                print(f"Processing Pharokka output: {dirname}")
                counts = {col: 0 for col in header[1:]}
                counts["Parent"] = dirname
                
                try:
                    df = pd.read_csv(cds_file, sep='\\t')
                    for _, row in df.iterrows():
                        if 'Description' in row and 'Count' in row:
                            desc = row['Description']
                            if desc in counts:
                                counts[desc] = row['Count']
                except Exception as e:
                    print(f"Error processing {cds_file}: {e}")
                    continue
                
                # Calculate structural genes
                total_structural = (counts.get("head and packaging", 0) + 
                                 counts.get("tail", 0) + counts.get("connector", 0))
                percent_structural = (total_structural / counts["CDS"] * 100 
                                   if counts["CDS"] > 0 else 0)
                
                counts["Total Structural Genes"] = total_structural
                counts["% Structural Genes"] = percent_structural
                
                results.append(counts)
            else:
                print(f"Warning: CDS functions file not found: {cds_file}")
    
    return pd.DataFrame(results) if results else pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

def parse_phold_output():
    results = []
    header = ["Parent", "CDS", "connector", "DNA, RNA and nucleotide metabolism",
             "head and packaging", "integration and excision", "lysis",
             "moron, auxiliary metabolic gene and host takeover", "other", "tail",
             "transcription regulation", "unknown function", "VFDB_Virulence_Factors",
             "CARD_AMR", "ACR_anti_crispr", "Defensefinder"]

    phold_dir = "phold_results"
    if not os.path.exists(phold_dir):
        print(f"Warning: PHOLD results directory not found: {phold_dir}")
        return pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

    for dirname in os.listdir(phold_dir):
        if dirname.endswith("_phold"):
            func_file = os.path.join(phold_dir, dirname, "phold_all_cds_functions.tsv")
            if os.path.isfile(func_file):
                print(f"Processing PHOLD output: {dirname}")
                counts = {col: 0 for col in header[1:]}
                counts["Parent"] = dirname
                
                try:
                    df = pd.read_csv(func_file, sep='\\t')
                    for _, row in df.iterrows():
                        if 'Description' in row and 'Count' in row:
                            desc = row['Description']
                            if desc in counts:
                                counts[desc] = row['Count']
                except Exception as e:
                    print(f"Error processing {func_file}: {e}")
                    continue
                
                # Calculate structural genes
                total_structural = (counts.get("head and packaging", 0) + 
                                 counts.get("tail", 0) + counts.get("connector", 0))
                percent_structural = (total_structural / counts["CDS"] * 100 
                                   if counts["CDS"] > 0 else 0)
                
                counts["Total Structural Genes"] = total_structural
                counts["% Structural Genes"] = percent_structural
                
                results.append(counts)
            else:
                print(f"Warning: CDS functions file not found: {func_file}")
    
    return pd.DataFrame(columns=header + ["Total Structural Genes", "% Structural Genes"])

def filter_entries(df, mode, ph_perc, ph_total, pl_perc, pl_total):
    if df.empty:
        print("Warning: DataFrame is empty, no filtering applied")
        return df
        
    if mode == 'pharokka':
        filtered = df[(df['Total Structural Genes'] >= ph_total) & 
                     (df['% Structural Genes'] >= ph_perc)]
        print(f"Pharokka filtering: {len(filtered)} sequences passed out of {len(df)}")
        return filtered
    elif mode == 'phold':
        filtered = df[(df['Total Structural Genes'] >= pl_total) & 
                     (df['% Structural Genes'] >= pl_perc)]
        print(f"PHOLD filtering: {len(filtered)} sequences passed out of {len(df)}")
        return filtered
    else:  # both
        pharokka_filtered = df[(df['Total Structural Genes'] >= ph_total) & 
                             (df['% Structural Genes'] >= ph_perc)]
        phold_filtered = df[(df['Total Structural Genes'] >= pl_total) & 
                          (df['% Structural Genes'] >= pl_perc)]
        combined = pd.concat([pharokka_filtered, phold_filtered]).drop_duplicates()
        print(f"Combined filtering: {len(combined)} sequences passed out of {len(df)}")
        return combined

# Main processing
print("Starting annotation parsing and filtering...")

# Parse outputs
print("Parsing Pharokka outputs...")
pharokka_df = parse_pharokka_output()
print(f"Pharokka results: {len(pharokka_df)} sequences")

print("Parsing PHOLD outputs...")
phold_df = parse_phold_output()
print(f"PHOLD results: {len(phold_df)} sequences")

# Combine and filter
combined_df = pd.concat([pharokka_df, phold_df]).drop_duplicates()
print(f"Combined results: {len(combined_df)} sequences")

filtered_df = filter_entries(combined_df, "${filter_mode}", 
                           ${pharokka_perc}, ${pharokka_total},
                           ${phold_perc}, ${phold_total})

print(f"Final filtered results: {len(filtered_df)} sequences")

# Write count to file
with open("annotation_count.txt", "w") as count_f:
    count_f.write(str(len(filtered_df)))

# Save filtered summary
filtered_df.to_csv("filtered_annotation_output.tsv", sep='\\t', index=False)
print("Saved filtered annotation summary")

# Process sequences
os.makedirs("annotation_filtered_sequences", exist_ok=True)

# Check if we have any filtered results
if len(filtered_df) == 0:
    print("")
    print("WARNING: No sequences passed annotation filtering!")
    print(f"  Pharokka thresholds: ${pharokka_perc}% / ${pharokka_total} genes")
    print(f"  PHOLD thresholds: ${phold_perc}% / ${phold_total} genes")
    print("")
    # Create empty combined FASTA file
    with open("annotation_filtered_sequences/filtered_phage_set.fasta", 'w') as f:
        pass
    print("Created empty output files")
else:
    filtered_names = [name.replace('_pharokka', '').replace('_phold', '') 
                     for name in filtered_df['Parent']]
    
    print(f"Looking for sequences with names: {filtered_names}")
    
    sequences_found = 0
    with open("annotation_filtered_sequences/filtered_phage_set.fasta", 'w') as combined:
        input_dir = "input_sequences"
        if os.path.exists(input_dir):
            for seq_file in os.listdir(input_dir):
                if seq_file.endswith(('.fasta', '.fa', '.fna')):
                    name = os.path.splitext(seq_file)[0]
                    if name in filtered_names:
                        src = os.path.join(input_dir, seq_file)
                        dst = os.path.join("annotation_filtered_sequences", seq_file)
                        shutil.copy(src, dst)
                        sequences_found += 1
                        
                        # Append to combined file
                        for record in SeqIO.parse(src, "fasta"):
                            SeqIO.write(record, combined, "fasta")
        else:
            print(f"Warning: Input sequences directory not found: {input_dir}")
    
    print(f"Successfully processed {sequences_found} filtered sequences")

print("Annotation parsing and filtering completed")
EOF
        
        # Run the Python script using conda environment
        python3 parse_filter_annotations.py
        
        # Verify output files were created
        if [ ! -f "filtered_annotation_output.tsv" ]; then
            echo "ERROR: Filtered annotation output file not created"
            exit 1
        fi
        
        if [ ! -f "annotation_filtered_sequences/filtered_phage_set.fasta" ]; then
            echo "ERROR: Filtered phage set FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "annotation_count.txt" ]; then
            echo "ERROR: Annotation count file not created"
            exit 1
        fi
        
        echo "Parse Filter Annotations completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}