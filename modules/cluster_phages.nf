process CLUSTER_PHAGES {
    publishDir "${params.outdir}/3.Annotation/Anno6_Clustering", mode: 'copy'

    input:
    path input_fasta
    val min_ani
    val min_coverage
    path anicalc_script
    path aniclust_script

    output:
    path "blast_db/*", emit: blast_db
    path "phage_blast.tsv", emit: blast_results
    path "phage_ani.tsv", emit: ani_results
    path "phage_clusters.tsv", emit: clusters
    tuple path("phage_clusters.tsv"), path(input_fasta), emit: for_extraction

    script:
    """
    # Create directory for blast database
    mkdir -p blast_db

    # 1. Make BLAST database
    makeblastdb -in ${input_fasta} \\
                -dbtype nucl \\
                -out blast_db/filtered_phage_db

    # 2. Run all-vs-all BLAST
    blastn -query ${input_fasta} \\
           -db blast_db/filtered_phage_db \\
           -outfmt '6 std qlen slen' \\
           -max_target_seqs 10000 \\
           -out phage_blast.tsv \\
           -num_threads ${task.cpus}

    # 3. Calculate pairwise ANI
    python ${anicalc_script} \\
           -i phage_blast.tsv \\
           -o phage_ani.tsv

    # 4. Perform clustering
    python ${aniclust_script} \\
           --fna ${input_fasta} \\
           --ani phage_ani.tsv \\
           --out phage_clusters.tsv \\
           --min_ani ${min_ani} \\
           --min_tcov ${min_coverage} \\
           --min_qcov ${min_coverage}
    """
}
