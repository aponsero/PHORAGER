process EXTRACT_REPRESENTATIVES {
    tag "Extracting cluster representatives"
    publishDir "${params.outdir}/3.Annotation/Anno6_Clustering", mode: 'copy'

    input:
    tuple path(clusters), path(input_fasta)

    output:
    path "cluster_representatives.tsv", emit: rep_list
    path "cluster_representative_sequences.fasta", emit: rep_seqs

    script:
    // This process uses the checkv environment (includes seqfu)
    def tool_spec = params.container_specs['checkv']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for checkv"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Extract Representatives via Singularity container..."
        echo "Clusters file: ${clusters}"
        echo "Input fasta: ${input_fasta}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling CheckV environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "CheckV environment container already exists, using cached version."
        fi
        
        # Verify input files exist
        if [ ! -f "${clusters}" ]; then
            echo "ERROR: Clusters file not found: ${clusters}"
            exit 1
        fi
        
        if [ ! -f "${input_fasta}" ]; then
            echo "ERROR: Input FASTA file not found: ${input_fasta}"
            exit 1
        fi
        
        # Extract representative sequence IDs (first column of clusters file)
        echo "Extracting representative sequence IDs..."
        awk '{print \$1}' ${clusters} > cluster_representatives.tsv
        
        # Verify representatives file was created and is not empty
        if [ ! -s "cluster_representatives.tsv" ]; then
            echo "ERROR: No representative sequences found in clusters file"
            echo "Clusters file contents:"
            head -n 5 ${clusters}
            exit 1
        fi
        
        rep_count=\$(wc -l < cluster_representatives.tsv)
        echo "Found \$rep_count representative sequences"
        
        # Extract representative sequences using seqfu
        echo "Extracting representative sequences using seqfu..."
        singularity exec ${container_path} \\
            seqfu list cluster_representatives.tsv ${input_fasta} > cluster_representative_sequences.fasta
        
        # Verify output FASTA file was created and is not empty
        if [ ! -s "cluster_representative_sequences.fasta" ]; then
            echo "ERROR: Representative sequences FASTA file is empty or not created"
            echo "Representative IDs:"
            head cluster_representatives.tsv
            echo "Input FASTA headers (first 5):"
            singularity exec ${container_path} grep "^>" ${input_fasta} | head -n 5
            exit 1
        fi
        
        seq_count=\$(singularity exec ${container_path} grep -c "^>" cluster_representative_sequences.fasta)
        echo "Successfully extracted \$seq_count representative sequences"
        
        if [ "\$seq_count" -ne "\$rep_count" ]; then
            echo "WARNING: Number of extracted sequences (\$seq_count) does not match number of representatives (\$rep_count)"
            echo "Some representative sequences may not have been found in the input FASTA"
        fi
        
        echo "Extract representatives completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Extract Representatives via Conda environment..."
        echo "Clusters file: ${clusters}"
        echo "Input fasta: ${input_fasta}"
        
        # Verify input files exist
        if [ ! -f "${clusters}" ]; then
            echo "ERROR: Clusters file not found: ${clusters}"
            exit 1
        fi
        
        if [ ! -f "${input_fasta}" ]; then
            echo "ERROR: Input FASTA file not found: ${input_fasta}"
            exit 1
        fi
        
        # Extract representative sequence IDs (first column of clusters file)
        echo "Extracting representative sequence IDs..."
        awk '{print \$1}' ${clusters} > cluster_representatives.tsv
        
        # Verify representatives file was created and is not empty
        if [ ! -s "cluster_representatives.tsv" ]; then
            echo "ERROR: No representative sequences found in clusters file"
            echo "Clusters file contents:"
            head -n 5 ${clusters}
            exit 1
        fi
        
        rep_count=\$(wc -l < cluster_representatives.tsv)
        echo "Found \$rep_count representative sequences"
        
        # Extract representative sequences using seqfu
        echo "Extracting representative sequences using seqfu..."
        seqfu list cluster_representatives.tsv ${input_fasta} > cluster_representative_sequences.fasta
        
        # Verify output FASTA file was created and is not empty
        if [ ! -s "cluster_representative_sequences.fasta" ]; then
            echo "ERROR: Representative sequences FASTA file is empty or not created"
            echo "Representative IDs:"
            head cluster_representatives.tsv
            echo "Input FASTA headers (first 5):"
            grep "^>" ${input_fasta} | head -n 5
            exit 1
        fi
        
        seq_count=\$(grep -c "^>" cluster_representative_sequences.fasta)
        echo "Successfully extracted \$seq_count representative sequences"
        
        if [ "\$seq_count" -ne "\$rep_count" ]; then
            echo "WARNING: Number of extracted sequences (\$seq_count) does not match number of representatives (\$rep_count)"
            echo "Some representative sequences may not have been found in the input FASTA"
        fi
        
        echo "Extract representatives completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}