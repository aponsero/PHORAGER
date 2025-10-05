process INSTALL_GENOMAD {
    tag "Installing GenoMAD"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "genomad_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['genomad']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Validate required configuration
    if (!container_url) {
        error "Missing docker_url in container_specs for genomad"
    }
    if (!verification_cmd) {
        error "Missing verification_cmd in container_specs for genomad"
    }
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing GenoMAD via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling GenoMAD container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "GenoMAD container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        singularity exec ${container_path} ${verification_cmd} > genomad_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" genomad_test.txt | head -1)
            
            echo "GenoMAD installation completed successfully." > genomad_install_check.log
            echo "GenoMAD version: \$version_line" >> genomad_install_check.log
            echo "Installation method: Singularity" >> genomad_install_check.log
            echo "Container: ${container_path}" >> genomad_install_check.log
            echo "Installation date: \$(date)" >> genomad_install_check.log
        else
            echo "ERROR: GenoMAD installation verification failed" > genomad_install_check.log
            echo "Error details: \$(cat genomad_test.txt)" >> genomad_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing GenoMAD via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > genomad_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" genomad_test.txt | head -1)
            
            echo "GenoMAD installation completed successfully." > genomad_install_check.log
            echo "GenoMAD version: \$version_line" >> genomad_install_check.log
            echo "Installation method: Conda" >> genomad_install_check.log
            echo "Installation date: \$(date)" >> genomad_install_check.log
        else
            echo "ERROR: GenoMAD installation verification failed" > genomad_install_check.log
            echo "Error details: \$(cat genomad_test.txt)" >> genomad_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > genomad_install_check.log
        exit 1
        """
}