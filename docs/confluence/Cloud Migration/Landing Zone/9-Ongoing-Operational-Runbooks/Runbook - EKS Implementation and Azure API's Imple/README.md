# Runbook - EKS Implementation and Azure API's Implementation

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5288296475/Runbook%20-%20EKS%20Implementation%20and%20Azure%20API%27s%20Implementation

**Created by:** Aravindan A on December 01, 2025  
**Last modified by:** Aravindan A on December 10, 2025 at 07:18 PM

---

Annexure
--------

* Introduction
* EKS Deployment Strategy
* Naming Convention
* Pre-Requisites
* High Level Steps
* EKS Configuration
* Detailed Implementation Steps

  + Deploy EKS Cluster
  + Verify EKS Cluster Creation
  + Configure EKS Access
  + Setup Jump Server Access
  + Deploy Applications via Jump Server
* Azure API Implementation
* Monitoring and Troubleshooting
* Lessons Learnt/Known Issues

---

1. Introduction
---------------

This runbook details the implementation process for AWS EKS (Elastic Kubernetes Service) clusters and Azure API integration for GuidingCare applications. The solution provides containerized application deployment with enhanced scalability, security, and AWS-native integration.

**Important Note**: EKS clusters are deployed without CI/CD pipelines. Application deployments are performed directly through the EKS jump server using kubectl and manifest files.

Below are the components involved in the implementation:

* **EKS Cluster** - Managed Kubernetes service with worker nodes
* **Jump Server** - EC2 instance for EKS cluster management and deployments
* **IAM Roles** - Service accounts and access control
* **Application Manifests** - Kubernetes deployment configurations
* **Azure API Integration** - External API connectivity and authentication

2. EKS Deployment Strategy
--------------------------

### 2.1 EKS Architecture Components

Each EKS deployment contains multiple components:

**EKS Cluster Elements:**

* **Control Plane**: Managed Kubernetes API server and etcd
* **Worker Nodes**: EC2 instances running containerized applications
* **Add-ons**: VPC CNI, CoreDNS, Kube-proxy, EFS CSI, ALB Controller
* **Security**: IRSA (IAM Roles for Service Accounts), Security Groups
* **Networking**: Private endpoint access, VPC integration

### 2.2 Deployment Architecture

* **Private Cluster**: Control plane accessible only from VPC
* **Jump Server Access**: Dedicated EC2 instance for cluster management
* **Direct Deployment**: No CI/CD pipeline, manual kubectl deployments
* **Manifest-based**: Application deployments using Kubernetes YAML files
* **Multi-Environment**: Separate configurations for dev, perf, prod

3. Naming Convention
--------------------

To maintain consistency across all environments, follow the standardized naming convention for EKS resources:

### 3.1 Naming Format

**Standard Format**: `[business-unit]-[customer]-[resource-type]-[descriptor]-[environment]-[region]`

Where:

* **business-unit**: `gc` (GuidingCare), `hrp` (HRP)
* **customer**: `infraops` (infrastructure operations)
* **resource-type**: `eks`, `jumpserver`
* **descriptor**: `cluster`, `01`, `02`
* **environment**: `dev`, `qa`, `perf`, `prod`
* **region**: `use1`, `usw2`

### 3.2 EKS Resource Naming

* **EKS Cluster**: `gc-infraops-eks-cluster-<env>-<region>`
* **Jump Server**: `gc-eks-jumpserver-<env>-<region>`
* **Node Groups**: `general-purpose`, `compute-optimized`
* **Service Accounts**: `aws-load-balancer-controller`, `cluster-autoscaler`

### 3.3 Configuration File Naming

* **Format**: `guiding-care-<env>-config.yaml`
* **Examples**: `guiding-care-perf-config.yaml`, `guiding-care-dev-config.yaml`

### 3.4 Complete Naming Examples

| Component | Example |
| --- | --- |
| **EKS Cluster** | `gc-infraops-eks-cluster-perf-use1` |
| **Jump Server** | `gc-eks-jumpserver-perf-use1` |
| **Config File** | `guiding-care-perf-config.yaml` |

4. Pre-Requisites
-----------------

* VPC and subnets configured for EKS deployment
* Security groups configured for EKS cluster and jump server
* IAM roles and policies for EKS service and worker nodes
* Jump server EC2 instance with kubectl and AWS CLI installed
* EKS configuration file prepared
* Application manifest files ready for deployment
* GitHub repository access for configuration management

5. High Level Steps
-------------------

