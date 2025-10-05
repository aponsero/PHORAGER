<div align="center">
  <img src="phorager_logo.png" alt="Phorager Logo" width="400"/>

  # Phorager
  ### Prophage Analysis Pipeline

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A522.10.0-23aa62.svg)](https://www.nextflow.io/)
  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

  A comprehensive pipeline for bacterial genome quality control, prophage detection, and prophage characterization
</div>

<div align="left">

**Authors:**  

- Xena Dyball
- James Docherty
- [Alise Ponsero](https://github.com/aponsero)
- Ryan Cook

**Citation:**
[Paper Citation or Preprint Link]

</div>

## Overview

Phorager provides an integrated workflow for:

- **Bacterial genome quality control** - CheckM2 assessment, filtering, and dRep dereplication
- **Prophage detection** - GenoMAD and VIBRANT-based identification of integrated prophages
- **Phage annotation** - CheckV quality assessment, Pharokka annotation, and Phold function prediction

> **Note**: Phorager is currently in beta release. We welcome feedback, bug reports, and feature requests through our [issue tracker](../../issues).

## Quick Start

### 1. Configure
Set your preferred installation backend and locations:

```bash
phorager config set --backend conda --db-location /data/phorager
```

### 2. Install
Install required tools and databases:

```bash
# Install tools for bacterial genome analysis
phorager install --tools genome --databases checkm2

# Install prophage detection tools
phorager install --tools prophage --databases genomad,vibrant
```

### 3. Run Analysis
Execute workflows on your data:

```bash
# Bacterial genome quality control
phorager bacterial --genome /path/to/genomes

# Prophage detection
phorager prophage --genome /path/to/genomes
```

## Prerequisites

- [Nextflow](https://www.nextflow.io/) (≥ 21.04.0)
- Either [Conda/Mamba](https://docs.conda.io/en/latest/) or [Singularity](https://sylabs.io/singularity/)

## Documentation

**For detailed documentation, see the [Wiki](../../wiki):**

- [Configuration Management](../../wiki/Configuration) - Backend setup and locations
- [Installation Management](../../wiki/Installation) - Tools and database installation
- [Bacterial Workflow](../../wiki/Bacterial-Workflow) - Genome quality control and dereplication
- [Prophage Workflow](../../wiki/Prophage-Workflow) - Integrated prophage detection

## Getting Help

- Check command-specific help: `phorager [command] --help`
- View available tools and databases: `phorager install --list-available`
- Preview commands before running: `phorager [command] --dry-run`
- See current configuration: `phorager config show`

## Reporting Issues and Feedback

Phorager is actively being developed and improved. We encourage users to:

- **Report bugs** - Found an issue? [Open a bug report](../../issues/new)
- **Request features** - Have an idea for improvement? [Submit a feature request](../../issues/new)
- **Ask questions** - Need help? [Start a discussion](../../issues/new)
- **Share feedback** - Let us know about your experience using Phorager

When reporting issues, please include:
- Command used
- Error messages or unexpected behavior
- Phorager version and backend (conda/singularity)
- System information (OS, available resources)

