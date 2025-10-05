process CHECKM2 {
    tag "CheckM2 on ${genome.simpleName}"
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact1_CheckM2", mode: 'copy'

    input:
    path genome
    path checkm2_db
    val threads

    output:
    path "checkm2_output", emit: dir
    path "quality_report.tsv", emit: report

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['checkm2']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running CheckM2 via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling CheckM2 container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "CheckM2 container already exists, using cached version."
        fi
        
        # Set the CheckM2 database location
        export CHECKM2DB=\$(realpath ${checkm2_db}/uniref100.KO.1.dmnd)
        echo "CHECKM2DB environment variable: \$CHECKM2DB"

        # Create a directory for the input genomes
        mkdir -p input_genomes
        
        # Copy and rename genome files to .fna extension (CheckM2 bug workaround)
        # Handle both single files and directories
        for GENOME_FILE in *.fa *.fasta *.fna; do
            # Skip if no files match the pattern
            [ -e "\$GENOME_FILE" ] || continue
            
            GENOME_BASENAME=\$(basename "\$GENOME_FILE")
            
            # Strip the actual extension (.fa, .fasta, or .fna) and add .fna
            GENOME_NAME="\${GENOME_BASENAME%.fa}"
            GENOME_NAME="\${GENOME_NAME%.fasta}"
            GENOME_NAME="\${GENOME_NAME%.fna}"
            
            echo "Copying \$GENOME_BASENAME as \${GENOME_NAME}.fna"
            cp "\$GENOME_FILE" "input_genomes/\${GENOME_NAME}.fna"
        done

        # Run CheckM2 using manual singularity execution (no bind mounting for HPC compatibility)
        singularity exec ${container_path} \\
            checkm2 predict --threads ${threads} --input input_genomes --output-directory checkm2_output --force

        # Move the quality report to the current directory
        mv checkm2_output/quality_report.tsv .
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running CheckM2 via Conda environment..."
        
        # Set the CheckM2 database location
        export CHECKM2DB=\$(realpath ${checkm2_db}/uniref100.KO.1.dmnd)
        echo "CHECKM2DB environment variable: \$CHECKM2DB"

        # Create a directory for the input genomes
        mkdir -p input_genomes
        
        # Copy and rename genome files to .fna extension (CheckM2 bug workaround)
        # Handle both single files and directories
        for GENOME_FILE in *.fa *.fasta *.fna; do
            # Skip if no files match the pattern
            [ -e "\$GENOME_FILE" ] || continue
            
            GENOME_BASENAME=\$(basename "\$GENOME_FILE")
            
            # Strip the actual extension (.fa, .fasta, or .fna) and add .fna
            GENOME_NAME="\${GENOME_BASENAME%.fa}"
            GENOME_NAME="\${GENOME_NAME%.fasta}"
            GENOME_NAME="\${GENOME_NAME%.fna}"
            
            echo "Copying \$GENOME_BASENAME as \${GENOME_NAME}.fna"
            cp "\$GENOME_FILE" "input_genomes/\${GENOME_NAME}.fna"
        done

        # Run CheckM2
        checkm2 predict --threads ${threads} --input input_genomes --output-directory checkm2_output --force

        # Move the quality report to the current directory
        mv checkm2_output/quality_report.tsv .
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}