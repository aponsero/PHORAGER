process PROPHAGE_SUMMARY {
    publishDir "${params.outdir}/2.Prophage_detection", mode: 'copy'

    input:
    path summaries
    path coordinates
    path sequences

    output:
    path "Prophage_detection_summary.log", emit: summary_log
    path "All_prophage_sequences.fasta", emit: combined_sequences
    path "All_prophage_coordinates.tsv", emit: combined_coordinates

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
        cat > prophage_summary.py << 'EOF'
#!/usr/bin/env python3
import os
import glob
import pandas as pd
from collections import defaultdict

def parse_summary_files(summary_files):
    total_stats = defaultdict(int)
    tool_stats = defaultdict(int)
    
    for summary_file in summary_files:
        with open(summary_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "Total consolidated regions:" in line:
                    total_stats['total_regions'] += int(line.split(":")[1].strip())
                elif "Number of sequences extracted:" in line:
                    total_stats['sequences_extracted'] += int(line.split(":")[1].strip())
                elif "geNomad:" in line:
                    count = int(line.split(":")[1].strip())
                    tool_stats['geNomad'] += count
                elif "VIBRANT:" in line:
                    count = int(line.split(":")[1].strip())
                    tool_stats['VIBRANT'] += count

    return total_stats, tool_stats

def count_and_combine_sequences(sequence_files, output_fasta):
    total_sequences = 0
    total_bp = 0
    
    with open(output_fasta, 'w') as outf:
        for fasta in sequence_files:
            if os.path.exists(fasta) and os.path.getsize(fasta) > 0:
                with open(fasta, 'r') as f:
                    for line in f:
                        outf.write(line)
                        if line.startswith('>'):
                            total_sequences += 1
                        else:
                            total_bp += len(line.strip())
                            
    return total_sequences, total_bp

def combine_coordinates(coordinate_files, output_tsv):
    dfs = []
    for coord_file in coordinate_files:
        if os.path.exists(coord_file) and os.path.getsize(coord_file) > 0:
            df = pd.read_csv(coord_file, sep='\\t')
            dfs.append(df)
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_csv(output_tsv, sep='\\t', index=False)
    else:
        pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End']).to_csv(
            output_tsv, sep='\\t', index=False)

# Main execution
sequence_files = [f for f in glob.glob("*_prophage_sequences.fasta") if os.path.exists(f)]
total_sequences, total_bp = count_and_combine_sequences(sequence_files, "All_prophage_sequences.fasta")

coordinate_files = [f for f in glob.glob("*_consolidated_coordinates.tsv") if os.path.exists(f)]
combine_coordinates(coordinate_files, "All_prophage_coordinates.tsv")

with open("Prophage_detection_summary.log", 'w') as f:
    f.write("Prophage Detection Pipeline Summary\\n")
    f.write("=" * 50 + "\\n\\n")

    summary_files = [f for f in glob.glob("*_summary.txt") if os.path.exists(f)]
    total_stats, tool_stats = parse_summary_files(summary_files)

    f.write("Total genomes analyzed: " + str(len(summary_files)) + "\\n")
    f.write("Total prophage regions detected: " + str(total_stats['total_regions']) + "\\n")
    f.write("Total sequences extracted: " + str(total_sequences) + "\\n")
    f.write("Total base pairs in prophage sequences: " + str(total_bp) + "\\n\\n")
    
    f.write("Tool Statistics:\\n")
    f.write("-" * 20 + "\\n")
    for tool, count in tool_stats.items():
        f.write(tool + ": " + str(count) + " predictions\\n")
        
    f.write("\\nOutput Files:\\n")
    f.write("-" * 20 + "\\n")
    f.write("All prophage sequences: All_prophage_sequences.fasta\\n")
    f.write("All prophage coordinates: All_prophage_coordinates.tsv\\n")
EOF

        # Execute script with singularity
        singularity exec --bind \$(pwd):\$(pwd) ${container_path} python3 prophage_summary.py
        """
    else if (workflow.profile.contains('conda'))
        """
        # Create Python script
        cat > prophage_summary.py << 'EOF'
#!/usr/bin/env python3
import os
import glob
import pandas as pd
from collections import defaultdict

def parse_summary_files(summary_files):
    total_stats = defaultdict(int)
    tool_stats = defaultdict(int)
    
    for summary_file in summary_files:
        with open(summary_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "Total consolidated regions:" in line:
                    total_stats['total_regions'] += int(line.split(":")[1].strip())
                elif "Number of sequences extracted:" in line:
                    total_stats['sequences_extracted'] += int(line.split(":")[1].strip())
                elif "geNomad:" in line:
                    count = int(line.split(":")[1].strip())
                    tool_stats['geNomad'] += count
                elif "VIBRANT:" in line:
                    count = int(line.split(":")[1].strip())
                    tool_stats['VIBRANT'] += count

    return total_stats, tool_stats

def count_and_combine_sequences(sequence_files, output_fasta):
    total_sequences = 0
    total_bp = 0
    
    with open(output_fasta, 'w') as outf:
        for fasta in sequence_files:
            if os.path.exists(fasta) and os.path.getsize(fasta) > 0:
                with open(fasta, 'r') as f:
                    for line in f:
                        outf.write(line)
                        if line.startswith('>'):
                            total_sequences += 1
                        else:
                            total_bp += len(line.strip())
                            
    return total_sequences, total_bp

def combine_coordinates(coordinate_files, output_tsv):
    dfs = []
    for coord_file in coordinate_files:
        if os.path.exists(coord_file) and os.path.getsize(coord_file) > 0:
            df = pd.read_csv(coord_file, sep='\\t')
            dfs.append(df)
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_csv(output_tsv, sep='\\t', index=False)
    else:
        pd.DataFrame(columns=['Folder', 'Contig', 'Start', 'End']).to_csv(
            output_tsv, sep='\\t', index=False)

# Main execution
sequence_files = [f for f in glob.glob("*_prophage_sequences.fasta") if os.path.exists(f)]
total_sequences, total_bp = count_and_combine_sequences(sequence_files, "All_prophage_sequences.fasta")

coordinate_files = [f for f in glob.glob("*_consolidated_coordinates.tsv") if os.path.exists(f)]
combine_coordinates(coordinate_files, "All_prophage_coordinates.tsv")

with open("Prophage_detection_summary.log", 'w') as f:
    f.write("Prophage Detection Pipeline Summary\\n")
    f.write("=" * 50 + "\\n\\n")

    summary_files = [f for f in glob.glob("*_summary.txt") if os.path.exists(f)]
    total_stats, tool_stats = parse_summary_files(summary_files)

    f.write("Total genomes analyzed: " + str(len(summary_files)) + "\\n")
    f.write("Total prophage regions detected: " + str(total_stats['total_regions']) + "\\n")
    f.write("Total sequences extracted: " + str(total_sequences) + "\\n")
    f.write("Total base pairs in prophage sequences: " + str(total_bp) + "\\n\\n")
    
    f.write("Tool Statistics:\\n")
    f.write("-" * 20 + "\\n")
    for tool, count in tool_stats.items():
        f.write(tool + ": " + str(count) + " predictions\\n")
        
    f.write("\\nOutput Files:\\n")
    f.write("-" * 20 + "\\n")
    f.write("All prophage sequences: All_prophage_sequences.fasta\\n")
    f.write("All prophage coordinates: All_prophage_coordinates.tsv\\n")
EOF

        # Execute script with conda environment
        python3 prophage_summary.py
        """
    else
        error "Unsupported backend. Please use either 'conda' or 'singularity' profile."
}