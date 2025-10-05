"""
Phorager Utilities Module

Contains shared utilities and helper functions used across commands.
Includes validation, logging, and common operations.
"""

from .install_validation import (
    validate_tools_list, validate_databases_list,
    get_available_tools_summary, ALL_TOOLS, DATABASE_TOOLS
)
from .bacterial_validation import (
    validate_genome_input, 
    validate_percentage_threshold,
    validate_ani_threshold,
    validate_threads, 
    validate_output_directory
)
from .prophage_validation import (
    validate_and_detect_genome_input, validate_tool_selection,
    validate_genomad_preset, validate_vibrant_min_length,
    validate_databases
)

from .annotation_validation import (
    validate_and_detect_prophage_input,
    validate_checkv_quality_levels,
    validate_annotation_parameters,
    validate_filter_mode,
    validate_min_prophage_length,
    validate_structural_thresholds,
    validate_clustering_parameters,
    validate_databases as validate_annotation_databases,
    VALID_CHECKV_QUALITY_LEVELS,
    VALID_FILTER_MODES
)

__all__ = [
    # Install validation
    'validate_tools_list',
    'validate_databases_list', 
    'get_available_tools_summary',
    'ALL_TOOLS',
    'DATABASE_TOOLS',
    # Bacterial validation
    'validate_genome_input',
    'validate_percentage_threshold',
    'validate_ani_threshold',
    'validate_threads',
    'validate_output_directory',
    # Prophage validation
    'validate_and_detect_genome_input',
    'validate_tool_selection',
    'validate_genomad_preset',
    'validate_vibrant_min_length',
    'validate_databases'
    # Annotation validation
    'validate_and_detect_prophage_input',
    'validate_checkv_quality_levels',
    'validate_annotation_parameters',
    'validate_filter_mode',
    'validate_min_prophage_length',
    'validate_structural_thresholds',
    'validate_clustering_parameters',
    'validate_annotation_databases',
    'VALID_CHECKV_QUALITY_LEVELS',
    'VALID_FILTER_MODES'
]