process INSTALL_CHECKM2_DATABASE {
    tag "Installing CheckM2 Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "checkm2_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['checkm2']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def download_url = db_spec.download_url
    def description = db_spec.description

    // Validate required configuration
    if (!download_url) {
        error "Missing download_url in database_specs for checkm2"
    }
    if (!key_file) {
        error "Missing key_file in database_specs for checkm2"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing CheckM2 database via Singularity..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "CheckM2 database already exists, skipping download."
        else
            echo "Downloading CheckM2 database from Zenodo..."
            
            rm -rf ${db_path}
            
            # Download database from configured URL
            wget -O ${database_location}/checkm2_database.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/checkm2_database.tar.gz -C ${database_location}
            
            # Remove the tar file to save space
            rm ${database_location}/checkm2_database.tar.gz
            rm ${database_location}/CONTENTS.json
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and extraction"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}/${key_file}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "CheckM2 database installation completed successfully." > checkm2_database_install_check.log
        echo "Database location: ${db_path}" >> checkm2_database_install_check.log
        echo "Key file: ${key_file} (size: \${actual_size}, expected: ~${expected_size}GB)" >> checkm2_database_install_check.log
        echo "Installation method: Singularity (Zenodo download)" >> checkm2_database_install_check.log
        echo "Installation date: \$(date)" >> checkm2_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing CheckM2 database via Conda..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "CheckM2 database already exists, skipping download."
        else
            echo "Downloading CheckM2 database from Zenodo..."
            
            rm -rf ${db_path}
            
            # Download database from configured URL
            wget -O ${database_location}/checkm2_database.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/checkm2_database.tar.gz -C ${database_location}
            
            # Remove the tar file and unwanted files
            rm ${database_location}/checkm2_database.tar.gz
            rm ${database_location}/CONTENTS.json
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and extraction"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}/${key_file}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "CheckM2 database installation completed successfully." > checkm2_database_install_check.log
        echo "Database location: ${db_path}" >> checkm2_database_install_check.log
        echo "Key file: ${key_file} (size: \${actual_size}, expected: ~${expected_size}GB)" >> checkm2_database_install_check.log
        echo "Installation method: Conda (Zenodo download)" >> checkm2_database_install_check.log
        echo "Installation date: \$(date)" >> checkm2_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > checkm2_database_install_check.log
        exit 1
        """
}