# parsing-env: Python data-parsing environment for PHORAGER utility processes
# Package versions match conda_tools.config (pandas 2.2.3, biopython 1.84).
FROM mambaorg/micromamba:1.5.10

RUN micromamba install -y -n base -c conda-forge \
      pandas=2.2.3 \
      biopython=1.84 \
 && micromamba clean --all --yes

# Put the base env on PATH. `singularity/apptainer exec` bypasses the image
# ENTRYPOINT that micromamba normally uses to activate the env, so binaries
# must be discoverable on the default PATH (same convention as the quay.io
# biocontainers already used by the pipeline).
ENV PATH=/opt/conda/bin:$PATH
