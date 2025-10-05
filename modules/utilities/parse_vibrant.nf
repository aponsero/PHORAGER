process PARSE_VIBRANT {
    tag "Parse VIBRANT results for ${genome_name}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph2_VIBRANT/${genome_name}", mode: 'copy'
    
    input:
    tuple val(genome_name), path('vibrant_dir')

    output:
    tuple val(genome_name), path("*_vibrant_coordinates.tsv"), emit: coordinates 

    script:
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        # Create singularity cache directory
        mkdir -p ${params.singularity_cache_dir}

        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            singularity pull ${container_path} ${tool_spec.docker_url}
        fi

        # Create Python script
        cat > parse_vibrant.py << 'EOF'
#!/usr/bin/env python3
import glob
import os
import pandas as pd
from Bio import SeqIO

# Get genome name from Nextflow
genome_name = '${genome_name}'

def find_files(directory, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if pattern in filename:
                matches.append(os.path.join(root, filename))
    return matches

def extract_contig_headers(fasta_files):
    data = []
    for file_path in fasta_files:
        genome_id = os.path.basename(file_path).split('.phages_')[0]
        with open(file_path, "r") as file:
            for record in SeqIO.parse(file, "fasta"):
                data.append([genome_id, record.id, record.description])
    return pd.DataFrame(data, columns=['Folder', 'Contig', 'full_header'])

def process_coordinates_file(file_path):
    try:
        return pd.read_csv(file_path, sep='\\t')
    except Exception as e:
        return pd.DataFrame(columns=['fragment', 'nucleotide start', 'nucleotide stop'])

# Find relevant files with correct file pattern
fasta_files = find_files('vibrant_dir', '.phages_combined.fna')
coordinate_files = find_files('vibrant_dir', 'integrated_prophage_coordinates')

output_file = f"{genome_name}_vibrant_coordinates.tsv"

if not coordinate_files:
    empty_df = pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])
    empty_df.to_csv(output_file, sep='\\t', index=False)
else:
    try:
        coords_df = process_coordinates_file(coordinate_files[0])
        
        if fasta_files and not coords_df.empty:
            headers_df = extract_contig_headers(fasta_files)
            
            merged_df = pd.merge(headers_df, coords_df, 
                               left_on='full_header', 
                               right_on='fragment', 
                               how='left')
            
            result_df = pd.DataFrame({
                'Folder': merged_df['Folder'],
                'Contig': merged_df['Contig'],
                'Start': merged_df['nucleotide start'].fillna('NA'),
                'End': merged_df['nucleotide stop'].fillna('NA'),
                'Tool': 'VIBRANT'
            })
            
            for col in ['Start', 'End']:
                result_df[col] = result_df[col].apply(
                    lambda x: str(int(float(x))) if x != 'NA' else 'NA'
                )
        else:
            result_df = pd.DataFrame({
                'Folder': [genome_name] * len(coords_df),
                'Contig': coords_df['fragment'],
                'Start': coords_df['nucleotide start'],
                'End': coords_df['nucleotide stop'],
                'Tool': 'VIBRANT'
            })

        result_df.to_csv(output_file, sep='\\t', index=False)
        
    except Exception as e:
        empty_df = pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])
        empty_df.to_csv(output_file, sep='\\t', index=False)
EOF

        # Execute script with singularity
        singularity exec --bind \$(pwd):\$(pwd) ${container_path} python3 parse_vibrant.py
        """
    else if (workflow.profile.contains('conda'))
        """
        # Create Python script
        cat > parse_vibrant.py << 'EOF'
#!/usr/bin/env python3
import glob
import os
import pandas as pd
from Bio import SeqIO

# Get genome name from Nextflow
genome_name = '${genome_name}'

def find_files(directory, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if pattern in filename:
                matches.append(os.path.join(root, filename))
    return matches

def extract_contig_headers(fasta_files):
    data = []
    for file_path in fasta_files:
        genome_id = os.path.basename(file_path).split('.phages_')[0]
        with open(file_path, "r") as file:
            for record in SeqIO.parse(file, "fasta"):
                data.append([genome_id, record.id, record.description])
    return pd.DataFrame(data, columns=['Folder', 'Contig', 'full_header'])

def process_coordinates_file(file_path):
    try:
        return pd.read_csv(file_path, sep='\\t')
    except Exception as e:
        return pd.DataFrame(columns=['fragment', 'nucleotide start', 'nucleotide stop'])

# Find relevant files with correct file pattern
fasta_files = find_files('vibrant_dir', '.phages_combined.fna')
coordinate_files = find_files('vibrant_dir', 'integrated_prophage_coordinates')

output_file = f"{genome_name}_vibrant_coordinates.tsv"

if not coordinate_files:
    empty_df = pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])
    empty_df.to_csv(output_file, sep='\\t', index=False)
else:
    try:
        coords_df = process_coordinates_file(coordinate_files[0])
        
        if fasta_files and not coords_df.empty:
            headers_df = extract_contig_headers(fasta_files)
            
            merged_df = pd.merge(headers_df, coords_df, 
                               left_on='full_header', 
                               right_on='fragment', 
                               how='left')
            
            result_df = pd.DataFrame({
                'Folder': merged_df['Folder'],
                'Contig': merged_df['Contig'],
                'Start': merged_df['nucleotide start'].fillna('NA'),
                'End': merged_df['nucleotide stop'].fillna('NA'),
                'Tool': 'VIBRANT'
            })
            
            for col in ['Start', 'End']:
                result_df[col] = result_df[col].apply(
                    lambda x: str(int(float(x))) if x != 'NA' else 'NA'
                )
        else:
            result_df = pd.DataFrame({
                'Folder': [genome_name] * len(coords_df),
                'Contig': coords_df['fragment'],
                'Start': coords_df['nucleotide start'],
                'End': coords_df['nucleotide stop'],
                'Tool': 'VIBRANT'
            })

        result_df.to_csv(output_file, sep='\\t', index=False)
        
    except Exception as e:
        empty_df = pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])
        empty_df.to_csv(output_file, sep='\\t', index=False)
EOF

        # Execute script with conda environment
        python3 parse_vibrant.py
        """
    else
        error "Unsupported backend. Please use either 'conda' or 'singularity' profile."
}