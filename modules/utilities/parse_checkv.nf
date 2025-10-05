process PARSE_CHECKV {
    tag "Parsing CheckV results"
    publishDir "${params.outdir}/3.Annotation/Anno1_CheckV", mode: 'copy'

    input:
    path checkv_dir
    val min_length
    val quality_levels

    output:
    path "filtered_prophages.fasta", emit: filtered_fasta
    path "filter_summary.txt", emit: summary
    path "prophage_count.txt", emit: count

    script:
    // This process uses the parsing_env (Python + BioPython)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for parsing_env"
    }
    
    // Convert quality levels list to Python format - FIX: split by comma first
    def qualities = quality_levels.split(',').collect { "\"${it.trim()}\"" }.join(", ")
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Parse CheckV via Singularity container..."
        echo "CheckV directory: ${checkv_dir}"
        echo "Min length: ${min_length}"
        echo "Quality levels: ${quality_levels}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling parsing environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing environment container already exists, using cached version."
        fi
        
        # Create the Python script
        cat > parse_checkv.py << 'EOF'
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

# Verify input files exist
if not os.path.exists(quality_summary_file):
    print(f"ERROR: Quality summary file not found: {quality_summary_file}")
    exit(1)

# Filter prophages based on quality and length
filtered_prophages, header = filter_quality_summary(quality_summary_file, ${min_length}, ALLOWED_QUALITIES)

# Write count to file for workflow control
with open("prophage_count.txt", "w") as count_f:
    count_f.write(str(len(filtered_prophages)))

print(f"Filtered {len(filtered_prophages)} prophages based on quality and length criteria")

# If no prophages, still create valid empty outputs and warn
if len(filtered_prophages) == 0:
    print("")
    print("WARNING: No prophages passed the quality and length filters")
    print(f"  Minimum length: ${min_length}bp")
    print(f"  Quality levels: {', '.join(ALLOWED_QUALITIES)}")
    print("")

# Write summary
with open("filter_summary.txt", "w") as sum_f:
    sum_f.write("CheckV Filter Summary\\n")
    sum_f.write("===================\\n\\n")
    sum_f.write(f"Minimum length threshold: ${min_length}bp\\n")
    sum_f.write(f"Quality levels included: {', '.join(ALLOWED_QUALITIES)}\\n\\n")
    
    if len(filtered_prophages) == 0:
        sum_f.write("WARNING: No prophages passed the filters!\\n")
    else:
        sum_f.write("Filtered Prophages:\\n")
        sum_f.write(f"{'Contig ID':<40} {'Quality':<15} {'Length (bp)':<12}\\n")
        sum_f.write("-" * 67 + "\\n")
        for phage in filtered_prophages:
            sum_f.write(f"{phage[0]:<40} {phage[1]:<15} {phage[2]:<12}\\n")

# Function to extract sequences
def extract_sequences(fasta_file, filtered_ids, output_handle):
    if os.path.exists(fasta_file):
        print(f"Processing sequences from {fasta_file}")
        for record in SeqIO.parse(fasta_file, "fasta"):
            if any(f_id in record.id for f_id, _, _ in filtered_ids):
                SeqIO.write(record, output_handle, "fasta")
    else:
        print(f"Warning: FASTA file not found: {fasta_file}")

# Write filtered sequences (will be empty if no prophages passed)
with open("filtered_prophages.fasta", "w") as out_f:
    extract_sequences(viruses_file, filtered_prophages, out_f)
    extract_sequences(proviruses_file, filtered_prophages, out_f)

print("CheckV parsing completed successfully")
EOF
        
        # Run the Python script using the container
        singularity exec ${container_path} python3 parse_checkv.py
        
        # Verify output files were created
        if [ ! -f "filtered_prophages.fasta" ]; then
            echo "ERROR: Filtered prophages FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "filter_summary.txt" ]; then
            echo "ERROR: Filter summary file not created"
            exit 1
        fi
        
        if [ ! -f "prophage_count.txt" ]; then
            echo "ERROR: Prophage count file not created"
            exit 1
        fi
        
        echo "Parse CheckV completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Parse CheckV via Conda environment..."
        echo "CheckV directory: ${checkv_dir}"
        echo "Min length: ${min_length}"
        echo "Quality levels: ${quality_levels}"
        
        # Create the Python script
        cat > parse_checkv.py << 'EOF'
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

# Verify input files exist
if not os.path.exists(quality_summary_file):
    print(f"ERROR: Quality summary file not found: {quality_summary_file}")
    exit(1)

# Filter prophages based on quality and length
filtered_prophages, header = filter_quality_summary(quality_summary_file, ${min_length}, ALLOWED_QUALITIES)

# Write count to file for workflow control
with open("prophage_count.txt", "w") as count_f:
    count_f.write(str(len(filtered_prophages)))

print(f"Filtered {len(filtered_prophages)} prophages based on quality and length criteria")

# If no prophages, still create valid empty outputs and warn
if len(filtered_prophages) == 0:
    print("")
    print("WARNING: No prophages passed the quality and length filters")
    print(f"  Minimum length: ${min_length}bp")
    print(f"  Quality levels: {', '.join(ALLOWED_QUALITIES)}")
    print("")

# Write summary
with open("filter_summary.txt", "w") as sum_f:
    sum_f.write("CheckV Filter Summary\\n")
    sum_f.write("===================\\n\\n")
    sum_f.write(f"Minimum length threshold: ${min_length}bp\\n")
    sum_f.write(f"Quality levels included: {', '.join(ALLOWED_QUALITIES)}\\n\\n")
    
    if len(filtered_prophages) == 0:
        sum_f.write("WARNING: No prophages passed the filters!\\n")
    else:
        sum_f.write("Filtered Prophages:\\n")
        sum_f.write(f"{'Contig ID':<40} {'Quality':<15} {'Length (bp)':<12}\\n")
        sum_f.write("-" * 67 + "\\n")
        for phage in filtered_prophages:
            sum_f.write(f"{phage[0]:<40} {phage[1]:<15} {phage[2]:<12}\\n")

# Function to extract sequences
def extract_sequences(fasta_file, filtered_ids, output_handle):
    if os.path.exists(fasta_file):
        print(f"Processing sequences from {fasta_file}")
        for record in SeqIO.parse(fasta_file, "fasta"):
            if any(f_id in record.id for f_id, _, _ in filtered_ids):
                SeqIO.write(record, output_handle, "fasta")
    else:
        print(f"Warning: FASTA file not found: {fasta_file}")

# Write filtered sequences (will be empty if no prophages passed)
with open("filtered_prophages.fasta", "w") as out_f:
    extract_sequences(viruses_file, filtered_prophages, out_f)
    extract_sequences(proviruses_file, filtered_prophages, out_f)

print("CheckV parsing completed successfully")
EOF
        
        # Run the Python script using conda environment
        python3 parse_checkv.py
        
        # Verify output files were created
        if [ ! -f "filtered_prophages.fasta" ]; then
            echo "ERROR: Filtered prophages FASTA file not created"
            exit 1
        fi
        
        if [ ! -f "filter_summary.txt" ]; then
            echo "ERROR: Filter summary file not created"
            exit 1
        fi
        
        if [ ! -f "prophage_count.txt" ]; then
            echo "ERROR: Prophage count file not created"
            exit 1
        fi
        
        echo "Parse CheckV completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}