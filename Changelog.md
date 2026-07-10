# Changelog

All notable changes to PHORAGER will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Nextflow 26.04+ compatibility: pipeline failed to compile under the strict syntax parser**
  - Nextflow 26.04 enables the strict (v2) syntax parser by default. `nextflow lint .` reported 15 errors across `main.nf` and `install_vibrant_database.nf`, and the pipeline would not run at all on 26.04+ without these fixes
  - `main.nf` mixed top-level `log.info` statements with script declarations (`include`, `nextflow.enable.dsl`), which the strict parser rejects. Fixed by moving the startup banner into the entry `workflow { }` block
  - Beyond what `nextflow lint` reported, actually compiling under the strict parser surfaced a separate, narrower bug: a `publishDir` directive written as a plain interpolated string that references an input-block variable fails to resolve that variable (`No such variable: <name>`) under the strict parser, even though the identical pattern in a `tag` directive works fine and `nextflow lint` does not flag it. This affected five processes in the prophage-detection pipeline: `genomad.nf`, `vibrant.nf`, `parse_genomad.nf`, `parse_vibrant.nf`, and `compare_prophages.nf`. Fixed by switching to the closure form (`publishDir { "..." }`), which is standard, documented Nextflow syntax and resolves correctly under both parsers
  - All fixes are backward compatible with the legacy (v1) parser — no v2-only syntax was introduced, so the pipeline continues to run unchanged on previously-supported Nextflow versions

- **VIBRANT database installation could silently fail or write its completion log to the wrong directory (`install_vibrant_database.nf`)**
  - `WORK_DIR="$PWD"` and `cd $WORK_DIR` were unescaped inside the process `script:` blocks. Because Nextflow interpolates unescaped `$var` references in script blocks itself (before bash ever runs), `$PWD` was resolved by Nextflow to the pipeline's *launch* directory — the directory `nextflow run` was invoked from — not the task's own working directory as intended, and not the value bash's own `$PWD` would have held at that point
  - Confirmed by isolated testing: the subsequent `cd $WORK_DIR` moved execution into the launch directory instead of back into the task directory, so the install-check log file (`vibrant_database_install_check.log`) was written outside the location Nextflow expects for the declared process output. On a fresh VIBRANT database build (not the "already installed" skip path), this very likely caused the process to fail with a missing-output-file error on every run, rather than silently succeeding with misplaced output
  - Fixed by escaping as `\$PWD` / `\$WORK_DIR` (lines 29, 169, 183, 270) so bash resolves them at the task's own working directory, matching the escaping convention already used elsewhere in the same file (e.g. `actual_size=\$(du -sh ...)`)

- **`--run_genomad false`, `--run_vibrant false`, `--rename_contigs false`, and `--skip_detailed_annotation true` could be silently ignored depending on Nextflow version**
  - Nextflow's strict syntax parser disables the legacy automatic type-coercion of CLI parameter values. Under the legacy parser, `--run_genomad false` was coerced to the Groovy boolean `false`; under the strict parser it remains the string `'false'`, which is truthy in a Groovy `if (params.run_genomad)` check. This means the flag intended to *disable* geNomad, VIBRANT, contig renaming, or detailed annotation could instead have had no effect at all on Nextflow versions using the strict parser, without any error or warning
  - Fixed by declaring these four params' defaults as strings in `configs/base.config` and coercing explicitly with `.toBoolean()` at every place they're evaluated as booleans (`workflows/prophage.nf`, `workflows/annotation.nf`). Verified to produce identical results under both the legacy and strict parsers, and across CLI-supplied and default values
  - `annotation_summary.nf`'s existing `'${skip_detailed_annotation}'.lower() == 'true'` string comparison was already safe under both parsers and is unchanged

- **`summarize.nf` accessed `projectDir` from inside the process body**
  - Flagged as discouraged practice under the strict parser (input files should be declared as process inputs, not referenced via `projectDir` inside a task). Not a functional bug on its own, but the process also used a singularity `--bind ${projectDir}:${projectDir}` mount to compensate, which is fragile outside local/Singularity execution
  - Fixed by passing the runner script and its `summaries` Python package as proper `path` inputs, constructed from `projectDir` in the calling workflow (`main.nf`) rather than inside the process, and removing the now-unnecessary `--bind` — the staged files live in the task's own working directory, which is mounted into the container by default

- **Singularity-backend installs attempting to build Conda environments and failing with `conda: command not found`**
  - Reported symptom: with `"backend": "singularity"` configured, `phorager install` printed `Profile: standard` (correct) but then tried to create a Conda environment before running any tool logic, and failed on systems without Conda on `PATH`
  - Root cause: Conda was enabled globally by default, and the only thing turning it off for Singularity was Nextflow implicitly falling back to the `standard` profile. Anything that perturbed profile resolution (a site-wide `$NXF_HOME/config`, an `NXF_CONDA_ENABLED` environment variable, an extra `-c` config file) silently re-enabled Conda for Singularity users
  - Fixed by making Conda opt-in only, passing the backend's profile explicitly from the CLI instead of relying on an implicit default, and making the per-process profile check tolerant of multi-profile invocations

