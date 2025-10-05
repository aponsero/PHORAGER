process INSTALL_CHECKM2 {
    tag "Installing checkM2"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "checkm2_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['checkm2']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing checkm2 via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling checkm2 container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "checkm2 container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        singularity exec ${container_path} ${verification_cmd} > checkm2_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" checkm2_test.txt | head -1)
            
            echo "checkm2 installation completed successfully." > checkm2_install_check.log
            echo "checkm2 version: \$version_line" >> checkm2_install_check.log
            echo "Installation method: Singularity" >> checkm2_install_check.log
            echo "Container: ${container_path}" >> checkm2_install_check.log
            echo "Installation date: \$(date)" >> checkm2_install_check.log
        else
            echo "ERROR: checkm2 installation verification failed" > checkm2_install_check.log
            echo "Error details: \$(cat checkm2_test.txt)" >> checkm2_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing checkm2 via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > checkm2_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" checkm2_test.txt | head -1)
            
            echo "checkm2 installation completed successfully." > checkm2_install_check.log
            echo "checkm2 version: \$version_line" >> checkm2_install_check.log
            echo "Installation method: Conda" >> checkm2_install_check.log
            echo "Installation date: \$(date)" >> checkm2_install_check.log
        else
            echo "ERROR: checkm2 installation verification failed" > checkm2_install_check.log
            echo "Error details: \$(cat checkm2_test.txt)" >> checkm2_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > checkm2_install_check.log
        exit 1
        """
}