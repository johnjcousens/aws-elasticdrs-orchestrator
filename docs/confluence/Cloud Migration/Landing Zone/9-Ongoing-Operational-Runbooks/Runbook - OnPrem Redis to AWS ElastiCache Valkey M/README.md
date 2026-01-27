# Runbook - OnPrem Redis to AWS ElastiCache Valkey Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5287313623/Runbook%20-%20OnPrem%20Redis%20to%20AWS%20ElastiCache%20Valkey%20Migration

**Created by:** Aravindan A on December 01, 2025  
**Last modified by:** Aravindan A on December 10, 2025 at 07:17 PM

---

Annexure
--------

* Introduction
* Migration Strategy
* Naming Convention
* Pre-Requisites
* High Level Steps
* Redis to Valkey Mapping
* Detailed Implementation Steps

  + Analyze Current Redis Configuration
  + Create Valkey Configuration
  + Deploy Valkey via GitHub Actions
  + Configure User and Group Authentication
  + Update Application Configuration
  + Perform Migration Testing
* Monitoring
* Lessons Learnt/Known Issues

---

1. Introduction
---------------

This runbook details the migration process from OnPremise Redis clusters to AWS ElastiCache Valkey for GuidingCare and HRP applications. The solution provides enhanced performance, scalability, and AWS-native integration while maintaining Redis compatibility.

Below are the components involved in the migration:

* **OnPrem Redis Cluster** - Migrated to AWS ElastiCache Valkey Serverless
* **Redis Authentication** - Migrated to Valkey User/Group Authentication
* **Application Configuration** - Updated connection strings and endpoints
* **Session State Management** - Migrated from multi-node to single endpoint
* **API Caching** - Migrated to Valkey with improved performance

2. Migration Strategy
---------------------

### 2.1 Current Redis Architecture Analysis

Each Redis deployment contains multiple components that need to be migrated:

**OnPrem Redis Elements:**

* **Multi-Node Cluster**: 9 Redis servers with custom ports
* **SSL/TLS**: Encrypted connections with custom SSL hosts
* **Authentication**: User/password based authentication
* **Session State**: <http://ASP.NET> session state provider
* **API Caching**: Application-level caching with key prefixes

### 2.2 AWS Valkey Architecture

* **Single Endpoint**: Serverless Valkey with auto-scaling
* **Built-in SSL/TLS**: AWS managed encryption in transit
* **User Groups**: AWS managed authentication and authorization
* **Secrets Manager**: Secure credential storage
* **CloudWatch**: Integrated monitoring and metrics

### 2.3 Migration Benefits

* **Simplified Architecture**: Single endpoint vs multi-node cluster
* **Auto-Scaling**: Serverless scaling based on demand
* **Enhanced Security**: AWS managed encryption and authentication
* **Cost Optimization**: Pay-per-use serverless model
* **High Availability**: Multi-AZ deployment with automatic failover
* **Monitoring**: CloudWatch integration for detailed metrics

3. Naming Convention
--------------------

To maintain consistency across all environments, follow the standardized naming convention for Valkey resources:

### 3.1 Naming Format

**Standard Format**: `[business-unit]-[customer]-[resource-type]-[descriptor]-[environment]-[region]`

Where:

* **business-unit**: `gc` (GuidingCare), `hrp` (HRP)
* **customer**: `gcix`, `gcom`, `gcpf`, `gcre`, `gctm`, `gcwf`, `sclr`, etc.
* **resource-type**: `valkey`, `sm` (secrets manager)
* **descriptor**: `01`, `02` or functional names
* **environment**: `dev`, `qa`, `perf`, `prod`
* **region**: `use1`, `usw2`

### 3.2 Valkey Configuration File Naming

* **Format**: `<customer>-valkey-<region>.yaml`
* **Examples**: `gcom-valkey-usw2.yaml`, `gcre-valkey-use1.yaml`

### 3.3 Valkey Cluster Naming

* **Format**: `gc-<customer>-valkey-<descriptor>-<env>-<region>`
* **Examples**: `gc-gcom-valkey-01-perf-usw2`, `gc-gcre-valkey-01-dev-use1`

### 3.4 User and Group Naming

* **User Format**: `app<customer>`
* **Group Format**: `gc-<customer>-valkey-usergroup-<env>-<region>`
* **Examples**:

  + User: `appgcom`, `appgcre`
  + Group: `gc-gcom-valkey-usergroup-perf-usw2`

### 3.5 Secrets Manager Naming

* **Format**: `gc-<customer>-sm-valkey-<env>-<region>`
* **Examples**: `gc-gcom-sm-valkey-perf-usw2`, `gc-gcre-sm-valkey-dev-use1`

