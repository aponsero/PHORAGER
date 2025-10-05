process CLUSTER_PHAGES {
    tag "Clustering ${input_fasta.simpleName}"
    publishDir "${params.outdir}/3.Annotation/Anno6_Clustering", mode: 'copy'

    input:
    path input_fasta
    val min_ani
    val min_coverage
    path anicalc_script
    path aniclust_script

    output:
    path "blast_db/*", emit: blast_db
    path "phage_blast.tsv", emit: blast_results
    path "phage_ani.tsv", emit: ani_results
    path "phage_clusters.tsv", emit: clusters
    tuple path("phage_clusters.tsv"), path(input_fasta), emit: for_extraction

    script:
    // This process uses the checkv environment (includes blast, seqfu, python)
    def tool_spec = params.container_specs['checkv']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for checkv"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Running Cluster Phages via Singularity container..."
        echo "Input fasta: ${input_fasta}"
        echo "Min ANI: ${min_ani}"
        echo "Min coverage: ${min_coverage}"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling CheckV environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "CheckV environment container already exists, using cached version."
        fi
        
        # Verify input files exist
        if [ ! -f "${input_fasta}" ]; then
            echo "ERROR: Input FASTA file not found: ${input_fasta}"
            exit 1
        fi
        
        if [ ! -f "${anicalc_script}" ]; then
            echo "ERROR: ANI calculation script not found: ${anicalc_script}"
            exit 1
        fi
        
        if [ ! -f "${aniclust_script}" ]; then
            echo "ERROR: ANI clustering script not found: ${aniclust_script}"
            exit 1
        fi
        
        # Create directory for blast database
        mkdir -p blast_db
        
        # 1. Make BLAST database
        echo "Creating BLAST database..."
        singularity exec ${container_path} \\
            makeblastdb -in ${input_fasta} \\
                        -dbtype nucl \\
                        -out blast_db/filtered_phage_db
        
        # 2. Run all-vs-all BLAST
        echo "Running all-vs-all BLAST..."
        singularity exec ${container_path} \\
            blastn -query ${input_fasta} \\
                   -db blast_db/filtered_phage_db \\
                   -outfmt '6 std qlen slen' \\
                   -max_target_seqs 10000 \\
                   -out phage_blast.tsv \\
                   -num_threads ${task.cpus}
        
        # 3. Calculate pairwise ANI
        echo "Calculating pairwise ANI..."
        singularity exec ${container_path} \\
            python ${anicalc_script} \\
                   -i phage_blast.tsv \\
                   -o phage_ani.tsv
        
        # 4. Perform clustering
        echo "Performing clustering..."
        singularity exec ${container_path} \\
            python ${aniclust_script} \\
                   --fna ${input_fasta} \\
                   --ani phage_ani.tsv \\
                   --out phage_clusters.tsv \\
                   --min_ani ${min_ani} \\
                   --min_tcov ${min_coverage} \\
                   --min_qcov ${min_coverage}
        
        # Verify outputs
        if [ ! -f "phage_blast.tsv" ]; then
            echo "ERROR: BLAST results file not created"
            exit 1
        fi
        
        if [ ! -f "phage_ani.tsv" ]; then
            echo "ERROR: ANI results file not created"
            exit 1
        fi
        
        if [ ! -f "phage_clusters.tsv" ]; then
            echo "ERROR: Clustering results file not created"
            exit 1
        fi
        
        echo "Clustering completed successfully"
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Running Cluster Phages via Conda environment..."
        echo "Input fasta: ${input_fasta}"
        echo "Min ANI: ${min_ani}"
        echo "Min coverage: ${min_coverage}"
        
        # Verify input files exist
        if [ ! -f "${input_fasta}" ]; then
            echo "ERROR: Input FASTA file not found: ${input_fasta}"
            exit 1
        fi
        
        if [ ! -f "${anicalc_script}" ]; then
            echo "ERROR: ANI calculation script not found: ${anicalc_script}"
            exit 1
        fi
        
        if [ ! -f "${aniclust_script}" ]; then
            echo "ERROR: ANI clustering script not found: ${aniclust_script}"
            exit 1
        fi
        
        # Create directory for blast database
        mkdir -p blast_db
        
        # 1. Make BLAST database
        echo "Creating BLAST database..."
        makeblastdb -in ${input_fasta} \\
                    -dbtype nucl \\
                    -out blast_db/filtered_phage_db
        
        # 2. Run all-vs-all BLAST
        echo "Running all-vs-all BLAST..."
        blastn -query ${input_fasta} \\
               -db blast_db/filtered_phage_db \\
               -outfmt '6 std qlen slen' \\
               -max_target_seqs 10000 \\
               -out phage_blast.tsv \\
               -num_threads ${task.cpus}
        
        # 3. Calculate pairwise ANI
        echo "Calculating pairwise ANI..."
        python ${anicalc_script} \\
               -i phage_blast.tsv \\
               -o phage_ani.tsv
        
        # 4. Perform clustering
        echo "Performing clustering..."
        python ${aniclust_script} \\
               --fna ${input_fasta} \\
               --ani phage_ani.tsv \\
               --out phage_clusters.tsv \\
               --min_ani ${min_ani} \\
               --min_tcov ${min_coverage} \\
               --min_qcov ${min_coverage}
        
        # Verify outputs
        if [ ! -f "phage_blast.tsv" ]; then
            echo "ERROR: BLAST results file not created"
            exit 1
        fi
        
        if [ ! -f "phage_ani.tsv" ]; then
            echo "ERROR: ANI results file not created"
            exit 1
        fi
        
        if [ ! -f "phage_clusters.tsv" ]; then
            echo "ERROR: Clustering results file not created"
            exit 1
        fi
        
        echo "Clustering completed successfully"
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}