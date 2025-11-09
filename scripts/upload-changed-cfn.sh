#!/bin/bash
#
# Selective CloudFormation Template Upload Script
# Uploads only CloudFormation templates that have changed since last commit
# Target: s3://onprem-aws-ia/AWS-DRS-Orchestration/cfn/
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BUCKET="onprem-aws-ia/AWS-DRS-Orchestration"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFN_DIR="${PROJECT_ROOT}/cfn"
DRY_RUN=false
FORCE_ALL=false

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

print_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [S3_BUCKET]

Uploads CloudFormation templates that have changed since last commit to S3.

OPTIONS:
    --dry-run       Show what would be uploaded without actually uploading
    --force-all     Upload all CloudFormation templates regardless of changes
    -h, --help      Show this help message

ARGUMENTS:
    S3_BUCKET       S3 bucket path (default: ${DEFAULT_BUCKET})
                    Format: bucket-name/path or s3://bucket-name/path

EXAMPLES:
    # Upload changed templates to default bucket
    $0

    # Dry-run to see what would be uploaded
    $0 --dry-run

    # Force upload all templates
    $0 --force-all

    # Upload to custom bucket
    $0 my-bucket/my-path

EOF
}

# Parse command line arguments
DEPLOYMENT_PATH="${DEFAULT_BUCKET}"
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force-all)
            FORCE_ALL=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        s3://*)
            DEPLOYMENT_PATH="${1#s3://}"
            shift
            ;;
        *)
            DEPLOYMENT_PATH="$1"
            shift
            ;;
    esac
done

# Extract bucket name and path
BUCKET_NAME=$(echo "${DEPLOYMENT_PATH}" | cut -d'/' -f1)
BUCKET_PATH=$(echo "${DEPLOYMENT_PATH}" | cut -d'/' -f2-)

# If bucket path is same as bucket name, no subdirectory specified
if [ "${BUCKET_PATH}" = "${BUCKET_NAME}" ]; then
    BUCKET_PATH=""
fi

print_info "Starting selective CloudFormation upload..."
print_info "Project Root: ${PROJECT_ROOT}"
print_info "CFN Directory: ${CFN_DIR}"
print_info "Target Bucket: s3://${BUCKET_NAME}/${BUCKET_PATH}"

if [ "${DRY_RUN}" = true ]; then
    print_warn "DRY-RUN MODE: No files will be uploaded"
fi

if [ "${FORCE_ALL}" = true ]; then
    print_warn "FORCE-ALL MODE: Uploading all templates"
fi

# Verify AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Verify S3 bucket exists
print_info "Verifying S3 bucket accessibility..."
if ! aws s3 ls "s3://${BUCKET_NAME}" &> /dev/null; then
    print_error "S3 bucket '${BUCKET_NAME}' does not exist or is not accessible"
    exit 1
fi

# Verify we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository. This script requires git for change detection."
    exit 1
fi