| # | Phase | Task | Details |
| --- | --- | --- | --- |
| 1 | Deployment | Deploy EKS Cluster | Create EKS cluster using configuration file |
| 2 | Verification | Verify EKS Cluster Creation | Check cluster status and components in AWS Console |
| 3 | Access | Configure EKS Access | Add jump server IAM role to cluster access |
| 4 | Setup | Setup Jump Server Access | Configure kubectl context and verify connectivity |
| 5 | Deployment | Deploy Applications | Deploy applications using manifest files |
| 6 | Testing | Verify Application Deployment | Test application functionality and connectivity |
| 7 | Integration | Azure API Implementation | Configure Azure API connectivity |

6. EKS Configuration
--------------------

### 6.1 EKS Cluster Configuration Analysis

**Configuration File**: `platform.cloud-engineering-eks/config/guiding-care/guiding-care-dev-config.yaml`

| Component | Configuration | Notes |
| --- | --- | --- |
| **Cluster Name** | `gc-infraops-eks-cluster-perf-use1` | Follows naming convention |
| **Kubernetes Version** | `1.32` | Latest supported version |
| **Endpoint Access** | `private` | VPC-only access for security |
| **Node Group** | `general-purpose` with `m7i.xlarge` | 3-10 nodes, ON\_DEMAND |
| **Add-ons** | VPC CNI, CoreDNS, Kube-proxy, EFS CSI, ALB Controller | Essential cluster components |
| **Security** | IRSA enabled, Admin role configured | Service account authentication |
| **Monitoring** | Container Insights, Log forwarding | CloudWatch integration |

### 6.2 Key Configuration Elements


```yaml
cluster_name: "gc-infraops-eks-cluster-dev-use1"
kubernetes_version: "1.32"
region: "us-east-1"
account_id: "<ACCOUNT_ID>"

vpc_config:
  vpc_id: "<VPC_ID>"

control_plane_config:
  endpoint_access: "private"
  logging_types: ["api", "audit", "authenticator"]

node_groups:
  - name: "general-purpose"
    instance_types: ["m7i.xlarge"]
    min_size: 3
    max_size: 10
    desired_size: 3
    capacity_type: "ON_DEMAND"
    auto_update_node_group_version: false

addons:
  - name: "vpc-cni"
    version: "v1.19.0-eksbuild.1"
  - name: "coredns"
    version: "v1.11.3-eksbuild.2"
  - name: "kube-proxy"
    version: "v1.32.0-eksbuild.2"
  - name: "aws-efs-csi-driver"
    version: "v2.1.0-eksbuild.1"
  - name: "aws-load-balancer-controller"
    version: "v2.14.1"

security_config:
  enable_irsa: true
  admin_role_arn: "<ADMIN_ROLE_ARN>"
  iam_roles:
    - name: "alb-controller-role"
      service_account: "aws-load-balancer-controller"
      namespace: "kube-system"
      policies: []

autoscaling_config:
  cluster_autoscaler: true
  horizontal_pod_autoscaler: true
  metrics_server: true

monitoring_config:
  enable_container_insights: true
  enable_log_forwarding: true
  log_retention_days: 7

tags:
  BusinessUnit: "GuidingCare"
  Environment: "Development"
  DataClassification: "Clear"
  ComplianceScope: "None"
  Customer: "GuidingCare"
  Application: "EKS"
  Service: "EKS"
  Version: "1.0"
  Project: "GuidingCare EKS Dev"
  DRS: "False"
  Backup: "NotRequired"
  Owner: "gc_infrastructure@healthedge.com"
```


### 6.3 Application Container Configuration

**Key Features**:

* **ECR Container Images**: All applications use ECR registry `<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com`

  + `docio:latest`
  + `authdelivery:latest`
  + `connectedapp:latest`
  + `benefitpredictor:latest`
* **IRSA Integration**: Each service uses dedicated service accounts with IAM role annotations
* **TLS Certificate Mounting**: Wildcard certificate (\*.guidingcare.com) mounted at `/etc/tls/`
* **DocumentDB CA Bundle**: Global bundle mounted at `/opt/certs/` with lifecycle hook
* **Environment Variables**: App Insights, Cognito, and shared secrets configured

**Container Lifecycle Hook**:


```yaml
lifecycle:
  postStart:
    exec:
      command:
      - sh
      - -c
      - |
        cp /opt/certs/global-bundle.pem /usr/local/share/ca-certificates/docdb.crt
        update-ca-certificates
```


