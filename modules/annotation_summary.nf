process ANNOTATION_SUMMARY {
    publishDir "${params.outdir}/3.Annotation", mode: 'copy'

    input:
    path checkv_summary         // From PARSE_CHECKV
    path annotation_summary     // From PARSE_FILTER_ANNOTATIONS (optional)
    path cluster_results        // From CLUSTER_PHAGES
    path rep_sequences         // From EXTRACT_REPRESENTATIVES
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
    """
    #!/usr/bin/env python3
    import pandas as pd
    from Bio import SeqIO
    import shutil
    import json
    
    # Initialize summary lines
    summary_lines = []
    summary_lines.append("================================")
    summary_lines.append("PROPHAGE ANNOTATION AND CLUSTERING")
    summary_lines.append("================================\\n")

    # Add parameter section
    summary_lines.append("Parameters Used:")
    summary_lines.append("-----------------")
    summary_lines.append(f"Minimum prophage length: ${min_prophage_length}")
    
    # Parse quality levels from string representation
    quality_levels = '${checkv_quality_levels}'.replace('[', '').replace(']', '').replace("'", "").split(', ')
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

    # Process CheckV results
    checkv_df = pd.read_csv("${checkv_summary}", sep='\\t')
    total_initial = len(checkv_df)
    summary_lines.append("CheckV Filtering Results:")
    summary_lines.append("------------------------")
    summary_lines.append(f"Total sequences analyzed: {total_initial}")

    # Process annotation results if available
    if not skip_detailed and "${annotation_summary}" != "":
        annot_df = pd.read_csv("${annotation_summary}", sep='\\t')
        total_after_annotation = len(annot_df)
        summary_lines.append(f"Sequences after structural filtering: {total_after_annotation}")
        summary_lines.append(f"Sequences filtered out: {total_initial - total_after_annotation}")

    # Process clustering results
    cluster_df = pd.read_csv("${cluster_results}", sep='\\t')
    total_clusters = len(cluster_df)
    summary_lines.append("\\nClustering Results:")
    summary_lines.append("------------------")
    summary_lines.append(f"Total clusters formed: {total_clusters}")
    
    # Count sequences per cluster
    if not cluster_df.empty and len(cluster_df.columns) > 1:  # Assuming cluster members are in column 2
        cluster_sizes = cluster_df.iloc[:, 1].str.count(',') + 1
        avg_cluster_size = cluster_sizes.mean()
        max_cluster_size = cluster_sizes.max()
        singleton_clusters = sum(cluster_sizes == 1)
        
        summary_lines.append(f"Average sequences per cluster: {avg_cluster_size:.2f}")
        summary_lines.append(f"Largest cluster size: {max_cluster_size}")
        summary_lines.append(f"Singleton clusters: {singleton_clusters}")

    # Write summary
    with open("Annotation_summary.log", "w") as f:
        f.write("\\n".join(summary_lines))

    # Copy final files
    shutil.copy("${rep_sequences}", "Final_representatives.fasta")
    shutil.copy("${cluster_results}", "Cluster_information.tsv")
    """
}
