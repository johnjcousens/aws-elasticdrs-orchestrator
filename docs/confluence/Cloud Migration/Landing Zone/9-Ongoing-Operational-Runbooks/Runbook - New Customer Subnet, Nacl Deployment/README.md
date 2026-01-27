# Runbook - New Customer Subnet, Nacl Deployment

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5288132649/Runbook%20-%20New%20Customer%20Subnet%2C%20Nacl%20Deployment

**Created by:** Aravindan A on December 01, 2025  
**Last modified by:** Aravindan A on December 10, 2025 at 07:16 PM

---

Annexure
--------

* Introduction
* CIDR Allocation Strategy
* Naming Convention
* Pre-Requisites
* High Level Steps
* Subnet and NACL Mapping
* Detailed Implementation Steps

  + Get Subnet Requirements
  + Get NACL Rules
  + Create Subnet and NACL Configuration
  + Complete Configuration File
  + Deploy Subnets and NACLs via GitHub Actions
  + Verify Deployment
* Lessons Learnt/Known Issues

---

1. Introduction
---------------

This runbook details the CDK code changes required to implement subnets and Network Access Control Lists (NACLs) for GuidingCare customers/partners. The solution uses IPAM-based automatic IP allocation with comprehensive NACL rule management.

Below are the network components needed for each customer/partner:

* **Application Subnets** - Private subnets for application workloads with egress connectivity
* **Database Subnets** - Private subnets for database workloads with restricted access
* **Network ACLs** - Stateless firewall rules for subnet-level security

2. CIDR Allocation Strategy
---------------------------

### 2.1 Customer/Partner CIDR Allocation

Each customer/partner is allocated an entire **/24 CIDR block** from the VPC address space. This /24 allocation provides clear network segregation and simplifies network configuration management for each customer/partner.

**Benefits of /24 per customer:**

* Clear network boundaries between customers/partners
* Simplified routing and firewall rule management
* Adequate IP space for multi-tier applications
* Complete /24 CIDR block occupation per customer

### 2.2 Subnet Size Standards and /24 CIDR Utilization

* **Application Subnets**: **/26 CIDR** (64 IP addresses per subnet)

  + Provides sufficient IPs for application workloads
  + 3 application subnets across AZs = 3 × /26 = 192 IPs used
* **Database Subnets**: **/28 CIDR** (16 IP addresses per subnet)

  + Optimized for database workloads with fewer instances
  + 3 database subnets across AZs = 3 × /28 = 48 IPs used

### 2.3 Complete /24 CIDR Block Utilization

**Total IP Usage per Customer:**

* Application subnets: 3 × /26 = 192 IP addresses
* Database subnets: 3 × /28 = 48 IP addresses
* **Total Used**: 240 IP addresses out of 256 available in /24
* **Remaining Unused**: 16 IP addresses

**Unused CIDR Space:**  
The remaining 16 IP addresses (equivalent to one /28 subnet) within each customer's /24 allocation are left unused in the configuration. This unused space ensures complete /24 CIDR block occupation per customer while maintaining clean subnet boundaries.

**Purpose of /24 Complete Occupation:**

* Ensures entire /24 block is allocated to single customer
* Prevents CIDR fragmentation across multiple customers
* Maintains network isolation boundaries
* Simplifies IP address management and routing

**Example /24 Utilization for Customer "Shared":**


```
Customer /24 Block: 10.0.1.0/24 (256 IPs)
├── App Subnet 1: 10.0.1.0/26   (64 IPs) - AZ-1a
├── App Subnet 2: 10.0.1.64/26  (64 IPs) - AZ-1b  
├── App Subnet 3: 10.0.1.128/26 (64 IPs) - AZ-1c
├── DB Subnet 1:  10.0.1.192/28 (16 IPs) - AZ-1a
├── DB Subnet 2:  10.0.1.208/28 (16 IPs) - AZ-1b
├── DB Subnet 3:  10.0.1.224/28 (16 IPs) - AZ-1c
└── Unused Space: 10.0.1.240/28 (16 IPs) - Completes /24 occupation
```


### 2.4 IPAM Pool Configuration

The subnet creation uses **IPAM (IP Address Manager) pools** for automatic CIDR allocation. This approach provides:

* **Automatic IP Allocation**: CIDR blocks are automatically assigned by IPAM
* **IPAM Pool Integration**: Uses `ipam_pool_id` with the respective VPC as the source
* **Dynamic CIDR Assignment**: IPAM automatically assigns available CIDR blocks from the pool
* **Conflict Prevention**: Prevents overlapping CIDR assignments across deployments
* **Centralized IP Management**: All IP allocations managed through AWS IPAM service

