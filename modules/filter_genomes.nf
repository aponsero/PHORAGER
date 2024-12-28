process FILTER_GENOMES {
    publishDir "${params.outdir}/1.Genome_preprocessing/Bact2_FilteredGenomes", mode: 'copy'

    input:
    path quality_report
    val completeness_threshold
    val contamination_threshold

    output:
    path 'passed_genomes.txt', emit: passed
    path 'failed_genomes.txt', emit: failed

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd

    # Read the quality report
    df = pd.read_csv('${quality_report}', sep='\t')

    # Filter genomes based on thresholds
    passed = df[(df['Completeness'] >= ${completeness_threshold}) & (df['Contamination'] <= ${contamination_threshold})]
    failed = df[(df['Completeness'] < ${completeness_threshold}) | (df['Contamination'] > ${contamination_threshold})]

    # Write passed genomes to file
    with open('passed_genomes.txt', 'w') as f:
        for genome in passed['Name']:
            f.write(f"{genome}\\n")

    # Write failed genomes to file
    with open('failed_genomes.txt', 'w') as f:
        for genome in failed['Name']:
            f.write(f"{genome}\\n")

    # Print summary
    print("Genomes that passed the quality thresholds:")
    print(passed['Name'].tolist())
    print("Genomes that failed the quality thresholds:")
    print(failed['Name'].tolist())
    """
}
