#!/usr/bin/env python3
"""
Test Script for Phorager Bacterial Workflow Wrapper

Comprehensive testing of the bacterial command functionality including
parameter validation, input validation, configuration integration, 
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


class BacterialTester:
    """Test suite for phorager bacterial command"""
    
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
        temp_dir = tempfile.mkdtemp(prefix=f"phorager_test_{name}_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def _create_test_genome_file(self, path: str, name: str = "test_genome.fasta") -> str:
        """Create a test genome file"""
        genome_path = os.path.join(path, name)
        with open(genome_path, 'w') as f:
            f.write(">test_genome_1\nATCGATCGATCGATCG\n")
            f.write(">test_genome_2\nGCTAGCTAGCTAGCTA\n")
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
    
    def _create_test_config(self, config_dir: str) -> str:
        """Create a test configuration file"""
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")
        
        test_config = {
            "backend": "conda",
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
        passed = exit_code == 0 and 'bacterial' in stdout
        self._record_test("Main help shows bacterial command", passed, 
                         f"Exit code: {exit_code}, 'bacterial' in output: {'bacterial' in stdout}")
        
        # Test bacterial help
        exit_code, stdout, stderr = self._run_command(['bacterial', '-h'])
        passed = exit_code == 0
        self._record_test("Bacterial help command works", passed, f"Exit code: {exit_code}")
        
        if passed:
            # Check required arguments
            required_args = ['--genome']
            optional_args = ['--completeness-threshold', '--contamination-threshold', 
                           '--drep-ani-threshold', '--outdir', '--threads', '--dry-run']
            
            missing_required = [arg for arg in required_args if arg not in stdout]
            missing_optional = [arg for arg in optional_args if arg not in stdout]
            
            self._record_test("Required arguments present", len(missing_required) == 0,
                            f"Missing: {missing_required}")
            self._record_test("Optional arguments present", len(missing_optional) == 0,
                            f"Missing: {missing_optional}")

    def test_input_validation(self):
        """Test genome file/directory validation"""
        print("\n2. Testing Input Validation")
        print("-" * 40)
        
        # Test missing genome argument
        exit_code, stdout, stderr = self._run_command(['bacterial'])
        passed = exit_code != 0
        self._record_test("Missing genome argument fails", passed,
                         f"Exit code: {exit_code} (should be non-zero)")
        
        # Test non-existent file
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', '/nonexistent/path', '--dry-run'])
        passed = exit_code != 0 and ('does not exist' in stderr or 'Error:' in stdout)
        self._record_test("Non-existent genome path fails", passed,
                         f"Exit code: {exit_code}, error detected: {('does not exist' in stderr or 'Error:' in stdout)}")
        
        # Create test files and directories
        test_dir = self._create_temp_dir("input_validation")
        
        # Test invalid file extension
        invalid_file = os.path.join(test_dir, "test.txt")
        with open(invalid_file, 'w') as f:
            f.write("test content")
        
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', invalid_file, '--dry-run'])
        passed = exit_code != 0
        self._record_test("Invalid file extension fails", passed,
                         f"Exit code: {exit_code} (should fail for .txt file)")
        
        # Test valid single file
        valid_file = self._create_test_genome_file(test_dir, "valid_genome.fasta")
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', valid_file, '--dry-run'])
        passed = exit_code == 0
        self._record_test("Valid single genome file succeeds", passed,
                         f"Exit code: {exit_code}")
        
        # Test valid directory with genome files
        valid_dir = self._create_test_genome_dir(test_dir)
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', valid_dir, '--dry-run'])
        passed = exit_code == 0
        self._record_test("Valid genome directory succeeds", passed,
                         f"Exit code: {exit_code}")
        
        # Test empty directory
        empty_dir = os.path.join(test_dir, "empty")
        os.makedirs(empty_dir)
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', empty_dir, '--dry-run'])
        passed = exit_code != 0
        self._record_test("Empty genome directory fails", passed,
                         f"Exit code: {exit_code} (should fail for empty directory)")

    def test_parameter_validation(self):
        """Test workflow parameter validation"""
        print("\n3. Testing Parameter Validation")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("param_validation")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test invalid completeness threshold
        test_cases = [
            (['--completeness-threshold', '-10'], "Negative completeness threshold"),
            (['--completeness-threshold', '150'], "Completeness threshold > 100"),
            (['--contamination-threshold', '-5'], "Negative contamination threshold"),
            (['--contamination-threshold', '110'], "Contamination threshold > 100"),
            (['--drep-ani-threshold', '-0.1'], "Negative ANI threshold"),
            (['--drep-ani-threshold', '1.5'], "ANI threshold > 1"),
            (['--threads', '0'], "Zero threads"),
            (['--threads', '-1'], "Negative threads"),
        ]
        
        for args, description in test_cases:
            cmd = ['bacterial', '--genome', valid_genome, '--dry-run'] + args
            exit_code, stdout, stderr = self._run_command(cmd)
            passed = exit_code != 0
            self._record_test(f"{description} fails", passed,
                             f"Exit code: {exit_code} for args: {args}")
        
        # Test valid parameters
        valid_cases = [
            (['--completeness-threshold', '90'], "Valid completeness threshold"),
            (['--contamination-threshold', '10'], "Valid contamination threshold"),
            (['--drep-ani-threshold', '0.95'], "Valid ANI threshold"),
            (['--threads', '4'], "Valid thread count"),
        ]
        
        for args, description in valid_cases:
            cmd = ['bacterial', '--genome', valid_genome, '--dry-run'] + args
            exit_code, stdout, stderr = self._run_command(cmd)
            passed = exit_code == 0
            self._record_test(f"{description} succeeds", passed,
                             f"Exit code: {exit_code} for args: {args}")

    def test_configuration_integration(self):
        """Test config system integration"""
        print("\n4. Testing Configuration Integration")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("config_integration")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test with default configuration (no config file)
        exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', valid_genome, '--dry-run'])
        passed = exit_code == 0 and 'Backend: singularity' in stdout
        self._record_test("Default configuration works", passed,
                         f"Exit code: {exit_code}, default backend detected: {'Backend: singularity' in stdout}")
        
        # Test with custom config file
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir)
        
        # Temporarily set HOME to test directory to use test config
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            exit_code, stdout, stderr = self._run_command(['bacterial', '--genome', valid_genome, '--dry-run'])
            passed = exit_code == 0 and 'Backend: conda' in stdout
            self._record_test("Custom configuration loads", passed,
                             f"Exit code: {exit_code}, custom backend detected: {'Backend: conda' in stdout}")
        finally:
            os.environ['HOME'] = original_home

    def test_dry_run_functionality(self):
        """Test dry-run output and command building"""
        print("\n5. Testing Dry-run Functionality")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("dry_run")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test basic dry-run
        cmd = ['bacterial', '--genome', valid_genome, '--dry-run']
        exit_code, stdout, stderr = self._run_command(cmd)
        
        # Check dry-run output format
        expected_sections = [
            'Phorager Bacterial Workflow Plan',
            'Configuration:',
            'Input:',
            'Workflow Parameters:',
            'Nextflow command that would be executed:',
            'NOTE: This is a dry-run'
        ]
        
        missing_sections = [section for section in expected_sections if section not in stdout]
        passed = exit_code == 0 and len(missing_sections) == 0
        self._record_test("Dry-run output format correct", passed,
                         f"Exit code: {exit_code}, Missing sections: {missing_sections}")
        
        # Test command building with custom parameters
        cmd = ['bacterial', '--genome', valid_genome, '--dry-run',
               '--completeness-threshold', '90', '--contamination-threshold', '10',
               '--drep-ani-threshold', '0.95', '--threads', '8']
        exit_code, stdout, stderr = self._run_command(cmd)
        
        # Check if parameters appear in output
        expected_params = ['90.0%', '10.0%', '0.95', 'Threads: 8']
        missing_params = [param for param in expected_params if param not in stdout]
        passed = exit_code == 0 and len(missing_params) == 0
        self._record_test("Custom parameters in dry-run output", passed,
                         f"Exit code: {exit_code}, Missing params: {missing_params}")
        
        # Test default thread behavior (should show auto-detected message)
        cmd_default = ['bacterial', '--genome', valid_genome, '--dry-run']
        exit_code, stdout, stderr = self._run_command(cmd_default)
        passed = exit_code == 0 and 'Threads: (using Nextflow default - auto-detected)' in stdout
        self._record_test("Default threads show auto-detected message", passed,
                         f"Exit code: {exit_code}, Auto-detected message found: {'auto-detected' in stdout}")
        
        # Check nextflow command structure
        if 'nextflow run main.nf' in stdout and '--workflow bacterial' in stdout:
            self._record_test("Nextflow command structure correct", True)
        else:
            self._record_test("Nextflow command structure correct", False,
                             "Missing 'nextflow run main.nf' or '--workflow bacterial'")

    def test_output_directory_handling(self):
        """Test output directory creation and validation"""
        print("\n6. Testing Output Directory Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("output_handling")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test auto-creation of output directory
        new_outdir = os.path.join(test_dir, "new_results")
        cmd = ['bacterial', '--genome', valid_genome, '--outdir', new_outdir, '--dry-run']
        exit_code, stdout, stderr = self._run_command(cmd)
        
        passed = exit_code == 0 and os.path.exists(new_outdir)
        self._record_test("Output directory auto-creation", passed,
                         f"Exit code: {exit_code}, Directory created: {os.path.exists(new_outdir)}")
        
        # Test using existing directory
        existing_outdir = os.path.join(test_dir, "existing_results")
        os.makedirs(existing_outdir)
        cmd = ['bacterial', '--genome', valid_genome, '--outdir', existing_outdir, '--dry-run']
        exit_code, stdout, stderr = self._run_command(cmd)
        
        passed = exit_code == 0 and 'Warning: Using existing' in stdout
        self._record_test("Existing output directory warning", passed,
                         f"Exit code: {exit_code}, Warning shown: {'Warning: Using existing' in stdout}")

    def test_error_handling(self):
        """Test error conditions and exit codes"""
        print("\n7. Testing Error Handling")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("error_handling")
        
        # Test various error conditions
        error_cases = [
            ([], "No arguments provided"),
            (['bacterial'], "Missing required genome argument"),
            (['bacterial', '--genome', '/nonexistent'], "Non-existent genome path"),
            (['bacterial', '--genome', '/dev/null'], "Invalid genome file"),
            (['bacterial', '--genome', test_dir], "Directory without genome files"),
        ]
        
        for args, description in error_cases:
            exit_code, stdout, stderr = self._run_command(args)
            passed = exit_code != 0
            self._record_test(f"Error case: {description}", passed,
                             f"Exit code: {exit_code} (should be non-zero)")

    def test_resume_functionality(self):
        """Test resume parameter handling"""
        print("\n8. Testing Resume Functionality")  
        print("-" * 40)
        
        test_dir = self._create_temp_dir("resume_test")
        valid_genome = self._create_test_genome_file(test_dir)
        
        # Test resume parameter in dry-run
        cmd = ['bacterial', '--genome', valid_genome, '--resume', '--dry-run']
        exit_code, stdout, stderr = self._run_command(cmd)
        
        passed = exit_code == 0 and '-resume' in stdout
        self._record_test("Resume parameter in command", passed,
                         f"Exit code: {exit_code}, -resume in output: {'-resume' in stdout}")

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
        print("Starting Phorager Bacterial Command Test Suite")
        print("=" * 60)
        
        try:
            self.test_basic_help()
            self.test_input_validation()
            self.test_parameter_validation()
            self.test_configuration_integration()
            self.test_dry_run_functionality()
            self.test_output_directory_handling()
            self.test_error_handling()
            self.test_resume_functionality()
            
        except Exception as e:
            print(f"Test suite failed with exception: {e}")
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
    tester = BacterialTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())