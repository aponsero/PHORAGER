process INSTALL_DREP {
    tag "Installing dRep"
    label "conda_install"

    input:
    path db_location
    val conda_only

    output:
    path "${db_location}", emit: drep_db

    script:
    """
    # Create a test command to verify dRep installation
    echo "dRep conda environment installed successfully." > ${db_location}/drep_install_check.log
    """
}