# Function to detect changed CloudFormation files
detect_changed_cfn_files() {
    local changed_files=()
    
    if [ "${FORCE_ALL}" = true ]; then
        # Upload all CloudFormation templates
        print_info "Detecting all CloudFormation templates..."
        while IFS= read -r file; do
            changed_files+=("$file")
        done < <(find "${CFN_DIR}" -name "*.yaml" -type f 2>/dev/null)
    else
        # Get changed files since last commit
        print_info "Detecting changed CloudFormation templates since last commit..."
        
        # Check if we have any commits
        if ! git log -1 &>/dev/null; then
            print_warn "No git commit history found. Uploading all templates."
            while IFS= read -r file; do
                changed_files+=("$file")
            done < <(find "${CFN_DIR}" -name "*.yaml" -type f 2>/dev/null)
        else
            # Get files changed in last commit
            while IFS= read -r file; do
                # Convert to absolute path
                full_path="${PROJECT_ROOT}/${file}"
                if [ -f "$full_path" ]; then
                    changed_files+=("$full_path")
                fi
            done < <(git diff --name-only HEAD~1 HEAD -- cfn/*.yaml 2>/dev/null)
            
            # Also check for uncommitted changes
            while IFS= read -r file; do
                full_path="${PROJECT_ROOT}/${file}"
                if [ -f "$full_path" ]; then
                    # Check if not already in array
                    found=false
                    for existing in "${changed_files[@]}"; do
                        if [ "$existing" = "$full_path" ]; then
                            found=true
                            break
                        fi
                    done
                    if [ "$found" = false ]; then
                        changed_files+=("$full_path")
                    fi
                fi
            done < <(git diff --name-only HEAD -- cfn/*.yaml 2>/dev/null)
        fi
    fi
    
    # Return the array
    printf '%s\n' "${changed_files[@]}"
}

# Get list of changed files
CHANGED_FILES=()
while IFS= read -r file; do
    CHANGED_FILES+=("$file")
done < <(detect_changed_cfn_files)

if [ ${#CHANGED_FILES[@]} -eq 0 ]; then
    print_info "No CloudFormation templates have changed. Nothing to upload."
    exit 0
fi

print_info "Found ${#CHANGED_FILES[@]} template(s) to upload:"
for file in "${CHANGED_FILES[@]}"; do
    filename=$(basename "$file")
    echo "  - ${filename}"
done
echo ""

# Upload each changed file
UPLOAD_COUNT=0
FAILED_COUNT=0
declare -a UPLOADED_FILES

for file in "${CHANGED_FILES[@]}"; do
    filename=$(basename "$file")
    
    # Construct S3 key
    if [ -n "${BUCKET_PATH}" ]; then
        s3_key="${BUCKET_PATH}/cfn/${filename}"
    else
        s3_key="cfn/${filename}"
    fi
    
    s3_uri="s3://${BUCKET_NAME}/${s3_key}"
    
    print_info "Processing: ${filename}"
    
    if [ "${DRY_RUN}" = true ]; then
        echo "  Would upload to: ${s3_uri}"
        ((UPLOAD_COUNT++))
        UPLOADED_FILES+=("${filename}:${s3_uri}")
    else
        # Perform actual upload
        if aws s3 cp "$file" "${s3_uri}" --no-progress 2>&1; then
            echo -e "  ${GREEN}✓${NC} Uploaded to: ${s3_uri}"
            ((UPLOAD_COUNT++))
            UPLOADED_FILES+=("${filename}:${s3_uri}")
        else
            echo -e "  ${RED}✗${NC} Failed to upload: ${filename}"
            ((FAILED_COUNT++))
        fi
    fi
    echo ""
done

# Generate upload manifest
MANIFEST_FILE="${PROJECT_ROOT}/.cfn_upload_manifest.json"
print_info "Generating upload manifest..."

cat > "${MANIFEST_FILE}" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "bucket": "s3://${BUCKET_NAME}/${BUCKET_PATH}",
  "dryRun": ${DRY_RUN},
  "forceAll": ${FORCE_ALL},
  "uploadedCount": ${UPLOAD_COUNT},
  "failedCount": ${FAILED_COUNT},
  "files": [
EOF

# Add uploaded files to manifest
FIRST=true
for entry in "${UPLOADED_FILES[@]}"; do
    filename="${entry%%:*}"
    s3_uri="${entry#*:}"
    
    if [ "$FIRST" = true ]; then
        FIRST=false
    else
        echo "," >> "${MANIFEST_FILE}"
    fi
    
    cat >> "${MANIFEST_FILE}" <<EOF
    {
      "filename": "${filename}",
      "s3Uri": "${s3_uri}"
    }
EOF
done

cat >> "${MANIFEST_FILE}" <<EOF

  ]
}
EOF

print_info "Manifest saved to: ${MANIFEST_FILE}"

# Print summary
echo ""
print_info "================================"
if [ "${DRY_RUN}" = true ]; then
    print_info "DRY-RUN SUMMARY"
else
    print_info "UPLOAD SUMMARY"
fi
print_info "================================"
echo ""
print_info "Templates processed: ${#CHANGED_FILES[@]}"
print_info "Successfully uploaded: ${UPLOAD_COUNT}"
if [ ${FAILED_COUNT} -gt 0 ]; then
    print_error "Failed uploads: ${FAILED_COUNT}"
fi
print_info "Target bucket: s3://${BUCKET_NAME}/${BUCKET_PATH}/cfn/"
echo ""

if [ "${DRY_RUN}" = true ]; then
    print_info "To perform actual upload, run without --dry-run flag"
elif [ ${FAILED_COUNT} -eq 0 ]; then
    print_info "All templates uploaded successfully!"
    echo ""
    print_info "CloudFormation templates are now available at:"
    print_info "  https://${BUCKET_NAME}.s3.amazonaws.com/${BUCKET_PATH}/cfn/"
else
    print_error "Some uploads failed. Check the output above for details."
    exit 1
fi
