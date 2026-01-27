# HRP DRS Staging VPC Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5371854850/HRP%20DRS%20Staging%20VPC%20Design

**Created by:** Venkata Kommuri on December 18, 2025  
**Last modified by:** Venkata Kommuri on December 19, 2025 at 05:43 PM

---

📊  **Subnet Design with /24 Staging Subnets**
---------------------------------------------

### **us-east-2 (Ohio) - DR Region**

* ✅ **3-AZ Support**: us-east-2a, us-east-2b, us-east-2c

### **us-west-1 (N. California) - DR Region**

* ✅ **2-AZ Support**: us-west-1a, us-west-1b

### **DRS Staging Subnets (3-AZ Distribution)**

*Purpose: DRS replication servers (300 servers capacity)*

| Subnet Name | Availability Zone | CIDR Allocation | Subnet Size | Usable IPs | Server Capacity |
| --- | --- | --- | --- | --- | --- |
| **StagingSubnet1** | us-east-2a (AZ 1) | IPAM /24 | /24 | 251 | 100 servers |
| **StagingSubnet2** | us-east-2b (AZ 2) | IPAM /24 | /24 | 251 | 100 servers |
| **StagingSubnet3** | us-east-2c (AZ 3) | IPAM /24 | /24 | 251 | 100 servers |

**Total DRS Capacity**: 753 usable IPs, 300 servers (40% efficiency)

### **Transit Gateway Subnets (3-AZ Cross-Account Connectivity)**

*Purpose: TGW attachments and cross-account routing*

| Subnet Name | Availability Zone | CIDR Allocation | Subnet Size | Usable IPs | Purpose |
| --- | --- | --- | --- | --- | --- |
| **TgwSubnet1** | us-east-2a (AZ 1) | IPAM /28 | /28 | 11 | TGW ENIs |
| **TgwSubnet2** | us-east-2b (AZ 2) | IPAM /28 | /28 | 11 | TGW ENIs |
| **TgwSubnet3** | us-east-2c (AZ 3) | IPAM /28 | /28 | 11 | TGW ENIs |

### **Management Subnets (3-AZ VPC Endpoints)**

*Purpose: VPC endpoints, monitoring, and management services*

| Subnet Name | Availability Zone | CIDR Allocation | Subnet Size | Usable IPs | Purpose |
| --- | --- | --- | --- | --- | --- |
| **MgmtSubnet1** | us-east-2a (AZ 1) | IPAM /28 | /28 | 11 | VPC Endpoints |
| **MgmtSubnet2** | us-east-2b (AZ 2) | IPAM /28 | /28 | 11 | VPC Endpoints |
| **MgmtSubnet3** | us-east-2c (AZ 3) | IPAM /28 | /28 | 11 | VPC Endpoints |

---

### **VPC Endpoints**

Create the following VPC endpoints in staging VPC account with appropriate security group rules to allow communication from recovery VPC and staging VPC on port 443:

1. Elastic Disaster Recovery
2. Amazon S3
3. AWS STS
4. Amazon EC2