include { INSTALL_CHECKM2 } from '../modules/install_checkm2'
include { INSTALL_DREP } from '../modules/install_drep'
include { INSTALL_VIBRANT } from '../modules/install_vibrant'
include { INSTALL_GENOMAD } from '../modules/install_genomad'
include { INSTALL_PARSING_ENV } from '../modules/install_parsing_env'
include { INSTALL_CHECKV } from '../modules/install_checkv'
include { INSTALL_PHAROKKA } from '../modules/install_pharokka'
include { INSTALL_PHOLD } from '../modules/install_phold'

workflow install {
    main:
        db_location = file(params.global_db_location)
        INSTALL_CHECKM2(params.global_db_location)
        INSTALL_DREP(params.global_db_location)
        INSTALL_VIBRANT(params.global_db_location)
        INSTALL_GENOMAD(params.global_db_location)
	INSTALL_PARSING_ENV(params.global_db_location)
	INSTALL_CHECKV(params.global_db_location)
	INSTALL_PHAROKKA(params.global_db_location)
	INSTALL_PHOLD(params.global_db_location)
}
