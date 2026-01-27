# Cloud Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4805754941/Cloud%20Migration

**Created by:** Kaitlin Wieand on May 23, 2025  
**Last modified by:** Kaitlin Wieand on December 04, 2025 at 08:33 AM

---

Objective: Driving agility, scalability and cost efficiency through a strategic migration to AWS that positions us for long-term growth and innovation.

| **URL** |
| --- |
| [AWS/HealthEdge Sharepoint](https://healthedgetrial.sharepoint.com/sites/AWSCloudMigration/Shared%20Documents/Forms/AllItems.aspx) |
| [AWS Migration JIRA Board](https://healthedge.atlassian.net/jira/software/projects/AWSM/summary) |
| [Cloud Migration Confluence](https://healthedge.atlassian.net/wiki/spaces/CP1/pages/edit-v2/4805754941) |

**POC**
-------

| **HealthEdge** | **POC** | **Teams** | **Amazon** |
| --- | --- | --- | --- |
| Program Management | Kaitlin Wieand | Program |  |
| Technical Lead | Ted O'Hayer | Migration |  |
| GC Technical Lead | Marc Kaplan, Vidya Sambasivan | Security |  |
| HRP Technical Lead | Todd Matton, Joseph Branciforte, Brijesh Singh | Foundations |  |
| HRP DevOps | Riyazuddin Shaik, Vikas Kumar Agrawal |  |  |
| QA Testing | Vishnu Mani |  |  |
| Security Leads | Jarrod Hermance, Aslam Khan, Jordan Herrera, Jeannine Gaudreau |  |  |
| Customer Operations Team | Renee Ghent, Sarang Muralidharan, Michele Oliveto-Hill (Deactivated), Steffanie Wood |  |  |
| Networks & Database Leads | Aravind Rao, Madhu Ravi, Jawad Shah |  |  |
| Supporting Technical Roles | Jim Fallon |  |  |
| TLT | Cris Grunca, Mark Mucha |  |  |

Governance Cadence:
-------------------

| **Meeting** | **Audience** | **Frequency** | **Meeting Invite** | **Notes** |
| --- | --- | --- | --- | --- |
| Steerco | ELT, TLT, Customer Leads | 1x month (Last Tuesday of the month, 1130AM) |  |  |
| Program Leads | AWS and HealthEdge Program Leads | 1x week. (Mon 1200 ET) |  |  |
| Status Review |  | 1x week  (Tuesdays 1130 am) |  |  |
| Technical Standup (workstreams) | Foundation & Migration Workstreams | Monday - Thursday |  | 5 workstreams, 2 different standups |
| Scrum of Scrums | EMs, Tech Leads, PM, Workstream Leads. | 1x week (Thursdays 130PM) |  |  |

**Pre-planning**
----------------

ModelizeIT Matrix

| **Product** | **Owner** | **Status** | **Date for Date** | **Target Completion Date** | **Next Steps** |
| --- | --- | --- | --- | --- | --- |
| HRP | Todd Matton | Done | May 27, 2025 | May 30, 2025 | Currently deployed in the test environment, planning to discuss rollout plan with change management on 5/27/2025 |
| GC | Marc Kaplan | Done | May 27, 2025 | May 29, 2025 | Waiting on go-live date, will check in on Tuesday |
| Source | Ted O'Hayer | In progress | May 27, 2025 | June 06, 2025 | POS is currently out of office, will check in Tuesday. |
| Wellframe | Ted O'Hayer | In progress | May 27, 2025 |  | POC is currently out of office, but was informed they may be out of scope for this since ProServ is not involved. |

**Security & Compliance:**
--------------------------

Security is a foundational pillar of our AWS Cloud Migration strategy. As we transition workloads to the cloud, we are committed to maintaining the highest standards of data protection, compliance, and operational integrity. 📌 For more details, visit the Cloud Security Framework Confluence page.

What’s in scope:
----------------

This migration initiative focuses on transitioning our existing infrastructure, applications, and services to Amazon Web Services (AWS) to enhance scalability, reliability, and cost-efficiency. The following components are in scope for this phase:

* **Infrastructure Migration**: Lift-and-shift of on-premises servers, virtual machines, and storage to AWS EC2, S3, and related services.
* **Application Rehosting & Refactoring**: Selected applications will be rehosted as-is, while others may undergo minor refactoring to leverage AWS-native services (e.g., RDS, Lambda, ECS).
* **Database Migration**: Migration of structured and unstructured data to AWS-managed databases (e.g., RDS, DynamoDB).
* **Networking & Security**: Configuration of VPCs, subnets, security groups, IAM roles, and VPNs to ensure secure and compliant cloud operations.
* **Monitoring & Logging**: Implementation of AWS CloudWatch, CloudTrail, and other observability tools for performance and security monitoring.
* **Automation & CI/CD**: Integration of infrastructure-as-code (e.g., Terraform, CloudFormation) and CI/CD pipelines for streamlined deployments.
* **Knowledge Transfer & Training**: Enablement sessions and documentation to support internal teams in managing and operating the new AWS environment.
* See Migration Technical Plans

Project Tenets
--------------

1. **Customer First**

2. **Better Forward**

3. **Scale Beyond Boundaries**

4. **Automate Everything**
5. **Security by Design**
6. **Fail Fast, Learn Faster**

7. **Cost Conscious, Value Driven**

8. **Data Integrity Above All**
9. **Team Empowerment Through Knowledge**
10. **Measure Everything, Decide with Data**

More Info on the Tenets

Supporting Docs:
----------------