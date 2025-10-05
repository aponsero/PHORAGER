process ANNOTATION_SUMMARY {
    tag "Generating annotation workflow summary"
    publishDir "${params.outdir}/3.Annotation", mode: 'copy'

    input:
    path checkv_summary         // From PARSE_CHECKV
    path annotation_summary     // From PARSE_FILTER_ANNOTATIONS (optional)
    path cluster_results        // From CLUSTER_PHAGES
    path rep_sequences         // From EXTRACT_REPRESENTATIVES
    path prophage_count        // From PARSE_CHECKV
    path annotation_count      // From PARSE_FILTER_ANNOTATIONS (optional)
    val min_prophage_length
    val checkv_quality_levels
    val skip_detailed_annotation
    val pharokka_perc
    val pharokka_total
    val phold_perc
    val phold_total
    val clustering_min_ani
    val clustering_min_coverage

    output:
    path "Annotation_summary.log", emit: summary
    path "Final_representatives.fasta", emit: final_fasta
    path "Cluster_information.tsv", emit: final_clusters

    script:
    // This process uses the parsing_env (Python + pandas)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for parsing_env"
    }
    
    // Convert quality levels list to Python format - split by comma first
    def qualities = checkv_quality_levels.split(',').collect { "\"${it.trim()}\"" }.join(", ")
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Annotation Summary via Singularity container..."
        echo "CheckV summary: ${checkv_summary}"
        echo "Annotation summary: ${annotation_summary}"
        echo "Cluster results: ${cluster_results}"
        echo "Representative sequences: ${rep_sequences}"
        echo "Prophage count: ${prophage_count}"
        echo "Annotation count: ${annotation_count}"
        
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
        cat > annotation_summary.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
from Bio import SeqIO
import shutil
import os

# Read the prophage count first
with open("${prophage_count}", "r") as f:
    num_prophages = int(f.read().strip())

print(f"Number of prophages that passed CheckV filters: {num_prophages}")

# Read annotation count if available
num_annotation_filtered = None
if os.path.exists("${annotation_count}") and os.path.getsize("${annotation_count}") > 0:
    with open("${annotation_count}", "r") as f:
        num_annotation_filtered = int(f.read().strip())
    print(f"Number of sequences that passed annotation filters: {num_annotation_filtered}")

# Initialize summary lines
summary_lines = []
summary_lines.append("================================")
summary_lines.append("PROPHAGE ANNOTATION AND CLUSTERING")
summary_lines.append("================================\\n")

# Add parameter section
summary_lines.append("Parameters Used:")
summary_lines.append("-----------------")
summary_lines.append(f"Minimum prophage length: ${min_prophage_length}")

# Parse quality levels from parameter
quality_levels = [${qualities}]
summary_lines.append(f"CheckV quality levels: {', '.join(quality_levels)}")

# Convert string 'true'/'false' to boolean
skip_detailed = '${skip_detailed_annotation}'.lower() == 'true'

if not skip_detailed:
    summary_lines.append("\\nDetailed Annotation Parameters:")
    summary_lines.append(f"Pharokka structural percentage threshold: ${pharokka_perc}")
    summary_lines.append(f"Pharokka structural genes threshold: ${pharokka_total}")
    summary_lines.append(f"PHOLD structural percentage threshold: ${phold_perc}")
    summary_lines.append(f"PHOLD structural genes threshold: ${phold_total}")

summary_lines.append("\\nClustering Parameters:")
summary_lines.append(f"Minimum ANI: ${clustering_min_ani}")
summary_lines.append(f"Minimum coverage: ${clustering_min_coverage}\\n")

