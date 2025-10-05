process INSTALL_GENOMAD_DATABASE {
    tag "Installing GenoMAD Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "genomad_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['genomad']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def download_url = db_spec.download_url
    def description = db_spec.description

    // Validate required configuration
    if (!download_url) {
        error "Missing download_url in database_specs for genomad"
    }
    if (!key_file) {
        error "Missing key_file in database_specs for genomad"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing GenoMAD database via Singularity..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "GenoMAD database already exists, skipping download."
        else
            echo "Downloading GenoMAD database from Zenodo..."
            
            rm -rf ${db_path}
            
            # Download database from configured URL
            wget -O ${database_location}/genomad_db_v1.9.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/genomad_db_v1.9.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/genomad_db" ]; then
                mv "${database_location}/genomad_db" "${db_path}"
            else
                echo "ERROR: Expected genomad_db directory not found after extraction"
                exit 1
            fi
            
            # Remove the tar file to save space
            rm ${database_location}/genomad_db_v1.9.tar.gz
            
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
        
        echo "GenoMAD database installation completed successfully." > genomad_database_install_check.log
        echo "Database location: ${db_path}" >> genomad_database_install_check.log
        echo "Key file: ${key_file} (size: \${actual_size}, expected: ~${expected_size}GB)" >> genomad_database_install_check.log
        echo "Installation method: Singularity (Zenodo download)" >> genomad_database_install_check.log
        echo "Installation date: \$(date)" >> genomad_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing GenoMAD database via Conda..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "GenoMAD database already exists, skipping download."
        else
            echo "Downloading GenoMAD database from Zenodo..."
            
            rm -rf ${db_path}
            
            # Download database from configured URL
            wget -O ${database_location}/genomad_db_v1.9.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/genomad_db_v1.9.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/genomad_db" ]; then
                mv "${database_location}/genomad_db" "${db_path}"
            else
                echo "ERROR: Expected genomad_db directory not found after extraction"
                exit 1
            fi
            
            # Remove the tar file to save space
            rm ${database_location}/genomad_db_v1.9.tar.gz
            
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
        
        echo "GenoMAD database installation completed successfully." > genomad_database_install_check.log
        echo "Database location: ${db_path}" >> genomad_database_install_check.log
        echo "Key file: ${key_file} (size: \${actual_size}, expected: ~${expected_size}GB)" >> genomad_database_install_check.log
        echo "Installation method: Conda (Zenodo download)" >> genomad_database_install_check.log
        echo "Installation date: \$(date)" >> genomad_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > genomad_database_install_check.log
        exit 1
        """
}