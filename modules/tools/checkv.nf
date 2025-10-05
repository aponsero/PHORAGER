process CHECKV {
    tag "CheckV quality assessment on ${fasta.simpleName}"
    publishDir "${params.outdir}/3.Annotation/Anno1_CheckV", mode: 'copy'

    input:
    path fasta
    path checkv_db

    output:
    path "checkv_output", emit: dir
    path "checkv_output/quality_summary.tsv", emit: summary
    path "checkv_output/completeness.tsv", emit: completeness

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['checkv']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url  // CheckV uses singularity_url not docker_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for checkv"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running CheckV via Singularity container..."
        echo "Input fasta: ${fasta}"
        echo "CheckV database: ${checkv_db}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling CheckV container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "CheckV container already exists, using cached version."
        fi
        
        # Run CheckV with explicit database path (no bind mounting for HPC compatibility)
        singularity exec ${container_path} \\
                         checkv end_to_end ${fasta} checkv_output -d ${checkv_db} -t ${task.cpus}
        
        # Verify expected output files exist
        if [ ! -f "checkv_output/quality_summary.tsv" ]; then
            echo "ERROR: CheckV quality_summary.tsv not found"
            echo "CheckV output directory contents:"
            ls -la checkv_output/
            exit 1
        fi
        
        if [ ! -f "checkv_output/completeness.tsv" ]; then
            echo "ERROR: CheckV completeness.tsv not found"
            echo "CheckV output directory contents:"
            ls -la checkv_output/
            exit 1
        fi
        
        echo "CheckV analysis completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running CheckV via Conda environment..."
        echo "Input fasta: ${fasta}"
        echo "CheckV database: ${checkv_db}"
        
        # Run CheckV with explicit database path
        checkv end_to_end ${fasta} checkv_output -d ${checkv_db} -t ${task.cpus}
        
        # Verify expected output files exist
        if [ ! -f "checkv_output/quality_summary.tsv" ]; then
            echo "ERROR: CheckV quality_summary.tsv not found"
            echo "CheckV output directory contents:"
            ls -la checkv_output/
            exit 1
        fi
        
        if [ ! -f "checkv_output/completeness.tsv" ]; then
            echo "ERROR: CheckV completeness.tsv not found"
            echo "CheckV output directory contents:"
            ls -la checkv_output/
            exit 1
        fi
        
        echo "CheckV analysis completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}