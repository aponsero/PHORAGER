process SPLIT_FASTA {
    tag "Splitting filtered prophage sequences"
    publishDir "${params.outdir}/3.Annotation/Anno2_SplitSequences", mode: 'copy'

    input:
    path fasta_file

    output:
    path "putative_prophage_sequences/*.fasta", emit: split_fastas

    script:
    """
    #!/usr/bin/env python3
    from Bio import SeqIO
    import os

    # Create output directory
    os.makedirs("putative_prophage_sequences", exist_ok=True)

    # Read and split sequences
    for record in SeqIO.parse("${fasta_file}", "fasta"):
        # Get sequence ID without spaces and create filename
        seq_id = record.id.split()[0]
        output_file = f"putative_prophage_sequences/{seq_id}.fasta"
        
        # Write individual sequence to file
        with open(output_file, 'w') as out_handle:
            SeqIO.write(record, out_handle, "fasta")
    """
}