### 3.6 Complete Naming Examples

| Component | Old Naming | New Naming |
| --- | --- | --- |
| **Config File** | `gcom-valkey-usw2.yaml` | `gcom-valkey-usw2.yaml` |
| **Valkey Cluster** | `gc-gcomvalkey-e01-usw2` | `gc-gcom-valkey-01-perf-usw2` |
| **User** | `appgcom` | `appgcom` |
| **User Group** | `gc-valkey-gcom-user-group` | `gc-gcom-valkey-usergroup-perf-usw2` |
| **Secret** | `gc-sm-valkeygcom-dev-usw2` | `gc-gcom-sm-valkey-perf-usw2` |

### 3.7 Environment Mapping

| Customer | Environment | Description |
| --- | --- | --- |
| gcix | perf | Performance environment |
| gcom | perf | Performance environment |
| gcpf | perf | Performance environment |
| gcre | dev | Development environment |
| gctm | qa | QA environment |
| gcwf | qa | QA environment |
| sclr | perf | Performance environment |

4. Pre-Requisites
-----------------

* AWS Target account with appropriate permissions
* VPC and subnets configured for ElastiCache deployment
* Security groups configured for Valkey access
* Current Redis cluster configuration documentation
* Application configuration files access
* AWS CLI configured with appropriate permissions
* GitHub repository access with Actions enabled
* Backup of current application configurations

5. High Level Steps
-------------------

| # | Phase | Task | Details |
| --- | --- | --- | --- |
| 1 | Analysis | Analyze Current Redis Configuration | Document cluster setup, authentication, and application usage |
| 2 | Planning | Create Migration Mapping | Map Redis components to Valkey equivalents |
| 3 | Implementation | Create Valkey Configuration | Generate YAML configuration for deployment |
| 4 | Deployment | Deploy Valkey via GitHub Actions | Use CI/CD pipeline for consistent deployment |
| 5 | Configuration | Configure User and Group Authentication | Set up Valkey users, groups, and secrets |
| 6 | Migration | Update Application Configuration | Modify connection strings and endpoints |
| 7 | Testing | Perform Migration Testing | Validate functionality and performance |
| 8 | Cutover | Production Deployment | Deploy to production and monitor |

6. Redis to Valkey Mapping
--------------------------

### 6.1 OnPrem Redis to AWS Valkey Component Mapping

| OnPrem Redis Component | AWS Valkey Equivalent | Purpose |
| --- | --- | --- |
| Multi-node cluster | Single serverless endpoint | Simplified connection management |
| Custom port configuration | Standard port 6379 | Standardized connectivity |
| SSL with custom host | AWS managed TLS | Enhanced security |
| User/password auth | Valkey User Groups | AWS managed authentication |
| Manual scaling | Auto-scaling serverless | Dynamic resource allocation |
| Custom monitoring | CloudWatch integration | Comprehensive monitoring |
| Manual backups | Automated snapshots | Reliable backup management |

### 6.2 Configuration Migration Examples

| Configuration Element | OnPrem Redis | AWS Valkey |
| --- | --- | --- |
| **Connection String** | `server1:port,server2:port,...` | `single-endpoint:6379` |
| **SSL Configuration** | `ssl=true,sslHost=custom.host` | `ssl=true` (AWS managed) |
| **Authentication** | `user=appuser,password=pass` | `user=appuser,password=pass` |
| **Endpoint Count** | 9 servers | 1 serverless endpoint |
| **Port** | Custom port | Standard 6379 |

7. Detailed Implementation Steps
--------------------------------

### 7.1 Analyze Current Redis Configuration

1. **Document Current Redis Setup**:

**Example: GCOM Redis Analysis**

| Component | Current Configuration | Notes |
| --- | --- | --- |
| **Cluster Nodes** | 9 Redis servers (gctmrdss01-09) | Multi-node cluster |
| **Port** | Custom port | Non-standard configuration |
| **SSL** | Custom SSL host | `ingress.s01-lax3.redis.guidingcare.org` |
| **Authentication** | `appgcom` user | User/password authentication |
| **Session State** | <http://ASP.NET> provider | `sessgcom/Portal` application |
| **API Cache** | JSON configuration | `gcom` key prefix |
| **Connection String** | Multi-server list | Complex connection management |

**Current Redis Configuration Analysis:**


```
Session State (web.config):
- 9 server endpoints with custom ports
- SSL with custom sslHost
- User: appgcom
- Application: sessgcom/Portal

API Cache (appsettings.json):
- Same 9 server endpoints
- CacheType: Redis
- CacheKeyPrefix: gcom
```


### 7.2 Create Valkey Configuration

