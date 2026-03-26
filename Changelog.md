# Changelog

All notable changes to PHORAGER will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Critical: Nextflow false failures on SLURM HPC due to job state polling race condition**
  - Processes reporting "terminated for an unknown reason -- Likely it has been terminated by the external system" with exit status `-` despite jobs completing successfully
  - Root cause: SLURM briefly removes jobs from `squeue` output during scheduler events or the `COMPLETING` state transition before the job wrapper has finished writing `.exitcode`. Nextflow polls `squeue`, sees the job gone, immediately tries to read `.exitcode`, fails, and declares the task terminated — even though the job is still running or has just finished
  - This manifested specifically on long-running processes (PHOLD ~10min, PARSE_FILTER_ANNOTATIONS ~34min, CLUSTER_PHAGES ~1h+) where the window for the race condition is larger
  - Fixed by adding an `executor` block to `nextflow.config` with three settings:
    ```groovy
    executor {
        exitReadTimeout = '15 min'   // Retry reading .exitcode file for up to 15min after job completion
        pollInterval = '30 sec'      // Reduce squeue polling frequency
        queueStatInterval = '3 min'  // Increase interval between squeue status checks, reducing race condition window
    }
    ```

- **Spurious PHOLD and PARSE_FILTER_ANNOTATIONS retry cascade**
  - When one long-running process was falsely declared failed, Nextflow sent SIGTERM to concurrently running tasks, causing those tasks to also appear failed on the next `--resume`
  - The two tasks would then perpetually kill each other across retries, producing growing retry counts (`retries: 8`) far exceeding `maxRetries`
  - Fixed by the executor block above preventing the initial false failure

- **Duplicate `errorStrategy` in `base.config`**
  - Two conflicting `errorStrategy` declarations existed, with the first (`'retry'`) immediately overridden by the second (closure), making it dead code and causing confusion about retry behaviour
  - Cleaned up to a single unambiguous declaration:
    ```groovy
    maxRetries = 3
    maxErrors = -1
    errorStrategy = { task.attempt <= maxRetries ? 'retry' : 'ignore' }
    ```

- **CLUSTER_PHAGES OOM failure on large datasets**
  - All-vs-all BLAST on 18,103 sequences requires substantially more memory than the default `4.GB * task.attempt` scaling
  - Increased baseline memory for `CLUSTER_PHAGES` to `50.GB * task.attempt` in `base.config`

### Technical Details

- **Diagnosis methodology**: The key diagnostic signal was the combination of (1) `.exitcode = 0` present in the work directory, (2) PHOLD/job logs showing successful completion with "phold run has finished", and (3) Nextflow reporting `exit: -` with "terminated for unknown reason". This pattern is distinct from genuine failures (non-zero exit codes) or OOM kills (exit code 137).

- **SLURM `COMPLETING` state**: When a SLURM job finishes, it enters a `COMPLETING` state during epilog execution before fully disappearing from `squeue`. During this window, Nextflow's `squeue` poll may see the job as absent while the `.command.run` wrapper is still executing. The `queueStatInterval` setting reduces the frequency of these polls, significantly reducing the probability of catching a job in this transient state.

- **Exit code 137**: Genuine OOM kills produce exit code 137 (SIGKILL from kernel OOM killer), which is distinct from the `-` exit status of the race condition. CLUSTER_PHAGES OOM was identified by this exit code combined with the `.command.err` showing `Killed` on the `blastn` command line.


## [v0.3.0-beta] -

### Fixed
- **PHOLD graceful handling of "no hits"**: PHOLD now handles sequences with no structural matches gracefully instead of failing
  - Sequences that legitimately lack known phage structural proteins are now processed successfully
  - Creates empty output directory with `NO_HITS.txt` marker for sequences with no Foldseek hits
  - Allows pipeline to continue when PHOLD cannot find structural matches (valid biological result)
  - These sequences are appropriately filtered out during annotation filtering step

### Changed
- **Parallelized annotation workflow**: Pharokka and PHOLD now process sequences in parallel instead of sequentially
  - Modified `split_fasta.nf` to output `file_list.txt` containing names of created files
  - Modified `annotation.nf` to create channels from physical files in SPLIT_FASTA work directory using file_list.txt
  - Applied same pattern to PHOLD to process Pharokka output directories in parallel
  - Added filtering to exclude combined `filtered_prophages.fasta` from parallel processing
  - Set `maxForks = 20` for PHAROKKA and PHOLD processes in `base.config` for concurrent execution
  - Disabled publishDir for PHAROKKA and PHOLD intermediate results (`enabled: false`)

### Technical Details
- The key insight: Nextflow process outputs with glob patterns (`path "*.fasta"`) always emit all matching files as a single collection. The solution creates a new channel by reading the file list and constructing file objects pointing to the physical files in the process work directory, then flattening to create individual emissions.

- PHOLD error handling: Modified `phold.nf` to capture exit status and distinguish between "no structural hits found" (valid biology) versus true errors. Uses `set +e` to temporarily disable automatic failure, checks log output for the specific "Foldseek found no hits whatsoever" message, and creates placeholder output for graceful continuation.

---

## [v0.2.0-beta] - 2025-12-17

Release addressing main bugs in the prophage detection and annotation subworkflows.

### Fixed
- **Critical**: Fixed Pharokka environment bleedthrough issue
- Fixed bugs in prophage detection subworkflow
- Fixed bugs in annotation subworkflow

### Changed
- Work directory now located in `tmp/` folder within output directory for better organization
- dRep now runs using greedy algorithm when more than 10 genomes are provided (improves performance and avoids centrality calculation errors)
- Contigs are now renamed before prophage detection to avoid identifier conflicts with VIBRANT and GenoMAD

### Added
- Test set for pipeline installation verification

### Links
- [Full comparison v0.1.0-beta...v0.2.0-beta](https://github.com/aponsero/PHORAGER/compare/v0.1.0-beta...v0.2.0-beta)

---

## [v0.1.0-beta] - 2025-10-05

Initial beta release for user testing.

### Added
- **Bacterial genome workflow** with quality assessment and dereplication
  - CheckM2 genome quality assessment
  - Quality-based filtering
  - dRep genome dereplication
- **Dual backend support** for Conda and Singularity execution
- **Command-line wrapper** (`phorager` command) for easy pipeline execution
- **Prophage detection workflow** with GenoMAD and VIBRANT
- **Annotation workflow** with CheckV, Pharokka, and PHOLD

### Beta Testing Focus
Initial release seeking user feedback on:
- Installation process
- Workflow execution
- Bug reports and enhancement suggestions

---

## Version Guide

- **[Unreleased]** - Changes in development, not yet released
- **[vX.Y.Z-beta]** - Beta releases (feature-complete, testing phase)
- **[vX.Y.Z]** - Stable production releases

## Contributing

When contributing to PHORAGER, please:
1. Add your changes to the `[Unreleased]` section
2. Categorize changes appropriately (Added, Changed, Fixed, etc.)
3. Include relevant technical details for developers
4. Update the changelog as part of your pull request

## Reporting Issues

Please report issues at: https://github.com/aponsero/PHORAGER/issues

When reporting issues, include:
- Command used
- Error messages or unexpected behavior
- Phorager version and backend (conda/singularity)
- System information (OS, available resources)
