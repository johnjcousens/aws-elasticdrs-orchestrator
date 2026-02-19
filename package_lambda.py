#!/usr/bin/env python3
"""
Lambda Function Packager
Packages Lambda functions with their dependencies into deployment-ready ZIP files.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path





def package_lambda(function_name: str, source_dir: Path, output_dir: Path):
    """
    Package a Lambda function with its dependencies.
    
    Args:
        function_name: Name of the Lambda function
        source_dir: Source directory containing the Lambda code
        output_dir: Output directory for the ZIP file
    """
    print(f"Packaging {function_name}...")
    
    # Create temporary build directory
    build_dir = output_dir / "temp" / function_name
    build_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Copy Lambda code
        for item in source_dir.iterdir():
            if item.name == "__pycache__":
                continue
            if item.name == "requirements.txt":
                continue
            if item.is_file():
                shutil.copy2(item, build_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, build_dir / item.name, dirs_exist_ok=True)
        
        # Install dependencies if requirements.txt exists
        requirements_file = source_dir / "requirements.txt"
        if requirements_file.exists():
            # Check if requirements file has content
            with open(requirements_file) as f:
                content = f.read().strip()
            
            if content:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(requirements_file),
                        "-t",
                        str(build_dir),
                        "--no-cache-dir",
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"  ⚠ Warning: pip install failed for {function_name}")
                    print(f"    {result.stderr[:200]}")
                    # Continue anyway - some functions may not need dependencies
        
        # Copy shared code if it exists (maintain directory structure)
        shared_dir = source_dir.parent / "shared"
        if shared_dir.exists():
            target_shared_dir = build_dir / "shared"
            target_shared_dir.mkdir(exist_ok=True)
            for item in shared_dir.iterdir():
                if item.name == "__pycache__":
                    continue
                if item.is_file():
                    shutil.copy2(item, target_shared_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(
                        item, target_shared_dir / item.name, dirs_exist_ok=True
                    )
        
        # Special handling for frontend-deployer: include frontend/dist/
        if function_name == "frontend-deployer":
            frontend_dist = source_dir.parent.parent / "frontend" / "dist"
            if frontend_dist.exists():
                target_frontend_dir = build_dir / "frontend"
                target_frontend_dir.mkdir(exist_ok=True)
                shutil.copytree(
                    frontend_dist,
                    target_frontend_dir / "dist",
                    dirs_exist_ok=True
                )
                print(f"  ✓ Included frontend/dist/ in package")
            else:
                print(f"  ⚠ Warning: frontend/dist/ not found - "
                      f"run 'npm run build' in frontend/ first")
        
        # Create ZIP file
        zip_file = output_dir / f"{function_name}.zip"
        shutil.make_archive(
            str(zip_file.with_suffix("")), "zip", str(build_dir)
        )
        
        print(f"  ✓ {function_name}.zip created")
        
    finally:
        # Cleanup temporary directory
        if build_dir.exists():
            shutil.rmtree(build_dir.parent)


def main():
    """Main packaging function."""
    # Get project root
    project_root = Path(__file__).parent
    lambda_dir = project_root / "lambda"
    output_dir = project_root / "build" / "lambda"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Lambda functions to package
    functions = [
        ("data-management-handler", "data-management-handler"),
        ("execution-handler", "execution-handler"),
        ("query-handler", "query-handler"),
        ("dr-orchestration-stepfunction", "dr-orchestration-stepfunction"),
        ("frontend-deployer", "frontend-deployer"),
        # Note: drs-agent-deployer not yet implemented in CloudFormation
        # Note: notification functionality moved to lambda/shared/notifications.py
    ]
    
    # Package each function
    for zip_name, dir_name in functions:
        source_dir = lambda_dir / dir_name
        if source_dir.exists():
            package_lambda(zip_name, source_dir, output_dir)
        else:
            print(f"  ⚠ Skipping {dir_name} (directory not found)")
    
    print("\n✓ All Lambda functions packaged successfully")


if __name__ == "__main__":
    main()