### 6.4 ALB Ingress Configuration

**Ingress Setup**: The Application Load Balancer (ALB) is configured as an internal load balancer with path-based routing for all four microservices.

**Key ALB Annotations**:


```yaml
annotations:
  alb.ingress.kubernetes.io/scheme: internal                    # Internal ALB (VPC only)
  alb.ingress.kubernetes.io/target-type: ip                     # Direct pod IP targeting
  alb.ingress.kubernetes.io/certificate-arn: <CERTIFICATE_ARN>
  alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS": 443}]'    # HTTPS only on port 443
  alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS13-1-2-2021-06  # TLS 1.3 security
  alb.ingress.kubernetes.io/success-codes: '200-404'            # Health check accepts 200-404
  alb.ingress.kubernetes.io/backend-protocol: HTTPS             # Backend uses HTTPS
  alb.ingress.kubernetes.io/backend-protocol-version: HTTP1     # HTTP/1.1 protocol
  alb.ingress.kubernetes.io/tags: 'BusinessUnit=GuidingCare,Owner=gc_infrastructure@example.com,Environment=Development,DataClassification=Internal,ComplianceScope=None,Service=EKS,Version=1.0'
```


**Path-Based Routing**:

* `/docio/v1/*` → docio service
* `/authdelivery/v1/*` → authdelivery service
* `/connectedapp/v1/*` → connectedapp service
* `/benefitpredictor/v1/*` → benefitpredictor service

**DNS Configuration**:

* **Performance**: `gcapi-perf-test.guidingcare.com`
* **Development**: `gcapi-dev-test.guidingcare.com`

### 6.5 Deploy Using GitHub Actions

**Deploy EKS Cluster via GitHub Actions**:

* Go to GitHub repository: `platform.cloud-engineering-eks`
* Navigate to **Actions** tab
* Select **Deploy** workflow
* Click **Run workflow**
* Configure parameters:

  + **Branch**: `main`
  + **Configuration file path**: `config/guiding-care/guiding-care-perf-config.yaml`
  + **AWS Region**: `us-east-1`
  + **Environment**: `performance`
  + **Action to perform**: `deploy`
  + **AWS Account ID**: `<ACCOUNT_ID>`
* Click **Run workflow**

7. Detailed Implementation Steps
--------------------------------

### 7.1 Deploy EKS Cluster

1. **Navigate to EKS Configuration Directory**:

   
```bash
cd platform.cloud-engineering-eks/config/guiding-care/
```

2. **Review Configuration File**:

   
```bash
cat guiding-care-perf-config.yaml
```

3. **Deploy EKS Cluster via GitHub Actions**:

   * Go to GitHub repository: `platform.cloud-engineering-eks`
   * Navigate to **Actions** tab
   * Select **Deploy EKS** workflow
   * Click **Run workflow**
   * Configure parameters:

     + **Branch**: `main`
     + **Configuration file**: `config/guiding-care/guiding-care-perf-config.yaml`
     + **AWS Region**: `us-east-1`
     + **Environment**: `performance`
     + **Action**: `deploy`
     + **AWS Account ID**: `<ACCOUNT_ID>`
   * Click **Run workflow**
4. **Monitor Deployment Progress**:

   * Monitor GitHub Actions workflow execution
   * Deployment typically takes 15-20 minutes
   * Verify no errors in workflow logs

### 7.2 Verify EKS Cluster Creation

1. **Check EKS Cluster in AWS Console**:

   * Navigate to **EKS** service in AWS Console
   * Region: **us-east-1**
   * Verify cluster: `gc-infraops-eks-cluster-perf-use1`
   * Status should be: **Active**
2. **Verify Cluster Components**:

   * **Compute**: Check node group `general-purpose` is active
   * **Add-ons**: Verify all add-ons are active and healthy
   * **Networking**: Confirm VPC and subnet configuration
   * **Logging**: Check CloudWatch log groups are created
3. **Verify Node Group Status**:

   * Node group: `general-purpose`
   * Instance type: `m7i.xlarge`
   * Desired capacity: `3`
   * Status: **Active**
   * Auto Scaling Group: Verify ASG is created
4. **Verify Add-ons Status**:

   * **VPC CNI**: Status should be **Active**
   * **CoreDNS**: Status should be **Active**
   * **Kube-proxy**: Status should be **Active**
   * **EFS CSI Driver**: Status should be **Active**
   * **AWS Load Balancer Controller**: Status should be **Active**
   * Check versions match configuration file requirements

