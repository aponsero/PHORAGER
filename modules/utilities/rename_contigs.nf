process RENAME_CONTIGS {
    tag "Renaming contigs in ${genome_files.size()} genomes"
    publishDir "${params.outdir}/2.Prophage_detection/Proph1_Rename", mode: 'copy'

    input:
    path genome_files

    output:
    path "renamed_genomes/*.{fa,fasta,fna}", emit: renamed_genomes
    path "contig_name_mapping.tsv", emit: mapping

    script:
    // This process uses the parsing_env (Python + BioPython)
    def tool_spec = params.container_specs['parsing_env']
    def container_path = "${params.singularity_cache_dir}/${tool_spec.image}"
    def container_url = tool_spec.singularity_url
    
    // Validate required configuration
    if (!container_url) {
        error "Missing singularity_url in container_specs for parsing_env"
    }
    
    // Detect backend by profile name
    if (workflow.profile == 'standard' || workflow.profile.contains('singularity'))
        """
        echo "Renaming contigs via Singularity container..."
        echo "Processing ${genome_files.size()} genome files"
        
        # Create singularity cache directory if it doesn't exist
        mkdir -p ${params.singularity_cache_dir}
        
        # Pull container if it doesn't exist
        if [ ! -f "${container_path}" ]; then
            echo "Pulling parsing environment container..."
            singularity pull ${container_path} ${container_url}
        else
            echo "Parsing environment container already exists, using cached version."
        fi
        
        # Create the Python script
        cat > rename_contigs.py << 'EOFPYTHON'
#!/usr/bin/env python3
from Bio import SeqIO
import os
from pathlib import Path
from collections import Counter

def get_padding_width(num_contigs):
    if num_contigs < 1000:
        return 3
    elif num_contigs < 10000:
        return 4
    else:
        return 5

def detect_duplicate_basenames(genome_files):
    basenames = [Path(f).stem for f in genome_files]
    basename_counts = Counter(basenames)
    basename_versions = {}
    basename_mapping = {}
    
    for genome_file in genome_files:
        original_basename = Path(genome_file).stem
        
        if basename_counts[original_basename] > 1:
            if original_basename not in basename_versions:
                basename_versions[original_basename] = 1
            version = basename_versions[original_basename]
            unique_basename = f"{original_basename}_v{version}"
            basename_versions[original_basename] += 1
        else:
            unique_basename = original_basename
        
        basename_mapping[genome_file] = unique_basename
    
    return basename_mapping

def rename_contigs(genome_files):
    os.makedirs("renamed_genomes", exist_ok=True)
    basename_mapping = detect_duplicate_basenames(genome_files)
    mapping_data = []
    
    for genome_file in genome_files:
        unique_basename = basename_mapping[genome_file]
        original_basename = Path(genome_file).stem
        contig_count = sum(1 for _ in SeqIO.parse(genome_file, "fasta"))
        padding_width = get_padding_width(contig_count)
        contig_counter = 1
        renamed_records = []
        
        for record in SeqIO.parse(genome_file, "fasta"):
            new_name = f"{unique_basename}_ctg{str(contig_counter).zfill(padding_width)}"
            mapping_data.append({
                'genome_file': original_basename,
                'genome_basename_used': unique_basename,
                'original_contig_name': record.id,
                'new_contig_name': new_name,
                'contig_length': len(record.seq)
            })
            original_id = record.id
            record.id = new_name
            record.description = f"{new_name} (original: {original_id})"
            renamed_records.append(record)
            contig_counter += 1
        
        original_ext = Path(genome_file).suffix
        output_file = f"renamed_genomes/{unique_basename}{original_ext}"
        SeqIO.write(renamed_records, output_file, "fasta")
        print(f"Renamed {contig_count} contigs in {genome_file} -> {output_file}")
    
    with open("contig_name_mapping.tsv", 'w') as f:
        f.write("genome_file\\tgenome_basename_used\\toriginal_contig_name\\tnew_contig_name\\tcontig_length\\n")
        for entry in mapping_data:
            f.write(f"{entry['genome_file']}\\t{entry['genome_basename_used']}\\t{entry['original_contig_name']}\\t{entry['new_contig_name']}\\t{entry['contig_length']}\\n")
    
    print(f"\\nRenaming complete. Processed {len(genome_files)} genome files.")
    print(f"Total contigs renamed: {len(mapping_data)}")

import sys
genome_files = sys.argv[1:]
rename_contigs(genome_files)
EOFPYTHON
        
        # Run the Python script using the container
        singularity exec --no-home ${container_path} python3 rename_contigs.py ${genome_files}
        
        # Verify output directory was created and contains files
        if [ ! -d "renamed_genomes" ]; then
            echo "ERROR: Output directory 'renamed_genomes' not created"
            exit 1
        fi
        
        file_count=\$(ls renamed_genomes/*.{fa,fasta,fna} 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No renamed genome files created in output directory"
            exit 1
        fi
        
        if [ ! -f "contig_name_mapping.tsv" ]; then
            echo "ERROR: Mapping file 'contig_name_mapping.tsv' not created"
            exit 1
        fi
        
        echo "Contig renaming completed successfully. Created \$file_count renamed genome files."
        """
    
    else if (workflow.profile.contains('conda'))
        """
        echo "Renaming contigs via Conda environment..."
        echo "Processing ${genome_files.size()} genome files"
        
        # Create the Python script
        cat > rename_contigs.py << 'EOFPYTHON'
#!/usr/bin/env python3
from Bio import SeqIO
import os
from pathlib import Path
from collections import Counter

def get_padding_width(num_contigs):
    if num_contigs < 1000:
        return 3
    elif num_contigs < 10000:
        return 4
    else:
        return 5

def detect_duplicate_basenames(genome_files):
    basenames = [Path(f).stem for f in genome_files]
    basename_counts = Counter(basenames)
    basename_versions = {}
    basename_mapping = {}
    
    for genome_file in genome_files:
        original_basename = Path(genome_file).stem
        
        if basename_counts[original_basename] > 1:
            if original_basename not in basename_versions:
                basename_versions[original_basename] = 1
            version = basename_versions[original_basename]
            unique_basename = f"{original_basename}_v{version}"
            basename_versions[original_basename] += 1
        else:
            unique_basename = original_basename
        
        basename_mapping[genome_file] = unique_basename
    
    return basename_mapping

def rename_contigs(genome_files):
    os.makedirs("renamed_genomes", exist_ok=True)
    basename_mapping = detect_duplicate_basenames(genome_files)
    mapping_data = []
    
    for genome_file in genome_files:
        unique_basename = basename_mapping[genome_file]
        original_basename = Path(genome_file).stem
        contig_count = sum(1 for _ in SeqIO.parse(genome_file, "fasta"))
        padding_width = get_padding_width(contig_count)
        contig_counter = 1
        renamed_records = []
        
        for record in SeqIO.parse(genome_file, "fasta"):
            new_name = f"{unique_basename}_ctg{str(contig_counter).zfill(padding_width)}"
            mapping_data.append({
                'genome_file': original_basename,
                'genome_basename_used': unique_basename,
                'original_contig_name': record.id,
                'new_contig_name': new_name,
                'contig_length': len(record.seq)
            })
            original_id = record.id
            record.id = new_name
            record.description = f"{new_name} (original: {original_id})"
            renamed_records.append(record)
            contig_counter += 1
        
        original_ext = Path(genome_file).suffix
        output_file = f"renamed_genomes/{unique_basename}{original_ext}"
        SeqIO.write(renamed_records, output_file, "fasta")
        print(f"Renamed {contig_count} contigs in {genome_file} -> {output_file}")
    
    with open("contig_name_mapping.tsv", 'w') as f:
        f.write("genome_file\\tgenome_basename_used\\toriginal_contig_name\\tnew_contig_name\\tcontig_length\\n")
        for entry in mapping_data:
            f.write(f"{entry['genome_file']}\\t{entry['genome_basename_used']}\\t{entry['original_contig_name']}\\t{entry['new_contig_name']}\\t{entry['contig_length']}\\n")
    
    print(f"\\nRenaming complete. Processed {len(genome_files)} genome files.")
    print(f"Total contigs renamed: {len(mapping_data)}")

import sys
genome_files = sys.argv[1:]
rename_contigs(genome_files)
EOFPYTHON
        
        # Run the Python script using conda environment
        python3 rename_contigs.py ${genome_files}
        
        # Verify output directory was created and contains files
        if [ ! -d "renamed_genomes" ]; then
            echo "ERROR: Output directory 'renamed_genomes' not created"
            exit 1
        fi
        
        file_count=\$(ls renamed_genomes/*.{fa,fasta,fna} 2>/dev/null | wc -l)
        if [ "\$file_count" -eq 0 ]; then
            echo "ERROR: No renamed genome files created in output directory"
            exit 1
        fi
        
        if [ ! -f "contig_name_mapping.tsv" ]; then
            echo "ERROR: Mapping file 'contig_name_mapping.tsv' not created"
            exit 1
        fi
        
        echo "Contig renaming completed successfully. Created \$file_count renamed genome files."
        """
        
    else
        """
        echo "ERROR: No supported backend detected. Use -profile conda or -profile singularity" 
        exit 1
        """
}
