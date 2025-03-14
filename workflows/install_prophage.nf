// This subworkflow installs tools required for prophage detection
include { INSTALL_VIBRANT } from '../modules/install_vibrant'
include { INSTALL_GENOMAD } from '../modules/install_genomad'
include { INSTALL_PARSING_ENV } from '../modules/install_parsing_env'

workflow install_prophage {
    main:
        db_location = file(params.global_db_location)
        conda_only = params.conda_only
        
        INSTALL_VIBRANT(db_location, conda_only)
        INSTALL_GENOMAD(db_location, conda_only)
        INSTALL_PARSING_ENV(db_location, conda_only)
}