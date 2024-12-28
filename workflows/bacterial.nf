include { CHECKM2 } from '../modules/checkm2'
include { FILTER_GENOMES } from '../modules/filter_genomes'
include { DREP } from '../modules/drep'
include { SUMMARY_REPORT } from '../modules/summary_report'

workflow bacterial {
    main:
        // Define input channel for genomes
        def input = file(params.genome)
        if (input.isDirectory()) {
            genome_ch = Channel.fromPath("${params.genome}/*.{fa,fasta,fna}", checkIfExists: true)
        } else {
            genome_ch = Channel.fromPath(params.genome, checkIfExists: true)
        }

        checkm2_db_ch = Channel.fromPath(params.checkm2_db_location, checkIfExists: true)

        // Run CheckM2
        CHECKM2(genome_ch.collect(), checkm2_db_ch)

        // Filter genomes on completeness and contamination
        FILTER_GENOMES(CHECKM2.out.report, params.completeness_threshold, params.contamination_threshold)

        // Count number of passed genomes
        FILTER_GENOMES.out.passed
            .map { file -> 
                def lines = file.readLines()
                return [lines.size(), file]
            }
            .branch {
                run_drep: it[0] > 1
                skip_drep: true
            }
            .set { drep_decision }

        // Run dRep only if we have more than 1 genome
        drep_out = drep_decision.run_drep
            .map { it[1] }  // Extract just the file from the tuple
            .branch { 
                do_drep: true
                no_drep: false
            }

        DREP(
            drep_out.do_drep,
            genome_ch.collect(),
            params.drep_ani_threshold
        )

        // Create a channel for the final dRep output
        drep_result = DREP.out.drep_dir
            .mix(Channel.value(file("NO_DREP_DIR")))
            .first()

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
