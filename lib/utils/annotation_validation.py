"""
Annotation Validation Utilities

Validation functions for the annotation workflow command.
"""

from pathlib import Path
from typing import List, Tuple, Optional


# Valid CheckV quality levels
VALID_CHECKV_QUALITY_LEVELS = [
    'Complete',
    'High-quality',
    'Medium-quality',
    'Low-quality',
    'Not-determined'
]

# Valid filter modes
VALID_FILTER_MODES = ['pharokka', 'phold', 'combined']


def validate_and_detect_prophage_input(prophage_path: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Validate and detect prophage input type
    
    Args:
        prophage_path: Input path from user
    
    Returns:
        Tuple of (is_valid, input_mode, resolved_path, error_message)
        input_mode can be: 'single_file', 'prophage_workflow', 'direct_subdir'
    """
    input_path = Path(prophage_path)
    
    # Check if path exists
    if not input_path.exists():
        return False, None, None, f"Input path does not exist: {prophage_path}"
    
    # Mode 1: Single FASTA file
    if input_path.is_file():
        # Validate file extension
        valid_extensions = {'.fa', '.fasta', '.fna'}
        if input_path.suffix.lower() not in valid_extensions:
            return False, None, None, (
                f"Invalid file extension '{input_path.suffix}'. "
                f"Expected one of: {', '.join(valid_extensions)}"
            )
        
        # Check if file is not empty
        if input_path.stat().st_size == 0:
            return False, None, None, f"Input file is empty: {prophage_path}"
        
        return True, 'single_file', str(input_path), None
    
    # Mode 2 & 3: Directory input
    elif input_path.is_dir():
        # Check for prophage workflow output structure
        prophage_output = input_path / '2.Prophage_detection' / 'All_prophage_sequences.fasta'
        
        if prophage_output.exists():
            # Mode 2: Prophage workflow results
            if prophage_output.stat().st_size == 0:
                return False, None, None, f"Prophage sequences file is empty: {prophage_output}"
            return True, 'prophage_workflow', str(input_path), None
        
        # Check for direct subdirectory with All_prophage_sequences.fasta
        direct_fasta = input_path / 'All_prophage_sequences.fasta'
        if direct_fasta.exists():
            # Mode 3: Direct subdirectory
            if direct_fasta.stat().st_size == 0:
                return False, None, None, f"Prophage sequences file is empty: {direct_fasta}"
            return True, 'direct_subdir', str(input_path), None
        
        # Check if directory contains multiple FASTA files (ERROR case)
        fasta_files = list(input_path.glob('*.fa')) + \
                     list(input_path.glob('*.fasta')) + \
                     list(input_path.glob('*.fna'))
        
        if len(fasta_files) > 1:
            return False, None, None, (
                f"Directory contains multiple FASTA files ({len(fasta_files)} files found). "
                "Annotation workflow requires a single merged prophage file. "
                "Please use the prophage workflow output or merge sequences into a single file."
            )
        elif len(fasta_files) == 1:
            # Single FASTA file in directory - treat as single file mode
            if fasta_files[0].stat().st_size == 0:
                return False, None, None, f"Input file is empty: {fasta_files[0]}"
            return True, 'single_file', str(fasta_files[0]), None
        
        # No valid input found
        return False, None, None, (
            f"Directory does not contain valid prophage input. Expected:\n"
            f"  - Prophage workflow results (with 2.Prophage_detection/All_prophage_sequences.fasta)\n"
            f"  - Direct subdirectory (with All_prophage_sequences.fasta)\n"
            f"  - Single FASTA file"
        )
    
    return False, None, None, f"Invalid input type: {prophage_path}"


def validate_checkv_quality_levels(levels_str: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Validate CheckV quality levels
    
    Args:
        levels_str: Comma-separated string of quality levels
    
    Returns:
        Tuple of (valid_levels_list, error_message)
    """
    if not levels_str or not levels_str.strip():
        return None, "CheckV quality levels cannot be empty"
    
    # Parse comma-separated list
    levels = [level.strip() for level in levels_str.split(',') if level.strip()]
    
    if not levels:
        return None, "No valid quality levels found in input"
    
    # Validate each level
    invalid_levels = []
    for level in levels:
        if level not in VALID_CHECKV_QUALITY_LEVELS:
            invalid_levels.append(level)
    
    if invalid_levels:
        return None, (
            f"Invalid CheckV quality level(s): {', '.join(invalid_levels)}. "
            f"Valid levels are: {', '.join(VALID_CHECKV_QUALITY_LEVELS)}"
        )
    
    return levels, None


def validate_annotation_parameters(args) -> Tuple[bool, Optional[str]]:
    """
    Validate annotation parameters for conflicts
    
    Args:
        args: Parsed command-line arguments
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if skip flag conflicts with structural filtering parameters
    if args.skip_detailed_annotation:
        # Check for annotation filter mode
        if hasattr(args, 'annotation_filter_mode') and args.annotation_filter_mode != 'combined':
            # User explicitly changed filter mode
            return False, (
                "Cannot specify --annotation-filter-mode when using --skip-detailed-annotation. "
                "Structural filtering requires annotation. "
                "Remove --skip-detailed-annotation or remove filtering parameters."
            )
        
        # Check for any structural parameter changes from defaults
        structural_params_changed = []
        
        if args.pharokka_structural_perc != 10.0:
            structural_params_changed.append('--pharokka-structural-perc')
        if args.pharokka_structural_total != 3:
            structural_params_changed.append('--pharokka-structural-total')
        if args.phold_structural_perc != 10.0:
            structural_params_changed.append('--phold-structural-perc')
        if args.phold_structural_total != 3:
            structural_params_changed.append('--phold-structural-total')
        
        if structural_params_changed:
            return False, (
                f"Cannot specify structural filtering parameters when using --skip-detailed-annotation: "
                f"{', '.join(structural_params_changed)}. "
                f"Remove --skip-detailed-annotation or remove structural parameters."
            )
    
    # Check filter mode conflicts with tool parameters (only if NOT skipping)
    if not args.skip_detailed_annotation:
        if args.annotation_filter_mode == 'pharokka':
            # Check for PHOLD parameter changes
            if args.phold_structural_perc != 10.0 or args.phold_structural_total != 3:
                return False, (
                    "Cannot specify PHOLD structural parameters when filter mode is 'pharokka'. "
                    "Change filter mode to 'phold' or 'combined', or remove PHOLD parameters."
                )
        
        elif args.annotation_filter_mode == 'phold':
            # Check for Pharokka parameter changes
            if args.pharokka_structural_perc != 10.0 or args.pharokka_structural_total != 3:
                return False, (
                    "Cannot specify Pharokka structural parameters when filter mode is 'phold'. "
                    "Change filter mode to 'pharokka' or 'combined', or remove Pharokka parameters."
                )
    
    return True, None


def validate_filter_mode(mode: str) -> Tuple[bool, Optional[str]]:
    """
    Validate annotation filter mode
    
    Args:
        mode: Filter mode string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if mode not in VALID_FILTER_MODES:
        return False, (
            f"Invalid filter mode: '{mode}'. "
            f"Valid modes are: {', '.join(VALID_FILTER_MODES)}"
        )
    
    return True, None


def validate_min_prophage_length(length: int) -> Tuple[bool, Optional[str]]:
    """
    Validate minimum prophage length
    
    Args:
        length: Minimum length in bp
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if length < 500:
        return False, f"Minimum prophage length must be at least 500 bp (got: {length})"
    
    if length > 50000:
        return False, f"Minimum prophage length cannot exceed 50000 bp (got: {length})"
    
    return True, None


def validate_structural_thresholds(perc: float, total: int, tool_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate structural gene thresholds
    
    Args:
        perc: Percentage threshold (0-100)
        total: Total count threshold
        tool_name: Name of tool for error messages (e.g., 'Pharokka', 'PHOLD')
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate percentage
    if perc < 0 or perc > 100:
        return False, (
            f"{tool_name} structural percentage must be between 0 and 100 "
            f"(got: {perc})"
        )
    
    # Validate total count
    if total < 1:
        return False, (
            f"{tool_name} structural total must be at least 1 "
            f"(got: {total})"
        )
    
    if total > 20:
        return False, (
            f"{tool_name} structural total cannot exceed 20 "
            f"(got: {total})"
        )
    
    return True, None


def validate_clustering_parameters(ani: float, coverage: float) -> Tuple[bool, Optional[str]]:
    """
    Validate clustering parameters
    
    Args:
        ani: Minimum ANI threshold (0-100)
        coverage: Minimum coverage threshold (0-100)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate ANI
    if ani < 0 or ani > 100:
        return False, f"Clustering ANI must be between 0 and 100 (got: {ani})"
    
    # Validate coverage
    if coverage < 0 or coverage > 100:
        return False, f"Clustering coverage must be between 0 and 100 (got: {coverage})"
    
    return True, None


def validate_databases(required_databases: List[str], db_location: str) -> Tuple[bool, Optional[List[str]], Optional[str]]:
    """
    Validate that required databases exist
    
    Args:
        required_databases: List of required database names
        db_location: Base database directory path
    
    Returns:
        Tuple of (is_valid, missing_databases, error_message)
    """
    db_path = Path(db_location)
    
    if not db_path.exists():
        return False, required_databases, (
            f"Database location does not exist: {db_location}\n"
            f"Run 'phorager config set --db-location /path/to/databases' to set the location."
        )
    
    # Database directory naming convention
    db_dir_mapping = {
        'checkv': 'checkv_database',
        'pharokka': 'pharokka_database',
        'phold': 'phold_database'
    }
    
    missing_databases = []
    
    for db in required_databases:
        if db not in db_dir_mapping:
            return False, [db], f"Unknown database: {db}"
        
        db_dir = db_path / db_dir_mapping[db]
        if not db_dir.exists():
            missing_databases.append(db)
    
    if missing_databases:
        return False, missing_databases, (
            f"Required database(s) not found in {db_location}"
        )
    
    return True, [], None