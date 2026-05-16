process PHAROKKA {
    tag "Pharokka annotation on ${fasta_file.simpleName}"  
    publishDir "${params.outdir}/3.Annotation/Anno3_Pharokka", mode: 'copy',
        pattern: "*_pharokka_pub",
        saveAs: { filename -> filename.replace('_pharokka_pub', '_pharokka') }

    input:
    each path(fasta_file) 
    path pharokka_db

    output:
    path "*_pharokka", emit: results
    path "*_pharokka_pub", emit: publish_files, optional: true

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
        
        # Removed loop - process single fasta file
        name=\$(basename ${fasta_file} .fasta)
        echo "Processing ${fasta_file} -> \${name}_pharokka"
        
        singularity exec --no-home --cleanenv ${container_path} \\
            pharokka.py -i ${fasta_file} \\
                        -o "\${name}_pharokka" \\
                        -d ${pharokka_db} \\
                        -t ${task.cpus}
        
        # Verify output was created
        if [ ! -d "\${name}_pharokka" ]; then
            echo "ERROR: Pharokka output directory not found for ${fasta_file}"
            exit 1
        fi
        
        if [ ! -f "\${name}_pharokka/pharokka.gbk" ]; then
            echo "ERROR: Pharokka GenBank file not found for ${fasta_file}"
            exit 1
        fi
        
        # Stage key files for publishing
        mkdir -p "\${name}_pharokka_pub"
        for f in pharokka.gbk pharokka.gff pharokka_cds_functions.tsv \\
                  pharokka_length_gc_cds_density.tsv pharokka_top_hits_mash_inphared.tsv; do
            [ -f "\${name}_pharokka/\${f}" ] && cp "\${name}_pharokka/\${f}" "\${name}_pharokka_pub/"
        done
        
        echo "Successfully processed ${fasta_file}"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Pharokka via Conda environment..."
        echo "Pharokka database: ${pharokka_db}"
        
        # Removed loop - process single fasta file
        name=\$(basename ${fasta_file} .fasta)
        echo "Processing ${fasta_file} -> \${name}_pharokka"
        
        pharokka.py -i ${fasta_file} \\
                    -o "\${name}_pharokka" \\
                    -d ${pharokka_db} \\
                    -t ${task.cpus}
        
        # Verify output was created
        if [ ! -d "\${name}_pharokka" ]; then
            echo "ERROR: Pharokka output directory not found for ${fasta_file}"
            exit 1
        fi
        
        if [ ! -f "\${name}_pharokka/pharokka.gbk" ]; then
            echo "ERROR: Pharokka GenBank file not found for ${fasta_file}"
            exit 1
        fi
        
        # Stage key files for publishing
        mkdir -p "\${name}_pharokka_pub"
        for f in pharokka.gbk pharokka.gff pharokka_cds_functions.tsv \\
                  pharokka_length_gc_cds_density.tsv pharokka_top_hits_mash_inphared.tsv; do
            [ -f "\${name}_pharokka/\${f}" ] && cp "\${name}_pharokka/\${f}" "\${name}_pharokka_pub/"
        done
        
        echo "Successfully processed ${fasta_file}"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}
