#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

log.info ""
log.info "======================================"
log.info "         PHORAGER PIPELINE            "
log.info "======================================"
log.info ""
log.info "Workflow: ${params.workflow}"
log.info "Installation logs directory: ${params.installation_logs_dir}"
log.info "Database directory: ${params.database_location}"
log.info "Output directory: ${params.outdir}"
log.info "Profile: ${workflow.profile}"
log.info ""

// Include workflows
include { install }    from './workflows/install'
include { bacterial }  from './workflows/bacterial'
include { prophage }   from './workflows/prophage'
include { annotation } from './workflows/annotation'
include { SUMMARIZE } from './workflows/summarize'

workflow {
    if (params.workflow == 'install') {
        log.info "Running installation workflow..."
        install()
    }
    else if (params.workflow == 'bacterial') {
        log.info "Running bacterial genome quality control workflow..."
        bacterial()
    }
    else if (params.workflow == 'prophage') {
        log.info "Running prophage detection workflow..."
        prophage()
    }
    else if (params.workflow == 'annotation') {
        log.info "Running annotation and clustering workflow..."
        annotation()
    }
    else if (params.workflow == 'summarize') {
        log.info "Generating summary table: ${params.summary_type}"
        SUMMARIZE(
            params.summary_type,
            params.bacterial_outdir ?: 'NONE',
            params.annotation_outdir ?: 'NONE',
            params.summary_format ?: 'tsv'
        )
    }
    else {
        error """
        Invalid workflow specified: '${params.workflow}'

        Available workflows:
          --workflow install     Install tools and databases
          --workflow bacterial   Bacterial genome quality control
          --workflow prophage    Prophage detection in genomes
          --workflow annotation  Prophage annotation and clustering
          --workflow summarize   Generate summary tables from completed workflow outputs

        Example usage:
          nextflow run main.nf --workflow bacterial --genome /path/to/genomes/
          nextflow run main.nf --workflow summarize --summary_type bacterial_genome \\
              --outdir summaries/ --bacterial_outdir results/ --annotation_outdir results/
        """.stripIndent()
    }
}
