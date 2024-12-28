process DREP {
    tag "dRep on filtered genomes"
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact3_dRep", mode: 'copy'

    input:
    path passed_list
    path genomes
    val ani_threshold    // New input parameter

    output:
    path "drep_output", optional: true, emit: drep_dir

    script:
    """
    # Create temporary directory for filtered genomes
    mkdir -p filtered_genomes

    # Read the passed_genomes.txt and copy corresponding genomes
    while IFS= read -r genome_name; do
        cp \$(find ${genomes} -name "\${genome_name}*.fa" -o -name "\${genome_name}*.fasta" -o -name "\${genome_name}*.fna") filtered_genomes/
    done < ${passed_list}

    # Run dRep with the configurable ANI threshold
    dRep dereplicate drep_output -g filtered_genomes/* -sa ${ani_threshold} --ignoreGenomeQuality
    """
}
