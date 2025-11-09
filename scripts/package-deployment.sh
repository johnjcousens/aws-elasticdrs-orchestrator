#!/bin/bash
# Package AWS DRS Orchestration for S3-hosted deployment
# This script creates deployment artifacts ready to upload to S3

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
OUTPUT_DIR="deployment-package"
SKIP_FRONTEND=false

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Package AWS DRS Orchestration deployment artifacts for S3 hosting.

OPTIONS:
    -o, --output DIR        Output directory (default: deployment-package)
    -s, --skip-frontend     Skip frontend packaging (faster for Lambda-only updates)
    -h, --help             Display this help message

EXAMPLE:
    $0
    $0 --output my-deployment --skip-frontend

OUTPUT STRUCTURE:
    deployment-package/
    ├── master-template.yaml
    ├── nested-stacks/
    │   ├── database-stack.yaml
    │   ├── lambda-stack.yaml
    │   ├── api-stack.yaml
    │   ├── security-stack.yaml
    │   └── frontend-stack.yaml
    ├── lambda/
    │   ├── api-handler.zip
    │   ├── orchestration.zip
    │   ├── s3-cleanup.zip
    │   └── frontend-builder.zip
    └── frontend/
        └── frontend-source.zip

NEXT STEPS:
    1. Upload contents to S3 bucket:
       aws s3 sync deployment-package/ s3://your-solution-bucket/ --delete

    2. Make template publicly readable (optional):
       aws s3 cp s3://your-solution-bucket/master-template-consolidated.yaml \\
         s3://your-solution-bucket/master-template-consolidated.yaml \\
         --acl public-read

    3. Users deploy with:
       aws cloudformation create-stack \\
         --stack-name drs-orchestration \\
         --template-url https://your-solution-bucket.s3.amazonaws.com/master-template.yaml \\
         --parameters ParameterKey=SourceBucket,ParameterValue=your-solution-bucket \\
                      ParameterKey=AdminEmail,ParameterValue=admin@example.com \\
         --capabilities CAPABILITY_NAMED_IAM
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -s|--skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_info "AWS DRS Orchestration - Deployment Package Builder"
print_info "Project root: $PROJECT_ROOT"
print_info "Output directory: $OUTPUT_DIR"

# Check if required directories exist
if [ ! -d "$PROJECT_ROOT/lambda" ]; then
    print_error "Lambda directory not found: $PROJECT_ROOT/lambda"
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/frontend" ] && [ "$SKIP_FRONTEND" = false ]; then
    print_error "Frontend directory not found: $PROJECT_ROOT/frontend"
    exit 1
fi

# Create output directory structure
print_info "Creating output directory structure..."
mkdir -p "$OUTPUT_DIR/lambda"
mkdir -p "$OUTPUT_DIR/nested-stacks"
if [ "$SKIP_FRONTEND" = false ]; then
    mkdir -p "$OUTPUT_DIR/frontend"
fi

# Package Lambda functions
print_info "Packaging Lambda functions..."

