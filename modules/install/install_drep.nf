process INSTALL_DREP {
    tag "Installing dRep"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "drep_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['drep']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.docker_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing dRep via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling dRep container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "dRep container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        export MPLCONFIGDIR=/tmp/matplotlib_config
        singularity exec ${container_path} ${verification_cmd} > drep_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" drep_test.txt | head -1)
            
            echo "dRep installation completed successfully." > drep_install_check.log
            echo "dRep version: \$version_line" >> drep_install_check.log
            echo "Installation method: Singularity" >> drep_install_check.log
            echo "Container: ${container_path}" >> drep_install_check.log
            echo "Installation date: \$(date)" >> drep_install_check.log
        else
            echo "ERROR: dRep installation verification failed" > drep_install_check.log
            echo "Error details: \$(cat drep_test.txt)" >> drep_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing dRep via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > drep_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" drep_test.txt | head -1)
            
            echo "dRep installation completed successfully." > drep_install_check.log
            echo "dRep version: \$version_line" >> drep_install_check.log
            echo "Installation method: Conda" >> drep_install_check.log
            echo "Installation date: \$(date)" >> drep_install_check.log
        else
            echo "ERROR: dRep installation verification failed" > drep_install_check.log
            echo "Error details: \$(cat drep_test.txt)" >> drep_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > drep_install_check.log
        exit 1
        """
}