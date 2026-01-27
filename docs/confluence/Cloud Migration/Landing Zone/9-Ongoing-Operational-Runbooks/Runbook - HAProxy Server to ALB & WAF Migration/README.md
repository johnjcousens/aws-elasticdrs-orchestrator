# Runbook - HAProxy Server to ALB & WAF Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5287313614/Runbook%20-%20HAProxy%20Server%20to%20ALB%20%26%20WAF%20Migration

**Created by:** Aravindan A on December 01, 2025  
**Last modified by:** Aravindan A on December 12, 2025 at 11:27 AM

---

Annexure
--------

* Introduction
* Migration Strategy
* Naming Convention
* Pre-Requisites
* High Level Steps
* HAProxy to ALB/WAF Mapping
* Detailed Implementation Steps

  + Analyze HAProxy Configuration
  + Create ALB and WAF Configuration
  + Deploy ALB and WAF via GitHub Actions
  + Verify Deployment
  + Migration Testing
* Lessons Learnt/Known Issues

---

1. Introduction
---------------

This runbook details the migration process from HAProxy load balancers to AWS Application Load Balancer (ALB) with Web Application Firewall (WAF) for GuidingCare and HRP applications. The solution provides enhanced security, scalability, and AWS-native integration while maintaining existing functionality.

Below are the components involved in the migration:

* **HAProxy Frontend** - Migrated to ALB Listeners (HTTP/HTTPS)
* **HAProxy Backend** - Migrated to ALB Target Groups
* **HAProxy ACLs** - Migrated to ALB Listener Rules and WAF Rules
* **HAProxy Security Rules** - Migrated to WAF Web ACLs
* **HAProxy Health Checks** - Migrated to ALB Target Group Health Checks

2. Migration Strategy
---------------------

### 2.1 HAProxy Components Analysis

Each HAProxy server contains multiple components that need to be mapped to AWS services:

**HAProxy Configuration Elements:**

* **Global Settings**: Connection limits, timeouts, SSL configuration
* **Frontend**: Port bindings, SSL certificates, redirects
* **Backend**: Server pools, load balancing algorithms, health checks
* **ACLs**: Host-based routing, security rules, IP restrictions

### 2.2 AWS Service Mapping

* **HAProxy Global/Defaults** → ALB Connection Settings
* **HAProxy Frontend** → ALB Listeners (HTTP:80, HTTPS:443)
* **HAProxy Backend** → ALB Target Groups
* **HAProxy ACLs (Routing)** → ALB Listener Rules
* **HAProxy ACLs (Security)** → WAF Web ACL Rules
* **HAProxy Health Checks** → ALB Target Group Health Checks

3. Naming Convention
--------------------

To maintain consistency across all environments, follow the new standardized naming convention for ALB and WAF resources:

### 3.1 Naming Format

**Standard Format**: `[business-unit]-[customer]-[resource-type]-[descriptor]-[environment]-[region]`

Where:

* **business-unit**: `gc` (GuidingCare), `hrp` (HRP)
* **customer**: `gcix`, `gcom`, `gcpf`, `gcre`, `gctm`, `gcwf`, `sclr`, etc.
* **resource-type**: `alb`, `waf`, `tg`, `wafrule`
* **descriptor**: `01`, `02` or functional names like `dev`, `qa`, `perf`, `carepayer`, etc.
* **environment**: `dev`, `qa`, `perf`, `prod`
* **region**: `use1`, `usw2`

### 3.2 ALB Resource Naming

* **Format**: `gc-<customer>-alb-<descriptor>-<env>-<region>`
* **Examples**:

  + `gc-gcom-alb-01-perf-usw2`
  + `gc-gcre-alb-01-qa-use1`
  + `gc-gctm-alb-01-dev-use1`

### 3.3 WAF Resource Naming

* **Format**: `gc-<customer>-waf-<descriptor>-<env>-<region>`
* **Examples**:

  + `gc-gcom-waf-01-perf-usw2`
  + `gc-gcre-waf-01-qa-use1`
  + `gc-gctm-waf-01-dev-use1`

