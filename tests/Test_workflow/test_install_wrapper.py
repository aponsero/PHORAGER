#!/usr/bin/env python3
"""
Test Script for Phorager Install Command Wrapper

Comprehensive testing of the install command functionality including
tool/database validation, group expansion, configuration integration,
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


class InstallTester:
    """Test suite for phorager install command"""
    
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
        temp_dir = tempfile.mkdtemp(prefix=f"phorager_install_test_{name}_")
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
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
        passed = exit_code == 0 and 'install' in stdout
        self._record_test("Main help shows install command", passed,
                         f"Exit code: {exit_code}, 'install' in output: {'install' in stdout}")
        
        # Test install help
        exit_code, stdout, stderr = self._run_command(['install', '-h'])
        passed = exit_code == 0
        self._record_test("Install help command works", passed, f"Exit code: {exit_code}")
        
        if passed:
            # Check required arguments
            required_args = ['--tools', '--databases']
            optional_args = ['--dry-run', '--list-available']
            
            missing_required = [arg for arg in required_args if arg not in stdout]
            missing_optional = [arg for arg in optional_args if arg not in stdout]
            
            self._record_test("Tool/Database arguments present", len(missing_required) == 0,
                            f"Missing: {missing_required}")
            self._record_test("Optional arguments present", len(missing_optional) == 0,
                            f"Missing: {missing_optional}")
    
    def test_list_available(self):
        """Test --list-available functionality"""
        print("\n2. Testing --list-available")
        print("-" * 40)
        
        exit_code, stdout, stderr = self._run_command(['install', '--list-available'])
        
        # Check exit code
        passed = exit_code == 0
        self._record_test("List available succeeds", passed, f"Exit code: {exit_code}")
        
        # Check for all 8 tools
        all_tools = ['checkm2', 'drep', 'parsing_env', 'genomad', 'vibrant', 
                     'checkv', 'pharokka', 'phold']
        missing_tools = [tool for tool in all_tools if tool not in stdout]
        passed = len(missing_tools) == 0
        self._record_test("All 8 tools listed", passed, f"Missing: {missing_tools}")
        
        # Check for all 3 groups
        all_groups = ['genome', 'prophage', 'annotation']
        missing_groups = [group for group in all_groups if group not in stdout]
        passed = len(missing_groups) == 0
        self._record_test("All 3 tool groups listed", passed, f"Missing: {missing_groups}")
        
        # Check for all 6 databases
        all_databases = ['checkm2', 'genomad', 'vibrant', 'checkv', 'pharokka', 'phold']
        # Only check in databases section (not in tools section)
        databases_section = stdout.split('Available databases:')[-1] if 'Available databases:' in stdout else ""
        missing_databases = [db for db in all_databases if db not in databases_section]
        passed = len(missing_databases) == 0
        self._record_test("All 6 databases listed", passed, f"Missing: {missing_databases}")
        
        # Check for database sizes
        database_sizes = ['2.9GB', '1.4GB', '11.0GB', '6.4GB', '1.9GB', '15.0GB']
        missing_sizes = [size for size in database_sizes if size not in stdout]
        passed = len(missing_sizes) == 0
        self._record_test("Database sizes shown", passed, f"Missing: {missing_sizes}")
        
        # Check for tool descriptions
        descriptions = ['Genome quality', 'Genome dereplication', 'Prophage and virus detection',
                       'Virus genome quality', 'Phage genome annotation', 'Protein function prediction']
        missing_descriptions = [desc for desc in descriptions if desc not in stdout]
        passed = len(missing_descriptions) == 0
        self._record_test("Tool descriptions shown", passed, f"Missing: {missing_descriptions}")
    
    def test_tool_validation(self):
        """Test individual tool validation"""
        print("\n3. Testing Tool Validation")
        print("-" * 40)
        
        # Test valid individual tools
        valid_tools = ['checkm2', 'drep', 'genomad', 'vibrant', 'checkv', 'pharokka', 'phold']
        for tool in valid_tools:
            exit_code, stdout, stderr = self._run_command(['install', '--tools', tool, '--dry-run'])
            passed = exit_code == 0 and tool in stdout
            self._record_test(f"Valid tool '{tool}' accepted", passed,
                             f"Exit code: {exit_code}, tool in output: {tool in stdout}")
        
        # Test invalid tool
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'invalid_tool', '--dry-run'])
        passed = exit_code != 0 and 'Invalid tools' in stdout
        self._record_test("Invalid tool rejected", passed,
                         f"Exit code: {exit_code}, error shown: {'Invalid tools' in stdout}")
        
        # Test multiple valid tools
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2,drep', '--dry-run'])
        passed = exit_code == 0 and 'checkm2' in stdout and 'drep' in stdout
        self._record_test("Multiple valid tools accepted", passed,
                         f"Exit code: {exit_code}")
        
        # Test mixed valid and invalid
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2,invalid', '--dry-run'])
        passed = exit_code != 0 and 'Invalid tools' in stdout
        self._record_test("Mixed valid/invalid tools rejected", passed,
                         f"Exit code: {exit_code}")
    
    def test_group_expansion(self):
        """Test tool group expansion and deduplication"""
        print("\n4. Testing Group Expansion")
        print("-" * 40)
        
        # Test genome group expansion
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'genome', '--dry-run'])
        genome_tools = ['checkm2', 'drep', 'parsing_env']
        missing = [tool for tool in genome_tools if tool not in stdout]
        passed = exit_code == 0 and len(missing) == 0
        self._record_test("Genome group expands correctly", passed,
                         f"Exit code: {exit_code}, Missing tools: {missing}")
        
        # Test prophage group expansion
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'prophage', '--dry-run'])
        prophage_tools = ['genomad', 'vibrant', 'parsing_env']
        missing = [tool for tool in prophage_tools if tool not in stdout]
        passed = exit_code == 0 and len(missing) == 0
        self._record_test("Prophage group expands correctly", passed,
                         f"Exit code: {exit_code}, Missing tools: {missing}")
        
        # Test annotation group expansion
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'annotation', '--dry-run'])
        annotation_tools = ['checkv', 'pharokka', 'phold', 'parsing_env']
        missing = [tool for tool in annotation_tools if tool not in stdout]
        passed = exit_code == 0 and len(missing) == 0
        self._record_test("Annotation group expands correctly", passed,
                         f"Exit code: {exit_code}, Missing tools: {missing}")
        
        # Test deduplication: genome + prophage should only have parsing_env once
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'genome,prophage', '--dry-run'])
        # Count occurrences of parsing_env in the tools list
        tools_section = stdout.split('Tools to install')[1].split('Nextflow command')[0] if 'Tools to install' in stdout else stdout
        parsing_env_count = tools_section.count('parsing_env')
        passed = exit_code == 0 and parsing_env_count == 1
        self._record_test("Deduplication works (genome+prophage)", passed,
                         f"Exit code: {exit_code}, parsing_env count: {parsing_env_count} (should be 1)")
        
        # Test 'all' expansion
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'all', '--dry-run'])
        all_tools = ['checkm2', 'drep', 'parsing_env', 'genomad', 'vibrant', 
                     'checkv', 'pharokka', 'phold']
        missing = [tool for tool in all_tools if tool not in stdout]
        passed = exit_code == 0 and len(missing) == 0
        self._record_test("'all' expands to all 8 tools", passed,
                         f"Exit code: {exit_code}, Missing tools: {missing}")
    
    def test_database_validation(self):
        """Test database validation"""
        print("\n5. Testing Database Validation")
        print("-" * 40)
        
        # Test valid individual databases
        valid_databases = ['checkm2', 'genomad', 'vibrant', 'checkv', 'pharokka', 'phold']
        for db in valid_databases:
            exit_code, stdout, stderr = self._run_command(['install', '--databases', db, '--dry-run'])
            passed = exit_code == 0 and db in stdout
            self._record_test(f"Valid database '{db}' accepted", passed,
                             f"Exit code: {exit_code}, database in output: {db in stdout}")
        
        # Test invalid database
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'invalid_db', '--dry-run'])
        passed = exit_code != 0 and 'Invalid databases' in stdout
        self._record_test("Invalid database rejected", passed,
                         f"Exit code: {exit_code}, error shown: {'Invalid databases' in stdout}")
        
        # Test 'all' databases
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'all', '--dry-run'])
        all_databases = ['checkm2', 'genomad', 'vibrant', 'checkv', 'pharokka', 'phold']
        missing = [db for db in all_databases if db not in stdout]
        passed = exit_code == 0 and len(missing) == 0
        self._record_test("'all' expands to all 6 databases", passed,
                         f"Exit code: {exit_code}, Missing databases: {missing}")
        
        # Test tool without database (drep has no database)
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'drep', '--dry-run'])
        passed = exit_code != 0 and 'Invalid databases' in stdout
        self._record_test("Tool without database rejected as database", passed,
                         f"Exit code: {exit_code}")
    
    def test_no_parameters_error(self):
        """Test that install requires tools or databases"""
        print("\n6. Testing No Parameters Error")
        print("-" * 40)
        
        # Test with no tools or databases
        exit_code, stdout, stderr = self._run_command(['install', '--dry-run'])
        passed = exit_code != 0 and 'No tools or databases specified' in stdout
        self._record_test("No parameters error shown", passed,
                         f"Exit code: {exit_code}, error message present: {'No tools' in stdout}")
    
    def test_dry_run_output(self):
        """Test dry-run output formatting"""
        print("\n7. Testing Dry-run Output")
        print("-" * 40)
        
        # Test basic dry-run structure
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2', '--dry-run'])
        
        expected_sections = [
            'Phorager Installation Plan',
            'Configuration:',
            'Backend:',
            'Tools to install',
            'Databases to install',
            'Nextflow command that would be executed:',
            'NOTE: This is a dry-run'
        ]
        
        missing_sections = [section for section in expected_sections if section not in stdout]
        passed = exit_code == 0 and len(missing_sections) == 0
        self._record_test("Dry-run output structure correct", passed,
                         f"Exit code: {exit_code}, Missing sections: {missing_sections}")
        
        # Test tool descriptions in output
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2,genomad', '--dry-run'])
        descriptions = ['Genome quality', 'Prophage and virus detection']
        missing_descriptions = [desc for desc in descriptions if desc not in stdout]
        passed = exit_code == 0 and len(missing_descriptions) == 0
        self._record_test("Tool descriptions shown in dry-run", passed,
                         f"Exit code: {exit_code}, Missing descriptions: {missing_descriptions}")
        
        # Test database sizes in output
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'checkm2,genomad', '--dry-run'])
        sizes = ['2.9GB', '1.4GB']
        missing_sizes = [size for size in sizes if size not in stdout]
        passed = exit_code == 0 and len(missing_sizes) == 0
        self._record_test("Database sizes shown in dry-run", passed,
                         f"Exit code: {exit_code}, Missing sizes: {missing_sizes}")
        
        # Test total size calculation
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'checkm2,genomad,vibrant', '--dry-run'])
        # Total should be 2.9 + 1.4 + 11.0 = 15.3GB
        passed = exit_code == 0 and '15.3GB' in stdout
        self._record_test("Total database size calculated", passed,
                         f"Exit code: {exit_code}, Total size shown: {'15.3GB' in stdout}")
        
        # Test cleanup note in dry-run
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2', '--dry-run'])
        passed = exit_code == 0 and 'cleanup = true' in stdout
        self._record_test("Cleanup config note shown", passed,
                         f"Exit code: {exit_code}, cleanup note present: {'cleanup' in stdout}")
    
    def test_configuration_integration(self):
        """Test config system integration"""
        print("\n8. Testing Configuration Integration")
        print("-" * 40)
        
        test_dir = self._create_temp_dir("config_integration")
        
        # Test with default configuration (singularity)
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2', '--dry-run'])
        passed = exit_code == 0 and 'Backend: singularity' in stdout
        self._record_test("Default backend (singularity)", passed,
                         f"Exit code: {exit_code}, default backend detected: {'singularity' in stdout}")
        
        # Test with custom config (conda)
        config_dir = os.path.join(test_dir, ".phorager")
        self._create_test_config(config_dir, backend="conda")
        
        original_home = os.environ.get('HOME', '')
        os.environ['HOME'] = test_dir
        
        try:
            exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2', '--dry-run'])
            passed = exit_code == 0 and 'Backend: conda' in stdout
            self._record_test("Custom backend (conda) loads", passed,
                             f"Exit code: {exit_code}, conda backend detected: {'conda' in stdout}")
            
            # Check that conda profile is used
            passed = exit_code == 0 and '-profile conda' in stdout
            self._record_test("Conda profile in command", passed,
                             f"Exit code: {exit_code}, '-profile conda' in command: {'-profile conda' in stdout}")
        finally:
            os.environ['HOME'] = original_home
    
    def test_nextflow_command_building(self):
        """Test Nextflow command structure"""
        print("\n9. Testing Nextflow Command Building")
        print("-" * 40)
        
        # Test basic command structure
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2', '--dry-run'])
        
        command_parts = ['nextflow run main.nf', '--workflow install', '--tools']
        missing_parts = [part for part in command_parts if part not in stdout]
        passed = exit_code == 0 and len(missing_parts) == 0
        self._record_test("Basic Nextflow command structure", passed,
                         f"Exit code: {exit_code}, Missing parts: {missing_parts}")
                
        # Test tools and databases in command
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2,drep', '--databases', 'checkm2', '--dry-run'])
        passed = (exit_code == 0 and 
                 '--tools checkm2,drep' in stdout and 
                 '--databases checkm2' in stdout)
        self._record_test("Tools and databases in command", passed,
                         f"Exit code: {exit_code}")
    
    def test_edge_cases(self):
        """Test edge cases and special scenarios"""
        print("\n10. Testing Edge Cases")
        print("-" * 40)
        
        # Test only tools (no databases)
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'drep', '--dry-run'])
        passed = exit_code == 0 and 'drep' in stdout
        self._record_test("Only tools (no databases)", passed,
                         f"Exit code: {exit_code}")
        
        # Test only databases (no tools)
        exit_code, stdout, stderr = self._run_command(['install', '--databases', 'checkm2', '--dry-run'])
        passed = exit_code == 0 and 'checkm2' in stdout
        self._record_test("Only databases (no tools)", passed,
                         f"Exit code: {exit_code}")
        
        # Test whitespace handling in tool list
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'checkm2, drep, parsing_env', '--dry-run'])
        passed = exit_code == 0 and all(tool in stdout for tool in ['checkm2', 'drep', 'parsing_env'])
        self._record_test("Whitespace handling in tool list", passed,
                         f"Exit code: {exit_code}")
        
        # Test case sensitivity (should be case-sensitive)
        exit_code, stdout, stderr = self._run_command(['install', '--tools', 'CheckM2', '--dry-run'])
        passed = exit_code != 0
        self._record_test("Case sensitivity (reject uppercase)", passed,
                         f"Exit code: {exit_code} (should fail for incorrect case)")
    
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
        print("Starting Phorager Install Command Test Suite")
        print("=" * 60)
        
        try:
            self.test_basic_help()
            self.test_list_available()
            self.test_tool_validation()
            self.test_group_expansion()
            self.test_database_validation()
            self.test_no_parameters_error()
            self.test_dry_run_output()
            self.test_configuration_integration()
            self.test_nextflow_command_building()
            self.test_edge_cases()
            
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
    tester = InstallTester()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())