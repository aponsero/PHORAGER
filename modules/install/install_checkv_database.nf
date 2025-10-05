process INSTALL_CHECKV_DATABASE {
    tag "Installing CheckV Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "checkv_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['checkv']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def download_url = db_spec.download_url
    def description = db_spec.description

    // Validate required configuration
    if (!download_url) {
        error "Missing download_url in database_specs for checkv"
    }
    if (!key_file) {
        error "Missing key_file in database_specs for checkv"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing CheckV database via Singularity..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "CheckV database already exists, skipping download."
        else
            echo "Downloading CheckV database from NERSC..."
            
            rm -rf ${db_path} #####
            
            # Download database directly from NERSC
            wget --no-check-certificate -O ${database_location}/checkv-db-v1.5.tar.gz "${download_url}" 
            
            # Extract the database
            tar -xzf ${database_location}/checkv-db-v1.5.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/checkv-db-v1.5" ]; then
                mv "${database_location}/checkv-db-v1.5" "${db_path}"
            else
                echo "ERROR: Expected checkv-db-v1.5 directory not found after extraction"
                exit 1
            fi
            
            # Build DIAMOND database using container
            echo "Building DIAMOND database..."
            cd "${db_path}/genome_db"
            
            # Use the CheckV container to build DIAMOND database
            singularity exec ${params.singularity_cache_dir}/checkv-env-1.0.sif \\
                diamond makedb --in checkv_reps.faa --db checkv_reps
            
            cd -
            
            # Remove the tar file to save space
            rm ${database_location}/checkv-db-v1.5.tar.gz
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and DIAMOND build"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download and build completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "CheckV database installation completed successfully." > checkv_database_install_check.log
        echo "Database location: ${db_path}" >> checkv_database_install_check.log
        echo "Key file: ${key_file} verified" >> checkv_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> checkv_database_install_check.log
        echo "Installation method: Singularity (NERSC download + DIAMOND build)" >> checkv_database_install_check.log
        echo "Installation date: \$(date)" >> checkv_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing CheckV database via Conda..."
        
        mkdir -p ${database_location}
        
        if [ -f "${db_path}/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "CheckV database already exists, skipping download."
        else
            echo "Downloading CheckV database from NERSC..."
            
            rm -rf ${db_path}
            
            # Download database directly from NERSC
            wget --no-check-certificate -O ${database_location}/checkv-db-v1.5.tar.gz "${download_url}"
            
            # Extract the database
            tar -xzf ${database_location}/checkv-db-v1.5.tar.gz -C ${database_location}
            
            # Move extracted contents to proper directory name
            if [ -d "${database_location}/checkv-db-v1.5" ]; then
                mv "${database_location}/checkv-db-v1.5" "${db_path}"
            else
                echo "ERROR: Expected checkv-db-v1.5 directory not found after extraction"
                exit 1
            fi
            
            # Build DIAMOND database using conda environment
            echo "Building DIAMOND database..."
            cd "${db_path}/genome_db"
            
            # Use conda environment to build DIAMOND database
            diamond makedb --in checkv_reps.faa --db checkv_reps
            
            cd -
            
            # Remove the tar file to save space
            rm ${database_location}/checkv-db-v1.5.tar.gz
            
            # Verify the key file exists
            if [ ! -f "${db_path}/${key_file}" ]; then
                echo "ERROR: Key file ${key_file} missing after download and DIAMOND build"
                exit 1
            fi
            
            touch "${db_path}/.download_complete"
            echo "Database download and build completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        echo "CheckV database installation completed successfully." > checkv_database_install_check.log
        echo "Database location: ${db_path}" >> checkv_database_install_check.log
        echo "Key file: ${key_file} verified" >> checkv_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> checkv_database_install_check.log
        echo "Installation method: Conda (NERSC download + DIAMOND build)" >> checkv_database_install_check.log
        echo "Installation date: \$(date)" >> checkv_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > checkv_database_install_check.log
        exit 1
        """
}