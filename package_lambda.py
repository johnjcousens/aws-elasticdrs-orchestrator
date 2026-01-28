#!/usr/bin/env python3
"""
Package all Lambda functions with correct directory structure.

Repository Structure:
    This script works from the repository root directory.
    All paths are relative to the repository root.

Each Lambda gets its own zip with:
- index.py at root
- shared/ module included
- Dependencies from requirements.txt installed
- For frontend-deployer: includes pre-built frontend/dist/
"""
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def install_dependencies(requirements_file: Path, target_dir: Path) -> bool:
    """Install dependencies from requirements.txt to target directory."""
    if not requirements_file.exists():
        return True

    try:
        subprocess.run(
            [
                "pip",
                "install",
                "-r",
                str(requirements_file),
                "-t",
                str(target_dir),
                "--quiet",
                "--no-cache-dir",
            ],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  WARNING: Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("  WARNING: pip not found")
        return False


def package_lambda_function(
    lambda_name: str,
    lambda_dir: Path,
    shared_dir: Path,
    output_dir: Path,
    requirements_file: Path = None,
    include_frontend: bool = False,
    frontend_dir: Path = None,
):
    """Package a single Lambda function."""
    output_zip = output_dir / f"{lambda_name}.zip"

    # Remove old zip if exists
    if output_zip.exists():
        output_zip.unlink()

    file_count = 0

    # Create temp directory for dependencies
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Install dependencies if requirements.txt exists
        if requirements_file and requirements_file.exists():
            install_dependencies(requirements_file, temp_path)

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add dependencies from temp directory
            if temp_path.exists():
                for root, dirs, files in os.walk(temp_path):
                    # Skip __pycache__ and .dist-info directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if not d.endswith((".dist-info", "__pycache__"))
                    ]
                    for file in files:
                        if file.endswith(".pyc"):
                            continue
                        file_path = Path(root) / file
                        arcname = str(file_path.relative_to(temp_path))
                        zipf.write(file_path, arcname)
                        file_count += 1

            # Add index.py at root
            index_file = lambda_dir / "index.py"
            if index_file.exists():
                zipf.write(index_file, "index.py")
                file_count += 1

            # Add shared module
            if shared_dir.exists():
                # Create shared/__init__.py if it doesn't exist
                init_file = shared_dir / "__init__.py"
                if not init_file.exists():
                    zipf.writestr("shared/__init__.py", "")
                    file_count += 1
                for py_file in shared_dir.glob("*.py"):
                    arcname = f"shared/{py_file.name}"
                    zipf.write(py_file, arcname)
                    file_count += 1

            # For frontend-builder, include the pre-built frontend
            if include_frontend and frontend_dir and frontend_dir.exists():
                dist_dir = frontend_dir / "dist"
                if dist_dir.exists():
                    for root, dirs, files in os.walk(dist_dir):
                        for file in files:
                            file_path = Path(root) / file
                            # Put dist contents under frontend/dist/
                            rel_path = file_path.relative_to(frontend_dir)
                            arcname = f"frontend/{rel_path}"
                            zipf.write(file_path, arcname)
                            file_count += 1

    size_kb = output_zip.stat().st_size / 1024
    print(f"  {lambda_name}.zip: {size_kb:.1f} KB ({file_count} files)")
    return output_zip


def build_frontend_if_needed(frontend_dir: Path) -> bool:
    """Build frontend if dist/ doesn't exist or is outdated."""
    dist_dir = frontend_dir / "dist"

    # Check if we need to build
    if not dist_dir.exists():
        print("  Frontend dist/ not found, building...")
        need_build = True
    else:
        # Check if source is newer than dist
        src_dir = frontend_dir / "src"
        if src_dir.exists():
            src_mtime = max(
                f.stat().st_mtime
                for f in src_dir.rglob("*")
                if f.is_file()
            )
            dist_mtime = min(
                f.stat().st_mtime
                for f in dist_dir.rglob("*")
                if f.is_file()
            )
            need_build = src_mtime > dist_mtime
            if need_build:
                print("  Frontend source newer than dist, rebuilding...")
        else:
            need_build = False

    if need_build:
        try:
            # Run npm build
            subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                check=True,
                capture_output=True,
            )
            print("  Frontend build complete")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  WARNING: Frontend build failed: {e}")
            return False
        except FileNotFoundError:
            print("  WARNING: npm not found, skipping frontend build")
            return False

    return True


def main():
    """Package all Lambda functions."""
    print("Packaging Lambda functions...")
    print()

    # Paths
    lambda_base = Path("lambda")
    shared_dir = lambda_base / "shared"
    output_dir = Path("build/lambda")
    frontend_dir = Path("frontend")
    requirements_file = lambda_base / "requirements.txt"

    # Create build directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Lambda functions to package
    # Current architecture (decomposed handlers):
    lambdas = [
        ("query-handler", False),  # Read-only infrastructure queries
        ("data-management-handler", False),  # Protection Groups + Recovery Plans CRUD
        ("execution-handler", False),  # DR execution lifecycle operations
        ("frontend-deployer", True),  # Frontend deployment automation (includes frontend dist)
        ("notification-formatter", False),  # SNS notification formatting
        ("orchestration-stepfunctions", False),  # Step Functions orchestration
    ]

    # Build frontend if needed (for frontend-builder Lambda)
    if any(needs_frontend for _, needs_frontend in lambdas):
        print("Checking frontend build...")
        build_frontend_if_needed(frontend_dir)
        print()

    # Package each Lambda
    print("Creating Lambda packages:")
    for lambda_name, needs_frontend in lambdas:
        lambda_dir = lambda_base / lambda_name
        if lambda_dir.exists():
            package_lambda_function(
                lambda_name=lambda_name,
                lambda_dir=lambda_dir,
                shared_dir=shared_dir,
                output_dir=output_dir,
                requirements_file=requirements_file,
                include_frontend=needs_frontend,
                frontend_dir=frontend_dir if needs_frontend else None,
            )
        else:
            print(f"  {lambda_name}: SKIPPED (directory not found)")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