1. **Config Directory Structure**:

   
```
config/
├── gcom-valkey-usw2.yaml
├── gcpf-valkey-use1.yaml
├── gctm-valkey-use1.yaml
└── sclr-valkey-usw2.yaml
```

2. **Navigate to Config Directory**:

   
```bash
cd platform.gc-iac/config
```

3. **Create Valkey Configuration File**:  
   Create configuration file following the existing pattern:


```yaml
globals:
  region: "us-west-2"  
  org_name: "guiding-care"
  project_name: "gcom-valkey"
  account_id: "<ACCOUNT_ID>"
  vpc_id: "<VPC_ID>"
  
  common_tags: &common_tags
    BusinessUnit: "GuidingCare" 
    Owner: "gc_infrastructure@healthedge.com" 
    Environment: "Development"
    DataClassification: "Internal"  
    ComplianceScope: "None"

resource_groups:
  elasticache_valkey:
    resources:
      serverless_caches:
        - id: "serverless-valkey"
          serverless_cache_name: "gc-gcom-valkey-01-perf-usw2"
          engine: "valkey"
          description: "ElastiCache Serverless Valkey cluster for GCOM"
          
          # Engine version
          major_engine_version: "8"
          
          # Cache usage limits for serverless scaling
          # max_ecpu_per_second: 5000
          # max_data_storage: 20
          # data_storage_unit: "GB"
          
          # Network configuration
          subnet_ids:
            - "<SUBNET_ID_1>"
            - "<SUBNET_ID_2>"
            - "<SUBNET_ID_3>"
          security_group_ids: 
            - "<SECURITY_GROUP_ID>"
          
          # Encryption (optional)
          # kms_key_id: "<KMS_KEY_ARN>"
          
          # User access control (configured post-deployment)
          # user_group_id: "gc-gcom-valkey-usergroup-perf-usw2"
          
          # Backup settings
          daily_snapshot_time: "07:30"
          snapshot_retention_limit: 3
          
          # Snapshot restore (optional)
          # snapshot_arns_to_restore:
          #   - "<SNAPSHOT_ARN>"
          
          # Final snapshot name (optional)
          # final_snapshot_name: "final-snapshot-serverless-valkey"
          
          tags: *common_tags
```


### 7.3 Deploy Valkey via GitHub Actions

1. **Create Feature Branch**:

   
```bash
git checkout -b feature/gcom-valkey-migration
```

2. **Add Configuration Files**:

   
```bash
git add config/gcom-valkey-usw2.yaml
git commit -m "Adding GCOM Valkey configuration for Redis migration"
git push origin feature/gcom-valkey-migration
```

3. **Deploy Using GitHub Actions**:

   * Go to GitHub repository
   * Navigate to **Actions** tab
   * Select **Deploy** workflow
   * Click **Run workflow**
   * Configure parameters:

     + **Branch**: `main`
     + **Configuration file path**: `config/gcom-valkey-usw2.yaml`
     + **AWS Region**: `us-west-2`
     + **Environment**: `development`
     + **Action to perform**: `deploy`
     + **AWS Account ID**: `<TARGET_ACCOUNT_ID>`
   * Click **Run workflow**

### 7.4 Configure User and Group Authentication

**Note**: Run these commands in AWS CloudShell of the respective region where Valkey is deployed.

After Valkey deployment is complete, configure authentication using the following steps:

1. **Generate Secure Password**:

   
```bash
# Generate 32-character random hexadecimal string
openssl rand -hex 16
# Example output: 6c884c5eae91d80870e7b3b4eb86d95b
```

2. **Create Valkey User**:

   
```bash
# Create user with secure password for application access
aws elasticache create-user \
  --user-id "appgcom" \
  --user-name "appgcom" \
  --engine "valkey" \
  --passwords "<GENERATED_PASSWORD>" \
  --access-string "on ~* &* +@all" \
  --region us-west-2
```

3. **Store Credentials in Secrets Manager**:

   
```bash
# Create secret for Valkey credentials
aws secretsmanager create-secret \
  --name "gc-gcom-sm-valkey-perf-usw2" \
  --description "ElastiCache Valkey user credentials for gc-gcom-valkey-01-perf-usw2 cluster" \
  --secret-string '{"appgcom":{"username":"appgcom","password":"<GENERATED_PASSWORD>"}}' \
  --region us-west-2
```

4. **Create User Group**:

   
```bash
# Create user group to manage authentication
aws elasticache create-user-group \
  --user-group-id "gc-gcom-valkey-usergroup-perf-usw2" \
  --engine "valkey" \
  --user-ids "appgcom" \
  --region us-west-2
```

