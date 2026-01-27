#!/usr/bin/env python3
"""
Local test for frontend-builder Lambda
Tests the Lambda package before CloudFormation deployment
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Test configuration
LAMBDA_PACKAGE_PATH = "/tmp/frontend-builder-package"
TEST_BUCKET = "test-bucket"
TEST_DISTRIBUTION_ID = "d123456789"
TEST_API_ENDPOINT = "https://api.example.com"
TEST_USER_POOL_ID = "us-east-1_test123"
TEST_CLIENT_ID = "test-client-id"
TEST_REGION = "us-east-1"


def test_package_structure():
    """Test 1: Verify Lambda package structure"""
    print("\n" + "="*60)
    print("TEST 1: Package Structure")
    print("="*60)
    
    required_paths = [
        "index.py",
        "frontend/dist/index.html",
        "frontend/dist/assets",
        "shared/security_utils.py",
    ]
    
    missing = []
    for path in required_paths:
        full_path = os.path.join(LAMBDA_PACKAGE_PATH, path)
        if os.path.exists(full_path):
            print(f"✅ Found: {path}")
        else:
            print(f"❌ Missing: {path}")
            missing.append(path)
    
    if missing:
        print(f"\n❌ TEST FAILED: Missing {len(missing)} required paths")
        return False
    
    print("\n✅ TEST PASSED: All required paths exist")
    return True


def test_frontend_dist_contents():
    """Test 2: Verify frontend dist has built files"""
    print("\n" + "="*60)
    print("TEST 2: Frontend Dist Contents")
    print("="*60)
    
    dist_path = os.path.join(LAMBDA_PACKAGE_PATH, "frontend/dist")
    
    if not os.path.exists(dist_path):
        print(f"❌ TEST FAILED: dist directory not found at {dist_path}")
        return False
    
    # Count files
    file_count = 0
    for root, dirs, files in os.walk(dist_path):
        file_count += len(files)
        for file in files[:5]:  # Show first 5 files
            rel_path = os.path.relpath(os.path.join(root, file), dist_path)
            print(f"  - {rel_path}")
    
    if file_count > 5:
        print(f"  ... and {file_count - 5} more files")
    
    print(f"\n✅ Found {file_count} files in dist/")
    
    if file_count < 3:
        print("❌ TEST FAILED: Too few files in dist/ (expected at least 3)")
        return False
    
    print("✅ TEST PASSED: dist/ has sufficient files")
    return True


def test_security_utils_import():
    """Test 3: Verify security_utils can be imported"""
    print("\n" + "="*60)
    print("TEST 3: Security Utils Import")
    print("="*60)
    
    # Add package to path
    sys.path.insert(0, LAMBDA_PACKAGE_PATH)
    
    try:
        from shared.security_utils import (
            validate_file_path,
            sanitize_string_input,
            log_security_event,
            safe_aws_client_call
        )
        print("✅ Successfully imported security_utils functions")
        
        # Test validate_file_path with /var/task
        try:
            validate_file_path("/var/task/frontend/dist")
            print("✅ validate_file_path allows /var/task")
        except Exception as e:
            print(f"❌ validate_file_path blocks /var/task: {e}")
            return False
        
        print("✅ TEST PASSED: security_utils working correctly")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: Cannot import security_utils: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lambda_handler_import():
    """Test 4: Verify Lambda handler can be imported"""
    print("\n" + "="*60)
    print("TEST 4: Lambda Handler Import")
    print("="*60)
    
    try:
        from index import lambda_handler, create_or_update, use_prebuilt_dist
        print("✅ Successfully imported Lambda handler functions")
        print("✅ TEST PASSED: Lambda handler imports correctly")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: Cannot import Lambda handler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_use_prebuilt_dist():
    """Test 5: Test use_prebuilt_dist function"""
    print("\n" + "="*60)
    print("TEST 5: use_prebuilt_dist Function")
    print("="*60)
    
    try:
        from index import use_prebuilt_dist
        
        frontend_path = os.path.join(LAMBDA_PACKAGE_PATH, "frontend")
        dist_dir = use_prebuilt_dist(frontend_path)
        
        print(f"✅ use_prebuilt_dist returned: {dist_dir}")
        
        if not os.path.exists(dist_dir):
            print(f"❌ TEST FAILED: Returned dist_dir doesn't exist: {dist_dir}")
            return False
        
        # Check for index.html
        index_html = os.path.join(dist_dir, "index.html")
        if not os.path.exists(index_html):
            print(f"❌ TEST FAILED: index.html not found in {dist_dir}")
            return False
        
        print(f"✅ Found index.html in dist/")
        print("✅ TEST PASSED: use_prebuilt_dist works correctly")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: use_prebuilt_dist error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inject_aws_config():
    """Test 6: Test inject_aws_config_into_dist function"""
    print("\n" + "="*60)
    print("TEST 6: inject_aws_config_into_dist Function")
    print("="*60)
    
    try:
        from index import inject_aws_config_into_dist
        
        # Create temp copy of dist
        with tempfile.TemporaryDirectory() as temp_dir:
            import shutil
            source_dist = os.path.join(LAMBDA_PACKAGE_PATH, "frontend/dist")
            temp_dist = os.path.join(temp_dir, "dist")
            shutil.copytree(source_dist, temp_dist)
            
            # Test properties
            properties = {
                'Region': TEST_REGION,
                'UserPoolId': TEST_USER_POOL_ID,
                'UserPoolClientId': TEST_CLIENT_ID,
                'ApiEndpoint': TEST_API_ENDPOINT
            }
            
            # Inject config
            inject_aws_config_into_dist(temp_dist, properties)
            
            # Verify aws-config.json created at root
            config_json = os.path.join(temp_dist, "aws-config.json")
            if not os.path.exists(config_json):
                print(f"❌ TEST FAILED: aws-config.json not created at {config_json}")
                return False
            
            print(f"✅ Created aws-config.json at root")
            
            # Verify aws-config.js created in assets/
            config_js = os.path.join(temp_dist, "assets/aws-config.js")
            if not os.path.exists(config_js):
                print(f"❌ TEST FAILED: aws-config.js not created at {config_js}")
                return False
            
            print(f"✅ Created aws-config.js in assets/")
            
            # Verify index.html has script tag
            index_html = os.path.join(temp_dist, "index.html")
            with open(index_html, 'r') as f:
                html_content = f.read()
            
            if 'aws-config.js' not in html_content:
                print(f"❌ TEST FAILED: index.html doesn't reference aws-config.js")
                return False
            
            print(f"✅ index.html references aws-config.js")
            
            # Show config content
            with open(config_json, 'r') as f:
                config_data = json.load(f)
            
            print(f"\nGenerated config:")
            print(json.dumps(config_data, indent=2))
            
            print("\n✅ TEST PASSED: inject_aws_config_into_dist works correctly")
            return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: inject_aws_config_into_dist error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("FRONTEND-BUILDER LAMBDA LOCAL TEST SUITE")
    print("="*60)
    print(f"Package path: {LAMBDA_PACKAGE_PATH}")
    
    if not os.path.exists(LAMBDA_PACKAGE_PATH):
        print(f"\n❌ FATAL: Lambda package not found at {LAMBDA_PACKAGE_PATH}")
        print("Run: cd infra/orchestration/drs-orchestration && make build-frontend-builder")
        return False
    
    tests = [
        ("Package Structure", test_package_structure),
        ("Frontend Dist Contents", test_frontend_dist_contents),
        ("Security Utils Import", test_security_utils_import),
        ("Lambda Handler Import", test_lambda_handler_import),
        ("use_prebuilt_dist Function", test_use_prebuilt_dist),
        ("inject_aws_config Function", test_inject_aws_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {test_name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED - Lambda package is ready for deployment!")
        return True
    else:
        print(f"\n❌ {total_count - passed_count} TESTS FAILED - Fix issues before deploying")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
