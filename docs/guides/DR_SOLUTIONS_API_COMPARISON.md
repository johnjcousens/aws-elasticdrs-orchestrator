# Disaster Recovery Solutions API Comparison Guide

**Version**: 1.0  
**Last Updated**: November 23, 2025  
**Purpose**: Comprehensive API comparison for DR platform evaluation and implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Architecture Comparison](#api-architecture-comparison)
4. [Core API Categories](#core-api-categories)
5. [Integration Capabilities](#integration-capabilities)
6. [Gap Analysis & Implementation Roadmap](#gap-analysis--implementation-roadmap)
7. [Developer Handoff Guide](#developer-handoff-guide)

---

# Executive Summary

## Overview

This document provides a comprehensive comparison of REST APIs across four major disaster recovery platforms:

- **Azure Site Recovery (ASR)** - Microsoft's native Azure DR solution
- **Zerto** - Multi-cloud DR and data protection platform
- **VMware Site Recovery Manager (SRM)** - VMware-native DR solution
- **AWS DRS Orchestration** - Serverless orchestration layer on AWS DRS

## Quick Reference Matrix

| Category | Azure ASR | Zerto | VMware SRM | AWS DRS Orch | Winner |
|----------|-----------|-------|------------|--------------|--------|
| **API Maturity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Azure ASR |
| **Ease of Integration** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | AWS DRS |
| **Documentation Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Azure/Zerto |
| **SDK Availability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Azure ASR |
| **Webhook Support** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | Zerto |
| **Performance** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Zerto/AWS |
| **Cost Efficiency** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | AWS DRS |

## Authentication Complexity Rating

| Platform | Complexity | Setup Time | Learning Curve |
|----------|------------|------------|----------------|
| **Azure ASR** | Medium | 2-4 hours | Moderate |
| **Zerto** | Low-Medium | 1-2 hours | Easy |
| **VMware SRM** | High | 4-8 hours | Steep |
| **AWS DRS Orch** | Low | 1-2 hours | Easy |

## API Coverage Comparison

### Protection Management
- ✅ Azure ASR: Comprehensive ARM-based protection APIs
- ✅ Zerto: VPG (Virtual Protection Group) APIs
- ⚠️ VMware SRM: Limited, relies on vSphere integration
- ⚠️ AWS DRS Orch: Custom implementation required (DynamoDB-backed)

### Recovery Orchestration
- ✅ Azure ASR: Recovery Plans with runbook integration
- ✅ Zerto: Built-in orchestration with priorities
- ✅ VMware SRM: Recovery Plans with vRO workflows
- ⚠️ AWS DRS Orch: Step Functions-based custom orchestration

### Monitoring & Status
- ✅ Azure ASR: Comprehensive job tracking and reporting
- ✅ Zerto: Real-time monitoring with detailed metrics
- ⚠️ VMware SRM: Basic job status, limited details
- ✅ AWS DRS Orch: Real-time job monitoring via DRS APIs

### Advanced Features
- ✅ Azure ASR: Multi-VM consistency, network remapping, automated runbooks
- ✅ Zerto: Journal-based recovery, automated failback, cloud migration
- ⚠️ VMware SRM: Placeholder VMs, basic customization
- ⚠️ AWS DRS Orch: SSM post-launch actions, basic automation

## Recommended Use Cases by Platform

### Azure Site Recovery APIs
**Best For:**
- Azure-native workloads
- Organizations heavily invested in Azure ecosystem
- Complex automation requirements with Azure Automation
- Enterprise compliance and reporting needs

**API Strengths:**
- Comprehensive ARM REST APIs
- Deep Azure service integration
- Extensive PowerShell/CLI support
- Strong compliance and audit capabilities

### Zerto APIs
**Best For:**
- Multi-cloud DR strategies
- Near-zero RPO/RTO requirements
- Organizations requiring cross-platform DR
- Cloud migration projects

**API Strengths:**
- RESTful design with excellent documentation
- Real-time replication monitoring
- Webhook notifications for automation
- Comprehensive VPG management

### VMware SRM APIs
**Best For:**
- VMware-centric organizations
- On-premises to on-premises DR
- Organizations with vSphere expertise
- Traditional datacenter environments

**API Limitations:**
- Mixed SOAP/REST architecture
- Limited modern integration capabilities
- Requires vSphere authentication complexity
- Minimal webhook/event support

### AWS DRS Orchestration APIs
**Best For:**
- AWS-native workloads
- Serverless architecture preferences
- Cost-conscious implementations
- Developer-friendly integrations

**API Strengths:**
- Modern REST design
- Serverless, scalable architecture
- Native AWS service integration
- Pay-per-use pricing model

**API Gaps:**
- No native protection group APIs
- No built-in recovery plan management
- Limited multi-VM consistency
- Custom orchestration required

## Key Decision Factors

### Choose Azure ASR If:
- ✅ Primary cloud is Azure
- ✅ Need comprehensive out-of-box APIs
- ✅ Require enterprise-grade compliance reporting
- ✅ Have Azure expertise on team

### Choose Zerto If:
- ✅ Multi-cloud strategy required
- ✅ Near-zero RPO is critical
- ✅ Need advanced replication features
- ✅ Want commercial support and SLAs

### Choose VMware SRM If:
- ✅ Committed to VMware ecosystem
- ✅ On-premises DR is primary use case
- ✅ Already have vSphere infrastructure
- ✅ Limited cloud integration needed

### Choose AWS DRS Orchestration If:
- ✅ AWS-first or AWS-only strategy
- ✅ Want serverless, zero-infrastructure approach
- ✅ Cost optimization is priority
- ✅ Developer team prefers modern APIs
- ✅ Willing to build custom orchestration

---

# Authentication & Authorization

## Azure Site Recovery Authentication

### Authentication Method
**Azure Active Directory (AAD) + ARM Tokens**

```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.recoveryservices import RecoveryServicesClient

# Authenticate using Azure AD
credential = DefaultAzureCredential()

# Initialize client
client = RecoveryServicesClient(
    credential=credential,
    subscription_id='your-subscription-id'
)
```

### Token Management
- **Token Type**: OAuth 2.0 Bearer tokens
- **Token Lifetime**: 1 hour (default)
- **Refresh Strategy**: Automatic via Azure SDK
- **Scopes**: Specific ARM resource scopes

### Authorization Model
**Azure RBAC (Role-Based Access Control)**

Common roles for DR operations:
- `Site Recovery Contributor`: Full access to ASR operations
- `Site Recovery Operator`: Can execute failovers, no config changes
- `Site Recovery Reader`: Read-only access

```json
{
  "roleDefinitionId": "/subscriptions/{sub-id}/providers/Microsoft.Authorization/roleDefinitions/6670b86e-a3f7-4917-ac9b-5d6ab1be4567",
  "roleName": "Site Recovery Contributor",
  "scope": "/subscriptions/{sub-id}/resourceGroups/{rg-name}"
}
```

### API Request Example
```http
POST https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.RecoveryServices/vaults/{vaultName}/replicationProtectedItems/{protectedItemName}/failover?api-version=2022-10-01
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "properties": {
    "failoverDirection": "PrimaryToRecovery",
    "providerSpecificDetails": {
      "instanceType": "A2A"
    }
  }
}
```

---

## Zerto Authentication

### Authentication Methods

**1. Session-Based Authentication** (Legacy)
```http
POST https://zvm.example.com:9669/v1/session/add
Content-Type: application/json
Authorization: Basic {base64(username:password)}

Response:
{
  "x-zerto-session": "token-value"
}
```

**2. API Key Authentication** (Recommended)
```http
GET https://zvm.example.com:9669/v1/vpgs
x-zerto-session: {api-key}
```

### Token Management
- **Session Token**: Valid for 30 minutes (configurable)
- **API Key**: Long-lived, rotatable
- **Renewal**: Automatic if using Zerto SDK

### Authorization Model
**Role-Based with Custom Permissions**

Available roles:
- **Administrator**: Full access
- **Site Administrator**: Manage specific sites
- **Operator**: Execute recovery operations
- **Read Only**: View-only access

### API Request Example
```python
import requests

# Authenticate
session = requests.post(
    'https://zvm.example.com:9669/v1/session/add',
    auth=('username', 'password'),
    verify=False
)

token = session.headers['x-zerto-session']

# Use token for API calls
vpgs = requests.get(
    'https://zvm.example.com:9669/v1/vpgs',
    headers={'x-zerto-session': token},
    verify=False
)
```

---

## VMware SRM Authentication

### Authentication Method
**vSphere Single Sign-On (SSO)**

```python
from pyVim.connect import SmartConnect
from suds.client import Client

# Connect to vCenter
si = SmartConnect(
    host='vcenter.example.com',
    user='administrator@vsphere.local',
    pwd='password'
)

# Create SRM SOAP client
srm_client = Client(
    'https://srm.example.com:9085/srm-service?wsdl',
    username='administrator@vsphere.local',
    password='password'
)
```

### Token Management
- **Session Token**: vSphere session token
- **Token Lifetime**: 30 minutes (idle timeout)
- **Renewal**: Manual renewal required

### Authorization Model
**vSphere Permissions + SRM Roles**

SRM-specific roles:
- `SRM Administrator`: Full SRM access
- `SRM Site Administrator`: Single site management
- `SRM Recovery Manager`: Execute recoveries only

### API Request Example (REST)
```http
POST https://srm.example.com:9087/api/recovery-plans/rp-1/recovery
Authorization: Bearer {vsphere-session-token}
Content-Type: application/json

{
  "recoveryMode": "Test",
  "syncData": true
}
```

---

## AWS DRS Orchestration Authentication

### Authentication Method
**AWS Cognito + IAM Roles**

```python
import boto3
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

# DRS API authentication using IAM
drs_client = boto3.client(
    'drs',
    region_name='us-east-1',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY'
)

# Custom Orchestration API authentication using Cognito
auth = BotoAWSRequestsAuth(
    aws_host='api.example.com',
    aws_region='us-east-1',
    aws_service='execute-api'
)

import requests
response = requests.get(
    'https://api.example.com/recovery-plans',
    auth=auth
)
```

### Token Management
- **Cognito Tokens**: ID token, access token, refresh token
- **ID Token Lifetime**: 1 hour
- **Refresh Token Lifetime**: 30 days (configurable)
- **Auto-Refresh**: Handled by AWS SDK

### Authorization Model
**IAM Roles + Custom API Policies**

IAM policies for DRS operations:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:StartRecovery",
        "drs:DescribeJobs",
        "drs:TerminateRecoveryInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

### API Request Example
```python
# DRS native API
response = drs_client.start_recovery(
    sourceServers=[
        {
            'sourceServerID': 's-1234567890abcdef0'
        }
    ],
    isDrill=True
)

# Custom Orchestration API
import requests
response = requests.post(
    'https://api.example.com/recovery-plans/plan-123/execute',
    headers={
        'Authorization': f'Bearer {cognito_id_token}'
    },
    json={
        'isDrill': True,
        'waves': ['wave-1', 'wave-2']
    }
)
```

### Cognito Integration
```javascript
// Frontend Cognito authentication
import { Amplify, Auth } from 'aws-amplify';

Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_XXXXXXXXX',
    userPoolWebClientId: 'xxxxxxxxxxxxxxxxxxxx'
  }
});

// Sign in
const user = await Auth.signIn(username, password);
const token = user.signInUserSession.idToken.jwtToken;

// Use token for API calls
const response = await fetch('/api/recovery-plans', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## Authentication Comparison Summary

| Feature | Azure ASR | Zerto | VMware SRM | AWS DRS Orch |
|---------|-----------|-------|------------|--------------|
| **Auth Type** | OAuth 2.0 | Session/API Key | SSO | Cognito + IAM |
| **Token Format** | JWT | Custom | vSphere session | JWT |
| **Token Lifetime** | 1 hour | 30 min | 30 min | 1 hour |
| **Auto-Refresh** | ✅ Yes | ⚠️ Manual | ❌ No | ✅ Yes |
| **MFA Support** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **API Key Support** | ⚠️ Service Principal | ✅ Yes | ❌ No | ✅ Yes (IAM) |
| **RBAC** | ✅ Comprehensive | ✅ Yes | ✅ Yes | ✅ Comprehensive |
| **Federation** | ✅ AAD, SAML | ✅ SAML, LDAP | ✅ AD, LDAP | ✅ SAML, OIDC |

### Setup Complexity Ranking
1. **Easiest**: AWS DRS Orchestration (Cognito user pools, IAM roles)
2. **Easy**: Zerto (Simple API key or session auth)
3. **Moderate**: Azure ASR (AAD app registration, RBAC setup)
4. **Complex**: VMware SRM (vSphere SSO, permission mapping)

---

# API Architecture Comparison

## REST vs SOAP Architecture

### Azure Site Recovery
**Architecture**: Pure REST (ARM-based)

**Request Format**:
```http
GET https://management.azure.com/subscriptions/{subscriptionId}/providers/Microsoft.RecoveryServices/vaults?api-version=2022-10-01
```

**Response Format**: JSON
```json
{
  "value": [
    {
      "id": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.RecoveryServices/vaults/vault1",
      "name": "vault1",
      "type": "Microsoft.RecoveryServices/vaults",
      "location": "eastus",
      "properties": {}
    }
  ]
}
```

**Characteristics**:
- ✅ Consistent ARM API patterns
- ✅ Standard HTTP verbs (GET, POST, PUT, DELETE, PATCH)
- ✅ JSON request/response
- ✅ Hypermedia links (HAL)
- ✅ ETags for optimistic concurrency

---

### Zerto
**Architecture**: RESTful with custom conventions

**Request Format**:
```http
GET https://zvm.example.com:9669/v1/vpgs
x-zerto-session: {token}
```

**Response Format**: JSON
```json
{
  "VpgName": "WebApp-VPG",
  "VpgIdentifier": "guid-12345",
  "SourceSite": "site1",
  "TargetSite": "site2",
  "Priority": "High",
  "Status": "Meeting SLA"
}
```

**Characteristics**:
- ✅ Clean RESTful design
- ✅ JSON only
- ✅ Custom headers for authentication
- ✅ Hypermedia links
- ⚠️ Some non-standard conventions

---

### VMware SRM
**Architecture**: Hybrid SOAP/REST

**SOAP Request Format**:
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <GetRecoveryPlan>
      <recoveryPlanId>rp-1</recoveryPlanId>
    </GetRecoveryPlan>
  </soapenv:Body>
</soapenv:Envelope>
```

**REST Request Format** (newer APIs):
```http
GET https://srm.example.com:9087/api/recovery-plans/rp-1
```

**Characteristics**:
- ⚠️ Mixed SOAP/REST architecture
- ⚠️ XML for SOAP, JSON for REST
- ❌ Inconsistent API patterns
- ⚠️ Legacy SOAP for core operations

---

### AWS DRS Orchestration
**Architecture**: RESTful + AWS SDK patterns

**DRS API Request Format**:
```python
# AWS SDK pattern
response = drs_client.describe_source_servers(
    filters={'sourceServerIDs': ['s-123']}
)
```

**Custom REST API Format**:
```http
GET https://api.example.com/protection-groups/pg-123
Authorization: Bearer {token}
```

**Response Format**: JSON
```json
{
  "protectionGroupId": "pg-123",
  "name": "WebServers",
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "web-01"
    }
  ]
}
```

**Characteristics**:
- ✅ RESTful design for custom APIs
- ✅ JSON request/response
- ✅ Standard HTTP verbs
- ✅ AWS SDK for DRS native APIs
- ✅ Consistent error handling

---

## Error Handling Patterns

### Azure ASR Error Response
```json
{
  "error": {
    "code": "InvalidParameterValue",
    "message": "The parameter resourceGroup is invalid",
    "target": "resourceGroup",
    "details": [
      {
        "code": "NullOrEmpty",
        "message": "Resource group cannot be null or empty"
      }
    ]
  }
}
```

**HTTP Status Codes**:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

---

### Zerto Error Response
```json
{
  "Message": "VPG not found",
  "ErrorCode": "VPG_NOT_FOUND",
  "Details": "The specified VPG identifier does not exist"
}
```

**HTTP Status Codes**:
- 200: Success
- 400: Invalid request
- 401: Unauthorized
- 404: Resource not found
- 500: Server error

---

### VMware SRM Error Response (SOAP)
```xml
<soapenv:Fault>
  <faultcode>Server</faultcode>
  <faultstring>Recovery plan not found</faultstring>
  <detail>
    <RecoveryPlanFault>
      <recoveryPlanId>rp-invalid</recoveryPlanId>
    </RecoveryPlanFault>
  </detail>
</soapenv:Fault>
```

---

### AWS DRS Error Response
```json
{
  "__type": "ValidationException",
  "message": "1 validation error detected: Value null at 'sourceServerID' failed to satisfy constraint: Member must not be null"
}
```

**HTTP Status Codes**:
- 200: Success
- 400: ValidationException
- 403: AccessDeniedException
- 404: ResourceNotFoundException
- 429: ThrottlingException
- 500: InternalServerException

---

## Pagination Patterns

### Azure ASR
```json
{
  "value": [...],
  "nextLink": "https://management.azure.com/subscriptions/{sub}/providers/Microsoft.RecoveryServices/vaults?api-version=2022-10-01&$skiptoken=token123"
}
```

**Pattern**: Link-based pagination
```python
results = []
next_link = initial_url

while next_link:
    response = requests.get(next_link)
    results.extend(response.json()['value'])
    next_link = response.json().get('nextLink')
```

---

### Zerto
```http
GET /v1/vpgs?pageNumber=1&pageSize=50
```

**Pattern**: Page number and size
```python
page = 1
page_size = 50

while True:
    response = requests.get(
        f'/v1/vpgs?pageNumber={page}&pageSize={page_size}'
    )
    vpgs = response.json()
    
    if len(vpgs) < page_size:
        break
    page += 1
```

---

### VMware SRM
**Limited Pagination**: Most APIs return full result sets

---

### AWS DRS
```json
{
  "items": [...],
  "nextToken": "eyJsYXN0RXZhbHVhdGVkS2V5Ijp7fX0="
}
```

**Pattern**: Token-based pagination
```python
results = []
next_token = None

while True:
    params = {'maxResults': 200}
    if next_token:
        params['nextToken'] = next_token
        
    response = drs_client.describe_source_servers(**params)
    results.extend(response['items'])
    
    next_token = response.get('nextToken')
    if not next_token:
        break
```

---

## Rate Limiting

| Platform | Rate Limit | Retry Strategy | Burst Handling |
|----------|------------|----------------|----------------|
| **Azure ASR** | 12,000 reads/hr<br>1,200 writes/hr | Exponential backoff | Token bucket |
| **Zerto** | Varies by ZVM<br>~100 req/sec | Custom retry | Rate limiting headers |
| **VMware SRM** | No documented limits | None | N/A |
| **AWS DRS** | 10 req/sec (describe)<br>2 req/sec (launch) | AWS SDK retry | Exponential backoff |

### Rate Limit Headers

**Azure ASR**:
```http
x-ms-ratelimit-remaining-subscription-reads: 11999
x-ms-ratelimit-remaining-subscription-writes: 1199
Retry-After: 60
```

**Zerto**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

**AWS DRS**:
```json
{
  "__type": "ThrottlingException",
  "message": "Rate exceeded"
}
```

---

# Core API Categories

## 1. Protection Management APIs

### Azure Site Recovery

**Enable Protection (Create Protected Item)**
```http
PUT https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.RecoveryServices/vaults/{vaultName}/replicationFabrics/{fabricName}/replicationProtectionContainers/{protectionContainerName}/replicationProtectedItems/{protectedItemName}?api-version=2022-10-01

{
  "properties": {
    "policyId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.RecoveryServices/vaults/{vault}/replicationPolicies/policy1",
    "providerSpecificDetails": {
      "instanceType": "A2A",
      "fabricObjectId": "vm-id",
      "recoveryResourceGroupId": "/subscriptions/{sub}/resourceGroups/recovery-rg",
      "recoveryCloudServiceId": "/subscriptions/{sub}/resourceGroups/recovery-rg/providers/Microsoft.Compute/cloudServices/recovery-cs",
      "recoveryAvailabilitySetId": "/subscriptions/{sub}/resourceGroups/recovery-rg/providers/Microsoft.Compute/availabilitySets/recovery-as",
      "vmDisks": [
        {
          "diskId": "disk-id-1",
          "primaryStagingStorageAccountId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Storage/storageAccounts/cache-account",
          "recoveryResourceGroupId": "/subscriptions/{sub}/resourceGroups/recovery-rg",
          "recoveryReplicaDiskAccountType": "Premium_LRS",
          "recoveryTargetDiskAccountType": "Premium_LRS"
        }
      ]
    }
  }
}
```

**List Protected Items**
```http
GET https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.RecoveryServices/vaults/{vaultName}/replicationProtectedItems?api-version=2022-10-01
```

---

### Zerto

**Create VPG (Virtual Protection Group)**
```http
POST https://zvm.example.com:9669/v1/vpgs
x-zerto-session: {token}
Content-Type: application/json

{
  "VpgName": "WebApp-VPG",
  "Priority": "High",
  "RpoInSeconds": 300,
  "JournalHistoryInHours": 24,
  "SourceSite": "site-1",
  "TargetSite": "site-2",
  "Vms": [
    {
      "VmIdentifier": "vm-001",
      "Nics": [
        {
          "IpConfig": {
            "StaticIp": "10.0.2.100",
            "SubnetMask": "255.255.255.0",
            "Gateway": "10.0.2.1"
          }
        }
      ]
    }
  ]
}
```

**List VPGs**
```http
GET https://zvm.example.com:9669/v1/vpgs
x-zerto-session: {token}
```

---

### VMware SRM

**Create Protection Group (SOAP)**
```xml
<soapenv:Envelope>
  <soapenv:Body>
    <CreateProtectionGroup>
      <protectionGroupName>WebServers-PG</protectionGroupName>
      <inputSpec>
        <type>san</type>
        <datastoreGroups>
          <datastores>ds-001</datastores>
        </datastoreGroups>
      </inputSpec>
    </CreateProtectionGroup>
  </soapenv:Body>
</soapenv:Envelope>
```

**List Protection Groups (REST)**
```http
GET https://srm.example.com:9087/api/protection-groups
Authorization: Bearer {token}
```

---

### AWS DRS Orchestration

**Create Protection Group (Custom API)**
```http
POST https://api.example.com/protection-groups
Authorization: Bearer {cognito-token}
Content-Type: application/json

{
  "name": "WebServers",
  "description": "Web tier servers",
  "sourceServerIds": [
    "s-1234567890abcdef0",
    "s-1234567890abcdef1"
  ],
  "tags": {
    "Environment": "Production",
    "Application": "WebApp"
  }
}
```

**Implementation (DynamoDB + DRS Tags)**
```python
def create_protection_group(name, server_ids):
    """Create protection group with DynamoDB storage"""
    
    # Generate unique ID
    pg_id = str(uuid.uuid4())
    
    # Store in DynamoDB
    dynamodb.put_item(
        TableName='ProtectionGroups',
        Item={
            'ProtectionGroupId': pg_id,
            'Name': name,
            'SourceServerIds': server_ids,
            'CreatedAt': datetime.now().isoformat()
        }
    )
    
    # Tag DRS servers
    for server_id in server_ids:
        drs_client.tag_resource(
            resourceArn=f'arn:aws:drs:region:account:source-server/{server_id}',
            tags={'ProtectionGroup': name}
        )
    
    return {'protectionGroupId': pg_id, 'name': name}
```

**List Protection Groups**
```http
GET https://api.example.com/protection-groups
Authorization: Bearer {cognito-token}
```

---

## 2. Recovery Orchestration APIs

### Azure Site Recovery

**Create Recovery Plan**
```http
PUT https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.RecoveryServices/vaults/{vaultName}/replicationRecoveryPlans/{recoveryPlanName}?api-version=2022-10-01

{
  "properties": {
    "primaryFabricId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.RecoveryServices/vaults/{vault}/replicationFabrics/fabric1",
    "primaryFabricFriendlyName": "Primary Site",
    "recoveryFabricId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.RecoveryServices/vaults/{vault}/replicationFabrics/fabric2",
    "recoveryFabricFriendlyName": "Recovery Site",
    "groups": [
      {
        "groupType": "Shutdown",
        "replicationProtectedItems": [],
        "startGroupActions": [],
        "endGroupActions": []
      },
      {
        "groupType": "Boot",
        "replicationProtectedItems": [
          {
            "id": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.RecoveryServices/vaults/{vault}/replicationProtectedItems/item1"
          }
        ],
        "startGroupActions": [
          {
            "actionName": "pre-boot-action",
            "failoverTypes": ["Test", "Planned", "Unplanned"],
            "failoverDirections": ["PrimaryToRecovery"],
            "customDetails": {
              "instanceType": "AutomationRunbookActionDetails",
              "runbookId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Automation/automationAccounts/account1/runbooks/runbook1",
              "timeout": "PT30M"
            }
          }
        ],
        "endGroupActions": []
      },
      {
        "groupType": "Commit",
        "replicationProtectedItems": [],
        "startGroupActions": [],
        "endGroupActions": []
      }
    ]
  }
}
```

---

### Zerto (VPGs serve as recovery plans)

VPGs inherently include orchestration logic through priority settings.

**Get VPG Recovery Order**
```http
GET https://zvm.example.com:9669/v1/vpgs/{vpg-id}
x-zerto-session: {token}
```

Response includes boot order and timing.

---

### VMware SRM

**Create Recovery Plan**
```http
POST https://srm.example.com:9087/api/recovery-plans
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "WebApp-Recovery",
  "description": "Production web application recovery",
  "protectionGroups": [
    {
      "protectionGroupId": "pg-001",
      "priority": 1
    },
    {
      "protectionGroupId": "pg-002",
      "priority": 2
    }
  ]
}
```

---

### AWS DRS Orchestration

**Create Recovery Plan (Custom)**
```http
POST https://api.example.com/recovery-plans
Authorization: Bearer {cognito-token}
Content-Type: application/json

{
  "name": "Production-DR-Plan",
  "description": "Multi-wave production recovery",
  "protectionGroupIds": ["pg-123", "pg-456"],
  "waves": [
    {
      "name": "Wave 1 - Database Tier",
      "order": 1,
      "servers": ["s-db01", "s-db02"],
      "waitTimeSeconds": 300
    },
    {
      "name": "Wave 2 - Application Tier",
      "order": 2,
      "servers": ["s-app01", "s-app02"],
      "waitTimeSeconds": 180
    },
    {
      "name": "Wave 3 - Web Tier",
      "order": 3,
      "servers": ["s-web01", "s-web02"],
      "waitTimeSeconds": 60
    }
  ]
}
```

**Implementation with Step Functions**
```python
def create_recovery_plan_state_machine(plan):
    """Generate Step Functions state machine for recovery plan"""
    
    states = {}
    current_state = "Wave_1"
    
    for i, wave in enumerate(plan['waves'], 1):
        wave_name = f"Wave_{i}"
        
        # Wave execution state
        states[wave_name] = {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "drs-orchestration-lambda",
                "Payload": {
                    "action": "execute_wave",
                    "wave": wave,
                    "plan_id": plan['planId']
                }
            },
            "Next": f"Wait_{i}" if i < len(plan['waves']) else "Success"
        }
        
        # Wait state between waves
        if i < len(plan['waves']):
            states[f"Wait_{i}"] = {
                "Type": "Wait",
                "Seconds": wave['waitTimeSeconds'],
                "Next": f"Wave_{i+1}"
            }
    
    states["Success"] = {"Type": "Succeed"}
    
    return {
        "Comment": f"Recovery Plan: {plan['name']}",
        "StartAt": "Wave_1",
        "States": states
    }
```

---

# Gap Analysis & Implementation Roadmap

## Critical API Gaps in AWS DRS Orchestration

### Gap 1: Native Protection Group Management
**Current State**: Custom DynamoDB implementation with DRS tagging  
**Competitor State**: All have native protection group APIs  
**Impact**: HIGH - Fundamental DR concept missing  
**User Experience**: Requires custom code, no out-of-box functionality

**Implementation Recommendation**:
```python
# Proposed Protection Group API Layer
class ProtectionGroupAPI:
    """REST API wrapper for DynamoDB-backed protection groups"""
    
    def create(self, name, server_ids, tags=None):
        """Create protection group with validation"""
        # Validate servers exist and are not in other PGs
        # Store in DynamoDB with metadata
        # Tag DRS servers atomically
        pass
    
    def list(self, filters=None):
        """List protection groups with filtering"""
        # Query DynamoDB with optional filters
        # Join with live DRS server data
        pass
    
    def get(self, pg_id):
        """Get detailed protection group info"""
        # Retrieve from DynamoDB
        # Enrich with live DRS replication status
        pass
    
    def update(self, pg_id, updates):
        """Update protection group configuration"""
        # Update DynamoDB
        # Update DRS tags if needed
        pass
    
    def delete(self, pg_id):
        """Delete protection group"""
        # Remove DRS tags
        # Delete from DynamoDB
        pass
```

**Timeline**: 1-2 months  
**Effort**: Medium  
**Priority**: HIGH

---

### Gap 2: Built-in Recovery Plan Orchestration
**Current State**: Step Functions-based custom orchestration  
**Competitor State**: Native recovery plan APIs with runbooks  
**Impact**: HIGH - Core DR functionality  
**User Experience**: Complex setup, requires AWS expertise

**Implementation Recommendation**:
```python
# Proposed Recovery Plan API
class RecoveryPlanAPI:
    """Serverless recovery plan management"""
    
    def create(self, plan_config):
        """Create recovery plan with Step Functions"""
        # Validate wave dependencies
        # Generate State Machine definition
        # Create Step Functions workflow
        # Store metadata in DynamoDB
        pass
    
    def execute(self, plan_id, is_drill=False):
        """Execute recovery plan"""
        # Start Step Functions execution
        # Monitor progress via EventBridge
        # Update execution history
        pass
    
    def get_execution_status(self, execution_id):
        """Get real-time execution status"""
        # Query Step Functions
        # Aggregate wave status
        # Return detailed progress
        pass
```

**Timeline**: 2-3 months  
**Effort**: High  
**Priority**: HIGH

---

### Gap 3: Multi-VM Application Consistency
**Current State**: Individual server recovery only  
**Competitor State**: Application-aware consistency groups  
**Impact**: MEDIUM - RPO may be inconsistent  
**User Experience**: Manual coordination required

**Implementation Recommendation**:
```python
# Proposed Consistency Group Feature
def create_consistency_group(server_ids, snapshot_frequency=300):
    """Coordinate point-in-time snapshots"""
    
    # Leverage DRS PIT policy
    pit_policy = {
        "interval": snapshot_frequency,
        "retentionDuration": 60,
        "units": "MINUTE",
        "enabled": True
    }
    
    # Update all servers with identical policy
    for server_id in server_ids:
        drs_client.update_replication_configuration(
            sourceServerID=server_id,
            pitPolicy=[pit_policy]
        )
    
    # Store consistency group metadata
    dynamodb.put_item(
        TableName='ConsistencyGroups',
        Item={
            'GroupId': str(uuid.uuid4()),
            'ServerIds': server_ids,
            'SnapshotFrequency': snapshot_frequency
        }
    )
```

**Timeline**: 1-2 months  
**Effort**: Medium  
**Priority**: MEDIUM

---

### Gap 4: Advanced Network Configuration APIs
**Current State**: Manual launch template configuration  
**Competitor State**: Automated network remapping  
**Impact**: MEDIUM - Manual effort for network changes  
**User Experience**: Requires AWS networking knowledge

**Implementation Recommendation**:
```python
# Proposed Network Mapping API
class NetworkMappingAPI:
    """Automatic network configuration for recovery"""
    
    def create_mapping(self, mapping_config):
        """Create network mapping rule"""
        return {
            'mappingId': str(uuid.uuid4()),
            'sourceSubnet': mapping_config['sourceSubnet'],
            'targetSubnet': mapping_config['targetSubnet'],
            'ipAssignmentMode': 'DHCP',  # or 'STATIC'
            'staticIpPool': mapping_config.get('ipPool', [])
        }
    
    def apply_to_server(self, server_id, mapping_id):
        """Apply network mapping to server launch config"""
        mapping = self.get_mapping(mapping_id)
        
        # Update DRS launch configuration
        drs_client.update_launch_configuration(
            sourceServerID=server_id,
            copyPrivateIp=False,  # Use new IP
            # Additional network config...
        )
```

**Timeline**: 2-3 months  
**Effort**: High  
**Priority**: MEDIUM

---

### Gap 5: Compliance & Reporting APIs
**Current State**: Custom DynamoDB queries  
**Competitor State**: Built-in compliance reports  
**Impact**: MEDIUM - Audit requirements  
**User Experience**: Manual report generation

**Implementation Recommendation**:
```python
# Proposed Compliance Reporting API
class ComplianceReportingAPI:
    """Automated DR compliance tracking"""
    
    def generate_rpo_rto_report(self, date_range):
        """Generate RPO/RTO compliance report"""
        executions = self.query_executions(date_range)
        
        return {
            'reportPeriod': date_range,
            'totalTests': len(executions),
            'successfulTests': len([e for e in executions if e['status'] == 'SUCCESS']),
            'averageRTO': self.calculate_avg_rto(executions),
            'rpoCompliance': self.check_rpo_compliance(executions),
            'recommendations': self.generate_recommendations(executions)
        }
    
    def schedule_automated_tests(self, schedule):
        """Schedule automated DR tests"""
        # Create EventBridge rule
        # Trigger recovery plan execution
        # Store test results
        pass
```

**Timeline**: 1-2 months  
**Effort**: Medium  
**Priority**: MEDIUM

---

### Gap 6: Cross-Region Orchestration
**Current State**: Not implemented  
**Competitor State**: Multi-region failover support  
**Impact**: HIGH - Geographic DR scenarios  
**User Experience**: Cannot orchestrate cross-region DR

**Implementation Recommendation**:
```python
# Proposed Cross-Region Orchestration
class CrossRegionOrchestration:
    """Multi-region DR coordination"""
    
    def create_multi_region_plan(self, config):
        """Create plan spanning multiple regions"""
        return {
            'planId': str(uuid.uuid4()),
            'regions': [
                {
                    'region': 'us-east-1',
                    'role': 'primary',
                    'servers': config['primary_servers']
                },
                {
                    'region': 'us-west-2',
                    'role': 'recovery',
                    'servers': config['recovery_servers']
                }
            ],
            'failoverStrategy': 'active-passive'
        }
    
    def execute_cross_region_failover(self, plan_id):
        """Coordinate failover across regions"""
        # Get plan configuration
        # Start recovery in target region
        # Monitor via CloudWatch cross-region
        # Update Route53 if needed
        pass
```

**Timeline**: 3-4 months  
**Effort**: High  
**Priority**: HIGH

---

## Implementation Priority Matrix

| Gap | Business Impact | Technical Complexity | Development Time | Priority Score |
|-----|-----------------|---------------------|------------------|----------------|
| Protection Group APIs | HIGH | Medium | 1-2 months | **9/10** |
| Recovery Plan APIs | HIGH | High | 2-3 months | **9/10** |
| Cross-Region Orchestration | HIGH | High | 3-4 months | **8/10** |
| Network Mapping APIs | MEDIUM | High | 2-3 months | **6/10** |
| Multi-VM Consistency | MEDIUM | Medium | 1-2 months | **7/10** |
| Compliance Reporting | MEDIUM | Medium | 1-2 months | **6/10** |

---

## Recommended Implementation Phases

### Phase 1: Foundation (Months 1-3)
**Goal**: Establish parity with core competitor features

**Deliverables**:
1. **Protection Group REST API** (Month 1-2)
   - DynamoDB-backed storage
   - Full CRUD operations
   - Server assignment validation
   - Integration with DRS tags

2. **Multi-VM Consistency** (Month 2-3)
   - Coordinated PIT snapshots
   - Consistency group management
   - Application-aware recovery

3. **Basic Compliance Reporting** (Month 3)
   - Execution history tracking
   - RPO/RTO calculation
   - Simple report generation

**Success Criteria**:
- Protection groups fully functional
- Multi-VM recovery validated
- Basic compliance reports available

---

### Phase 2: Advanced Orchestration (Months 4-6)
**Goal**: Match competitor orchestration capabilities

**Deliverables**:
1. **Recovery Plan API** (Month 4-5)
   - Wave-based orchestration
   - Dependency management
   - Step Functions integration
   - Execution monitoring

2. **Network Mapping APIs** (Month 5-6)
   - Automated IP assignment
   - Subnet mapping rules
   - Security group configuration
   - Launch template generation

3. **Enhanced Monitoring** (Month 6)
   - Real-time status WebSockets
   - Granular progress tracking
   - Alert integration

**Success Criteria**:
- Complex recovery plans executable
- Network configuration automated
- Real-time monitoring working

---

### Phase 3: Enterprise Features (Months 7-12)
**Goal**: Differentiate with cloud-native capabilities

**Deliverables**:
1. **Cross-Region Orchestration** (Month 7-9)
   - Multi-region plan management
   - Cross-region failover
   - Global health monitoring

2. **Advanced Automation** (Month 9-11)
   - Visual workflow designer
   - Custom action marketplace
   - Template library

3. **AI-Driven Optimization** (Month 11-12)
   - Predictive RTO analysis
   - Auto resource sizing
   - Failure pattern detection

**Success Criteria**:
- Geographic DR functional
- Advanced automation in place
- AI features demonstrated

---

# Developer Handoff Guide

## Quick Start for New Developers

### Prerequisites
- AWS Account with appropriate permissions
- Node.js 18+ and Python 3.9+
- AWS CLI configured
- Git access to repository

### Local Development Setup

1. **Clone Repository**
```bash
git clone git@ssh.code.aws.dev:personal_projects/alias_j/jocousen/AWS-DRS-Orchestration.git
cd AWS-DRS-Orchestration
```

2. **Install Dependencies**
```bash
# Frontend
cd frontend
npm install

# Lambda
cd ../lambda
pip install -r requirements.txt -t package/
```

3. **Configure Environment**
```bash
# Copy environment template
cp .env.example .env.test

# Edit with your AWS account details
# Required: AWS_ACCOUNT_ID, AWS_REGION, COGNITO_USER_POOL_ID
```

4. **Deploy Infrastructure**
```bash
# Deploy CloudFormation stacks
make deploy-all

# Or deploy individually
make deploy-security
make deploy-database
make deploy-lambda
make deploy-api
make deploy-frontend
```

---

## Key Architecture Components

### 1. Frontend (React + TypeScript + MUI)
- **Location**: `frontend/src/`
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **State Management**: React Context
- **Authentication**: AWS Amplify + Cognito

**Key Files**:
- `src/services/drsService.ts` - DRS API wrapper
- `src/services/orchestrationService.ts` - Custom API client
- `src/contexts/AuthContext.tsx` - Authentication state
- `src/pages/` - Page components

### 2. Backend (Lambda + Python)
- **Location**: `lambda/`
- **Runtime**: Python 3.9
- **Framework**: boto3 for AWS SDK
- **Storage**: DynamoDB for metadata

**Key Files**:
- `index.py` - Main Lambda handler
- `build_and_deploy.py` - Deployment script

### 3. Infrastructure (CloudFormation)
- **Location**: `cfn/`
- **IaC Tool**: CloudFormation YAML

**Stack Files**:
- `master-template.yaml` - Root stack
- `security-stack.yaml` - IAM roles, Cognito
- `database-stack.yaml` - DynamoDB tables
- `lambda-stack.yaml` - Lambda functions
- `api-stack.yaml` - API Gateway
- `frontend-stack.yaml` - S3, CloudFront

---

## Common Development Tasks

### Adding a New Protection Group Feature

1. **Update DynamoDB Schema** (`cfn/database-stack.yaml`)
```yaml
ProtectionGroupsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    AttributeDefinitions:
      - AttributeName: ProtectionGroupId
        AttributeType: S
      - AttributeName: NewAttribute  # Add here
        AttributeType: S
```

2. **Update Lambda Handler** (`lambda/index.py`)
```python
def create_protection_group(event):
    body = json.loads(event['body'])
    
    # Add new attribute handling
    new_attribute = body.get('newAttribute')
    
    dynamodb.put_item(
        TableName=os.environ['PG_TABLE'],
        Item={
            'ProtectionGroupId': str(uuid.uuid4()),
            'Name': body['name'],
            'NewAttribute': new_attribute,  # Add here
            # ...
        }
    )
```

3. **Update Frontend Service** (`frontend/src/services/orchestrationService.ts`)
```typescript
export interface ProtectionGroup {
  protectionGroupId: string;
  name: string;
  newAttribute?: string;  // Add here
  // ...
}

export const createProtectionGroup = async (
  data: Omit<ProtectionGroup, 'protectionGroupId'>
): Promise<ProtectionGroup> => {
  const response = await authenticatedFetch('/protection-groups', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  return response.json();
};
```

4. **Update UI Component** (`frontend/src/components/`)
```typescript
// Add form field for new attribute
<TextField
  label="New Attribute"
  value={formData.newAttribute}
  onChange={(e) => setFormData({...formData, newAttribute: e.target.value})}
/>
```

---

### Integrating a New DRS API

1. **Add to DRS Service** (`frontend/src/services/drsService.ts`)
```typescript
export const describeNewFeature = async (
  params: NewFeatureParams
): Promise<NewFeatureResponse> => {
  const drs = new DRSClient({ region: AWS_REGION });
  
  const command = new DescribeNewFeatureCommand(params);
  const response = await drs.send(command);
  
  return response;
};
```

2. **Add Lambda Helper** (`lambda/index.py`)
```python
def call_drs_new_feature(params):
    """Wrapper for new DRS API"""
    try:
        response = drs_client.describe_new_feature(**params)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

---

## Testing Strategies

### Unit Tests
```bash
# Frontend
cd frontend
npm test

# Lambda
cd lambda
python -m pytest tests/
```

### Integration Tests
```bash
# Run E2E tests
cd tests/playwright
npx playwright test
```

### Manual Testing Checklist
- [ ] Create protection group
- [ ] Add servers to group
- [ ] Create recovery plan
- [ ] Execute drill recovery
- [ ] Monitor job progress
- [ ] Terminate recovery instances
- [ ] View execution history

---

## Deployment Guide

### Prerequisites
- AWS CLI configured with admin permissions
- CloudFormation stack names decided
- S3 bucket for deployment artifacts

### Deployment Steps

1. **Package Lambda**
```bash
cd lambda
python build_and_deploy.py
```

2. **Deploy Stacks in Order**
```bash
# 1. Security (IAM, Cognito)
aws cloudformation deploy \
  --template-file cfn/security-stack.yaml \
  --stack-name drs-orch-security \
  --capabilities CAPABILITY_IAM

# 2. Database (DynamoDB)
aws cloudformation deploy \
  --template-file cfn/database-stack.yaml \
  --stack-name drs-orch-database

# 3. Lambda Functions
aws cloudformation deploy \
  --template-file cfn/lambda-stack.yaml \
  --stack-name drs-orch-lambda

# 4. API Gateway
aws cloudformation deploy \
  --template-file cfn/api-stack.yaml \
  --stack-name drs-orch-api

# 5. Frontend (S3 + CloudFront)
aws cloudformation deploy \
  --template-file cfn/frontend-stack.yaml \
  --stack-name drs-orch-frontend
```

3. **Build and Deploy Frontend**
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://drs-orchestration-frontend-bucket/
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

---

## Monitoring & Debugging

### CloudWatch Logs
- Lambda logs: `/aws/lambda/drs-orchestration-function`
- API Gateway logs: `/aws/apigateway/drs-orch-api`
- Step Functions: `/aws/states/drs-recovery-plan`

### Common Issues

**Issue**: DRS API ThrottlingException
```python
# Solution: Implement exponential backoff
from botocore.exceptions import ClientError
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise
```

**Issue**: Cognito token expired
```typescript
// Solution: Implement auto-refresh
import { Auth } from 'aws-amplify';

async function refreshToken() {
  try {
    const session = await Auth.currentSession();
    return session.getIdToken().getJwtToken();
  } catch (error) {
    // Redirect to login
    await Auth.signOut();
    window.location.href = '/login';
  }
}
```

---

## Useful Resources

### Documentation
- AWS DRS API: https://docs.aws.amazon.com/drs/latest/APIReference/
- Project Wiki: `docs/` folder in repository
- Architecture Diagram: `docs/architecture/AWS-DRS-Orchestration-Architecture.drawio`

### Internal Tools
- DRS Console: https://console.aws.amazon.com/drs/
- CloudFormation: https://console.aws.amazon.com/cloudformation/
- CloudWatch: https://console.aws.amazon.com/cloudwatch/
- DynamoDB: https://console.aws.amazon.com/dynamodb/

### Support
- Issues: Repository GitHub issues
- Questions: Internal team Slack channel

---

## Next Steps for New Team Members

1. **Week 1**: Environment setup, run local development
2. **Week 2**: Review architecture, understand DRS concepts
3. **Week 3**: Implement small feature (add field, new API endpoint)
4. **Week 4**: Take on medium feature from Gap Analysis roadmap

**Welcome to the team! 🚀**

---

# Conclusion

This comprehensive API comparison provides the foundation for understanding disaster recovery platforms and continuing development of the AWS DRS Orchestration solution. The gap analysis and implementation roadmap offer clear direction for achieving feature parity with commercial solutions while leveraging AWS-native advantages.

For questions or contributions, please refer to the Developer Handoff Guide and project documentation.
