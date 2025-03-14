// This subworkflow installs tools required for bacterial genome analysis
include { INSTALL_CHECKM2 } from '../modules/install_checkm2'
include { INSTALL_DREP } from '../modules/install_drep'
include { INSTALL_PARSING_ENV } from '../modules/install_parsing_env'

workflow install_genome {
    main:
        db_location = file(params.global_db_location)
        conda_only = params.conda_only
        
        INSTALL_CHECKM2(db_location, conda_only)
        INSTALL_DREP(db_location, conda_only)
        INSTALL_PARSING_ENV(db_location, conda_only)
}