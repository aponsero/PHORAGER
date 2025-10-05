#!/usr/bin/env python3
"""
Test Script for Phorager Annotation Workflow Wrapper

Comprehensive testing of the annotation command functionality including
input detection, skip flag behavior, parameter validation, filter mode conflicts,
configuration integration, and dry-run functionality.
"""

import os
import sys
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class AnnotationTester:
    """Test suite for phorager annotation command"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
        self.original_dir = os.getcwd()
        
        # Find phorager executable
        self.phorager_path = self._find_phorager()
        
        print(f"Testing phorager at: {self.phorager_path}")
        print("=" * 60)
    
    def _find_phorager(self) -> str:
        """Find the phorager executable"""
        possible_paths = [
            './phorager',
            '../phorager',
            'phorager'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        raise FileNotFoundError("Could not find phorager executable")
    
    def _run_command(self, args: List[str]) -> Tuple[int, str, str]:
        """
        Run phorager command and return exit code, stdout, stderr
        """
        cmd = [self.phorager_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def _create_temp_dir(self, name: str) -> str:
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix=f"phorager_annotation_test_{name}_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def _create_test_prophage_file(self, path: str, name: str = "prophages.fasta") -> str:
        """Create a test prophage file"""
        prophage_path = os.path.join(path, name)
        with open(prophage_path, 'w') as f:
            f.write(">prophage_1\nATCGATCGATCGATCGATCGATCGATCGATCGATCG\n")
            f.write(">prophage_2\nGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA\n")
            f.write(">prophage_3\nTATATATATATATATATATATATATATATATATATA\n")
        return prophage_path
    
    def _create_prophage_workflow_structure(self, base_path: str) -> str:
        """Create a mock prophage workflow output structure"""
        # Create the expected path structure
        prophage_path = os.path.join(
            base_path,
            "2.Prophage_detection"
        )
        os.makedirs(prophage_path)
        
        # Add the All_prophage_sequences.fasta file
        self._create_test_prophage_file(prophage_path, "All_prophage_sequences.fasta")
        
        return base_path
    
    def _create_direct_subdirectory_structure(self, base_path: str) -> str:
        """Create a direct subdirectory with All_prophage_sequences.fasta"""
        prophage_dir = os.path.join(base_path, "2.Prophage_detection")
        os.makedirs(prophage_dir)
        
        self._create_test_prophage_file(prophage_dir, "All_prophage_sequences.fasta")
        
        return prophage_dir
    
    def _create_test_config(self, config_dir: str, backend: str = "conda") -> str:
        """Create a test configuration file"""
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")
        
        test_config = {
            "backend": backend,
            "db_location": "/tmp/test_databases",
            "cache_location": "/tmp/test_cache"
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        return config_file
    
    def _setup_databases_for_test(self, test_dir: str, skip_annotation: bool = False):
        """
        Set up databases and config for testing
        
        Returns:
            Tuple of (original_home, db_location)
        """
        # Create config
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        
        # Create databases (just empty directories)
        db_location = "/tmp/test_databases"
        os.makedirs(os.path.join(db_location, "checkv_database"), exist_ok=True)
        
        if not skip_annotation:
            os.makedirs(os.path.join(db_location, "pharokka_database"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "phold_database"), exist_ok=True)
        
        # Set HOME
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        return original_home, db_location
    
    def _record_test(self, test_name: str, passed: bool, message: str = ""):
        """Record test result"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append((test_name, passed, message))
        print(f"[{status}] {test_name}")
        if message and not passed:
            print(f"      {message}")
    
    def test_basic_help(self):
        """Test help command and argument availability"""
        print("\n1. Testing Basic Help and Arguments")
        print("-" * 40)
        
        # Test main help
        exit_code, stdout, stderr = self._run_command(['-h'])
        passed = exit_code == 0 and 'annotation' in stdout
        self._record_test("Main help shows annotation command", passed,
                         f"Exit code: {exit_code}, 'annotation' in output: {'annotation' in stdout}")
        
        # Test annotation help
        exit_code, stdout, stderr = self._run_command(['annotation', '-h'])
        passed = exit_code == 0
        self._record_test("Annotation help command works", passed, f"Exit code: {exit_code}")
        
        if passed:
            # Check required arguments
            required_args = ['--prophage']
            quality_args = ['--min-prophage-length', '--checkv-quality-levels']
            annotation_args = ['--skip-detailed-annotation']
            filtering_args = ['--annotation-filter-mode', '--pharokka-structural-perc', 
                            '--pharokka-structural-total', '--phold-structural-perc', 
                            '--phold-structural-total']
            clustering_args = ['--clustering-min-ani', '--clustering-min-coverage']
            optional_args = ['--outdir', '--threads', '--resume', '--dry-run']
            
            all_args = required_args + quality_args + annotation_args + filtering_args + clustering_args + optional_args
            missing_args = [arg for arg in all_args if arg not in stdout]
            
            self._record_test("All expected arguments present", len(missing_args) == 0,
                            f"Missing: {missing_args}")

    def test_input_validation_single_file(self):
        """Test single file input validation"""
        print("\n2. Testing Input Validation - Single File")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("input_file")
        
        # Test missing prophage argument
        exit_code, stdout, stderr = self._run_command(['annotation'])
        passed = exit_code != 0
        self._record_test("Missing prophage argument fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test non-existent file
        exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', '/nonexistent/path', '--dry-run'])
        passed = exit_code != 0 and 'does not exist' in stdout
        self._record_test("Non-existent prophage path fails", passed,
                         f"Exit code: {exit_code}, error detected: {'does not exist' in stdout}")
        
        # Test invalid file extension
        invalid_file = os.path.join(test_dir, "test.txt")
        with open(invalid_file, 'w') as f:
            f.write("test content")
        
        exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', invalid_file, '--dry-run'])
        passed = exit_code != 0 and 'Invalid file extension' in stdout
        self._record_test("Invalid file extension fails", passed,
                         f"Exit code: {exit_code}, error message present: {'Invalid file extension' in stdout}")
        
        # Test empty file
        empty_file = self._create_test_prophage_file(test_dir, "empty.fasta")
        open(empty_file, 'w').close()  # Make it empty
        exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', empty_file, '--dry-run'])
        passed = exit_code != 0 and 'empty' in stdout
        self._record_test("Empty file fails", passed,
                         f"Exit code: {exit_code}, error detected: {'empty' in stdout}")
        
        # Test valid single file - WITH DATABASE SETUP
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            valid_file = self._create_test_prophage_file(test_dir, "valid_prophages.fasta")
            exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', valid_file, '--dry-run'])
            passed = exit_code == 0 and 'Single FASTA file detected' in stdout
            self._record_test("Valid single prophage file succeeds", passed,
                             f"Exit code: {exit_code}, mode detected: {'Single FASTA file' in stdout}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
    
    def test_input_validation_prophage_workflow(self):
        """Test prophage workflow output detection"""
        print("\n3. Testing Input Validation - Prophage Workflow")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("prophage_workflow")
        
        # Test valid prophage workflow structure - WITH DATABASE SETUP
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            prophage_results = self._create_prophage_workflow_structure(test_dir)
            exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', prophage_results, '--dry-run'])
            passed = exit_code == 0 and 'Prophage workflow results detected' in stdout
            self._record_test("Prophage workflow structure detected", passed,
                            f"Exit code: {exit_code}, mode detected: {'Prophage workflow results' in stdout}")
            
            if passed:
                # Check that input path is shown (not necessarily the full file path)
                passed = f'Input: {prophage_results}' in stdout or 'Input:' in stdout
                self._record_test("Input path shown in output", passed,
                                f"Input path present: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test prophage structure with empty file
        empty_workflow = self._create_temp_dir("empty_workflow")
        prophage_path = os.path.join(empty_workflow, "2.Prophage_detection")
        os.makedirs(prophage_path)
        empty_file = os.path.join(prophage_path, "All_prophage_sequences.fasta")
        open(empty_file, 'w').close()  # Empty file
        
        exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', empty_workflow, '--dry-run'])
        passed = exit_code != 0 and 'empty' in stdout
        self._record_test("Prophage workflow with empty file fails", passed,
                        f"Exit code: {exit_code}, error detected: {'empty' in stdout}")


    def test_input_validation_direct_subdirectory(self):
        """Test direct subdirectory detection"""
        print("\n4. Testing Input Validation - Direct Subdirectory")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("direct_subdir")
        
        # Test valid direct subdirectory - WITH DATABASE SETUP
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            subdir = self._create_direct_subdirectory_structure(test_dir)
            exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', subdir, '--dry-run'])
            passed = exit_code == 0 and 'Direct subdirectory detected' in stdout
            self._record_test("Direct subdirectory detected", passed,
                             f"Exit code: {exit_code}, mode detected: {'Direct subdirectory' in stdout}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_input_validation_multiple_files_error(self):
        """Test error when directory contains multiple FASTA files"""
        print("\n5. Testing Input Validation - Multiple Files Error")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("multiple_files")
        
        # Create directory with multiple FASTA files
        self._create_test_prophage_file(test_dir, "prophage1.fasta")
        self._create_test_prophage_file(test_dir, "prophage2.fasta")
        self._create_test_prophage_file(test_dir, "prophage3.fa")
        
        exit_code, stdout, stderr = self._run_command(['annotation', '--prophage', test_dir, '--dry-run'])
        passed = exit_code != 0 and 'multiple FASTA files' in stdout
        self._record_test("Directory with multiple FASTA files fails", passed,
                         f"Exit code: {exit_code}, error detected: {'multiple FASTA files' in stdout}")
        
        if passed:
            # Check that error message is helpful
            helpful_msg = 'single merged' in stdout or 'merge sequences' in stdout
            self._record_test("Error message provides guidance", helpful_msg,
                             f"Helpful guidance present: {helpful_msg}")

    def test_checkv_quality_levels_validation(self):
        """Test CheckV quality levels parameter validation"""
        print("\n6. Testing CheckV Quality Levels Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("checkv_quality")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid quality levels
            valid_levels = [
                'Complete',
                'High-quality',
                'Medium-quality',
                'Complete,High-quality',
                'Complete,High-quality,Medium-quality',
                'Low-quality',
                'Not-determined'
            ]
            
            for levels in valid_levels:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--checkv-quality-levels', levels, '--dry-run'
                ])
                passed = exit_code == 0 and levels in stdout
                self._record_test(f"Valid quality levels '{levels}' accepted", passed,
                                 f"Exit code: {exit_code}, levels in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid quality level (no database setup needed for error case)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--checkv-quality-levels', 'Complete,Invalid,High-quality', '--dry-run'
        ])
        passed = exit_code != 0 and 'Invalid CheckV quality level' in stdout
        self._record_test("Invalid quality level rejected", passed,
                         f"Exit code: {exit_code}, error message: {'Invalid CheckV quality level' in stdout}")
        
        # Test empty quality levels
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--checkv-quality-levels', '', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Empty quality levels rejected", passed,
                         f"Exit code: {exit_code} (should be non-zero)")

    def test_min_prophage_length_validation(self):
        """Test minimum prophage length validation"""
        print("\n7. Testing Min Prophage Length Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("min_length")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid lengths
            valid_lengths = [500, 1000, 5000, 10000, 50000]
            for length in valid_lengths:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--min-prophage-length', str(length), '--dry-run'
                ])
                passed = exit_code == 0 and f'{length} bp' in stdout
                self._record_test(f"Valid min-length {length} accepted", passed,
                                 f"Exit code: {exit_code}, length in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test too small (no database setup needed for error case)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--min-prophage-length', '100', '--dry-run'
        ])
        passed = exit_code != 0 and ('at least 500' in stdout or 'must be' in stdout)
        self._record_test("Min-length too small fails", passed,
                         f"Exit code: {exit_code}, error message present: {passed}")
        
        # Test too large
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--min-prophage-length', '100000', '--dry-run'
        ])
        passed = exit_code != 0 and ('cannot exceed' in stdout or '50000' in stdout)
        self._record_test("Min-length too large fails", passed,
                         f"Exit code: {exit_code}, error message present: {passed}")

    def test_skip_annotation_flag(self):
        """Test skip detailed annotation flag behavior"""
        print("\n8. Testing Skip Detailed Annotation Flag")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("skip_annotation")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases - only CheckV needed when skipping
        original_home, db_location = self._setup_databases_for_test(test_dir, skip_annotation=True)
        
        try:
            # Test skip flag shows correct tools
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--skip-detailed-annotation', '--dry-run'
            ])
            passed = exit_code == 0 and 'Pharokka - Skipped' in stdout and 'PHOLD - Skipped' in stdout
            self._record_test("Skip flag disables annotation tools", passed,
                             f"Exit code: {exit_code}, tools skipped: {passed}")
            
            # Test that only CheckV database is required
            passed = 'CheckV:' in stdout and 'Pharokka:' not in stdout and 'PHOLD:' not in stdout
            self._record_test("Skip flag only requires CheckV database", passed,
                             f"Only CheckV shown: {passed}")
            
            # Test that clustering still runs
            passed = 'ANI clustering' in stdout
            self._record_test("Clustering still runs with skip flag", passed,
                             f"Clustering shown: {passed}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_skip_annotation_conflicts(self):
        """Test skip annotation conflicts with structural parameters"""
        print("\n9. Testing Skip Annotation Parameter Conflicts")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("skip_conflicts")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Test skip + annotation-filter-mode conflict (no database setup needed for error)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--skip-detailed-annotation', '--annotation-filter-mode', 'pharokka', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot specify' in stdout and 'filter-mode' in stdout
        self._record_test("Skip + filter mode conflict detected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test skip + pharokka structural parameters conflict
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--skip-detailed-annotation', '--pharokka-structural-perc', '20.0', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot specify' in stdout and 'structural' in stdout
        self._record_test("Skip + pharokka parameters conflict detected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test skip + phold structural parameters conflict
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--skip-detailed-annotation', '--phold-structural-total', '5', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot specify' in stdout and 'structural' in stdout
        self._record_test("Skip + phold parameters conflict detected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")

    def test_annotation_filter_mode_validation(self):
        """Test annotation filter mode validation"""
        print("\n10. Testing Annotation Filter Mode Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("filter_mode")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid filter modes
            valid_modes = ['pharokka', 'phold', 'combined']
            for mode in valid_modes:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--annotation-filter-mode', mode, '--dry-run'
                ])
                passed = exit_code == 0 and f'Mode: {mode}' in stdout
                self._record_test(f"Valid filter mode '{mode}' accepted", passed,
                                 f"Exit code: {exit_code}, mode in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid filter mode (no database setup needed for error)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--annotation-filter-mode', 'invalid', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Invalid filter mode rejected", passed,
                         f"Exit code: {exit_code} (should be non-zero)")

    def test_filter_mode_parameter_conflicts(self):
        """Test filter mode parameter conflicts"""
        print("\n11. Testing Filter Mode Parameter Conflicts")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("filter_conflicts")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Test pharokka mode + phold parameters conflict (no database setup needed for error)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--annotation-filter-mode', 'pharokka',
            '--phold-structural-perc', '20.0', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot specify PHOLD' in stdout
        self._record_test("Pharokka mode + PHOLD parameters conflict", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test phold mode + pharokka parameters conflict
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--annotation-filter-mode', 'phold',
            '--pharokka-structural-total', '5', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot specify Pharokka' in stdout
        self._record_test("PHOLD mode + Pharokka parameters conflict", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test combined mode allows both parameters - WITH DATABASE SETUP
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--annotation-filter-mode', 'combined',
                '--pharokka-structural-perc', '15.0',
                '--phold-structural-perc', '15.0', '--dry-run'
            ])
            passed = exit_code == 0
            self._record_test("Combined mode allows both tool parameters", passed,
                             f"Exit code: {exit_code}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_structural_threshold_validation(self):
        """Test structural gene threshold validation"""
        print("\n12. Testing Structural Threshold Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("thresholds")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid percentage thresholds
            valid_percs = [0.0, 5.0, 10.0, 50.0, 100.0]
            for perc in valid_percs:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--pharokka-structural-perc', str(perc), '--dry-run'
                ])
                passed = exit_code == 0 and f'{perc}%' in stdout
                self._record_test(f"Valid percentage {perc} accepted", passed,
                                 f"Exit code: {exit_code}, percentage in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid percentage (negative) - no database setup needed
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--pharokka-structural-perc', '-5.0', '--dry-run'
        ])
        passed = exit_code != 0 and ('between 0 and 100' in stdout or 'must be' in stdout)
        self._record_test("Negative percentage rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test invalid percentage (too large)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--phold-structural-perc', '150.0', '--dry-run'
        ])
        passed = exit_code != 0 and ('between 0 and 100' in stdout or '100' in stdout)
        self._record_test("Percentage over 100 rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Setup databases for valid total tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid total counts
            valid_totals = [1, 3, 5, 10, 20]
            for total in valid_totals:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--pharokka-structural-total', str(total), '--dry-run'
                ])
                passed = exit_code == 0 and f'≥{total} total' in stdout
                self._record_test(f"Valid total {total} accepted", passed,
                                 f"Exit code: {exit_code}, total in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid total (too small) - no database setup needed
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--pharokka-structural-total', '0', '--dry-run'
        ])
        passed = exit_code != 0 and ('at least 1' in stdout or 'must be' in stdout)
        self._record_test("Total 0 rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test invalid total (too large)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--phold-structural-total', '25', '--dry-run'
        ])
        passed = exit_code != 0 and ('cannot exceed 20' in stdout or '20' in stdout)
        self._record_test("Total over 20 rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")

    def test_clustering_parameter_validation(self):
        """Test clustering parameter validation"""
        print("\n13. Testing Clustering Parameter Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("clustering")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid ANI values
            valid_ani = [0.0, 50.0, 95.0, 100.0]
            for ani in valid_ani:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--clustering-min-ani', str(ani), '--dry-run'
                ])
                passed = exit_code == 0 and f'{ani}%' in stdout
                self._record_test(f"Valid ANI {ani} accepted", passed,
                                 f"Exit code: {exit_code}, ANI in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid ANI (negative) - no database setup needed
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--clustering-min-ani', '-10.0', '--dry-run'
        ])
        passed = exit_code != 0 and ('between 0 and 100' in stdout or 'must be' in stdout)
        self._record_test("Negative ANI rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Test invalid ANI (too large)
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--clustering-min-ani', '150.0', '--dry-run'
        ])
        passed = exit_code != 0 and ('between 0 and 100' in stdout or '100' in stdout)
        self._record_test("ANI over 100 rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")
        
        # Setup databases for valid coverage tests
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid coverage values
            valid_coverage = [0.0, 50.0, 85.0, 100.0]
            for coverage in valid_coverage:
                exit_code, stdout, stderr = self._run_command([
                    'annotation', '--prophage', valid_prophage,
                    '--clustering-min-coverage', str(coverage), '--dry-run'
                ])
                passed = exit_code == 0 and f'{coverage}%' in stdout
                self._record_test(f"Valid coverage {coverage} accepted", passed,
                                 f"Exit code: {exit_code}, coverage in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test invalid coverage - no database setup needed
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage,
            '--clustering-min-coverage', '150.0', '--dry-run'
        ])
        passed = exit_code != 0 and ('between 0 and 100' in stdout or '100' in stdout)
        self._record_test("Coverage over 100 rejected", passed,
                         f"Exit code: {exit_code}, error message: {passed}")

    def test_threads_validation(self):
        """Test thread parameter validation"""
        print("\n14. Testing Threads Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("threads")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases for valid test
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test valid thread count
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--threads', '8', '--dry-run'
            ])
            passed = exit_code == 0 and 'Threads: 8' in stdout
            self._record_test("Valid thread count accepted", passed,
                             f"Exit code: {exit_code}, threads in output: {passed}")
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)
        
        # Test zero threads - no database setup needed
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage, '--threads', '0', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Zero threads fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test negative threads
        exit_code, stdout, stderr = self._run_command([
            'annotation', '--prophage', valid_prophage, '--threads', '-1', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Negative threads fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")

    def test_database_validation(self):
        """Test database availability checking"""
        print("\n15. Testing Database Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("database_check")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Create test config with database location
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Test with missing databases (should fail by default)
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--dry-run'
            ])
            passed = exit_code != 0 and ('not found' in stdout or 'Missing' in stdout)
            self._record_test("Missing databases detected", passed,
                             f"Exit code: {exit_code}, error shown: {passed}")
            
            # Create mock databases
            db_location = "/tmp/test_databases"
            os.makedirs(os.path.join(db_location, "checkv_database"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "pharokka_database"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "phold_database"), exist_ok=True)
            
            # Test with all databases present
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--dry-run'
            ])
            # Check for checkmarks (using 'CheckV:' as proxy since encoding might vary)
            passed = exit_code == 0 and 'CheckV:' in stdout and 'Pharokka:' in stdout and 'PHOLD:' in stdout
            self._record_test("All databases found", passed,
                             f"Exit code: {exit_code}, all databases shown: {passed}")
            
            # Test skip annotation only checks CheckV database
            shutil.rmtree(os.path.join(db_location, "pharokka_database"))
            shutil.rmtree(os.path.join(db_location, "phold_database"))
            
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--skip-detailed-annotation', '--dry-run'
            ])
            passed = exit_code == 0  # Should pass since only CheckV needed
            self._record_test("Skip flag only checks CheckV database", passed,
                             f"Exit code: {exit_code} (should pass with only CheckV)")
            
            # Cleanup
            shutil.rmtree(db_location, ignore_errors=True)
            
        finally:
            os.environ['HOME'] = original_home

    def test_configuration_integration(self):
        """Test config system integration"""
        print("\n16. Testing Configuration Integration")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("config_integration")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Test with custom config file
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir, backend="conda")
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Create mock databases
            db_location = "/tmp/test_databases"
            os.makedirs(os.path.join(db_location, "checkv_database"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "pharokka_database"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "phold_database"), exist_ok=True)
            
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--dry-run'
            ])
            passed = 'Backend: conda' in stdout or '-profile conda' in stdout
            self._record_test("Custom configuration loads", passed,
                             f"Conda backend detected: {passed}")
            
            # Cleanup
            shutil.rmtree(db_location, ignore_errors=True)
        finally:
            os.environ['HOME'] = original_home

    def test_dry_run_functionality(self):
        """Test dry-run output format and content"""
        print("\n17. Testing Dry-run Functionality")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("dry_run")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test basic dry-run structure
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--dry-run'
            ])
            
            expected_sections = [
                'Annotation Workflow - Dry Run',
                'Input Detection:',
                'Configuration:',
                'Quality Filtering',
                'Annotation Pipeline:',
                'Structural Filtering:',
                'Clustering Parameters:',
                'Databases Required:',
                'Nextflow Command:'
            ]
            
            missing_sections = [section for section in expected_sections if section not in stdout]
            passed = exit_code == 0 and len(missing_sections) == 0
            self._record_test("Dry-run output structure correct", passed,
                             f"Exit code: {exit_code}, Missing sections: {missing_sections}")
            
            # Test with custom parameters
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--min-prophage-length', '10000',
                '--pharokka-structural-perc', '15.0',
                '--clustering-min-ani', '98.0',
                '--threads', '16',
                '--dry-run'
            ])
            
            expected_params = ['10000 bp', '15.0%', '98.0%', 'Threads: 16']
            missing_params = [param for param in expected_params if param not in stdout]
            passed = exit_code == 0 and len(missing_params) == 0
            self._record_test("Custom parameters in dry-run output", passed,
                             f"Exit code: {exit_code}, Missing params: {missing_params}")
            
            # Test Nextflow command structure
            passed = 'nextflow run main.nf' in stdout and '--workflow annotation' in stdout
            self._record_test("Nextflow command structure correct", passed,
                             f"Command structure found: {passed}")
            
            # Test skip annotation dry-run
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--skip-detailed-annotation', '--dry-run'
            ])
            
            passed = 'Pharokka - Skipped' in stdout and 'PHOLD - Skipped' in stdout
            self._record_test("Skip annotation shown in dry-run", passed,
                             f"Skip status shown: {passed}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_output_directory_handling(self):
        """Test output directory creation and validation"""
        print("\n18. Testing Output Directory Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("output_handling")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test output directory is NOT created in dry-run mode (correct behavior)
            new_outdir = os.path.join(test_dir, "new_annotation_results")
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--outdir', new_outdir, '--dry-run'
            ])
            
            # In dry-run, directory should NOT be created
            passed = exit_code == 0 and not os.path.exists(new_outdir)
            self._record_test("Output directory NOT created in dry-run", passed,
                             f"Exit code: {exit_code}, Directory not created: {not os.path.exists(new_outdir)}")
            
            # Test using existing directory
            existing_outdir = os.path.join(test_dir, "existing_results")
            os.makedirs(existing_outdir)
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage,
                '--outdir', existing_outdir, '--dry-run'
            ])
            
            passed = exit_code == 0
            self._record_test("Existing output directory accepted", passed,
                             f"Exit code: {exit_code}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_resume_functionality(self):
        """Test resume parameter handling"""
        print("\n19. Testing Resume Functionality")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("resume_test")
        valid_prophage = self._create_test_prophage_file(test_dir)
        
        # Setup databases
        original_home, db_location = self._setup_databases_for_test(test_dir)
        
        try:
            # Test resume parameter in dry-run
            exit_code, stdout, stderr = self._run_command([
                'annotation', '--prophage', valid_prophage, '--resume', '--dry-run'
            ])
            
            passed = exit_code == 0 and '-resume' in stdout
            self._record_test("Resume parameter in command", passed,
                             f"Exit code: {exit_code}, -resume in output: {'-resume' in stdout}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_error_handling(self):
        """Test error conditions and exit codes"""
        print("\n20. Testing Error Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("error_handling")
        
        # Test various error conditions
        error_cases = [
            (['annotation'], "Missing required prophage argument"),
            (['annotation', '--prophage', '/nonexistent'], "Non-existent prophage path"),
            (['annotation', '--prophage', test_dir], "Directory without valid input"),
        ]
        
        for args, description in error_cases:
            exit_code, stdout, stderr = self._run_command(args)
            passed = exit_code != 0
            self._record_test(f"Error case: {description}", passed,
                             f"Exit code: {exit_code} (should be non-zero)")

    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up {temp_dir}: {e}")
        
        os.chdir(self.original_dir)

    def run_all_tests(self):
        """Run all test suites"""
        print("Starting Phorager Annotation Command Test Suite")
        print("=" * 60)
        
        try:
            self.test_basic_help()
            self.test_input_validation_single_file()
            self.test_input_validation_prophage_workflow()
            self.test_input_validation_direct_subdirectory()
            self.test_input_validation_multiple_files_error()
            self.test_checkv_quality_levels_validation()
            self.test_min_prophage_length_validation()
            self.test_skip_annotation_flag()
            self.test_skip_annotation_conflicts()
            self.test_annotation_filter_mode_validation()
            self.test_filter_mode_parameter_conflicts()
            self.test_structural_threshold_validation()
            self.test_clustering_parameter_validation()
            self.test_threads_validation()
            self.test_database_validation()
            self.test_configuration_integration()
            self.test_dry_run_functionality()
            self.test_output_directory_handling()
            self.test_resume_functionality()
            self.test_error_handling()
            
        except Exception as e:
            print(f"Test suite failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        failed_tests = [result for result in self.test_results if not result[1]]
        return len(failed_tests) == 0

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([result for result in self.test_results if result[1]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for test_name, passed, message in self.test_results:
                if not passed:
                    print(f"  - {test_name}")
                    if message:
                        print(f"    {message}")
        
        print("=" * 60)


def main():
    """Main test runner"""
    tester = AnnotationTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())