process INSTALL_PHAROKKA {
    publishDir "${params.global_db_location}", mode: 'copy'

    input:
    val db_location

    output:
    path "pharokka_database", emit: db_dir

    script:
    """
    # Create database directory
    mkdir -p pharokka_database
    
    # Run database installation
    install_databases.py -o pharokka_database
    """
}
