# Runbook - HRP New Customer LZA Active Directory, DNS, Firewall

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5275943240/Runbook%20-%20HRP%20New%20Customer%20LZA%20Active%20Directory%2C%20DNS%2C%20Firewall

**Created by:** Chris Falk on November 26, 2025  
**Last modified by:** Chris Falk on November 26, 2025 at 03:27 PM

---

This runbook details the Landing Zone Accelerator (LZA) code changes required to implement an HRP customer’s Active Directory servers, DNS forwarding rules, and supporting firewall rules for AD and VPN traffic.

### 1. Deploy network resources

This runbook assumes that the [HRP platform CDK repository](https://github.com/HE-Core/platform.hrp-iac) has been used to deploy **application** and **database** subnets to the production and non-production VPC for this customer in their primary and DR regions.

### 2. Deploy AWS Active Directory server instances

Deploy three customer Active Directory EC2 instances to the production VPC application subnets (spanning three AZs), documenting IP addresses for later use. For non-partner deployments, also deploy a single Active Directory instance in one DR region application subnet.

### 3. Create LZA branch

Create a new branch in the LZA repository titled `feature/hrp-cust-<code>-addns-resources` where `<code>` is the customer code such as `MCHO`.

### 4. Create IPSets entries in network-config.yaml

Create the following IPSets in each region under the `# common to all regions` sections in `network-config.yaml`:

* `HRP_CUST_<CODE>_PROD` = all production AWS customer CIDRs in primary and DR regions
* `HRP_CUST_<CODE>_NONPROD` = all non-production AWS customer CIDRs in primary and DR regions
* `HRP_CUST_<CODE>_AD` = all customer AD server IPs in both AWS and on-prem
* `HRP_CUST_VPN_<CODE>` = customer side of VPN tunnel CIDRs

Region-specific examples:


```yaml
# HRP Customer VPN CIDRs
- name: HRP_CUST_VPN_ALH
  definition: ['162.95.224.0/21','162.95.232.0/21','162.95.240.0/20']
# HRP Customer AD servers
- name: HRP_CUST_ALH_AD
  definition: ['10.229.0.81', '10.229.0.213', '10.229.0.148', '172.29.38.11', '172.29.38.12']
# HRP Customer VPC Subnet CIDRs
- name: HRP_CUST_ALH_PROD
  definition: ['10.229.0.64/26','10.229.0.192/26','10.229.0.128/26','10.229.1.16/28','10.229.0.48/28','10.229.1.0/28']
- name: HRP_CUST_ALH_NONPROD
  definition: ['10.225.1.192/26', '10.225.1.128/26', '10.225.0.64/26', '10.225.2.0/28', '10.225.1.96/28', '10.225.1.112/28']
```


### 5. Create firewall rules for AD and customer VPN traffic

Create the following firewall rules entries in `BaselineFirewallRuleGroup.txt`:

* Active Directory traffic from non-production CIDRs to AWS AD servers
* Active Directory traffic to/from on-prem and AWS AD servers
* Customer VPN traffic from customer VPN CIDRs to prod and nonprod subnets

Example:


```
pass tcp $HRP_CUST_ALH_NONPROD any -> $HRP_CUST_ALH_AD $AD_TCP (flow:established; msg:"ALH NonProd to Prod AD server TCP communication"; sid:20500;)
pass udp $HRP_CUST_ALH_NONPROD any -> $HRP_CUST_ALH_AD $AD_UDP (msg:"ALH NonProd to Prod AD server UDP communication"; sid:20501;)
pass tcp $HRP_CUST_ALH_AD any -> $HRP_CUST_ALH_AD $AD_TCP (flow:established; msg:"ALH AD to AD server TCP communication"; sid:20700;)
pass udp $HRP_CUST_ALH_AD any -> $HRP_CUST_ALH_AD $AD_UDP (msg:"ALH AD to AD server UDP communication"; sid:20701;)
pass tcp $HRP_CUST_VPN_ALH any -> [$HRP_CUST_ALH_NONPROD,$HRP_CUST_ALH_PROD] $HRP_CUSTOMER_PORTS (flow:established; msg:"ALH customer VPN traffic to ALH subnets"; sid:21000; )
```


### 6. Create Route53 forwarding rules

To support resolution of customer AD DNS via the Route53 Resolver service using outbound resolver endpoints, create Route53 forwarding rules for each regional outbound endpoint in `network-config.yaml` targeting the on-premise AD servers initially. Watch out for the naming scheme; make sure it reflects the region and domain components.


```
- domainName: alh.local
  name: he-prod-r53-fwd-use1-alh-local
  shareTargets:
    organizationalUnits:
      - Root
  targetIps:
    - ip: 172.29.38.11 #onprem
    - ip: 172.29.38.12 #onprem
```


### 7. Associate forwarding rules to VPCs

In `network-config.yaml`, associate the forwarding rule to the following VPCs and VPC templates in the customer production and DR regions:

* Network Endpoints VPCs
* Production workload VPC templates
* VPN production workload VPC templates
* Nonproduction workload VPC templates
* VPN nonproduction workload VPC templates


```yaml
# NetworkEndpoints VPC (us-east-1)
- name: NetworkEndpointsVpcUsEast1
  account: Network
  region: us-east-1
  ipamAllocations:
    - ipamPoolName: us-east-1-infrastructure
      netmaskLength: 22
  enableDnsHostnames: true
  enableDnsSupport: true
  instanceTenancy: default
  internetGateway: false
  resolverRules:
    - he-prod-r53-fwd-use1-healthedge-biz
    - he-prod-r53-fwd-use1-altruistahealth-net
    - he-prod-r53-fwd-use1-hq-he-com
    - he-prod-r53-fwd-use1-idm-he-biz
    - he-prod-r53-fwd-use1-alh-local
    - he-prod-r53-fwd-use1-axm-local
    - he-prod-r53-fwd-use1-citi-local
    - he-prod-r53-fwd-use1-frso-local
```


### 8. Merge branch and run pipeline

After PR review and firewall change approval by the security team, merge the branch to release the pipeline and deploy the changes.

### 9. Join AWS AD servers to the domain and DCPROMO

Using `nslookup`, confirm you can successfully resolve the customer domain e.g. `aha.local` and the request returns the list of AD/DNS name servers for the domain.

Create two new AD Sites and Services sites, one for the primary region and one for DR. Join the AD servers to the domain, install AD services, and promote them to domain controllers.

### 10. Update forwarding rules to use AWS AD servers

Create a new branch. Update the forwarding rules in `network-config.yaml` to target the AWS AD servers for each region, primary and DR if applicable. After approval, merge and deploy the PR.

Verify DNS resolution still functions as expected after the change.