process SUMMARY_REPORT {
    publishDir "${params.outdir}/1.Genome_preprocessing", mode: 'copy'

    input:
    path checkm_report
    path passed_genomes
    path failed_genomes
    path drep_output
    val completeness_threshold
    val contamination_threshold
    val ani_threshold

    output:
    path "Bacterial_genome_QC.log", emit: report

    script:
    """
    #!/usr/bin/env python3
    import os
    import pandas as pd
    import glob
    
    # Initialize summary text
    summary = []
    summary.append("===============================")
    summary.append("BACTERIAL GENOME QUALITY CHECK")
    summary.append("===============================\\n")

    # Add software versions
    summary.append("Software Versions:")
    summary.append("-----------------")
    summary.append("CheckM2: v1.0.2")
    summary.append("dRep: v3.5.0\\n")
    
    # Parameters section
    summary.append("Parameters:")
    summary.append("-----------")
    summary.append(f"Minimum completeness: ${completeness_threshold}%")
    summary.append(f"Maximum contamination: ${contamination_threshold}%")
    summary.append(f"dRep ANI threshold: ${ani_threshold}\\n")
    
    # Input genomes summary
    checkm_df = pd.read_csv('${checkm_report}', sep='\\t')
    total_genomes = len(checkm_df)
    summary.append("Input Summary:")
    summary.append("-------------")
    summary.append(f"Total number of input genomes: {total_genomes}\\n")
    
    # Quality filtering results
    with open('${failed_genomes}', 'r') as f:
        failed_list = f.read().splitlines()
    with open('${passed_genomes}', 'r') as f:
        passed_list = f.read().splitlines()
        
    n_failed = len(failed_list)
    n_passed = len(passed_list)
    
    summary.append("Quality Check Results:")
    summary.append("---------------------")
    summary.append(f"Genomes passed quality thresholds: {n_passed}")
    summary.append(f"Genomes failed quality thresholds: {n_failed}\\n")
    
    if n_failed > 0:
        summary.append("Failed Genomes Details:")
        summary.append("---------------------")
        for genome in failed_list:
            genome_stats = checkm_df[checkm_df['Name'] == genome].iloc[0]
            summary.append(f"Genome: {genome}")
            summary.append(f"  Completeness: {genome_stats['Completeness']:.2f}%")
            summary.append(f"  Contamination: {genome_stats['Contamination']:.2f}%")
        summary.append("")

    # Dereplication results
    summary.append("Dereplication Results:")
    summary.append("---------------------")
    
    # Check if dRep was skipped
    if '${drep_output}'.endswith('NO_DREP_DIR'):
        if n_passed == 0:
            summary.append("Dereplication was skipped: No genomes passed quality filters")
        elif n_passed == 1:
            summary.append("Dereplication was skipped: Only one genome passed quality filters")
            summary.append("\\nFinal genome:")
            summary.append(f"  - {passed_list[0]}")
    else:
        derep_dir = '${drep_output}/dereplicated_genomes'
        if os.path.exists(derep_dir):
            # Get all files with any of the three extensions
            derep_genomes = []
            for ext in ['fna', 'fa', 'fasta']:
                derep_genomes.extend(glob.glob(os.path.join(derep_dir, f'*.{ext}')))
            
            n_derep = len(derep_genomes)
            n_removed = n_passed - n_derep
            
            summary.append(f"Genomes after dereplication: {n_derep}")
            summary.append(f"Genomes removed by dereplication: {n_removed}")
            
            if n_derep > 0:
                summary.append("\\nDereplicated genomes:")
                for genome in sorted(derep_genomes):
                    summary.append(f"  - {os.path.basename(genome)}")
        else:
            summary.append("No dereplication results found")
    
    # Write summary to file
    with open('Bacterial_genome_QC.log', 'w') as f:
        f.write('\\n'.join(summary))
    """
}
