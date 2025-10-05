process DREP {
    tag "dRep on filtered genomes"
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact3_dRep", mode: 'copy'

    input:
    path passed_list
    path genomes
    val ani_threshold
    val threads

    output:
    path "drep_output", optional: true, emit: drep_dir

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['drep']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running dRep via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling dRep container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "dRep container already exists, using cached version."
        fi
        
        # Create temporary directory for filtered genomes
        mkdir -p filtered_genomes

        # Read the passed_genomes.txt and copy corresponding genomes
        while IFS= read -r genome_name; do
            cp \$(find ${genomes} -name "\${genome_name}*.fa" -o -name "\${genome_name}*.fasta" -o -name "\${genome_name}*.fna") filtered_genomes/
        done < ${passed_list}

        # Set matplotlib configuration directory to avoid permission issues
        export MPLCONFIGDIR=/tmp/matplotlib_config
        
        # Run dRep using singularity
        singularity exec ${container_path} \\
            dRep dereplicate drep_output -g filtered_genomes/* -sa ${ani_threshold} --ignoreGenomeQuality --processors ${threads}
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running dRep via Conda environment..."
        
        # Create temporary directory for filtered genomes
        mkdir -p filtered_genomes

        # Read the passed_genomes.txt and copy corresponding genomes
        while IFS= read -r genome_name; do
            cp \$(find ${genomes} -name "\${genome_name}*.fa" -o -name "\${genome_name}*.fasta" -o -name "\${genome_name}*.fna") filtered_genomes/
        done < ${passed_list}

        # Run dRep with the configurable ANI threshold
        dRep dereplicate drep_output -g filtered_genomes/* -sa ${ani_threshold} --ignoreGenomeQuality --processors ${threads}
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}