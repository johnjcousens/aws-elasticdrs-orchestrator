# DACI: AWS Migration with VPN Transition

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5202411678/DACI%3A%20AWS%20Migration%20with%20VPN%20Transition

**Created by:** Kaitlin Wieand on November 05, 2025  
**Last modified by:** Kaitlin Wieand on November 12, 2025 at 07:08 PM

---

|  |  |
| --- | --- |
| **Status** | DECISION MADEGreen |
| **Impact** | HighRed |
| **Driver** | Kaitlin Wieand |
| **Approver** | Mark Mucha, Rob Duffy |
| **Contributors** | Joseph Branciforte, Jim Fallon, Aravind Rao, Brijesh Singh |
| **Informed** | Renee Ghent, Cris Grunca |
| **Due date** | 11/10/2025 |
| **Resources** | Type /link to add links to relevant research, pages, and related decisions |

Background
----------

As part of the AWS Migration, HealthEdge will need to migrate customer workloads from on-premises HEDC to AWS. Since we cannot keep the same IP address running on-prem and in the cloud, we’ll need to update existing network configurations during transition while trying to minimize customer disruption.

A fundamental networking constraint prevents the same IP address from existing simultaneously in HEDC and AWS on an interconnected network.

Relevant data
-------------

**Multiple Integration Points Per Customer:**

Customers connect to HealthEdge-hosted applications and services through numerous integration points, each potentially containing hardcoded IP addresses or network dependencies that must be managed during migration:

* A customer with >5 different integration points means each configuration change approach must be evaluated and executed ~5 times
* Each integration point may have different stakeholders, testing requirements, and maintenance windows. For example, Partnership of California has 95 applications that point to HRP Payer, Connector, DW, or CES.
* Cumulative risk increases exponentially with the number of integration points, requiring a lot of coordination among various teams on the HE and the customer's end.
* Multiple teams within customer organization own different integration points (application teams, infrastructure teams, security teams, partner management)

Options considered
------------------

|  | **Option 1** | **Option 2** |  |  |
| --- | --- | --- | --- | --- |
| **Description** | HE keeps the external NAT’d IPs the same, avoiding additional work for customers as part of the migration. With this scenario traffic will route from Customer VPN to HEDC and then on to AWS. As part of Production go-live customer will switch to a new VPN that will connect directly to AWS.  *(Note the new VPN is an existing migration requirement and not introduced by this option.)* | Convert all hardcoded IP addresses in customer and HealthEdge configurations to DNS hostnames, then migrate services to AWS while updating DNS records to point to new AWS IPs |  |  |
| **Pros and cons** | Easier lift for the customer during the migration.  Not all customers have readily available network staff. This solution mitigates that issue during migration.  By keeping external IPs the same a backout to on-prem during the AWS migration is trivial.    Increased latency due to additional network hops through HEDC infrastructure. Customer impact depends on location.  Temporary solution only, not strategic and will need to be remediated.  HealthEdge Networking and App Services takes the majority of the work  Temporary workarounds that must be maintained until customer upgrade occurs at which time they will have to migration to DNS.  Network diagrams/runbooks to be updated for the temporary solution | Makes future migrations, DR failovers, and infrastructure changes trivial  Industry standardization  Centralized IP management. IP changes managed in one place instead of hundreds of configs  This is the strategic approach for HealthEdge, no future remediation will be required.      All External (Customer and Partner) integrations need to be changed to new DNS endpoints, which takes time for the customer.  Also applies to Database and SFTP access.  Coordination complexity  During the AWS migration if a customer environment is “backed out” to On-Prem, customer will have to undo their DNS changes adding complexity to the backout. |  |  |
| **Estimated cost** | LARGERed (on networking)  IP to IP mappings will need to be maintained for each customer. | LARGERed (on customer/app team)  Customers need to update all integration/service endpoints. |  |  |

Action items
------------

Add action items to close the loop on open questions or concerns.



- [ ] Update network runbooks by2025-11-17
- [ ] Update FAQ pages for customers migrating explaining steps



Outcome
-------

Summarize the outcome.
----------------------

**Option 1 Selected** - Keep all external NATted IPs, route traffic through customer VPN to on-prem and then to AWS during migration. This minimizes customer disruption and coordination effort.

Key Rationale
-------------

* **Minimal customer impact**: Customers avoid coordinating multiple DNS/IP changes across integration points
* **Better rollback capability**: Easier to revert if issues arise
* **Flexible timing**: Allows customers to change VPN once during production cutover rather than piecemeal
* **Risk mitigation**: Even if customers delay VPN cutover, they can continue operating with acceptable latency