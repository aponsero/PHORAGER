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
    tuple val("${genome.simpleName}"), path("VIBRANT_*"), emit: results  // Using wildcard to match VIBRANT's output

    script:
    """
    # Run VIBRANT
    VIBRANT_run.py -i ${genome} -d ${vibrant_db}/databases/ -m ${vibrant_db}/files/ -no_plot -t 32
    """
}
