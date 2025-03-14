process INSTALL_GENOMAD {
    tag "Installing geNomad"
    label "conda_install"

    input:
    path db_location
    val conda_only

    output:
    path "${db_location}", emit: genomad_db

    script:
    def success_log = "${db_location}/genomad_install_check.log"
    
    if (conda_only)
        """
        echo "geNomad conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """
        # Create a directory for geNomad database
        mkdir -p ${db_location}/geNomad_database

        # Download database directly to the specified path
        genomad download-database ${db_location}/geNomad_database

        # Create installation check log
        echo "geNomad installation completed successfully." > ${success_log}
        """
}