### 7.3 Configure EKS Access

1. **Identify Jump Server IAM Role**:

   
```bash
# Get gc-eks-jumpserver instance profile
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=gc-eks-jumpserver" \
  --query 'Reservations[*].Instances[*].IamInstanceProfile.Arn' \
  --region us-east-1
```

2. **Add Jump Server Role to EKS Access**:

   * Navigate to **EKS** → **Clusters** → `gc-infraops-eks-cluster-perf-use1`
   * Go to **Access** tab
   * Click **Create access entry**
   * Configure access entry:

     + **Principal ARN**: `<JUMP_SERVER_ROLE_ARN>`
     + **Type**: `Standard`
     + **Username**: `jump-server-admin`
     + **Groups**: `system:masters`
   * Click **Create**
3. **Associate Cluster Admin Policy**:

   * Select the created access entry
   * Click **Associate policy**
   * Select: **AmazonEKSClusterAdminPolicy**
   * Click **Associate**

### 7.4 Setup Jump Server Access

1. **Connect to Jump Server**:

   
```bash
# Connect via EC2 Console Session Manager (recommended)
Navigate to EC2 → Instances → Select gc-eks-jumpserver → Connect → Session Manager

# Or SSH connection (if configured)
ssh -i <key-file> ec2-user@<gc-eks-jumpserver-ip>

# Or PuTTY connection (Windows)
# Use PuTTY with .ppk private key file
# Host: <gc-eks-jumpserver-ip>
# Connection → SSH → Auth → Browse for .ppk file
# Login as: ec2-user
```

2. **Update kubectl Context**:

   
```bash
# Update kubeconfig for EKS cluster
aws eks update-kubeconfig \
  --region us-east-1 \
  --name gc-infraops-eks-cluster-perf-use1
```

3. **Verify kubectl Access**:

   
```bash
# Test cluster connectivity
kubectl cluster-info

# Check nodes
kubectl get nodes

# Verify node status
kubectl get nodes -o wide

# Check system pods
kubectl get pods -n kube-system

# Verify add-ons
kubectl get pods -n kube-system | grep -E "(coredns|aws-load-balancer|vpc-cni)"
```

4. **Expected Output Verification**:

   
```bash
# Nodes should show Ready status
NAME                             STATUS   ROLES    AGE   VERSION
ip-10-x-x-x.ec2.internal        Ready    <none>   5m    v1.32.0-eks-xxxxx
ip-10-x-x-x.ec2.internal        Ready    <none>   5m    v1.32.0-eks-xxxxx
ip-10-x-x-x.ec2.internal        Ready    <none>   5m    v1.32.0-eks-xxxxx
```


### 7.5 Deploy Applications via Jump Server

**Note**: Login to the gc-eks-jumpserver and switch to root user before proceeding with application deployment.

1. **Navigate to Manifest Directory**:

   
```bash
cd /root/eks-manifests
```

2. **Review Available Environments**:

   
```bash
ls -la
# Should show: dev/ perf/
```


   **Folder Structure**:

   
```
eks-manifests/
├── dev/
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── setup-ca-bundle.sh
│   ├── ingress.yaml
│   ├── docio/
│   │   ├── service-account.yaml (uses GC-InfraOps-EKS-Dev-MultiService-Role)
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── authdelivery/
│   │   ├── service-account.yaml (uses GC-InfraOps-EKS-Dev-MultiService-Role)
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── connectedapp/
│   │   ├── service-account.yaml (uses GC-InfraOps-EKS-Dev-MultiService-Role)
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── benefitpredictor/
│       ├── service-account.yaml (uses GC-InfraOps-EKS-Dev-MultiService-Role)
│       ├── deployment.yaml
│       └── service.yaml
└── perf/
    ├── namespace.yaml
    ├── secrets.yaml
    ├── setup-ca-bundle.sh
    ├── ingress.yaml
    ├── docio/
    │   ├── service-account.yaml (uses GC-InfraOps-EKS-Perf-MultiService-Role)
    │   ├── deployment.yaml
    │   └── service.yaml
    ├── authdelivery/
    │   ├── service-account.yaml (uses GC-InfraOps-EKS-Perf-MultiService-Role)
    │   ├── deployment.yaml
    │   └── service.yaml
    ├── connectedapp/
    │   ├── service-account.yaml (uses GC-InfraOps-EKS-Perf-MultiService-Role)
    │   ├── deployment.yaml
    │   └── service.yaml
    └── benefitpredictor/
        ├── service-account.yaml (uses GC-InfraOps-EKS-Perf-MultiService-Role)
        ├── deployment.yaml
        └── service.yaml
```

