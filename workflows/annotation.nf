// Annotation Workflow

include { CHECKV } from '../modules/tools/checkv'
include { PHAROKKA } from '../modules/tools/pharokka'
include { PHOLD } from '../modules/tools/phold'
include { PARSE_CHECKV } from '../modules/utilities/parse_checkv'
include { SPLIT_FASTA } from '../modules/utilities/split_fasta'
include { PARSE_FILTER_ANNOTATIONS } from '../modules/utilities/parse_filter_annotations'
include { CLUSTER_PHAGES } from '../modules/utilities/cluster_phages'
include { EXTRACT_REPRESENTATIVES } from '../modules/utilities/extract_representatives'
include { ANNOTATION_SUMMARY } from '../modules/utilities/annotation_summary'

workflow annotation {
    main:
        // Smart input detection following bacterial/prophage workflow pattern
        def input = file(params.prophage)
        
        if (input.isFile()) {
            // Direct FASTA file input
            if (!input.exists()) {
                error "Prophage FASTA file not found: ${params.prophage}"
            }
            
            // Validate file extension
            def valid_extensions = ['.fa', '.fasta', '.fna']
            if (!valid_extensions.any { params.prophage.endsWith(it) }) {
                error """
                Invalid file extension. Prophage file must end with: ${valid_extensions.join(', ')}
                Provided: ${params.prophage}
                """.stripIndent()
            }
            
            fasta_ch = Channel.fromPath(params.prophage, checkIfExists: true)
            log.info "Using direct prophage FASTA input: ${params.prophage}"
            
        } else if (input.isDirectory()) {
            // Check if it's prophage workflow output directory
            def prophage_output = file("${input}/2.Prophage_detection/All_prophage_sequences.fasta")
            
            if (prophage_output.exists()) {
                log.info "Detected prophage workflow output directory"
                log.info "Using prophage sequences from: ${prophage_output}"
                fasta_ch = Channel.fromPath(prophage_output)
            } else {
                // Check if it's just the prophage detection subdirectory
                def alt_prophage_output = file("${input}/All_prophage_sequences.fasta")
                if (alt_prophage_output.exists()) {
                    log.info "Detected prophage detection subdirectory"
                    log.info "Using prophage sequences from: ${alt_prophage_output}"
                    fasta_ch = Channel.fromPath(alt_prophage_output)
                } else {
                    // Directory of FASTA files
                    def fasta_files = file("${input}/*.{fa,fasta,fna}")
                    if (fasta_files.size() == 0) {
                        error """
                        No prophage FASTA files found in directory: ${input}
                        
                        Expected either:
                        1. Prophage workflow output directory containing 2.Prophage_detection/All_prophage_sequences.fasta
                        2. Directory containing prophage FASTA files with extensions: .fa, .fasta, .fna
                        """.stripIndent()
                    }
                    
                    if (fasta_files.size() == 1) {
                        log.info "Found single prophage FASTA file in directory: ${fasta_files[0]}"
                        fasta_ch = Channel.fromPath(fasta_files[0])
                    } else {
                        error """
                        Multiple FASTA files found in directory: ${input}
                        
                        For annotation workflow, please provide either:
                        1. A single combined FASTA file with all prophage sequences
                        2. Prophage workflow output directory
                        
                        Found files: ${fasta_files.collect { it.getName() }.join(', ')}
                        """.stripIndent()
                    }
                }
            }
        } else {
            error """
            Prophage input not found or invalid: ${params.prophage}
            
            Please provide either:
            1. A prophage FASTA file: --prophage sequences.fasta
            2. Prophage workflow output directory: --prophage /path/to/prophage_results/
            3. Directory with prophage detection results: --prophage /path/to/2.Prophage_detection/
            """.stripIndent()
        }

        // Create database channels using configuration-driven paths from database_specs
        checkv_db_ch = Channel.fromPath("${params.database_location}/${params.database_specs.checkv.directory}", checkIfExists: true)
        pharokka_db_ch = Channel.fromPath("${params.database_location}/${params.database_specs.pharokka.directory}", checkIfExists: true)
        phold_db_ch = Channel.fromPath("${params.database_location}/${params.database_specs.phold.directory}", checkIfExists: true)

        // Log workflow configuration
        log.info "Annotation workflow configuration:"
        log.info "  - Prophage input: ${params.prophage}"
        log.info "  - Skip detailed annotation: ${params.skip_detailed_annotation}"
        log.info "  - Min prophage length: ${params.min_prophage_length}"
        log.info "  - CheckV quality levels: ${params.checkv_quality_levels}"
        if (!params.skip_detailed_annotation) {
            log.info "  - Annotation filter mode: ${params.annotation_filter_mode}"
            log.info "  - Pharokka thresholds: ${params.pharokka_structural_perc}% / ${params.pharokka_structural_total} genes"
            log.info "  - PHOLD thresholds: ${params.phold_structural_perc}% / ${params.phold_structural_total} genes"
        }
        log.info "  - Clustering: ANI ${params.clustering_min_ani}%, coverage ${params.clustering_min_coverage}%"

        // Phase 1: CheckV quality assessment and filtering
        CHECKV(fasta_ch, checkv_db_ch)
        PARSE_CHECKV(
            CHECKV.out.dir, 
            params.min_prophage_length, 
            params.checkv_quality_levels
        )

        // Read the count and branch based on whether prophages were found
        PARSE_CHECKV.out.count
            .splitText()
            .map { it.trim().toInteger() }
            .branch {
                found: it > 0
                none: it == 0
            }
            .set { count_result }

        // Log the outcome
        count_result.found.subscribe { 
            log.info "Found ${it} prophages passing quality filters, proceeding with annotation pipeline..." 
        }
        count_result.none.subscribe { 
            log.warn "No prophages passed quality filters. Skipping annotation/clustering, generating summary report..." 
        }

        // Conditional execution based on prophage count
        if (!params.skip_detailed_annotation) {
            // Phase 2: Detailed annotation pipeline - only if prophages exist
            log.info "Configured for detailed annotation pipeline (Pharokka + PHOLD)"
            
            // Only split if we have prophages - filter by count
            PARSE_CHECKV.out.filtered_fasta
                .combine(count_result.found)
                .map { fasta, count -> fasta }
                .set { fasta_for_split }
            
            SPLIT_FASTA(fasta_for_split.ifEmpty([]))
            
            // Run annotation tools (only executed if SPLIT_FASTA produces output)
            PHAROKKA(
                SPLIT_FASTA.out.split_fastas.flatten().ifEmpty([]),
                pharokka_db_ch
            )
            PHOLD(
                PHAROKKA.out.results.ifEmpty([]),
                phold_db_ch
            )
            
            // Parse and filter annotation results
            PARSE_FILTER_ANNOTATIONS(
                PHAROKKA.out.results.collect().ifEmpty([]),
                PHOLD.out.results.collect().ifEmpty([]),
                SPLIT_FASTA.out.split_fastas.collect().ifEmpty([]),
                params.annotation_filter_mode,
                params.pharokka_structural_perc,
                params.pharokka_structural_total,
                params.phold_structural_perc,
                params.phold_structural_total
            )

            // Get annotation filtering results
            annotation_summary_input = PARSE_FILTER_ANNOTATIONS.out.summary.ifEmpty([])
            annotation_count_input = PARSE_FILTER_ANNOTATIONS.out.count
            
            // Branch based on annotation count to decide if clustering should run
            annotation_count_input
                .splitText()
                .map { it.trim().toInteger() }
                .branch {
                    found: it > 0
                    none: it == 0
                }
                .set { annotation_count_result }
            
            // Log annotation filtering outcome
            annotation_count_result.found.subscribe { 
                log.info "${it} sequences passed annotation filtering, proceeding with clustering..." 
            }
            annotation_count_result.none.subscribe { 
                log.warn "No sequences passed annotation filtering. Skipping clustering..." 
            }
            
            // Only pass sequences to clustering if annotation count > 0
            PARSE_FILTER_ANNOTATIONS.out.filtered_fasta
                .combine(annotation_count_result.found)
                .map { fasta, count -> fasta }
                .set { clustering_input }
            
        } else {
            // Skip detailed annotation, use CheckV results directly
            log.info "Skipping detailed annotation, using CheckV results for clustering"
            
            // Only pass fasta if prophages were found
            PARSE_CHECKV.out.filtered_fasta
                .combine(count_result.found)
                .map { fasta, count -> fasta }
                .set { clustering_input }
            
            annotation_summary_input = Channel.empty()
            annotation_count_input = Channel.empty()
        }

        // Phase 3: Clustering pipeline - only if sequences available
        CLUSTER_PHAGES(
            clustering_input.ifEmpty([]),
            params.clustering_min_ani,
            params.clustering_min_coverage,
            file(params.anicalc_script),
            file(params.aniclust_script)
        )

        // Extract cluster representatives
        EXTRACT_REPRESENTATIVES(
            CLUSTER_PHAGES.out.for_extraction.ifEmpty([])
        )

        // Phase 4: Generate comprehensive summary - ALWAYS RUN
        ANNOTATION_SUMMARY(
            PARSE_CHECKV.out.summary,
            annotation_summary_input.ifEmpty([]),
            CLUSTER_PHAGES.out.clusters.ifEmpty([]),
            EXTRACT_REPRESENTATIVES.out.rep_seqs.ifEmpty([]),
            PARSE_CHECKV.out.count,
            annotation_count_input.ifEmpty([]),
            params.min_prophage_length,
            params.checkv_quality_levels,
            params.skip_detailed_annotation,
            params.pharokka_structural_perc,
            params.pharokka_structural_total,
            params.phold_structural_perc,
            params.phold_structural_total,
            params.clustering_min_ani,
            params.clustering_min_coverage
        )
}