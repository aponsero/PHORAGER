# create test env if not present

micromamba create -n pytest
micromamba activate pytest
micromamba install -c conda-forge pytest pandas biopython openpyxl

# Run pytest

micromamba activate pytest
cd PHORAGER
##### From the project root (where lib/ and tests/ live)
pytest tests/ -v

