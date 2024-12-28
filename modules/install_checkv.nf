process INSTALL_CHECKV {
    publishDir "${db_location}/checkv_database", mode: 'copy'

    input:
    val db_location

    output:
    path "checkv-db-v1.5", emit: db_dir

    script:
    """
    # Download CheckV database in the work directory
    checkv download_database .
    """
}
