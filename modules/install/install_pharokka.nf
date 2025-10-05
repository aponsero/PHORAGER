process INSTALL_PHAROKKA {
    tag "Installing Pharokka"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "pharokka_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['pharokka']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for pharokka"
    }
    if (!verification_cmd) {
        error "Missing verification_cmd in container_specs for pharokka"
    }
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing Pharokka via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling Pharokka container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Pharokka container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        singularity exec ${container_path} ${verification_cmd} > pharokka_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" pharokka_test.txt | head -1)
            
            echo "Pharokka installation completed successfully." > pharokka_install_check.log
            echo "Pharokka version: \$version_line" >> pharokka_install_check.log
            echo "Installation method: Singularity" >> pharokka_install_check.log
            echo "Container: ${container_path}" >> pharokka_install_check.log
            echo "Installation date: \$(date)" >> pharokka_install_check.log
        else
            echo "ERROR: Pharokka installation verification failed" > pharokka_install_check.log
            echo "Error details: \$(cat pharokka_test.txt)" >> pharokka_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing Pharokka via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > pharokka_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" pharokka_test.txt | head -1)
            
            echo "Pharokka installation completed successfully." > pharokka_install_check.log
            echo "Pharokka version: \$version_line" >> pharokka_install_check.log
            echo "Installation method: Conda" >> pharokka_install_check.log
            echo "Installation date: \$(date)" >> pharokka_install_check.log
        else
            echo "ERROR: Pharokka installation verification failed" > pharokka_install_check.log
            echo "Error details: \$(cat pharokka_test.txt)" >> pharokka_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > pharokka_install_check.log
        exit 1
        """
}