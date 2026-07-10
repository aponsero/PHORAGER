include { CHECKM2 } from '../modules/tools/checkm2'
include { FILTER_GENOMES } from '../modules/utilities/filter_genomes'
include { DREP } from '../modules/tools/drep'
include { SUMMARY_REPORT } from '../modules/utilities/summary_report'

workflow bacterial {
    main:
        // Define input channel for genomes
        def input = file(params.genome)
        if (input.isDirectory()) {
            genome_ch = channel.fromPath("${params.genome}/*.{fa,fasta,fna}", checkIfExists: true)
        } else {
            genome_ch = channel.fromPath(params.genome, checkIfExists: true)
        }

        checkm2_db_ch = channel.fromPath("${params.database_location}/CheckM2_database", checkIfExists: true)

        // Run CheckM2
        CHECKM2(genome_ch.collect(), checkm2_db_ch, params.threads)

        // Filter genomes on completeness and contamination
        FILTER_GENOMES(CHECKM2.out.report, params.completeness_threshold, params.contamination_threshold)

        // Count number of passed genomes
        FILTER_GENOMES.out.passed
            .map { file -> 
                def lines = file.readLines()
                return [lines.size(), file]
            }
            .branch { entry ->
                run_drep: entry[0] > 1
                skip_drep: true
            }
            .set { drep_decision }

        // Run dRep only if we have more than 1 genome
        if_drep = drep_decision.run_drep.map { entry -> entry[1] }

        DREP(
            if_drep,
            genome_ch.collect(),
            params.drep_ani_threshold,
            params.threads,
            drep_decision.run_drep.map { entry -> entry[0] }  // genome count
        )

        // Create a channel for the final dRep output
        drep_result = DREP.out.drep_dir.ifEmpty(file("NO_DREP_DIR"))

        // Generate summary report
        SUMMARY_REPORT(
            CHECKM2.out.report,
            FILTER_GENOMES.out.passed,
            FILTER_GENOMES.out.failed,
            drep_result,
            params.completeness_threshold,
            params.contamination_threshold,
            params.drep_ani_threshold
        )
}