### Changed

- **Deprecation cleanup for Nextflow 26.04+**: `nextflow lint .` also reported 93 deprecation warnings across 13 files; none were functional bugs, but all are addressed to keep the pipeline warning-clean going forward
  - Replaced deprecated `Channel` channel-factory access with lowercase `channel` (~25 occurrences across `workflows/*.nf`)
  - Declared explicit closure parameters in place of the implicit `it` (~35 occurrences), using names that reflect what the channel carries (e.g. `tool ->`, `count ->`, `coord_file ->`) instead of generic placeholders
  - Prefixed genuinely-unused closure parameters with `_` to suppress the warning without changing behaviour (~24 occurrences, e.g. `.map { _tool -> install_logs_dir }`)
  - Removed the unused `def description = db_spec.description` local variable from six `install_*_database.nf` files (checkm2, checkv, genomad, pharokka, phold, vibrant); confirmed unused elsewhere in each file before removal
  - Deferred: `workflows/summarize.nf`'s two `projectDir`-in-process warnings were addressed separately above rather than folded into this mechanical pass, since the fix changes container bind logic rather than being a pure rename/refactor

### Technical Details

- **Conda default inversion**: `configs/base.config`'s `conda { }` scope now sets `enabled = false` (previously `true`). Conda is enabled only via the explicit `conda.enabled = true` override inside the `conda` profile block in `configs/profiles.config`, which was already present and is unchanged. The unconditional `conda` process directives in `configs/conda_tools.config` are left in place — they are inert when `conda.enabled` is false and remain required by the `conda` profile
- **Explicit profile flag**: `install.py`, `bacterial.py`, `prophage.py`, `annotation.py`, and `summarize.py` previously passed `-profile conda` only for the Conda backend and relied on Nextflow's implicit `standard` profile for Singularity. Each now passes `-profile conda` or `-profile singularity` explicitly based on `config['backend']`, and raises a `ValueError` on an unrecognized backend value instead of silently omitting the flag
- **Profile composability**: all 34 process `.nf` files under `modules/` gated their Singularity script branch on `workflow.profile == 'standard' || workflow.profile.contains('singularity')`. The exact-equality check against `'standard'` failed for any multi-profile invocation (e.g. `-profile standard,benchmark`), silently falling through to the Conda branch. Changed to `workflow.profile.contains('singularity') || workflow.profile.contains('standard')`; the `else if` Conda branch and final `else` error branch are unchanged
- **Manifest block**: `nextflow.config` declares `manifest { name, version, nextflowVersion }`. `nextflowVersion` is now `'>=24.04.0'` (raised from `'>=23.04.0'`), reflecting the floor actually tested against the strict-syntax fixes in this release; no upper bound is set since the pipeline now compiles under both the legacy and strict (26.04+) parsers
- **`$PWD` interpolation in Nextflow script blocks**: confirmed empirically (via an isolated repro process run under `NXF_SYNTAX_PARSER=v1`) that an unescaped `$PWD`/`$VAR` inside a `"""..."""` script block is resolved by Nextflow's Groovy layer at script-assembly time, using the pipeline's launch directory — not the task's own working directory, and not a compile error under the legacy parser, which is why this went undetected until the strict-parser lint pass
- **`each` was not the cause of the `publishDir` v2 bug**: initial investigation suspected the `each path(...)` input qualifier (used by `genomad.nf`/`vibrant.nf` to broadcast a single database channel across many genome files) was responsible, since both affected files use it. Isolated testing showed `each` alone is unaffected — a plain `path` input with a `publishDir` string referencing it fails identically. The five affected files were identified by scanning for `publishDir` directives (as plain strings, not closures) that reference any variable declared in the same process's `input:` block
- **Boolean coercion scheme verified empirically**: tested all six combinations of `{NXF_SYNTAX_PARSER=v1, v2} × {--flag true, --flag false, no override}` against a string-typed `params` default with `.toBoolean()` at the read site. Under v1, a CLI-supplied `true`/`false` value is still coerced to a real Groovy `Boolean` regardless of the declared default's type (i.e. changing the default to a string does not, by itself, fix the issue) — `.toBoolean()` returns the correct result whether called on a `String` or a `Boolean`, which is why explicit coercion at every read site (rather than relying on the default's type) is required for correctness under both parsers
- **Pre-existing, unrelated issue found during verification (not fixed here)**: `configs/base.config`'s `errorStrategy = { task.attempt <= maxRetries ? 'retry' : 'ignore' }` closure throws a `ClassCastException` (`ConfigObject cannot be cast to Integer`) when Nextflow evaluates it after certain task failures, masking the real error behind a Groovy stack trace. Reproduced under both parsers; unrelated to the strict-syntax migration and out of scope for this change

