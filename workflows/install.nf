include { INSTALL_DREP } from '../modules/install/install_drep'
include { INSTALL_CHECKM2 } from '../modules/install/install_checkm2'
include { INSTALL_CHECKM2_DATABASE } from '../modules/install/install_checkm2_database'
include { INSTALL_PARSING_ENV } from '../modules/install/install_parsing_env'
include { INSTALL_GENOMAD } from '../modules/install/install_genomad'
include { INSTALL_GENOMAD_DATABASE } from '../modules/install/install_genomad_database'
include { INSTALL_VIBRANT } from '../modules/install/install_vibrant'
include { INSTALL_VIBRANT_DATABASE } from '../modules/install/install_vibrant_database'
include { INSTALL_CHECKV } from '../modules/install/install_checkv'
include { INSTALL_CHECKV_DATABASE } from '../modules/install/install_checkv_database'
include { INSTALL_PHAROKKA } from '../modules/install/install_pharokka'
include { INSTALL_PHAROKKA_DATABASE } from '../modules/install/install_pharokka_database'
include { INSTALL_PHOLD } from '../modules/install/install_phold'
include { INSTALL_PHOLD_DATABASE } from '../modules/install/install_phold_database'

workflow install {
    main:
        // Create directories
        install_logs_dir = file(params.installation_logs_dir)
        database_location = file(params.database_location)
        
        if (!install_logs_dir.exists()) {
            install_logs_dir.mkdirs()
        }
        if (!database_location.exists()) {
            database_location.mkdirs()
        }
        
        // Handle null parameters safely
        tools_list = params.tools ? params.tools.split(',').collect { it.trim() } : []
        databases_list = params.databases ? params.databases.split(',').collect { it.trim() } : []
        
        // Create channels
        tools_ch = tools_list ? Channel.fromList(tools_list) : Channel.empty()
        databases_ch = databases_list ? Channel.fromList(databases_list) : Channel.empty()

        // Install genome analysis tools
        tools_ch
            .filter { it == 'drep' }
            .map { tool -> install_logs_dir }
            .set { drep_input }
        
        tools_ch
            .filter { it == 'checkm2' }
            .map { tool -> install_logs_dir }
            .set { checkm2_input }

        tools_ch
            .filter { it == 'parsing_env' }
            .map { tool -> install_logs_dir }
            .set { parsing_env_input }
        
        // Install prophage detection tools
        tools_ch
            .filter { it == 'genomad' }
            .map { tool -> install_logs_dir }
            .set { genomad_input }
        
        tools_ch
            .filter { it == 'vibrant' }
            .map { tool -> install_logs_dir }
            .set { vibrant_input }
        
        // Install annotation tools
        tools_ch
            .filter { it == 'checkv' }
            .map { tool -> install_logs_dir }
            .set { checkv_input }
        
        tools_ch
            .filter { it == 'pharokka' }
            .map { tool -> install_logs_dir }
            .set { pharokka_input }
        
        tools_ch
            .filter { it == 'phold' }
            .map { tool -> install_logs_dir }
            .set { phold_input }
        
        // Run all tool installations
        INSTALL_DREP(drep_input)
        INSTALL_CHECKM2(checkm2_input)
        INSTALL_PARSING_ENV(parsing_env_input)
        INSTALL_GENOMAD(genomad_input)
        INSTALL_VIBRANT(vibrant_input)
        INSTALL_CHECKV(checkv_input)
        INSTALL_PHAROKKA(pharokka_input)
        INSTALL_PHOLD(phold_input)
        
        // Create database input channels (always create, even if empty)
        databases_ch
            .filter { it == 'checkm2' }
            .map { db -> database_location }
            .set { checkm2_db_input }
        
        databases_ch
            .filter { it == 'genomad' }
            .map { db -> database_location }
            .set { genomad_db_input }
        
        databases_ch
            .filter { it == 'vibrant' }
            .map { db -> database_location }
            .set { vibrant_db_input }
        
        databases_ch
            .filter { it == 'checkv' }
            .map { db -> database_location }
            .set { checkv_db_input }
        
        databases_ch
            .filter { it == 'pharokka' }
            .map { db -> database_location }
            .set { pharokka_db_input }
        
        databases_ch
            .filter { it == 'phold' }
            .map { db -> database_location }
            .set { phold_db_input }
        
        // Run database installations with dependency logic
        if ('checkm2' in tools_list && 'checkm2' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_CHECKM2_DATABASE(
                checkm2_db_input.combine(INSTALL_CHECKM2.out.install_check)
                                .map { db_location, tool_log -> db_location }
            )
        } else if ('checkm2' in databases_list) {
            // Only database requested - runs independently
            INSTALL_CHECKM2_DATABASE(checkm2_db_input)
        }
        
        if ('genomad' in tools_list && 'genomad' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_GENOMAD_DATABASE(
                genomad_db_input.combine(INSTALL_GENOMAD.out.install_check)
                                .map { db_location, tool_log -> db_location }
            )
        } else if ('genomad' in databases_list) {
            // Only database requested - runs independently
            INSTALL_GENOMAD_DATABASE(genomad_db_input)
        }
        
        if ('vibrant' in tools_list && 'vibrant' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_VIBRANT_DATABASE(
                vibrant_db_input.combine(INSTALL_VIBRANT.out.install_check)
                               .map { db_location, tool_log -> db_location }
            )
        } else if ('vibrant' in databases_list) {
            // Only database requested - runs independently
            INSTALL_VIBRANT_DATABASE(vibrant_db_input)
        }
        
        if ('checkv' in tools_list && 'checkv' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_CHECKV_DATABASE(
                checkv_db_input.combine(INSTALL_CHECKV.out.install_check)
                               .map { db_location, tool_log -> db_location }
            )
        } else if ('checkv' in databases_list) {
            // Only database requested - runs independently
            INSTALL_CHECKV_DATABASE(checkv_db_input)
        }
        
        if ('pharokka' in tools_list && 'pharokka' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_PHAROKKA_DATABASE(
                pharokka_db_input.combine(INSTALL_PHAROKKA.out.install_check)
                                 .map { db_location, tool_log -> db_location }
            )
        } else if ('pharokka' in databases_list) {
            // Only database requested - runs independently
            INSTALL_PHAROKKA_DATABASE(pharokka_db_input)
        }
        
        if ('phold' in tools_list && 'phold' in databases_list) {
            // Both tool and database requested - database waits for tool
            INSTALL_PHOLD_DATABASE(
                phold_db_input.combine(INSTALL_PHOLD.out.install_check)
                              .map { db_location, tool_log -> db_location }
            )
        } else if ('phold' in databases_list) {
            // Only database requested - runs independently
            INSTALL_PHOLD_DATABASE(phold_db_input)
        }
        
        log.info "Installation workflow completed"
}