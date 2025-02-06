include { GENOMAD } from '../modules/genomad'
include { VIBRANT } from '../modules/vibrant'
include { PARSE_GENOMAD } from '../modules/parse_genomad'
include { PARSE_VIBRANT } from '../modules/parse_vibrant'
include { COMPARE_PROPHAGES } from '../modules/compare_prophages'
include { PROPHAGE_SUMMARY } from '../modules/prophage_summary'

workflow prophage {
    main:

        // Input channel setup
        if (params.use_dereplicated_genomes) {
            def derep_dir = file("${params.outdir}/1.Genome_preprocessing/Bact3_dRep/drep_output/dereplicated_genomes")
            if (derep_dir.exists()) {
                genomes = Channel.fromPath("${derep_dir}/*.{fa,fasta,fna}")
                    .ifEmpty { error "No genomes found in ${derep_dir}" }
            } else {
                error "Dereplicated genomes directory not found. Please run the bacterial workflow first or provide direct input with --genome"
            }
        } else {
            def input = file(params.genome)
            if (input.isDirectory()) {
                genomes = Channel.fromPath("${input}/*.{fa,fasta,fna}")
                    .ifEmpty { error "No genomes found in ${params.genome}" }
            } else {
                genomes = Channel.fromPath(params.genome)
                    .ifEmpty { error "Genome file not found: ${params.genome}" }
            }
        }

        if (params.run_genomad) {
            genomad_db_ch = Channel.fromPath(params.genomad_db_location, checkIfExists: true)
            GENOMAD(genomes, genomad_db_ch)
            PARSE_GENOMAD(GENOMAD.out.results)
            genomad_coords = PARSE_GENOMAD.out.coordinates
        } else {
            genomad_coords = Channel.empty()
        }

        log.info "DEBUG: vibrant database parameter: ${params.vibrant_db_location}"

        if (params.run_vibrant) {
            vibrant_db_ch = Channel.fromPath(params.vibrant_db_location, checkIfExists: true)
            VIBRANT(genomes, vibrant_db_ch)
            PARSE_VIBRANT(VIBRANT.out.results)
            vibrant_coords = PARSE_VIBRANT.out.coordinates
        } else {
            vibrant_coords = Channel.empty()
        }

	  // Create a channel that contains genome files with their names
    	genome_ch = genomes.map { genome_file ->
        	def genome_name = genome_file.name.toString().tokenize('.')[0]
        	return tuple(genome_name, genome_file)
    	}

    	// channel combination
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
}
