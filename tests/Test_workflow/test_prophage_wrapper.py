#!/usr/bin/env python3
"""
Test Script for Phorager Prophage Workflow Wrapper

Comprehensive testing of the prophage command functionality including
input detection, tool selection, parameter validation, configuration integration,
and dry-run functionality.
"""

import os
import sys
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple


class ProphageTester:
    """Test suite for phorager prophage command"""
    
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
        temp_dir = tempfile.mkdtemp(prefix=f"phorager_prophage_test_{name}_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def _create_test_genome_file(self, path: str, name: str = "test_genome.fasta") -> str:
        """Create a test genome file"""
        genome_path = os.path.join(path, name)
        with open(genome_path, 'w') as f:
            f.write(">test_contig_1\nATCGATCGATCGATCGATCGATCG\n")
            f.write(">test_contig_2\nGCTAGCTAGCTAGCTAGCTAGCTA\n")
        return genome_path
    
    def _create_test_genome_dir(self, path: str) -> str:
        """Create a directory with multiple test genome files"""
        genome_dir = os.path.join(path, "genomes")
        os.makedirs(genome_dir)
        
        # Create different file extensions
        self._create_test_genome_file(genome_dir, "genome1.fa")
        self._create_test_genome_file(genome_dir, "genome2.fasta")
        self._create_test_genome_file(genome_dir, "genome3.fna")
        
        return genome_dir
    
    def _create_bacterial_workflow_structure(self, base_path: str) -> str:
        """Create a mock bacterial workflow output structure"""
        # Create the expected path structure
        derep_path = os.path.join(
            base_path,
            "1.Genome_preprocessing",
            "Bact3_dRep",
            "drep_output",
            "dereplicated_genomes"
        )
        os.makedirs(derep_path)
        
        # Add some genome files
        self._create_test_genome_file(derep_path, "derep_genome1.fa")
        self._create_test_genome_file(derep_path, "derep_genome2.fasta")
        
        return base_path
    
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
        passed = exit_code == 0 and 'prophage' in stdout
        self._record_test("Main help shows prophage command", passed,
                         f"Exit code: {exit_code}, 'prophage' in output: {'prophage' in stdout}")
        
        # Test prophage help
        exit_code, stdout, stderr = self._run_command(['prophage', '-h'])
        passed = exit_code == 0
        self._record_test("Prophage help command works", passed, f"Exit code: {exit_code}")
        
        if passed:
            # Check required arguments
            required_args = ['--genome']
            tool_args = ['--skip-genomad', '--skip-vibrant']
            param_args = ['--genomad-preset', '--vibrant-min-length']
            optional_args = ['--outdir', '--threads', '--resume', '--dry-run']
            
            all_args = required_args + tool_args + param_args + optional_args
            missing_args = [arg for arg in all_args if arg not in stdout]
            
            self._record_test("All expected arguments present", len(missing_args) == 0,
                            f"Missing: {missing_args}")

    def test_input_validation_file(self):
        """Test single file input validation"""
        print("\n2. Testing Input Validation - Single File")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("input_file")
        
        # Test missing genome argument
        exit_code, stdout, stderr = self._run_command(['prophage'])
        passed = exit_code != 0
        self._record_test("Missing genome argument fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test non-existent file
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', '/nonexistent/path', '--dry-run'])
        passed = exit_code != 0 and 'does not exist' in stdout
        self._record_test("Non-existent genome path fails", passed,
                         f"Exit code: {exit_code}, error detected: {'does not exist' in stdout}")
        
        # Test invalid file extension
        invalid_file = os.path.join(test_dir, "test.txt")
        with open(invalid_file, 'w') as f:
            f.write("test content")
        
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', invalid_file, '--dry-run'])
        passed = exit_code != 0 and 'Invalid file extension' in stdout
        self._record_test("Invalid file extension fails", passed,
                         f"Exit code: {exit_code}, error message present: {'Invalid file extension' in stdout}")
        
        # Test valid single file
        valid_file = self._create_test_genome_file(test_dir, "valid_genome.fasta")
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', valid_file, '--dry-run'])
        passed = exit_code == 0 and 'Mode: file' in stdout
        self._record_test("Valid single genome file succeeds", passed,
                         f"Exit code: {exit_code}, mode detected: {'Mode: file' in stdout}")

    def test_input_validation_directory(self):
        """Test directory input validation"""
        print("\n3. Testing Input Validation - Directory")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("input_directory")
        
        # Test empty directory
        empty_dir = os.path.join(test_dir, "empty")
        os.makedirs(empty_dir)
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', empty_dir, '--dry-run'])
        passed = exit_code != 0 and 'no .fa, .fasta, or .fna files' in stdout
        self._record_test("Empty genome directory fails", passed,
                         f"Exit code: {exit_code}, error message present: {'no .fa' in stdout}")
        
        # Test valid directory with genome files
        valid_dir = self._create_test_genome_dir(test_dir)
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', valid_dir, '--dry-run'])
        passed = exit_code == 0 and 'Mode: directory' in stdout
        self._record_test("Valid genome directory succeeds", passed,
                         f"Exit code: {exit_code}, mode detected: {'Mode: directory' in stdout}")

    def test_input_validation_bacterial_workflow(self):
        """Test bacterial workflow output detection"""
        print("\n4. Testing Input Validation - Bacterial Workflow")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("bacterial_workflow")
        
        # Test valid bacterial workflow structure
        bacterial_results = self._create_bacterial_workflow_structure(test_dir)
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', bacterial_results, '--dry-run'])
        passed = exit_code == 0 and 'Mode: bacterial_workflow' in stdout
        self._record_test("Bacterial workflow structure detected", passed,
                         f"Exit code: {exit_code}, mode detected: {'Mode: bacterial_workflow' in stdout}")
        
        if passed:
            # Check that the dereplicated genomes path is shown
            derep_path = "dereplicated_genomes"
            passed = derep_path in stdout
            self._record_test("Dereplicated genomes path shown", passed,
                             f"Path shown: {derep_path in stdout}")
        
        # Test bacterial structure without genome files
        empty_bacterial = self._create_temp_dir("empty_bacterial")
        derep_path = os.path.join(
            empty_bacterial,
            "1.Genome_preprocessing",
            "Bact3_dRep",
            "drep_output",
            "dereplicated_genomes"
        )
        os.makedirs(derep_path)
        
        exit_code, stdout, stderr = self._run_command(['prophage', '--genome', empty_bacterial, '--dry-run'])
        passed = exit_code != 0 and 'no genome files' in stdout
        self._record_test("Bacterial structure without genomes fails", passed,
                         f"Exit code: {exit_code}, error detected: {'no genome files' in stdout}")

    def test_tool_selection_validation(self):
        """Test tool selection and skip flag validation"""
        print("\n5. Testing Tool Selection Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("tool_selection")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test both tools skipped
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, 
            '--skip-genomad', '--skip-vibrant', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot skip all tools' in stdout
        self._record_test("Both tools skipped fails", passed,
                         f"Exit code: {exit_code}, error message: {'Cannot skip all tools' in stdout}")
        
        # Test skip GenoMAD only
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--skip-genomad', '--dry-run'
        ])
        passed = exit_code == 0 and 'GenoMAD: disabled' in stdout and 'VIBRANT: enabled' in stdout
        self._record_test("Skip GenoMAD only succeeds", passed,
                         f"Exit code: {exit_code}, correct tool status: {passed}")
        
        # Test skip VIBRANT only
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--skip-vibrant', '--dry-run'
        ])
        passed = exit_code == 0 and 'GenoMAD: enabled' in stdout and 'VIBRANT: disabled' in stdout
        self._record_test("Skip VIBRANT only succeeds", passed,
                         f"Exit code: {exit_code}, correct tool status: {passed}")
        
        # Test default (both tools enabled)
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--dry-run'
        ])
        passed = exit_code == 0 and 'GenoMAD: enabled' in stdout and 'VIBRANT: enabled' in stdout
        self._record_test("Default enables both tools", passed,
                         f"Exit code: {exit_code}, both tools enabled: {passed}")

    def test_parameter_conflict_validation(self):
        """Test parameter conflict detection"""
        print("\n6. Testing Parameter Conflict Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("param_conflicts")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test GenoMAD preset with skip-genomad
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome,
            '--skip-genomad', '--genomad-preset', 'conservative', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot set --genomad-preset when --skip-genomad' in stdout
        self._record_test("GenoMAD preset with skip-genomad fails", passed,
                         f"Exit code: {exit_code}, error detected: {passed}")
        
        # Test VIBRANT min-length with skip-vibrant
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome,
            '--skip-vibrant', '--vibrant-min-length', '2000', '--dry-run'
        ])
        passed = exit_code != 0 and 'Cannot set --vibrant-min-length when --skip-vibrant' in stdout
        self._record_test("VIBRANT min-length with skip-vibrant fails", passed,
                         f"Exit code: {exit_code}, error detected: {passed}")

    def test_genomad_preset_validation(self):
        """Test GenoMAD preset parameter validation"""
        print("\n7. Testing GenoMAD Preset Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("genomad_preset")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test valid presets
        valid_presets = ['default', 'conservative', 'relaxed']
        for preset in valid_presets:
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome,
                '--genomad-preset', preset, '--dry-run'
            ])
            passed = exit_code == 0 and f'Preset: {preset}' in stdout
            self._record_test(f"Valid preset '{preset}' accepted", passed,
                             f"Exit code: {exit_code}, preset in output: {passed}")
        
        # Test invalid preset
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome,
            '--genomad-preset', 'invalid', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Invalid GenoMAD preset rejected", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test default shows Nextflow default message
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--dry-run'
        ])
        passed = exit_code == 0 and '(Nextflow default)' in stdout
        self._record_test("Default preset shows Nextflow default", passed,
                         f"Exit code: {exit_code}, default message shown: {passed}")

    def test_vibrant_min_length_validation(self):
        """Test VIBRANT min-length parameter validation"""
        print("\n8. Testing VIBRANT Min-Length Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("vibrant_min_length")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test valid min-length values
        valid_lengths = [500, 1000, 2000, 5000, 50000]
        for length in valid_lengths:
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome,
                '--vibrant-min-length', str(length), '--dry-run'
            ])
            passed = exit_code == 0 and f'{length} bp' in stdout
            self._record_test(f"Valid min-length {length} accepted", passed,
                             f"Exit code: {exit_code}, length in output: {passed}")
        
        # Test too small
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome,
            '--vibrant-min-length', '100', '--dry-run'
        ])
        passed = exit_code != 0 and 'too small' in stdout
        self._record_test("Min-length too small fails", passed,
                         f"Exit code: {exit_code}, error message: {'too small' in stdout}")
        
        # Test too large
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome,
            '--vibrant-min-length', '100000', '--dry-run'
        ])
        passed = exit_code != 0 and 'too large' in stdout
        self._record_test("Min-length too large fails", passed,
                         f"Exit code: {exit_code}, error message: {'too large' in stdout}")

    def test_threads_validation(self):
        """Test thread parameter validation"""
        print("\n9. Testing Threads Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("threads")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test valid thread count
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--threads', '8', '--dry-run'
        ])
        passed = exit_code == 0 and 'Threads: 8' in stdout
        self._record_test("Valid thread count accepted", passed,
                         f"Exit code: {exit_code}, threads in output: {passed}")
        
        # Test zero threads
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--threads', '0', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Zero threads fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test negative threads
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--threads', '-1', '--dry-run'
        ])
        passed = exit_code != 0
        self._record_test("Negative threads fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")

    def test_database_validation(self):
        """Test database availability checking"""
        print("\n10. Testing Database Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("database_check")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Create test config with database location
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Test with missing databases (should fail by default)
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--dry-run'
            ])
            passed = exit_code != 0 and 'Missing required databases' in stdout
            self._record_test("Missing databases detected", passed,
                             f"Exit code: {exit_code}, error shown: {'Missing required databases' in stdout}")
            
            # Create mock databases
            db_location = "/tmp/test_databases"
            os.makedirs(os.path.join(db_location, "genomad_db"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "VIBRANT_db"), exist_ok=True)
            
            # Test with databases present
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--dry-run'
            ])
            passed = exit_code == 0 and '✓' in stdout
            self._record_test("Databases found", passed,
                             f"Exit code: {exit_code}, checkmarks shown: {'✓' in stdout}")
            
            # Test skip tool doesn't check its database
            shutil.rmtree(os.path.join(db_location, "genomad_db"))
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--skip-genomad', '--dry-run'
            ])
            passed = exit_code == 0  # Should pass since GenoMAD is skipped
            self._record_test("Skipped tool database not checked", passed,
                             f"Exit code: {exit_code} (should pass when tool skipped)")
            
            # Cleanup
            shutil.rmtree(db_location, ignore_errors=True)
            
        finally:
            os.environ['HOME'] = original_home

    def test_configuration_integration(self):
        """Test config system integration"""
        print("\n11. Testing Configuration Integration")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("config_integration")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test with default configuration (singularity)
        exit_code, stdout, stderr = self._run_command([
            'prophage', '--genome', valid_genome, '--dry-run'
        ])
        # Default should use singularity
        passed = exit_code == 0 or 'Backend: singularity' in stdout or 'Backend: conda' in stdout
        self._record_test("Default configuration loads", passed,
                         f"Exit code: {exit_code}")
        
        # Test with custom config file
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir, backend="conda")
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Create mock databases to avoid database check failure
            db_location = "/tmp/test_databases"
            os.makedirs(os.path.join(db_location, "genomad_db"), exist_ok=True)
            os.makedirs(os.path.join(db_location, "VIBRANT_db"), exist_ok=True)
            
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--dry-run'
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
        print("\n12. Testing Dry-run Functionality")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("dry_run")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Create config and databases to allow dry-run to complete
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        db_location = "/tmp/test_databases"
        os.makedirs(os.path.join(db_location, "genomad_db"), exist_ok=True)
        os.makedirs(os.path.join(db_location, "VIBRANT_db"), exist_ok=True)
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Test basic dry-run structure
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--dry-run'
            ])
            
            expected_sections = [
                'Prophage Detection Dry Run',
                'Input Configuration:',
                'Tool Configuration:',
                'Database Configuration:',
                'Output Configuration:',
                'Nextflow Command:',
                'Notes:'
            ]
            
            missing_sections = [section for section in expected_sections if section not in stdout]
            passed = exit_code == 0 and len(missing_sections) == 0
            self._record_test("Dry-run output structure correct", passed,
                             f"Exit code: {exit_code}, Missing sections: {missing_sections}")
            
            # Test with custom parameters
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome,
                '--genomad-preset', 'conservative',
                '--vibrant-min-length', '2000',
                '--threads', '8',
                '--dry-run'
            ])
            
            expected_params = ['conservative', '2000 bp', 'Threads: 8']
            missing_params = [param for param in expected_params if param not in stdout]
            passed = exit_code == 0 and len(missing_params) == 0
            self._record_test("Custom parameters in dry-run output", passed,
                             f"Exit code: {exit_code}, Missing params: {missing_params}")
            
            # Test Nextflow command structure
            passed = 'nextflow run main.nf' in stdout and '--workflow prophage' in stdout
            self._record_test("Nextflow command structure correct", passed,
                             f"Command structure found: {passed}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_output_directory_handling(self):
        """Test output directory creation and validation"""
        print("\n13. Testing Output Directory Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("output_handling")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Create config and databases
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        db_location = "/tmp/test_databases"
        os.makedirs(os.path.join(db_location, "genomad_db"), exist_ok=True)
        os.makedirs(os.path.join(db_location, "VIBRANT_db"), exist_ok=True)
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Test auto-creation of output directory
            new_outdir = os.path.join(test_dir, "new_prophage_results")
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome,
                '--outdir', new_outdir, '--dry-run'
            ])
            
            passed = exit_code == 0 and os.path.exists(new_outdir)
            self._record_test("Output directory auto-creation", passed,
                             f"Exit code: {exit_code}, Directory created: {os.path.exists(new_outdir)}")
            
            # Test using existing directory
            existing_outdir = os.path.join(test_dir, "existing_results")
            os.makedirs(existing_outdir)
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome,
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
        print("\n14. Testing Resume Functionality")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("resume_test")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Create config and databases
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        db_location = "/tmp/test_databases"
        os.makedirs(os.path.join(db_location, "genomad_db"), exist_ok=True)
        os.makedirs(os.path.join(db_location, "VIBRANT_db"), exist_ok=True)
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            # Test resume parameter in dry-run
            exit_code, stdout, stderr = self._run_command([
                'prophage', '--genome', valid_genome, '--resume', '--dry-run'
            ])
            
            passed = exit_code == 0 and '-resume' in stdout
            self._record_test("Resume parameter in command", passed,
                             f"Exit code: {exit_code}, -resume in output: {'-resume' in stdout}")
            
            # Test resume note in output
            passed = exit_code == 0 and 'Resume: enabled' in stdout
            self._record_test("Resume status shown in output", passed,
                             f"Resume status shown: {passed}")
        
        finally:
            os.environ['HOME'] = original_home
            shutil.rmtree(db_location, ignore_errors=True)

    def test_error_handling(self):
        """Test error conditions and exit codes"""
        print("\n15. Testing Error Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("error_handling")
        
        # Test various error conditions
        error_cases = [
            (['prophage'], "Missing required genome argument"),
            (['prophage', '--genome', '/nonexistent'], "Non-existent genome path"),
            (['prophage', '--genome', test_dir], "Directory without genome files"),
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
        print("Starting Phorager Prophage Command Test Suite")
        print("=" * 60)
        
        try:
            self.test_basic_help()
            self.test_input_validation_file()
            self.test_input_validation_directory()
            self.test_input_validation_bacterial_workflow()
            self.test_tool_selection_validation()
            self.test_parameter_conflict_validation()
            self.test_genomad_preset_validation()
            self.test_vibrant_min_length_validation()
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
    tester = ProphageTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())