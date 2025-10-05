process FILTER_GENOMES {
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact2_FilteredGenomes", mode: 'copy'

    input:
    path quality_report
    val completeness_threshold
    val contamination_threshold

    output:
    path 'passed_genomes.txt', emit: passed
    path 'failed_genomes.txt', emit: failed

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running genome filtering via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling parsing environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing environment container already exists, using cached version."
        fi
        
        # Create Python script
        cat > filter_script.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd

# Read the quality report
df = pd.read_csv('${quality_report}', sep='\\t')

# Filter genomes based on thresholds
passed = df[(df['Completeness'] >= ${completeness_threshold}) & (df['Contamination'] <= ${contamination_threshold})]
failed = df[(df['Completeness'] < ${completeness_threshold}) | (df['Contamination'] > ${contamination_threshold})]

# Write passed genomes to file
with open('passed_genomes.txt', 'w') as f:
    for genome in passed['Name']:
        f.write(f"{genome}\\n")

# Write failed genomes to file
with open('failed_genomes.txt', 'w') as f:
    for genome in failed['Name']:
        f.write(f"{genome}\\n")

# Print summary
print("Genomes that passed the quality thresholds:")
print(passed['Name'].tolist())
print("Genomes that failed the quality thresholds:")
print(failed['Name'].tolist())
EOF

        # Run Python script using singularity
        singularity exec ${container_path} python3 filter_script.py
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running genome filtering via Conda environment..."
        
        # Create Python script
        cat > filter_script.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd

# Read the quality report
df = pd.read_csv('${quality_report}', sep='\\t')

# Filter genomes based on thresholds
passed = df[(df['Completeness'] >= ${completeness_threshold}) & (df['Contamination'] <= ${contamination_threshold})]
failed = df[(df['Completeness'] < ${completeness_threshold}) | (df['Contamination'] > ${contamination_threshold})]

# Write passed genomes to file
with open('passed_genomes.txt', 'w') as f:
    for genome in passed['Name']:
        f.write(f"{genome}\\n")

# Write failed genomes to file
with open('failed_genomes.txt', 'w') as f:
    for genome in failed['Name']:
        f.write(f"{genome}\\n")

# Print summary
print("Genomes that passed the quality thresholds:")
print(passed['Name'].tolist())
print("Genomes that failed the quality thresholds:")
print(failed['Name'].tolist())
EOF

        # Run Python script
        python3 filter_script.py
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}