## [v0.5.0-beta] - 2026-05-16

### Fixed

- **CheckV two-fragment split: `_2` fragments missing quality data in prophage table**
  - When CheckV detects two distinct viral sub-regions separated by bacterial genes within a single provirus, it produces two fragments in `proviruses.fna` with `_1` and `_2` suffixes. Both fragments are correctly extracted and annotated by the pipeline, but `_get_checkv_data` in `prophage_table.py` only handled the `_1` case when looking up quality data in `quality_summary.tsv` (which records the original input name without any suffix). All `_2` fragments therefore reported `NA` for `CheckV_quality` in the prophage table
  - Fixed by extending the suffix-stripping logic in `_get_checkv_data` to cover both `_1` and `_2` before retrying the lookup

- **CheckV fragment length reporting in prophage table**
  - The `Phage_length` column for `_1` fragments previously inherited `proviral_length` from the parent entry in `quality_summary.tsv`. This value represents the full trimmed proviral region, not the individual fragment, making it inaccurate for both `_1` and `_2`
  - Fixed by computing `Phage_length` from the actual sequence length (`len(record.seq)`) read directly from `filtered_phage_set.fasta` for all CheckV fragments (`_1` and `_2`). Non-fragment sequences continue to use `proviral_length` from the CheckV index as before.

- **Selective publishing of key Pharokka and PHOLD annotation outputs** — the annotation workflow now copies a curated subset of files per sample to the output directory by default, replacing the previous behaviour of publishing nothing (`enabled: false`)
  - Pharokka outputs published to `3.Annotation/Anno3_Pharokka/<sample>_pharokka/`:
    - `pharokka.gbk`, `pharokka.gff`, `pharokka_cds_functions.tsv`, `pharokka_length_gc_cds_density.tsv`, `pharokka_top_hits_mash_inphared.tsv`
  - PHOLD outputs published to `3.Annotation/Anno4_PHOLD/<sample>_phold/`:
    - `phold_all_cds_functions.tsv`, `phold_per_cds_predictions.tsv`, `phold_output.gbk`
  - Full tool output directories are intentionally excluded to avoid the large file volumes and write conflicts seen on HPC shared filesystems with previous full-directory publishing
  - NO_HITS samples (PHOLD sequences with no Foldseek structural hits) are handled gracefully — no publish directory is created and the pipeline continues normally

### Technical Details

- **Why both fragments reach annotation**: `extract_sequences` in `parse_checkv.nf` uses substring matching (`f_id in record.id`) against the parent ID from `quality_summary.tsv`. This correctly matches both `_1` and `_2` entries in `proviruses.fna`, so both fragments have always been extracted, split, and passed to Pharokka and PHOLD. The bug was purely in the summary table lookup, not in the annotation path
- **Fragment length source**: `filtered_phage_set.fasta` is already iterated record-by-record in `generate()`, making `len(record.seq)` available at zero additional I/O cost — no new file dependencies are introduced
- **Implementation**: Nextflow's `publishDir` with `pattern` and `saveAs` cannot filter inside process output directories — only top-level path names are matched. The fix stages selected files into a temporary `*_pharokka_pub` / `*_phold_pub` sibling directory inside the process script, declares it as an optional secondary output, and uses `saveAs` to strip the `_pub` suffix on publish. The internal `*_pharokka` / `*_phold` directories used by downstream processes are unaffected.
- **Recovery from previous runs**: users whose `.nextflow/` cache directory is intact can recover published outputs from a prior run without recomputation using `-resume`. If the cache has been deleted, the `recover_annotations.sh` utility script can reconstruct the same output structure by scanning the `tmp/` work directory directly.


## [v0.4.0-beta] - 2026-04-10

### Added

- **Summary workflow (`phorager summarize`)** — post-hoc summary table generation from completed pipeline outputs
  - New `phorager summarize` command that runs as a Nextflow workflow inside the existing `parsing_env` environment (Singularity or Conda), consistent with all other pipeline commands
  - Two summary types currently available:
    - `bacterial_genome` — one row per genome with CheckM2 QC metrics (completeness, contamination, genome size, GC content, N50, CDS count) plus prophage count derived from annotation output
    - `prophage_table` — one row per prophage with bacterial host, cluster representative, CheckV quality tier, phage length, and CDS count
  - Output written to `{outdir}/4.Summaries/{type}.tsv` (or `.csv` with `--format csv`)
  - Graceful handling of optional inputs: `bacterial_genome` runs without annotation output (prophage count defaults to 0 with a warning); `prophage_table` runs without annotation filtering output (CDS count returns `NA` with a warning, e.g. when `--skip-detailed-annotation` was used)
  - `--dry-run` support showing the exact Nextflow command and expected output path before execution
  - `--list` flag to display all available summary types and descriptions
  - Extensible registry-based architecture: new summary types can be added by creating one file in `lib/summaries/` and adding one line to `lib/commands/summarize.py` — see `ADDING_NEW_SUMMARIES.md`

