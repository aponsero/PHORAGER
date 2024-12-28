process PHAROKKA {
    tag "Pharokka on multiple sequences"
    publishDir "${params.outdir}/3.Annotation/Anno3_Pharokka", mode: 'copy'

    input:
    path "input_dir/*"
    path pharokka_db

    output:
    path "*_pharokka", emit: results

    script:
    """
    # Run pharokka on each fasta file
    for fasta in input_dir/*.fasta; do
        name=\$(basename \$fasta .fasta)
        pharokka.py -i \$fasta \\
                    -o "\${name}_pharokka" \\
                    -d ${pharokka_db}  \\
		    -t 16
        echo "Processed \$fasta"
    done
    """
}