### 3.4 Target Group Naming

* **Format**: `gc-<customer>-tg-<descriptor>-<env>-<region>`
* **Examples**:

  + `gc-gcom-tg-01-perf-usw2`
  + `gc-gcre-tg-dev-qa-use1`
  + `gc-gcpf-tg-carepayer-perf-use1`
  + `gc-gctm-tg-gcbidev-dev-use1`

### 3.5 WAF Rule Naming

* **Format**: `gc-<customer>-wafrule-<RulePurpose>-<env>-<region>`
* **Examples**:

  + `gc-gcom-wafrule-AllowTrustedNetworks-perf-usw2`
  + `gc-gcre-wafrule-BlockRestrictedAPIPaths-qa-use1`
  + `gc-gctm-wafrule-AllowNonameSecurityIPs-dev-use1`

### 3.6 Log Group and S3 Prefix Naming

* **WAF Log Groups**: `aws-waf-logs-gc-<customer>-waf-<descriptor>-<env>-<region>`
* **ALB Access Logs**: `gc-<customer>-alb-<descriptor>-accesslogs-<env>-<region>`
* **ALB Connection Logs**: `gc-<customer>-alb-<descriptor>-connectionlogs-<env>-<region>`

### 3.7 Complete Naming Examples

| Component | Old Naming | New Naming |
| --- | --- | --- |
| **Config File** | `gcom-perf-alb-waf-usw2.yaml` | `gcom-perf-alb-waf-usw2.yaml` |
| **ALB** | `gcomalbe01-usw2` | `gc-gcom-alb-01-perf-usw2` |
| **WAF** | `gcomwafe01-usw2` | `gc-gcom-waf-01-perf-usw2` |
| **Target Group** | `gcomtge01-usw2` | `gc-gcom-tg-01-perf-usw2` |
| **WAF Rule** | `gc-AllowTrustedNetworks-gcomalbe01-usw2` | `gc-gcom-wafrule-AllowTrustedNetworks-perf-usw2` |
| **WAF Log Group** | `aws-waf-logs-gc-gcomwafe01-usw2` | `aws-waf-logs-gc-gcom-waf-01-perf-usw2` |
| **Access Logs** | `gc-gcomalbe01-accesslogs-usw2` | `gc-gcom-alb-01-accesslogs-perf-usw2` |

### 3.8 Environment Mapping

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

* VPC and subnets configured for ALB deployment
* Security groups configured for ALB and target instances
* SSL certificates imported into AWS Certificate Manager
* S3 bucket for ALB access logs
* HAProxy configuration file for analysis
* Target instances identified and accessible
* GitHub repository access with Actions enabled

5. High Level Steps
-------------------

| # | Phase | Task | Details |
| --- | --- | --- | --- |
| 1 | Analysis | Analyze HAProxy Configuration | Extract frontends, backends, ACLs, and security rules |
| 2 | Planning | Create Migration Mapping | Map HAProxy components to ALB/WAF equivalents |
| 3 | Implementation | Create ALB and WAF Configuration | Generate YAML configuration for deployment |
| 4 | Deployment | Deploy ALB and WAF via GitHub Actions | Use CI/CD pipeline for consistent deployment |
| 5 | Testing | Verify Deployment | Test ALB functionality and WAF rules |
| 6 | Migration | Perform Migration Testing | Validate traffic routing and security |
| 7 | Cutover | DNS and Traffic Switch | Update DNS to point to ALB |

6. HAProxy to ALB/WAF Mapping
-----------------------------

### 6.1 HAProxy to AWS Services Component Mapping

