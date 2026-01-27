# 5.9 Transit Gateway Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867097666/5.9%20Transit%20Gateway%20Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Gary Edwards on August 26, 2025 at 08:51 PM

---

---

**Purpose**
-----------

Design and document Transit Gateway route tables.

**Transit Gateway Route Tables**
--------------------------------

The AWS Transit Gateway (TGW) supports up to 20 separate route tables. These route table serve as separate virtual routers for the VPCs associated with them. Each VPC can only be associated with one TGW route table. However, a VPC can propagate a route (to its own CIDR) to multiple TGW route tables. The route propagations provide reachability information to VPCs associated with the route tables receiving the propagated routes.

### Transit Gateway Routing

| TGW Route Table | Associations | Propagations | Static Routes | Notes |
| --- | --- | --- | --- | --- |
| Inspection | * Inspection VPC | * All VPCs * Advertised data center routes | * VPN Customer CIDRs | All traffic from the Inspection VPC destined to the Spoke VPCs, VPN customers, data centers, or another region is forwarded through this route table. |
| Spoke | * All Spoke VPCs * Customer Connections VPC * DXGW | * VpcEndpoints VPC * SharedServices VPC | * 0.0.0.0/0 to Inspection VPC * TGW Peer Connections | By default, this route table forwards all traffic to the Inspection VPC for inspection by the AWS Network Firewall. |

### **Inter-region Connectivity**

HealthEdge will implement a DR strategy that aligns with their RTO/RPO and will utilize Transit Gateway Peering to enable communication between AWS regions. A description of inter-region traffic flow is provided in 5.2 Network Data Flows.

### **Migration Traffic**

To avoid costs, traffic related to the migration on the path between the data centers and AWS is configured to bypass the TGW and NFW, flowing directly to the Staging subnet in the Migration account. A description of data center traffic flow is provided in 5.2 Network Data Flows.