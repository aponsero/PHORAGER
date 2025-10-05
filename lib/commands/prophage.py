"""
Phorager Prophage Command

Runs the prophage detection workflow using GenoMAD and VIBRANT.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from utils.prophage_validation import (
    validate_and_detect_genome_input, validate_tool_selection,
    validate_genomad_preset, validate_vibrant_min_length,
    validate_databases
)
from utils.bacterial_validation import validate_threads, validate_output_directory


class ProphageCommand:
    """
    Handles prophage detection workflow execution
    """
    
    def __init__(self):
        """Initialize prophage command"""
        self.config = None
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add arguments to the prophage subparser"""
        
        # Required arguments
        parser.add_argument(
            '--genome',
            required=True,
            type=str,
            help='Input genome file or directory (accepts bacterial workflow results)'
        )
        
        # Tool selection
        parser.add_argument(
            '--skip-genomad',
            action='store_true',
            help='Disable GenoMAD prophage detection'
        )
        parser.add_argument(
            '--skip-vibrant',
            action='store_true',
            help='Disable VIBRANT prophage detection'
        )
        
        # Tool-specific parameters
        parser.add_argument(
            '--genomad-preset',
            type=str,
            choices=['default', 'conservative', 'relaxed'],
            help='GenoMAD sensitivity preset (default: uses Nextflow default)'
        )
        parser.add_argument(
            '--vibrant-min-length',
            type=int,
            help='VIBRANT minimum scaffold length in bp (default: uses Nextflow default)'
        )
        
        # General workflow options
        parser.add_argument(
            '--outdir',
            type=str,
            default='results/',
            help='Output directory (default: results/)'
        )
        parser.add_argument(
            '--threads',
            type=int,
            help='Number of threads to use (default: auto-detect)'
        )
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume previous run (cannot be used with cleanup enabled)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show command without executing'
        )
    
    def _load_config(self) -> Dict:
        """Load user configuration"""
        config_file = Path.home() / '.phorager' / 'config.json'
        
        # Default configuration
        default_config = {
            'backend': 'singularity',
            'db_location': './databases',
            'cache_location': './cache'
        }
        
        if not config_file.exists():
            print("Warning: No configuration file found. Using defaults.")
            print("Run 'phorager config set' to configure backend and locations.")
            return default_config
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults - user config overrides, but defaults fill gaps
            for key, value in default_config.items():
                config.setdefault(key, value)
            
            return config
        except json.JSONDecodeError as e:
            print(f"Error: Invalid configuration file: {e}")
            sys.exit(1)
    
    def _validate_inputs(self, args) -> Tuple[bool, Optional[str], Optional[str], Optional[Path]]:
        """
        Validate all input arguments
        
        Returns:
            Tuple of (is_valid, input_mode, error_message, validated_genome_path)
        """
        # Validate genome input and detect type
        is_valid, input_mode, genome_path, error = validate_and_detect_genome_input(args.genome)
        if not is_valid:
            return (False, None, error, None)
        
        # Validate tool selection and parameter conflicts
        is_valid, error = validate_tool_selection(
            args.skip_genomad, args.skip_vibrant,
            args.genomad_preset, args.vibrant_min_length
        )
        if not is_valid:
            return (False, input_mode, error, None)
        
        # Validate GenoMAD preset if provided
        if args.genomad_preset is not None:
            is_valid, error = validate_genomad_preset(args.genomad_preset)
            if not is_valid:
                return (False, input_mode, error, None)
        
        # Validate VIBRANT min length if provided
        if args.vibrant_min_length is not None:
            is_valid, error = validate_vibrant_min_length(args.vibrant_min_length)
            if not is_valid:
                return (False, input_mode, error, None)
        
        # Validate threads if provided
        if args.threads is not None:
            try:
                validated_threads = validate_threads(args.threads)
            except ValueError as e:
                return (False, input_mode, str(e), None)
        
        # Validate output directory
        try:
            validated_outdir = validate_output_directory(args.outdir)
        except ValueError as e:
            return (False, input_mode, str(e), None)
        
        # Validate database availability
        is_valid, error = validate_databases(
            self.config['db_location'],
            args.skip_genomad,
            args.skip_vibrant
        )
        if not is_valid:
            return (False, input_mode, error, None)
        
        return (True, input_mode, None, genome_path)
    
    def _build_nextflow_command(self, args, input_mode: str) -> List[str]:
        """Build the nextflow command"""
        cmd = ['nextflow', 'run', 'main.nf']
        
        # Add profile based on backend
        if self.config['backend'] == 'conda':
            cmd.extend(['-profile', 'conda'])
        # singularity uses default profile
        
        # Add workflow specification
        cmd.extend(['--workflow', 'prophage'])
        
        # Add genome input
        cmd.extend(['--genome', args.genome])
        
        # Add output directory
        cmd.extend(['--outdir', args.outdir])
        
        # Add database location (only if configured)
        if self.config.get('db_location'):
            cmd.extend(['--database_location', self.config['db_location']])
        
        # Add cache location based on backend (only if configured)
        cache_location = self.config.get('cache_location')
        if cache_location:
            if self.config['backend'] == 'conda':
                cmd.extend(['--conda_cache_dir', cache_location])
            else:
                cmd.extend(['--singularity_cache_dir', cache_location])
        
        # Add tool selection (only if skipping)
        if args.skip_genomad:
            cmd.extend(['--run_genomad', 'false'])
        
        if args.skip_vibrant:
            cmd.extend(['--run_vibrant', 'false'])
        
        # Add tool-specific parameters (only if provided)
        if args.genomad_preset is not None:
            cmd.extend(['--genomad_preset', args.genomad_preset])
        
        if args.vibrant_min_length is not None:
            cmd.extend(['--vibrant_min_length', str(args.vibrant_min_length)])
        
        # Add threads if specified
        if args.threads is not None:
            cmd.extend(['--threads', str(args.threads)])
        
        # Add resume flag if specified
        if args.resume:
            cmd.append('-resume')
        
        return cmd
    
    def _print_dry_run(self, args, input_mode: str, cmd: List[str]):
        """Print dry-run information"""
        print("=== Prophage Detection Dry Run ===\n")
        
        # Input configuration
        print("Input Configuration:")
        print(f"  Mode: {input_mode}")
        print(f"  Path: {args.genome}")
        
        if input_mode == 'bacterial_workflow':
            genomes_path = Path(args.genome) / "1.Genome_preprocessing" / "Bact3_dRep" / "drep_output" / "dereplicated_genomes"
            print(f"  Genomes: {genomes_path}")
        print()
        
        # Tool configuration
        print("Tool Configuration:")
        
        genomad_status = "disabled" if args.skip_genomad else "enabled"
        print(f"  GenoMAD: {genomad_status}")
        if not args.skip_genomad:
            preset = args.genomad_preset if args.genomad_preset else "default (Nextflow default)"
            print(f"    Preset: {preset}")
        
        vibrant_status = "disabled" if args.skip_vibrant else "enabled"
        print(f"  VIBRANT: {vibrant_status}")
        if not args.skip_vibrant:
            min_len = f"{args.vibrant_min_length} bp" if args.vibrant_min_length else "1000 bp (Nextflow default)"
            print(f"    Min Length: {min_len}")
        print()
        
        # Database configuration
        print("Database Configuration:")
        print(f"  Location: {self.config['db_location']}")
        
        if not args.skip_genomad:
            genomad_db = Path(self.config['db_location']) / "genomad_database"
            status = "✓" if genomad_db.exists() else "✗"
            print(f"  GenoMAD DB: {genomad_db} {status}")
        
        if not args.skip_vibrant:
            vibrant_db = Path(self.config['db_location']) / "vibrant_database"
            status = "✓" if vibrant_db.exists() else "✗"
            print(f"  VIBRANT DB: {vibrant_db} {status}")
        print()
        
        # Output configuration
        print("Output Configuration:")
        print(f"  Directory: {args.outdir}")
        threads = f"{args.threads}" if args.threads else "auto-detect (Nextflow default)"
        print(f"  Threads: {threads}")
        print()
        
        # Nextflow command
        print("Nextflow Command:")
        print(f"  {' '.join(cmd)}")
        print()
        
        # Notes
        print("Notes:")
        resume_status = "enabled" if args.resume else "not enabled (add --resume to resume previous run)"
        print(f"  - Resume: {resume_status}")
        print(f"  - Cleanup: check nextflow.config (cleanup disables resume)")
    
    def run(self, args) -> bool:
        """Execute the prophage command"""
        
        try:
            # Load configuration
            self.config = self._load_config()
            
            # Validate all inputs
            is_valid, input_mode, error, genome_path = self._validate_inputs(args)
            if not is_valid:
                print(f"Error: {error}")
                return False
            
            # Build nextflow command
            cmd = self._build_nextflow_command(args, input_mode)
            
            # Handle dry-run
            if args.dry_run:
                self._print_dry_run(args, input_mode, cmd)
                return True
            
            # Check if nextflow is available
            try:
                subprocess.run(['nextflow', '-version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: Nextflow is not installed or not in PATH")
                print("Please install Nextflow: https://www.nextflow.io/docs/latest/getstarted.html")
                return False
            
            # Change to phorager directory before running nextflow
            phorager_dir = Path(sys.argv[0]).resolve().parent
            os.chdir(phorager_dir)

            # Execute command
            print(f"Running prophage detection workflow...")
            print(f"Command: {' '.join(cmd)}\n")
            
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                print("\nProphage detection workflow completed successfully!")
                return True
            else:
                print("\nProphage detection workflow failed!")
                return False
        
        except KeyboardInterrupt:
            print("\n\nWorkflow cancelled by user")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False