| HAProxy Component | AWS Equivalent | Purpose |
| --- | --- | --- |
| Frontend (bind :80) | ALB HTTP Listener | HTTP traffic handling |
| Frontend (bind :443 ssl) | ALB HTTPS Listener | HTTPS traffic with SSL termination |
| Backend servers | ALB Target Groups | Server pool management |
| ACL host routing | ALB Listener Rules | Host-based traffic routing |
| ACL security rules | WAF Web ACL Rules | Security filtering and blocking |
| Health checks | Target Group Health Checks | Server health monitoring |
| Load balancing | Target Group algorithms | Traffic distribution |
| SSL certificates | ACM certificates | SSL/TLS management |
| Logging | CloudWatch + S3 | Access and security logging |

### 6.2 HAProxy Configuration to ALB/WAF Migration Examples

| HAProxy Element | Configuration | ALB/WAF Equivalent |
| --- | --- | --- |
| `bind :443 ssl` | SSL on port 443 | HTTPS Listener with ACM certificate |
| `bind :80` | HTTP on port 80 | HTTP Listener with redirect to HTTPS |
| `backend BE_APP` | Server pool for application | Target Group `apptge01-usw2-tg` |
| `acl is_BE_APP hdr_dom(host)` | Host header matching | Listener Rule with host-header condition |
| `acl isBlockedPath` | Path-based blocking | WAF Rule with regex pattern matching |
| `option httpchk` | Health check configuration | Target Group health check settings |

7. Detailed Implementation Steps
--------------------------------

### 7.1 Analyze HAProxy Configuration

1. **Extract HAProxy Components**:  
   Review the HAProxy configuration file to identify key elements that need migration.
2. **HAProxy to AWS Service Conversion Analysis**:  
   Extract HAProxy frontend bindings and convert to ALB listeners with appropriate SSL policies. Map HAProxy backend server pools to ALB target groups with equivalent health check configurations and load balancing algorithms. Convert HAProxy ACL rules into ALB listener rules for host-based routing and WAF rules for security filtering, ensuring priority ordering matches the original HAProxy rule precedence.

**Example: HAProxy Analysis**

| Component | Current HAProxy Config | Notes |
| --- | --- | --- |
| Frontend | `bind :443 ssl`, `bind :80` | HTTPS on 443, HTTP on 80 with redirect |
| SSL Certificate | `/etc/pki/tls/private/cert.pem` | Needs ACM equivalent |
| Backend BE\_APP | 4 servers on port 443 | HTTPS backend servers |
| Backend BE\_API | 1 server on port 8086 | HTTP backend server |
| Host ACL | `app-example.domain.com` | Host-based routing |
| Security ACL | `isBlockedPath` regex | API path blocking |
| Health Check | `/health` | Custom health check endpoint |

**HAProxy Configuration Analysis:**


```
Frontend APP:
- bind :443 ssl crt /etc/pki/tls/private/cert.pem alpn h2,http/1.1
- bind :80
- redirect scheme https code 301 if !{ ssl_fc }

Backend BE_APP:
- balance leastconn
- option httpchk GET /health HTTP/1.0\r\nHost:\ app-example.domain.com
- server APP01 <server-ip>:443 check ssl
- server APP02 <server-ip>:443 check ssl

Backend BE_API:
- option httpchk GET /api/health HTTP/1.1\r\nHost:\ api-example.domain.com
- server API01 <server-ip>:8086 check

Security ACLs:
- acl isNonameSecIP src <security-scanner-ips>
- acl isLocalIP src <on-prem-cidr>
- acl isBlockedPath path -i -m reg (?:.*\/AuthorizationAPI\/.*|.*\/AdminAPI\/.*)
```


### 7.2 Create ALB and WAF Configuration

1. **Config Directory Structure**:

   
```
config/
├── gcom-perf-alb-waf-usw2.yaml
├── gcpf-alb-waf-use1.yaml
├── sclr-perf-alb-waf-usw2.yaml
└── gcwf-qa-alb-waf-usw2.yaml
```

2. **Navigate to Config Directory**:

   
```bash
cd platform.gc-iac/config
```

3. **Create ALB and WAF Configuration File**:  
   Create configuration file following the existing pattern:


