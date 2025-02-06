conda activate prophage

## installation workflow test
###################################################################################
./phorager install
./phorager install --verbose --force

NEW_DB="/home/ubuntu/mount/Informatics/AlisePonsero/DEV_ZONE/version1/new_database"
./phorager install --db-location $NEW_DB

CONDA_NEW="/home/ubuntu/mount/Informatics/AlisePonsero/DEV_ZONE/version1/new_conda"
./phorager install --conda-cache $CONDA_NEW

## bacterial subworkflow
###################################################################################
genome_dir="../test_data"
mygenome="$genome_dir/GCF_008121495.1_ASM812149v1_genomic.fna"

./phorager bacterial --genome $mygenome
./phorager bacterial --genome $genome_dir

## Conda cache and databases
./phorager bacterial --genome $genome_dir --db-location $NEW_DB
./phorager bacterial --genome $genome_dir --conda-cache $CONDA_NEW

## output directory location
NEW_DIR="new_results"
./phorager bacterial --genome $genome_dir --outdir $NEW_DIR 

## thresholds of completeness/contamination
./phorager bacterial --genome $genome_dir --contamination-threshold 1
./phorager bacterial --genome $genome_dir --completeness-threshold 75

./phorager bacterial --genome $genome_dir --drep-ani-threshold 0.995

## Out of range values
./phorager bacterial --genome $genome_dir --contamination-threshold 1000
./phorager bacterial --genome $genome_dir --completeness-threshold 1000
./phorager bacterial --genome $genome_dir --drep-ani-threshold 10000
./phorager bacterial --genome thisdoesnotexists

###################################################################################
## to do 

### Prophage workflow wrapper + tune threads/tool usage
###################################################################################
genome_dir="../test_data"
mygenome="$genome_dir/GCF_008121495.1_ASM812149v1_genomic.fna"

./phorager prophage --genome $mygenome
./phorager prophage --genome $genome_dir


###################################################################################

### annotation workflow wrapper + tune threads/tool usage


