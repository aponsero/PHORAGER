<div align="center">
  <img src="logo_phorager.png" alt="Phorager Logo" width="400"/>

  # Phorager
  ### Prophage Analysis Pipeline

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A522.10.0-23aa62.svg)](https://www.nextflow.io/)
  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

  A comprehensive pipeline for bacterial genome quality control, prophage detection, and prophage characterization

  **Authors:**  
  - Xena Dyball
  - James Docherty
  - [Alise Ponsero](https://github.com/aponsero)
  - Ryan Cook

  **Citation:**  
  [Your Paper Citation or Preprint Link]
</div>

## Overview

This Nextflow pipeline provides a comprehensive suite of tools for bacterial genome quality control, prophage detection, and prophage characterization. The pipeline is organized into three main workflows:

### 0. **Installation** (`phorager install`)
- Download and setup required databases and conda environment

### 1. Bacterial Genome Quality Control (`phorager bacterial` or `--workflow bacterial`)
Quality assessment and dereplication of bacterial genomes using:
- **CheckM2**: Evaluates genome completeness and contamination
- **dRep**: Performs genome dereplication to remove redundant sequences

### 2. Prophage Detection (`phorager prophage` or `--workflow prophage`)
Identification and extraction of prophage sequences using complementary approaches:
- **geNomad**: Machine learning-based viral sequence detection
- **VIBRANT**: Machine learning-based viral sequence detection

### 3. Prophage Annotation (`phorager annotation` or `--workflow annotation`)
Multi-level characterization of prophage sequences:
- **CheckV**: Quality assessment of viral sequences
- **Pharokka**: Specialized phage genome annotation
- **PHOLD**: Specialized phage genome annotation
- **Clustering**: Sequence-based clustering to identify unique viral populations

### 4. End-to-End Analysis (`phorager run`)
   - Automatically execute entire pipeline from genome preprocessing to prophage annotation

## Pipeline Features

- **Modular Design**: Each workflow can be run independently or as part of a complete analysis
- **Flexible Input**: Accepts single genomes or directories of multiple genomes
- **Quality Control**: Multiple filtering steps to ensure high-quality predictions
- **Comprehensive Analysis**: From genome QC to detailed prophage characterization
- **Reproducibility**: Conda environment management for consistent tool versions
- **User-Friendly Interface**: Command-line wrapper script for easy execution

## Quick Start

Using the wrapper script (recommended):
```bash
# Install pipeline and databases
./phorager install

# Basic bacterial genome analysis
./phorager bacterial --genome /path/to/genomes

# Prophage detection
./phorager prophage --genome /path/to/genomes

# Prophage annotation
./phorager annotation --prophage_fasta /path/to/prophages.fasta

# Complete end-to-end analysis
./phorager run --genome /path/to/genomes
```

Using Nextflow directly:
```bash
# Install pipeline and databases
nextflow run main.nf --workflow install

# Basic bacterial genome analysis
nextflow run main.nf --workflow bacterial --genome /path/to/genomes

# Prophage detection
nextflow run main.nf --workflow prophage --genome /path/to/genomes

# Prophage annotation
nextflow run main.nf --workflow annotation --prophage_fasta /path/to/prophages.fasta
```

## Installation

### System Requirements

- Linux-based operating system
- Minimum 32GB RAM recommended (64GB for large datasets)
- Minimum 100GB free disk space for databases, conda environment and output files
- Internet connection for initial setup

### Prerequisites

1. **Nextflow** (≥ 22.10.0)
```bash
# Install Nextflow
curl -s https://get.nextflow.io | bash
# Add to your PATH
mv nextflow ~/bin/
```

2. **Conda or Mamba** package manager
```bash
# Install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# Or install Mamba (recommended for faster dependency resolution)
conda install -c conda-forge mamba
```

### Pipeline Installation

1. Clone the repository and setup:
```bash
# Clone repository
git clone [repository-url]
cd [repository-name]

# Setup wrapper script (optional but recommended)
chmod +x phorager
```

2. Install required databases and tools:
```bash
# Basic installation
./phorager install

# Verbose mode (shows detailed Nextflow output)
./phorager install --verbose

# Force reinstall databases (overwrite existing installations)
./phorager install --force

# Combine verbose and force reinstall
./phorager install --verbose --force

# Or using Nextflow directly
nextflow run main.nf --workflow install
```

This installation workflow will:
- Set up all required conda environments
- Download and install databases for:
  - CheckM2 (≈ 2.9GB)
  - geNomad (≈ 1.4GB)
  - VIBRANT (≈ 11GB)
  - CheckV (≈ 6.4GB)
  - Pharokka (≈ 1.9GB)
  - PHOLD (≈ 15GB)

### Configuration

The pipeline configuration can be customized in `nextflow.config`. Key configuration parameters include:

```nextflow
params {
    // Output directory
    outdir = "$projectDir/results"

    // Conda environment location
    conda_cache_dir = "$projectDir/conda_cache"

    // Database locations
    global_db_location = "$projectDir/databases"
    checkm2_db_location = "$projectDir/databases/CheckM2_database"
    genomad_db_location = "$projectDir/databases/geNomad_database/genomad_db"
    vibrant_db_location = "$projectDir/databases/vibrant_database"
    checkv_db_location = "$projectDir/databases/checkv_database/checkv-db-v1.5"
    pharokka_db_location = "$projectDir/databases/pharokka_database"
    phold_db_location = "$projectDir/databases/phold_database"

}
```

These parameters can be modified either by:
1. Editing the config file directly
2. Providing parameters via command line with either the wrapper or Nextflow:

```bash
# Using the wrapper script
./phorager install \
    --conda_cache /path/to/conda \
    --db_location /path/to/databases

# Or using Nextflow directly
nextflow run main.nf --workflow install \
    --conda_cache_dir /path/to/conda \
    --global_db_location /path/to/databases
```

### Conda Environment Setup

The pipeline uses separate conda environments for each tool to manage dependencies. These are automatically created in the specified `conda_cache_dir` when running the installation workflow. Key environments include:

| Tool | Version | Key Dependencies |
|------|---------|-----------------|
| CheckM2 | 1.0.1 | Python 3.9 |
| dRep | 3.5.0 | Python 3.9, MUMmer4 |
| geNomad | 1.8.1 | Python 3.9, HMMER 3.3 |
| VIBRANT | 1.2.1 | Python 3.9 |
| CheckV | 1.0.3 | Python 3.9, BLAST 2.16.0 |
| Pharokka | 1.7.4 | Python 3.9 |
| PHOLD | 0.2.0 | Python 3.9 |

### Verifying Installation

After installation, verify the setup with:
```bash
# Check database installation
ls -l $projectDir/databases

# Verify conda environments
conda env list | grep -E 'checkm2|drep|genomad|vibrant|checkv|pharokka|phold'
```

Expected output should show:
1. Populated database directories for each tool
2. Created conda environments with correct versions

#### Installation Options
- **Default Mode**: Silently installs databases, logs output to file
- **Verbose Mode (`--verbose`)**: 
  - Displays detailed Nextflow installation messages in real-time
  - Provides transparency about installation progress
- **Force Reinstall (`--force`)**: 
  - Forces reinstallation of databases
  - Useful for updating or fixing corrupted database installations

#### Logging
- Log files are automatically generated in `phorager_logs/`
- Log filename format: `install_YYYYMMDD_HHMMSS.log`
- Logs contain:
  - Detailed Nextflow installation output
  - Installation progress messages
  - Error details (if any)
- Logs are created regardless of verbose mode

Example log location:
```bash
# View recent installation log
cat phorager_logs/install_20241229_200747.log
```

## Bacterial Workflow

### Tool Overview

#### CheckM2 (v1.0.1)
- Assesses bacterial genome quality using machine learning
- Provides completeness and contamination estimates
- Uses protein markers for genome quality assessment
- Publication: [CheckM2: a rapid, scalable and accurate tool for assessing microbial genome quality using machine learning](https://doi.org/10.1038/s41592-023-01940-w)

#### dRep (v3.5.0)
- Performs genome dereplication based on sequence similarity
- Uses Average Nucleotide Identity (ANI) for comparison
- Identifies and selects representative genomes
- Publication: [dRep: a tool for fast and accurate genomic comparisons that enables improved genome recovery from metagenomes through de-replication](https://doi.org/10.1038/ismej.2017.126)

### Running the Workflow

Basic usage:
```bash
# Using the wrapper script (recommended)
./phorager bacterial --genome /path/to/genomes

# Or using Nextflow directly
nextflow run main.nf --workflow bacterial --genome /path/to/genomes
```

#### Input Requirements
- Input genomes must be in FASTA format (.fa, .fasta, or .fna)
- Accepts either:
  - A directory containing multiple genome files
  - A single genome file

#### Parameters

| Parameter | Description | Default | Wrapper Usage | Nextflow Usage |
|-----------|-------------|---------|---------------|----------------|
| `--genome` | Input genome file or directory | `$projectDir/data/genome.fa` | `--genome /path/to/genomes` | `--genome /path/to/genomes` |
| `--completeness_threshold` | Minimum genome completeness (%) | 95 | `--completeness-threshold 90` | `--completeness_threshold 90` |
| `--contamination_threshold` | Maximum contamination allowed (%) | 5 | `--contamination-threshold 10` | `--contamination_threshold 10` |
| `--drep_ani_threshold` | ANI threshold for dereplication | 0.999 | `--drep-ani-threshold 0.95` | `--drep_ani_threshold 0.95` |
| `--conda_cache` | Path to conda environment directory | `$projectDir/conda_cache` | `--conda-cache /path/to/conda` | `--conda_cache_dir /path/to/conda` |
| `--db_location` | Path to database directory | `$projectDir/databases` | `--db-location /path/to/db` | `--global_db_location /path/to/db` |
| `--outdir` | Output directory | `$projectDir/results` | `--outdir /path/to/output` | `--outdir /path/to/output` |
| `--threads` | Number of threads to use | All available cores | `--threads 4` | `--threads 4` |

### Output Structure

```
results/
└── 1.Genome_preprocessing/
    ├── Bacterial_genome_QC.log       # Overall workflow summary
    ├── Bact1_CheckM2/               
    │   ├── checkm2_output/          # Raw CheckM2 results
    │   └── quality_report.tsv       # Genome quality metrics
    ├── Bact2_FilteredGenomes/       
    │   ├── passed_genomes.txt       # List of genomes passing QC
    │   └── failed_genomes.txt       # List of failed genomes
    └── Bact3_dRep/                  
        └── drep_output/             
            └── dereplicated_genomes/ # Final dereplicated genomes
```

#### Output Files Description

1. **Bacterial_genome_QC.log**
   - Summary of workflow execution
   - Input parameters used
   - Number of genomes at each step
   - Quality filtering results
   - Dereplication results

2. **CheckM2 Output (Bact1_CheckM2/)**
   - `quality_report.tsv`: Tab-separated file containing:
     - Genome completeness scores
     - Contamination estimates
     - Other quality metrics
   - Raw CheckM2 output files

3. **Filtered Genomes (Bact2_FilteredGenomes/)**
   - Lists of genomes that passed/failed quality thresholds
   - Includes full paths to genome files
   - Quality metrics for failed genomes

4. **dRep Output (Bact3_dRep/)**
   - Only present if multiple genomes pass quality filtering
   - Contains dereplicated genome sequences
   - Clustering information
   - ANI comparison results

### Example Commands

1. Basic run with default parameters:
```bash
# Using the wrapper script
./phorager bacterial --genome /path/to/genomes

# Or using Nextflow directly
nextflow run main.nf --workflow bacterial \
    --genome /path/to/genomes
```

2. Custom quality thresholds:
```bash
# Using the wrapper script
./phorager bacterial \
    --genome /path/to/genomes \
    --completeness-threshold 90 \
    --contamination-threshold 10

# Or using Nextflow directly
nextflow run main.nf --workflow bacterial \
    --genome /path/to/genomes \
    --completeness_threshold 90 \
    --contamination_threshold 10
```

3. Less stringent dereplication:
```bash
# Using the wrapper script
./phorager bacterial \
    --genome /path/to/genomes \
    --drep-ani-threshold 0.95

# Or using Nextflow directly
nextflow run main.nf --workflow bacterial \
    --genome /path/to/genomes \
    --drep_ani_threshold 0.95
```

4. Resume a previous run:
```bash
# Using the wrapper script
./phorager bacterial \
    --genome /path/to/genomes \
    -resume

# Or using Nextflow directly
nextflow run main.nf -resume \
    --workflow bacterial \
    --genome /path/to/genomes
```

5. Custom database, conda, and output locations:
```bash
# Using the wrapper script
./phorager bacterial \
    --genome /path/to/genomes \
    --conda-cache /path/to/conda \
    --db-location /path/to/databases \
    --outdir /path/to/output \
    --threads 4

# Or using Nextflow directly
nextflow run main.nf --workflow bacterial \
    --genome /path/to/genomes \
    --conda_cache_dir /path/to/conda \
    --global_db_location /path/to/databases \
    --outdir /path/to/output \
    --threads 4
```

## Prophage Workflow

### Tool Overview

#### geNomad (v1.8.1)
- Machine learning-based tool for viral sequence detection
- Identifies both viruses and plasmids in genomic sequences
- Uses marker genes and sequence characteristics
- Provides confidence scores for predictions
- Publication: [Identification of mobile genetic elements with geNomad](https://doi.org/10.1038/s41587-023-01953-y)

#### VIBRANT (v1.2.1)
- Neural network-based virus identification tool
- Specializes in identifying integrated prophages
- Uses protein-based sequence annotation
- Includes viral lifestyle prediction
- Publication: [VIBRANT: automated recovery, annotation and curation of microbial viruses, and evaluation of viral community function from genomic sequences](https://doi.org/10.1186/s40168-020-00867-0)

### Running the Workflow

Basic usage:
```bash
# Using the wrapper script (recommended)
./phorager prophage --genome /path/to/genomes

# Or using Nextflow directly
nextflow run main.nf --workflow prophage --genome /path/to/genomes
```

#### Input Requirements
- Input genomes must be in FASTA format (.fa, .fasta, or .fna)
- Accepts either:
  - A directory containing multiple genome files
  - A single genome file
- Can use dereplicated genomes from bacterial workflow
- Recommended minimum contig size: 5kb

#### Parameters

| Parameter | Description | Default | Wrapper Usage | Nextflow Usage |
|-----------|-------------|---------|---------------|----------------|
| `--genome` | Input genome file or directory | `$projectDir/data/genome.fa` | `--genome /path/to/genomes` | `--genome /path/to/genomes` |
| `--use_dereplicated_genomes` | Use output from bacterial workflow | false | `--use_dereplicated_genomes true` | `--use_dereplicated_genomes true` |
| `--run_genomad` | Enable geNomad analysis | true | `--run_genomad false` | `--run_genomad false` |
| `--run_vibrant` | Enable VIBRANT analysis | true | `--run_vibrant false` | `--run_vibrant false` |
| `--conda_cache` | Path to conda environment directory | `$HOME/phorager/conda_cache` | `--conda_cache /path/to/conda` | `--conda_cache_dir /path/to/conda` |
| `--db_location` | Path to database directory | `$HOME/phorager/databases` | `--db_location /path/to/db` | `--global_db_location /path/to/db` |

### Output Structure

```
results/
└── 2.Prophage_detection/
    ├── Prophage_detection_summary.log    # Overall workflow summary
    ├── All_prophage_sequences.fasta      # Combined prophage sequences
    ├── All_prophage_coordinates.tsv      # Combined coordinates
    ├── Proph1_geNomad/                  
    │   └── [genome_name]/
    │       ├── genomad_output/          # Raw geNomad results
    │       └── [genome]_genomad_coordinates.tsv
    ├── Proph2_VIBRANT/                  
    │   └── [genome_name]/
    │       ├── vibrant_output/          # Raw VIBRANT results
    │       └── [genome]_vibrant_coordinates.tsv
    └── Proph3_Comparison/               
        └── [genome_name]/
            ├── [genome]_consolidated_coordinates.tsv
            ├── [genome]_comparison_summary.txt
            └── [genome]_prophage_sequences.fasta
```

#### Output Files Description

1. **Prophage_detection_summary.log**
   - Overall workflow summary
   - Number of genomes analyzed
   - Prophages detected by each tool
   - Total prophage sequences extracted
   - Tool-specific statistics

2. **Combined Output Files**
   - `All_prophage_sequences.fasta`: All predicted prophage sequences
   - `All_prophage_coordinates.tsv`: Coordinates for all predictions

3. **geNomad Output (Proph1_geNomad/)**
   - Full geNomad analysis results
   - Coordinates of predicted prophages
   - Confidence scores and markers detected

4. **VIBRANT Output (Proph2_VIBRANT/)**
   - Complete VIBRANT analysis results
   - Prophage coordinates and annotations
   - Lifestyle predictions

5. **Comparison Results (Proph3_Comparison/)**
   - Combined predictions from both tools
   - Per-genome summary statistics
   - Extracted prophage sequences

### Example Commands

1. Basic run with all tools:
```bash
# Using the wrapper script
./phorager prophage \
    --genome /path/to/genomes

# Or using Nextflow directly
nextflow run main.nf --workflow prophage \
    --genome /path/to/genomes
```

2. Use dereplicated genomes from bacterial workflow:
```bash
# Using the wrapper script
./phorager prophage \
    --use_dereplicated_genomes true

# Or using Nextflow directly
nextflow run main.nf --workflow prophage \
    --use_dereplicated_genomes true
```

3. Run only geNomad:
```bash
# Using the wrapper script
./phorager prophage \
    --genome /path/to/genomes \
    --run_vibrant false

# Or using Nextflow directly
nextflow run main.nf --workflow prophage \
    --genome /path/to/genomes \
    --run_vibrant false
```

4. Resume a failed run:
```bash
# Using the wrapper script
./phorager prophage \
    --genome /path/to/genomes \
    -resume

# Or using Nextflow directly
nextflow run main.nf -resume \
    --workflow prophage \
    --genome /path/to/genomes
```

5. Custom database and conda locations:
```bash
# Using the wrapper script
./phorager prophage \
    --genome /path/to/genomes \
    --conda_cache /path/to/conda \
    --db_location /path/to/databases

# Or using Nextflow directly
nextflow run main.nf --workflow prophage \
    --genome /path/to/genomes \
    --conda_cache_dir /path/to/conda \
    --global_db_location /path/to/databases
```
## Annotation Workflow

### Tool Overview

#### CheckV (v1.0.3)
- Quality assessment tool for viral sequences
- Estimates genome completeness
- Provides quality metrics and contamination detection
- Publication: [CheckV assesses the quality and completeness of metagenome-assembled viral genomes](https://doi.org/10.1038/s41587-020-00774-7)

#### Pharokka (v1.7.4)
- Specialized phage genome annotation tool
- Identifies and annotates phage-specific genes
- Provides functional categorization of viral proteins
- Publication: [Pharokka: a fast scalable bacteriophage annotation tool](https://doi.org/10.1093/bioinformatics/btac776)

#### PHOLD (v0.2.0)
- Host-interaction and defense system prediction
- Identifies anti-CRISPR proteins
- Detects viral defense systems
- Repository: [PHOLD: Phage Annotation using Protein Structures](https://github.com/gbouras13/phold)

#### Clustering Tools
- BLAST-based all-vs-all comparison
- ANI (Average Nucleotide Identity) calculation using aniclust

### Running the Workflow

Basic usage:
```bash
# Using the wrapper script (recommended)
./phorager annotation --prophage_fasta /path/to/prophages.fasta

# Or using Nextflow directly
nextflow run main.nf --workflow annotation
```

#### Input Requirements
- Prophage sequences in FASTA format
- Can use either:
  - Output from prophage workflow (automatic)
  - User-provided sequences (via --prophage_fasta)
- Recommended minimum sequence length: 5kb

#### Parameters

| Parameter | Description | Default | Wrapper Usage | Nextflow Usage |
|-----------|-------------|---------|---------------|----------------|
| `--prophage_fasta` | Input prophage sequences | null | `--prophage_fasta /path/to/prophages.fasta` | `--prophage_fasta /path/to/prophages.fasta` |
| `--min_prophage_length` | Minimum sequence length | 5000 | `--min_prophage_length 10000` | `--min_prophage_length 10000` |
| `--checkv_quality_levels` | Acceptable quality levels | ['Medium-quality', 'High-quality', 'Complete'] | `--checkv_quality_levels 'High-quality,Complete'` | `--checkv_quality_levels '["High-quality", "Complete"]'` |
| `--skip_detailed_annotation` | Skip Pharokka and PHOLD | false | `--skip_detailed_annotation true` | `--skip_detailed_annotation true` |
| `--pharokka_structural_perc` | Min % structural genes (Pharokka) | 20.0 | `--pharokka_structural_perc 25.0` | `--pharokka_structural_perc 25.0` |
| `--pharokka_structural_total` | Min structural genes (Pharokka) | 3 | `--pharokka_structural_total 4` | `--pharokka_structural_total 4` |
| `--phold_structural_perc` | Min % structural genes (PHOLD) | 20.0 | `--phold_structural_perc 25.0` | `--phold_structural_perc 25.0` |
| `--phold_structural_total` | Min structural genes (PHOLD) | 3 | `--phold_structural_total 4` | `--phold_structural_total 4` |
| `--clustering_min_ani` | Minimum ANI for clustering | 99.0 | `--clustering_min_ani 95.0` | `--clustering_min_ani 95.0` |
| `--clustering_min_coverage` | Minimum coverage for clustering | 85.0 | `--clustering_min_coverage 80.0` | `--clustering_min_coverage 80.0` |
| `--conda_cache` | Path to conda environment directory | `$HOME/phorager/conda_cache` | `--conda_cache /path/to/conda` | `--conda_cache_dir /path/to/conda` |
| `--db_location` | Path to database directory | `$HOME/phorager/databases` | `--db_location /path/to/db` | `--global_db_location /path/to/db` |

### Output Structure

```
results/
└── 3.Annotation/
    ├── Annotation_summary.log         # Overall workflow summary
    ├── Final_representatives.fasta    # Cluster representative sequences
    ├── Cluster_information.tsv       # Cluster assignments
    ├── Anno1_CheckV/                
    │   ├── checkv_output/           # Raw CheckV results
    │   └── filtered_prophages.fasta # Quality-filtered sequences
    ├── Anno2_SplitSequences/        # Individual sequence files
    ├── Anno3_Pharokka/              # Pharokka results for each sequence
    │   └── [sequence_name]_pharokka/
    │       ├── pharokka_proteins.faa
    │       └── pharokka_cds_functions.tsv
    ├── Anno4_PHOLD/                 # PHOLD results for each sequence
    │   └── [sequence_name]_phold/
    │       └── phold_all_cds_functions.tsv
    └── Anno5_FilteredResults/       
        ├── filtered_annotation_output.tsv
        └── annotation_filtered_sequences/
```

#### Output Files Description

1. **Summary Files**
   - `Annotation_summary.log`: Complete workflow summary
   - `Final_representatives.fasta`: Representative sequences from clusters
   - `Cluster_information.tsv`: Cluster assignments and members

2. **CheckV Results (Anno1_CheckV/)**
   - Quality assessment for each sequence
   - Completeness estimates
   - Quality-filtered sequences

3. **Annotation Results**
   - Pharokka functional annotations
   - PHOLD host-interaction predictions
   - Gene counts and categorizations
   - Structural gene identification

4. **Clustering Results**
   - All-vs-all BLAST results
   - ANI calculations
   - Final cluster assignments
   - Representative sequence selection

### Example Commands

1. Basic run with prophage workflow output:
```bash
# Using the wrapper script
./phorager annotation --prophage_fasta /path/to/prophages.fasta

# Or using Nextflow directly
nextflow run main.nf --workflow annotation
```

2. Run with custom input and quality thresholds:
```bash
# Using the wrapper script
./phorager annotation \
    --prophage_fasta /path/to/prophages.fasta \
    --min_prophage_length 10000 \
    --checkv_quality_levels 'High-quality,Complete'

# Or using Nextflow directly
nextflow run main.nf --workflow annotation \
    --prophage_fasta /path/to/prophages.fasta \
    --min_prophage_length 10000 \
    --checkv_quality_levels '["High-quality", "Complete"]'
```

3. Adjust structural gene requirements:
```bash
# Using the wrapper script
./phorager annotation \
    --pharokka_structural_perc 25.0 \
    --pharokka_structural_total 4 \
    --phold_structural_perc 25.0 \
    --phold_structural_total 4

# Or using Nextflow directly
nextflow run main.nf --workflow annotation \
    --pharokka_structural_perc 25.0 \
    --pharokka_structural_total 4 \
    --phold_structural_perc 25.0 \
    --phold_structural_total 4
```

4. Modified clustering parameters:
```bash
# Using the wrapper script
./phorager annotation \
    --clustering_min_ani 95.0 \
    --clustering_min_coverage 80.0

# Or using Nextflow directly
nextflow run main.nf --workflow annotation \
    --clustering_min_ani 95.0 \
    --clustering_min_coverage 80.0
```

5. Skip detailed annotation:
```bash
# Using the wrapper script
./phorager annotation \
    --skip_detailed_annotation true

# Or using Nextflow directly
nextflow run main.nf --workflow annotation \
    --skip_detailed_annotation true
```

6. Custom database and conda locations:
```bash
# Using the wrapper script
./phorager annotation \
    --conda_cache /path/to/conda \
    --db_location /path/to/databases

# Or using Nextflow directly
nextflow run main.nf --workflow annotation \
    --conda_cache_dir /path/to/conda \
    --global_db_location /path/to/databases
```

## End-to-End Workflow

### Overview
The `phorager run` command provides the possibility to run the bacterial genome analysis, prophage detection, and annotation in a single command.

### Parameters

#### Bacterial Workflow Parameters
- `--genome`: Input genome file or directory (Required)
- `--completeness-threshold`: Minimum genome completeness (%)
- `--contamination-threshold`: Maximum contamination allowed (%)
- `--drep-ani-threshold`: ANI threshold for dereplication

#### Prophage Workflow Parameters
- `--skip-genomad`: Skip geNomad detection step
- `--skip-vibrant`: Skip VIBRANT detection step
- `--use-dereplicated-genomes`: Use dereplicated genomes from bacterial workflow

#### Annotation Workflow Parameters
- `--min-prophage-length`: Minimum prophage sequence length
- `--skip-detailed-annotation`: Skip Pharokka and PHOLD annotation
- `--checkv-quality-levels`: Acceptable CheckV quality levels
- `--pharokka-structural-perc`: Minimum % structural genes (Pharokka)
- `--pharokka-structural-total`: Minimum structural genes (Pharokka)
- `--phold-structural-perc`: Minimum % structural genes (PHOLD)
- `--phold-structural-total`: Minimum structural genes (PHOLD)
- `--clustering-min-ani`: Minimum ANI for clustering
- `--clustering-min-coverage`: Minimum coverage for clustering

#### Common Parameters
- `--db-location`: Path to database directory
- `--conda-cache`: Path to conda environment directory
- `--outdir`: Output directory
- `--threads`: Number of threads to use
- `--verbose`: Enable detailed output
- `--force`: Force overwrite existing results

### Example Commands

1. Basic end-to-end analysis:
```bash
./phorager run --genome /path/to/genomes
```

2. Customized analysis:
```bash
./phorager run --genome /path/to/genomes \
    --completeness-threshold 90 \
    --skip-vibrant \
    --min-prophage-length 4000 \
    --clustering-min-ani 95.0
```



