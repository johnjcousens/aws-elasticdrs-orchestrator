# AWS Internal Standup

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5077500105/AWS%20Internal%20Standup

**Created by:** Kaitlin Wieand on September 08, 2025  
**Last modified by:** Kaitlin Wieand on September 15, 2025 at 04:14 PM

---

none

AWS Internal Standup Notes
==========================

### **Date:** September 15, 2025

| Project/Component | BU | Status | Owner | Target Date | Action Items | Notes/Risks |
| --- | --- | --- | --- | --- | --- | --- |
| EKS | HRP | 🟢 On Track | Vaughn Sargent, Brijesh Singh | October 15, 2025 | 9/8 - AWS to set up 2 AWS clusters for HRP. (rancher being used in onprem)  9/11 - proposed solution was sent out, Vaughn to review early next week |  |
| Firewall | HRP | 🟢 On Track | Aravind Rao  Aslam Khan | October 04, 2025 | Need to follow up with Palo | 9/11 - still waiting on landing zone. AWS has already completed a couple VPCs. |
| SFTP Implementation | HRP | 🟡 Not Started | Brijesh Singh | TBD | 9/11 - Zak confirmed POC set up utilizing s3 + aws transfer/sftp services. Need Brijesh to identify next step.  9/15 - get a few people trained on AWS to check on POC.  Meet with AWS on how the managed SFTP works. | Ensure that it’s up and running and ready in the customer network. Aravind Rao, should provide input. |
| MoveIt Automation | HRP | 🔴 Blocked | Brijesh Singh | TBD | Vendor engagement, license procurement, AWS server setup  9/15 - on prem MoveIt. Dependent on SFTP server in each region. | 9/11 - KW to follow up with Brijesh on vendor engagement/license procurement. KW to start thread with Brijesh, Joe, Mucha and Emily.  soft requirement. |
| Local VLAN | HRP | 🟢 Complete | Aravind Rao | September 27, 2025 | 9/11 - Aravind to follow up with VPCs  9/12 - done | off track for 9/15, updated to 9/27 |
| Provisioning Automation | HRP | 🔴 Off Track | Brijesh Singh, Pardeep Soni | September 15, 2025 | 9/11 - Joseph S to set up call to discuss scope of work with DevOps team.  9/15 - Call scheduled for 9/16, need new date. | Heavy lift - missing deadline, needs staffing  9/11 - DevOps coding effort. Script to reconfigure, migrate server.  We will need to rewrite it to make compatible with AWS EC2 (AWS Native) |
| DNS/AD | HRP | 🟢 On Track | Todd Matton | September 27, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025  9/15 - Todd unblocked and can continue working on tasks. | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| AD | HRP | 🟢 On Track | Todd Matton | September 27, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025  Will need security to provision AWS management console for Todd. (AWS Identity Manager) | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. ConnManagement VLAN 3. Connectivity to Datacenter to perform DC promotions 4. OS Template with Windows 2025, and way to deploy to our account 5. IDM Requires RHEL 8 template |
| SMTP Relay | HRP | 🟢 On Track | Todd Matton  Jeff Rudolph | September 27, 2025 | Decision on shared email relay service  9/11 - route back into the HRP datacenter for day 1. Will schedule time in Q4 to discuss decision for day 2.  9/15 - KW to kick off thread with Jeff/Todd | Waiting for the decision on what will be used to relay mail in AWS. If no decision is made will continue to relay email through datacenter relays |
| Container Registry | HRP | ⚫ TBD | Swarna Kunnath, Ted O'Hayer, Brijesh Singh | October 10, 2025 | 9/12 - have a conversation with AWS. Use what Github has. | standardize in GitHub’s registry? Version sets.  ECR is good for container reg |
| Redhat satellite servers | HRP | 🟢 On Track | Todd Matton, Jim Fallon | October 01, 2025 | Use marketplace (provision on demand) comes with satellite license. **need to have conversation with finance** on getting a site license for going forward to bring the price down.  Todd to look at server count for the first couple phases.  9/15 - | redhat template being built, (checkbox on EC2). how to track this  Coupa for everything. |
| Ansible control servers | HRP | 🔴 Off Track | Brijesh Singh, Todd Matton | September 15, 2025 | 9/15 - PINIT-131. |  |
| Ansible control servers | HRP/GC |  |  |  |  |  |
| Jenkins server | HRP | 🟢 On track | Vaughn Sargent, Brijesh Singh | September 15, 2025 | 9/11 - KW to follow up on this | 9/8 - use on-prem as is to start, day 2 build new bots, jenkins and ansible control server in aws. |
| Jump servers | HRP | 🔴 Blocked | Todd Matton, Ted O'Hayer | September 15, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025 | Connecting to AWS Servers workshop - Teleport |
| Storage (DB servers) | HRP | ⚫ TBD | Kendra McCormick  Madhu Ravi | TBD | 9/11 - KW to follow up with Madhu on any necessary steps with using EBS | Do we have storage that will support the needed IOPS |
| Core Network connectivity | HRP | 🔴 Blocked | Aravind Rao, Brijesh Singh | September 27, 2025 | 9/11 - dependent on AWS |  |
| Redhat Identity Manager | HRP | 🟢 On Track | Todd Matton | September 15, 2025 | 9/11 - Dependent on AWS | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template     9/10 - Chris F to set up call |
| ConductorOne | HRP/GC | 🔴 Off track | Jarrod Hermance, Aslam Khan | September 15, 2025 | 9/11 - change in resourcing, haven’t defined or built out any roles with the help of AWS. Chris F is supporting atm.  KW to follow up. | requires to be set up in AWS first, actual work is easy.  determine all the teams with our internal teams and what they need access to in AWS. |
| ETL - CCDA | GC | ⚫ TBD | Anupama Sivasanker | October 15, 2025 |  |  |
| Storage - Container | GC | 🟢 On track | Ted O'Hayer | October 15, 2025 |  |  |
| Nexus | HRP | ⚫ TBD | Jim Fallon | TBD |  |  |
| IP/DNS config files / app investigation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |
| IP/DNS update Automation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |

