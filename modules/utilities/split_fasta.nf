process SPLIT_FASTA {
    tag "Splitting ${fasta_file.simpleName}"
    publishDir "${params.outdir}/3.Annotation/Anno2_SplitSequences", mode: 'copy'

    input:
    path fasta_file

    output:
    path "putative_prophage_sequences/*.fasta", emit: split_fastas

    script:
    // This process uses the parsing_env (Python + BioPython)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for parsing_env"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Split FASTA via Singularity container..."
        echo "Input fasta: ${fasta_file}"
        
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
        cat > split_sequences.py << 'EOF'
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

print(f"Successfully split sequences from ${fasta_file}")
EOF
        
        # Run the Python script using the container
        singularity exec ${container_path} python3 split_sequences.py
        
        # Verify output directory was created and contains files
        if [ ! -d "putative_prophage_sequences" ]; then
            echo "ERROR: Output directory 'putative_prophage_sequences' not created"
            exit 1
        fi
        
        file_count=\$(ls putative_prophage_sequences/*.fasta 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No FASTA files created in output directory"
            echo "Input file contents:"
            head -n 5 ${fasta_file}
            exit 1
        fi
        
        echo "Split FASTA completed successfully. Created \$file_count individual sequence files."
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Split FASTA via Conda environment..."
        echo "Input fasta: ${fasta_file}"
        
        # Create the Python script
        cat > split_sequences.py << 'EOF'
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

print(f"Successfully split sequences from ${fasta_file}")
EOF
        
        # Run the Python script using conda environment
        python3 split_sequences.py
        
        # Verify output directory was created and contains files
        if [ ! -d "putative_prophage_sequences" ]; then
            echo "ERROR: Output directory 'putative_prophage_sequences' not created"
            exit 1
        fi
        
        file_count=\$(ls putative_prophage_sequences/*.fasta 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No FASTA files created in output directory"
            echo "Input file contents:"
            head -n 5 ${fasta_file}
            exit 1
        fi
        
        echo "Split FASTA completed successfully. Created \$file_count individual sequence files."
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}