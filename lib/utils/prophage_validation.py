"""
Prophage Validation Utilities

Validation functions for the prophage workflow command.
"""

from pathlib import Path
from typing import Tuple, List, Optional


def validate_and_detect_genome_input(genome_path: str) -> Tuple[bool, Optional[str], Optional[Path], Optional[str]]:
    """
    Validate and detect the type of genome input
    
    Returns:
        Tuple of (is_valid, input_mode, validated_path, error_message)
        input_mode: 'file' | 'directory' | 'bacterial_workflow' | None
    """
    path = Path(genome_path)
    
    if not path.exists():
        return (False, None, None, f"Path does not exist: {genome_path}")
    
    # Check if it's a file
    if path.is_file():
        if path.suffix.lower() in ['.fa', '.fasta', '.fna']:
            return (True, 'file', path, None)
        else:
            return (False, None, None, 
                   f"Invalid file extension: {path.suffix}. Must be .fa, .fasta, or .fna")
    
    # Check if it's a directory
    if path.is_dir():
        # First check for bacterial workflow structure
        bacterial_genomes = path / "1.Genome_preprocessing" / "Bact3_dRep" / "drep_output" / "dereplicated_genomes"
        
        if bacterial_genomes.exists() and bacterial_genomes.is_dir():
            # Validate it has genome files
            genome_files = (list(bacterial_genomes.glob("*.fa")) + 
                          list(bacterial_genomes.glob("*.fasta")) + 
                          list(bacterial_genomes.glob("*.fna")))
            
            if genome_files:
                return (True, 'bacterial_workflow', path, None)
            else:
                return (False, None, None, 
                       f"Bacterial workflow directory structure found but no genome files in:\n"
                       f"  {bacterial_genomes}")
        
        # Not bacterial structure, check for genome files directly in directory
        genome_files = (list(path.glob("*.fa")) + 
                       list(path.glob("*.fasta")) + 
                       list(path.glob("*.fna")))
        
        if genome_files:
            return (True, 'directory', path, None)
        else:
            return (False, None, None, 
                   f"Directory contains no .fa, .fasta, or .fna files: {genome_path}")
    
    return (False, None, None, f"Path is neither a file nor a directory: {genome_path}")


def validate_tool_selection(skip_genomad: bool, skip_vibrant: bool, 
                           genomad_preset: Optional[str], 
                           vibrant_min_length: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate tool selection and parameter conflicts
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check both tools aren't skipped
    if skip_genomad and skip_vibrant:
        return (False, "Cannot skip all tools. At least one prophage detection tool must run.")
    
    # Check for conflicting parameters - GenoMAD
    if skip_genomad and genomad_preset is not None:
        return (False, "Cannot set --genomad-preset when --skip-genomad is enabled")
    
    # Check for conflicting parameters - VIBRANT
    if skip_vibrant and vibrant_min_length is not None:
        return (False, "Cannot set --vibrant-min-length when --skip-vibrant is enabled")
    
    return (True, None)


def validate_genomad_preset(preset: str) -> Tuple[bool, Optional[str]]:
    """
    Validate GenoMAD preset value
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_presets = ['default', 'conservative', 'relaxed']
    
    if preset not in valid_presets:
        return (False, f"Invalid GenoMAD preset: '{preset}'. Must be one of: {', '.join(valid_presets)}")
    
    return (True, None)


def validate_vibrant_min_length(min_length: int) -> Tuple[bool, Optional[str]]:
    """
    Validate VIBRANT minimum scaffold length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if min_length < 500:
        return (False, f"VIBRANT min length too small: {min_length} bp. Must be at least 500 bp")
    
    if min_length > 50000:
        return (False, f"VIBRANT min length too large: {min_length} bp. Must be at most 50000 bp")
    
    return (True, None)


def validate_databases(db_location: str, skip_genomad: bool, skip_vibrant: bool) -> Tuple[bool, Optional[str]]:
    """
    Check that required databases exist
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    db_path = Path(db_location)
    missing_dbs = []
    
    # Check GenoMAD database if tool will run
    if not skip_genomad:
        genomad_db = db_path / "genomad_database"
        if not genomad_db.exists():
            missing_dbs.append(("GenoMAD", "genomad", str(genomad_db)))
    
    # Check VIBRANT database if tool will run
    if not skip_vibrant:
        vibrant_db = db_path / "vibrant_database"
        if not vibrant_db.exists():
            missing_dbs.append(("VIBRANT", "vibrant", str(vibrant_db)))
    
    if missing_dbs:
        error_msg = "Missing required databases:\n"
        for tool_name, db_name, db_path in missing_dbs:
            error_msg += f"  - {tool_name}: {db_path} not found\n"
        error_msg += "\nInstall missing databases with:\n"
        db_names = ','.join([db[1] for db in missing_dbs])
        error_msg += f"  phorager install --databases {db_names}"
        return (False, error_msg)
    
    return (True, None)