**IPAM Configuration Requirements:**

* IPAM pool must be configured with the target VPC
* Pool must have sufficient available CIDR space for requested subnet sizes
* Pool must be accessible from the deployment account/region
* Pool should be organized to allocate complete /24 blocks per customer

**Important**: Throughout this runbook we will take an example of **Shared** customer environment to create the required AWS components.

3. Naming Convention
--------------------

To maintain consistency across all environments, follow below naming convention for Subnets and NACLs:

### 3.1 Subnet Naming Convention

* **Format**: `<project>-<customer>-<type>sub-<purpose><number>-<env>-<region>`

### 3.2 NACL Naming Convention

* **Format**: `<project>-<customer>-nacl-<purpose>-<env>-<region>`

### 3.3 Naming Examples

| Component | GC Example | HRP Example |
| --- | --- | --- |
| App Subnet | `gc-shared-pvtsub-app01-nonprod-use1` | `hrp-atr-pvtsub-app01-nonprod-use1` |
| DB Subnet | `gc-shared-pvtsub-db01-nonprod-use1` | `hrp-atr-pvtsub-db01-nonprod-use1` |
| App NACL | `gc-shared-nacl-app-nonprod-use1` | `hrp-atr-nacl-app-nonprod-use1` |
| DB NACL | `gc-shared-nacl-db-nonprod-use1` | `hrp-atr-nacl-db-nonprod-use1` |

4. Pre-Requisites
-----------------

* AWS Target account created via LZA
* Customer VPC deployed in the AWS target account
* IPAM pool configured and accessible for automatic allocation
* IPAM pool associated with the target VPC
* Route tables created for subnet associations
* AWS CLI configured with appropriate permissions
* Access to GitHub repository with Actions enabled

5. High Level Steps
-------------------

| # | Phase | Task | Details |
| --- | --- | --- | --- |
| 1 | Requirement Gathering | Get Subnet Requirements | Gather subnet requirements, availability zones, and routing needs from application teams |
| 2 | Requirement Gathering | Get NACL Rules | Document required network access rules for each subnet tier |
| 3 | Implementation | Create Subnet Configuration | Create YAML configuration files for subnet deployment |
| 4 | Implementation | Deploy via Git Actions | Deploy subnets using GitHub Actions pipeline |
| 5 | Implementation | Create NACL Configuration | Create YAML configuration files for NACL rules |
| 6 | Implementation | Deploy NACLs via Git Actions | Deploy NACLs using GitHub Actions pipeline |
| 7 | Validation | Verify Deployment | Validate subnet creation and NACL rule application |

6. Subnet and NACL Mapping
--------------------------

| Resource Type | Count | Size | Total IPs | Purpose |
| --- | --- | --- | --- | --- |
| Application Subnets | 3 | /26 each | 192 IPs | App workloads across 3 AZs |
| Database Subnets | 3 | /28 each | 48 IPs | DB workloads across 3 AZs |
| **Unused Space** | **1** | **/28** | **16 IPs** | **Completes /24 occupation** |
| Application NACL | 1 | N/A | N/A | Controls app subnet traffic |
| Database NACL | 1 | N/A | N/A | Controls DB subnet traffic |
| **Total** | **6 subnets + 2 NACLs** | **Mixed** | **256 IPs (/24)** | **Complete customer allocation** |

7. Detailed Implementation Steps
--------------------------------

### 7.1 Get Subnet Requirements

Talk to the application team and understand the network requirements:

1. **Subnet Types Needed**: Application, Database private subnets
2. **CIDR Requirements**: Confirm /24 allocation for customer and subnet sizing (/26 for app, /28 for DB)
3. **Availability Zones**: Multi-AZ requirements for high availability
4. **Routing Requirements**: Route table associations and egress needs
5. **IPAM Pool**: Verify IPAM pool has sufficient space for customer allocation

Create a Subnet tab in the project documentation and record these details:

**Example: Subnet Requirements**

| Subnet Name | Type | AZ | CIDR Size | IP Count | Route Table | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| gc-shared-pvtsub-app01 | Private | us-east-1a | /26 | 64 | rtb-xxxxxxxxx | Application workloads |
| gc-shared-pvtsub-app02 | Private | us-east-1b | /26 | 64 | rtb-xxxxxxxxx | Application workloads |
| gc-shared-pvtsub-app03 | Private | us-east-1c | /26 | 64 | rtb-xxxxxxxxx | Application workloads |
| gc-shared-pvtsub-db01 | Private | us-east-1a | /28 | 16 | rtb-yyyyyyyyy | Database workloads |
| gc-shared-pvtsub-db02 | Private | us-east-1b | /28 | 16 | rtb-yyyyyyyyy | Database workloads |
| gc-shared-pvtsub-db03 | Private | us-east-1c | /28 | 16 | rtb-yyyyyyyyy | Database workloads |
| **Unused Space** | **N/A** | **N/A** | **/28** | **16** | **N/A** | **Completes /24 occupation** |

