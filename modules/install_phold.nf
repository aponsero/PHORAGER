process INSTALL_PHOLD {
    publishDir "${params.global_db_location}", mode: 'copy'

    input:
    val db_location

    output:
    path "phold_database", emit: db_dir

    script:
    """
    # Create database directory
    mkdir -p phold_database
    
    # Install PHOLD database
    phold install -d phold_database
    """
}