### **Date:** September 11, 2025

| Project/Component | BU | Status | Owner | Target Date | Action Items | Notes/Risks |
| --- | --- | --- | --- | --- | --- | --- |
| EKS | HRP | 🟢 On Track | Vaughn Sargent, Brijesh Singh | October 15, 2025 | 9/8 - AWS to set up 2 AWS clusters for HRP. (rancher being used in onprem)  9/11 - proposed solution was sent out, Vaughn to review early next week |  |
| Firewall | HRP | 🟢 On Track | Aravind Rao  Aslam Khan | October 04, 2025 | Need to follow up with Palo | 9/11 - still waiting on landing zone. AWS has already completed a couple VPCs. |
| SFTP Implementation | HRP | 🟡 Not Started | Brijesh Singh | TBD | 9/11 - Zak confirmed POC set up utilizing s3 + aws transfer/sftp services. Need Brijesh to identify next step.  9/12 - get a few people trained on AWS to check on POC.  Meet with AWS on how the managed SFTP works. | Ensure that it’s up and running and ready in the customer network. Aravind Rao, should provide input. |
| MoveIt Automation | HRP | 🔴 Blocked | Brijesh Singh | TBD | Vendor engagement, license procurement, AWS server setup  9/12 - on prem MoveIt. Dependent on SFTP server in each region. | 9/11 - KW to follow up with Brijesh on vendor engagement/license procurement. KW to start thread with Brijesh, Joe, Mucha and Emily.  soft requirement. |
| Local VLAN | HRP | 🟢 Done | Aravind Rao | September 27, 2025 | 9/11 - Aravind to follow up with VPCs  9/12 - done | off track for 9/15, updated to 9/27 |
| Provisioning Automation | HRP | 🔴 Off Track | Brijesh Singh, Pardeep Soni | September 15, 2025 | 9/11 - Joseph S to set up call to discuss scope of work with DevOps team.  9/12 - Call scheduled for 9/16, need new date. | Heavy lift - missing deadline, needs staffing  9/11 - DevOps coding effort. Script to reconfigure, migrate server.  We will need to rewrite it to make compatible with AWS EC2 (AWS Native) |
| DNS/AD | HRP | 🟢 On Track | Todd Matton | September 27, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025  9/12 - Todd unblocked and can continue working on tasks. | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| AD | HRP | 🟢 On Track | Todd Matton | September 27, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025  Will need security to provision AWS management console for Todd. (AWS Identity Manager) | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. ConnManagement VLAN 3. Connectivity to Datacenter to perform DC promotions 4. OS Template with Windows 2025, and way to deploy to our account 5. IDM Requires RHEL 8 template |
| SMTP Relay | HRP | 🟢 On Track | Todd Matton  Jeff Rudolph | September 27, 2025 | Decision on shared email relay service  9/11 - route back into the HRP datacenter for day 1. Will schedule time in Q4 to discuss decision for day 2.  9/12 - KW to kick off thread with Jeff/Todd | Waiting for the decision on what will be used to relay mail in AWS. If no decision is made will continue to relay email through datacenter relays  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| Container Registry | HRP | ⚫ TBD | Swarna Kunnath, Ted O'Hayer, Brijesh Singh | October 10, 2025 | 9/12 - have a conversation with AWS. Use what Github has. | standardize in GitHub’s registry? Version sets. |
| Redhat satellite servers | HRP | 🟢 On Track | Todd Matton, Jim Fallon | October 01, 2025 | Use marketplace (provision on demand) comes with satellite license. **need to have conversation with finance** on getting a site license for going forward to bring the price down.  Todd to look at server count for the first couple phases.  9/15 - | redhat template being built, (checkbox on EC2). how to track this  Coupa for everything. |
| Ansible control servers | HRP | 🔴 Off Track | Brijesh Singh, Todd Matton | September 15, 2025 | 9/15 - PINIT-131. |  |
| Ansible control servers | HRP/GC |  |  |  |  |  |
| Jenkins server | HRP | 🟢 On track | Vaughn Sargent, Brijesh Singh | September 15, 2025 | 9/11 - KW to follow up on this | 9/8 - use on-prem as is to start, day 2 build new bots, jenkins and ansible control server in aws. |
| Jump servers | HRP | 🔴 Blocked | Todd Matton, Ted O'Hayer | September 15, 2025 | 9/11 - AWS to build out shared services (HRP specific) VPC. Todd to get access, networking/routing ‘should’ be ready by September 16, 2025 | Connecting to AWS Servers workshop - Teleport |
| Storage (DB servers) | HRP | ⚫ TBD | Kendra McCormick  Madhu Ravi | TBD | 9/11 - KW to follow up with Madhu on any necessary steps with using EBS | Do we have storage that will support the needed IOPS |
| Core Network connectivity | HRP | 🔴 Blocked | Aravind Rao, Brijesh Singh | September 27, 2025 | 9/11 - dependent on AWS |  |
| Redhat Identity Manager | HRP | 🟢 On Track | Todd Matton | September 15, 2025 | 9/11 - Dependent on AWS | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template     9/10 - Chris F to set up call |
| ConductorOne | HRP/GC | 🔴 Off track | Jarrod Hermance, Aslam Khan | September 15, 2025 | 9/11 - change in resourcing, haven’t defined or built out any roles with the help of AWS. Chris F is supporting atm.  KW to follow up. | requires to be set up in AWS first, actual work is easy.  determine all the teams with our internal teams and what they need access to in AWS. |
| ETL - CCDA | GC | ⚫ TBD | Anupama Sivasanker | October 15, 2025 |  |  |
| Storage - Container | GC | 🟢 On track | Ted O'Hayer | October 15, 2025 |  |  |
| Nexus | HRP | ⚫ TBD | Jim Fallon | TBD |  |  |
| IP/DNS config files / app investigation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |
| IP/DNS update Automation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |

