#!/usr/bin/env python3
"""
Validate test infrastructure setup.
Run this script to verify all dependencies and configuration are correct.
"""
import sys
import os

def check_python_version():
    """Verify Python version is 3.12+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need 3.12+")
        return False

def check_dependencies():
    """Check if required packages can be imported"""
    required_packages = [
        ("pytest", "pytest"),
        ("moto", "moto"),
        ("hypothesis", "hypothesis"),
        ("boto3", "boto3"),
    ]
    
    all_ok = True
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name} installed")
        except ImportError:
            print(f"❌ {package_name} not installed - run: pip install -r requirements.txt")
            all_ok = False
    
    return all_ok

def check_directory_structure():
    """Verify test directory structure exists"""
    base_dir = os.path.dirname(__file__)
    required_dirs = [
        "unit",
        "integration",
        "e2e",
        "fixtures",
        "mocks",
        "utils"
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            print(f"✅ Directory exists: {dir_name}/")
        else:
            print(f"❌ Directory missing: {dir_name}/")
            all_ok = False
    
    return all_ok

def check_config_files():
    """Verify configuration files exist"""
    base_dir = os.path.dirname(__file__)
    required_files = [
        "pytest.ini",
        "conftest.py",
        "requirements.txt"
    ]
    
    all_ok = True
    for file_name in required_files:
        file_path = os.path.join(base_dir, file_name)
        if os.path.isfile(file_path):
            print(f"✅ Config file exists: {file_name}")
        else:
            print(f"❌ Config file missing: {file_name}")
            all_ok = False
    
    return all_ok

def main():
    """Run all validation checks"""
    print("=" * 60)
    print("Execution Engine Test Infrastructure Validation")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Directory Structure", check_directory_structure),
        ("Configuration Files", check_config_files),
        ("Python Dependencies", check_dependencies),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 40)
        result = check_func()
        results.append(result)
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All checks passed! Test infrastructure is ready.")
        print()
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run unit tests: pytest unit/ -m unit")
        print("  3. Check coverage: pytest --cov=../../lambda")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
