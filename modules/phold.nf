process PHOLD {
    tag "PHOLD on multiple sequences"
    publishDir "${params.outdir}/3.Annotation/Anno4_PHOLD", mode: 'copy'

    input:
    path "*_pharokka"
    path phold_db

    output:
    path "*_phold", emit: results

    script:
    """
    # Run phold on each pharokka output
    for pharokka_dir in *_pharokka; do
        # Get the original sequence name from the symlink
        original_name=\$(readlink \$pharokka_dir | xargs basename | sed 's/_pharokka\$//')
        
        phold run -i "\${pharokka_dir}/pharokka.gbk" \\
                  -o "\${original_name}_phold" \\
                  -d ${phold_db} \\
                  --cpu
    done
    """
}