### **Date:** September 10, 2025

| Project/Component | BU | Status | Owner | Target Date | Action Items | Notes/Risks |
| --- | --- | --- | --- | --- | --- | --- |
| EKS | HRP | 🟢 On Track | Vaughn Sargent, Brijesh Singh | October 15, 2025 | 9/8 - AWS to set up 2 AWS clusters for HRP. (rancher being used in onprem) |  |
| Firewall | HRP | 🔴Blocked | Aravind Rao | October 04, 2025 |  | 9/9 - Firewall cannot be deployed until Local VLAN/VPC is deployed which is planned to be completed before 9/27  9/9 - Gary working on deploying the VPCs. not required for the landing zone. |
| SFTP Implementation | HRP | 🟡 Not Started | Brijesh Singh | TBD | Work with Zak Thompson |  |
| MoveIt Automation | HRP | 🟡 Not Started | Brijesh Singh | TBD | Vendor engagement, license procurement, AWS server setup |  |
| Local VLAN | HRP | 🟢 In Progress | Aravind Rao | September 27, 2025 | off track for 9/15, updated to 9/27 | 9/9 - Gary is working on deploying the VPCs before 9/27 |
| Provisioning Automation | HRP | 🔴 Off Track | Brijesh Singh | September 15, 2025 | Resource allocation review | Heavy lift - missing deadline, needs staffing |
| DNS/AD | HRP | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| AD | HRP | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. ConnManagement VLAN 3. Connectivity to Datacenter to perform DC promotions 4. OS Template with Windows 2025, and way to deploy to our account 5. IDM Requires RHEL 8 template |
| SMTP Relay | HRP | 🔴 Blocked | Todd Matton  Jeff Rudolph | September 27, 2025 | Decision on shared email relay service | Waiting for the decision on what will be used to relay mail in AWS. If no decision is made will continue to relay email through datacenter relays  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| Container Registry | HRP | ⚫ TBD | Swarna Kunnath, Ted O'Hayer, Brijesh Singh | October 10, 2025 |  |  |
| Redhat satellite servers | HRP | 🔴 Blocked | Todd Matton, Jim Fallon | October 01, 2025 |  | Requires licensing for cloud based servers.  9/9 - Chris F has identified experts and will arrange a call as soon as possible |
| Ansible control servers | HRP | 🔴 Blocked | Brijesh Singh, Todd Matton | September 15, 2025 | Need to understand what has to happen to deploy | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| Jenkins server | HRP | 🟢 On track | Vaughn Sargent, Brijesh Singh | September 15, 2025 |  | 9/8 - use on-prem as is to start, day 2 build new bots, jenkins and ansible control server in aws. |
| Jump servers | HRP | 🔴 Blocked | Todd Matton, Ted O'Hayer | September 15, 2025 |  | Connecting to AWS Servers workshop - Teleport |
| Storage | HRP | ⚫ TBD | Kendra McCormick | TBD |  |  |
| Core Network connectivity | HRP | ⚫ TBD | Aravind Rao, Brijesh Singh | September 12, 2025 |  |  |
| Redhat Identity Manager | HRP | 🔴 Blocked | Todd Matton | September 15, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template     9/10 - Chris F to set up call |
| ConductorOne | HRP/GC | 🟢 On track | Jarrod Hermance, Aslam Khan | September 15, 2025 |  |  |
| IP Addressing | GC | 🟢 Complete | Marc Kaplan | September 09, 2025 | Sync with AWS team | Coordination meeting pending |
| Ingress | Egress - VPN | GC | 🟢 Complete | Marc Kaplan | October 15, 2025 | Marc Kaplan, now that the networks review tasks are closed, I’ll need the actual steps your team is handling to add to this list. |  |
| Ingress | Egress - WAN | GC | 🟢 Complete | Marc Kaplan | October 15, 2025 | Marc Kaplan, now that the networks review tasks are closed, I’ll need the actual steps your team is handling to add to this list. |  |
| Networks - VNET | GC | 🟢 Complete | Marc Kaplan | October 15, 2025 | Marc Kaplan, now that the networks review tasks are closed, I’ll need the actual steps your team is handling to add to this list. |  |
| ETL - CCDA | GC | ⚫ TBD | Anupama Sivasanker | October 15, 2025 |  |  |
| Storage - Container | GC | 🟢 On track | Ted O'Hayer | October 15, 2025 |  |  |
| Nexus | HRP | ⚫ TBD | Jim Fallon | TBD |  |  |
| IP/DNS config files / app investigation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |
| IP/DNS update Automation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |

