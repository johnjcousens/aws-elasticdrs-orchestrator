#!/usr/bin/env python3
"""
Build Status Generator for AWS DRS Orchestration
Generates build status information for security scans
"""

import json
import os


def main():
    """Generate build status information."""
    # Determine build status
    status = 'passed' if os.environ.get('CODEBUILD_BUILD_SUCCEEDING', '0') == '1' else 'failed'
    message = 'Security scan passed' if status == 'passed' else 'Security scan failed'
    
    print(f'Security scan completed with status: {status}')
    
    # Create build status file
    build_status = {
        'status': status,
        'message': message
    }
    
    with open('reports/security/build-status.json', 'w') as f:
        json.dump(build_status, f, indent=2)


if __name__ == '__main__':
    main()