# Scenario 1: No prophages passed CheckV
if num_prophages == 0:
    summary_lines.append("=" * 70)
    summary_lines.append("WARNING: NO PROPHAGES PASSED CHECKV QUALITY FILTERS")
    summary_lines.append("=" * 70)
    summary_lines.append("")
    summary_lines.append("No prophage sequences met the quality and length criteria.")
    summary_lines.append("The annotation and clustering pipeline was skipped.")
    summary_lines.append("")
    summary_lines.append("Possible solutions:")
    summary_lines.append("  1. Lower the minimum length threshold (--min_prophage_length)")
    summary_lines.append("     Current: ${min_prophage_length}bp")
    summary_lines.append("  2. Include lower quality levels (--checkv_quality_levels)")
    summary_lines.append("     Current: " + ', '.join(quality_levels))
    summary_lines.append("     Available: Complete, High-quality, Medium-quality, Low-quality, Not-determined")
    summary_lines.append("  3. Review your input sequences and CheckV results")
    summary_lines.append("")
    
    # Write summary
    with open("Annotation_summary.log", "w") as f:
        f.write("\\n".join(summary_lines))
    
    # Create empty placeholder files
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences - no prophages passed CheckV filters\\n")
    
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No clusters - no prophages passed CheckV filters\\n")
    
    print("Generated summary report for zero CheckV results")
    exit(0)

# Scenario 2: Prophages passed CheckV but none passed annotation filtering
if num_annotation_filtered is not None and num_annotation_filtered == 0:
    summary_lines.append("CheckV Filtering Results:")
    summary_lines.append("-----------------------")
    summary_lines.append(f"Sequences passing CheckV filters: {num_prophages}\\n")
    
    summary_lines.append("=" * 70)
    summary_lines.append("WARNING: NO SEQUENCES PASSED ANNOTATION FILTERING")
    summary_lines.append("=" * 70)
    summary_lines.append("")
    summary_lines.append(f"{num_prophages} prophage(s) passed CheckV quality filters,")
    summary_lines.append("but none passed the structural gene annotation thresholds.")
    summary_lines.append("The clustering pipeline was skipped.")
    summary_lines.append("")
    summary_lines.append("Possible solutions:")
    summary_lines.append("  1. Lower the structural gene thresholds:")
    summary_lines.append(f"     --pharokka_structural_perc (current: ${pharokka_perc}%)")
    summary_lines.append(f"     --pharokka_structural_total (current: ${pharokka_total} genes)")
    summary_lines.append(f"     --phold_structural_perc (current: ${phold_perc}%)")
    summary_lines.append(f"     --phold_structural_total (current: ${phold_total} genes)")
    summary_lines.append("  2. Change filter mode (--annotation_filter_mode):")
    summary_lines.append("     'pharokka', 'phold', or 'combined' (less stringent)")
    summary_lines.append("  3. Skip detailed annotation (--skip_detailed_annotation)")
    summary_lines.append("     to use CheckV results directly for clustering")
    summary_lines.append("")
    
    # Write summary
    with open("Annotation_summary.log", "w") as f:
        f.write("\\n".join(summary_lines))
    
    # Create empty placeholder files
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences - no sequences passed annotation filters\\n")
    
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No clusters - no sequences passed annotation filters\\n")
    
    print("Generated summary report for zero annotation results")
    exit(0)

# Scenario 3: Normal case - we have sequences for clustering
summary_lines.append("CheckV Filtering Results:")
summary_lines.append("-----------------------")

# Process CheckV results
if os.path.exists("${checkv_summary}"):
    checkv_df = pd.read_csv("${checkv_summary}", sep='\\t')
    total_initial = len(checkv_df)
    summary_lines.append(f"Total sequences processed by CheckV: {total_initial}")
    summary_lines.append(f"Sequences passing filters: {num_prophages}\\n")
else:
    summary_lines.append("CheckV summary file not found\\n")

# Process annotation results if available
if not skip_detailed and num_annotation_filtered is not None:
    summary_lines.append("Annotation Filtering Results:")
    summary_lines.append("---------------------------")
    summary_lines.append(f"Sequences after annotation filtering: {num_annotation_filtered}\\n")
elif skip_detailed:
    summary_lines.append("Detailed annotation was skipped\\n")