# Function to package a Lambda function
package_lambda() {
    local LAMBDA_NAME=$1
    local LAMBDA_DIR="$PROJECT_ROOT/lambda/$LAMBDA_NAME"
    local OUTPUT_ZIP="$OUTPUT_DIR/lambda/$LAMBDA_NAME.zip"
    
    if [ ! -d "$LAMBDA_DIR" ]; then
        print_warn "Lambda directory not found: $LAMBDA_DIR (skipping)"
        return
    fi
    
    print_info "  Packaging $LAMBDA_NAME..."
    
    # Remove old zip if exists
    rm -f "$OUTPUT_ZIP"
    
    # Create zip file
    cd "$LAMBDA_DIR"
    
    # Check if requirements.txt exists and warn (dependencies should be packaged separately)
    if [ -f "requirements.txt" ]; then
        print_warn "    $LAMBDA_NAME has requirements.txt - ensure dependencies are included"
        
        # Install dependencies to temporary directory
        if command -v pip3 &> /dev/null; then
            print_info "    Installing Python dependencies..."
            TEMP_DIR=$(mktemp -d)
            pip3 install -r requirements.txt -t "$TEMP_DIR" --quiet
            
            # Create zip with dependencies first
            cd "$TEMP_DIR"
            zip -r9 "$PROJECT_ROOT/$OUTPUT_ZIP" . -q
            
            # Add Lambda code
            cd "$LAMBDA_DIR"
            zip -g "$PROJECT_ROOT/$OUTPUT_ZIP" *.py -q
            
            # Cleanup
            rm -rf "$TEMP_DIR"
            
            print_info "    ✓ Packaged with dependencies"
        else
            print_warn "    pip3 not found - packaging code only (dependencies must be added manually)"
            zip -r9 "$PROJECT_ROOT/$OUTPUT_ZIP" . -q
        fi
    else
        # No dependencies, just zip the code
        zip -r9 "$PROJECT_ROOT/$OUTPUT_ZIP" . -q
        print_info "    ✓ Packaged"
    fi
    
    cd "$PROJECT_ROOT"
    
    # Show zip size
    local SIZE=$(du -h "$OUTPUT_ZIP" | cut -f1)
    print_info "    Size: $SIZE"
}

# Package each Lambda function
package_lambda "api-handler"
package_lambda "orchestration"
package_lambda "custom-resources"
package_lambda "frontend-builder"

# Package frontend source
if [ "$SKIP_FRONTEND" = false ]; then
    print_info "Packaging frontend source code..."
    
    FRONTEND_DIR="$PROJECT_ROOT/frontend"
    FRONTEND_ZIP="$OUTPUT_DIR/frontend/frontend-source.zip"
    
    cd "$FRONTEND_DIR"
    
    # Remove old zip
    rm -f "$PROJECT_ROOT/$FRONTEND_ZIP"
    
    # Create zip excluding node_modules and dist
    print_info "  Creating frontend source archive..."
    zip -r9 "$PROJECT_ROOT/$FRONTEND_ZIP" . \
        -x "node_modules/*" \
        -x "dist/*" \
        -x ".git/*" \
        -x "*.log" \
        -q
    
    cd "$PROJECT_ROOT"
    
    # Show zip size
    SIZE=$(du -h "$FRONTEND_ZIP" | cut -f1)
    print_info "  ✓ Packaged (Size: $SIZE)"
else
    print_info "Skipping frontend packaging (--skip-frontend specified)"
fi

# Copy CloudFormation templates
print_info "Copying CloudFormation templates..."

# Copy master template
if [ -f "$PROJECT_ROOT/cfn/master-template.yaml" ]; then
    cp "$PROJECT_ROOT/cfn/master-template.yaml" "$OUTPUT_DIR/"
    print_info "  ✓ Copied master-template.yaml"
else
    print_error "  Master template not found!"
    exit 1
fi

# Copy nested stack templates
print_info "Copying nested stack templates..."
for template in database-stack lambda-stack api-stack security-stack frontend-stack; do
    if [ -f "$PROJECT_ROOT/cfn/${template}.yaml" ]; then
        cp "$PROJECT_ROOT/cfn/${template}.yaml" "$OUTPUT_DIR/nested-stacks/"
        print_info "  ✓ Copied ${template}.yaml"
    else
        print_error "  ${template}.yaml not found!"
        exit 1
    fi
done

# Create README for deployment package
print_info "Creating deployment README..."
cat > "$OUTPUT_DIR/README.md" << 'EOFREADME'
# AWS DRS Orchestration - Deployment Package

This package contains all artifacts needed to deploy the AWS DRS Orchestration solution via CloudFormation.

## Contents

```
deployment-package/
├── master-template.yaml               # Root CloudFormation template
├── nested-stacks/                     # Nested stack templates
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                            # Lambda function code
│   ├── api-handler.zip
│   ├── orchestration.zip
│   ├── s3-cleanup.zip
│   └── frontend-builder.zip
└── frontend/                          # React frontend source
    └── frontend-source.zip
```