- **`ADDING_NEW_SUMMARIES.md`** — developer documentation for extending the summary toolkit with new table types, including a worked template, file path reference table, and checklist

- **Summary toolkit test suite** — 106 unit and integration tests covering:
  - Registry registration, retrieval, and error handling
  - Per-column correctness for both summary types
  - Edge cases: empty FASTA, missing optional files, proviral `_1` suffix matching, empty CheckV output, `NA`/`None` proviral length strings, empty cluster files, unexpected prophage ID formats

### Fixed

- **Critical: Local Python packages bleeding into Singularity containers causing CheckM2 (and potentially other tools) to fail**
  - CheckM2 failed with `AttributeError: 'MinMaxScaler' object has no attribute 'clip'` during the ML prediction step
  - Root cause: Singularity mounts `$HOME` by default, making `~/.local/lib/python3.8/site-packages/` visible inside the container. A locally installed sklearn 1.0.2 was shadowing the container's sklearn 0.23.2, which is the version the CheckM2 model pickle was built with. The 1.0.2 `MinMaxScaler` lacks the `clip` attribute expected by the unpickled object
  - All `singularity exec` calls across the pipeline were missing the `--no-home` flag, leaving every Python-based tool vulnerable to the same class of conflict
  - Fixed by adding `--no-home` to all `singularity exec` invocations in: `checkm2.nf`, `checkv.nf`, `drep.nf`, `phold.nf`, `cluster_phages.nf`, `extract_representatives.nf`, `filter_genomes.nf`, `parse_checkv.nf`, `parse_filter_annotations.nf`, `annotation_summary.nf`, `rename_contigs.nf`, `split_fasta.nf`, `summary_report.nf`, `compare_prophages.nf`, `parse_genomad.nf`, `parse_vibrant.nf`, `prophage_summary.nf`, `genomad.nf`, `vibrant.nf`, and `pharokka.nf`
  - Note: `singularity.runOptions` in `nextflow.config` has no effect here because all Singularity calls are manual `singularity exec` invocations inside process scripts, bypassing Nextflow's executor-managed container handling entirely

- **CLUSTER_PHAGES failure with `--no-home` due to symlinked `anicalc.py` / `aniclust.py`**
  - After adding `--no-home`, `anicalc.py` and `aniclust.py` became inaccessible inside the container
  - Root cause: Nextflow stages these `path` inputs as symlinks pointing to `/hpc-home/zar24gir/PHORAGER/bin/`. With `--no-home`, `/hpc-home` is not mounted inside the container, so Python cannot follow the symlink to the script
  - Fixed in `cluster_phages.nf` by dereferencing the symlinks into real copies in the work directory before the container calls, using `cp --dereference`

- **Prophage–CheckV name mismatch for proviral sequences**
  - CheckV appends `_1` to sequences it identifies as proviruses in `proviruses.fna` (its trimmed output). `PARSE_CHECKV` extracts sequences from this file, so downstream files including `filtered_phage_set.fasta` carry the `_1` suffix. However, `quality_summary.tsv` records the original input name without `_1`, causing all proviral sequences to report `NA` for CheckV quality and length in the prophage table
  - Fixed in `_get_checkv_data`: exact name match is tried first; if it fails and the name ends in `_1`, the suffix is stripped and the lookup retried before falling back to `NA`

### Technical Details

- **Architecture**: `phorager summarize` follows the same delegation pattern as all other commands — the Python wrapper validates arguments and builds a `nextflow run main.nf --workflow summarize` command; all execution and environment management is handled by Nextflow. No Python packages beyond those already in `parsing_env` (pandas, biopython) are required
- **Output path convention**: `4.Summaries/` follows the numbered subdirectory convention established by the other three workflows (`1.Genome_preprocessing/`, `2.Prophage_detection/`, `3.Annotation/`). The same `--outdir` used for other workflows is passed to `phorager summarize`
- **`filtered_phage_set.fasta` location**: the file is published under `3.Annotation/Anno5_FilteredResults/annotation_filtered_sequences/` by `PARSE_FILTER_ANNOTATIONS`. It is staged as input to `CLUSTER_PHAGES` but not re-published from there

---

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
