process INSTALL_GENOMAD {
    input:
    path db_location

    output:
    path "${db_location}", emit: genomad_db

    script:
    """
    # Create a directory for geNomad database
    mkdir -p ${db_location}/geNomad_database

    # Download database directly to the specified path
    genomad download-database ${db_location}/geNomad_database

    # Create installation check log
    genomad --help > ${db_location}/genomad_install_check.log
    """
}
