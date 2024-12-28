// modules/install_checkm2.nf
process INSTALL_CHECKM2 {
    // conda "bioconda::checkm2=1.0.1"

    input:
    path db_location

    output:
    path "${db_location}", emit: checkm2_db

    script:
    """
    # Download and install the CheckM2 database
    checkm2 database --download --path ${db_location}
    """
}
