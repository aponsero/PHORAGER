process INSTALL_PHAROKKA_DATABASE {
    tag "Installing Pharokka Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "pharokka_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['pharokka']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def download_url = db_spec.download_url
    def description = db_spec.description

    // Validate required configuration
    if (!download_url) {
        error "Missing download_url in database_specs for pharokka"
    }
    if (!key_file) {
        error "Missing key_file in database_specs for pharokka"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing Pharokka database via Singularity..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "Pharokka database already exists, skipping download."
        else
            echo "Downloading Pharokka database from Zenodo..."
            
            # rm -rf ${db_path}
            
            # Download database directly from Zenodo
            # wget --no-check-certificate -O ${database_location}/pharokka_v1.4.0_databases.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/pharokka_v1.4.0_databases.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/pharokka_v1.4.0_databases" ]; then
                mv "${database_location}/pharokka_v1.4.0_databases" "${db_path}"
            else
                echo "ERROR: Expected pharokka_v1.4.0_databases directory not found after extraction"
                exit 1
            fi
            
            # Remove the tar file to save space
            rm ${database_location}/pharokka_v1.4.0_databases.tar.gz
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and extraction"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "Pharokka database installation completed successfully." > pharokka_database_install_check.log
        echo "Database location: ${db_path}" >> pharokka_database_install_check.log
        echo "Key file: ${key_file} verified" >> pharokka_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> pharokka_database_install_check.log
        echo "Installation method: Singularity (Zenodo download)" >> pharokka_database_install_check.log
        echo "Installation date: \$(date)" >> pharokka_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing Pharokka database via Conda..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "Pharokka database already exists, skipping download."
        else
            echo "Downloading Pharokka database from Zenodo..."
            
            rm -rf ${db_path}
            
            # Download database directly from Zenodo
            wget --no-check-certificate -O ${database_location}/pharokka_v1.4.0_databases.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/pharokka_v1.4.0_databases.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/pharokka_v1.4.0_databases" ]; then
                mv "${database_location}/pharokka_v1.4.0_databases" "${db_path}"
            else
                echo "ERROR: Expected pharokka_v1.4.0_databases directory not found after extraction"
                exit 1
            fi
            
            # Remove the tar file to save space
            rm ${database_location}/pharokka_v1.4.0_databases.tar.gz
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and extraction"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "Pharokka database installation completed successfully." > pharokka_database_install_check.log
        echo "Database location: ${db_path}" >> pharokka_database_install_check.log
        echo "Key file: ${key_file} verified" >> pharokka_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> pharokka_database_install_check.log
        echo "Installation method: Conda (Zenodo download)" >> pharokka_database_install_check.log
        echo "Installation date: \$(date)" >> pharokka_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > pharokka_database_install_check.log
        exit 1
        """
}