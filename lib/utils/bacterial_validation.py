"""
Bacterial Workflow Validation Utilities

Provides validation functions for bacterial genome quality control workflow.
Adapted from original wrapper validation logic with modular architecture.
"""

import os
import multiprocessing
from pathlib import Path
from typing import Dict


def validate_genome_input(genome_path: str) -> str:
    """
    Validate genome input (file or directory)
    
    Args:
        genome_path: Path to genome file or directory
        
    Returns:
        Validated genome path (absolute)
        
    Raises:
        ValueError: If genome path is invalid
    """
    if not genome_path:
        raise ValueError("Genome path cannot be empty")
    
    # Convert to absolute path
    genome_path = os.path.abspath(os.path.expanduser(genome_path))
    
    if not os.path.exists(genome_path):
        raise ValueError(f"Genome path does not exist: {genome_path}")
    
    if os.path.isfile(genome_path):
        # Validate file extension
        valid_extensions = ['.fa', '.fasta', '.fna']
        if not any(genome_path.endswith(ext) for ext in valid_extensions):
            raise ValueError(
                f"Invalid genome file extension. Must end with {', '.join(valid_extensions)}: {genome_path}"
            )
        return genome_path
    
    elif os.path.isdir(genome_path):
        # Check directory contains valid genome files
        genome_files = []
        for ext in ['.fa', '.fasta', '.fna']:
            genome_files.extend([
                f for f in os.listdir(genome_path) 
                if f.endswith(ext)
            ])
        
        if not genome_files:
            raise ValueError(
                f"No genome files found in directory. Files must end with .fa, .fasta, or .fna: {genome_path}"
            )
        
        return genome_path
    
    else:
        raise ValueError(f"Genome path is neither a file nor a directory: {genome_path}")


def validate_threads(threads) -> int:
    """
    Validate user-provided thread count
    
    Args:
        threads: Thread count (int or str)
        
    Returns:
        Validated thread count
        
    Raises:
        ValueError: If thread count is invalid
    """
    try:
        threads = int(threads)
        
        if threads < 1:
            raise ValueError("Thread count must be a positive integer")
        
        return threads
    except (ValueError, TypeError):
        raise ValueError(f"Invalid thread count: {threads}. Must be a positive integer.")


def validate_percentage_threshold(value, name: str) -> float:
    """
    Validate percentage thresholds (0-100)
    
    Args:
        value: Threshold value
        name: Parameter name for error messages
        
    Returns:
        Validated threshold value
        
    Raises:
        ValueError: If threshold is invalid
    """
    try:
        float_value = float(value)
        if float_value < 0 or float_value > 100:
            raise ValueError(f"{name} must be between 0 and 100, got {float_value}")
        return float_value
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {name}: {value}. Must be a number between 0 and 100.")


def validate_ani_threshold(value) -> float:
    """
    Validate ANI threshold (0-1)
    
    Args:
        value: ANI threshold value
        
    Returns:
        Validated ANI threshold
        
    Raises:
        ValueError: If ANI threshold is invalid
    """
    try:
        float_value = float(value)
        if float_value < 0 or float_value > 1:
            raise ValueError(f"dRep ANI threshold must be between 0 and 1, got {float_value}")
        return float_value
    except (ValueError, TypeError):
        raise ValueError(f"Invalid dRep ANI threshold: {value}. Must be a number between 0 and 1.")


def validate_parameter_ranges(
    completeness_threshold,
    contamination_threshold, 
    drep_ani_threshold
) -> Dict[str, float]:
    """
    Validate all workflow parameter ranges
    
    Args:
        completeness_threshold: CheckM2 completeness threshold
        contamination_threshold: CheckM2 contamination threshold
        drep_ani_threshold: dRep ANI threshold
        
    Returns:
        Dictionary of validated parameters
        
    Raises:
        ValueError: If any parameter is invalid
    """
    return {
        'completeness_threshold': validate_percentage_threshold(
            completeness_threshold, 'Completeness threshold'
        ),
        'contamination_threshold': validate_percentage_threshold(
            contamination_threshold, 'Contamination threshold'
        ),
        'drep_ani_threshold': validate_ani_threshold(drep_ani_threshold)
    }


def validate_output_directory(outdir: str) -> str:
    """
    Validate and prepare output directory
    
    Args:
        outdir: Output directory path
        
    Returns:
        Validated output directory (absolute path)
        
    Raises:
        ValueError: If directory cannot be created or accessed
    """
    if not outdir:
        raise ValueError("Output directory cannot be empty")
    
    # Convert to absolute path
    outdir = os.path.abspath(os.path.expanduser(outdir))
    
    if not os.path.exists(outdir):
        try:
            os.makedirs(outdir, exist_ok=True)
            print(f"Created output directory: {outdir}")
        except Exception as e:
            raise ValueError(f"Could not create output directory: {outdir}. Error: {e}")
    else:
        print(f"Warning: Using existing output directory: {outdir}")
    
    # Verify directory is writable
    if not os.access(outdir, os.W_OK):
        raise ValueError(f"Output directory is not writable: {outdir}")
    
    return outdir


def validate_database_location(db_location: str) -> str:
    """
    Validate database location (basic directory check)
    
    Args:
        db_location: Database location path
        
    Returns:
        Validated database location (absolute path)
        
    Raises:
        ValueError: If database location is invalid
    """
    if not db_location:
        raise ValueError("Database location cannot be empty")
    
    # Convert to absolute path
    db_location = os.path.abspath(os.path.expanduser(db_location))
    
    if not os.path.exists(db_location):
        raise ValueError(f"Database location does not exist: {db_location}")
    
    if not os.path.isdir(db_location):
        raise ValueError(f"Database location is not a directory: {db_location}")
    
    return db_location


def validate_directory_path(path: str, name: str) -> str:
    """
    Generic directory validation utility
    
    Args:
        path: Directory path to validate
        name: Name for error messages
        
    Returns:
        Validated directory path (absolute)
        
    Raises:
        ValueError: If directory is invalid
    """
    if not path:
        raise ValueError(f"{name} cannot be empty")
    
    # Convert to absolute path
    path = os.path.abspath(os.path.expanduser(path))
    
    if not os.path.exists(path):
        raise ValueError(f"{name} does not exist: {path}")
    
    if not os.path.isdir(path):
        raise ValueError(f"{name} is not a directory: {path}")
    
    return path