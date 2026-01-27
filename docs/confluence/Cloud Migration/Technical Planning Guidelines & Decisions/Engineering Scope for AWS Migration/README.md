# Engineering Scope for AWS Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5100667098/Engineering%20Scope%20for%20AWS%20Migration

**Created by:** Kaitlin Wieand on September 16, 2025  
**Last modified by:** Kaitlin Wieand on September 16, 2025 at 03:48 PM

---

Scope document to track tasks, identify roles/responsibilities for teams and completion date.

| **Project** | **Task** | **Team** | **Jira ticket** | **Completion Date** |
| --- | --- | --- | --- | --- |
| DNS/IP Config | DNS updates for internal servers - DevOps   1. Payer 2. Connector 3. Answers 4. Answers AdHoc 5. Load Balancer (OPS - Brijesh’s Team) | DevOps |  | 10/30/2025 |
| DNS/IP Config - Database | Change the host file in the DB server with the new IP address | Database Team (Madhu) |  |  |
| DNS/IP Config - Data Collection | Collect the list of integrations for each customer. Examples:   1. Cotivity 2. Zelis 3. CXT 4. CES 5. EASYGroup 6. 3M 7. IBM MQ 8. HMEM (Market Prominence) 9. DDPA for NW accounts 10. Plan Connection for Blues customers 11. CareFirst integration for FEP claims for Blues customers | Ops (Brijesh’s Team) |  | 01/12/2025 |
| DNS/IP Config -  Validation after migration | Ensuring external integrations work after migration   1. Cotivity 2. Zelis 3. CXT 4. CES 5. EASYGroup 6. 3M 7. IBM MQ 8. HMEM (Market Prominence) 9. DDPA for NW accounts 10. Plan Connection for Blues customers 11. CareFirst integration for FEP claims for Blues customers | OPS (Brijesh’s Team) |  | N/A - Will be done during each migration |
| Provision new environment in AWS for a customer | Rewrite the provisioner to provision new servers in AWS   1. Payer 2. Connector 3. Promote 4. PIK 5. Answers 6. LB 7. NextGen Correspondence 8. iWay 9. Provider Directory | DevOps |  |  |
| DNS/IP - External Updates | Provide external DNS address to customer where they are connecting to our App/DB servers in Environment Handoff Document | CSE,CSM,Ops |  |  |
|  | Certification of the installer to ensure that we can perform upgrades for customers/partners migrated to AWS | DevOps |  |  |
| Provisioning Automation | Reconfigure Script |  |  |  |
| Provisioning Automation | Migrate Server |  |  |  |
| Provisioning Automation |  |  |  |  |
| Ansible Control Servers |  |  | PINIT-131 |  |

|  |
| --- |
|  |
|  |
|  |
|  |
|  |
|  |
|  |
|  |
|  |