```yaml
# ALB Configuration for HAProxy Server Migration
# HAProxy Server: example-haproxy-server
# HAProxy Frontend: APP (bind :443 ssl, bind :80)
# HAProxy Backends: BE_APP, BE_API

globals:
  region: "us-west-2"  
  org_name: "guiding-care"
  project_name: "example-ha-proxy-alb"
  account_id: "<ACCOUNT_ID>"
  vpc_id: "<VPC_ID>"
  
  common_tags: &common_tags
    BusinessUnit: "GuidingCare" 
    Owner: "gc_infrastructure@healthedge.com" 
    Environment: "Development"
    DataClassification: "Internal"  
    ComplianceScope: "None"

resource_groups:
  # WAF Configuration - HAProxy Security ACLs Migration
  waf:
    resources:
      web_acls:
        - id: "gc-example-waf-01-perf-usw2-waf" 
          name: "gc-example-waf-01-perf-usw2" 
          description: "Dedicated WAF for ALB replacing HAProxy security ACLs"
          scope: "REGIONAL"
          default_action: "ALLOW"
          
          # WAF Logging
          logging:
            create_log_group: true
            log_group_name: "aws-waf-logs-gc-example-waf-01-perf-usw2"
            retention_days: 7
            redacted_fields:
              - "query_string"
              - "uri_path"
            default_behavior: "KEEP"
            filters:
              - behavior: "KEEP"
                requirement: "MEETS_ANY"
                conditions:
                  - field: "action"
                    value: "BLOCK"
            tags:
              <<: *common_tags
          
          rules:
            # Allow Trusted Networks - HAProxy isLocalIP equivalent
            - name: "gc-example-wafrule-AllowTrustedNetworks-perf-usw2"
              type: "ip_set"
              priority: 1
              action: "allow"
              ip_addresses:
                - "<vpc-cidr>"   # VPC CIDR
                - "<on-prem-network>"    # On-prem network
              description: "Allow trusted networks VPC CIDR and on-prem access"
            
            # Block Restricted API Paths - HAProxy isBlockedPath equivalent
            - name: "gc-example-wafrule-BlockRestrictedAPIPaths-perf-usw2"
              type: "regex_pattern"
              priority: 2
              action: "block"
              field_to_match: "uri_path"
              regex_patterns:
                - ".*\\/AuthorizationAPI\\/.*"
                - ".*\\/AdminAPI\\/.*"
                - ".*\\/ConfigAPI\\/.*"
              custom_response:
                response_code: 403
                body_key: "blocked_api_path"
                response_headers:
                  - name: "X-Blocked-Reason"
                    value: "Restricted API Access"
              description: "Block restricted API paths for ALL IPs"
            
            # Allow Security Scanner IPs - HAProxy isNonameSecIP equivalent
            - name: "gc-example-wafrule-AllowSecurityScannerIPs-perf-usw2"
              type: "ip_set"
              priority: 3
              action: "allow"
              ip_addresses:
                - "<security-scanner-ip-1>"
                - "<security-scanner-ip-2>"
                - "<security-scanner-ip-3>"
              description: "Allow Security Scanner IPs"
          
          tags:
            <<: *common_tags

  # Load Balancer Configuration - HAProxy Frontend/Backend Migration
  load_balancer:
    resources:
      application_load_balancers:
        - id: "gc-example-alb-01-perf-usw2-alb"
          name: "gc-example-alb-01-perf-usw2"
          internet_facing: true
          
          protection:
            deletion_protection_enabled: true
          
          # Network Configuration
          subnets:
            subnet_ids:
              - "<SUBNET_ID_1>"
              - "<SUBNET_ID_2>"
              - "<SUBNET_ID_3>"
          
          security_groups:
            existing_security_group_ids:
              - "<SECURITY_GROUP_ID>"
          
          # Connection Settings - HAProxy timeout mapping
          connection_settings:
            idle_timeout_seconds: 120  # HAProxy timeout client 2m
            client_keep_alive_seconds: 3600
            http2_enabled: true  # HAProxy alpn h2,http/1.1
            drop_invalid_header_fields_enabled: false
            xff_header_processing_mode: "append"
            xff_client_port_enabled: true
            cross_zone_load_balancing_enabled: true
            desync_mitigation_mode: "defensive"
            connection_logs_enabled: true
            connection_logs_bucket: "<LOG_BUCKET>"
            connection_logs_prefix: "gc-example-alb-01-connectionlogs-perf-usw2"
          
          # Access Logging - HAProxy log equivalent
          access_logs:
            enabled: true
            bucket: "<LOG_BUCKET>"
            prefix: "gc-example-alb-01-accesslogs-perf-usw2"
          
          # Associate with WAF
          web_acl_id: "gc-example-waf-01-perf-usw2-waf"
          
          # Listeners - HAProxy frontend equivalent
          listeners:
            # HTTP Listener - HAProxy bind :80 with redirect
            - id: "http-redirect-listener"
              port: 80
              protocol: "HTTP"
              default_actions:
                - type: "redirect"
                  redirect_config:
                    protocol: "HTTPS"
                    port: "443"
                    status_code: "HTTP_301"
            
            # HTTPS Listener - HAProxy bind :443 ssl
            - id: "https-listener"
              port: 443
              protocol: "HTTPS"
              ssl_policy: "ELBSecurityPolicy-TLS13-1-2-2021-06"
              certificate:
                certificate_arn: "<CERTIFICATE_ARN>"
              
              default_actions:
                - type: "forward"
                  target_group_id: "gc-example-tg-app-perf-usw2-tg"
              
              # Listener Rules - HAProxy ACL equivalent
              rules:
                # APP Host Routing - HAProxy is_BE_APP
                - priority: 100
                  conditions:
                    - field: "host-header"
                      values: ["app-example.domain.com"]
                  actions:
                    - type: "forward"
                      target_group_id: "gc-example-tg-app-perf-usw2-tg"
                
                # API Host Routing - HAProxy is_BE_API
                - priority: 200
                  conditions:
                    - field: "host-header"
                      values: ["api-example.domain.com"]
                  actions:
                    - type: "forward"
                      target_group_id: "gc-example-tg-api-perf-usw2-tg"
          
          # Target Groups - HAProxy backend equivalent
          target_groups:
            # BE_APP Backend Migration
            - id: "gc-example-tg-app-perf-usw2-tg"
              name: "gc-example-tg-app-perf-usw2"
              port: 443
              protocol: "HTTPS"
              vpc_id: "${globals.vpc_id}"
              
              # Health Check - HAProxy option httpchk
              health_check:
                enabled: true
                healthy_threshold_count: 2
                unhealthy_threshold_count: 3
                timeout_seconds: 60
                interval_seconds: 90
                path: "/health"
                success_codes: "200-404"
                protocol: "HTTPS"
                port: "traffic-port"
              
              attributes:
                deregistration_delay_timeout_seconds: 90
                load_balancing_algorithm_type: "least_outstanding_requests"
                slow_start_duration_seconds: 0
                load_balancing_cross_zone_enabled: true
              
              targets: []  # Targets managed by deployment process
              
              tags:
                <<: *common_tags
            
            # BE_API Backend Migration
            - id: "gc-example-tg-api-perf-usw2-tg"
              name: "gc-example-tg-api-perf-usw2"
              port: 8086
              protocol: "HTTP"
              vpc_id: "${globals.vpc_id}"
              
              health_check:
                enabled: true
                healthy_threshold_count: 2
                unhealthy_threshold_count: 3
                timeout_seconds: 60
                interval_seconds: 90
                path: "/api/health"
                success_codes: "200-404"
                protocol: "HTTP"
                port: "traffic-port"
              
              attributes:
                deregistration_delay_timeout_seconds: 90
                load_balancing_algorithm_type: "least_outstanding_requests"
                slow_start_duration_seconds: 0
                load_balancing_cross_zone_enabled: true
              
              targets: []  # Targets managed by deployment process
              
              tags:
                <<: *common_tags
          
          tags:
            <<: *common_tags
```


