process INSTALL_CHECKM2 {
    tag "Installing CheckM2"
    label "conda_install"

    input:
    path db_location
    val conda_only

    output:
    path "${db_location}", emit: checkm2_db

    script:
    def success_log = "${db_location}/checkm2_install_check.log"
    
    if (conda_only)
        """
        echo "CheckM2 conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """
        # Download and install the CheckM2 database
        checkm2 database --download --path ${db_location}
        
        echo "CheckM2 installation completed successfully." > ${success_log}
        """
}