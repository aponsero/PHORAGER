// This subworkflow installs tools required for prophage annotation
include { INSTALL_CHECKV } from '../modules/install_checkv'
include { INSTALL_PHAROKKA } from '../modules/install_pharokka'
include { INSTALL_PHOLD } from '../modules/install_phold'
include { INSTALL_PARSING_ENV } from '../modules/install_parsing_env'

workflow install_annotation {
    main:
        db_location = file(params.global_db_location)
        conda_only = params.conda_only
        
        INSTALL_CHECKV(db_location, conda_only)
        INSTALL_PHAROKKA(db_location, conda_only)
        INSTALL_PHOLD(db_location, conda_only)
        INSTALL_PARSING_ENV(db_location, conda_only)
}