### 7.3 Deploy ALB and WAF via GitHub Actions

**Important**: Deploy ALB initially with empty target groups (`targets: []`). After server rehosting through CMF and confirming instance health, redeploy with actual targets including instance names and ports.

1. **Create Feature Branch**:

   
```bash
git checkout -b feature/example-alb-waf-migration
```

2. **Add Configuration Files**:

   
```bash
git add config/example-perf-alb-waf-usw2.yaml
git commit -m "Adding ALB and WAF configuration for HAProxy migration"
git push origin feature/example-alb-waf-migration
```

3. **Deploy Using GitHub Actions**:

   * Go to GitHub repository
   * Navigate to **Actions** tab
   * Select **Deploy** workflow
   * Click **Run workflow**
   * Configure parameters:

     + **Branch**: `main`
     + **Configuration file path**: `config/example-perf-alb-waf-usw2.yaml`
     + **AWS Region**: `us-west-2`
     + **Environment**: `development`
     + **Action to perform**: `deploy`
     + **AWS Account ID**: `<TARGET_ACCOUNT_ID>`
   * Click **Run workflow**

### 7.4 Verify Deployment

1. **Check Deployment Status**:  
   Monitor the GitHub Actions workflow for successful completion.
2. **Verify ALB Creation**:  
   Check AWS Console for ALB creation and configuration.
