# GC - Wave 1 Details

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5142970448/GC%20-%20Wave%201%20Details

**Created by:** Marc Kaplan on October 02, 2025  
**Last modified by:** Kaitlin Wieand on October 02, 2025 at 07:29 PM

---

**Domain root**: [altruistahealth.net](http://altruistahealth.net)

**Naming convention**: Server names typically are [XXXX][XXX][XX]-[XXXX].altruistahealth.net

Where as each bracketed item is as follows left to right:

[XXXX][XXX][XX]-[XXXX] - Client acronym

[XXXX][XXX][XX]-[XXXX] - Service Type

[XXXX][XXX][XX]-[XXXX] - System numerical value

[XXXX][XXX][XX]-[XXXX] - Designated location

The Service Type legend is:

|  |  |
| --- | --- |
| APP | Application (IIS Server) |
| FCO | FICO Servers |
| LOD | Load Balancer |
| MON | Mongo Databases |
| MPM | Member Portal Mongo |
| PKT | Packet Generator Service |
| SPR | PROD Microsoft SQL Server |

Scaler Environment
------------------

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **Server** | **Migration Approach** | **OS** | **AWS Service** | **DC IP** | **AWS IP** |
| SCLRAPP01-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |
| SCLRAPP02-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |
| SCLRAPP03-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |
| SCLRAPP04-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |
| SCLRFCO02-LAX3 | Re-host |  | EC2 |  |  |
| sclrlod02-lax3 | Re-platform | Rocky 8.10 | ALB |  |  |
| sclrmonp01-lax3 | Rehost | Rocky 8.10 | EC2 |  |  |
| sclrmpmp01-lax3 | Re-host | Rocky 8.10 | EC2 |  |  |
| SCLRPKTSK01-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |
| SCLR-SPR03-LAX3 | Re-platform | Server 2022 Std | EC2 |  |  |
| SCLR-SPR04-LAX3 | Re-platform | Server 2022 Std | EC2 |  |  |

Index Environment
-----------------

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **Server** | **Migration Approach** | **On-Prem OS** | **AWS Service** | **DC IP** | **AWS IP** |
| GCIXAPPE01-IAD3 | Re-host | Server 2022 Std | EC2 |  |  |
| GCIXAPPE02-IAD3 | Re-host | Server 2022 Std | EC2 |  |  |
| GCIXAPPE03-IAD3 | Re-host | Server 2022 Std | EC2 |  |  |
| GCIXAPPE04-IAD3 | Re-host | Server 2022 Std | EC2 |  |  |
| GCIXFCOE01-IAD3 | Re-host | Rocky 8.10 | EC2 |  |  |
| GCIXLODE01-IAD3 | Re-platform | Rocky 8.10 | ALB |  |  |
| GCIXSQLE01-IAD3 | Re-platform | Server 2022 Std | EC2 |  |  |

Performance Environment 01
--------------------------

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **Server** | **Migration Approach** | **OS** | **AWS Service** | **DC IP** | **AWS IP** |
| gcpfappe01-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpfappe02-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpfappe03-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpfappe04-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpfdex01-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpffcoe01-iad3 | Re-host | Rocky 8.10 | EC2 |  |  |
| gcpflgae01-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflgae02-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflgae03-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflgae04-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflgae05-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflgae06-iad3 | Re-host | Server 2022 Std | EC2 |  |  |
| gcpflode01-iad3 | Re-platform | Rocky 8.10 | ALB |  |  |
| gcpfmone01-iad3 | Re-platform | Rocky 8.10 | EC2 |  |  |
| gcpfsqle01-iad3 | Re-platform | Server 2022 Std | EC2 |  |  |
| gcpfsqle02-iad3 | Re-platform | Server 2022 Std | EC2 |  |  |

Performance Environment 02
--------------------------

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| **Server** | **Migration Approach** | **OS** | **AWS Service** | **DC IP** | **AWS IP** |
| AHPERFCO01-LAX3 | Re-platform | CentOS 7.8.2003 | EC2 |  |  |
| ahsapp5-lax3 | Re-host | Server 2022 Std | EC2 |  |  |
| ahsapp6-lax3 | Re-host | Server 2022 Std | EC2 |  |  |
| ahsapp7-lax3 | Re-host | Server 2022 Std | EC2 |  |  |
| ahsapp8-lax3 | Re-host | Server 2022 Std | EC2 |  |  |
| ahspktp01-lax3 | Re-host | Server 2022 Std | EC2 |  |  |
| UNHGSQLE02-LAX3 | Re-host | Server 2022 Std | EC2 |  |  |