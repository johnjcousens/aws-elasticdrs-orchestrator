# VM Configuration Management / DNS Changes

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5046665292/VM%20Configuration%20Management%20/%20DNS%20Changes

**Created by:** Kaitlin Wieand on August 26, 2025  
**Last modified by:** Brijesh Singh on August 27, 2025 at 09:19 PM

---

|  |  |
| --- | --- |
| **Driver** | Ted O'Hayer |
| **Approver** | Mark Mucha, Madhu Ravi, Joseph Branciforte, Brijesh Singh |
| **Contributors** | Marc Kaplan, Jim Fallon, Aslam Khan |
| **Informed** | Kaitlin Wieand, Jarrod Hermance, Aravind Rao, Cris Grunca |
| **Objective** | Templatize HRP and GuidingCare configs using Saltstack, ensure internal (east-west) components can connect to each other, update HRP customers to use DNS for north-south traffic |
| **Due date** | September 29, 2025 |
| **Key outcomes** | List expected outcomes and success metrics |
| **Status** | IN PROGRESSYellow |

Problem Statement
-----------------

Both HRP and GC systems currently use hardcoded IP addresses instead of DNS, creating operational risks. HRP faces higher exposure since they must communicate with external customers and deploy Windows desktop application updates, while GC's DNS issues are contained to internal systems. The planned solution involves replacing all hardcoded IPs with proper DNS entries to enable dynamic IP resolution by name rather than manual IP configuration.

Scope
-----

| **Must have:** | * Deployed production saltmaster * Templatize HRP and GuidingCare configs using Saltstack * Grains (metadata) for HRP and GC VMs * Ensure internal (east-west) components can connect to each other * Update HRP customers to use DNS for north-south traffic |
| --- | --- |
| **Nice to have:** | * Build Guidingcare and HRP from State files * Custom grains to query GC/HRP versions |
| **Not in scope:** | * Payor/GC CDK Stack * Payor Installation/Upgrades * Ad-hoc tasks driven by Salt * Zeta Integration   *These should be done as part of automation for net-new customers, but are not needed by 9/29* |

Next Steps & Questions:
-----------------------

We need an inventory of everything because we need to migrate everyone to DNS

1. Do we have the list of products for each product suite?
2. Do we know where to update DNS Names from IPs for each application under the product suite?
3. Do we know which products will work with IP to DNS changes and which won’t?
4. Do we have automation to replace the IPs with DNS for each product? If not, who owns this task, and which resources are assigned to do the work?

**HealthRules Payer:**
----------------------

* Payer
* Connector
* Answers-Info/Answers-AdHoc
* Load Balancer
* PIK
* Promote
* NextGen Accelerator
* IBM MQ
* CES
* CXT
* EASYGroup
* RateManager
* Provider Dirtectory
* PDM
* MRF-as-a-Service
* SmartComm
* iWay
* Inbound Proxy Servers
* Automations
* BitBucket/Git customer\_environment Properties
* HRP Client and properties in BitBucket/Git
* MoveIT Jobs / Hosts
* ELK/Filebeat config
* CMDB populations jobs
* IBM ILMT
* SolarWinds Monitoring

What Changes Need to Happen within HealthEdge
---------------------------------------------

1. Set up new VPN tunnels
2. Change all the entries using IP to use DNS
3. Provide new URLs to customers using DNS names for each environment
4. Build new clients, upload to SFTP, and communicate with customers - Coordination woith customer is needed
5. Communicate with Plan Connection and manage the work needed to update MQs.
6. Update firewall to reflect new IPs
7. ProxyServer Config changes
8. Update/restart DW replications - Coordination with the customer is needed
9. Provide new environemnt handoff documents with new URLs to customers

What Changes Need to Happen within the Customer Environment
-----------------------------------------------------------

1. Set up new VPN Tunnels
2. Create network tickets on their end to update the firewall
3. Make the firewall changes
4. Update endpoints/ URLs in all the applications
5. Update connectivity to DW servers
6. Deploy new clients based on the migration plan
7. Communicate to their stakeholders on new URLs
8. Definitely take care of RSO and DW repliation related n/w changes on the customer and HE end

**Changes Required When DNS Name Updates**
------------------------------------------

1. **TNS Configuration (tnsnames.ora / listener.ora):**

   * Update the **hostnames** in `tnsnames.ora` and `listener.ora` files to reflect the new DNS name.
   * Ensure the Oracle listener is restarted after changes.
2. **Application Connection Strings:**

   * Update any **application-level connection strings** or configuration files
3. **Delphix Configuration (if applicable):**

   * If Delphix is used to virtualize or manage the database, update the **environment configuration** in Delphix to point to the new DNS name.
4. **Firewall / Security Groups:**

   * Ensure that any **network rules or firewalls** allow traffic to the new DNS name.
5. **OEM Monitoring & Backup Tools:**

   * Update OEM **monitoring, backup, or automation scripts** that rely on the old IP addresses with DNS name.
6. **OS-Level Hostname Resolution:**

   * If `/etc/hosts` or similar files are used for static resolution, update them accordingly.

     + *Is there any domain overlap? Can we eliminate /etc/hosts and use internal DNS?*
7. **AWS to automate this** *Will they? Do we have a commitment?*

Associated Tickets
------------------

| **Ticket** | **Owner** | **Due Date** |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |

Milestones and deadlines - WIP
------------------------------

| **Milestone** | **Owner** | **Deadline** | **Status** |
| --- | --- | --- | --- |
| Discuss upcoming changes |  | August 27, 2025 | Not started |
| Review and approve changes for DNS | Approved Group | Type // to add a date | Not started |
| Create communication plan for customers | Kaitlin Wieand |  |  |
| Deliver plan for customers | CSE team |  |  |
| Coordinate with customer on changes | CSE team |  |  |
| Ensure changes line up with wave |  |  |  |

Communication Plan
------------------

Document changes for HealthEdge

Document changes for customers (differentiate between BUs if needed)

Deliver to CSE team

Related materials
-----------------

Type /database to create a database of relevant research, meetings, or any other key documents for this project