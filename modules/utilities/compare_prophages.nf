process COMPARE_PROPHAGES {
    tag "Comparing prophages for ${genome_name}"
    publishDir "${params.outdir}/2.Prophage_detection/Proph3_Comparison/${genome_name}", mode: 'copy'

    input:
    tuple val(genome_name), path(genomad_coords), path(vibrant_coords), path(genome_file)

    output:
    tuple val(genome_name), path("${genome_name}_consolidated_coordinates.tsv"), emit: consolidated
    path "${genome_name}_comparison_summary.txt", emit: summary
    path "${genome_name}_prophage_sequences.fasta", emit: prophage_sequences

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
        cat > compare_prophages.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import os
from collections import defaultdict
from Bio import SeqIO
import re

def read_results_file(filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0 and not filepath.endswith('NO_RESULTS'):
        return pd.read_csv(filepath, sep='\\t', dtype=str)
    return pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])

def find_max_overlap(group, contig_data):
    contig_id = group['Contig'].iloc[0]
    folder = group['Folder'].iloc[0]
    starts = list(group['Start'])
    ends = list(group['End'])
    
    if any(str(start).upper() == 'NA' or str(end).upper() == 'NA' for start, end in zip(starts, ends)):
        contig_data[contig_id].append(('all', 'all', folder))
    else:
        starts = [int(float(x)) for x in starts]
        ends = [int(float(x)) for x in ends]
        sorted_ranges = sorted(zip(starts, ends))
        
        if sorted_ranges:
            current_start, current_end = sorted_ranges[0]
            
            for start, end in sorted_ranges[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    contig_data[contig_id].append((current_start, current_end, folder))
                    current_start, current_end = start, end
                    
            contig_data[contig_id].append((current_start, current_end, folder))

def extract_prophage_sequences(genome_file, result_df, output_fasta):
    sequences_by_contig = {}
    full_names = {}
    
    for record in SeqIO.parse(genome_file, "fasta"):
        contig_prefix = re.split(r'[_ .]', record.id)[0]
        sequences_by_contig[contig_prefix] = record.seq
        full_names[contig_prefix] = record.id
    
    extracted_count = 0
    with open(output_fasta, "w") as output:
        for _, row in result_df.iterrows():
            contig_prefix = re.split(r'[_ .]', row['Contig'])[0]
            start = row['Start']
            end = row['End']
            
            sequence = sequences_by_contig.get(contig_prefix, None)
            full_name = full_names.get(contig_prefix, contig_prefix)
            
            if sequence is not None:
                if str(start).lower() == 'all' and str(end).lower() == 'all':
                    header = ">" + full_name + "_complete"
                    output.write(header + "\\n" + str(sequence) + "\\n")
                    extracted_count += 1
                else:
                    try:
                        start = int(float(start))
                        end = int(float(end))
                        header = ">" + full_name + "_" + str(start) + "_" + str(end)
                        subsequence = sequence[start - 1:end]
                        output.write(header + "\\n" + str(subsequence) + "\\n")
                        extracted_count += 1
                    except (ValueError, TypeError):
                        print("Skipping invalid coordinates for contig " + full_name + ": " + str(start) + ", " + str(end))
            else:
                print("Warning: Contig " + full_name + " not found in genome file")
                
    return extracted_count

def write_summary(summary_file, result_df, df, extracted_count, genome_name):
    with open(summary_file, 'w') as f:
        f.write("Summary for " + genome_name + "\\n")
        f.write("=" * 50 + "\\n")
        f.write("Total consolidated regions: " + str(len(result_df)) + "\\n")
        f.write("Number of contigs with prophages: " + str(result_df['Contig'].nunique()) + "\\n")
        f.write("Number of sequences extracted: " + str(extracted_count) + "\\n")
        
        tool_counts = df['Tool'].value_counts()
        f.write("\\nPredictions by tool:\\n")
        for tool, count in tool_counts.items():
            f.write(tool + ": " + str(count) + "\\n")
        
        original_count = len(df)
        consolidated_count = len(result_df)
        f.write("\\nOriginal predictions: " + str(original_count) + "\\n")
        f.write("Consolidated predictions: " + str(consolidated_count) + "\\n")
        if original_count > consolidated_count:
            f.write("Overlapping regions merged: " + str(original_count - consolidated_count) + "\\n")

# Main execution
genome_name = "${genome_name}"
try:
    genomad_df = read_results_file("${genomad_coords}")
    vibrant_df = read_results_file("${vibrant_coords}")
    
    df = pd.concat([genomad_df, vibrant_df], ignore_index=True)
    
    if df.empty:
        pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool']).to_csv(
            genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
        with open(genome_name + '_comparison_summary.txt', 'w') as f:
            f.write("Summary for " + genome_name + "\\n")
            f.write("=" * 50 + "\\n")
            f.write("No prophage regions detected\\n")
        with open(genome_name + '_prophage_sequences.fasta', 'w') as f:
            pass
    else:
        contig_data = defaultdict(list)
        
        for name, group in df.groupby('Contig'):
            find_max_overlap(group, contig_data)
        
        result_data = []
        for contig_id, data_list in contig_data.items():
            for start, end, folder in data_list:
                if start != 'all':
                    start = int(float(start))
                    end = int(float(end))
                result_data.append((folder, contig_id, start, end))
                
        result_df = pd.DataFrame(result_data, columns=['Folder', 'Contig', 'Start', 'End'])
        
        result_df.to_csv(genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
        
        extracted_count = extract_prophage_sequences(
            "${genome_file}",
            result_df,
            genome_name + '_prophage_sequences.fasta'
        )
        
        write_summary(genome_name + '_comparison_summary.txt', result_df, df, extracted_count, genome_name)
        
except Exception as e:
    print("Error processing " + genome_name + ": " + str(e))
    pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool']).to_csv(
        genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
    with open(genome_name + '_comparison_summary.txt', 'w') as f:
        f.write("Error processing " + genome_name + ": " + str(e) + "\\n")
    with open(genome_name + '_prophage_sequences.fasta', 'w') as f:
        pass
    raise
EOF

        # Execute script with singularity
        singularity exec --bind \$(pwd):\$(pwd) ${container_path} python3 compare_prophages.py
        """
    else if (workflow.profile.contains('conda'))
        """
        # Create Python script
        cat > compare_prophages.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import os
from collections import defaultdict
from Bio import SeqIO
import re

def read_results_file(filepath):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0 and not filepath.endswith('NO_RESULTS'):
        return pd.read_csv(filepath, sep='\\t', dtype=str)
    return pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool'])

def find_max_overlap(group, contig_data):
    contig_id = group['Contig'].iloc[0]
    folder = group['Folder'].iloc[0]
    starts = list(group['Start'])
    ends = list(group['End'])
    
    if any(str(start).upper() == 'NA' or str(end).upper() == 'NA' for start, end in zip(starts, ends)):
        contig_data[contig_id].append(('all', 'all', folder))
    else:
        starts = [int(float(x)) for x in starts]
        ends = [int(float(x)) for x in ends]
        sorted_ranges = sorted(zip(starts, ends))
        
        if sorted_ranges:
            current_start, current_end = sorted_ranges[0]
            
            for start, end in sorted_ranges[1:]:
                if start <= current_end:
                    current_end = max(current_end, end)
                else:
                    contig_data[contig_id].append((current_start, current_end, folder))
                    current_start, current_end = start, end
                    
            contig_data[contig_id].append((current_start, current_end, folder))

def extract_prophage_sequences(genome_file, result_df, output_fasta):
    sequences_by_contig = {}
    full_names = {}
    
    for record in SeqIO.parse(genome_file, "fasta"):
        contig_prefix = re.split(r'[_ .]', record.id)[0]
        sequences_by_contig[contig_prefix] = record.seq
        full_names[contig_prefix] = record.id
    
    extracted_count = 0
    with open(output_fasta, "w") as output:
        for _, row in result_df.iterrows():
            contig_prefix = re.split(r'[_ .]', row['Contig'])[0]
            start = row['Start']
            end = row['End']
            
            sequence = sequences_by_contig.get(contig_prefix, None)
            full_name = full_names.get(contig_prefix, contig_prefix)
            
            if sequence is not None:
                if str(start).lower() == 'all' and str(end).lower() == 'all':
                    header = ">" + full_name + "_complete"
                    output.write(header + "\\n" + str(sequence) + "\\n")
                    extracted_count += 1
                else:
                    try:
                        start = int(float(start))
                        end = int(float(end))
                        header = ">" + full_name + "_" + str(start) + "_" + str(end)
                        subsequence = sequence[start - 1:end]
                        output.write(header + "\\n" + str(subsequence) + "\\n")
                        extracted_count += 1
                    except (ValueError, TypeError):
                        print("Skipping invalid coordinates for contig " + full_name + ": " + str(start) + ", " + str(end))
            else:
                print("Warning: Contig " + full_name + " not found in genome file")
                
    return extracted_count

def write_summary(summary_file, result_df, df, extracted_count, genome_name):
    with open(summary_file, 'w') as f:
        f.write("Summary for " + genome_name + "\\n")
        f.write("=" * 50 + "\\n")
        f.write("Total consolidated regions: " + str(len(result_df)) + "\\n")
        f.write("Number of contigs with prophages: " + str(result_df['Contig'].nunique()) + "\\n")
        f.write("Number of sequences extracted: " + str(extracted_count) + "\\n")
        
        tool_counts = df['Tool'].value_counts()
        f.write("\\nPredictions by tool:\\n")
        for tool, count in tool_counts.items():
            f.write(tool + ": " + str(count) + "\\n")
        
        original_count = len(df)
        consolidated_count = len(result_df)
        f.write("\\nOriginal predictions: " + str(original_count) + "\\n")
        f.write("Consolidated predictions: " + str(consolidated_count) + "\\n")
        if original_count > consolidated_count:
            f.write("Overlapping regions merged: " + str(original_count - consolidated_count) + "\\n")

# Main execution
genome_name = "${genome_name}"
try:
    genomad_df = read_results_file("${genomad_coords}")
    vibrant_df = read_results_file("${vibrant_coords}")
    
    df = pd.concat([genomad_df, vibrant_df], ignore_index=True)
    
    if df.empty:
        pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool']).to_csv(
            genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
        with open(genome_name + '_comparison_summary.txt', 'w') as f:
            f.write("Summary for " + genome_name + "\\n")
            f.write("=" * 50 + "\\n")
            f.write("No prophage regions detected\\n")
        with open(genome_name + '_prophage_sequences.fasta', 'w') as f:
            pass
    else:
        contig_data = defaultdict(list)
        
        for name, group in df.groupby('Contig'):
            find_max_overlap(group, contig_data)
        
        result_data = []
        for contig_id, data_list in contig_data.items():
            for start, end, folder in data_list:
                if start != 'all':
                    start = int(float(start))
                    end = int(float(end))
                result_data.append((folder, contig_id, start, end))
                
        result_df = pd.DataFrame(result_data, columns=['Folder', 'Contig', 'Start', 'End'])
        
        result_df.to_csv(genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
        
        extracted_count = extract_prophage_sequences(
            "${genome_file}",
            result_df,
            genome_name + '_prophage_sequences.fasta'
        )
        
        write_summary(genome_name + '_comparison_summary.txt', result_df, df, extracted_count, genome_name)
        
except Exception as e:
    print("Error processing " + genome_name + ": " + str(e))
    pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End', 'Tool']).to_csv(
        genome_name + '_consolidated_coordinates.tsv', sep='\\t', index=False)
    with open(genome_name + '_comparison_summary.txt', 'w') as f:
        f.write("Error processing " + genome_name + ": " + str(e) + "\\n")
    with open(genome_name + '_prophage_sequences.fasta', 'w') as f:
        pass
    raise
EOF

        # Execute script with conda environment
        python3 compare_prophages.py
        """
    else
        error "Unsupported backend. Please use either 'conda' or 'singularity' profile."
}