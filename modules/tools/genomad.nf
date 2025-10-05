process GENOMAD {
    tag "GenoMAD on ${genome.simpleName}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph1_geNomad/${genome.simpleName}", mode: 'copy'

    input:
    each path(genome)
    path genomad_db

    output:
    tuple val("${genome.simpleName}"), path("genomad_output"), emit: results

    script:
    def tool_spec = params.container_specs['genomad']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    
    // Handle GenoMAD preset parameter
    def preset_flag = ""
    if (params.genomad_preset == 'conservative') {
        preset_flag = "--conservative"
    } else if (params.genomad_preset == 'relaxed') {
        preset_flag = "--relaxed"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        # Create singularity cache directory
        mkdir -p ${params.singularity_cache_dir}

        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            singularity pull ${container_path} ${tool_spec.docker_url}
        fi

        # Get absolute paths for bind mounting
        GENOMAD_DB_ABS=\$(realpath ${genomad_db})

        # Run GenoMAD with bind mounting
        singularity exec --bind \$(pwd):\$(pwd) --bind \${GENOMAD_DB_ABS}:\${GENOMAD_DB_ABS} ${container_path} \\
            genomad end-to-end ${preset_flag} --cleanup --threads ${task.cpus} \\
            ${genome} genomad_output \${GENOMAD_DB_ABS}
        """
    else if (workflow.profile.contains('conda'))
        """
        # Run GenoMAD using conda environment
        genomad end-to-end ${preset_flag} --cleanup --threads ${task.cpus} \\
            ${genome} genomad_output ${genomad_db}
        """
    else
        error "Unsupported backend. Please use either 'conda' or 'singularity' profile."
}