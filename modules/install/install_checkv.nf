process INSTALL_CHECKV {
    tag "Installing CheckV"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "checkv_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['checkv']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for checkv"
    }
    if (!verification_cmd) {
        error "Missing verification_cmd in container_specs for checkv"
    }
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing CheckV via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling CheckV container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "CheckV container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        singularity exec ${container_path} ${verification_cmd} > checkv_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" checkv_test.txt | head -1)
            
            echo "CheckV installation completed successfully." > checkv_install_check.log
            echo "CheckV version: \$version_line" >> checkv_install_check.log
            echo "Installation method: Singularity" >> checkv_install_check.log
            echo "Container: ${container_path}" >> checkv_install_check.log
            echo "Installation date: \$(date)" >> checkv_install_check.log
        else
            echo "ERROR: CheckV installation verification failed" > checkv_install_check.log
            echo "Error details: \$(cat checkv_test.txt)" >> checkv_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing CheckV via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > checkv_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" checkv_test.txt | head -1)
            
            echo "CheckV installation completed successfully." > checkv_install_check.log
            echo "CheckV version: \$version_line" >> checkv_install_check.log
            echo "Installation method: Conda" >> checkv_install_check.log
            echo "Installation date: \$(date)" >> checkv_install_check.log
        else
            echo "ERROR: CheckV installation verification failed" > checkv_install_check.log
            echo "Error details: \$(cat checkv_test.txt)" >> checkv_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > checkv_install_check.log
        exit 1
        """
}