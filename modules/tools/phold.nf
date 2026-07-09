process PHOLD {
    tag "PHOLD annotation on ${pharokka_dir.simpleName}"
    publishDir "${params.outdir}/3.Annotation/Anno4_PHOLD", mode: 'copy',
        pattern: "*_phold_pub",
        saveAs: { filename -> filename.replace('_phold_pub', '_phold') }

    input:
    each path(pharokka_dir) 
    path phold_db

    output:
    path "*_phold", emit: results
    path "*_phold_pub", emit: publish_files, optional: true

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['phold']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for phold"
    }
    
    // Detect backend by profile name
    if (workflow.profile.contains('singularity') || workflow.profile.contains('standard'))
        """
        echo "Running PHOLD via Singularity container..."
        echo "PHOLD database: ${phold_db}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling PHOLD container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "PHOLD container already exists, using cached version."
        fi
        
        # Removed loop - process single pharokka output
        # Get the original sequence name from the directory name
        original_name=\$(echo ${pharokka_dir} | sed 's/_pharokka\$//')
        phold_output="\${original_name}_phold"
        
        echo "Processing ${pharokka_dir} -> \$phold_output"
        
        # Verify Pharokka GenBank file exists
        if [ ! -f "${pharokka_dir}/pharokka.gbk" ]; then
            echo "ERROR: Pharokka GenBank file not found at ${pharokka_dir}/pharokka.gbk"
            echo "Pharokka directory contents:"
            ls -la ${pharokka_dir}/
            exit 1
        fi
        
        # Run PHOLD and capture exit status - allow failure for "no hits" case
        set +e  # Temporarily disable exit on error
        singularity exec --no-home ${container_path} \\
            phold run -i ${pharokka_dir}/pharokka.gbk \\
                      -o \$phold_output \\
                      -d ${phold_db} \\
                      -t ${task.cpus} \\
                      --cpu 2>&1 | tee phold_run.log
        phold_exit=\$?
        set -e  # Re-enable exit on error
        
        # Handle the exit status
        if [ \$phold_exit -ne 0 ]; then
            # Check if failure was due to no hits (valid biological result)
            if grep -q "Foldseek found no hits whatsoever" phold_run.log; then
                echo "WARNING: PHOLD found no structural hits for ${pharokka_dir}"
                echo "This sequence may not be phage-like or lacks known structural proteins"
                echo "Creating empty output directory as this is a valid result"
                mkdir -p \$phold_output
                echo "# PHOLD found no structural hits for this sequence" > \$phold_output/NO_HITS.txt
            else
                # Real error - fail the process
                echo "ERROR: PHOLD failed with unexpected error for ${pharokka_dir}"
                cat phold_run.log
                exit 1
            fi
        fi
        
        # Verify output directory was created (either normally or as placeholder)
        if [ ! -d "\$phold_output" ]; then
            echo "ERROR: PHOLD output directory not found for ${pharokka_dir}"
            echo "Current directory contents:"
            ls -la
            exit 1
        fi
        
        # Stage key files for publishing (skipped gracefully for NO_HITS case)
        mkdir -p "\${phold_output}_pub"
        for f in phold_all_cds_functions.tsv phold_per_cds_predictions.tsv phold_output.gbk; do
            [ -f "\${phold_output}/\${f}" ] && cp "\${phold_output}/\${f}" "\${phold_output}_pub/"
        done
        
        echo "Successfully processed ${pharokka_dir}"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running PHOLD via Conda environment..."
        echo "PHOLD database: ${phold_db}"
        
        # Removed loop - process single pharokka output
        # Get the original sequence name from the directory name
        original_name=\$(echo ${pharokka_dir} | sed 's/_pharokka\$//')
        phold_output="\${original_name}_phold"
        
        echo "Processing ${pharokka_dir} -> \$phold_output"
        
        # Verify Pharokka GenBank file exists
        if [ ! -f "${pharokka_dir}/pharokka.gbk" ]; then
            echo "ERROR: Pharokka GenBank file not found at ${pharokka_dir}/pharokka.gbk"
            echo "Pharokka directory contents:"
            ls -la ${pharokka_dir}/
            exit 1
        fi
        
        # Run PHOLD and capture exit status - allow failure for "no hits" case
        set +e  # Temporarily disable exit on error
        phold run -i ${pharokka_dir}/pharokka.gbk \\
                  -o \$phold_output \\
                  -d ${phold_db} \\
                  -t ${task.cpus} \\
                  --cpu 2>&1 | tee phold_run.log
        phold_exit=\$?
        set -e  # Re-enable exit on error
        
        # Handle the exit status
        if [ \$phold_exit -ne 0 ]; then
            # Check if failure was due to no hits (valid biological result)
            if grep -q "Foldseek found no hits whatsoever" phold_run.log; then
                echo "WARNING: PHOLD found no structural hits for ${pharokka_dir}"
                echo "This sequence may not be phage-like or lacks known structural proteins"
                echo "Creating empty output directory as this is a valid result"
                mkdir -p \$phold_output
                echo "# PHOLD found no structural hits for this sequence" > \$phold_output/NO_HITS.txt
            else
                # Real error - fail the process
                echo "ERROR: PHOLD failed with unexpected error for ${pharokka_dir}"
                cat phold_run.log
                exit 1
            fi
        fi
        
        # Verify output directory was created (either normally or as placeholder)
        if [ ! -d "\$phold_output" ]; then
            echo "ERROR: PHOLD output directory not found for ${pharokka_dir}"
            echo "Current directory contents:"
            ls -la
            exit 1
        fi
        
        # Stage key files for publishing (skipped gracefully for NO_HITS case)
        mkdir -p "\${phold_output}_pub"
        for f in phold_all_cds_functions.tsv phold_per_cds_predictions.tsv phold_output.gbk; do
            [ -f "\${phold_output}/\${f}" ] && cp "\${phold_output}/\${f}" "\${phold_output}_pub/"
        done
        
        echo "Successfully processed ${pharokka_dir}"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}
