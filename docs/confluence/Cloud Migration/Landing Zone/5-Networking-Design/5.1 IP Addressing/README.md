# 5.1 IP Addressing

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5023367261/5.1%20IP%20Addressing

**Created by:** Gary Edwards on August 19, 2025  
**Last modified by:** Gary Edwards on November 11, 2025 at 05:14 PM

---

IP Addressing Scope
-------------------

HealthEdge has reserved CIDR 10.192.0.0/10 for their overall AWS IP addressing scope.  This CIDR block will be broken in half as follows to provide two /11 CIDRs:

* 10.192.0.0/11 - HealthEdge standard public facing workloads and shared infrastructure
* 10.224.0.0/11 - HealthEdge VPN customer workloads

**NOTE:** The 10.224.0.0/11 CIDR overlaps with the IP space currently in use within the HealthEdge data centers. However, this is not an issue since this CIDR will not be advertised across the data center connections. Upon completion of the migration, the overlapping addresses will no longer be in use within the data centers.

Standard Workloads and Shared Infrastructure
--------------------------------------------

CIDR 10.192.0.0/11 will be further broken down into 4 regional /13 CIDRs to accommodate HealthEdge’s current and future standard workload VPC and shared infrastructure networking requirements.

Within each regional /13 CIDR, a /16 CIDR is reserved for the shared infrastructure, and the remaining IP space is utilized for workload VPCs.

HealthEdge requires large VPCs to support their workloads. To accommodate this requirement, a default /19 mask is used for workload VPC assignments. This will allow for provisioning a total of up to 64 workload VPCs per region, each containing:

* 3 x /28 TGW subnets spanning 3 AZs to support Transit Gateway attachments
* 3 x /28 NFW subnets spanning 3 AZs to support NFW endpoints
* 3 x /22 public subnets spanning 3 AZs
* 3 x /22 private workload subnets spanning 3 AZs
* 3 x /23 private DB subnets spanning 3 AZs

This allocation scheme provides spare addressing for limited expansion within the VPC if necessary. Variations on this default can be allocated as needed to accommodate differing workload subnet and addressing requirements.

IP Address Allocation Scheme
----------------------------

The standard IP address allocation scheme is illustrated in the table below:



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="0f660296-4277-4bb0-8b3c-c83736b7631d" data-layout="center" data-table-width="1800"><tbody><tr><th rowspan="2"><strong>Region</strong></th><th rowspan="2"><strong>IP Pool</strong></th><th rowspan="2"><strong>VPC CIDR</strong></th><th colspan="3"><strong>Subnets / VPC</strong></th><th colspan="3"><strong>Hosts / Subnet</strong></th><th rowspan="2"><strong>VPCs</strong></th></tr><tr><td>/28</td><td>/23</td><td>/22</td><td>/28</td><td>/23</td><td>/22</td></tr><tr><td rowspan="5">us-east-1</td><td>10.192.0.0/13</td><td>10.192.0.0/19</td><td>32</td><td>3</td><td>6</td><td>11</td><td>507</td><td>1019</td><td rowspan="4">64</td></tr><tr><td>10.192.0.0/13</td><td>10.192.8.0/19</td><td>32</td><td>3</td><td>6</td><td>11</td><td>507</td><td>1019</td></tr><tr><td colspan="8">…</td></tr><tr><td>10.198.0.0/13</td><td>10.198.224.0/19</td><td>32</td><td>3</td><td>6</td><td>11</td><td>507</td><td>1019</td></tr><tr><td>10.199.0.0/16</td><td colspan="8">(Reserved for shared infrastructure)</td></tr><tr><td>us-east-2</td><td>10.200.0.0/13</td><td colspan="8">(Workloads and shared infrastructure)</td></tr><tr><td>us-west-1</td><td>10.208.0.0/13</td><td colspan="8">(Workloads and shared infrastructure)</td></tr><tr><td>us-west-2</td><td>10.216.0.0/13</td><td colspan="8">(Workloads and shared infrastructure)</td></tr></tbody></table>



VPN Customer Workloads
----------------------

The CIDR 10.224.0.0/11 is allocated for HealthEdge VPN customer workloads. As shown in the following table, this CIDR is broken down into 4 x /13 CIDRs to provide addressing for the VPN customers currently terminating at the 4 HealthEdge data centers.

| **Application** | **Data Center** | **CIDR** | **AWS Region** |
| --- | --- | --- | --- |
| HRP | HE1 | 10.224.0.0/13 | us-east-1 |
| HRP | HE2 | 10.232.0.0/13 | us-east-2 |
| Guiding Care | IAD | 10.240.0.0/13 | us-west-1 |
| Guiding Care | LAX | 10.248.0.0/13 | us-west-2 |

**NOTE:** To optimize network latency, customer VPNs may be migrated to a different region from the data center where they are currently connected depending on customer proximity.

The CIDR allocated to each region is split across the following production and non-production accounts.

* **GuidingCareVpnCustomerNonProduction** - this account will host all Guiding Care VPN customer non-production workloads.
* **GuidingCareVpnCustomerProduction** - this account will host all Guiding Care VPN customer production workloads.
* **HrpVpnCustomerNonProduction** - this account will host all HRP VPN customer non-production workloads.
* **HrpVpnCustomerProduction** - this account will host all HRP VPN customer production workloads.

