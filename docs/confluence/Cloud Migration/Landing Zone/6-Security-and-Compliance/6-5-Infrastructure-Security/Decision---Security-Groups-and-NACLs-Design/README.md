# Decision---Security-Groups-and-NACLs-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065303/Decision---Security-Groups-and-NACLs-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:34 AM

---

### Document Lifecycle Status

**Purpose**
-----------

This document outlines Security Groups and Network Access Control Lists which will be deployed in AWS accounts. It is Well-Architected best practice to define network protection requirements, to control traffic at all layers and to limit the exposure of workloads to the internet and internal networks by only allowing the minimum required access. [Customer] will use Security Groups as virtual firewalls to control network access to AWS resources. Network Access List will be used to explicitly block malicious traffic.

AWS SGs/NACLs provide the following capabilities and benefits:

1. Security Groups act as stateful firewalls and use connection tracking to track information about traffic to and from the instances.
2. Security group rules are always permissive and allow to control access based on IP, protocol, and port numbers.
3. Network ACLs are stateless and can either allow or deny traffic.
4. Network ACLs allow to control access based on IP, protocol, and port numbers.

**Implementation**
------------------

Define the Security Groups and NACLs using the below tables as starting points for discussion, replacing the necessary details based on requirements

#### Naming Convention

SG: <Namespace>-sg-<function>-<semantics> (<semantics> is optional)

NACL: <Namespace>-nacl-<function>-<semantics> (<semantics> is optional)

#### Global Security Groups

Global security groups can be shared among multiple resources and are designed to address most common access requirements.

| **Purpose** | **SG Name** | **Source** | **Protocol** | **Port Range** |
| --- | --- | --- | --- | --- |
| SSH access to EC2 instances | its-sg-remote-linux | \[Customer\] corp space | TCP | 22 |
| RDP access to EC2 instances | its-sg-remote-windows | \[Customer\] corp space | TCP | 3389  445  139  5985 |
| Isolation for contaminated EC2 instances | its-sg-isolated | N/A | N/A | N/A |
| Common-Windows(CheckMK, WMI,Nessus) | its-sg-common-windows | \[Customer\] corp space  \[Customer\] Shared-Services account space | TCP |  |
| Common-Linux(CheckMK,Nessus) | its-sg-common-linux | \[Customer\] corp space  \[Customer\] Shared-Services account space | TCP |  |
| Commvault Agent  \\*could be part of Common | its-sg-commclient | Commvault Server SG group or \[Customer\] corp space | TCP | 8400  8403 |

#### Applications Security Groups

Security Groups will be used to control access to all applications and access rules will be developed based on the specific needs of the applications.

Template:

Inbound



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<td>
<strong><span>Purpose</span></strong>

</td>
<td>
<strong><span>SG Name (example)</span></strong>

</td>
<td>
<strong><span>Source</span></strong>

</td>
<td>
<strong><span>Protocol</span></strong>

</td>
<td>
<strong><span>Port Range</span></strong>

</td>
</tr>
<tr>
<th rowspan="2">
<span>Internet facing load balancer</span>

</th>
<td>
<span>its-sg-banner-weblb</span>

</td>
<td>
<span>0.0.0.0/0</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>443</span>

</td>
</tr>
<tr>
<td>
<span>its-sg-banner-weblb</span>

</td>
<td>
<span>\[Customer\] internal space</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>80/443</span>

</td>
</tr>
<tr>
<th>
<span>Internet facing web server (behind LB)</span>

</th>
<td>
<span>its-sg-banner-instance</span>

</td>
<td>
<span>Bastion Host SG</span>

<span>Internet LB SG</span>

</td>
<td>
<span>TCP</span>

<span>TCP</span>

</td>
<td>
<span>22/3389</span>

<span>8080</span>

</td>
</tr>
<tr>
<th>
<span>Internal load balancer</span>

</th>
<td>
<span>its-sg-banner-applb</span>

</td>
<td>
<span>Web Server SG</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>80/443</span>

</td>
</tr>
<tr>
<th>
<span>Internal application servers</span>

</th>
<td>
<span>its-sg-app1-instance</span>

</td>
<td>
<span>Bastion Host SG</span>

<span>Internal LB SG</span>

</td>
<td>
<span>TCP</span>

<span>TCP</span>

</td>
<td>
<span>22/3389</span>

<span>8080</span>

</td>
</tr>
<tr>
<th>
<span>Internal databases</span>

</th>
<td>
<span>its-sg-app1-rds</span>

</td>
<td>
<span>App Servers SG</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>3306</span>

</td>
</tr>
<tr>
<th rowspan="3">
<span>Internal services</span>

</th>
<td>
<span>its-sg-tenable-instance</span>

</td>
<td>
<span>\[Customer\] internal space</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>443</span>

</td>
</tr>
<tr>
<td>
<span>its-sg-ldap-instance</span>

</td>
<td>
<span>\[Customer\] internal space</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>389</span>

</td>
</tr>
<tr>
<td>
<span>its-sg-backup-instance</span>

</td>
<td>
<span>Instance SG</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>8400,8401,8403</span>

</td>
</tr>
<tr>
<th>
<span>Bastion host</span>

</th>
<td>
<span>its-sg-bastion-instance</span>

</td>
<td>
<span>\[Customer\] public space</span>

</td>
<td>
<span>TCP</span>

</td>
<td>
<span>22/3389</span>

</td>
</tr>
</tbody>
</table>



By default, SG Outbound rules allow All traffic.

#### Network Access Lists

Initially, NACLs will be used to explicitly block specific traffic on a subnet level in cases such as:

* [Customer] have identified Internet IP addresses or ranges that are unwanted or potentially abusive;
* [Customer] needs to block malicious traffic during an active security incident;
* [Customer] needs to explicitly deny traffic to a sensitive subnet.

Template:

Inbound/Outbound



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>
<strong><span>Purpose</span></strong>

</th>
<th>
<strong><span>NACL Name (example)</span></strong>

</th>
<th>
<strong><span>Rule #</span></strong>

</th>
<th>
<strong><span>Source/Destination</span></strong>

</th>
<th>
<strong><span>Protocol</span></strong>

</th>
<th>
<strong><span>Port</span></strong>

</th>
<th>
<strong><span>Allow/Deny</span></strong>

</th>
</tr>
<tr>
<th rowspan="3">
<span>Block Known Malicious IPs</span>

</th>
<td rowspan="3">
<span>its-nacl-publicsubnet</span>

</td>
<td>
<span>100</span>

</td>
<td>
<span>Malicious IP</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>Deny</span>

</td>
</tr>
<tr>
<td>
<span>1000</span>

</td>
<td>
<span>0.0.0.0/0</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>Allow</span>

</td>
</tr>
<tr>
<td>
<span>\*</span>

</td>
<td>
<span>0.0.0.0/0</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>All</span>

</td>
<td>
<span>Deny</span>

</td>
</tr>
</tbody>
</table>