### 7.2 Get NACL Rules

Document the required network access rules for each subnet tier:

1. **Application Tier Rules**: Inter-application communication, database access
2. **Database Tier Rules**: Application access, backup traffic
3. **Protocol Requirements**: TCP, UDP, ICMP specifications
4. **Port Ranges**: Specific ports or port ranges needed

**Example: NACL Rules Documentation**

| Rule # | Direction | Protocol | Port Range | Source/Destination | Action | Description |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | Inbound | TCP | 80 | Internal CIDR | Allow | HTTP from internal |
| 110 | Inbound | TCP | 443 | Internal CIDR | Allow | HTTPS from internal |
| 200 | Outbound | All | All | 0.0.0.0/0 | Allow | All outbound traffic |

### 7.3 Create Subnet and NACL Configuration

1. **Config Directory Structure**:

   
```
config/
└── network-resources/
    ├── shared/
    │   ├── gc-shared-prod-use1.yaml
    │   └── gc-shared-nonprod-use1.yaml
    ├── sales-demo/
    │   ├── gc-sales-prod-use1.yaml
    │   └── gc-sales-nonprod-use1.yaml
    └── migration-test/
        ├── gc-migration-prod-use1.yaml
        └── gc-migration-nonprod-use1.yaml
```

2. **Navigate to Config Directory**:

   
```bash
cd platform.gc-iac/config/network-resources
```

3. **Create Customer Directory** (if not exists):

   
```bash
mkdir -p shared
```

4. **Create Subnet Configuration File**:  
   Create `gc-shared-nonprod-use1.yaml` with the following structure:


```yaml
globals:
  region: "us-east-1"
  org_name: "guiding-care"
  project_name: "shared-network-resources"
  environment: "nonprod"
  account_id: "<ACCOUNT_ID>"
  vpc_id: "<VPC_ID>"
  ipam_pool_id: "<IPAM_POOL_ID>"  # IPAM pool associated with the VPC
  
  common_tags: &common_tags
    BusinessUnit: "GuidingCare"
    Owner: "gc_infrastructure@healthedge.com"
    Environment: "NonProduction"
    DataClassification: "Internal"
    ComplianceScope: "None"
    Customer: "Shared"

resource_groups:
  subnets:
    resources:
      subnets:
        # Application Private Subnets (/26 each - 64 IPs per subnet)
        - id: "gc-shared-pvtsub-app01"
          name: "gc-shared-pvtsub-app01-nonprd-use1"
          availability_zone: "us-east-1a"
          type: "private_with_egress"
          ipam_allocation:
            netmask_length: 26  # /26 for application subnets
          route_table_id: "<ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags
            kubernetes.io/role/internal-elb: "1"
            
        - id: "gc-shared-pvtsub-app02"
          name: "gc-shared-pvtsub-app02-nonprd-use1"
          availability_zone: "us-east-1b"
          type: "private_with_egress"
          ipam_allocation:
            netmask_length: 26  # /26 for application subnets
          route_table_id: "<ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags
            kubernetes.io/role/internal-elb: "1"
            
        - id: "gc-shared-pvtsub-app03"
          name: "gc-shared-pvtsub-app03-nonprd-use1"
          availability_zone: "us-east-1c"
          type: "private_with_egress"
          ipam_allocation:
            netmask_length: 26  # /26 for application subnets
          route_table_id: "<ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags
            kubernetes.io/role/internal-elb: "1"

        # Database Private Subnets (/28 each - 16 IPs per subnet)
        - id: "gc-shared-pvtsub-db01"
          name: "gc-shared-pvtsub-db01-nonprd-use1"
          availability_zone: "us-east-1a"
          type: "private_isolated"
          ipam_allocation:
            netmask_length: 28  # /28 for database subnets
          route_table_id: "<DB_ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags
            
        - id: "gc-shared-pvtsub-db02"
          name: "gc-shared-pvtsub-db02-nonprd-use1"
          availability_zone: "us-east-1b"
          type: "private_isolated"
          ipam_allocation:
            netmask_length: 28  # /28 for database subnets
          route_table_id: "<DB_ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags
            
        - id: "gc-shared-pvtsub-db03"
          name: "gc-shared-pvtsub-db03-nonprd-use1"
          availability_zone: "us-east-1c"
          type: "private_isolated"
          ipam_allocation:
            netmask_length: 28  # /28 for database subnets
          route_table_id: "<DB_ROUTE_TABLE_ID>"
          tags:
            <<: *common_tags

# Note: The above configuration uses 240 IPs out of the allocated /24 CIDR block
# Remaining 16 IPs (one /28) are unused to complete /24 occupation per customer
```


