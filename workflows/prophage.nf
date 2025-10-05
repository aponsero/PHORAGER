include { GENOMAD } from '../modules/tools/genomad'
include { VIBRANT } from '../modules/tools/vibrant'
include { PARSE_GENOMAD } from '../modules/utilities/parse_genomad'
include { PARSE_VIBRANT } from '../modules/utilities/parse_vibrant'
include { COMPARE_PROPHAGES } from '../modules/utilities/compare_prophages'
include { PROPHAGE_SUMMARY } from '../modules/utilities/prophage_summary'

workflow prophage {
    main:
        // Smart input detection for --genome parameter
        def input = file(params.genome)
        
        if (input.isDirectory()) {
            // Check if it's a bacterial workflow output directory
            def bacterial_genomes = file("${input}/1.Genome_preprocessing/Bact3_dRep/drep_output/dereplicated_genomes")
            
            if (bacterial_genomes.exists()) {
                def genome_files = bacterial_genomes.listFiles()
                if (genome_files && genome_files.size() > 0) {
                    log.info "Detected bacterial workflow output directory"
                    log.info "Using dereplicated genomes from: ${bacterial_genomes}"
                    genomes = Channel.fromPath("${bacterial_genomes}/*.{fa,fasta,fna}")
                        .ifEmpty { error "No FASTA files found in dereplicated genomes directory: ${bacterial_genomes}" }
                } else {
                    log.info "Using directory of FASTA files: ${input}"
                    genomes = Channel.fromPath("${input}/*.{fa,fasta,fna}")
                        .ifEmpty { error "No FASTA files found in directory: ${input}" }
                }
            } else {
                log.info "Using directory of FASTA files: ${input}"
                genomes = Channel.fromPath("${input}/*.{fa,fasta,fna}")
                    .ifEmpty { error "No FASTA files found in directory: ${input}" }
            }
        } else if (input.isFile()) {
            log.info "Using single FASTA file: ${input}"
            genomes = Channel.fromPath(params.genome)
                .ifEmpty { error "Genome file not found: ${params.genome}" }
        } else {
            error "Input path does not exist or is not accessible: ${params.genome}"
        }

        // Database path construction from config specs
        genomad_db_ch = Channel.fromPath("${params.database_location}/${params.database_specs.genomad.directory}")
        vibrant_db_ch = Channel.fromPath("${params.database_location}/${params.database_specs.vibrant.directory}")

        // Tool execution with conditional logic
        if (params.run_genomad) {
            log.info "Running GenoMAD analysis with preset: ${params.genomad_preset}"
            GENOMAD(genomes, genomad_db_ch)
            PARSE_GENOMAD(GENOMAD.out.results)
            genomad_coords = PARSE_GENOMAD.out.coordinates
        } else {
            log.info "Skipping GenoMAD analysis (run_genomad = false)"
            genomad_coords = Channel.empty()
        }

        if (params.run_vibrant) {
            log.info "Running VIBRANT analysis with minimum length: ${params.vibrant_min_length} bp"
            VIBRANT(genomes, vibrant_db_ch)
            PARSE_VIBRANT(VIBRANT.out.results)
            vibrant_coords = PARSE_VIBRANT.out.coordinates
        } else {
            log.info "Skipping VIBRANT analysis (run_vibrant = false)"
            vibrant_coords = Channel.empty()
        }
        
        // Error handling for when both tools are disabled
        if (!params.run_genomad && !params.run_vibrant) {
            error "At least one prophage detection tool must be enabled. Set run_genomad=true or run_vibrant=true"
        }

        // Create a channel that contains genome files with their names
        genome_ch = genomes.map { genome_file ->
            def genome_name = genome_file.name.toString().tokenize('.')[0]
            return tuple(genome_name, genome_file)
        }

        // Channel combination and comparison
        genomad_coords
            .mix(vibrant_coords)
            .groupTuple()
            .combine(genome_ch, by: 0)  // Combine with genome files based on name
            .map { genome_name, coords_files, genome_file -> 
                if (coords_files.size() == 1) {
                    return tuple(genome_name, coords_files[0], 
                           file("${params.outdir}/NO_RESULTS_${genome_name}.tsv"),
                           genome_file)
                } else {
                    return tuple(genome_name, coords_files[0], coords_files[1], genome_file)
                }
            }
            .set { comparison_input }

        COMPARE_PROPHAGES(comparison_input)
        
        // Collect all summary and results files
        comparison_summaries = COMPARE_PROPHAGES.out.summary
            .collect()
        consolidated_coords = COMPARE_PROPHAGES.out.consolidated
            .map { genome_name, file -> file }
            .collect()
        prophage_sequences = COMPARE_PROPHAGES.out.prophage_sequences
            .collect()

        // Generate final summary and cleanup
        PROPHAGE_SUMMARY(
            comparison_summaries,
            consolidated_coords,
            prophage_sequences
        )

    emit:
        summary_log = PROPHAGE_SUMMARY.out.summary_log
        combined_sequences = PROPHAGE_SUMMARY.out.combined_sequences
        combined_coordinates = PROPHAGE_SUMMARY.out.combined_coordinates
}