5. **Apply User Group to Valkey Cluster**:

   
```bash
# Enable authentication on serverless cache
aws elasticache modify-serverless-cache \
  --serverless-cache-name "gc-gcom-valkey-01-perf-usw2" \
  --user-group-id "gc-gcom-valkey-usergroup-perf-usw2" \
  --region us-west-2
```

6. **Verify Authentication Setup**:

   
```bash
# Check if user group is applied
aws elasticache describe-serverless-caches \
  --serverless-cache-name gc-gcom-valkey-01-perf-usw2 \
  --query 'ServerlessCaches[0].UserGroupId' \
  --region us-west-2
```


### 7.5 Update Application Configuration

1. **Update Session State Configuration (web.config)**:

**BEFORE (OnPrem Redis):**


```xml
<add name="MySessionStateStore" 
     type="Microsoft.Web.Redis.RedisSessionStateProvider" 
     connectionString="server1:port,server2:port,server3:port,...,ssl=true,sslHost=custom.host,user=appgcom,password=OLD_PASSWORD" 
     applicationName="sessgcom/Portal" />
```


**AFTER (AWS Valkey):**


```xml
<add name="MySessionStateStore" 
     type="Microsoft.Web.Redis.RedisSessionStateProvider" 
     connectionString="<VALKEY_ENDPOINT>:6379,ssl=true,user=appgcom,password=<GENERATED_PASSWORD>,syncTimeout=20000" 
     applicationName="sessgcom/Portal" />
```


2. **Update API Cache Configuration (appsettings.json)**:

**BEFORE (OnPrem Redis):**


```json
{
  "Redis": "server1:port,server2:port,server3:port,...,ssl=true,sslHost=custom.host,user=appgcom,password=OLD_PASSWORD",
  "CacheType": "Redis",
  "CacheKeyPrefix": "gcom"
}
```


**AFTER (AWS Valkey):**


```json
{
  "Redis": "<VALKEY_ENDPOINT>:6379,ssl=true,user=appgcom,password=<GENERATED_PASSWORD>,syncTimeout=20000",
  "CacheType": "Redis",
  "CacheKeyPrefix": "gcom"
}
```


### 7.6 Perform Migration Testing

1. **Pre-Migration Testing**:

   * Test Valkey connectivity and authentication
   * Verify basic cache operations (SET/GET)
   * Validate SSL/TLS connections
   * Test application configuration changes in development
2. **Connectivity Testing**:

   
```bash
# Test network connectivity
telnet <VALKEY_ENDPOINT> 6379
```

3. **Application Testing**:

   * Deploy updated configurations to development environment
   * Test session state functionality
   * Test API cache operations
   * Validate cache key prefixing
   * Perform load testing to validate auto-scaling

8. Monitoring
-------------

**Note**: This monitoring configuration will be handled by the respective GC application and DevOps teams.

### 8.1 Database Configuration for Redis Monitoring

Configure the monitoring database with the following Valkey connection parameters:

* **Endpoint**: `<VALKEY_ENDPOINT>:6379`
* **Username**: `appgcom` (or respective customer user)
* **Password**: `<GENERATED_PASSWORD>` (from Secrets Manager)
* **SSL/TLS**: `enabled` (AWS managed encryption)
* **Connection String**: `<VALKEY_ENDPOINT>:6379,ssl=true,user=appgcom,password=<GENERATED_PASSWORD>`

### 8.2 Monitoring Resources

For comprehensive monitoring and insights of your Valkey deployment, use the following resources:

**Link**: [redis.io/insights](https://redis.io/insights)

This provides detailed monitoring capabilities including:

* Performance metrics and analytics
* Real-time cluster health monitoring
* Query performance analysis
* Memory usage optimization insights
* Connection and throughput monitoring

9. Lessons Learnt/Known Issues
------------------------------

1. **User and Group Global Resources**: ElastiCache users and user groups are global resources within an AWS account/region and can be reused across multiple clusters. Plan user naming carefully to avoid conflicts.
2. **Authentication Timing**: After applying user groups to a serverless cache, wait 5-10 minutes for the modification to complete before testing authentication.
3. **Connection String Simplification**: Moving from multi-node Redis to single Valkey endpoint significantly simplifies connection string management and reduces application complexity.
4. **SSL Configuration**: AWS Valkey uses managed TLS, eliminating the need for custom SSL host configurations. Simply use `ssl=true` in connection strings.
5. **Secrets Management**: Store Valkey credentials in AWS Secrets Manager for secure access and easy rotation. Avoid hardcoding passwords in configuration files.
6. **Backup and Rollback**: Always backup current configurations before migration. Keep rollback procedures ready for emergency situations.
7. **Performance Monitoring**: Use CloudWatch metrics to monitor Valkey performance and compare with previous Redis cluster metrics to validate migration success.