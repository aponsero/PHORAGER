process INSTALL_VIBRANT {
    tag "Installing VIBRANT"
    label "conda_install"

    input:
    path db_location
    val conda_only

    output:
    path "${db_location}", emit: vibrant_db

    script:
    def success_log = "${db_location}/vibrant_install_check.log"
    
    if (conda_only)
        """
        echo "VIBRANT conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """    
        # Download VIBRANT database
        mkdir -p ${db_location}/vibrant_database
        download-db.sh ${db_location}/vibrant_database
        
        echo "VIBRANT installation completed successfully." > ${success_log}
        """
}