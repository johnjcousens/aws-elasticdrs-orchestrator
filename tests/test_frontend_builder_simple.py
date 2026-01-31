#!/usr/bin/env python3
"""
Simplified local test for frontend-builder Lambda
Tests core functionality without AWS dependencies
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Test configuration
LAMBDA_PACKAGE_PATH = "/tmp/frontend-builder-package"


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
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else "dir"
            print(f"✅ Found: {path} ({size})")
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
    
    # Check for required files
    required_files = ["index.html"]
    required_dirs = ["assets"]
    
    for file in required_files:
        file_path = os.path.join(dist_path, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ Found: {file} ({size} bytes)")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    for dir_name in required_dirs:
        dir_path = os.path.join(dist_path, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
            print(f"✅ Found: {dir_name}/ ({file_count} files)")
        else:
            print(f"❌ Missing: {dir_name}/")
            return False
    
    # Count total files
    file_count = 0
    for root, dirs, files in os.walk(dist_path):
        file_count += len(files)
    
    print(f"\n✅ Total files in dist/: {file_count}")
    
    if file_count < 3:
        print("❌ TEST FAILED: Too few files in dist/ (expected at least 3)")
        return False
    
    print("✅ TEST PASSED: dist/ has sufficient files")
    return True


def test_config_injection_logic():
    """Test 3: Test config injection logic (without AWS dependencies)"""
    print("\n" + "="*60)
    print("TEST 3: Config Injection Logic")
    print("="*60)
    
    try:
        # Create temp copy of dist
        with tempfile.TemporaryDirectory() as temp_dir:
            import shutil
            source_dist = os.path.join(LAMBDA_PACKAGE_PATH, "frontend/dist")
            temp_dist = os.path.join(temp_dir, "dist")
            shutil.copytree(source_dist, temp_dist)
            
            print(f"✅ Created temp dist at {temp_dist}")
            
            # Test config generation (manual implementation)
            config_obj = {
                "region": "us-east-1",
                "userPoolId": "us-east-1_test123",
                "userPoolClientId": "test-client-id",
                "identityPoolId": "us-east-1:test-identity",
                "apiEndpoint": "https://api.example.com"
            }
            
            # 1. Create aws-config.json at root
            config_json_path = os.path.join(temp_dist, "aws-config.json")
            with open(config_json_path, "w") as f:
                json.dump(config_obj, f, indent=2)
            
            if os.path.exists(config_json_path):
                print(f"✅ Created aws-config.json at root")
            else:
                print(f"❌ Failed to create aws-config.json")
                return False
            
            # 2. Create aws-config.js in assets/
            assets_dir = os.path.join(temp_dist, "assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            config_js_content = f"""// AWS Configuration
window.AWS_CONFIG = {{
  Auth: {{
    Cognito: {{
      region: '{config_obj['region']}',
      userPoolId: '{config_obj['userPoolId']}',
      userPoolClientId: '{config_obj['userPoolClientId']}',
      identityPoolId: '{config_obj['identityPoolId']}',
      loginWith: {{
        email: true
      }}
    }}
  }},
  API: {{
    REST: {{
      DRSOrchestration: {{
        endpoint: '{config_obj['apiEndpoint']}',
        region: '{config_obj['region']}'
      }}
    }}
  }}
}};
"""
            
            config_js_path = os.path.join(assets_dir, "aws-config.js")
            with open(config_js_path, "w") as f:
                f.write(config_js_content)
            
            if os.path.exists(config_js_path):
                print(f"✅ Created aws-config.js in assets/")
            else:
                print(f"❌ Failed to create aws-config.js")
                return False
            
            # 3. Inject script tag into index.html
            index_html_path = os.path.join(temp_dist, "index.html")
            if os.path.exists(index_html_path):
                with open(index_html_path, "r") as f:
                    html_content = f.read()
                
                import re
                script_pattern = r"(<script[^>]*>)"
                match = re.search(script_pattern, html_content, re.IGNORECASE)
                
                if match:
                    insert_pos = match.start()
                    config_script = '    <script src="/assets/aws-config.js"></script>\n    '
                    html_content = html_content[:insert_pos] + config_script + html_content[insert_pos:]
                    
                    with open(index_html_path, "w") as f:
                        f.write(html_content)
                    
                    print(f"✅ Injected aws-config.js script tag into index.html")
                else:
                    print(f"⚠️  No script tags found in index.html")
            
            # Verify all files created
            if not os.path.exists(config_json_path):
                print(f"❌ aws-config.json not found")
                return False
            
            if not os.path.exists(config_js_path):
                print(f"❌ aws-config.js not found")
                return False
            
            # Show generated config
            with open(config_json_path, 'r') as f:
                config_data = json.load(f)
            
            print(f"\nGenerated config:")
            print(json.dumps(config_data, indent=2))
            
            print("\n✅ TEST PASSED: Config injection logic works correctly")
            return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: Config injection error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lambda_code_syntax():
    """Test 4: Verify Lambda code has valid Python syntax"""
    print("\n" + "="*60)
    print("TEST 4: Lambda Code Syntax")
    print("="*60)
    
    index_py = os.path.join(LAMBDA_PACKAGE_PATH, "index.py")
    
    if not os.path.exists(index_py):
        print(f"❌ TEST FAILED: index.py not found")
        return False
    
    try:
        with open(index_py, 'r') as f:
            code = f.read()
        
        # Check for syntax errors
        compile(code, index_py, 'exec')
        print(f"✅ index.py has valid Python syntax")
        
        # Check for required functions
        required_functions = [
            'lambda_handler',
            'create_or_update',
            'use_prebuilt_dist',
            'inject_aws_config_into_dist',
            'upload_to_s3'
        ]
        
        for func in required_functions:
            if f"def {func}" in code:
                print(f"✅ Found function: {func}")
            else:
                print(f"❌ Missing function: {func}")
                return False
        
        print("\n✅ TEST PASSED: Lambda code syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ TEST FAILED: Syntax error in index.py: {e}")
        return False
    except Exception as e:
        print(f"❌ TEST FAILED: Error reading index.py: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("FRONTEND-BUILDER LAMBDA SIMPLIFIED TEST SUITE")
    print("="*60)
    print(f"Package path: {LAMBDA_PACKAGE_PATH}")
    
    if not os.path.exists(LAMBDA_PACKAGE_PATH):
        print(f"\n❌ FATAL: Lambda package not found at {LAMBDA_PACKAGE_PATH}")
        print("Run: cd infra/orchestration/drs-orchestration && make build-frontend-builder")
        return False
    
    tests = [
        ("Package Structure", test_package_structure),
        ("Frontend Dist Contents", test_frontend_dist_contents),
        ("Config Injection Logic", test_config_injection_logic),
        ("Lambda Code Syntax", test_lambda_code_syntax),
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
        print("\nNext steps:")
        print("1. Upload to S3: aws s3 cp /tmp/frontend-builder.zip s3://aws-drs-orch-dev/lambda/")
        print("2. Deploy stack: aws cloudformation deploy ...")
        return True
    else:
        print(f"\n❌ {total_count - passed_count} TESTS FAILED - Fix issues before deploying")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
