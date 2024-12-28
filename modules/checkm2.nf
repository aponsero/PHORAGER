process CHECKM2 {
    tag "CheckM2 on ${genome.simpleName}"
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact1_CheckM2", mode: 'copy'

    input:
    path genome
    path checkm2_db

    output:
    path "checkm2_output", emit: dir
    path "quality_report.tsv", emit: report

    script:
    """
    # Set the CheckM2 database location
    export CHECKM2DB=\$(realpath ${checkm2_db}/uniref100.KO.1.dmnd)
    echo "CHECKM2DB environment variable: \$CHECKM2DB"

    # Create a directory for the input genome
    mkdir -p input_genomes
    cp -r ${genome} input_genomes/

    # Run CheckM2
    checkm2 predict --threads ${task.cpus} --input input_genomes --output-directory checkm2_output --force

    # Move the quality report to the current directory
    mv checkm2_output/quality_report.tsv .
    """
}
