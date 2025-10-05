"""
Phorager Bacterial Command

Handles bacterial genome quality control workflow for the phorager pipeline.
Performs CheckM2 quality assessment, filtering, and dRep dereplication.
"""

import argparse
import json
import sys
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Optional

from utils.bacterial_validation import (
    validate_genome_input, validate_parameter_ranges,
    validate_output_directory, validate_threads
)


class BacterialCommand:
    """
    Handles phorager bacterial genome quality control workflow
    """
    
    def __init__(self):
        """Initialize bacterial command"""
        # Config file location (same as other commands)
        self.config_dir = Path.home() / '.phorager'
        self.config_file = self.config_dir / 'config.json'
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add arguments to the bacterial subparser"""
        
        # Required arguments
        parser.add_argument(
            '--genome',
            type=str,
            required=True,
            help='Input genome file or directory containing .fa, .fasta, or .fna files'
        )
        
        # Optional workflow parameters
        parser.add_argument(
            '--completeness-threshold',
            type=float,
            help='CheckM2 completeness threshold (0-100, default: 95)'
        )
        parser.add_argument(
            '--contamination-threshold', 
            type=float,
            help='CheckM2 contamination threshold (0-100, default: 5)'
        )
        parser.add_argument(
            '--drep-ani-threshold',
            type=float,
            help='dRep ANI threshold (0-1, default: 0.999)'
        )
        parser.add_argument(
            '--outdir',
            type=str,
            help='Output directory (default: results/)'
        )
        parser.add_argument(
            '--threads',
            type=int,
            help='Number of threads to use'
        )
        
        # Behavior options
        parser.add_argument(
            '--resume',
            action='store_true',
            help='Resume previous run'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show command without executing'
        )
    
    def _load_config(self) -> dict:
        """Load user configuration, return defaults if not found"""
        default_config = {
            'backend': 'singularity',
            'db_location': './databases',     # Changed from None
            'cache_location': './cache'       # Changed from None
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

    def _load_nextflow_defaults(self) -> dict:
        """Load defaults from Nextflow configuration"""
        try:
            # Try to read nextflow.config from current directory
            config_path = Path.cwd() / 'nextflow.config'
            if not config_path.exists():
                # Fallback to basic defaults if nextflow.config not found
                return {
                    'outdir': 'results',
                    'database_location': 'databases',
                    'threads': multiprocessing.cpu_count(),
                    'completeness_threshold': 95,
                    'contamination_threshold': 5,
                    'drep_ani_threshold': 0.999
                }
            
            # Parse key parameters from nextflow.config
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Simple regex-based extraction of key parameters
            import re
            
            defaults = {}
            
            # Extract outdir
            outdir_match = re.search(r'outdir\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            defaults['outdir'] = outdir_match.group(1) if outdir_match else 'results'
            
            # Extract database_location
            db_match = re.search(r'database_location\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            defaults['database_location'] = db_match.group(1) if db_match else 'databases'
            
            # Extract threads (handle Runtime.runtime.availableProcessors())
            threads_match = re.search(r'threads\s*=\s*Runtime\.runtime\.availableProcessors\(\)', content)
            if threads_match:
                defaults['threads'] = multiprocessing.cpu_count()
            else:
                threads_num_match = re.search(r'threads\s*=\s*(\d+)', content)
                defaults['threads'] = int(threads_num_match.group(1)) if threads_num_match else multiprocessing.cpu_count()
            
            # Extract thresholds
            comp_match = re.search(r'completeness_threshold\s*=\s*(\d+\.?\d*)', content)
            defaults['completeness_threshold'] = float(comp_match.group(1)) if comp_match else 95
            
            cont_match = re.search(r'contamination_threshold\s*=\s*(\d+\.?\d*)', content)
            defaults['contamination_threshold'] = float(cont_match.group(1)) if cont_match else 5
            
            ani_match = re.search(r'drep_ani_threshold\s*=\s*(\d+\.?\d*)', content)
            defaults['drep_ani_threshold'] = float(ani_match.group(1)) if ani_match else 0.999
            
            return defaults
            
        except Exception as e:
            print(f"Warning: Could not parse nextflow.config ({e}). Using built-in defaults.")
            return {
                'outdir': 'results',
                'database_location': 'databases', 
                'threads': multiprocessing.cpu_count(),
                'completeness_threshold': 95,
                'contamination_threshold': 5,
                'drep_ani_threshold': 0.999
            }
    
    def _validate_parameters(self, args) -> dict:
        """
        Validate bacterial workflow parameters
        
        Returns:
            Dictionary of validated parameters
        """
        # Load configuration
        user_config = self._load_config()
        nextflow_defaults = self._load_nextflow_defaults()
        
        # Validate genome input
        validated_genome = validate_genome_input(args.genome)
        
        # Validate output directory (creates if needed)
        validated_outdir = validate_output_directory(
            args.outdir if args.outdir else nextflow_defaults['outdir']
        )
        
        # Validate threads ONLY if user provided a value
        if args.threads is not None:
            validated_threads = validate_threads(args.threads)
        else:
            # Use None to indicate we should use Nextflow's default (don't pass --threads)
            validated_threads = None
        
        # Validate parameter ranges
        validated_params = validate_parameter_ranges(
            completeness_threshold=args.completeness_threshold if args.completeness_threshold is not None else nextflow_defaults['completeness_threshold'],
            contamination_threshold=args.contamination_threshold if args.contamination_threshold is not None else nextflow_defaults['contamination_threshold'],
            drep_ani_threshold=args.drep_ani_threshold if args.drep_ani_threshold is not None else nextflow_defaults['drep_ani_threshold']
        )
        
        # Construct validated parameter set
        validated = {
            'genome': validated_genome,
            'outdir': validated_outdir,
            'threads': validated_threads,
            'completeness_threshold': validated_params['completeness_threshold'],
            'contamination_threshold': validated_params['contamination_threshold'], 
            'drep_ani_threshold': validated_params['drep_ani_threshold'],
            'database_location': user_config['db_location'] if user_config['db_location'] else nextflow_defaults['database_location'],
            'backend': user_config['backend'],
            'cache_location': user_config['cache_location']
        }
        
        return validated
    
    def _build_nextflow_command(self, params: dict, args) -> List[str]:
        """
        Build the nextflow command that would be executed
        
        Args:
            params: Validated parameters dictionary
            args: Parsed command arguments
            
        Returns:
            List of command components
        """
        cmd = ['nextflow', 'run', 'main.nf']
        
        # Add profile based on backend
        if params['backend'] == 'conda':
            cmd.extend(['-profile', 'conda'])
        # singularity is the default profile, no need to specify
        
        # Add workflow
        cmd.extend(['--workflow', 'bacterial'])
        
        # Add required parameters
        cmd.extend(['--genome', params['genome']])
        cmd.extend(['--outdir', params['outdir']])
        
        # Add workflow parameters
        if params['threads'] is not None:
            cmd.extend(['--threads', str(params['threads'])])
        cmd.extend(['--completeness_threshold', str(params['completeness_threshold'])])
        cmd.extend(['--contamination_threshold', str(params['contamination_threshold'])])
        cmd.extend(['--drep_ani_threshold', str(params['drep_ani_threshold'])])
        
        # Add database location (only if configured)
        if params.get('database_location'):
            cmd.extend(['--database_location', params['database_location']])

        # Add cache location if specified
        cache_location = params.get('cache_location')
        if cache_location:
            if params['backend'] == 'conda':
                cmd.extend(['--conda_cache_dir', cache_location])
            else:
                cmd.extend(['--singularity_cache_dir', cache_location])

        # Add behavior flags
        if args.resume:
            cmd.insert(2, '-resume')  # Resume goes right after 'run'
        
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
                print("Bacterial workflow completed successfully!")
                return True
            else:
                print(f"Bacterial workflow failed with exit code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            print("Error: Nextflow not found. Please ensure Nextflow is installed and in your PATH.")
            return False
        except Exception as e:
            print(f"Error executing Nextflow: {e}")
            return False
    
    def _show_workflow_plan(self, params: dict, cmd: List[str]):
        """Show what would be executed in dry-run mode"""
        print("Phorager Bacterial Workflow Plan")
        print("=" * 35)
        print()
        
        # Show configuration
        print("Configuration:")
        print(f"  Backend: {params['backend']}")
        print(f"  Database location: {params['database_location']}")
        if params['cache_location']:
            print(f"  Cache location: {params['cache_location']}")
        else:
            print("  Cache location: (pipeline default)")
        print()
        
        # Show input information
        genome_path = Path(params['genome'])
        if genome_path.is_file():
            print("Input:")
            print(f"  Genome file: {params['genome']}")
        else:
            # Count genome files in directory
            genome_files = []
            for ext in ['.fa', '.fasta', '.fna']:
                genome_files.extend(list(genome_path.glob(f'*{ext}')))
            print("Input:")
            print(f"  Genome directory: {params['genome']} ({len(genome_files)} files found)")
        print()
        
        # Show parameters
        print("Workflow Parameters:")
        print(f"  Completeness threshold: {params['completeness_threshold']}%")
        print(f"  Contamination threshold: {params['contamination_threshold']}%") 
        print(f"  dRep ANI threshold: {params['drep_ani_threshold']}")
        print(f"  Output directory: {params['outdir']}")
        if params['threads'] is not None:
            print(f"  Threads: {params['threads']}")
        else:
            print(f"  Threads: (using Nextflow default - auto-detected)")
        print()
        
        # Show nextflow command
        print("Nextflow command that would be executed:")
        print(f"  {' '.join(cmd)}")
        print()
        
        print("NOTE: This is a dry-run. Use without --dry-run to execute.")
    
    def run(self, args) -> bool:
        """Execute the bacterial command"""
        
        try:
            # Validate parameters
            validated_params = self._validate_parameters(args)
            
            # Build nextflow command
            nextflow_cmd = self._build_nextflow_command(validated_params, args)
            
            # Show dry-run if requested, otherwise execute
            if args.dry_run:
                self._show_workflow_plan(validated_params, nextflow_cmd)
                return True  # Success
            else:
                phorager_dir = Path(sys.argv[0]).resolve().parent
                os.chdir(phorager_dir)
                
                # Execute nextflow command
                print("Executing bacterial workflow...")
                success = self._execute_nextflow(nextflow_cmd)
                return success
        
        except ValueError as e:
            print(f"Error: {e}")
            return False  # Failure
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False  # Failure