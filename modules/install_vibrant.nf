process INSTALL_VIBRANT {
    input:
    path db_location

    output:
    path "${db_location}", emit: vibrant_db

    script:
    """    
    # Download VIBRANT database
    mkdir -p ${db_location}/vibrant_database
    download-db.sh ${db_location}/vibrant_database
    
    # Create a test command to verify VIBRANT installation
    VIBRANT_run.py -h > ${db_location}/vibrant_install_check.log
    """
}
