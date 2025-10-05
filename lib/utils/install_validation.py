"""
Phorager Validation Utilities

Provides tool registry constants and validation functions.
Supports bacterial genome, prophage detection, and annotation tools.
"""

from typing import List, Set, Dict


# Tool Groups - organized by workflow
TOOL_GROUPS: Dict[str, List[str]] = {
    'genome': ['checkm2', 'drep', 'parsing_env'],
    'prophage': ['genomad', 'vibrant', 'parsing_env'],
    'annotation': ['checkv', 'pharokka', 'phold', 'parsing_env']
}

# All available tools
ALL_TOOLS: List[str] = [
    'checkm2', 
    'drep', 
    'parsing_env',
    'genomad',
    'vibrant',
    'checkv',
    'pharokka',
    'phold'
]

# Tools that require database installation
DATABASE_TOOLS: List[str] = [
    'checkm2',
    'genomad',
    'vibrant',
    'checkv',
    'pharokka',
    'phold'
]

# Tool descriptions (from tools_registry.yaml)
TOOL_DESCRIPTIONS: Dict[str, str] = {
    'checkm2': 'Genome quality',
    'drep': 'Genome dereplication',
    'parsing_env': 'Python parsing environment for data processing',
    'genomad': 'Prophage and virus detection in genomes',
    'vibrant': 'Prophage detection in bacterial genomes',
    'checkv': 'Virus genome quality assessment',
    'pharokka': 'Phage genome annotation',
    'phold': 'Protein function prediction'
}

# Database sizes (from tool_parameters.config)
DATABASE_SIZES: Dict[str, str] = {
    'checkm2': '2.9GB',
    'genomad': '1.4GB',
    'vibrant': '11.0GB',
    'checkv': '6.4GB',
    'pharokka': '1.9GB',
    'phold': '15.0GB'
}

# Valid backend options
VALID_BACKENDS: List[str] = ['conda', 'singularity']


def is_valid_tool(tool_name: str) -> bool:
    """
    Check if a tool name is valid
    
    Args:
        tool_name: Name of the tool to validate
        
    Returns:
        True if tool is valid, False otherwise
    """
    return tool_name in ALL_TOOLS


def is_valid_database(database_name: str) -> bool:
    """
    Check if a database name is valid (corresponds to a tool that has a database)
    
    Args:
        database_name: Name of the database to validate
        
    Returns:
        True if database is valid, False otherwise
    """
    return database_name in DATABASE_TOOLS


def is_valid_tool_group(group_name: str) -> bool:
    """
    Check if a tool group name is valid
    
    Args:
        group_name: Name of the tool group to validate
        
    Returns:
        True if group is valid, False otherwise
    """
    return group_name in TOOL_GROUPS


def expand_tool_groups(tools: List[str]) -> List[str]:
    """
    Expand tool groups to individual tools and remove duplicates
    
    Args:
        tools: List of tool names and/or group names
        
    Returns:
        List of individual tool names with duplicates removed
        
    Example:
        expand_tool_groups(['genome']) 
        -> ['checkm2', 'drep', 'parsing_env']
        
        expand_tool_groups(['genome', 'prophage'])
        -> ['checkm2', 'drep', 'parsing_env', 'genomad', 'vibrant']
        (parsing_env appears only once)
    """
    expanded = []
    
    for item in tools:
        if item == 'all':
            # Special case: 'all' expands to all available tools
            expanded.extend(ALL_TOOLS)
        elif is_valid_tool_group(item):
            # Expand group to individual tools
            expanded.extend(TOOL_GROUPS[item])
        elif is_valid_tool(item):
            # Individual tool
            expanded.append(item)
        else:
            # Invalid tool/group - let calling code handle this
            expanded.append(item)
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for tool in expanded:
        if tool not in seen:
            seen.add(tool)
            result.append(tool)
    
    return result


def expand_database_list(databases: List[str]) -> List[str]:
    """
    Expand database list, handling 'all' special case
    
    Args:
        databases: List of database names
        
    Returns:
        List of database names with 'all' expanded
        
    Example:
        expand_database_list(['all']) -> ['checkm2', 'genomad', ...]
        expand_database_list(['checkm2']) -> ['checkm2']
    """
    if 'all' in databases:
        return DATABASE_TOOLS.copy()
    
    return databases


def calculate_total_database_size(databases: List[str]) -> str:
    """
    Calculate total download size for selected databases
    
    Args:
        databases: List of database names
        
    Returns:
        Formatted string with total size (e.g., "18.8GB")
    """
    total_gb = 0.0
    
    for db in databases:
        if db in DATABASE_SIZES:
            size_str = DATABASE_SIZES[db]
            # Extract numeric value (e.g., "2.9GB" -> 2.9)
            size_value = float(size_str.replace('GB', ''))
            total_gb += size_value
    
    return f"{total_gb:.1f}GB"


def validate_tools_list(tools: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of tools/groups and return valid and invalid items
    
    Args:
        tools: List of tool names, group names, or 'all'
        
    Returns:
        Tuple of (valid_tools, invalid_items)
        valid_tools: List of valid individual tool names (deduplicated)
        invalid_items: List of invalid tool/group names
    """
    expanded_tools = expand_tool_groups(tools)
    
    valid_tools = []
    invalid_items = []
    
    for tool in expanded_tools:
        if is_valid_tool(tool):
            valid_tools.append(tool)
        else:
            invalid_items.append(tool)
    
    return valid_tools, invalid_items


def validate_databases_list(databases: List[str]) -> tuple[List[str], List[str]]:
    """
    Validate a list of databases and return valid and invalid items
    
    Args:
        databases: List of database names or 'all'
        
    Returns:
        Tuple of (valid_databases, invalid_items)
    """
    expanded_databases = expand_database_list(databases)
    
    valid_databases = []
    invalid_items = []
    
    for db in expanded_databases:
        if is_valid_database(db):
            valid_databases.append(db)
        else:
            invalid_items.append(db)
    
    return valid_databases, invalid_items


def get_available_tools_summary() -> str:
    """
    Get a formatted summary of available tools and groups for help messages
    
    Returns:
        Formatted string describing available tools, groups, and databases
    """
    lines = []
    
    lines.append("\nAvailable tools:")
    lines.append("=" * 50)
    for tool in sorted(ALL_TOOLS):
        desc = TOOL_DESCRIPTIONS.get(tool, '')
        db_marker = ' (requires database)' if tool in DATABASE_TOOLS else ''
        lines.append(f"  {tool:15} - {desc}{db_marker}")
    
    lines.append("\nTool groups:")
    lines.append("=" * 50)
    for group in sorted(TOOL_GROUPS.keys()):
        tools = TOOL_GROUPS[group]
        lines.append(f"  {group:15} - {', '.join(tools)}")
    
    lines.append("\nAvailable databases:")
    lines.append("=" * 50)
    for db in sorted(DATABASE_TOOLS):
        size = DATABASE_SIZES.get(db, '?')
        desc = TOOL_DESCRIPTIONS.get(db, '')
        lines.append(f"  {db:15} - {desc} (~{size})")
    
    lines.append("\nSpecial values:")
    lines.append("=" * 50)
    lines.append("  all             - All available tools/databases")
    
    return "\n".join(lines)