"""
Phorager Install Command

Handles installation of tools and databases for the phorager pipeline.
Supports all bacterial genome, prophage detection, and annotation tools.
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

from utils.install_validation import (
    validate_tools_list, validate_databases_list, 
    get_available_tools_summary, calculate_total_database_size,
    TOOL_DESCRIPTIONS, DATABASE_SIZES
)


class InstallCommand:
    """
    Handles phorager tool and database installation
    """
    
    def __init__(self):
        """Initialize install command"""
        # Config file location (same as config command)
        self.config_dir = Path.home() / '.phorager'
        self.config_file = self.config_dir / 'config.json'
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add arguments to the install subparser"""
        
        # Tool and database selection
        parser.add_argument(
            '--tools',
            type=str,
            help='Comma-separated list of tools to install (e.g., checkm2,drep or genome or all)'
        )
        parser.add_argument(
            '--databases', 
            type=str,
            help='Comma-separated list of databases to install (e.g., checkm2 or all)'
        )
        
        # Behavior flags
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be installed without executing'
        )
        
        # Help option
        parser.add_argument(
            '--list-available',
            action='store_true',
            help='List all available tools and databases'
        )
    
    def _load_config(self) -> dict:
        """Load user configuration, return defaults if not found"""
        default_config = {
            'backend': 'singularity',
            'db_location': './databases',      # Changed from None
            'cache_location': './cache'        # Changed from None
        }
        
        if not self.config_file.exists():
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults - fills in any missing keys
            for key, value in default_config.items():
                config.setdefault(key, value)
            
            return config
                
        except (json.JSONDecodeError, OSError):
            print("Warning: Could not read config file. Using defaults.")
            return default_config

    def _parse_tool_list(self, tools_str: str) -> List[str]:
        """Parse comma-separated tool list"""
        if not tools_str:
            return []
        return [tool.strip() for tool in tools_str.split(',') if tool.strip()]
    
    def _validate_parameters(self, args) -> tuple[List[str], List[str]]:
        """
        Validate install parameters and return validated tools and databases
        
        Returns:
            Tuple of (validated_tools, validated_databases)
        """
        errors = []
        
        # Parse tool and database lists
        tools_list = self._parse_tool_list(args.tools) if args.tools else []
        databases_list = self._parse_tool_list(args.databases) if args.databases else []
        
        # Check if anything was specified
        if not tools_list and not databases_list:
            errors.append("No tools or databases specified for installation.")
            errors.append("Use --tools and/or --databases to specify what to install.")
            errors.append("Use --list-available to see available options.")
            raise ValueError("\n".join(errors))
        
        # Validate tools
        validated_tools = []
        if tools_list:
            valid_tools, invalid_tools = validate_tools_list(tools_list)
            if invalid_tools:
                errors.append(f"Invalid tools: {', '.join(invalid_tools)}")
            validated_tools = valid_tools
        
        # Validate databases
        validated_databases = []
        if databases_list:
            valid_databases, invalid_databases = validate_databases_list(databases_list)
            if invalid_databases:
                errors.append(f"Invalid databases: {', '.join(invalid_databases)}")
            validated_databases = valid_databases
        
        # If there were validation errors, show available options
        if errors:
            errors.append("\n" + get_available_tools_summary())
            raise ValueError("\n".join(errors))
        
        return validated_tools, validated_databases
    
    def _build_nextflow_command(self, config: dict, tools: List[str], 
                               databases: List[str], args) -> List[str]:
        """
        Build the nextflow command that would be executed
        
        Args:
            config: User configuration
            tools: Validated list of tools
            databases: Validated list of databases
            args: Parsed command arguments
            
        Returns:
            List of command components
        """
        cmd = ['nextflow', 'run', 'main.nf']
        
        # Add profile based on backend
        if config['backend'] == 'conda':
            cmd.extend(['-profile', 'conda'])
        # singularity is the default profile, no need to specify
        
        # Add workflow
        cmd.extend(['--workflow', 'install'])
        
        # Add tools and databases (sorted for consistency)
        if tools:
            cmd.extend(['--tools', ','.join(sorted(tools))])
        if databases:
            cmd.extend(['--databases', ','.join(sorted(databases))])
        
        # Add location parameters if configured
        if config.get('db_location'):
            cmd.extend(['--database_location', config['db_location']])

        cache_location = config.get('cache_location')
        if cache_location:
            if config['backend'] == 'conda':
                cmd.extend(['--conda_cache_dir', cache_location])
            else:
                cmd.extend(['--singularity_cache_dir', cache_location])
        
        return cmd
    
    def _execute_nextflow(self, cmd: List[str]) -> bool:
        """Execute the nextflow command"""
        try:
            print(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                text=True,
                cwd=Path.cwd()  # Run from current directory
            )
            
            if result.returncode == 0:
                print("\nInstallation completed successfully!")
                return True
            else:
                print(f"\nInstallation failed with exit code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            print("Error: Nextflow not found. Please ensure Nextflow is installed and in your PATH.")
            return False
        except Exception as e:
            print(f"Error executing Nextflow: {e}")
            return False
    
    def _show_installation_plan(self, config: dict, tools: List[str], 
                               databases: List[str], cmd: List[str]):
        """Show what would be installed with enhanced formatting"""
        print("\nPhorager Installation Plan")
        print("=" * 50)
        print()
        
        # Show configuration
        print("Configuration:")
        print(f"  Backend: {config['backend']}")
        print(f"  Database location: {config['db_location'] or '(pipeline default)'}")
        print(f"  Cache location: {config['cache_location'] or '(pipeline default)'}")
        print()
        
        # Show tools with descriptions
        if tools:
            print(f"Tools to install ({len(tools)}):")
            for tool in sorted(tools):
                desc = TOOL_DESCRIPTIONS.get(tool, 'No description')
                print(f"  - {tool:15} ({desc})")
            print()
        
        # Show databases with sizes and descriptions
        if databases:
            print(f"Databases to install ({len(databases)}):")
            for db in sorted(databases):
                size = DATABASE_SIZES.get(db, '?')
                desc = TOOL_DESCRIPTIONS.get(db, 'No description')
                print(f"  - {db:15} (~{size:>6}) - {desc}")
            print()
            
            # Show total download size
            total_size = calculate_total_database_size(databases)
            print(f"Total estimated download: ~{total_size}")
            print()
        
        # Show nextflow command
        print("Nextflow command that would be executed:")
        print(f"  {' '.join(cmd)}")
        print()
        
        print("NOTE: This is a dry-run. Use without --dry-run to execute.")
        print("      To automatically clean work directories after successful")
        print("      installation, add 'cleanup = true' to your nextflow.config")
    
    def show_available(self):
        """Show available tools and databases"""
        print(get_available_tools_summary())
    
    def run(self, args) -> bool:
        """Execute the install command"""
        
        # Handle list-available option
        if args.list_available:
            self.show_available()
            return True  # Success
        
        try:
            # Load configuration
            config = self._load_config()
            
            # Validate parameters
            validated_tools, validated_databases = self._validate_parameters(args)
            
            # Build nextflow command
            nextflow_cmd = self._build_nextflow_command(
                config, validated_tools, validated_databases, args
            )
            
            # Show dry-run if requested, otherwise execute
            if args.dry_run:
                self._show_installation_plan(
                    config, validated_tools, validated_databases, nextflow_cmd
                )
                return True  # Success
            else:
                phorager_dir = Path(sys.argv[0]).resolve().parent
                os.chdir(phorager_dir)
                
                # Execute nextflow command
                print("Executing installation...")
                success = self._execute_nextflow(nextflow_cmd)
                return success
        
        except ValueError as e:
            print(f"Error: {e}")
            return False  # Failure
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False  # Failure