3. **Verify WAF Configuration**:  
   Confirm WAF rules are properly configured and associated with ALB.
4. **Check Target Group Health**:  
   Verify target groups are created and health checks are configured.

### 7.5 Migration Testing

1. **Pre-Migration Testing**:

   * Test ALB functionality with temporary DNS entries
   * Verify WAF rules are blocking restricted paths
   * Confirm health checks are passing
   * Validate SSL certificate configuration
2. **Traffic Validation**:

   * Test blocked API paths return 403 responses
   * Test allowed paths work correctly
   * Verify host-based routing functions properly

8. Lessons Learnt/Known Issues
------------------------------

1. **Load Balancing Algorithm**: Do not use round robin algorithm as per GC requirements. AWS ALB only supports `least_outstanding_requests` algorithm, which provides better performance than round robin by routing requests to targets with the fewest active requests.
2. **SSL Certificate Migration**: Ensure SSL certificates are imported into AWS Certificate Manager before ALB deployment. HAProxy PEM files need to be converted to ACM format.
3. **Certificate Configuration Patterns**: The ALB construct supports two distinct certificate configuration patterns:

   * **Single Certificate**: Use `certificate:` (singular) for single domain configurations

     
```yaml
certificate:
  certificate_arn: "arn:aws:acm:region:account:certificate/cert-id"
```

   * **Multiple Certificates (SNI)**: Use `certificates:` (plural) with array format for multi-domain SNI support

     
```yaml
certificates:
  - certificate_arn: "arn:aws:acm:region:account:certificate/cert-id-1"  # Default certificate
  - certificate_arn: "arn:aws:acm:region:account:certificate/cert-id-2"  # SNI certificate
```

   * **Important**: First certificate in the array becomes the default certificate, additional certificates are configured for SNI (Server Name Indication)
4. **Health Check Differences**: ALB health checks have different timeout and interval constraints compared to HAProxy. Ensure health check intervals are greater than timeout values.
5. **WAF Rule Ordering**: WAF rules are processed in priority order. Ensure allow rules have higher priority (lower numbers) than block rules to prevent unintended blocking.
6. **Target Group Registration**: Target groups are initially created empty. Target registration is handled through the deployment process or separate automation.
7. **Cross-Zone Load Balancing**: Enable cross-zone load balancing for even traffic distribution across availability zones, especially important for uneven target distribution.
8. **Logging Configuration**: ALB access logs and WAF logs use different formats than HAProxy logs. Update log parsing and monitoring tools accordingly.
9. **Connection Draining**: ALB deregistration delay should match HAProxy timeout server settings to ensure graceful connection handling during deployments.