### 7.4 Complete Configuration File

Add NACL configuration to the same YAML file created in step 7.3:


```yaml
  network_acls:
    resources:
      network_acls:
        # NACL for Application Private Subnets
        - id: "gc-shared-nacl-app"
          name: "gc-shared-nacl-app-nonprd-use1"
          subnet_associations:
            - "gc-shared-pvtsub-app01"
            - "gc-shared-pvtsub-app02"
            - "gc-shared-pvtsub-app03"
          inbound_rules:
            # Add inbound rules as per requirements
            - rule_number: 100
              protocol: "all"
              rule_action: "allow"
              cidr_block: "0.0.0.0/0"
          outbound_rules:
            # Add outbound rules as per requirements
            - rule_number: 100
              protocol: "all"
              rule_action: "allow"
              cidr_block: "0.0.0.0/0"
          tags:
            <<: *common_tags

        # NACL for Database Private Subnets
        - id: "gc-shared-nacl-db"
          name: "gc-shared-nacl-db-nonprd-use1"
          subnet_associations:
            - "gc-shared-pvtsub-db01"
            - "gc-shared-pvtsub-db02"
            - "gc-shared-pvtsub-db03"
          inbound_rules:
            # Add inbound rules as per requirements
            - rule_number: 100
              protocol: "all"
              rule_action: "allow"
              cidr_block: "0.0.0.0/0"
          outbound_rules:
            # Add outbound rules as per requirements
            - rule_number: 100
              protocol: "all"
              rule_action: "allow"
              cidr_block: "0.0.0.0/0"
          tags:
            <<: *common_tags
```


### 7.5 Deploy Subnets and NACLs via GitHub Actions

1. **Create Feature Branch**:

   
```bash
git checkout -b feature/shared-network-resources
```

2. **Add Complete Configuration**:

   
```bash
git add config/network-resources/shared/gc-shared-nonprod-use1.yaml
git commit -m "Adding Shared subnet and NACL configuration"
git push origin feature/shared-network-resources
```

3. **Deploy Using GitHub Actions**:

   * Go to GitHub repository
   * Navigate to **Actions** tab
   * Select **Deploy** workflow
   * Click **Run workflow**
   * Configure parameters:

     + **Branch**: `main`
     + **Configuration file path**: `config/network-resources/shared/gc-shared-nonprod-use1.yaml`
     + **AWS Region**: `us-east-1`
     + **Environment**: `nonprod`
     + **Action to perform**: `deploy`
     + **AWS Account ID**: `<TARGET_ACCOUNT_ID>`
   * Click **Run workflow**

### 7.6 Verify Deployment

1. **Check Subnet Creation**:

   
```bash
aws ec2 describe-subnets \
  --filters "Name=tag:Customer,Values=Shared" \
  --query 'Subnets[*].[Tags[?Key==`Name`].Value|[0],AvailabilityZone,CidrBlock,SubnetId]' \
  --output table
```

2. **Check NACL Creation**:

   
```bash
aws ec2 describe-network-acls \
  --filters "Name=tag:Customer,Values=Shared" \
  --query 'NetworkAcls[*].[Tags[?Key==`Name`].Value|[0],NetworkAclId,Associations[*].SubnetId]' \
  --output table
```


8. Lessons Learnt/Known Issues
------------------------------

1. **IPAM /24 CIDR Allocation Issue**: When requesting /24 subnets for a customer, IPAM pool ran out of available /24 blocks. The pool was configured with smaller available ranges. **Solution**: Either use /26 or /25 subnets, or expand the IPAM pool with additional /24 ranges before deployment.
2. **Sequential IPAM Dependency**: IPAM-based subnets must be created sequentially to avoid IP conflicts. Parallel deployment causes "overlapping CIDR" errors. The construct handles this with dependency chains.
3. **Route Table Association Timing**: Route table associations fail if the route table doesn't exist at deployment time. Always verify route table IDs before deployment.
4. **NACL Rule Number Conflicts**: Duplicate rule numbers within the same NACL cause deployment failures. Use increments of 10 for rule numbering to allow future insertions.
5. **Subnet Reference Resolution in NACL Rules**: When using `source_subnet` in NACL rules, ensure the referenced subnet exists and CIDR can be resolved at deployment time. CDK-managed subnets may require runtime resolution.