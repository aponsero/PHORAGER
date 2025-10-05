process INSTALL_PARSING_ENV {
    tag "Installing Parsing Environment"
    label "tool_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path install_location

    output:
    path "parsing_env_install_check.log", emit: install_check

    script:
    // Get tool specifications from config
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    def verification_cmd = tool_spec.verification_cmd
    def version_pattern = tool_spec.version_pattern
    
    // Detect backend by profile name since we're doing manual container management
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing Parsing Environment via Singularity container..."
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling Parsing Environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing Environment container already exists, skipping pull."
        fi
        
        # Manual singularity execution
        export MPLCONFIGDIR=/tmp/matplotlib_config
        singularity exec ${container_path} ${verification_cmd} > parsing_env_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" parsing_env_test.txt | head -1)
            
            echo "Parsing Environment installation completed successfully." > parsing_env_install_check.log
            echo "Parsing Environment version: \$version_line" >> parsing_env_install_check.log
            echo "Installation method: Singularity" >> parsing_env_install_check.log
            echo "Container: ${container_path}" >> parsing_env_install_check.log
            echo "Installation date: \$(date)" >> parsing_env_install_check.log
        else
            echo "ERROR: Parsing Environment installation verification failed" > parsing_env_install_check.log
            echo "Error details: \$(cat parsing_env_test.txt)" >> parsing_env_install_check.log
            exit 1
        fi
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing Parsing Environment via Conda environment..."
        
        # Test installation using verification command from config
        ${verification_cmd} > parsing_env_test.txt 2>&1
        
        # Check if command was found (exit status should be 0 or 1, not 127)
        if [ \$? -ne 127 ]; then
            # Extract version from the output
            version_line=\$(grep "${version_pattern}" parsing_env_test.txt | head -1)
            
            echo "Parsing Environment installation completed successfully." > parsing_env_install_check.log
            echo "Parsing Environment version: \$version_line" >> parsing_env_install_check.log
            echo "Installation method: Conda" >> parsing_env_install_check.log
            echo "Installation date: \$(date)" >> parsing_env_install_check.log
        else
            echo "ERROR: Parsing Environment installation verification failed" > parsing_env_install_check.log
            echo "Error details: \$(cat parsing_env_test.txt)" >> parsing_env_install_check.log
            exit 1
        fi
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > parsing_env_install_check.log
        exit 1
        """
}