# Process clustering results
if os.path.exists("${cluster_results}") and os.path.getsize("${cluster_results}") > 0:
    try:
        cluster_df = pd.read_csv("${cluster_results}", sep='\\t', header=None)
        num_clusters = len(cluster_df)
        summary_lines.append("Clustering Results:")
        summary_lines.append("------------------")
        summary_lines.append(f"Total number of clusters: {num_clusters}")
        
        # Calculate cluster statistics from column 2
        cluster_sizes = cluster_df.iloc[:, 1].str.count(',') + 1
        avg_cluster_size = cluster_sizes.mean()
        max_cluster_size = cluster_sizes.max()
        singleton_clusters = sum(cluster_sizes == 1)
        
        summary_lines.append(f"Average sequences per cluster: {avg_cluster_size:.2f}")
        summary_lines.append(f"Largest cluster size: {max_cluster_size}")
        summary_lines.append(f"Singleton clusters: {singleton_clusters}")
    except Exception as e:
        summary_lines.append("\\nClustering Results:")
        summary_lines.append("------------------")
        summary_lines.append(f"Error reading cluster results: {e}")
else:
    summary_lines.append("\\nClustering Results:")
    summary_lines.append("------------------")
    summary_lines.append("Cluster results file not found or empty")

# Write summary
with open("Annotation_summary.log", "w") as f:
    f.write("\\n".join(summary_lines))

# Copy final files
if os.path.exists("${rep_sequences}") and os.path.getsize("${rep_sequences}") > 0:
    shutil.copy("${rep_sequences}", "Final_representatives.fasta")
    print("Copied representative sequences")
else:
    print("Warning: Representative sequences file not found or empty")
    # Create empty file
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences available\\n")

if os.path.exists("${cluster_results}") and os.path.getsize("${cluster_results}") > 0:
    shutil.copy("${cluster_results}", "Cluster_information.tsv")
    print("Copied cluster information")
else:
    print("Warning: Cluster results file not found or empty")
    # Create empty file with header
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No cluster information available\\n")

print("Annotation summary generation completed")
EOF
        
        # Run the Python script using the container
        singularity exec ${container_path} python3 annotation_summary.py
        
        # Verify output files were created
        if [ ! -f "Annotation_summary.log" ]; then
            echo "ERROR: Annotation summary log file not created"
            exit 1
        fi
        
        if [ ! -f "Final_representatives.fasta" ]; then
            echo "ERROR: Final representatives FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "Cluster_information.tsv" ]; then
            echo "ERROR: Cluster information file not created"
            exit 1
        fi
        
        echo "Annotation Summary completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Annotation Summary via Conda environment..."
        echo "CheckV summary: ${checkv_summary}"
        echo "Annotation summary: ${annotation_summary}"
        echo "Cluster results: ${cluster_results}"
        echo "Representative sequences: ${rep_sequences}"
        echo "Prophage count: ${prophage_count}"
        echo "Annotation count: ${annotation_count}"
        
        # Create the Python script (same as singularity block)
        cat > annotation_summary.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
from Bio import SeqIO
import shutil
import os

# Read the prophage count first
with open("${prophage_count}", "r") as f:
    num_prophages = int(f.read().strip())

print(f"Number of prophages that passed CheckV filters: {num_prophages}")

# Read annotation count if available
num_annotation_filtered = None
if os.path.exists("${annotation_count}") and os.path.getsize("${annotation_count}") > 0:
    with open("${annotation_count}", "r") as f:
        num_annotation_filtered = int(f.read().strip())
    print(f"Number of sequences that passed annotation filters: {num_annotation_filtered}")

# Initialize summary lines
summary_lines = []
summary_lines.append("================================")
summary_lines.append("PROPHAGE ANNOTATION AND CLUSTERING")
summary_lines.append("================================\\n")

# Add parameter section
summary_lines.append("Parameters Used:")
summary_lines.append("-----------------")
summary_lines.append(f"Minimum prophage length: ${min_prophage_length}")