## Deployment Steps

### 1. Upload to S3

Upload this entire directory structure to an S3 bucket:

```bash
# Create S3 bucket (if needed)
aws s3 mb s3://my-drs-solution-bucket --region us-west-2

# Upload deployment package
aws s3 sync . s3://my-drs-solution-bucket/ --exclude "README.md"

# Make template publicly readable (optional, for easier access)
aws s3 cp s3://my-drs-solution-bucket/master-template.yaml \
  s3://my-drs-solution-bucket/master-template.yaml \
  --acl public-read
```

### 2. Deploy Stack

#### Option A: AWS CLI

```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration \
  --template-url https://my-drs-solution-bucket.s3.amazonaws.com/master-template.yaml \
  --parameters \
    ParameterKey=SourceBucket,ParameterValue=my-drs-solution-bucket \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

#### Option B: AWS Console

1. Open AWS CloudFormation Console
2. Create Stack → With new resources
3. Template source: Amazon S3 URL
4. Enter URL: `https://my-drs-solution-bucket.s3.amazonaws.com/master-template.yaml`
5. Provide parameters:
   - **SourceBucket**: `my-drs-solution-bucket`
   - **AdminEmail**: Your email address
6. Acknowledge IAM capability
7. Create stack

### 3. Wait for Completion

Stack creation takes approximately 15-20 minutes. The Custom Resource will:
- Build the React frontend automatically
- Deploy to S3 + CloudFront
- Configure all AWS resources

### 4. Access the Application

After stack creation completes, find the CloudFront URL in stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

Open this URL in your browser to access the DRS Orchestration web application.

## Stack Parameters

### Required Parameters

- **SourceBucket**: S3 bucket containing deployment artifacts (this bucket)
- **AdminEmail**: Email address for initial Cognito admin user

### Optional Parameters

- **ProjectName**: Project identifier (default: drs-orchestration)
- **Environment**: Environment name (dev/test/prod, default: prod)
- **NotificationEmail**: Email for execution notifications

## Troubleshooting

### Stack creation fails

1. Check CloudWatch Logs for Custom Resource Lambda errors:
   ```bash
   aws logs tail /aws/lambda/drs-orchestration-frontend-builder --follow
   ```

2. Verify S3 bucket permissions allow CloudFormation to read objects

3. Ensure all Lambda zips are present in S3

### Frontend not deployed

1. Check Custom Resource Lambda logs
2. Verify frontend-source.zip exists in S3
3. Ensure Lambda has sufficient memory (2048 MB)

## Support

For issues or questions:
1. Review CloudFormation Events tab
2. Check CloudWatch Logs for Lambda functions
3. Refer to main documentation in project repository

---

**Package Generated**: $(date)
**Version**: 1.0.0
EOFREADME

print_info "  ✓ Created README.md"

# Summary
print_info ""
print_info "========================================="
print_info "Deployment package created successfully!"
print_info "========================================="
print_info ""
print_info "Output directory: $OUTPUT_DIR"
print_info ""
print_info "Contents:"
find "$OUTPUT_DIR" -type f | sed 's|^|  |'
print_info ""
print_info "Total size: $(du -sh "$OUTPUT_DIR" | cut -f1)"
print_info ""
print_info "Next steps:"
print_info "  1. Upload to S3:"
print_info "     aws s3 sync $OUTPUT_DIR/ s3://your-solution-bucket/ --exclude 'README.md'"
print_info ""
print_info "  2. Deploy stack:"
print_info "     aws cloudformation create-stack \\"
print_info "       --stack-name drs-orchestration \\"
print_info "       --template-url https://your-solution-bucket.s3.amazonaws.com/master-template.yaml \\"
print_info "       --parameters ParameterKey=SourceBucket,ParameterValue=your-solution-bucket \\"
print_info "                    ParameterKey=AdminEmail,ParameterValue=admin@example.com \\"
print_info "       --capabilities CAPABILITY_NAMED_IAM"
print_info ""
print_info "✓ Package ready for deployment!"
