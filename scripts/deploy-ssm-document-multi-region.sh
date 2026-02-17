#!/bin/bash
set -e

# Deploy SSM Document to all 20 DRS-supported regions (standard commercial regions)
# Usage: ./deploy-ssm-document-multi-region.sh [--profile PROFILE] [--dry-run]

DOCUMENT_NAME="DRS-InstallAgent-CrossAccount"
DOCUMENT_FILE="$(dirname "$0")/ssm-document-drs-agent-installer.yaml"

# 20 DRS-supported standard commercial regions
DRS_REGIONS=(
  # Americas (4)
  us-east-1 us-east-2 us-west-1 us-west-2
  # Europe (4)
  eu-west-1 eu-west-2 eu-west-3 eu-central-1
  # Asia Pacific (6)
  ap-northeast-1 ap-northeast-2 ap-southeast-1 ap-southeast-2 ap-south-1 ap-northeast-3
  # Other (6)
  ca-central-1 sa-east-1 eu-north-1 ap-east-1
)

AWS_PROFILE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      AWS_PROFILE="--profile $2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [ ! -f "$DOCUMENT_FILE" ]; then
  echo "Error: SSM Document file not found: $DOCUMENT_FILE"
  exit 1
fi

echo "Deploying SSM Document '$DOCUMENT_NAME' to ${#DRS_REGIONS[@]} DRS-supported regions..."
echo ""

SUCCESS_COUNT=0
FAILED_REGIONS=()

for region in "${DRS_REGIONS[@]}"; do
  echo "[$region] Deploying SSM Document..."
  
  if [ "$DRY_RUN" = true ]; then
    echo "[$region] DRY RUN - Would deploy to $region"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    continue
  fi
  
  # Check if document exists
  if aws ssm describe-document \
    --name "$DOCUMENT_NAME" \
    --region "$region" \
    $AWS_PROFILE \
    &>/dev/null; then
    
    # Update existing document
    if aws ssm update-document \
      --name "$DOCUMENT_NAME" \
      --content "file://$DOCUMENT_FILE" \
      --document-format YAML \
      --document-version '$LATEST' \
      --region "$region" \
      $AWS_PROFILE \
      &>/dev/null; then
      
      echo "[$region] ✓ Updated existing document"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "[$region] ✗ Failed to update document"
      FAILED_REGIONS+=("$region")
    fi
  else
    # Create new document
    if aws ssm create-document \
      --name "$DOCUMENT_NAME" \
      --content "file://$DOCUMENT_FILE" \
      --document-type "Command" \
      --document-format YAML \
      --region "$region" \
      $AWS_PROFILE \
      &>/dev/null; then
      
      echo "[$region] ✓ Created new document"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      echo "[$region] ✗ Failed to create document"
      FAILED_REGIONS+=("$region")
    fi
  fi
done

echo ""
echo "Deployment Summary:"
echo "  Success: $SUCCESS_COUNT/${#DRS_REGIONS[@]} regions"
echo "  Failed: ${#FAILED_REGIONS[@]} regions"

if [ ${#FAILED_REGIONS[@]} -gt 0 ]; then
  echo ""
  echo "Failed regions:"
  for region in "${FAILED_REGIONS[@]}"; do
    echo "  - $region"
  done
  exit 1
fi

echo ""
echo "✓ SSM Document deployed successfully to all DRS-supported regions"
