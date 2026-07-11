FROM mambaorg/micromamba:1.5.10
RUN micromamba install -y -n base -c conda-forge \
      pandas=2.2.3 \
      biopython=1.84 \
 && micromamba clean --all --yes
# Put the env on PATH so `singularity exec` (which bypasses the image
# ENTRYPOINT) can find python without env activation
ENV PATH=/opt/conda/bin:$PATH