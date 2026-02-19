#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

test_dir = Path("tests/unit")
failing_files = []

for test_file in sorted(test_dir.glob("test_*.py")):
    try:
        result = subprocess.run(
            [".venv/bin/pytest", str(test_file), "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "FAILED" in result.stdout or "ERROR" in result.stdout or result.returncode != 0:
            failing_files.append(test_file.name)
            print(f"FAIL: {test_file.name}")
    except subprocess.TimeoutExpired:
        failing_files.append(test_file.name)
        print(f"TIMEOUT: {test_file.name}")

print(f"\n{len(failing_files)} failing test files")
for f in failing_files:
    print(f"  {f}")
