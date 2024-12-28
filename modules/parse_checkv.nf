process PARSE_CHECKV {
    tag "Parse CheckV results"
    publishDir "${params.outdir}/3.Annotation/Anno1_CheckV", mode: 'copy'

    input:
    path checkv_dir
    val min_length
    val quality_levels

    output:
    path "filtered_prophages.fasta", emit: filtered_fasta
    path "filter_summary.txt", emit: summary

    script:
    def qualities = quality_levels.collect { "\"${it}\"" }.join(", ")
    """
    #!/usr/bin/env python3
    import os
    from Bio import SeqIO

    # Define quality levels as strings
    ALLOWED_QUALITIES = [${qualities}]

    def filter_quality_summary(file_path, min_length, allowed_qualities):
        filtered_results = []
        with open(file_path, 'r') as f:
            header = next(f)  # Store header for summary
            for line in f:
                data = line.strip().split('\\t')
                contig_id = data[0]
                checkv_quality = data[7]
                contig_length = int(data[1])
                if checkv_quality in allowed_qualities and contig_length >= min_length:
                    filtered_results.append([contig_id, checkv_quality, contig_length])
        return filtered_results, header

    # Get input files
    quality_summary_file = os.path.join("${checkv_dir}", "quality_summary.tsv")
    viruses_file = os.path.join("${checkv_dir}", "viruses.fna")
    proviruses_file = os.path.join("${checkv_dir}", "proviruses.fna")

    # Filter prophages based on quality and length
    filtered_prophages, header = filter_quality_summary(quality_summary_file, ${min_length}, ALLOWED_QUALITIES)

    # Write summary
    with open("filter_summary.txt", "w") as sum_f:
        sum_f.write("CheckV Filter Summary\\n")
        sum_f.write("===================\\n\\n")
        sum_f.write(f"Minimum length threshold: ${min_length}bp\\n")
        sum_f.write(f"Quality levels included: {', '.join(ALLOWED_QUALITIES)}\\n\\n")
        sum_f.write("Filtered Prophages:\\n")
        sum_f.write(f"{'Contig ID':<40} {'Quality':<15} {'Length (bp)':<12}\\n")
        sum_f.write("-" * 67 + "\\n")
        for phage in filtered_prophages:
            sum_f.write(f"{phage[0]:<40} {phage[1]:<15} {phage[2]:<12}\\n")

    # Function to extract sequences
    def extract_sequences(fasta_file, filtered_ids, output_handle):
        if os.path.exists(fasta_file):
            for record in SeqIO.parse(fasta_file, "fasta"):
                if any(f_id in record.id for f_id, _, _ in filtered_ids):
                    SeqIO.write(record, output_handle, "fasta")

    # Write filtered sequences
    with open("filtered_prophages.fasta", "w") as out_f:
        extract_sequences(viruses_file, filtered_prophages, out_f)
        extract_sequences(proviruses_file, filtered_prophages, out_f)
    """
}