### **Date:** September 9, 2025

| Project/Component | BU | Status | Owner | Target Date | Action Items | Notes/Risks |
| --- | --- | --- | --- | --- | --- | --- |
| EKS | HRP | 🟢 On Track | Vaughn Sargent, Brijesh Singh | October 15, 2025 | 9/8 - AWS to set up 2 AWS clusters for HRP. (rancher being used in onprem) | Rahul (AWS) will be building these out next sprint. |
| Firewall | HRP | 🔴Blocked | Aravind Rao | October 04, 2025 | Timeline adherence unclear | 9/9 - Firewall cannot be deployed until Local VLAN/VPC is deployed which is planned to be completed before 9/27  9/9 - Gary working on deploying the VPCs. not required for the landing zone. |
| SFTP Implementation | HRP | 🟡 Not Started | Brijesh Singh | TBD | Work with Zak Thompson | Starting 9/8 - immediate priority |
| MoveIt Automation | HRP | 🟡 Not Started | Brijesh Singh | TBD | Vendor engagement, license procurement, AWS server setup | Starting 9/8 - high priority |
| Local VLAN | HRP | 🟢 In Progress | Aravind Rao | September 27, 2025 | off track for 9/15, updated to 9/27 | 9/9 - Gary is working on deploying the VPCs before 9/27 |
| Provisioning Automation | HRP | 🔴 Off Track | Brijesh Singh | September 15, 2025 | Resource allocation review | Heavy lift - missing deadline, needs staffing |
| DNS/AD | HRP | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| AD | HRP | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. ConnManagement VLAN 3. Connectivity to Datacenter to perform DC promotions 4. OS Template with Windows 2025, and way to deploy to our account 5. IDM Requires RHEL 8 template |
| SMTP Relay | HRP | 🔴 Blocked | Todd Matton | September 27, 2025 | Decision on shared email relay service | Waiting for the decision on what will be used to relay mail in AWS. If no decision is made will continue to relay email through datacenter relays  minimum requirements:   1. ManaManagement VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| Container Registry | HRP | ⚫ TBD | Swarna Kunnath, Ted O'Hayer, Brijesh Singh | October 10, 2025 |  |  |
| Redhat satellite servers | HRP | 🔴 Blocked | Todd Matton, Jim Fallon | October 01, 2025 |  | Requires licensing for cloud based servers.  9/8 - chris f to follow up with redhat license specialist (windows)  9/9 - Chris F has identified experts and will arrange a call as soon as possible |
| Ansible control servers | HRP | 🔴 Blocked | Brijesh Singh, Todd Matton | September 15, 2025 | Need to understand what has to happen to deploy | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| Jenkins server | HRP | 🟢 On track | Vaughn Sargent, Brijesh Singh | September 15, 2025 |  | 9/8 - use on-prem as is to start, day 2 build new bots, jenkins and ansible control server in aws. |
| Jump servers | HRP | 🔴 Blocked | Todd Matton, Ted O'Hayer | September 15, 2025 |  | Connecting to AWS Servers workshop - Teleport |
| Storage | HRP | ⚫ TBD | Kendra McCormick | TBD |  |  |
| Core Network connectivity | HRP | ⚫ TBD | Aravind Rao, Brijesh Singh | September 12, 2025 |  |  |
| Redhat Identity Manager | HRP | 🔴 Blocked | Todd Matton | September 15, 2025 |  | Blocked by local VLAN Deployment  minimum requirements:   1. Management VLAN 2. Connectivity to Datacenter to perform DC promotions 3. OS Template with Windows 2025, and way to deploy to our account 4. IDM Requires RHEL 8 template |
| ConductorOne | HRP/GC | 🟢 On track | Jarrod Hermance, Aslam Khan | September 15, 2025 |  |  |
| IP Addressing | GC | 🟢 On track | Marc Kaplan | September 09, 2025 | Sync with AWS team | Coordination meeting pending |
| Ingress | Egress - VPN | GC | 🟢 On track | Marc Kaplan | October 15, 2025 | In confluence ready to be approved by Aravind and Marc. https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033182/5.2+Network+Data+Flows |  |
| Ingress | Egress - WAN | GC | 🟢 On track | Marc Kaplan | October 15, 2025 | In confluence ready to be approved by Aravind and Marc. https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867033182/5.2+Network+Data+Flows |  |
| Networks - VNET | GC | 🟢 On track | Marc Kaplan | October 15, 2025 |  |  |
| ETL - CCDA | GC | ⚫ TBD | Anupama Sivasanker | October 15, 2025 |  |  |
| Storage - Container | GC | 🟢 On track | Ted O'Hayer | October 15, 2025 |  |  |
| Nexus | HRP | ⚫ TBD | Jim Fallon | TBD |  |  |
| IP/DNS config files / app investigation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |
| IP/DNS update Automation | HRP | ⚫ TBD | Brijesh Singh | TBD |  |  |

