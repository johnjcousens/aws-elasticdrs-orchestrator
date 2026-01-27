#!/bin/bash
# Update Protection Groups to use HealthEdge-compliant tag filters
# Replaces legacy "Purpose" tag with proper Service tag filtering

set -e

REGION="us-east-1"
TABLE_NAME="aws-drs-orchestration-protection-groups-dev"

echo "Updating Protection Groups to use HealthEdge-compliant tags..."
echo ""

# Protection Group 1: Database Servers
# Old: Purpose=DatabaseServers
# New: Service=DatabaseServer, BusinessUnit=HRP, dr:wave=1
echo "1. Updating DatabaseServersGroup..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "30dce7f9-d1e1-42b5-a4fd-802068716217"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "Service": {"S": "DatabaseServer"},
        "BusinessUnit": {"S": "HRP"},
        "dr:wave": {"S": "1"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

# Protection Group 2: Application Servers
# Old: Purpose=AppServers
# New: Service=ApplicationServer, BusinessUnit=HRP, dr:wave=2
echo ""
echo "2. Updating AppServersGroup..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "c3448299-00e0-4a23-a359-20195a043230"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "Service": {"S": "ApplicationServer"},
        "BusinessUnit": {"S": "HRP"},
        "dr:wave": {"S": "2"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

# Protection Group 3: Web Servers
# Old: Purpose=WebServers
# New: Service=WebServer, BusinessUnit=HRP, dr:wave=3
echo ""
echo "3. Updating WebServersGroup..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "e27cf78d-fb75-49c0-ba7b-8b588ea42a21"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "Service": {"S": "WebServer"},
        "BusinessUnit": {"S": "HRP"},
        "dr:wave": {"S": "3"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

echo ""
echo "✓ Protection Groups updated successfully"
echo ""
echo "Tag Filter Updates:"
echo "  DatabaseServersGroup: Service=DatabaseServer, BusinessUnit=HRP, dr:wave=1"
echo "  AppServersGroup:      Service=ApplicationServer, BusinessUnit=HRP, dr:wave=2"
echo "  WebServersGroup:      Service=WebServer, BusinessUnit=HRP, dr:wave=3"
echo ""
echo "Verify updates:"
aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --projection-expression "groupName,serverSelectionTags" \
  --output table
