process CHECKV {
    tag "CheckV quality assessment"
    publishDir "${params.outdir}/3.Annotation/Anno1_CheckV", mode: 'copy'

    input:
    path fasta
    path checkv_db

    output:
    path "checkv_output", emit: dir
    path "checkv_output/quality_summary.tsv", emit: summary
    path "checkv_output/completeness.tsv", emit: completeness

    script:
    """
    # Print paths for debugging
    echo "Input fasta: ${fasta}"
    echo "CheckV database: ${checkv_db}"
    
    # Run CheckV with explicit database path
    checkv end_to_end ${fasta} checkv_output -d ${checkv_db}
    """
}