### **Date:** September 8, 2025

| Project/Component | Status | Owner | Target Date | Action Items | Notes/Risks |
| --- | --- | --- | --- | --- | --- |
| **GC - VLAN Closure** | ✅ Completed | - | - | None | Network segmentation complete |
| **GC - IP Addressing** | 🟡 In Progress | Marc Kaplan | 9/9 | Sync with AWS team | Coordination meeting pending |
| **CCDA Scope** | 🔴 Blocked | TBD | TBD | Understand scope & workshop status | Requirements unclear |
| **HRP - Firewall** | 🔴 Blocked | Aravind Rao | 10/4 | Blocked | September 09, 2025 - Firewall cannot be deployed until Local VLAN/VPC is deployed which is planned to be completed before 9/27 |
| **SFTP Implementation** | 🔴 Not Started | Brijesh Singh | TBD | Work with Zak Thompson | Starting 9/8 - immediate priority |
| **MoveIt Automation** | 🔴 Not Started | Brijesh Singh | TBD | Vendor engagement, license procurement, AWS server setup | Starting 9/8 - high priority |
| **Local VLAN** | 🟡 In Progress | Aravind Rao | September 27, 2025 | Confirm on-track status | Timeline confirmation needed 9/9 - Gary is working on deploying the VPCs before 9/27. Dependency for all DNS/AD work. |
| **Provisioning Automation** | 🔴 Off Track | Brijesh Singh | 9/15 | Resource allocation review | Heavy lift - missing deadline, needs staffing |
| HRP - DNS/AD | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment |
| HRP - AD | 🔴 Blocked | Todd Matton | September 27, 2025 |  | Blocked by local VLAN Deployment |
| HRP - SMTP Relay | 🔴 Blocked | Todd Matton | September 27, 2025 |  |  |