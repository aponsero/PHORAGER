process INSTALL_CHECKV {
    tag "Installing CheckV"
    label "conda_install"
    publishDir "${db_location}/checkv_database", mode: 'copy', enabled: !params.conda_only

    input:
    path db_location
    val conda_only

    output:
    path { conda_only ? "${db_location}" : "checkv-db-v1.5" }, emit: db_dir

    script:
    def success_log = "${db_location}/checkv_install_check.log"
    
    if (conda_only)
        """
        echo "CheckV conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """
        # Download CheckV database in the work directory
        checkv download_database .
        
        echo "CheckV installation completed successfully." > "${db_location}/checkv_install_check.log"
        """
}