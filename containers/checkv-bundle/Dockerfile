# checkv-bundle: multi-tool environment for PHORAGER annotation/clustering.
# Used by CHECKV (checkv end_to_end), CLUSTER_PHAGES (makeblastdb/blastn),
# and EXTRACT_REPRESENTATIVES (seqfu). Package versions match conda_tools.config
# (python 3.9, checkv 1.0.3, blast 2.16.0, seqfu 1.22.0).
FROM mambaorg/micromamba:1.5.10

RUN micromamba install -y -n base -c conda-forge -c bioconda \
      python=3.9 \
      checkv=1.0.3 \
      blast=2.16.0 \
      seqfu=1.22.0 \
 && micromamba clean --all --yes

# See parsing-env Dockerfile for why PATH is set explicitly.
ENV PATH=/opt/conda/bin:$PATH
