include { CHECKV } from '../modules/checkv'
include { PARSE_CHECKV } from '../modules/parse_checkv'
include { SPLIT_FASTA } from '../modules/split_fasta'
include { PHAROKKA } from '../modules/pharokka'
include { PHOLD } from '../modules/phold'
include { PARSE_FILTER_ANNOTATIONS } from '../modules/parse_filter_annotations'
include { CLUSTER_PHAGES } from '../modules/cluster_phages'
include { EXTRACT_REPRESENTATIVES } from '../modules/extract_representatives'
include { ANNOTATION_SUMMARY } from '../modules/annotation_summary'

workflow annotation {
    main:
        // Define input channel for prophage sequences
        if (params.prophage_fasta) {
            fasta_ch = Channel.fromPath(params.prophage_fasta, checkIfExists: true)
        } else {
            def prophage_output = file("${params.outdir}/2.Prophage_detection/All_prophage_sequences.fasta")
            if (!prophage_output.exists()) {
                error "All_prophage_sequences.fasta not found at ${params.outdir}/2.Prophage_detection/. Please run the prophage workflow first or provide input with --prophage_fasta"
            }
            fasta_ch = Channel.fromPath(prophage_output)
        }

        // Create channels for databases
        checkv_db_ch = Channel.fromPath("${params.global_db_location}/checkv_database/checkv-db-v1.5", checkIfExists: true)
        pharokka_db_ch = Channel.fromPath(params.pharokka_db_location, checkIfExists: true)
        phold_db_ch = Channel.fromPath(params.phold_db_location, checkIfExists: true)

        // Run CheckV and parse results
        CHECKV(fasta_ch, checkv_db_ch)
        PARSE_CHECKV(CHECKV.out.dir, params.min_prophage_length, params.checkv_quality_levels)

        if (!params.skip_detailed_annotation) {
            // Run detailed annotation steps
            SPLIT_FASTA(PARSE_CHECKV.out.filtered_fasta)
            PHAROKKA(SPLIT_FASTA.out.split_fastas, pharokka_db_ch)
            PHOLD(PHAROKKA.out.results, phold_db_ch)
            
            PARSE_FILTER_ANNOTATIONS(
                PHAROKKA.out.results.collect(),
                PHOLD.out.results.collect(),
                SPLIT_FASTA.out.split_fastas.collect(),
                params.annotation_filter_mode,
                params.pharokka_structural_perc,
                params.pharokka_structural_total,
                params.phold_structural_perc,
                params.phold_structural_total
            )

            // Clustering with annotation filtered results
            CLUSTER_PHAGES(
                PARSE_FILTER_ANNOTATIONS.out.filtered_fasta,
                params.clustering_min_ani,
                params.clustering_min_coverage,
                file(params.anicalc_script),
                file(params.aniclust_script)
            )

            // Extract representatives
            EXTRACT_REPRESENTATIVES(CLUSTER_PHAGES.out.for_extraction)

            // Generate summary with annotation results
            ANNOTATION_SUMMARY(
                PARSE_CHECKV.out.summary,
                PARSE_FILTER_ANNOTATIONS.out.summary,
                CLUSTER_PHAGES.out.clusters,
                EXTRACT_REPRESENTATIVES.out.rep_seqs,
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
        } else {
            // Clustering with CheckV results only
            CLUSTER_PHAGES(
                PARSE_CHECKV.out.filtered_fasta,
                params.clustering_min_ani,
                params.clustering_min_coverage,
                file(params.anicalc_script),
                file(params.aniclust_script)
            )

            // Extract representatives
            EXTRACT_REPRESENTATIVES(CLUSTER_PHAGES.out.for_extraction)

            // Generate summary without annotation results
            ANNOTATION_SUMMARY(
                PARSE_CHECKV.out.summary,
                Channel.empty(),  // No annotation summary
                CLUSTER_PHAGES.out.clusters,
                EXTRACT_REPRESENTATIVES.out.rep_seqs,
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
}
