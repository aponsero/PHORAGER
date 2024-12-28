process EXTRACT_REPRESENTATIVES {
    publishDir "${params.outdir}/3.Annotation/Anno6_Clustering", mode: 'copy'

    input:
    tuple path(clusters), path(input_fasta)

    output:
    path "cluster_representatives.tsv", emit: rep_list
    path "cluster_representative_sequences.fasta", emit: rep_seqs

    script:
    """
    # Extract representative sequence IDs
    awk '{print \$1}' ${clusters} > cluster_representatives.tsv

    # Extract representative sequences using seqfu
    seqfu list cluster_representatives.tsv ${input_fasta} > cluster_representative_sequences.fasta
    """
}
