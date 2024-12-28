process INSTALL_DREP {
    input:
    path db_location

    output:
    path "${db_location}", emit: drep_db

    script:
    """
    # Create a test command to verify dRep installation
    dRep -h > ${db_location}/drep_install_check.log
    """
}
