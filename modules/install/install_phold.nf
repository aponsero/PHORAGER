process INSTALL_PHOLD {
    tag "Installing Phold"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "phold_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['phold']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for phold"
    }
    if (!verification_cmd) {
        error "Missing verification_cmd in container_specs for phold"
    }
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing Phold via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling Phold container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Phold container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        singularity exec ${container_path} ${verification_cmd} > phold_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" phold_test.txt | head -1)
            
            echo "Phold installation completed successfully." > phold_install_check.log
            echo "Phold version: \$version_line" >> phold_install_check.log
            echo "Installation method: Singularity" >> phold_install_check.log
            echo "Container: ${container_path}" >> phold_install_check.log
            echo "Installation date: \$(date)" >> phold_install_check.log
        else
            echo "ERROR: Phold installation verification failed" > phold_install_check.log
            echo "Error details: \$(cat phold_test.txt)" >> phold_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing Phold via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > phold_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" phold_test.txt | head -1)
            
            echo "Phold installation completed successfully." > phold_install_check.log
            echo "Phold version: \$version_line" >> phold_install_check.log
            echo "Installation method: Conda" >> phold_install_check.log
            echo "Installation date: \$(date)" >> phold_install_check.log
        else
            echo "ERROR: Phold installation verification failed" > phold_install_check.log
            echo "Error details: \$(cat phold_test.txt)" >> phold_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > phold_install_check.log
        exit 1
        """
}