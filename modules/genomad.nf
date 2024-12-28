process GENOMAD {
    tag "geNomad on ${genome.simpleName}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph1_geNomad/${genome.simpleName}", mode: 'copy'

    input:
    each path(genome)
    path genomad_db

    output:
    tuple val("${genome.simpleName}"), path("genomad_output"), emit: results

    script:
    """
    # Run geNomad with cleanup option
    genomad end-to-end --cleanup ${genome} genomad_output ${genomad_db}
    """
}
