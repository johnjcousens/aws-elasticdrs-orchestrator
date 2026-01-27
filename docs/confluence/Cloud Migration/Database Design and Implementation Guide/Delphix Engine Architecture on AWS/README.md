# Delphix Engine Architecture on AWS

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5176951276/Delphix%20Engine%20Architecture%20on%20AWS

**Created by:** Sai Krishna Namburu on October 17, 2025  
**Last modified by:** Sai Krishna Namburu on October 17, 2025 at 02:18 PM

---

![image-20251017-141841.png](images/image-20251017-141841.png)

* **Version requirements**

  + The replication target (AWS) must be on the **same or newer version** than the source (Azure).
  + Since the Azure engine is on **2025.1.0**, the target can be on **2025.1.0 or a higher version**.
* **Instance/Storage allocation**

  + AWS instance type chosen should provide required IOPS and throughput. (example: R6in.12xlarge 2 or R5b.12xlarge for 100k iops requirement)
  + Delphix provided AMI for the engine : <https://download.delphix.com/link/0e8f5f79-3bde-46c2-a0d4-70f17246f870>
  + Storage : EBS volumes of type gp3/io1 to achieve required performance with some headroom for surge.
* **Privilege requirements**

  + The user configured in the replication profile must have **administrative privileges** on both the source and target engines.

**Engine Deployment:**

**General inbound from the Delphix engine port allocation**

|  |  |  |
| --- | --- | --- |
| **Protocol** | **Port Number** | **Use** |
| TCP | 22 | SSH connections to the Delphix Engine |
| TCP | 80 | HTTP connections to the Delphix GUI |
| UDP | 161 | Messages from an SNMP Manager to the Delphix Engine |
| TCP | 443 | HTTPS connections to the Delphix Management Application |
| TCP | 8415 | Delphix Session Protocol connections from all DSP-based network services including Replication, SnapSync for Oracle, V2P, and the Delphix Connector. |
| TCP | 50001 | Connections from source and target environments for network performance tests via the Delphix CLI |

General outbound to the Delphix Engine port allocation
------------------------------------------------------

|  |  |  |
| --- | --- | --- |
| **Protocol** | **Port** | **Use** |
| TCP | 25 | Connection to a local SMTP server for sending email |
| TCP/UDP | 53 | Connections to local DNS servers |
| UDP | 123 | Connection to an NTP server |
| UDP | 162 | Sending SNMP TRAP messages to an SNMP Manager |
| TCP | 443 | HTTPS connections from the Delphix Engine to the Delphix Support upload server |
| TCP/UDP | 636 | Secure connections to an LDAP server |
| TCP | 8415 | Connections to a Delphix replication target |
| TCP | 50001 | Connections to source and target environments for network performance tests |

**​Engine and Target(VDB)**:

o        Round-trip latency should be <1 ms (ideally ~300 μs)

o        Keep the Delphix Engine on the **same subnet** as the target environment

* There should be no firewalls between the Delphix Engine and the target environment.

**Engine and Source DB host:**

o        ​Deploy in the **same VPC** and latency should be < 50 ms.