3. **Configure Multiple Cluster Contexts**:

   
```bash
# Add dev cluster context
aws eks update-kubeconfig \
  --region us-east-1 \
  --name gc-infraops-eks-cluster-dev-use1 \
  --alias dev

# Add perf cluster context  
aws eks update-kubeconfig \
  --region us-east-1 \
  --name gc-infraops-eks-cluster-perf-use1 \
  --alias perf

# Verify contexts
kubectl config get-contexts
```

4. **Deploy Performance Environment Applications**:

   
```bash
# Switch to perf cluster context
kubectl config use-context perf

# Deploy all at once
kubectl apply -f perf/ --recursive

# Or in specific order for better visibility:
kubectl apply -f perf/namespace.yaml
kubectl apply -f perf/secrets.yaml
kubectl apply -f perf/docio/
kubectl apply -f perf/authdelivery/
kubectl apply -f perf/connectedapp/
kubectl apply -f perf/benefitpredictor/
kubectl apply -f perf/ingress.yaml
```

5. **Deploy Development Environment Applications**:

   
```bash
# Switch to dev cluster context
kubectl config use-context dev

# Deploy all at once
kubectl apply -f dev/ --recursive

# Or in specific order for better visibility:
kubectl apply -f dev/namespace.yaml
kubectl apply -f dev/secrets.yaml
kubectl apply -f dev/docio/
kubectl apply -f dev/authdelivery/
kubectl apply -f dev/connectedapp/
kubectl apply -f dev/benefitpredictor/
kubectl apply -f dev/ingress.yaml
```

6. **Redeploy Applications (Clean Restart)**:

   
```bash
# For dev environment
kubectl config use-context dev

# Delete all existing resources
kubectl delete -f dev/ --recursive

# Deploy everything fresh
kubectl apply -f dev/ --recursive

# For perf environment
kubectl config use-context perf

# Delete all existing resources
kubectl delete -f perf/ --recursive

# Deploy everything fresh
kubectl apply -f perf/ --recursive
```

7. **Update Applications Without Deleting**:

   
```bash
# Switch to desired cluster
kubectl config use-context dev  # or perf

# Update all resources (applies changes only)
kubectl apply -f dev/ --recursive  # or perf/

# Restart all pods to pick up changes
kubectl rollout restart deployment -n api-ingress-basic
```

8. **Verify Application Deployment**:

   
```bash
# Check deployments
kubectl get deployments

# Check pods
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# Check pod logs
kubectl logs -f <pod-name>
```

9. **Monitor Application Status**:

   
```bash
# Watch pod status
kubectl get pods -n api-ingress-basic -w

# Describe problematic pods
kubectl describe pod <pod-name> -n api-ingress-basic

# Check events in namespace
kubectl get events -n api-ingress-basic --sort-by=.metadata.creationTimestamp

# Check ALB ingress status
kubectl describe ingress gc-api-ingress -n api-ingress-basic
```

10. **Debug Applications Using Exec**:

    
```bash
# Get shell access to running pod
kubectl exec -it <pod-name> -n api-ingress-basic -- /bin/bash

# Or use sh if bash is not available
kubectl exec -it <pod-name> -n api-ingress-basic -- /bin/sh

# Execute specific commands in pod
kubectl exec <pod-name> -n api-ingress-basic -- ls -la /app
kubectl exec <pod-name> -n api-ingress-basic -- cat /app/appsettings.json
kubectl exec <pod-name> -n api-ingress-basic -- env | grep -i db

# Check certificate files
kubectl exec <pod-name> -n api-ingress-basic -- ls -la /etc/tls/
kubectl exec <pod-name> -n api-ingress-basic -- ls -la /opt/certs/

# Test internal connectivity
kubectl exec <pod-name> -n api-ingress-basic -- curl -k https://localhost:443/health
```

11. **Verify ALB and DNS Configuration**:

    
```bash
# Get ALB DNS name from ingress
kubectl get ingress gc-api-ingress -n api-ingress-basic -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Test application endpoints
curl -k https://gcapi-perf-test.guidingcare.com/docio/v1/health
curl -k https://gcapi-perf-test.guidingcare.com/authdelivery/v1/health
curl -k https://gcapi-perf-test.guidingcare.com/connectedapp/v1/health
curl -k https://gcapi-perf-test.guidingcare.com/benefitpredictor/v1/health
```


