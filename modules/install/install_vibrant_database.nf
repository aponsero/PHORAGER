process INSTALL_VIBRANT_DATABASE {
    tag "Installing VIBRANT Database"
    label "database_install"
    publishDir "${params.installation_logs_dir}", mode: 'copy'

    input:
    path database_location

    output:
    path "vibrant_database_install_check.log", emit: install_check

    script:
    def db_spec = params.database_specs['vibrant']
    def db_path = "${database_location}/${db_spec.directory}"
    def key_file = db_spec.key_file
    def expected_size = db_spec.expected_size_gb
    def description = db_spec.description

    // Validate required configuration
    if (!key_file) {
        error "Missing key_file in database_specs for vibrant"
    }

    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Installing VIBRANT database via manual construction (Singularity)..."
        
        mkdir -p ${database_location}
        WORK_DIR="$PWD"
        
        if [ -f "${db_path}/databases/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "VIBRANT database already exists, skipping download."
        else
            echo "Setting up VIBRANT database via manual construction..."
            
            rm -rf ${db_path}
            mkdir -p ${db_path}
            mkdir -p ${db_path}/databases
            mkdir -p ${db_path}/files
            cd ${db_path}
            
            # Step 1: Download source databases
            echo "Downloading source databases (VOG, Pfam, KEGG)..."
            wget --no-check-certificate -O vog.hmm.tar.gz "http://fileshare.csb.univie.ac.at/vog/vog94/vog.hmm.tar.gz"
            wget --no-check-certificate -O Pfam-A.hmm.gz "https://ftp.ebi.ac.uk/pub/databases/Pfam/releases/Pfam32.0/Pfam-A.hmm.gz"
            wget -O profiles.tar.gz "ftp://ftp.genome.jp/pub/db/kofam/archives/2019-08-10/profiles.tar.gz"
            
            # Step 2: Download profile filter files
            echo "Downloading VIBRANT profile filters..."
            mkdir -p profile_names
            wget --no-check-certificate -q -O profile_names/VIBRANT_vog_profiles.txt "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/databases/profile_names/VIBRANT_vog_profiles.txt"
            wget --no-check-certificate -q -O profile_names/VIBRANT_kegg_profiles.txt "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/databases/profile_names/VIBRANT_kegg_profiles.txt"
            
            # Step 2b: Download VIBRANT support files
            echo "Downloading VIBRANT support files..."
            wget --no-check-certificate -q -O files/VIBRANT_AMGs.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_AMGs.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_categories.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_categories.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_KEGG_pathways_summary.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_KEGG_pathways_summary.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_machine_model.sav "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_machine_model.sav"
            wget --no-check-certificate -q -O files/VIBRANT_names.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_names.tsv"

            # Verify all downloads completed
            if [ ! -f "vog.hmm.tar.gz" ] || [ ! -f "Pfam-A.hmm.gz" ] || [ ! -f "profiles.tar.gz" ] || [ ! -s "profile_names/VIBRANT_vog_profiles.txt" ] || [ ! -s "profile_names/VIBRANT_kegg_profiles.txt" ]; then
                echo "ERROR: Failed to download required VIBRANT database files"
                exit 1
            fi

            # Verify support files downloaded
            if [ ! -f "files/VIBRANT_AMGs.tsv" ] || [ ! -f "files/VIBRANT_categories.tsv" ] || [ ! -f "files/VIBRANT_KEGG_pathways_summary.tsv" ] || [ ! -f "files/VIBRANT_machine_model.sav" ] || [ ! -f "files/VIBRANT_names.tsv" ]; then
                echo "ERROR: Failed to download required VIBRANT support files"
                exit 1
            fi
            
            # Step 3: Extract archives
            echo "Extracting downloaded archives..."
            tar -xzf vog.hmm.tar.gz --overwrite-dir
            gunzip Pfam-A.hmm.gz
            tar -xzf profiles.tar.gz --overwrite-dir
            
            # Step 4: Concatenate profiles
            echo "Concatenating individual HMM profiles..."
            for v in VOG*.hmm; do cat "\$v" >> vog_temp.HMM; done
            for k in profiles/K*.hmm; do cat "\$k" >> kegg_temp.HMM; done
            mv Pfam-A.hmm Pfam-A_v32.HMM
            
            # Step 5: Filter profiles using VIBRANT selections
            echo "Filtering profiles using VIBRANT selections..."
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-vibrant-1.2.1--hdfd78af_4.img \\
                hmmfetch -o VOGDB94_phage.HMM -f vog_temp.HMM profile_names/VIBRANT_vog_profiles.txt
            
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-vibrant-1.2.1--hdfd78af_4.img \\
                hmmfetch -o KEGG_profiles_prokaryotes.HMM -f kegg_temp.HMM profile_names/VIBRANT_kegg_profiles.txt
            
            # Step 6: Press all HMM databases (avoiding the parallelism bug)
            echo "Creating HMM indexes (sequential to avoid parallelism bugs)..."
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-vibrant-1.2.1--hdfd78af_4.img \\
                hmmpress VOGDB94_phage.HMM
            
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-vibrant-1.2.1--hdfd78af_4.img \\
                hmmpress KEGG_profiles_prokaryotes.HMM
            
            singularity exec ${params.singularity_cache_dir}/quay.io-biocontainers-vibrant-1.2.1--hdfd78af_4.img \\
                hmmpress Pfam-A_v32.HMM

            # move results to databases directory
            mv KEGG_profiles_prokaryotes.HMM* databases
            mv Pfam-A_v32.HMM* databases
            mv VOGDB94_phage.HMM* databases
            mv profile_names databases
            
            # Step 7: Verify final databases and profile counts
            echo "Verifying database construction..."
            
            # Check files exist
            if [ ! -f "databases/VOGDB94_phage.HMM" ] || [ ! -f "databases/KEGG_profiles_prokaryotes.HMM" ] || [ ! -f "databases/Pfam-A_v32.HMM" ]; then
                echo "ERROR: Missing final HMM files after construction"
                exit 1
            fi
            
            # Check profile counts
            vog_count=\$(grep -c "NAME" databases/VOGDB94_phage.HMM)
            kegg_count=\$(grep -c "NAME" databases/KEGG_profiles_prokaryotes.HMM)
            pfam_count=\$(grep -c "NAME" databases/Pfam-A_v32.HMM)
            
            echo "Profile counts: VOG=\$vog_count, KEGG=\$kegg_count, Pfam=\$pfam_count"
            
            # Verify expected counts (from test results)
            if [ "\$vog_count" != "19181" ] && [ "\$vog_count" != "19182" ]; then
                echo "WARNING: Unexpected VOG profile count: \$vog_count (expected ~19182)"
            fi
            if [ "\$kegg_count" != "10032" ] && [ "\$kegg_count" != "10033" ]; then
                echo "WARNING: Unexpected KEGG profile count: \$kegg_count (expected ~10033)"
            fi
            if [ "\$pfam_count" != "17929" ]; then
                echo "WARNING: Unexpected Pfam profile count: \$pfam_count (expected 17929)"
            fi
            
            # Verify all HMM indexes exist in databases directory
            for hmm_file in VOGDB94_phage.HMM KEGG_profiles_prokaryotes.HMM Pfam-A_v32.HMM; do
                if [ ! -f "databases/\${hmm_file}.h3f" ] || [ ! -f "databases/\${hmm_file}.h3i" ] || [ ! -f "databases/\${hmm_file}.h3m" ] || [ ! -f "databases/\${hmm_file}.h3p" ]; then
                    echo "ERROR: Incomplete HMM indexes for \${hmm_file}"
                    exit 1
                fi
            done
            
            # Verify support files exist
            if [ ! -f "files/VIBRANT_AMGs.tsv" ] || [ ! -f "files/VIBRANT_categories.tsv" ] || [ ! -f "files/VIBRANT_KEGG_pathways_summary.tsv" ] || [ ! -f "files/VIBRANT_machine_model.sav" ] || [ ! -f "files/VIBRANT_names.tsv" ]; then
                echo "ERROR: Missing VIBRANT support files"
                exit 1
            fi
            
            # Step 8: Cleanup intermediate files
            echo "Cleaning up intermediate files..."
            rm -f vog.hmm.tar.gz Pfam-A.hmm.gz profiles.tar.gz
            rm -f vog_temp.HMM kegg_temp.HMM
            rm -f VOG*.hmm
            rm -rf profiles
            
            touch ".download_complete"
            echo "VIBRANT database construction completed successfully."
        fi
        
        if [ -f "${db_path}/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        cd $WORK_DIR
        echo "VIBRANT database installation completed successfully." > vibrant_database_install_check.log
        echo "Database location: ${db_path}" >> vibrant_database_install_check.log
        echo "Key file: ${key_file} verified" >> vibrant_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> vibrant_database_install_check.log
        echo "Installation method: Singularity (Manual database construction)" >> vibrant_database_install_check.log
        echo "Installation date: \$(date)" >> vibrant_database_install_check.log
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Installing VIBRANT database via manual construction (Conda)..."
        
        mkdir -p ${database_location}
        WORK_DIR="$PWD"
        
        if [ -f "${db_path}/databases/${key_file}" ] && [ -f "${db_path}/.download_complete" ]; then
            echo "VIBRANT database already exists, skipping download."
        else
            echo "Setting up VIBRANT database via manual construction..."
            
            rm -rf ${db_path}
            mkdir -p ${db_path}/databases
            mkdir -p ${db_path}/files
            cd ${db_path}
            
            # Step 1: Download source databases
            echo "Downloading source databases (VOG, Pfam, KEGG)..."
            wget --no-check-certificate -O vog.hmm.tar.gz "http://fileshare.csb.univie.ac.at/vog/vog94/vog.hmm.tar.gz"
            wget --no-check-certificate -O Pfam-A.hmm.gz "https://ftp.ebi.ac.uk/pub/databases/Pfam/releases/Pfam32.0/Pfam-A.hmm.gz"
            wget -O profiles.tar.gz "ftp://ftp.genome.jp/pub/db/kofam/archives/2019-08-10/profiles.tar.gz"
            
            # Step 2: Download profile filters and support files
            echo "Downloading VIBRANT profile filters and support files..."
            mkdir -p profile_names
            wget --no-check-certificate -q -O profile_names/VIBRANT_vog_profiles.txt "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/databases/profile_names/VIBRANT_vog_profiles.txt"
            wget --no-check-certificate -q -O profile_names/VIBRANT_kegg_profiles.txt "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/databases/profile_names/VIBRANT_kegg_profiles.txt"
            
            wget --no-check-certificate -q -O files/VIBRANT_AMGs.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_AMGs.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_categories.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_categories.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_KEGG_pathways_summary.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_KEGG_pathways_summary.tsv"
            wget --no-check-certificate -q -O files/VIBRANT_machine_model.sav "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_machine_model.sav"
            wget --no-check-certificate -q -O files/VIBRANT_names.tsv "https://raw.githubusercontent.com/AnantharamanLab/VIBRANT/master/files/VIBRANT_names.tsv"
            
            # Verify downloads and extract
            if [ ! -f "vog.hmm.tar.gz" ] || [ ! -f "Pfam-A.hmm.gz" ] || [ ! -f "profiles.tar.gz" ]; then
                echo "ERROR: Failed to download required database files"
                exit 1
            fi
            
            # Step 3: Extract and process using conda environment
            echo "Extracting and processing databases..."
            tar -xzf vog.hmm.tar.gz
            gunzip Pfam-A.hmm.gz
            tar -xzf profiles.tar.gz
            
            for v in VOG*.hmm; do cat "\$v" >> vog_temp.HMM; done
            for k in profiles/K*.hmm; do cat "\$k" >> kegg_temp.HMM; done
            
            # Step 4: Filter and press using conda environment
            echo "Filtering and pressing databases..."
            hmmfetch -o VOGDB94_phage.HMM -f vog_temp.HMM profile_names/VIBRANT_vog_profiles.txt
            hmmfetch -o KEGG_profiles_prokaryotes.HMM -f kegg_temp.HMM profile_names/VIBRANT_kegg_profiles.txt
            
            # Move to databases directory
            mv VOGDB94_phage.HMM databases/
            mv KEGG_profiles_prokaryotes.HMM databases/
            mv Pfam-A.hmm databases/Pfam-A_v32.HMM
            mv profile_names databases
            
            # Press databases
            hmmpress databases/VOGDB94_phage.HMM
            hmmpress databases/KEGG_profiles_prokaryotes.HMM
            hmmpress databases/Pfam-A_v32.HMM
            
            # Step 5: Verify and cleanup
            if [ ! -f "databases/VOGDB94_phage.HMM" ] || [ ! -f "databases/KEGG_profiles_prokaryotes.HMM" ] || [ ! -f "databases/Pfam-A_v32.HMM" ]; then
                echo "ERROR: Missing final HMM files after construction"
                exit 1
            fi
            
            # Verify support files
            if [ ! -f "files/VIBRANT_AMGs.tsv" ] || [ ! -f "files/VIBRANT_categories.tsv" ] || [ ! -f "files/VIBRANT_KEGG_pathways_summary.tsv" ] || [ ! -f "files/VIBRANT_machine_model.sav" ] || [ ! -f "files/VIBRANT_names.tsv" ]; then
                echo "ERROR: Missing VIBRANT support files"
                exit 1
            fi
            
            # Cleanup
            rm -f vog.hmm.tar.gz Pfam-A.hmm.gz profiles.tar.gz vog_temp.HMM kegg_temp.HMM VOG*.hmm
            rm -rf profiles
            
            touch ".download_complete"
            echo "VIBRANT database construction completed successfully."
        fi
        
        if [ -f "${db_path}/databases/${key_file}" ]; then
            actual_size=\$(du -sh "${db_path}" | cut -f1)
        else
            actual_size="Unknown"
        fi
        
        cd $WORK_DIR
        echo "VIBRANT database installation completed successfully." > vibrant_database_install_check.log
        echo "Database location: ${db_path}" >> vibrant_database_install_check.log
        echo "Key file: databases/${key_file} verified" >> vibrant_database_install_check.log
        echo "Database size: \${actual_size} (expected: ~${expected_size}GB)" >> vibrant_database_install_check.log
        echo "Installation method: Conda (Manual database construction)" >> vibrant_database_install_check.log
        echo "Installation date: \$(date)" >> vibrant_database_install_check.log
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" > vibrant_database_install_check.log
        exit 1
        """
}