The following table summarizes the CIDR allocations for each VPN customer account across all 4 regions.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="4e9b4f6d-3490-41dd-85f9-05a0763127b6" data-layout="align-start" data-table-width="1800"><tbody><tr><th rowspan="2"><strong>Region</strong></th><th rowspan="2"><strong>Regional</strong><br/><strong>CIDR</strong></th><th colspan="4"><strong>Account CIDR</strong></th></tr><tr><td><strong>GuidingCareVpnCustomerNonProduction</strong></td><td><strong>HrpVpnCustomerNonProduction</strong></td><td><strong>GuidingCareVpnCustomerProduction</strong></td><td><strong>HrpVpnCustomerProduction</strong></td></tr><tr><td>us-east-1</td><td>10.224.0.0/13</td><td>10.224.0.0/16</td><td>10.226.0.0/16</td><td>10.228.0.0/16</td><td>10.230.0.0/16</td></tr><tr><td>us-east-2</td><td>10.232.0.0/13</td><td>10.232.0.0/16</td><td>10.234.0.0/16</td><td>10.236.0.0/16</td><td>10.238.0.0/16</td></tr><tr><td>us-west-1</td><td>10.240.0.0/13</td><td>10.240.0.0/16</td><td>10.242.0.0/16</td><td>10.244.0.0/16</td><td>10.246.0.0/16</td></tr><tr><td>us-west-2</td><td>10.248.0.0/13</td><td>10.248.0.0/16</td><td>10.250.0.0/16</td><td>10.252.0.0/16</td><td>10.254.0.0/1</td></tr></tbody></table>



Network Address Translation
---------------------------

Network address translation (NAT) is utilized in order to accommodate the overlapping IP address space among HealthEdge VPN customers, This function is provided by the Palo Alto VM Series firewalls deployed in the Customer Connections VPC in each of the 4 regions. Each customer is allocated 2 x /24 subnets in the RFC 6598 CGNAT address space. The Palo Alto firewalls translate these subnets to corresponding /24 subnets from each of the /16 CIDRs allocated to the 4 accounts listed above.

IP Address Allocation Scheme
----------------------------

Using the following subnet sizes, the /16 CIDR allocated to each of the 4 accounts in each region will allow up to 256 customer workloads per account and support a total of 1024 production and non-production customer workloads spread across all 4 regions for both Guiding Care and HRP.

Each of the production and non-production accounts have a VPC with the following subnets spanning 3 availability zones:

* 3 x /28 TGW subnets spanning 3 AZs to support Transit Gateway attachments

In addition, each VPN customer hosted in each account is allocated the following subnets to support their workloads:

* 3 x /26 private workload subnets spanning 3 AZs
* 3 x /28 private DB subnets spanning 3 AZs

IP Address Management
---------------------

The AWS VPC IP Address Management (IPAM) service will be utilized to manage all of the IP address allocations for the AWS network. The following table summarizes the IPAM scopes and pools to support the network along with the OUs to which the pools will be shared.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="9d037eff-e6cb-4a4a-a6e7-5214eba93ff1" data-layout="align-start" data-table-width="1800"><tbody><tr><th><strong>IPAM Scope</strong></th><th><strong>Region</strong></th><th><strong>OU</strong></th><th><strong>IPAM Pools</strong></th></tr><tr><td rowspan="12">standard-workloads</td><td rowspan="3">us-east-1</td><td>Workloads/Non-Production</td><td><ul><li>10.192.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.196.0.0/15</li><li>10.198.0.0/16</li></ul></td></tr><tr><td>Infrastructure</td><td><ul><li>10.199.0.0/16</li></ul></td></tr><tr><td rowspan="3">us-east-2</td><td>Workloads/Non-Production</td><td><ul><li>10.200.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.204.0.0/15</li><li>10.206.0.0/16</li></ul></td></tr><tr><td>Infrastructure</td><td><ul><li>10.207.0.0/16</li></ul></td></tr><tr><td rowspan="3">us-west-1</td><td>Workloads/Non-Production</td><td><ul><li>10.208.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.212.0.0/15</li><li>10.214.0.0/16</li></ul></td></tr><tr><td>Infrastructure</td><td><ul><li>10.215.0.0/16</li></ul></td></tr><tr><td rowspan="3">us-west-2</td><td>Workloads/Non-Production</td><td><ul><li>10.216.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.220.0.0/15</li><li>10.222.0.0/16</li></ul></td></tr><tr><td>Infrastructure</td><td><ul><li>10.223.0.0/16</li></ul></td></tr><tr><td rowspan="8">vpn-customer-workloads</td><td rowspan="2">us-east-1</td><td>Workloads/Non-Production</td><td><ul><li>10.224.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.228.0.0/14</li></ul></td></tr><tr><td rowspan="2">us-east-2</td><td>Workloads/Non-Production</td><td><ul><li>10.232.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.236.0.0/14</li></ul></td></tr><tr><td rowspan="2">us-west-1</td><td>Workloads/Non-Production</td><td><ul><li>10.240.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.244.0.0/14</li></ul></td></tr><tr><td rowspan="2">us-west-2</td><td>Workloads/Non-Production</td><td><ul><li>10.248.0.0/14</li></ul></td></tr><tr><td>Workloads/Production</td><td><ul><li>10.252.0.0/14</li></ul></td></tr></tbody></table>

