process INSTALL_PHOLD {
    tag "Installing PHOLD"
    label "conda_install"
    publishDir "${db_location}", mode: 'copy', enabled: !conda_only

    input:
    path db_location
    val conda_only

    output:
    path { conda_only ? "${db_location}" : "phold_database" }, emit: db_dir

    script:
    def success_log = "${db_location}/phold_install_check.log"
    
    if (conda_only)
        """
        echo "PHOLD conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """
        # Create database directory
        mkdir -p phold_database
        
        # Install PHOLD database
        phold install -d phold_database
        
        echo "PHOLD installation completed successfully." > "${db_location}/phold_install_check.log"
        """
}