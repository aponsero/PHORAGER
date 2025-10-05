process PHAROKKA {
    tag "Pharokka annotation on multiple sequences"
    publishDir "${params.outdir}/3.Annotation/Anno3_Pharokka", mode: 'copy'

    input:
    path "input_dir/*"
    path pharokka_db

    output:
    path "*_pharokka", emit: results

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['pharokka']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for pharokka"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Pharokka via Singularity container..."
        echo "Pharokka database: ${pharokka_db}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling Pharokka container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Pharokka container already exists, using cached version."
        fi
        
        # Run pharokka on each fasta file
        for fasta in input_dir/*.fasta; do
            if [ -f "\$fasta" ]; then
                name=\$(basename \$fasta .fasta)
                echo "Processing \$fasta -> \${name}_pharokka"
                
                singularity exec ${container_path} \\
                    pharokka.py -i \$fasta \\
                                -o "\${name}_pharokka" \\
                                -d ${pharokka_db} \\
                                -t ${task.cpus}
                
                # Verify output was created
                if [ ! -d "\${name}_pharokka" ]; then
                    echo "ERROR: Pharokka output directory not found for \$fasta"
                    exit 1
                fi
                
                if [ ! -f "\${name}_pharokka/pharokka.gbk" ]; then
                    echo "ERROR: Pharokka GenBank file not found for \$fasta"
                    exit 1
                fi
                
                echo "Successfully processed \$fasta"
            fi
        done
        
        echo "Pharokka annotation completed successfully for all sequences"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Pharokka via Conda environment..."
        echo "Pharokka database: ${pharokka_db}"
        
        # Run pharokka on each fasta file
        for fasta in input_dir/*.fasta; do
            if [ -f "\$fasta" ]; then
                name=\$(basename \$fasta .fasta)
                echo "Processing \$fasta -> \${name}_pharokka"
                
                pharokka.py -i \$fasta \\
                            -o "\${name}_pharokka" \\
                            -d ${pharokka_db} \\
                            -t ${task.cpus}
                
                # Verify output was created
                if [ ! -d "\${name}_pharokka" ]; then
                    echo "ERROR: Pharokka output directory not found for \$fasta"
                    exit 1
                fi
                
                if [ ! -f "\${name}_pharokka/pharokka.gbk" ]; then
                    echo "ERROR: Pharokka GenBank file not found for \$fasta"
                    exit 1
                fi
                
                echo "Successfully processed \$fasta"
            fi
        done
        
        echo "Pharokka annotation completed successfully for all sequences"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}