# Parse quality levels from parameter
quality_levels = [${qualities}]
summary_lines.append(f"CheckV quality levels: {', '.join(quality_levels)}")

# Convert string 'true'/'false' to boolean
skip_detailed = '${skip_detailed_annotation}'.lower() == 'true'

if not skip_detailed:
    summary_lines.append("\\nDetailed Annotation Parameters:")
    summary_lines.append(f"Pharokka structural percentage threshold: ${pharokka_perc}")
    summary_lines.append(f"Pharokka structural genes threshold: ${pharokka_total}")
    summary_lines.append(f"PHOLD structural percentage threshold: ${phold_perc}")
    summary_lines.append(f"PHOLD structural genes threshold: ${phold_total}")

summary_lines.append("\\nClustering Parameters:")
summary_lines.append(f"Minimum ANI: ${clustering_min_ani}")
summary_lines.append(f"Minimum coverage: ${clustering_min_coverage}\\n")

# Scenario 1: No prophages passed CheckV
if num_prophages == 0:
    summary_lines.append("=" * 70)
    summary_lines.append("WARNING: NO PROPHAGES PASSED CHECKV QUALITY FILTERS")
    summary_lines.append("=" * 70)
    summary_lines.append("")
    summary_lines.append("No prophage sequences met the quality and length criteria.")
    summary_lines.append("The annotation and clustering pipeline was skipped.")
    summary_lines.append("")
    summary_lines.append("Possible solutions:")
    summary_lines.append("  1. Lower the minimum length threshold (--min_prophage_length)")
    summary_lines.append("     Current: ${min_prophage_length}bp")
    summary_lines.append("  2. Include lower quality levels (--checkv_quality_levels)")
    summary_lines.append("     Current: " + ', '.join(quality_levels))
    summary_lines.append("     Available: Complete, High-quality, Medium-quality, Low-quality, Not-determined")
    summary_lines.append("  3. Review your input sequences and CheckV results")
    summary_lines.append("")
    
    # Write summary
    with open("Annotation_summary.log", "w") as f:
        f.write("\\n".join(summary_lines))
    
    # Create empty placeholder files
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences - no prophages passed CheckV filters\\n")
    
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No clusters - no prophages passed CheckV filters\\n")
    
    print("Generated summary report for zero CheckV results")
    exit(0)

# Scenario 2: Prophages passed CheckV but none passed annotation filtering
if num_annotation_filtered is not None and num_annotation_filtered == 0:
    summary_lines.append("CheckV Filtering Results:")
    summary_lines.append("-----------------------")
    summary_lines.append(f"Sequences passing CheckV filters: {num_prophages}\\n")
    
    summary_lines.append("=" * 70)
    summary_lines.append("WARNING: NO SEQUENCES PASSED ANNOTATION FILTERING")
    summary_lines.append("=" * 70)
    summary_lines.append("")
    summary_lines.append(f"{num_prophages} prophage(s) passed CheckV quality filters,")
    summary_lines.append("but none passed the structural gene annotation thresholds.")
    summary_lines.append("The clustering pipeline was skipped.")
    summary_lines.append("")
    summary_lines.append("Possible solutions:")
    summary_lines.append("  1. Lower the structural gene thresholds:")
    summary_lines.append(f"     --pharokka_structural_perc (current: ${pharokka_perc}%)")
    summary_lines.append(f"     --pharokka_structural_total (current: ${pharokka_total} genes)")
    summary_lines.append(f"     --phold_structural_perc (current: ${phold_perc}%)")
    summary_lines.append(f"     --phold_structural_total (current: ${phold_total} genes)")
    summary_lines.append("  2. Change filter mode (--annotation_filter_mode):")
    summary_lines.append("     'pharokka', 'phold', or 'combined' (less stringent)")
    summary_lines.append("  3. Skip detailed annotation (--skip_detailed_annotation)")
    summary_lines.append("     to use CheckV results directly for clustering")
    summary_lines.append("")
    
    # Write summary
    with open("Annotation_summary.log", "w") as f:
        f.write("\\n".join(summary_lines))
    
    # Create empty placeholder files
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences - no sequences passed annotation filters\\n")
    
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No clusters - no sequences passed annotation filters\\n")
    
    print("Generated summary report for zero annotation results")
    exit(0)

