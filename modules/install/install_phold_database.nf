process INSTALL_PHOLD_DATABASE {
    tag "Installing Phold Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "phold_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['phold']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def download_cmd = db_spec.download_command
    def description = db_spec.description

    // Validate required configuration
    if (!download_cmd) {
        error "Missing download_command in database_specs for phold"
    }
    if (!key_file) {
        error "Missing key_file in database_specs for phold"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing Phold database via Singularity..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "Phold database already exists, skipping download."
        else
            echo "Downloading Phold database using tool command..."
            
            rm -rf ${db_path}
            mkdir -p ${db_path}
            
            # Use Phold container to install database
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-phold-0.2.0--pyhdfd78af_0.img \\
                phold install -d ${db_path}
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after database installation"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database installation completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "Phold database installation completed successfully." > phold_database_install_check.log
        echo "Database location: ${db_path}" >> phold_database_install_check.log
        echo "Key file: ${key_file} verified" >> phold_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> phold_database_install_check.log
        echo "Installation method: Singularity (tool command)" >> phold_database_install_check.log
        echo "Installation date: \$(date)" >> phold_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing Phold database via Conda..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "Phold database already exists, skipping download."
        else
            echo "Downloading Phold database using tool command..."
            
            rm -rf ${db_path}
            mkdir -p ${db_path}
            
            # Use conda environment to install database
            phold install -d ${db_path}
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after database installation"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database installation completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "Phold database installation completed successfully." > phold_database_install_check.log
        echo "Database location: ${db_path}" >> phold_database_install_check.log
        echo "Key file: ${key_file} verified" >> phold_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> phold_database_install_check.log
        echo "Installation method: Conda (tool command)" >> phold_database_install_check.log
        echo "Installation date: \$(date)" >> phold_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > phold_database_install_check.log
        exit 1
        """
}