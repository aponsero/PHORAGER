process PARSE_GENOMAD {
    tag "Parse geNomad results for ${genome_name}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph1_geNomad/${genome_name}", mode: 'copy'
    
    input:
    tuple val(genome_name), path('genomad_output')

    output:
    tuple val(genome_name), path("*_genomad_coordinates.tsv"), emit: coordinates 

    script:
    """
    #!/usr/bin/env python3
    import os
    import pandas as pd

    def extract_info(file_path):
        data = pd.read_csv(file_path, sep='\\t')
        folder_name = os.path.basename(os.path.dirname(file_path)).split('_summary')[0]
        result = []
        for index, row in data.iterrows():
            contig_name = row['seq_name'].split('|')[0]
            coordinates = row['coordinates']
            if isinstance(coordinates, str):
                start, end = coordinates.split('-')
            else:
                start = end = 'NA'
            tool = 'geNomad'
            result.append([folder_name, contig_name, start, end, tool])
        return result

    # Get the summary file for this specific genome
    output_file = "${genome_name}_genomad_coordinates.tsv"
    with open(output_file, 'w') as f_out:
        f_out.write("Folder\\tContig\\tStart\\tEnd\\tTool\\n")
        for root, dirs, files in os.walk('genomad_output'):
            for file in files:
                if file.endswith('_virus_summary.tsv'):
                    file_path = os.path.join(root, file)
                    info = extract_info(file_path)
                    for row in info:
                        f_out.write('\\t'.join(map(str, row)) + '\\n')
    """
}