8. Azure API Implementation
---------------------------

### 8.1 Azure API Configuration

**Note**: Azure API implementation details will be configured by the respective GC application teams based on specific API requirements.

### 8.2 Common Azure API Integration Steps

1. **Azure Service Principal Setup**:

   * Create Azure service principal for API access
   * Configure authentication credentials
   * Store credentials in Kubernetes secrets
2. **API Connectivity Configuration**:

   * Configure network connectivity to Azure endpoints
   * Set up SSL/TLS certificates if required
   * Configure firewall rules and security groups
3. **Application Configuration**:

   * Update application configuration for Azure API endpoints
   * Configure authentication mechanisms
   * Set up retry and timeout policies

9. Monitoring and Troubleshooting
---------------------------------

### 9.1 EKS Cluster Monitoring

1. **CloudWatch Container Insights**:

   * Navigate to **CloudWatch** → **Container Insights**
   * Select cluster: `gc-infraops-eks-cluster-perf-use1`
   * Monitor cluster, node, and pod metrics
2. **EKS Cluster Logs**:

   * **Log Groups**: `/aws/eks/gc-infraops-eks-cluster-perf-use1/cluster`
   * **Log Types**: API server, audit, authenticator
3. **Common kubectl Commands**:

   
```bash
# Check cluster status
kubectl cluster-info

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check pod status
kubectl get pods --all-namespaces
kubectl describe pod <pod-name> -n <namespace>

# Check logs
kubectl logs <pod-name> -n <namespace>
kubectl logs -f <pod-name> -n <namespace>

# Check events
kubectl get events -n <namespace>
```


### 9.2 Troubleshooting Common Issues

1. **Pod Scheduling Issues**:

   
```bash
# Check node resources
kubectl describe nodes
kubectl top nodes

# Check pod resource requests
kubectl describe pod <pod-name>
```

2. **Authentication Issues**:

   
```bash
# Check service account
kubectl get serviceaccount
kubectl describe serviceaccount <sa-name>
```


10. Lessons Learnt/Known Issues
-------------------------------

1. **Private Endpoint Access**: EKS clusters with private endpoint access require jump server or VPN connectivity. Ensure jump server has proper IAM roles and network access.
2. **Ingress and Service Configuration**: Verify that ingress resources reference the correct ClusterIP service names and ports. Mismatched service names in ingress configuration will result in 503 Service Unavailable errors. Use `kubectl get services` and `kubectl describe ingress` to validate service-to-ingress mapping.
3. **Add-on Version Compatibility**: Ensure add-on versions are compatible with the Kubernetes version. Use AWS documentation to verify compatibility matrix.
4. **IAM Roles for Service Accounts (IRSA) Configuration**: Enable IRSA for secure pod-level AWS service access. Ensure the EKS cluster has an OIDC identity provider configured. The trust relationship in IAM roles must include the OIDC provider URL and specify the correct namespace and service account in the condition. Example trust policy for multi-service role:

   
```json
{
  "Version": "October 17, 2012",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/oidc.eks.<REGION>.amazonaws.com/id/<CLUSTER_ID>"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.<REGION>.amazonaws.com/id/<CLUSTER_ID>:aud": "sts.amazonaws.com",
          "oidc.eks.<REGION>.amazonaws.com/id/<CLUSTER_ID>:sub": [
            "system:serviceaccount:api-ingress-basic:docio-service-account",
            "system:serviceaccount:api-ingress-basic:authdelivery-service-account",
            "system:serviceaccount:api-ingress-basic:connectedapp-service-account",
            "system:serviceaccount:api-ingress-basic:benefitpredictor-service-account"
          ]
        }
      }
    }
  ]
}
```

5. **ALB Ingress Controller IAM Permissions**: Ensure the ALB controller IAM role has necessary permissions including `elasticloadbalancing:*`, `ec2:DescribeVpcs`, `ec2:DescribeSubnets`, `ec2:DescribeSecurityGroups`, `iam:CreateServiceLinkedRole`, and `wafv2:*` for WAF integration. Verify the service account annotation points to the correct IAM role ARN.
6. **Namespace-Specific IRSA**: When configuring IRSA, ensure the namespace specified in the trust relationship matches the actual namespace where the service account is deployed. Mismatched namespaces will cause authentication failures.
7. **Manifest Management**: Organize manifest files by environment and application. Use consistent naming and labeling for easier management and troubleshooting.