process INSTALL_PHAROKKA {
    tag "Installing Pharokka"
    label "conda_install"
    publishDir "${db_location}", mode: 'copy', enabled: !params.conda_only

    input:
    path db_location
    val conda_only

    output:
    path { conda_only ? "${db_location}" : "pharokka_database" }, emit: db_dir

    script:
    def success_log = "${db_location}/pharokka_install_check.log"
    
    if (conda_only)
        """
        echo "Pharokka conda environment installed successfully. Database download skipped (--conda-only was used)." > ${success_log}
        """
    else
        """
        # Create database directory
        mkdir -p pharokka_database
        
        # Run database installation
        install_databases.py -o pharokka_database
        
        echo "Pharokka installation completed successfully." > "${db_location}/pharokka_install_check.log"
        """
}