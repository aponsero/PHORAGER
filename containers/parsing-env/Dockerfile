FROM mambaorg/micromamba:1.5.10
RUN micromamba install -y -n base -c conda-forge -c bioconda \
      python=3.9 \
      checkv=1.0.3 \
      blast=2.16.0 \
      seqfu=1.22.0 \
 && micromamba clean --all --yes
ENV PATH=/opt/conda/bin:$PATH