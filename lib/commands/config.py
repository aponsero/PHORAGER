"""
Phorager Configuration Command

Handles setting, showing, and resetting user configuration for phorager.
Manages persistent user preferences like backend selection and installation locations.
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigCommand:
    """
    Handles phorager configuration management
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'backend': 'singularity',
        'db_location': None,  # Will use nextflow.config defaults if None
        'cache_location': None  # Will use nextflow.config defaults if None
    }
    
    # Valid configuration values
    VALID_BACKENDS = ['conda', 'singularity']
    
    def __init__(self):
        """Initialize config command"""
        self.config_dir = Path.home() / '.phorager'
        self.config_file = self.config_dir / 'config.json'
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add arguments to the config subparser"""
        subparsers = parser.add_subparsers(
            dest='config_action',
            help='Configuration actions',
            metavar='ACTION'
        )
        
        # Set command
        set_parser = subparsers.add_parser(
            'set',
            help='Set configuration values',
            description='Set phorager configuration parameters'
        )
        set_parser.add_argument(
            '--backend',
            choices=['conda', 'singularity'],
            help='Installation backend (conda or singularity)'
        )
        set_parser.add_argument(
            '--db-location',
            type=str,
            help='Database installation directory'
        )
        set_parser.add_argument(
            '--cache-location',
            type=str,
            help='Cache directory for containers/packages'
        )
        
        # Show command
        show_parser = subparsers.add_parser(
            'show',
            help='Show current configuration',
            description='Display current phorager configuration'
        )
        show_parser.add_argument(
            '--json',
            action='store_true',
            help='Output configuration in JSON format'
        )
        
        # Reset command
        reset_parser = subparsers.add_parser(
            'reset',
            help='Reset configuration to defaults',
            description='Reset phorager configuration to default values'
        )
        reset_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, return defaults if file doesn't exist"""
        if not self.config_file.exists():
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to handle missing keys
            merged_config = self.DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
            
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not read config file ({e}). Using defaults.")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        self._ensure_config_dir()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            raise RuntimeError(f"Could not save configuration: {e}")
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration values"""
        # Validate backend
        if config.get('backend') not in self.VALID_BACKENDS:
            raise ValueError(f"Invalid backend. Must be one of: {', '.join(self.VALID_BACKENDS)}")
        
        # Validate paths if provided
        for path_key in ['db_location', 'cache_location']:
            path_value = config.get(path_key)
            if path_value is not None:
                path_obj = Path(path_value).expanduser().resolve()
                
                # Check if path exists or can be created
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValueError(f"Invalid {path_key.replace('_', ' ')}: {e}")
                
                # Update config with resolved path
                config[path_key] = str(path_obj)
    
    def set_config(self, args) -> None:
        """Set configuration values"""
        # Load current config
        config = self._load_config()
        
        # Update with provided values
        changes_made = False
        
        if args.backend is not None:
            if config['backend'] != args.backend:
                config['backend'] = args.backend
                changes_made = True
                print(f"Backend set to: {args.backend}")
        
        if args.db_location is not None:
            # Expand and resolve path
            db_path = Path(args.db_location).expanduser().resolve()
            if config['db_location'] != str(db_path):
                config['db_location'] = str(db_path)
                changes_made = True
                print(f"Database location set to: {db_path}")
        
        if args.cache_location is not None:
            # Expand and resolve path
            cache_path = Path(args.cache_location).expanduser().resolve()
            if config['cache_location'] != str(cache_path):
                config['cache_location'] = str(cache_path)
                changes_made = True
                print(f"Cache location set to: {cache_path}")
        
        if not changes_made:
            print("No configuration changes specified.")
            return
        
        # Validate configuration
        self._validate_config(config)
        
        # Save configuration
        self._save_config(config)
        print(f"Configuration saved to: {self.config_file}")
    
    def show_config(self, args) -> None:
        """Show current configuration"""
        config = self._load_config()
        
        if args.json:
            print(json.dumps(config, indent=2))
        else:
            print("Phorager Configuration:")
            print("=" * 24)
            
            for key, value in config.items():
                display_key = key.replace('_', ' ').title()
                if value is None:
                    display_value = "(using pipeline defaults)"
                else:
                    display_value = value
                print(f"{display_key:<20}: {display_value}")
            
            print(f"\nConfig file: {self.config_file}")
            if not self.config_file.exists():
                print("(Config file does not exist - showing defaults)")
    
    def reset_config(self, args) -> None:
        """Reset configuration to defaults"""
        if not args.confirm:
            response = input("Reset configuration to defaults? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Configuration reset cancelled.")
                return
        
        if self.config_file.exists():
            try:
                self.config_file.unlink()
                print("Configuration reset to defaults.")
                print(f"Config file removed: {self.config_file}")
            except OSError as e:
                raise RuntimeError(f"Could not remove config file: {e}")
        else:
            print("Configuration was already at defaults (no config file found).")
    
    def run(self, args) -> None:
        """Execute the config command"""
        if not args.config_action:
            print("Error: No config action specified. Use 'set', 'show', or 'reset'.")
            return
        
        if args.config_action == 'set':
            self.set_config(args)
        elif args.config_action == 'show':
            self.show_config(args)
        elif args.config_action == 'reset':
            self.reset_config(args)
        else:
            print(f"Unknown config action: {args.config_action}")