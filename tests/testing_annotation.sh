#!/bin/bash -l
#SBATCH --job-name=checkV
#SBATCH --output=errout/outputr%j.txt
#SBATCH --error=errout/errors_%j.txt
#SBATCH --partition=nbi-long
#SBATCH --time=72:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem-per-cpu=20G


export PATH="/hpc-home/zar24gir/miniconda3/bin:$PATH"
source /hpc-home/zar24gir/miniconda3/bin/activate

conda activate env_nf
export NXF_OFFLINE='true'

nextflow run main.nf --workflow annotation --prophage results

#singularity exec singularity_cache/checkv_1.0.3--pyhdfd78af_0.sif checkv end_to_end results/2.Prophage_detection/All_prophage_sequences.fasta testsingularity -d databases/checkv_database

#singularity exec checkv_test_mpi/checkv_mpi_1.0.sif checkv end_to_end results/2.Prophage_detection/All_prophage_sequences.fasta testsingularity -d databases/checkv_database

