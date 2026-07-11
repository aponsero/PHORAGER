process SPLIT_FASTA {
    tag "Splitting ${fasta_file.simpleName}"
    publishDir "${params.outdir}/3.Annotation/Anno2_SplitSequences", mode: 'copy'

    input:
    path fasta_file

    output:
    path "*.fasta", emit: split_fastas
    path "file_list.txt", emit: file_list

    script:
    // This process uses the parsing_env (Python + BioPython)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url

    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for parsing_env"
    }
    
    // Detect backend by profile name
    if (workflow.profile.contains('singularity') || workflow.profile.contains('standard'))
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

# Read and split sequences - write directly to current directory
for record in SeqIO.parse("${fasta_file}", "fasta"):
    # Get sequence ID without spaces and create filename
    seq_id = record.id.split()[0]
    output_file = f"{seq_id}.fasta"
    
    # Write individual sequence to file
    with open(output_file, 'w') as out_handle:
        SeqIO.write(record, out_handle, "fasta")

print(f"Successfully split sequences from ${fasta_file}")
EOF
        
        # Run the Python script using the container
        singularity exec --no-home ${container_path} python3 split_sequences.py
        
        # Create file list
        ls *.fasta > file_list.txt
        
        # Verify output files were created
        file_count=\$(ls *.fasta 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No FASTA files created"
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

# Read and split sequences - write directly to current directory
for record in SeqIO.parse("${fasta_file}", "fasta"):
    # Get sequence ID without spaces and create filename
    seq_id = record.id.split()[0]
    output_file = f"{seq_id}.fasta"
    
    # Write individual sequence to file
    with open(output_file, 'w') as out_handle:
        SeqIO.write(record, out_handle, "fasta")

print(f"Successfully split sequences from ${fasta_file}")
EOF
        
        # Run the Python script using conda environment
        python3 split_sequences.py
        
        # Create file list
        ls *.fasta > file_list.txt
        
        # Verify output files were created
        file_count=\$(ls *.fasta 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No FASTA files created"
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
