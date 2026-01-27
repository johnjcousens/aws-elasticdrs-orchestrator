#!/bin/bash
# Update Protection Groups to use complete HealthEdge-compliant tag filters
# Includes all relevant tags applied to source instances

set -e

REGION="us-east-1"
TABLE_NAME="aws-drs-orchestration-protection-groups-dev"

echo "Updating Protection Groups with complete tag filters..."
echo ""

# Protection Group 1: Database Servers
# All tags: BusinessUnit, ResourceType, Service, Application, Customer, MonitoringLevel, dr:enabled, dr:recovery-strategy, dr:priority, dr:wave
echo "1. Updating DatabaseServersGroup with complete tags..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "30dce7f9-d1e1-42b5-a4fd-802068716217"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "BusinessUnit": {"S": "HRP"},
        "ResourceType": {"S": "Database"},
        "Service": {"S": "DatabaseServer"},
        "Application": {"S": "HRP-Core-Platform"},
        "Customer": {"S": "CustomerA"},
        "MonitoringLevel": {"S": "Critical"},
        "dr:enabled": {"S": "true"},
        "dr:recovery-strategy": {"S": "drs"},
        "dr:priority": {"S": "critical"},
        "dr:wave": {"S": "1"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

# Protection Group 2: Application Servers
echo ""
echo "2. Updating AppServersGroup with complete tags..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "c3448299-00e0-4a23-a359-20195a043230"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "BusinessUnit": {"S": "HRP"},
        "ResourceType": {"S": "Compute"},
        "Service": {"S": "ApplicationServer"},
        "Application": {"S": "HRP-Core-Platform"},
        "Customer": {"S": "CustomerA"},
        "MonitoringLevel": {"S": "Standard"},
        "dr:enabled": {"S": "true"},
        "dr:recovery-strategy": {"S": "drs"},
        "dr:priority": {"S": "high"},
        "dr:wave": {"S": "2"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

# Protection Group 3: Web Servers
echo ""
echo "3. Updating WebServersGroup with complete tags..."
aws dynamodb update-item \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --key '{"groupId": {"S": "e27cf78d-fb75-49c0-ba7b-8b588ea42a21"}}' \
  --update-expression "SET serverSelectionTags = :tags, version = version + :inc, lastModifiedDate = :timestamp" \
  --expression-attribute-values '{
    ":tags": {
      "M": {
        "BusinessUnit": {"S": "HRP"},
        "ResourceType": {"S": "Compute"},
        "Service": {"S": "WebServer"},
        "Application": {"S": "HRP-Core-Platform"},
        "Customer": {"S": "CustomerA"},
        "MonitoringLevel": {"S": "Standard"},
        "dr:enabled": {"S": "true"},
        "dr:recovery-strategy": {"S": "drs"},
        "dr:priority": {"S": "medium"},
        "dr:wave": {"S": "3"}
      }
    },
    ":inc": {"N": "1"},
    ":timestamp": {"N": "'"$(date +%s)"'"}
  }' \
  --return-values UPDATED_NEW

echo ""
echo "✓ Protection Groups updated with complete tag filters"
echo ""
echo "Tag Filters Applied:"
echo ""
echo "DatabaseServersGroup:"
echo "  BusinessUnit=HRP, ResourceType=Database, Service=DatabaseServer"
echo "  Application=HRP-Core-Platform, Customer=CustomerA, MonitoringLevel=Critical"
echo "  dr:enabled=true, dr:recovery-strategy=drs, dr:priority=critical, dr:wave=1"
echo ""
echo "AppServersGroup:"
echo "  BusinessUnit=HRP, ResourceType=Compute, Service=ApplicationServer"
echo "  Application=HRP-Core-Platform, Customer=CustomerA, MonitoringLevel=Standard"
echo "  dr:enabled=true, dr:recovery-strategy=drs, dr:priority=high, dr:wave=2"
echo ""
echo "WebServersGroup:"
echo "  BusinessUnit=HRP, ResourceType=Compute, Service=WebServer"
echo "  Application=HRP-Core-Platform, Customer=CustomerA, MonitoringLevel=Standard"
echo "  dr:enabled=true, dr:recovery-strategy=drs, dr:priority=medium, dr:wave=3"
echo ""
echo "Verify updates:"
aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --projection-expression "groupName,serverSelectionTags" \
  --output json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['Items']:
    print(f\"\n{item['groupName']['S']}:\")
    tags = item['serverSelectionTags']['M']
    for key in sorted(tags.keys()):
        print(f\"  {key}: {tags[key]['S']}\")
"
