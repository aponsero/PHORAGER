process VIBRANT {
    tag "VIBRANT on ${genome.simpleName}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph2_VIBRANT/${genome.simpleName}", 
        mode: 'copy',
        saveAs: { filename -> 
            if (filename.startsWith("VIBRANT_")) {
                return "vibrant_output"
            }
        }

    input:
    each path(genome)
    path vibrant_db

    output:
    tuple val("${genome.simpleName}"), path("VIBRANT_*"), emit: results

    script:
    def tool_spec = params.container_specs['vibrant']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        # Create singularity cache directory
        mkdir -p ${params.singularity_cache_dir}

        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            singularity pull ${container_path} ${tool_spec.docker_url}
        fi

        # Get absolute paths for bind mounting
        VIBRANT_DB_ABS=\$(realpath ${vibrant_db})

        # Run VIBRANT with bind mounting
        singularity exec --bind \$(pwd):\$(pwd) --bind \${VIBRANT_DB_ABS}:\${VIBRANT_DB_ABS} ${container_path} \\
            VIBRANT_run.py -i ${genome} -d \${VIBRANT_DB_ABS}/databases/ -m \${VIBRANT_DB_ABS}/files/ \\
            -no_plot -l ${params.vibrant_min_length} -t ${task.cpus}
        """
    else if (workflow.profile.contains('conda'))
        """
        # Run VIBRANT using conda environment
        VIBRANT_run.py -i ${genome} -d ${vibrant_db}/databases/ -m ${vibrant_db}/files/ \\
            -no_plot -l ${params.vibrant_min_length} -t ${task.cpus}
        """
    else
        error "Unsupported backend. Please use either 'conda' or 'singularity' profile."
}