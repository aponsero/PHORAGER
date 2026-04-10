#!/usr/bin/env python3
"""
Comprehensive test script for Phorager wrapper functionality.

Tests config and install commands with expected output validation.
"""

import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional


class PhoragerTester:
    """Test runner for Phorager wrapper commands"""
    
    def __init__(self, phorager_path: str = "./phorager"):
        self.phorager_path = phorager_path
        self.test_results = []
        self.config_backup = None
        
        # Backup existing config if it exists
        self._backup_config()
    
    def _backup_config(self):
        """Backup existing config file"""
        config_file = Path.home() / '.phorager' / 'config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config_backup = f.read()
            print(f"📁 Backed up existing config from {config_file}")
    
    def _restore_config(self):
        """Restore original config file"""
        config_file = Path.home() / '.phorager' / 'config.json'
        if self.config_backup:
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                f.write(self.config_backup)
            print(f"📁 Restored original config to {config_file}")
        elif config_file.exists():
            config_file.unlink()
            print(f"📁 Removed test config file")
    
    def run_command(self, args: List[str], expect_success: bool = True) -> Dict[str, Any]:
        """Run a phorager command and capture output"""
        cmd = [self.phorager_path] + args
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'expected_success': expect_success
            }
        except subprocess.TimeoutExpired:
            return {
                'command': ' '.join(cmd),
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False,
                'expected_success': expect_success
            }
        except Exception as e:
            return {
                'command': ' '.join(cmd),
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False,
                'expected_success': expect_success
            }
    
    def test_basic_help(self):
        """Test basic help functionality"""
        print("\n🧪 Testing Basic Help")
        print("=" * 50)
        
        # Test main help
        result = self.run_command(['-h'])
        print(f"Command: {result['command']}")
        if result['success']:
            print("✅ Main help works")
            if 'config' in result['stdout'] and 'install' in result['stdout']:
                print("✅ Both config and install commands visible")
            else:
                print("❌ Missing expected commands in help")
        else:
            print(f"❌ Main help failed: {result['stderr']}")
        
        self.test_results.append(('Basic Help', result))
    
    def test_config_functionality(self):
        """Test all config command functionality"""
        print("\n🧪 Testing Config Functionality")
        print("=" * 50)
        
        # Test config help
        result = self.run_command(['config', '-h'])
        print(f"Command: {result['command']}")
        if result['success'] and 'set' in result['stdout'] and 'show' in result['stdout']:
            print("✅ Config help works")
        else:
            print(f"❌ Config help failed")
        
        # Test initial config show (should show defaults)
        result = self.run_command(['config', 'show'])
        print(f"\nCommand: {result['command']}")
        if result['success']:
            print("✅ Config show works")
            if 'singularity' in result['stdout'] and 'pipeline defaults' in result['stdout']:
                print("✅ Shows expected defaults")
            else:
                print("❌ Unexpected default values")
        else:
            print(f"❌ Config show failed: {result['stderr']}")
        
        # Test setting backend
        result = self.run_command(['config', 'set', '--backend', 'conda'])
        print(f"\nCommand: {result['command']}")
        if result['success'] and 'Backend set to: conda' in result['stdout']:
            print("✅ Backend setting works")
        else:
            print(f"❌ Backend setting failed")
        
        # Test setting database location
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_command(['config', 'set', '--db-location', tmpdir])
            print(f"\nCommand: {result['command']}")
            if result['success'] and 'Database location set to:' in result['stdout']:
                print("✅ Database location setting works")
            else:
                print(f"❌ Database location setting failed")
        
        # Test config show after changes
        result = self.run_command(['config', 'show'])
        print(f"\nCommand: {result['command']}")
        if result['success'] and 'conda' in result['stdout']:
            print("✅ Config persistence works")
        else:
            print(f"❌ Config persistence failed")
        
        # Test JSON output
        result = self.run_command(['config', 'show', '--json'])
        print(f"\nCommand: {result['command']}")
        if result['success']:
            try:
                config_data = json.loads(result['stdout'])
                if config_data.get('backend') == 'conda':
                    print("✅ JSON output works")
                else:
                    print("❌ JSON output incorrect")
            except json.JSONDecodeError:
                print("❌ Invalid JSON output")
        else:
            print(f"❌ JSON output failed")
        
        # Test config reset
        result = self.run_command(['config', 'reset', '--confirm'])
        print(f"\nCommand: {result['command']}")
        if result['success'] and 'reset to defaults' in result['stdout']:
            print("✅ Config reset works")
        else:
            print(f"❌ Config reset failed")
        
        self.test_results.append(('Config Functionality', 'Multiple tests completed'))
    
    def test_install_validation(self):
        """Test install command validation"""
        print("\n🧪 Testing Install Command Validation")
        print("=" * 50)
        
        # Test list available
        result = self.run_command(['install', '--list-available'])
        print(f"Command: {result['command']}")
        if (result['success'] and 'checkm2' in result['stdout'] and 
            'genome:' in result['stdout'] and 'Available tools:' in result['stdout']):
            print("✅ List available works")
        else:
            print(f"❌ List available failed")
        
        # Test no parameters (should fail)
        result = self.run_command(['install'], expect_success=False)
        print(f"\nCommand: {result['command']}")
        if not result['success'] and 'No tools or databases specified' in result['stdout']:
            print("✅ No parameters validation works")
        else:
            print(f"❌ No parameters validation failed")
        
        # Test invalid tool (should fail)
        result = self.run_command(['install', '--tools', 'invalid_tool'], expect_success=False)
        print(f"\nCommand: {result['command']}")
        if not result['success'] and 'Invalid tools:' in result['stdout']:
            print("✅ Invalid tool validation works")
        else:
            print(f"❌ Invalid tool validation failed")
        
        # Test invalid database (should fail)
        result = self.run_command(['install', '--databases', 'invalid_db'], expect_success=False)
        print(f"\nCommand: {result['command']}")
        if not result['success'] and 'Invalid databases:' in result['stdout']:
            print("✅ Invalid database validation works")
        else:
            print(f"❌ Invalid database validation failed")
        
        self.test_results.append(('Install Validation', 'Multiple tests completed'))
    
    def test_install_functionality(self):
        """Test install command functionality"""
        print("\n🧪 Testing Install Command Functionality")
        print("=" * 50)
        
        # Test valid tools installation
        result = self.run_command(['install', '--tools', 'checkm2,drep', '--databases', 'checkm2'])
        print(f"Command: {result['command']}")
        if (result['success'] and 'checkm2' in result['stdout'] and 'drep' in result['stdout'] and
            'nextflow run main.nf' in result['stdout']):
            print("✅ Valid tools installation planning works")
        else:
            print(f"❌ Valid tools installation planning failed")
        
        # Test group expansion
        result = self.run_command(['install', '--tools', 'genome', '--databases', 'checkm2'])
        print(f"\nCommand: {result['command']}")
        if (result['success'] and 'checkm2' in result['stdout'] and 
            'drep' in result['stdout'] and 'parsing_env' in result['stdout']):
            print("✅ Group expansion works")
        else:
            print(f"❌ Group expansion failed")
        
        # Test 'all' expansion
        result = self.run_command(['install', '--tools', 'all', '--databases', 'all'])
        print(f"\nCommand: {result['command']}")
        if (result['success'] and 'checkm2' in result['stdout'] and 
            'Tools to install (3):' in result['stdout']):
            print("✅ 'All' expansion works")
        else:
            print(f"❌ 'All' expansion failed")
        
        # Test with different backend
        self.run_command(['config', 'set', '--backend', 'conda'])
        result = self.run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2'])
        print(f"\nCommand: {result['command']}")
        if result['success'] and '-profile conda' in result['stdout']:
            print("✅ Backend selection works")
        else:
            print(f"❌ Backend selection failed")
        
        # Test behavior flags
        result = self.run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2', 
                                  '--force', '--verbose', '--resume'])
        print(f"\nCommand: {result['command']}")
        if (result['success'] and '--force' in result['stdout'] and 
            '-resume' in result['stdout'] and '--verbose true' in result['stdout']):
            print("✅ Behavior flags work")
        else:
            print(f"❌ Behavior flags failed")
        
        self.test_results.append(('Install Functionality', 'Multiple tests completed'))
    
    def test_config_install_integration(self):
        """Test integration between config and install commands"""
        print("\n🧪 Testing Config-Install Integration")
        print("=" * 50)
        
        # Reset config and test singularity default
        self.run_command(['config', 'reset', '--confirm'])
        result = self.run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2'])
        print(f"Command: {result['command']}")
        if result['success'] and '-profile conda' not in result['stdout']:
            print("✅ Singularity default works")
        else:
            print(f"❌ Singularity default failed")
        
        # Set conda and test
        self.run_command(['config', 'set', '--backend', 'conda'])
        result = self.run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2'])
        print(f"\nCommand: {result['command']}")
        if result['success'] and '-profile conda' in result['stdout']:
            print("✅ Conda config integration works")
        else:
            print(f"❌ Conda config integration failed")
        
        # Test with custom database location
        with tempfile.TemporaryDirectory() as tmpdir:
            self.run_command(['config', 'set', '--db-location', tmpdir])
            result = self.run_command(['install', '--tools', 'checkm2', '--databases', 'checkm2'])
            print(f"\nCommand: {result['command']}")
            if result['success'] and '--global_db_location' in result['stdout']:
                print("✅ Custom database location integration works")
            else:
                print(f"❌ Custom database location integration failed")
        
        self.test_results.append(('Config-Install Integration', 'Multiple tests completed'))
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Phorager Wrapper Tests")
        print("=" * 60)
        
        try:
            self.test_basic_help()
            self.test_config_functionality()
            self.test_install_validation()
            self.test_install_functionality()
            self.test_config_install_integration()
            
        finally:
            # Always restore config
            self._restore_config()
        
        # Print summary
        print("\n📊 Test Summary")
        print("=" * 60)
        print(f"Total test categories: {len(self.test_results)}")
        
        # Check if phorager executable exists
        if not Path(self.phorager_path).exists():
            print(f"❌ Phorager script not found at {self.phorager_path}")
        else:
            print(f"✅ Found phorager script at {self.phorager_path}")
        
        print("\n🎯 Key functionality tested:")
        print("   - Config set/show/reset")
        print("   - Install parameter validation")
        print("   - Tool group expansion")
        print("   - Backend selection")
        print("   - Nextflow command building")
        print("   - Config-install integration")


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Phorager wrapper functionality')
    parser.add_argument('--phorager-path', default='./phorager', 
                       help='Path to phorager script')
    args = parser.parse_args()
    
    tester = PhoragerTester(args.phorager_path)
    tester.run_all_tests()


if __name__ == '__main__':
    main()