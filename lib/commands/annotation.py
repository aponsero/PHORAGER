"""
Phorager Annotation Command

Runs the annotation workflow for prophage quality assessment, functional annotation,
structural filtering, and sequence clustering.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils.annotation_validation import (
    validate_and_detect_prophage_input,
    validate_checkv_quality_levels,
    validate_annotation_parameters,
    validate_filter_mode,
    validate_min_prophage_length,
    validate_structural_thresholds,
    validate_clustering_parameters,
    validate_databases
)


class AnnotationCommand:
    """
    Handles annotation workflow execution for prophage sequences
    """
    
    def __init__(self):
        """Initialize annotation command"""
        self.config = {}
        self.nextflow_params = {}
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add arguments to the annotation subparser"""
        
        # Required input
        parser.add_argument(
            '--prophage',
            type=str,
            required=True,
            help='Input prophage sequences (FASTA file, prophage workflow results directory, '
                 'or 2.Prophage_detection/ subdirectory)'
        )
        
        # Quality filtering parameters
        quality_group = parser.add_argument_group('Quality Filtering')
        quality_group.add_argument(
            '--min-prophage-length',
            type=int,
            default=5000,
            help='Minimum prophage length in bp (500-50000, default: 5000)'
        )
        quality_group.add_argument(
            '--checkv-quality-levels',
            type=str,
            default='Complete,High-quality,Medium-quality',
            help='Comma-separated list of CheckV quality levels to retain '
                 '(default: Complete,High-quality,Medium-quality). '
                 'Valid: Complete, High-quality, Medium-quality, Low-quality, Not-determined'
        )
        
        # Annotation control
        annotation_group = parser.add_argument_group('Annotation Control')
        annotation_group.add_argument(
            '--skip-detailed-annotation',
            action='store_true',
            help='Skip detailed annotation (Pharokka + PHOLD) and proceed directly to clustering. '
                 'Use for rapid clustering without functional annotation.'
        )
        
        # Structural filtering parameters
        filtering_group = parser.add_argument_group('Structural Gene Filtering')
        filtering_group.add_argument(
            '--annotation-filter-mode',
            type=str,
            choices=['pharokka', 'phold', 'combined'],
            default='combined',
            help='Filtering mode based on structural gene content (default: combined). '
                 'combined = pass if Pharokka OR PHOLD criteria met'
        )
        filtering_group.add_argument(
            '--pharokka-structural-perc',
            type=float,
            default=10.0,
            help='Minimum percentage of structural genes from Pharokka (0-100, default: 10.0)'
        )
        filtering_group.add_argument(
            '--pharokka-structural-total',
            type=int,
            default=3,
            help='Minimum total structural genes from Pharokka (1-20, default: 3)'
        )
        filtering_group.add_argument(
            '--phold-structural-perc',
            type=float,
            default=10.0,
            help='Minimum percentage of structural genes from PHOLD (0-100, default: 10.0)'
        )
        filtering_group.add_argument(
            '--phold-structural-total',
            type=int,
            default=3,
            help='Minimum total structural genes from PHOLD (1-20, default: 3)'
        )
        
        # Clustering parameters
        clustering_group = parser.add_argument_group('Clustering Parameters')
        clustering_group.add_argument(
            '--clustering-min-ani',
            type=float,
            default=95.0,
            help='Minimum ANI for clustering (0-100, default: 95.0)'
        )
        clustering_group.add_argument(
            '--clustering-min-coverage',
            type=float,
            default=85.0,
            help='Minimum coverage for clustering (0-100, default: 85.0)'
        )
        
        # Standard workflow parameters
        standard_group = parser.add_argument_group('Standard Options')
        standard_group.add_argument(
            '--outdir',
            type=str,
            default='results/',
            help='Output directory (default: results/)'
        )
        standard_group.add_argument(
            '--threads',
            type=int,
            help='Number of threads to use (default: auto-detect)'
        )
        standard_group.add_argument(
            '--resume',
            action='store_true',
            help='Resume previous run'
        )
        standard_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Show command without executing'
        )
    
    def _load_config(self) -> Dict:
        """Load user configuration from ~/.phorager/config.json"""
        config_file = Path.home() / '.phorager' / 'config.json'
        
        if not config_file.exists():
            print("Warning: No configuration found. Using defaults.")
            print("Run 'phorager config set' to configure backend and locations.")
            return {
                'backend': 'conda',
                'db_location': str(Path.home() / 'phorager_databases'),
                'cache_location': str(Path.home() / '.phorager' / 'cache')
            }
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _validate_input(self, args) -> Tuple[bool, str, str]:
        """
        Validate and detect prophage input
        
        Returns:
            Tuple of (is_valid, input_mode, resolved_path)
        """
        is_valid, input_mode, resolved_path, error = validate_and_detect_prophage_input(args.prophage)
        
        if not is_valid:
            print(f"Error: {error}")
            return False, None, None
        
        return True, input_mode, resolved_path
    
    def _validate_parameters(self, args) -> bool:
        """Validate all annotation parameters"""
        
        # Validate min prophage length
        is_valid, error = validate_min_prophage_length(args.min_prophage_length)
        if not is_valid:
            print(f"Error: {error}")
            return False
        
        # Validate CheckV quality levels
        valid_levels, error = validate_checkv_quality_levels(args.checkv_quality_levels)
        if error:
            print(f"Error: {error}")
            return False
        
        # Validate annotation parameter conflicts
        is_valid, error = validate_annotation_parameters(args)
        if not is_valid:
            print(f"Error: {error}")
            return False
        
        # If not skipping annotation, validate structural filtering parameters
        if not args.skip_detailed_annotation:
            # Validate filter mode
            is_valid, error = validate_filter_mode(args.annotation_filter_mode)
            if not is_valid:
                print(f"Error: {error}")
                return False
            
            # Validate Pharokka thresholds
            is_valid, error = validate_structural_thresholds(
                args.pharokka_structural_perc,
                args.pharokka_structural_total,
                'Pharokka'
            )
            if not is_valid:
                print(f"Error: {error}")
                return False
            
            # Validate PHOLD thresholds
            is_valid, error = validate_structural_thresholds(
                args.phold_structural_perc,
                args.phold_structural_total,
                'PHOLD'
            )
            if not is_valid:
                print(f"Error: {error}")
                return False
        
        # Validate clustering parameters
        is_valid, error = validate_clustering_parameters(
            args.clustering_min_ani,
            args.clustering_min_coverage
        )
        if not is_valid:
            print(f"Error: {error}")
            return False
        
        # Validate threads if specified
        if args.threads is not None:
            if args.threads < 1:
                print("Error: --threads must be at least 1")
                return False
        
        return True
    
    def _validate_databases(self, args) -> bool:
        """Validate required databases exist"""
        
        # Determine required databases based on skip flag
        required_databases = ['checkv']  # Always needed
        
        if not args.skip_detailed_annotation:
            required_databases.extend(['pharokka', 'phold'])
        
        # Validate databases
        is_valid, missing_dbs, error = validate_databases(
            required_databases,
            self.config['db_location']
        )
        
        if not is_valid:
            print(f"Error: {error}")
            if missing_dbs:
                print("\nMissing databases:")
                for db in missing_dbs:
                    print(f"  - {db}")
                print(f"\nInstall missing databases with:")
                print(f"  phorager install --databases {','.join(missing_dbs)}")
            return False
        
        return True
    
    def _build_nextflow_command(self, args, resolved_input: str) -> List[str]:
        """Build the Nextflow command with all parameters"""
        
        cmd = ['nextflow', 'run', 'main.nf']
        
        # Add profile based on backend
        if self.config['backend'] == 'conda':
            cmd.extend(['-profile', 'conda'])
        # singularity uses default profile
        
        # Core workflow parameters
        cmd.extend([
            '--workflow', 'annotation',
            '--prophage', resolved_input,
            '--outdir', args.outdir,
            '--database_location', self.config['db_location']
        ])
        
        # Add cache location based on backend
        if self.config['backend'] == 'conda':
            cmd.extend(['--conda_cache_dir', self.config['cache_location']])
        else:
            cmd.extend(['--singularity_cache_dir', self.config['cache_location']])
        
        # Quality filtering parameters (always passed)
        cmd.extend([
            '--min_prophage_length', str(args.min_prophage_length),
            '--checkv_quality_levels', args.checkv_quality_levels
        ])
        
        # Skip detailed annotation flag (only if True)
        if args.skip_detailed_annotation:
            cmd.extend(['--skip_detailed_annotation', 'true'])
        else:
            # Structural filtering parameters (only if NOT skipping)
            cmd.extend([
                '--annotation_filter_mode', args.annotation_filter_mode,
                '--pharokka_structural_perc', str(args.pharokka_structural_perc),
                '--pharokka_structural_total', str(args.pharokka_structural_total),
                '--phold_structural_perc', str(args.phold_structural_perc),
                '--phold_structural_total', str(args.phold_structural_total)
            ])
        
        # Clustering parameters (always passed)
        cmd.extend([
            '--clustering_min_ani', str(args.clustering_min_ani),
            '--clustering_min_coverage', str(args.clustering_min_coverage)
        ])
        
        # Threads (only if user-specified)
        if args.threads is not None:
            cmd.extend(['--threads', str(args.threads)])
        
        # Resume flag
        if args.resume:
            cmd.append('-resume')
        
        return cmd
    
    def _display_dry_run(self, args, input_mode: str, resolved_input: str, cmd: List[str]):
        """Display dry-run information"""
        
        print("Annotation Workflow - Dry Run")
        print("=" * 50)
        print()
        
        # Input detection
        print("Input Detection:")
        if input_mode == 'prophage_workflow':
            print("  ✓ Prophage workflow results detected")
        elif input_mode == 'direct_subdir':
            print("  ✓ Direct subdirectory detected")
        else:  # single_file
            print("  ✓ Single FASTA file detected")
        print(f"  Input: {resolved_input}")
        print()
        
        # Configuration
        print("Configuration:")
        print(f"  Backend: {self.config['backend']}")
        print(f"  Database location: {self.config['db_location']}")
        print(f"  Cache location: {self.config['cache_location']}")
        print(f"  Output directory: {args.outdir}")
        if args.threads:
            print(f"  Threads: {args.threads}")
        else:
            print(f"  Threads: auto-detected")
        print()
        
        # Quality filtering
        print("Quality Filtering (CheckV):")
        print(f"  Min prophage length: {args.min_prophage_length} bp")
        print(f"  Quality levels: {args.checkv_quality_levels}")
        print()
        
        # Annotation pipeline
        print("Annotation Pipeline:")
        print("  ✓ CheckV - Quality assessment")
        if args.skip_detailed_annotation:
            print("  ✗ Pharokka - Skipped (--skip-detailed-annotation)")
            print("  ✗ PHOLD - Skipped (--skip-detailed-annotation)")
            print("  ✗ Structural filtering - Skipped (--skip-detailed-annotation)")
            print("  ✓ ANI clustering (CheckV-filtered sequences)")
        else:
            print("  ✓ Pharokka - Functional annotation")
            print("  ✓ PHOLD - Structure prediction")
            print("  ✓ Structural filtering (combined mode)")
            print("  ✓ ANI clustering")
        print()
        
        # Structural filtering details (if applicable)
        if not args.skip_detailed_annotation:
            print("Structural Filtering:")
            mode_desc = {
                'pharokka': 'Pharokka criteria only',
                'phold': 'PHOLD criteria only',
                'combined': 'pass if Pharokka OR PHOLD criteria met'
            }
            print(f"  Mode: {args.annotation_filter_mode} ({mode_desc[args.annotation_filter_mode]})")
            print(f"  Pharokka thresholds: ≥{args.pharokka_structural_perc}% structural genes AND ≥{args.pharokka_structural_total} total")
            print(f"  PHOLD thresholds: ≥{args.phold_structural_perc}% structural genes AND ≥{args.phold_structural_total} total")
            print()
        
        # Clustering
        print("Clustering Parameters:")
        print(f"  Min ANI: {args.clustering_min_ani}%")
        print(f"  Min coverage: {args.clustering_min_coverage}%")
        print()
        
        # Database status
        print("Databases Required:")
        checkv_db = Path(self.config['db_location']) / 'checkv_database'
        print(f"  {'✓' if checkv_db.exists() else '✗'} CheckV: {checkv_db}")
        
        if not args.skip_detailed_annotation:
            pharokka_db = Path(self.config['db_location']) / 'pharokka_database'
            phold_db = Path(self.config['db_location']) / 'phold_database'
            print(f"  {'✓' if pharokka_db.exists() else '✗'} Pharokka: {pharokka_db}")
            print(f"  {'✓' if phold_db.exists() else '✗'} PHOLD: {phold_db}")
        print()
        
        # Nextflow command
        print("Nextflow Command:")
        print(f"  {' '.join(cmd)}")
    
    def run(self, args) -> bool:
        """Execute the annotation command"""
        
        try:
            # Load configuration
            self.config = self._load_config()
            
            # Validate input and detect mode
            success, input_mode, resolved_input = self._validate_input(args)
            if not success:
                return False
            
            # Validate all parameters
            if not self._validate_parameters(args):
                return False
            
            # Validate databases
            if not self._validate_databases(args):
                return False
            
            # Create output directory if needed
            outdir = Path(args.outdir)
            if outdir.exists() and not args.dry_run:
                print(f"Warning: Output directory '{args.outdir}' already exists. Contents may be overwritten.")
            elif not args.dry_run:
                outdir.mkdir(parents=True, exist_ok=True)
            
            # Build Nextflow command
            cmd = self._build_nextflow_command(args, resolved_input)
            
            # Handle dry-run
            if args.dry_run:
                self._display_dry_run(args, input_mode, resolved_input, cmd)
                return True
            
            # Check Nextflow availability
            try:
                subprocess.run(['nextflow', '-version'], 
                             capture_output=True, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: Nextflow not found. Please install Nextflow first.")
                print("Visit: https://www.nextflow.io/docs/latest/getstarted.html")
                return False
            
            # Change to phorager directory before running nextflow
            phorager_dir = Path(sys.argv[0]).resolve().parent
            os.chdir(phorager_dir)

            # Execute Nextflow
            print("Starting annotation workflow...")
            print(f"Command: {' '.join(cmd)}")
            print()
            
            result = subprocess.run(cmd)
            
            if result.returncode == 0:
                print("\nAnnotation workflow completed successfully!")
                return True
            else:
                print("\nAnnotation workflow failed!")
                return False
        
        except KeyboardInterrupt:
            print("\nAnnotation workflow cancelled by user")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False