# Scenario 3: Normal case - we have sequences for clustering
summary_lines.append("CheckV Filtering Results:")
summary_lines.append("-----------------------")

# Process CheckV results
if os.path.exists("${checkv_summary}"):
    checkv_df = pd.read_csv("${checkv_summary}", sep='\\t')
    total_initial = len(checkv_df)
    summary_lines.append(f"Total sequences processed by CheckV: {total_initial}")
    summary_lines.append(f"Sequences passing filters: {num_prophages}\\n")
else:
    summary_lines.append("CheckV summary file not found\\n")

# Process annotation results if available
if not skip_detailed and num_annotation_filtered is not None:
    summary_lines.append("Annotation Filtering Results:")
    summary_lines.append("---------------------------")
    summary_lines.append(f"Sequences after annotation filtering: {num_annotation_filtered}\\n")
elif skip_detailed:
    summary_lines.append("Detailed annotation was skipped\\n")

# Process clustering results
if os.path.exists("${cluster_results}") and os.path.getsize("${cluster_results}") > 0:
    try:
        cluster_df = pd.read_csv("${cluster_results}", sep='\\t', header=None)
        num_clusters = len(cluster_df)
        summary_lines.append("Clustering Results:")
        summary_lines.append("------------------")
        summary_lines.append(f"Total number of clusters: {num_clusters}")
        
        # Calculate cluster statistics from column 2
        cluster_sizes = cluster_df.iloc[:, 1].str.count(',') + 1
        avg_cluster_size = cluster_sizes.mean()
        max_cluster_size = cluster_sizes.max()
        singleton_clusters = sum(cluster_sizes == 1)
        
        summary_lines.append(f"Average sequences per cluster: {avg_cluster_size:.2f}")
        summary_lines.append(f"Largest cluster size: {max_cluster_size}")
        summary_lines.append(f"Singleton clusters: {singleton_clusters}")
    except Exception as e:
        summary_lines.append("\\nClustering Results:")
        summary_lines.append("------------------")
        summary_lines.append(f"Error reading cluster results: {e}")
else:
    summary_lines.append("\\nClustering Results:")
    summary_lines.append("------------------")
    summary_lines.append("Cluster results file not found or empty")

# Write summary
with open("Annotation_summary.log", "w") as f:
    f.write("\\n".join(summary_lines))

# Copy final files
if os.path.exists("${rep_sequences}") and os.path.getsize("${rep_sequences}") > 0:
    shutil.copy("${rep_sequences}", "Final_representatives.fasta")
    print("Copied representative sequences")
else:
    print("Warning: Representative sequences file not found or empty")
    # Create empty file
    with open("Final_representatives.fasta", "w") as f:
        f.write("# No representative sequences available\\n")

if os.path.exists("${cluster_results}") and os.path.getsize("${cluster_results}") > 0:
    shutil.copy("${cluster_results}", "Cluster_information.tsv")
    print("Copied cluster information")
else:
    print("Warning: Cluster results file not found or empty")
    # Create empty file with header
    with open("Cluster_information.tsv", "w") as f:
        f.write("# No cluster information available\\n")

print("Annotation summary generation completed")
EOF
        
        # Run the Python script using conda environment
        python3 annotation_summary.py
        
        # Verify output files were created
        if [ ! -f "Annotation_summary.log" ]; then
            echo "ERROR: Annotation summary log file not created"
            exit 1
        fi
        
        if [ ! -f "Final_representatives.fasta" ]; then
            echo "ERROR: Final representatives FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "Cluster_information.tsv" ]; then
            echo "ERROR: Cluster information file not created"
            exit 1
        fi
        
        echo "Annotation Summary completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}