process PHOLD {
    tag "PHOLD annotation on multiple sequences"
    publishDir "${params.outdir}/3.Annotation/Anno4_PHOLD", mode: 'copy'

    input:
    path "*_pharokka"
    path phold_db

    output:
    path "*_phold", emit: results

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
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
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
        
        # Run phold on each pharokka output
        for pharokka_dir in *_pharokka; do
            if [ -d "\$pharokka_dir" ]; then
                # Get the original sequence name from the directory name
                original_name=\$(echo \$pharokka_dir | sed 's/_pharokka\$//')
                phold_output="\${original_name}_phold"
                
                echo "Processing \$pharokka_dir -> \$phold_output"
                
                # Verify Pharokka GenBank file exists
                if [ ! -f "\${pharokka_dir}/pharokka.gbk" ]; then
                    echo "ERROR: Pharokka GenBank file not found at \${pharokka_dir}/pharokka.gbk"
                    echo "Pharokka directory contents:"
                    ls -la \${pharokka_dir}/
                    exit 1
                fi
                
                singularity exec ${container_path} \\
                    phold run -i \${pharokka_dir}/pharokka.gbk \\
                              -o \$phold_output \\
                              -d ${phold_db} \\
                              -t ${task.cpus} \\
                              --cpu
                
                # Verify expected output files exist
                if [ ! -d "\$phold_output" ]; then
                    echo "ERROR: PHOLD output directory not found for \$pharokka_dir"
                    echo "Current directory contents:"
                    ls -la
                    exit 1
                fi
                
                echo "Successfully processed \$pharokka_dir"
            fi
        done
        
        echo "PHOLD annotation completed successfully for all sequences"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running PHOLD via Conda environment..."
        echo "PHOLD database: ${phold_db}"
        
        # Run phold on each pharokka output
        for pharokka_dir in *_pharokka; do
            if [ -d "\$pharokka_dir" ]; then
                # Get the original sequence name from the directory name
                original_name=\$(echo \$pharokka_dir | sed 's/_pharokka\$//')
                phold_output="\${original_name}_phold"
                
                echo "Processing \$pharokka_dir -> \$phold_output"
                
                # Verify Pharokka GenBank file exists
                if [ ! -f "\${pharokka_dir}/pharokka.gbk" ]; then
                    echo "ERROR: Pharokka GenBank file not found at \${pharokka_dir}/pharokka.gbk"
                    echo "Pharokka directory contents:"
                    ls -la \${pharokka_dir}/
                    exit 1
                fi
                
                phold run -i \${pharokka_dir}/pharokka.gbk \\
                          -o \$phold_output \\
                          -d ${phold_db} \\
                          -t ${task.cpus} \\
                          --cpu
                
                # Verify expected output files exist
                if [ ! -d "\$phold_output" ]; then
                    echo "ERROR: PHOLD output directory not found for \$pharokka_dir"
                    echo "Current directory contents:"
                    ls -la
                    exit 1
                fi
                
                echo "Successfully processed \$pharokka_dir"
            fi
        done
        
        echo "PHOLD annotation completed successfully for all sequences"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}