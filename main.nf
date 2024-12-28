#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

log.info "Conda cache directory : ${params.conda_cache_dir}"
log.info "Database directory : ${params.global_db_location}"

// Include subworkflows
include { install } from './workflows/install'
include { bacterial } from './workflows/bacterial'
include { prophage } from './workflows/prophage'
include { annotation } from './workflows/annotation'

// Entry point
workflow {
    if (params.workflow == 'install') {
        install()
    } else if (params.workflow == 'bacterial') {
        bacterial()
    } else if (params.workflow == 'prophage') {
        prophage()
    } else if (params.workflow == 'annotation') {
        annotation()
    } else {
        error "Invalid workflow specified. Use --workflow install, workflow bacterial, or workflow prophage"
    }
}
