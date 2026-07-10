process SUMMARIZE {
    tag "Generating ${summary_type} summary"
    publishDir "${params.outdir}/4.Summaries", mode: 'copy'

    input:
    val summary_type
    val bacterial_outdir
    val annotation_outdir
    val summary_format
    path runner
    path summaries_pkg

    output:
    path "${summary_type}.${summary_format}", emit: summary_table

    script:
    def tool_spec    = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url  = tool_spec.singularity_url

    // Build optional directory arguments — only pass flags whose values
    // were actually provided (non-empty string, not the sentinel 'NONE')
    def bact_arg = (bacterial_outdir && bacterial_outdir != 'NONE')
        ? "--bacterial-outdir '${bacterial_outdir}'"
        : ""
    def anno_arg = (annotation_outdir && annotation_outdir != 'NONE')
        ? "--annotation-outdir '${annotation_outdir}'"
        : ""

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running ${summary_type} summary via Singularity container..."

        mkdir -p ${params.singularity_cache_dir}

        if [ ! -f "${container_path}" ]; then
            echo "Pulling parsing environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing environment container already exists, using cached version."
        fi

        singularity exec --no-home \\
            ${container_path} \\
            python3 ${runner} \\
                --type    ${summary_type} \\
                --output  ${summary_type}.${summary_format} \\
                --format  ${summary_format} \\
                ${bact_arg} \\
                ${anno_arg}
        """

    else if (workflow.profile.contains('conda'))
        """
        echo "Running ${summary_type} summary via Conda environment..."

        python3 ${runner} \\
            --type    ${summary_type} \\
            --output  ${summary_type}.${summary_format} \\
            --format  ${summary_format} \\
            ${bact_arg} \\
            ${anno_arg}
        """

    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity"
        exit 1
        """
}
