# Artifact---Business-Drivers-and-Technical-Guiding-Principles

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867001573/Artifact---Business-Drivers-and-Technical-Guiding-Principles

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:53 AM

---

### Document Lifecycle Status

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

### **Business Drivers**

The key is to identify the stakeholders that need to be part of the discussion to document the drivers. Typically, CxOs, senior managers, and key technology leaders within the organization. Business drivers should be linked to a metric that can be measured throughout the migration journey in order to validate whether the outcomes have been achieved. The company strategic goals and annual reports can act as a starting point. Focus the conversation on where the company wants to be, based on existent and projected metrics, as a result of moving to the cloud. Consider goals and business outcomes. Also, what success looks like as cloud adoption increases. Next, establish the importance level of each driver. What are the priorities? What are the expected benefits? How does the benefits support the business goals and outcomes? In the context of application portfolio assessment, this will help to assist workload prioritization for migration and to establish technical guiding principles. However, business drivers will define and impact the migration program as a whole.

### **Technical Guiding Principles**

These principles are key to inform migration strategy selection in portfolio assessment.  Guiding principles can be established as general technology- and approach-related decisions derived from business goals and outcomes. For example, if the primary goal is to reduce cost, and the desired outcome is to close an on-premises data center by a given date in the near future (e.g., 6 to 12 months), a resulting guiding principle would be to lift and shift all applications to the cloud by means of a rehost or relocate migration strategy whenever possible. In this case, the approach will accelerate migration outcomes and will permit to focus on the main business drivers to later optimize/modernize the migrated workloads once they have moved out the on-premises data center.  
To establish the technical guiding principles, start by analysing business drivers and identifying a list of technologies and techniques that will enable the business goals and outcomes. Next, refine the list and assign an order of relevance based on best suitability/preference to achieve a desired outcome.  
Document and socialize the guiding principles with the people involved in planning and performing the migration. Highlight concerns and potential conflicts between the principles and the actual implementation.

### **Sample of business drivers and technical guiding principles**

Update the table below based on actual drivers and guiding principles

| Goal | Outcome | Metric | Guiding Principle |
| --- | --- | --- | --- |
| *Innovation* | *Improved competitiveness, increased business agility* | *Number of deployments per day/month, new features release per quarter, customer satisfaction scores, number of experiments* | *Refactor differentiating applications leveraging Microservices and the DevOps operating model to increase agility and speed to market of new features* |
| *Operational Costs* | *Supply and demand matched, elastic cost base (pay for what you use)* | *Spend variation over time* | *1-Rehost applications with infrastructure right-sizing.*  *2-Retire applications with low/no utilization.* |
| *Operational Resiliency* | *Improved uptime, reduced mean time to recovery* | *SLA's, number of incidents* | *1-Replatform applications to latest and best supported OS versions and implement high availability architectures for critical applications* |
| *Data center exit* | *Data center closure by a date within 6-12 months* | *Speed of server migrations* | *1-Rehost applications leveraging AWS Cloud Endure Migration Factory*  *2-Relocate (via VMware Cloud on AWS).* |
| *Stay on premises, but increase agility and resiliency* | *Improved competitiveness & uptime while remaining on-premise* | *Number of deployments per day/month, new features release per quarter, SLA's, number of incidents* | *1-Modernize systems by extending its functionality into the Cloud*  *2-Assess for Rehost or Replatform to AWS Outposts* |