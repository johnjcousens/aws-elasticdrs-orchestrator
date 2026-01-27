# DRS Launch Settings - Static IP Preservation for Multi-Tenant Recovery

**Confluence Title**: DRS Launch Settings Analysis - Last Octet Preservation for Multi-Tenant DR  
**Description**: Comprehensive analysis of DRS launch configuration settings and implementation plan for automatic last octet preservation across different regional subnet CIDRs. Enables multi-tenant disaster recovery with consistent NAT mappings and IP addressing schemes for HRP Landing Zone architecture (10.230.x.x → 10.238.x.x). Includes complete DRS API settings reference, EC2 Launch Template integration, and HRP-specific IP allocation patterns.

**JIRA Ticket**: [AWSM-1115](https://healthedge.atlassian.net/browse/AWSM-1115)  
**Epic**: [AWSM-1112 - DRS Integration and EC2 Recovery](https://healthedge.atlassian.net/browse/AWSM-1112)  
**Document**: AWSM-1112 Launch Settings Enhancement  
**Date**: January 20, 2026  
**Status**: Implementation Ready  
**Purpose**: Enable automatic last octet preservation across different subnet CIDRs to support multi-tenant disaster recovery with consistent NAT mappings and IP addressing schemes

---

## Executive Summary

Your current DRS orchestration solution implements **Protection Groups** with `launchConfig` that applies settings to DRS source servers via `apply_launch_config_to_servers()`. This analysis identifies the gap between DRS `copyPrivateIp` (requires identical subnet CIDRs) and the HRP requirement for **last octet preservation across different regional /16 CIDRs** via EC2 Launch Template static IP assignment.

**Key Findings**:
- ✅ **Currently Implemented**: DRS `copyPrivateIp` and `licensing` settings
- ❌ **NOT Implemented**: EC2 Launch Template static IP assignment for last octet preservation
- 🎯 **Recommendation**: Add automatic static IP assignment to EC2 Launch Template when subnet specified

**Critical Distinction**:
- **DRS `copyPrivateIp=true`**: Copies exact IP (requires identical subnet CIDRs in both regions)
- **HRP Requirement**: Preserve last octet across different regional /16 CIDRs (requires EC2 Launch Template `PrivateIpAddress`)

**HRP Landing Zone Architecture** (per IP Addressing documentation):
- HrpVpnCustomerProduction: us-east-1 (10.230.0.0/16) → us-east-2 (10.238.0.0/16)
- HrpVpnCustomerNonProduction: us-east-1 (10.226.0.0/16) → us-east-2 (10.234.0.0/16)
- 256 customer VPCs per account per region
- Each VPC: 3 x /26 workload subnets spanning 3 AZs
- Palo Alto firewalls provide CGNAT translation (100.64.x.x → 10.238.x.x)

---

## Current Implementation Analysis

### Protection Group Schema (DynamoDB)

**Table**: `aws-elasticdrs-orchestrator-protection-groups-{env}`

**Current launchConfig Structure**:
```json
{
  "groupId": "pg-abc123",
  "groupName": "Production Web Servers",
  "launchConfig": {
    "instanceType": "t3.medium",
    "subnetId": "subnet-abc123",
    "securityGroupIds": ["sg-abc123", "sg-def456"],
    "instanceProfileName": "MyAppRole",
    "copyPrivateIp": false,
    "copyTags": true,
    "licensing": {"osByol": false},
    "targetInstanceTypeRightSizingMethod": "NONE",
    "launchDisposition": "STARTED"
  }
}
```

### Current apply_launch_config_to_servers() Implementation

**File**: `infra/orchestration/drs-orchestration/lambda/api-handler/index.py`

**What It Does**:
1. Gets DRS launch configuration for each server
2. Extracts EC2 launch template ID
3. **Updates DRS launch configuration FIRST** (critical order)
4. **Then updates EC2 launch template** (so changes stick)
5. Sets new template version as default

**Currently Supported Settings**:

| Setting | DRS API | EC2 Template | Status |
|---------|---------|--------------|--------|
| `instanceType` | ❌ | ✅ | Implemented |
| `subnetId` | ❌ | ✅ | Implemented |
| `securityGroupIds` | ❌ | ✅ | Implemented |
| `instanceProfileName` | ❌ | ✅ | Implemented |
| `copyPrivateIp` | ✅ | ❌ | ✅ **Implemented** (DRS setting) |
| `copyTags` | ✅ | ❌ | ✅ **Implemented** |
| `licensing` | ✅ | ❌ | ✅ **Implemented** |
| `targetInstanceTypeRightSizingMethod` | ✅ | ❌ | ✅ **Implemented** |
| `launchDisposition` | ✅ | ❌ | ✅ **Implemented** |
| **Static IP (EC2 Template)** | ❌ | ✅ | ❌ **NOT Implemented** |

**What's Missing**: EC2 Launch Template `NetworkInterfaces[0].PrivateIpAddress` for last octet preservation across different subnets.

---

## Complete DRS Launch Configuration Settings

### DRS API Settings (15 Total)

Based on AWS DRS API documentation and AWS Labs DRS Settings Tool:

#### 1. **copyPrivateIp** (Already Implemented - DRS Setting)
- **Type**: Boolean
- **Purpose**: Copy source server's exact private IP to recovery instance
- **Limitation**: Requires **identical subnet CIDRs** in both regions
- **Current Status**: ✅ **Implemented** (DRS API setting)
- **Use Case**: When source and DR subnets have identical CIDRs (e.g., both `10.0.1.0/24`)
- **HRP Note**: Not suitable for multi-tenancy (different subnet CIDRs per customer)

#### 2. **copyTags**
- **Type**: Boolean
- **Purpose**: Copy source server tags to recovery instance
- **Current Status**: ✅ Implemented
- **Default**: `true`

#### 3. **launchDisposition**
- **Type**: String (`STOPPED` | `STARTED`)
- **Purpose**: Control whether recovery instance starts automatically
- **Current Status**: ✅ Implemented
- **Default**: `STARTED`
- **Use Case**: `STOPPED` for validation before starting

#### 4. **launchIntoInstanceProperties**
- **Type**: Object `{launchIntoEC2InstanceID: string}`
- **Purpose**: **AllowLaunchingIntoThisInstance pattern** - launch into pre-provisioned instance
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **HIGH PRIORITY** - Enables 15-30 minute RTO (see AWSM-1112)

#### 5. **licensing** (Already Implemented)
- **Type**: Object `{osByol: boolean}`
- **Purpose**: Bring Your Own License for Windows/RHEL
- **Current Status**: ✅ **Implemented**
- **Default**: `{osByol: false}`

#### 6. **targetInstanceTypeRightSizingMethod**
- **Type**: String (`NONE` | `BASIC` | `IN_AWS`)
- **Purpose**: Instance type selection strategy
- **Current Status**: ✅ Implemented
- **Default**: `NONE`
- **Values**:
  - `NONE`: Use specified instance type
  - `BASIC`: DRS recommends based on source
  - `IN_AWS`: DRS optimizes for AWS

#### 7. **postLaunchActions** (NEW in DRS)
- **Type**: Object
- **Purpose**: SSM documents to run after recovery
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **MEDIUM PRIORITY** - Enables post-recovery automation

### EC2 Launch Template Settings

Settings managed via EC2 launch template (not DRS API):

#### 9. **InstanceType**
- **Current Status**: ✅ Implemented
- **Applied via**: EC2 `create_launch_template_version()`

#### 10. **SubnetId**
- **Current Status**: ✅ Implemented
- **Applied via**: EC2 `NetworkInterfaces[0].SubnetId`

#### 11. **SecurityGroupIds**
- **Current Status**: ✅ Implemented
- **Applied via**: EC2 `NetworkInterfaces[0].Groups`

#### 12. **IamInstanceProfile**
- **Current Status**: ✅ Implemented
- **Applied via**: EC2 `IamInstanceProfile.Name`

#### 13. **PrivateIpAddress** (CRITICAL - NOT Implemented)
- **Type**: String (IP address)
- **Purpose**: Assign static IP to preserve last octet across different subnets
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **HIGHEST PRIORITY** - Enables HRP multi-tenancy with NAT mapping
- **Applied via**: EC2 `NetworkInterfaces[0].PrivateIpAddress`
- **Use Case**: Preserve last octet when subnet CIDRs differ between regions

#### 14. **KeyName** (SSH Key Pair)
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **LOW PRIORITY** - Most customers use SSM Session Manager

#### 15. **UserData** (Startup Scripts)
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **MEDIUM PRIORITY** - Useful for post-recovery configuration
- **Note**: DRS may override this for recovery operations

#### 16. **BlockDeviceMappings** (EBS Volume Settings)
- **Current Status**: ❌ **NOT IMPLEMENTED**
- **Recommendation**: **LOW PRIORITY** - DRS manages volume mappings from source
- **Note**: DRS controls this for replication

---

## Static IP Implementation - HRP Multi-Tenancy

**Architecture Goal**: Preserve last octet across different regional /16 CIDRs for HealthEdge VPN customer workloads.

**Problem**: DRS `copyPrivateIp=true` requires identical subnet CIDRs, conflicting with Landing Zone regional IP allocation (us-east-1: 10.230.x.x → us-east-2: 10.238.x.x).

**Solution**: EC2 Launch Template `PrivateIpAddress` field preserves last octet across different regional /16 CIDRs.

### Multi-Tenant IP Preservation Architecture

**HRP VPN Customer Architecture** (HrpVpnCustomerProduction Account):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRIMARY REGION (us-east-1): 10.230.0.0/16               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Customer A VPC                          Customer B VPC                    │
│  ┌─────────────────────────────┐         ┌─────────────────────────────┐  │
│  │ Subnet: 10.230.1.0/26       │         │ Subnet: 10.230.64.0/26      │  │
│  │ ┌─────────────────────┐     │         │ ┌─────────────────────┐     │  │
│  │ │  Web Server         │     │         │ │  Web Server         │     │  │
│  │ │  IP: 10.230.1.100   │     │         │ │  IP: 10.230.64.100  │     │  │
│  │ │  Name: web-prod-01  │     │         │ │  Name: web-prod-01  │     │  │
│  │ └─────────────────────┘     │         │ └─────────────────────┘     │  │
│  └─────────────────────────────┘         └─────────────────────────────┘  │
│           │                                        │                        │
│           │ DRS Replication                        │ DRS Replication        │
│           ▼                                        ▼                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DR REGION (us-east-2): 10.238.0.0/16                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Customer A VPC                          Customer B VPC                    │
│  ┌─────────────────────────────┐         ┌─────────────────────────────┐  │
│  │ Subnet: 10.238.1.0/26       │         │ Subnet: 10.238.64.0/26      │  │
│  │ ┌─────────────────────┐     │         │ ┌─────────────────────┐     │  │
│  │ │  Recovery Instance  │     │         │ │  Recovery Instance  │     │  │
│  │ │  IP: 10.238.1.100 ✓ │     │         │ │  IP: 10.238.64.100 ✓│     │  │
│  │ │  Last Octet: .100   │     │         │ │  Last Octet: .100   │     │  │
│  │ │  Name: web-prod-01  │     │         │ │  Name: web-prod-01  │     │  │
│  │ └─────────────────────┘     │         │ └─────────────────────┘     │  │
│  └─────────────────────────────┘         └─────────────────────────────┘  │
│           │                                        │                        │
│           │ Palo Alto NAT                          │ Palo Alto NAT          │
│           │ 100.64.x.100 → 10.238.1.100           │ 100.64.y.100 → ...     │
│           ▼                                        ▼                        │
│    CGNAT: 100.64.x.100                     CGNAT: 100.64.y.100             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ACTUAL HRP IP ALLOCATION (per Landing Zone):
• HrpVpnCustomerProduction Account:
  - us-east-1: 10.230.0.0/16 → us-east-2: 10.238.0.0/16
  - Each customer VPC gets /26 workload subnets (62 usable IPs)
  - 256 customer VPCs supported per account per region
• Palo Alto firewalls provide NAT using RFC 6598 CGNAT space (100.64.0.0/10)
• Each customer allocated 2 x /24 CGNAT subnets

KEY BENEFITS:
✓ Different subnet CIDRs per customer VPC (multi-tenancy within account)
✓ Consistent last octet across regions for application compatibility
✓ Regional /16 CIDRs differ (10.230.x.x → 10.238.x.x) but last octet preserved
✓ Automatic - no manual IP assignment needed
```

### DRS copyPrivateIp vs EC2 Template Static IP

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    DRS copyPrivateIp=true (NOT SUITABLE)                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Source Region:      10.230.1.0/26  →  Server: 10.230.1.100             │
│  DR Region:          10.230.1.0/26  →  Server: 10.230.1.100 ✓           │
│                      ▲▲▲▲▲▲▲▲▲▲▲▲▲                                       │
│                      MUST BE IDENTICAL CIDR                              │
│                                                                          │
│  ❌ Breaks HRP architecture (regional /16 CIDRs differ)                  │
│  ❌ Requires 10.230.x.x in both us-east-1 AND us-east-2                  │
│  ❌ Conflicts with Landing Zone IP allocation scheme                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│              EC2 Launch Template PrivateIpAddress (SOLUTION)             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Source Region:      10.230.1.0/26  →  Server: 10.230.1.100             │
│  DR Region:          10.238.1.0/26  →  Server: 10.238.1.100 ✓           │
│                      ▲▲▲▲▲▲▲▲▲▲▲▲▲           Extract: .100               │
│                      DIFFERENT CIDR OK    Preserve: .100                 │
│                                                                          │
│  ✓ Aligns with Landing Zone regional /16 allocation                     │
│  ✓ us-east-1: 10.230.x.x → us-east-2: 10.238.x.x (last octet preserved) │
│  ✓ Supports 256 customer VPCs per account per region                    │
│  ✓ Works with Palo Alto CGNAT translation (100.64.x.100 → 10.238.1.100) │
│  ✓ Automatic - system calculates target IP from source                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

HRP REGIONAL IP ALLOCATION (Landing Zone):
• HrpVpnCustomerProduction:
  - us-east-1: 10.230.0.0/16 (primary)
  - us-east-2: 10.238.0.0/16 (DR)
• HrpVpnCustomerNonProduction:
  - us-east-1: 10.226.0.0/16 (primary)
  - us-east-2: 10.234.0.0/16 (DR)
```

### Implementation in `apply_launch_config_to_servers()`

**Modified Function Flow**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATIC STATIC IP WORKFLOW                         │
└─────────────────────────────────────────────────────────────────────────┘

User Action: Set subnetId in Protection Group launchConfig
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. GET TARGET SUBNET CIDR                                               │
│    ├─ Query EC2: describe_subnets(subnetId)                             │
│    └─ Extract: 10.1.5.0/24                                              │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. GET SOURCE SERVER IP (for each server)                               │
│    ├─ PRIMARY: DRS sourceProperties.networkInterfaces[0].ips[0]         │
│    │   └─ Result: 10.0.1.100 ✓                                          │
│    └─ FALLBACK: Resource Explorer (if DRS metadata unavailable)         │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. CALCULATE TARGET IP                                                  │
│    ├─ Extract last octet: .100                                          │
│    ├─ Extract subnet base: 10.1.5                                       │
│    └─ Build target IP: 10.1.5.100                                       │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. VALIDATE IP AVAILABILITY                                             │
│    ├─ Check: No existing ENI with this IP                               │
│    ├─ Check: IP within subnet CIDR range                                │
│    └─ Result: Available ✓                                               │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. UPDATE DRS CONFIGURATION                                             │
│    ├─ Set: copyPrivateIp = False (disable DRS IP management)            │
│    ├─ Set: copyTags, licensing, launchDisposition                       │
│    └─ API: update_launch_configuration()                                │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. UPDATE EC2 LAUNCH TEMPLATE                                           │
│    ├─ Set: NetworkInterfaces[0].PrivateIpAddress = 10.1.5.100           │
│    ├─ Set: NetworkInterfaces[0].SubnetId = subnet-dr-123                │
│    ├─ Set: NetworkInterfaces[0].Groups = [sg-dr-123]                    │
│    ├─ API: create_launch_template_version()                             │
│    └─ API: modify_launch_template(DefaultVersion="$Latest")             │
└─────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ RESULT: Recovery instance will launch with IP 10.1.5.100                │
│         Last octet preserved across different subnet CIDRs              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Modified Function Flow**:

```python
def apply_launch_config_to_servers(
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group_id: str = None,
    protection_group_name: str = None,
) -> Dict:
    """Apply launchConfig with automatic last octet preservation when subnet specified."""
    if not launch_config or not server_ids:
        return {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    regional_drs = boto3.client("drs", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)
    
    # Get target subnet CIDR for static IP calculation
    target_subnet_cidr = None
    if launch_config.get("subnetId"):
        subnet_response = ec2.describe_subnets(SubnetIds=[launch_config["subnetId"]])
        target_subnet_cidr = subnet_response['Subnets'][0]['CidrBlock']

    results = {"applied": 0, "skipped": 0, "failed": 0, "details": []}

    for server_id in server_ids:
        try:
            drs_config = regional_drs.get_launch_configuration(sourceServerID=server_id)
            template_id = drs_config.get("ec2LaunchTemplateID")

            if not template_id:
                results["skipped"] += 1
                results["details"].append({
                    "serverId": server_id,
                    "status": "skipped",
                    "reason": "No EC2 launch template found",
                })
                continue

            # Calculate static IP from source server IP + target subnet
            source_ip = None
            static_ip = None
            if target_subnet_cidr:
                source_ip = get_source_server_ip(server_id, region)
                if source_ip:
                    last_octet = source_ip.split('.')[-1]
                    subnet_base = '.'.join(target_subnet_cidr.split('.')[:3])
                    static_ip = f"{subnet_base}.{last_octet}"
                    
                    if not validate_ip_available(static_ip, launch_config["subnetId"], ec2):
                        print(f"Warning: IP {static_ip} not available, using DHCP")
                        static_ip = None

            # Build EC2 template data
            template_data = {}
            if launch_config.get("instanceType"):
                template_data["InstanceType"] = launch_config["instanceType"]

            # Network interface with static IP
            if launch_config.get("subnetId") or launch_config.get("securityGroupIds"):
                network_interface = {"DeviceIndex": 0}
                if launch_config.get("subnetId"):
                    network_interface["SubnetId"] = launch_config["subnetId"]
                if static_ip:
                    network_interface["PrivateIpAddress"] = static_ip
                if launch_config.get("securityGroupIds"):
                    network_interface["Groups"] = launch_config["securityGroupIds"]
                template_data["NetworkInterfaces"] = [network_interface]

            if launch_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {"Name": launch_config["instanceProfileName"]}

            # Update DRS configuration FIRST
            drs_update = {"sourceServerID": server_id}
            if static_ip:
                drs_update["copyPrivateIp"] = False  # Disable DRS IP management
            elif "copyPrivateIp" in launch_config:
                drs_update["copyPrivateIp"] = launch_config["copyPrivateIp"]
            
            if "copyTags" in launch_config:
                drs_update["copyTags"] = launch_config["copyTags"]
            if "licensing" in launch_config:
                drs_update["licensing"] = launch_config["licensing"]
            if "targetInstanceTypeRightSizingMethod" in launch_config:
                drs_update["targetInstanceTypeRightSizingMethod"] = launch_config["targetInstanceTypeRightSizingMethod"]
            if "launchDisposition" in launch_config:
                drs_update["launchDisposition"] = launch_config["launchDisposition"]

            if len(drs_update) > 1:
                regional_drs.update_launch_configuration(**drs_update)

            # THEN update EC2 launch template
            if template_data:
                from datetime import datetime
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                desc_parts = [f"DRS Orchestration | {timestamp}"]
                if protection_group_name:
                    desc_parts.append(f"PG: {protection_group_name}")
                if static_ip:
                    desc_parts.append(f"Static IP: {static_ip} (last octet from {source_ip})")
                version_desc = " | ".join(desc_parts)[:255]

                ec2.create_launch_template_version(
                    LaunchTemplateId=template_id,
                    LaunchTemplateData=template_data,
                    VersionDescription=version_desc,
                )
                ec2.modify_launch_template(LaunchTemplateId=template_id, DefaultVersion="$Latest")

            results["applied"] += 1
            results["details"].append({
                "serverId": server_id,
                "status": "applied",
                "templateId": template_id,
                "staticIp": static_ip,
                "sourceIp": source_ip,
            })

        except Exception as e:
            print(f"Error applying launchConfig to {server_id}: {e}")
            results["failed"] += 1
            results["details"].append({"serverId": server_id, "status": "failed", "error": str(e)})

    return results
```

**Helper Functions**:

```python
def get_source_server_ip(source_server_id: str, region: str) -> str:
    """Get source IP from DRS metadata (primary) or Resource Explorer (fallback)."""
    try:
        # PRIMARY: DRS source server metadata
        drs = boto3.client('drs', region_name=region)
        response = drs.describe_source_servers(filters={'sourceServerIDs': [source_server_id]})
        
        if response.get('items'):
            source_props = response['items'][0].get('sourceProperties', {})
            network_interfaces = source_props.get('networkInterfaces', [])
            if network_interfaces and network_interfaces[0].get('ips'):
                return network_interfaces[0]['ips'][0]
        
        # FALLBACK: Resource Explorer
        print(f"DRS metadata unavailable for {source_server_id}, trying Resource Explorer")
        resource_explorer = boto3.client('resource-explorer-2', region_name=region)
        response = resource_explorer.search(
            QueryString=f'tag:drs:sourceServerID:{source_server_id}',
            ViewArn=get_resource_explorer_view_arn(region)
        )
        
        for resource in response.get('Resources', []):
            if resource['ResourceType'] == 'ec2:instance':
                properties = resource.get('Properties', [])
                for prop in properties:
                    if prop['Name'] == 'PrivateIpAddress':
                        return prop['Data']['Value']
        return None
    except Exception as e:
        print(f"Error getting source IP for {source_server_id}: {e}")
        return None


def validate_ip_available(ip_address: str, subnet_id: str, ec2_client) -> bool:
    """Validate IP is available in target subnet."""
    try:
        response = ec2_client.describe_network_interfaces(
            Filters=[
                {'Name': 'private-ip-address', 'Values': [ip_address]},
                {'Name': 'subnet-id', 'Values': [subnet_id]}
            ]
        )
        if response['NetworkInterfaces']:
            return False
        
        subnet = ec2_client.describe_subnets(SubnetIds=[subnet_id])
        cidr = subnet['Subnets'][0]['CidrBlock']
        subnet_prefix = '.'.join(cidr.split('.')[:3])
        ip_prefix = '.'.join(ip_address.split('.')[:3])
        return subnet_prefix == ip_prefix
    except Exception as e:
        print(f"Error validating IP {ip_address}: {e}")
        return False
```

---

## Recommended Implementation Plan

### Phase 1: Implement Automatic Last Octet Preservation (1 week)

**Goal**: Add EC2 Launch Template static IP assignment to preserve last octet across different subnets

**User Experience**:
- User sets `subnetId` in Protection Group `launchConfig` via API, Lambda, or Frontend
- User clicks Save (or calls API endpoint)
- System automatically preserves last octet for all servers using EC2 Launch Template
- No additional UI fields needed

**What's Being Added**:
- EC2 Launch Template `NetworkInterfaces[0].PrivateIpAddress` assignment
- Automatic last octet extraction from DRS source server metadata
- IP availability validation in target subnet
- DRS `copyPrivateIp=False` when static IP assigned (disable DRS IP management)

**Access Methods**:
1. **API Gateway**: `POST /protection-groups` or `PUT /protection-groups/{groupId}`
2. **Direct Lambda Invocation**: Invoke `api-handler` Lambda with orchestration role
3. **Frontend**: Protection Group form (existing UI)

**Changes Required**:

1. **Backend - Update `apply_launch_config_to_servers()`** (`lambda/api-handler/index.py`):
   - Add `get_source_server_ip()` function to query DRS metadata (primary) or Resource Explorer (fallback)
   - Add `validate_ip_available()` function to check IP availability
   - Add `get_resource_explorer_view_arn()` helper function
   - Modify network interface logic to include `PrivateIpAddress` when subnet specified
   - Set DRS `copyPrivateIp=False` when static IP assigned
   - Add static IP details to version description

2. **API Endpoints** (already exist, no changes needed):
   - `POST /protection-groups` - Create Protection Group with launchConfig
   - `PUT /protection-groups/{groupId}` - Update Protection Group launchConfig
   - Both endpoints call `apply_launch_config_to_servers()` automatically

3. **Direct Lambda Invocation** (already supported):
   ```python
   # Invoke from orchestration Lambda or Step Functions
   lambda_client = boto3.client('lambda')
   response = lambda_client.invoke(
       FunctionName='api-handler',
       InvocationType='RequestResponse',
       Payload=json.dumps({
           'httpMethod': 'POST',
           'path': '/protection-groups',
           'body': json.dumps({
               'groupName': 'Production Servers',
               'launchConfig': {
                   'subnetId': 'subnet-dr-123',
                   'securityGroupIds': ['sg-dr-123']
               },
               'servers': ['s-123', 's-124']
           })
       })
   )
   ```

4. **Configuration - Resource Explorer View ARN**:
   - Add Resource Explorer view ARN to environment variables or DynamoDB config
   - Ensure Resource Explorer is indexing source region EC2 instances (fallback only)
   - DRS metadata is primary source (no additional setup needed)

5. **Testing**:
   - Unit tests for IP extraction and validation
   - Integration test with DRS metadata and Resource Explorer fallback
   - End-to-end test via API, Lambda invocation, and Frontend

**No Frontend Changes Required** - completely transparent to users across all access methods.

---

### Phase 2: Add UI Toggle for Manual Control (Optional - 2 days)

**Goal**: Allow users to disable automatic last octet preservation if needed

**Access Methods**:
1. **API Gateway**: Include `preserveLastOctet` field in launchConfig
2. **Direct Lambda Invocation**: Include `preserveLastOctet` in payload
3. **Frontend**: Add toggle to Protection Group form

**Changes Required**:

1. **Frontend - Protection Group Form** (`frontend/src/components/ProtectionGroupForm.tsx`):
```typescript
// Add optional toggle to disable automatic last octet preservation
<FormField 
  label="Preserve Last Octet" 
  description="Automatically preserve source IP last octet in recovery subnet"
>
  <Toggle
    checked={launchConfig.preserveLastOctet !== false}  // Default true
    onChange={({detail}) => 
      setLaunchConfig({...launchConfig, preserveLastOctet: detail.checked})
    }
  />
</FormField>

<FormField label="Launch Disposition" description="Start instance after recovery">
  <Select
    selectedOption={{value: launchConfig.launchDisposition || 'STARTED'}}
    onChange={({detail}) => 
      setLaunchConfig({...launchConfig, launchDisposition: detail.selectedOption.value})
    }
    options={[
      {value: 'STARTED', label: 'Started - Auto-start after recovery'},
      {value: 'STOPPED', label: 'Stopped - Manual start required'}
    ]}
  />
</FormField>

<FormField label="Right Sizing Method" description="Instance type selection">
  <Select
    selectedOption={{value: launchConfig.targetInstanceTypeRightSizingMethod || 'NONE'}}
    onChange={({detail}) => 
      setLaunchConfig({...launchConfig, targetInstanceTypeRightSizingMethod: detail.selectedOption.value})
    }
    options={[
      {value: 'NONE', label: 'None - Use specified instance type'},
      {value: 'BASIC', label: 'Basic - DRS recommends based on source'},
      {value: 'IN_AWS', label: 'In AWS - DRS optimizes for AWS'}
    ]}
  />
</FormField>
```

2. **Backend - Check `preserveLastOctet` flag** (`lambda/api-handler/index.py`):
```python
# In apply_launch_config_to_servers()
# Only apply static IP if preserveLastOctet is not explicitly disabled
if target_subnet_cidr and launch_config.get("preserveLastOctet", True):
    source_ip = get_source_server_ip(server_id, region)
    # ... rest of static IP logic
```

3. **API Example** (all access methods):
```json
POST /protection-groups
{
  "groupName": "Production Servers",
  "launchConfig": {
    "subnetId": "subnet-dr-123",
    "securityGroupIds": ["sg-dr-123"],
    "preserveLastOctet": true  // Optional, defaults to true
  },
  "servers": ["s-123", "s-124"]
}
```

**Default Behavior**: Automatic last octet preservation enabled by default across all access methods (API, Lambda, Frontend).

---

### Phase 3: Add Missing DRS Settings (2 weeks)

### Phase 3: Add Missing DRS Settings (2 weeks)

**Goal**: Implement `launchIntoInstanceProperties` (AllowLaunchingIntoThisInstance)

**Access Methods**: API, Direct Lambda Invocation, Frontend (all supported)

**Changes Required**:

1. **Protection Group Schema Extension**:
```json
POST /protection-groups
{
  "groupName": "Production Servers",
  "launchConfig": {
    "subnetId": "subnet-dr-123",
    "launchIntoInstanceProperties": {
      "launchIntoEC2InstanceID": "i-0abc123def456"
    }
  },
  "servers": ["s-123"]
}
```

2. **Name Tag Matching Logic** (from AWSM-1112):
```python
def match_target_instances(
    source_servers: List[Dict],
    target_region: str,
    target_subnet_id: str
) -> Dict[str, str]:
    """Match source servers to target instances by Name tag"""
    ec2 = boto3.client('ec2', region_name=target_region)
    
    # Get stopped instances in target subnet with AWSDRS tag
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'subnet-id', 'Values': [target_subnet_id]},
            {'Name': 'instance-state-name', 'Values': ['stopped']},
            {'Name': 'tag:AWSDRS', 'Values': ['AllowLaunchingIntoThisInstance']}
        ]
    )
    
    # Build lookup by Name tag
    target_instances = {}
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = next((t['Value'] for t in instance.get('Tags', []) 
                        if t['Key'] == 'Name'), None)
            if name:
                target_instances[name.lower().strip()] = instance['InstanceId']
    
    # Match source servers to targets
    matches = {}
    for server in source_servers:
        source_name = server.get('sourceProperties', {}).get(
            'identificationHints', {}).get('hostname', '')
        
        if source_name:
            normalized = source_name.lower().strip()
            target_id = target_instances.get(normalized)
            if target_id:
                matches[server['sourceServerID']] = target_id
    
    return matches
```

3. **Update apply_launch_config_to_servers()**:
```python
# Add launchIntoInstanceProperties support
if "launchIntoInstanceProperties" in launch_config:
    launch_into = launch_config["launchIntoInstanceProperties"]
    
    # Validate target instance
    target_instance_id = launch_into.get("launchIntoEC2InstanceID")
    if target_instance_id:
        # Verify instance exists and is stopped
        ec2_response = ec2.describe_instances(InstanceIds=[target_instance_id])
        instance = ec2_response['Reservations'][0]['Instances'][0]
        
        if instance['State']['Name'] != 'stopped':
            raise ValueError(f"Target instance must be stopped: {target_instance_id}")
        
        # Verify AWSDRS tag
        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
        if tags.get('AWSDRS') != 'AllowLaunchingIntoThisInstance':
            raise ValueError(f"Missing AWSDRS tag: {target_instance_id}")
        
        # Configure DRS
        drs_update["launchIntoInstanceProperties"] = launch_into
```

**Testing**:
- Create pre-provisioned instances in DR region
- Tag with `AWSDRS=AllowLaunchingIntoThisInstance`
- Configure Protection Group via API, Lambda, or Frontend
- Test recovery into pre-provisioned instances

---

### Phase 4: Add Nice-to-Have Settings (1 week)

**Goal**: Implement `postLaunchActions`, `keyName`, `userData`

**Access Methods**: API, Direct Lambda Invocation, Frontend (all supported)

**Changes Required**:

1. **postLaunchActions** (SSM Documents):
```json
POST /protection-groups
{
  "groupName": "Production Servers",
  "launchConfig": {
    "subnetId": "subnet-dr-123",
    "postLaunchActions": {
      "ssmDocuments": [
        {
          "actionName": "ConfigureApp",
          "ssmDocumentName": "AWS-ConfigureAWSPackage",
          "parameters": {
            "action": ["Install"],
            "name": ["MyApp"]
          },
          "mustSucceedForCutover": true,
          "timeoutSeconds": 300
        }
      ]
    }
  }
}
```

2. **KeyName** (SSH Key Pair):
```python
# In EC2 template data
if launch_config.get("keyName"):
    template_data["KeyName"] = launch_config["keyName"]
```

3. **UserData** (Startup Scripts):
```python
# In EC2 template data
if launch_config.get("userData"):
    import base64
    template_data["UserData"] = base64.b64encode(
        launch_config["userData"].encode()
    ).decode()
```

---

## Complete launchConfig Schema

### Recommended Final Schema

```typescript
interface LaunchConfig {
  // EC2 Launch Template Settings
  instanceType?: string;              // e.g., "t3.medium"
  subnetId?: string;                  // e.g., "subnet-abc123"
  securityGroupIds?: string[];        // e.g., ["sg-abc123"]
  instanceProfileName?: string;       // e.g., "MyAppRole"
  keyName?: string;                   // e.g., "my-key-pair"
  userData?: string;                  // Base64-encoded startup script
  
  // DRS Launch Configuration Settings
  copyPrivateIp?: boolean;            // Preserve source IP last octet
  copyTags?: boolean;                 // Copy source tags to recovery
  launchDisposition?: 'STARTED' | 'STOPPED';  // Auto-start behavior
  targetInstanceTypeRightSizingMethod?: 'NONE' | 'BASIC' | 'IN_AWS';
  
  // Licensing
  licensing?: {
    osByol?: boolean;                 // Bring Your Own License
  };
  
  // AllowLaunchingIntoThisInstance
  launchIntoInstanceProperties?: {
    launchIntoEC2InstanceID?: string; // Pre-provisioned instance ID
  };
  
  // Post-Launch Automation
  postLaunchActions?: {
    ssmDocuments?: Array<{
      actionName: string;
      ssmDocumentName: string;
      parameters?: Record<string, string[]>;
      mustSucceedForCutover?: boolean;
      timeoutSeconds?: number;
    }>;
  };
}
```

---

## Implementation Priority Matrix

| Setting | Priority | Effort | Business Value | RTO Impact |
|---------|----------|--------|----------------|------------|
| EC2 Template Static IP (last octet) | 🔥 **CRITICAL** | Medium (1 week) | **Very High** | Enables multi-tenancy |
| `launchIntoInstanceProperties` | 🔥 **CRITICAL** | High (2 weeks) | **Very High** | **95% reduction** |
| `postLaunchActions` | ⚠️ **HIGH** | Medium (1 week) | Medium | Low |
| `keyName` | ✅ **MEDIUM** | Low (1 day) | Low | None |
| `userData` | ✅ **MEDIUM** | Low (1 day) | Medium | Low |
| `blockDeviceMappings` | ⏸️ **LOW** | High (1 week) | Low | None |

**Note**: DRS `copyPrivateIp` and `licensing` are already implemented and working.

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_launch_config_static_ip.py

def test_get_source_server_ip_from_resource_explorer():
    """Test retrieving source IP from Resource Explorer"""
    source_ip = get_source_server_ip("s-123", "us-east-1")
    assert source_ip is not None
    assert len(source_ip.split('.')) == 4  # Valid IP format

def test_validate_ip_available():
    """Test IP availability validation"""
    ec2 = boto3.client('ec2', region_name='us-east-2')
    
    # Test available IP
    assert validate_ip_available("10.1.5.100", "subnet-abc123", ec2) == True
    
    # Test unavailable IP (already in use)
    assert validate_ip_available("10.1.5.1", "subnet-abc123", ec2) == False

def test_apply_launch_config_with_automatic_static_ip():
    """Test automatic last octet preservation when subnet specified"""
    launch_config = {
        "subnetId": "subnet-abc123",  # CIDR: 10.1.5.0/24
        "securityGroupIds": ["sg-abc123"]
    }
    
    # Mock source server with IP 10.0.1.100
    with mock.patch('get_source_server_ip', return_value='10.0.1.100'):
        result = apply_launch_config_to_servers(
            server_ids=["s-123"],
            launch_config=launch_config,
            region="us-east-2"
        )
    
    assert result["applied"] == 1
    assert result["details"][0]["staticIp"] == "10.1.5.100"  # Last octet preserved
    assert result["details"][0]["sourceIp"] == "10.0.1.100"

def test_apply_launch_config_without_subnet():
    """Test that static IP is not applied when subnet not specified"""
    launch_config = {
        "instanceType": "t3.medium"
    }
    
    result = apply_launch_config_to_servers(
        server_ids=["s-123"],
        launch_config=launch_config,
        region="us-east-2"
    )
    
    assert result["applied"] == 1
    assert result["details"][0].get("staticIp") is None

def test_apply_launch_config_with_preserve_last_octet_disabled():
    """Test that static IP is not applied when preserveLastOctet=false"""
    launch_config = {
        "subnetId": "subnet-abc123",
        "preserveLastOctet": False
    }
    
    result = apply_launch_config_to_servers(
        server_ids=["s-123"],
        launch_config=launch_config,
        region="us-east-2"
    )
    
    assert result["applied"] == 1
    assert result["details"][0].get("staticIp") is None
```

### Integration Tests

```python
# tests/integration/test_static_ip_recovery.py

def test_static_ip_preservation_end_to_end():
    """Test complete static IP preservation workflow"""
    # 1. Create Protection Group with subnet
    pg = create_protection_group({
        "groupName": "Static IP Test",
        "launchConfig": {
            "subnetId": "subnet-dr-123",  # DR subnet
            "securityGroupIds": ["sg-dr-123"]
        },
        "servers": ["s-123"]  # Source server with IP 10.0.1.100
    })
    
    # 2. Verify launch template updated with static IP
    drs = boto3.client('drs', region_name='us-east-2')
    config = drs.get_launch_configuration(sourceServerID='s-123')
    template_id = config['ec2LaunchTemplateID']
    
    ec2 = boto3.client('ec2', region_name='us-east-2')
    template = ec2.describe_launch_template_versions(
        LaunchTemplateId=template_id,
        Versions=['$Latest']
    )
    
    network_interfaces = template['LaunchTemplateVersions'][0]['LaunchTemplateData']['NetworkInterfaces']
    assert network_interfaces[0]['PrivateIpAddress'] == '10.1.5.100'  # Last octet preserved
    
    # 3. Verify DRS copyPrivateIp disabled
    assert config['copyPrivateIp'] == False
    
    # 4. Start recovery and verify IP
    execution = start_recovery(pg["groupId"])
    wait_for_execution(execution["executionId"])
    
    recovery_instance = get_recovery_instance('s-123')
    assert recovery_instance['PrivateIpAddress'] == '10.1.5.100'

def test_multiple_servers_different_last_octets():
    """Test that each server gets its own last octet preserved"""
    pg = create_protection_group({
        "groupName": "Multi-Server Static IP Test",
        "launchConfig": {
            "subnetId": "subnet-dr-123"  # Same subnet for all
        },
        "servers": [
            "s-100",  # Source IP: 10.0.1.100
            "s-101",  # Source IP: 10.0.1.101
            "s-102"   # Source IP: 10.0.1.102
        ]
    })
    
    # Verify each server has correct static IP
    for server_id, expected_last_octet in [("s-100", "100"), ("s-101", "101"), ("s-102", "102")]:
        config = drs.get_launch_configuration(sourceServerID=server_id)
        template_id = config['ec2LaunchTemplateID']
        
        template = ec2.describe_launch_template_versions(
            LaunchTemplateId=template_id,
            Versions=['$Latest']
        )
        
        network_interfaces = template['LaunchTemplateVersions'][0]['LaunchTemplateData']['NetworkInterfaces']
        static_ip = network_interfaces[0]['PrivateIpAddress']
        
        assert static_ip == f'10.1.5.{expected_last_octet}'
```

---

## Migration Path for Existing Protection Groups

### Backward Compatibility

**Existing Protection Groups** (without new settings):
- Continue to work with current behavior
- No breaking changes
- New settings are **optional**

**Migration Script** (optional):
```python
def migrate_protection_groups_to_new_schema():
    """Add default values for new settings to existing PGs"""
    table = dynamodb.Table('protection-groups')
    
    response = table.scan()
    for item in response['Items']:
        if 'launchConfig' in item:
            launch_config = item['launchConfig']
            
            # Add defaults for new settings
            if 'copyPrivateIp' not in launch_config:
                launch_config['copyPrivateIp'] = False
            
            if 'launchDisposition' not in launch_config:
                launch_config['launchDisposition'] = 'STARTED'
            
            if 'targetInstanceTypeRightSizingMethod' not in launch_config:
                launch_config['targetInstanceTypeRightSizingMethod'] = 'NONE'
            
            # Update item
            table.update_item(
                Key={'groupId': item['groupId']},
                UpdateExpression='SET launchConfig = :lc',
                ExpressionAttributeValues={':lc': launch_config}
            )
```

---

## Documentation Updates Required

1. **API Documentation**:
   - Update `/protection-groups` POST/PUT endpoints with new `launchConfig` fields
   - Add examples for static IP preservation
   - Document AllowLaunchingIntoThisInstance pattern

2. **User Guide**:
   - "How to Enable Static IP Preservation"
   - "How to Use Pre-Provisioned Instances"
   - "Subnet CIDR Alignment Requirements"

3. **Architecture Documentation**:
   - Update `dr-orchestration-architecture.md` with launch settings
   - Add static IP preservation to design patterns

---

## Success Metrics

### Phase 1 (Automatic Last Octet Preservation via EC2 Template)
- ✅ EC2 Launch Template static IP automatically assigned when Protection Group subnet specified
- ✅ Last octet preserved for all servers in Protection Group across different subnets
- ✅ No UI changes required - completely seamless
- ✅ DRS metadata used as primary source (Resource Explorer as fallback)
- ✅ DRS `copyPrivateIp` automatically disabled when EC2 template static IP used
- ✅ Multi-tenancy enabled with different subnet CIDRs per customer

### Phase 2 (Optional Manual Control)
- ✅ `preserveLastOctet` toggle available in UI
- ✅ Default behavior: automatic preservation enabled
- ✅ Users can disable if needed for specific use cases

### Phase 3 (AllowLaunchingIntoThisInstance)
- ✅ `launchIntoInstanceProperties` implemented
- ✅ Name tag matching working
- ✅ RTO reduced from 2-4 hours to 15-30 minutes (95% improvement)

### Phase 4 (Nice-to-Have Settings)
- ✅ `postLaunchActions` implemented
- ✅ `keyName` and `userData` supported
- ✅ Complete DRS launch configuration coverage

---

## Implementation Summary

**Seamless User Experience**:
1. User creates Protection Group
2. User sets `subnetId` in `launchConfig` (e.g., `subnet-dr-123` with CIDR `10.238.1.0/26`)
3. User adds servers to Protection Group
4. User clicks Save
5. **System automatically**:
   - Queries DRS metadata for each source server's IP (primary source)
   - Falls back to Resource Explorer if DRS metadata unavailable
   - Extracts last octet (e.g., `.100` from `10.230.1.100`)
   - Builds target IP using subnet CIDR + last octet (e.g., `10.238.1.100`)
   - Validates IP availability
   - Updates EC2 launch template with static IP
   - Sets DRS `copyPrivateIp=False`
6. Recovery instances launch with preserved last octet

**HRP Multi-Tenancy Support** (per Landing Zone):
- HrpVpnCustomerProduction Account:
  - Primary (us-east-1): 10.230.0.0/16 → DR (us-east-2): 10.238.0.0/16
  - Customer A: Source `10.230.1.100` → Recovery `10.238.1.100` (subnet `10.238.1.0/26`)
  - Customer B: Source `10.230.64.100` → Recovery `10.238.64.100` (subnet `10.238.64.0/26`)
- HrpVpnCustomerNonProduction Account:
  - Primary (us-east-1): 10.226.0.0/16 → DR (us-east-2): 10.234.0.0/16
- Palo Alto NAT: CGNAT `100.64.x.100` → `10.238.1.100` (consistent last octet)
- 256 customer VPCs supported per account per region
- Each VPC: 3 x /26 workload subnets spanning 3 AZs (62 usable IPs per subnet)

**No Additional Configuration Required** - works automatically when subnet specified.

---

**Last Updated**: January 20, 2026  
**Status**: Analysis Complete - Ready for Implementation  
**Next Steps**: Begin Phase 1 (Automatic Last Octet Preservation)
