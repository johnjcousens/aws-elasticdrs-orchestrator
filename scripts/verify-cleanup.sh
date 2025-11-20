#!/bin/bash
# Verify no orphaned resources remain after stack deletion
# Usage: ./scripts/verify-cleanup.sh <environment>

set -e

ENV=${1:-test}
PROJECT="drs-orchestration"
ERRORS=0

echo "🔍 Verifying cleanup for ${PROJECT}-${ENV}..."
echo ""

# Check SSM Documents
echo "📄 Checking SSM Documents..."
DOCS=$(aws ssm list-documents \
  --filters "Key=Name,Values=${PROJECT}" \
  --query "DocumentIdentifiers[?contains(Name, '-${ENV}')].Name" \
  --output json 2>/dev/null || echo "[]")

if [ "$DOCS" != "[]" ]; then
  echo "❌ Orphaned SSM Documents found:"
  echo "$DOCS" | jq -r '.[]' | while read doc; do
    echo "  - $doc"
    echo "    Cleanup: aws ssm delete-document --name $doc"
  done
  ERRORS=$((ERRORS + 1))
else
  echo "✅ No orphaned SSM documents"
fi
echo ""

# Check CloudFront OACs
echo "🌐 Checking CloudFront Origin Access Controls..."
OACS=$(aws cloudfront list-origin-access-controls \
  --query "OriginAccessControlList.Items[?contains(Name, '${PROJECT}') && contains(Name, '${ENV}')].{Name:Name,Id:Id}" \
  --output json 2>/dev/null || echo "[]")

if [ "$OACS" != "[]" ]; then
  echo "❌ Orphaned CloudFront OACs found:"
  echo "$OACS" | jq -r '.[] | "  - \(.Name) (ID: \(.Id))\n    Cleanup: aws cloudfront delete-origin-access-control --id \(.Id)"'
  ERRORS=$((ERRORS + 1))
else
  echo "✅ No orphaned CloudFront OACs"
fi
echo ""

# Summary
if [ $ERRORS -eq 0 ]; then
  echo "✅ All resources cleaned up for ${ENV} environment"
  exit 0
else
  echo "❌ Found $ERRORS categories of orphaned resources"
  echo ""
  echo "Run cleanup commands shown above, then re-run verification"
  exit 1
fi
